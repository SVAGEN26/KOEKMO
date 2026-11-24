// Local bridge between an AI assistant (MCP) and the open scenario lab page.
//
//   node mcp/bridge.ts                 MCP over HTTP at http://127.0.0.1:8765/mcp (Authorization: Bearer <token>)
//   node mcp/bridge.ts --stdio         MCP over stdin/stdout for a client that starts the bridge itself
//   options: --port 8765  --token <token>  --origin https://example.org  --host 127.0.0.1
//
// The bridge computes nothing. The page connects out to it (the "AI" menu at the top right, with address and token), the bridge
// forwards each tool call to the page, and the page runs it with its own OpenModelica build (site/src/ai-tools.js).
// It listens on 127.0.0.1 only unless --host says otherwise, makes no outgoing requests, holds no API keys, and
// requires the token from the page and from MCP clients over HTTP. The token is printed once to stderr.
import {createServer} from 'node:http';
import type {IncomingMessage, ServerResponse} from 'node:http';
import {randomBytes, timingSafeEqual} from 'node:crypto';
import {createInterface} from 'node:readline';
import {TOOLS} from '../site/src/ai-tools.js';

type Json = null | boolean | number | string | Json[] | {[key: string]: Json};
type Message = {jsonrpc?: string; id?: string | number | null; method?: string; params?: {[key: string]: any}};
type Pending = {resolve: (value: Json) => void; reject: (error: Error) => void; timer: NodeJS.Timeout};

const PROTOCOLS = ['2025-06-18', '2025-03-26', '2024-11-05'];
const SERVER_INFO = {name: 'motala-ekonomilabb-bridge', title: 'Motala ekonomilabb (sidan)', version: '0.1.0'};
const CALL_TIMEOUT_MS = 120_000;
const MAX_BODY = 1_000_000;
const DEFAULT_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000', 'https://svagen26.github.io'];

export function parseArgs(argv: string[]) {
  const options = {port: 8765, host: '127.0.0.1', token: '', origins: [...DEFAULT_ORIGINS], stdio: false};
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i], next = () => {
      const value = argv[++i];
      if (value === undefined) throw Error(`${arg} needs a value`);
      return value;
    };
    if (arg === '--port') options.port = Number(next());
    else if (arg === '--host') options.host = next();
    else if (arg === '--token') options.token = next();
    else if (arg === '--origin') options.origins.push(new URL(next()).origin);
    else if (arg === '--stdio') options.stdio = true;
    else throw Error(`Unknown option ${arg}`);
  }
  if (!Number.isInteger(options.port) || options.port < 0 || options.port > 65535) throw Error('--port is 0-65535');
  if (options.token && !/^[A-Za-z0-9_-]{16,128}$/.test(options.token)) throw Error('--token: 16-128 letters, digits, - or _');
  options.token ||= randomBytes(24).toString('base64url');
  return options;
}

export function createBridge(options: ReturnType<typeof parseArgs>) {
  const expected = Buffer.from(`Bearer ${options.token}`);
  const authorised = (request: IncomingMessage) => {
    const given = Buffer.from(String(request.headers.authorization ?? ''));
    return given.length === expected.length && timingSafeEqual(given, expected);
  };
  const loopbackOrigin = (origin: string) => /^https?:\/\/(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$/.test(origin);
  const allowedOrigin = (origin: string | undefined) => origin === undefined || options.origins.includes(origin) || loopbackOrigin(origin);

  let page: ServerResponse | null = null;
  let keepAlive: NodeJS.Timeout | null = null;
  let nextCall = 1;
  const pending = new Map<number, Pending>();

  function dropPage(reason: string) {
    if (keepAlive) clearInterval(keepAlive);
    keepAlive = null;
    page = null;
    for (const [id, call] of pending) {
      clearTimeout(call.timer);
      call.reject(Error(reason));
      pending.delete(id);
    }
  }

  function callPage(name: string, args: Json): Promise<Json> {
    if (!page) return Promise.reject(Error('Ingen sida är kopplad. Öppna ekonomilabbet, välj "AI" uppe till höger och koppla med bryggans adress och token.'));
    const id = nextCall++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(Error('Sidan svarade inte inom två minuter.'));
      }, CALL_TIMEOUT_MS);
      pending.set(id, {resolve, reject, timer});
      page!.write(`data: ${JSON.stringify({id, name, arguments: args})}\n\n`);
    });
  }

  async function handle(message: Message): Promise<Json | undefined> {
    const {id, method} = message;
    const params = message.params ?? {};
    if (id === undefined || id === null) return undefined; // notifications need no answer
    const reply = (result: Json) => ({jsonrpc: '2.0', id, result});
    try {
      switch (method) {
        case 'initialize':
          return reply({protocolVersion: PROTOCOLS.includes(params.protocolVersion) ? params.protocolVersion : PROTOCOLS[0],
            capabilities: {tools: {listChanged: false}, prompts: {listChanged: false}}, serverInfo: SERVER_INFO,
            instructions: 'Scenariolabb för kommunekonomin i Östergötlands 13 kommuner. Verktygen arbetar i den sida användaren har öppen: '
              + 'börja med get_state och list_assumptions, pröva med preview_scenario och visa med set_assumptions.'});
        case 'ping': return reply({});
        case 'tools/list': return reply({tools: TOOLS as unknown as Json});
        case 'tools/call': {
          const tool = TOOLS.find(t => t.name === params.name);
          if (!tool) throw Error(`Okänt verktyg ${params.name}`);
          try {
            const data = await callPage(tool.name, params.arguments ?? {});
            return reply({content: [{type: 'text', text: JSON.stringify(data)}], structuredContent: data, isError: false});
          } catch (error) {
            return reply({content: [{type: 'text', text: (error as Error).message}], isError: true});
          }
        }
        case 'prompts/list':
          return reply({prompts: [{name: 'scenario_lab', description: 'Pröva scenarier för den kommun sidan visar och förklara vad som driver resultatet.',
            arguments: [{name: 'question', description: 'Vad användaren vill veta', required: false}]}]});
        case 'prompts/get': {
          if (params.name !== 'scenario_lab') throw Error('Okänd prompt');
          const question = params.arguments?.question ?? 'Hur påverkar skattesats, investeringar och ränta resultatet och skulden?';
          return reply({description: 'Scenariolabb', messages: [{role: 'user', content: {type: 'text', text:
            `Du arbetar i ekonomilabbets sida via verktygen. Fråga: ${question}\n`
            + 'Börja med get_state och list_assumptions och läs förklaringarna. Hämta utfall med get_series (accounts) om historiken behövs. '
            + 'Pröva alternativ med preview_scenario och jämför resultat, skuld och kassa. Visa det scenario du rekommenderar med set_assumptions '
            + 'och ett kort skäl. Säg vilka antaganden som avgör slutsatsen och att modellen inte är en prognos att lita på framför enklare: '
            + 'i bakåttestet slår den "basårets resultatandel kvar" bara de tre första åren (get_series hindcast).'}}]});
        }
        default:
          return {jsonrpc: '2.0', id, error: {code: -32601, message: `Method not found: ${method}`}};
      }
    } catch (error) {
      return {jsonrpc: '2.0', id, error: {code: -32603, message: (error as Error).message}};
    }
  }

  function cors(request: IncomingMessage, response: ServerResponse) {
    const origin = request.headers.origin;
    if (origin && allowedOrigin(origin)) {
      response.setHeader('Access-Control-Allow-Origin', origin);
      response.setHeader('Vary', 'Origin');
    }
  }

  function readBody(request: IncomingMessage): Promise<string> {
    return new Promise((resolve, reject) => {
      let size = 0;
      const chunks: Buffer[] = [];
      request.on('data', (chunk: Buffer) => {
        size += chunk.length;
        if (size > MAX_BODY) {
          reject(Error('too large'));
          request.destroy();
        } else chunks.push(chunk);
      });
      request.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
      request.on('error', reject);
    });
  }

  const send = (response: ServerResponse, status: number, body?: Json) => {
    if (body === undefined) {
      response.writeHead(status).end();
      return;
    }
    const text = JSON.stringify(body);
    response.writeHead(status, {'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(text)}).end(text);
  };

  const server = createServer(async (request, response) => {
    const path = new URL(request.url ?? '/', 'http://bridge').pathname;
    if (!allowedOrigin(request.headers.origin)) return send(response, 403, {error: 'Origin not allowed'});
    cors(request, response);
    if (request.method === 'OPTIONS') {
      response.setHeader('Access-Control-Allow-Methods', 'GET, POST');
      response.setHeader('Access-Control-Allow-Headers', 'Authorization, Content-Type, Mcp-Session-Id, Mcp-Protocol-Version');
      if (request.headers['access-control-request-private-network']) response.setHeader('Access-Control-Allow-Private-Network', 'true');
      return send(response, 204);
    }
    if (!authorised(request)) return send(response, 401, {error: 'Token saknas eller är fel'});
    try {
      if (path === '/page/events' && request.method === 'GET') {
        if (page) {
          page.end();
          dropPage('En annan sida kopplade till bryggan.');
        }
        response.writeHead(200, {'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', Connection: 'keep-alive'});
        response.write(': kopplad\n\n');
        page = response;
        keepAlive = setInterval(() => response.write(': ping\n\n'), 15_000);
        request.on('close', () => {
          if (page === response) dropPage('Sidan kopplade från.');
        });
        log('page connected');
        return;
      }
      if (path === '/page/result' && request.method === 'POST') {
        const answer = JSON.parse(await readBody(request));
        const call = pending.get(answer.id);
        if (!call) return send(response, 404, {error: 'Unknown call'});
        pending.delete(answer.id);
        clearTimeout(call.timer);
        if (typeof answer.error === 'string') call.reject(Error(answer.error));
        else call.resolve(answer.result ?? null);
        return send(response, 204);
      }
      if (path === '/mcp' && request.method === 'POST') {
        const message = JSON.parse(await readBody(request)) as Message;
        log('mcp', message.method === 'tools/call' ? `tools/call ${message.params?.name}` : String(message.method));
        const reply = await handle(message);
        if (reply === undefined) return send(response, 202);
        if (message.method === 'initialize') response.setHeader('Mcp-Session-Id', randomBytes(16).toString('hex'));
        return send(response, 200, reply);
      }
      if (path === '/mcp') {
        response.setHeader('Allow', 'POST');
        return send(response, 405);
      }
      return send(response, 404, {error: 'Not found'});
    } catch (error) {
      return send(response, 400, {error: (error as Error).message === 'too large' ? 'Body too large' : 'Invalid request'});
    }
  });

  return {server, handle, pageConnected: () => page !== null, close() {
    if (page) page.end();
    dropPage('Bryggan stängdes.');
    server.close();
    server.closeAllConnections();
  }};
}

function log(...parts: string[]) {
  process.stderr.write(`[bridge] ${parts.join(' ')}\n`);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const bridge = createBridge(options);
  await new Promise<void>(resolve => bridge.server.listen(options.port, options.host, resolve));
  const address = bridge.server.address();
  const port = typeof address === 'object' && address ? address.port : options.port;
  const host = options.host.includes(':') ? `[${options.host}]` : options.host;
  if (!['127.0.0.1', '::1', 'localhost'].includes(options.host)) log(`Varning: lyssnar på ${options.host}, inte bara den egna datorn.`);
  log(`Sidans adress:  http://${host}:${port}/`);
  log(`Token:          ${options.token}`);
  log(options.stdio ? 'MCP över stdio.' : `MCP:            http://${host}:${port}/mcp med Authorization: Bearer <token>`);
  if (options.stdio) {
    const lines = createInterface({input: process.stdin});
    lines.on('line', async line => {
      if (!line.trim()) return;
      let message: Message;
      try {
        message = JSON.parse(line);
      } catch {
        process.stdout.write(JSON.stringify({jsonrpc: '2.0', id: null, error: {code: -32700, message: 'Parse error'}}) + '\n');
        return;
      }
      const reply = await bridge.handle(message);
      if (reply !== undefined) process.stdout.write(JSON.stringify(reply) + '\n');
    });
    lines.on('close', () => bridge.close());
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main().catch(error => {
  log(String(error.message ?? error));
  process.exit(1);
});
