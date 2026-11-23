// Opt-in link from the page to a local bridge (mcp/bridge.ts) that an AI assistant talks to over MCP.
// The page connects out to the address the user gives, with the bridge's token; it never listens itself.
// The bridge forwards tool calls; the page runs them with its own model (ai-tools.js) and posts the answer back.
import {callTool} from './ai-tools.js';

export function isLoopback(url) {
  try {return ['127.0.0.1','localhost','[::1]'].includes(new URL(url).hostname);} catch {return false;}
}

export function connect({address,token,adapter,onStatus=()=>{},onCall=()=>{}}) {
  const base=new URL(address);
  if(!['http:','https:'].includes(base.protocol)) throw Error('Adressen ska börja med http:// eller https://.');
  if(!/^[A-Za-z0-9_-]{16,128}$/.test(token)) throw Error('Token ska vara den som bryggan skrev ut.');
  const headers={Authorization:`Bearer ${token}`};
  const controller=new AbortController();
  let open=true;

  async function answer(call) {
    let body;
    try {body={id:call.id,result:await callTool(adapter,call.name,call.arguments??{})};}
    catch(e) {body={id:call.id,error:e.message};}
    onCall(call,body);
    await fetch(new URL('page/result',base),{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal});
  }

  (async()=>{
    try {
      const response=await fetch(new URL('page/events',base),{headers,signal:controller.signal,cache:'no-store'});
      if(response.status===401) throw Error('Bryggan godtog inte token.');
      if(!response.ok||!response.body) throw Error(`Bryggan svarade ${response.status}.`);
      onStatus('connected');
      const reader=response.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer='';
      for(;;) {
        const {value,done}=await reader.read();
        if(done) break;
        buffer+=value;
        let end;
        while((end=buffer.indexOf('\n\n'))>=0) {
          const event=buffer.slice(0,end);buffer=buffer.slice(end+2);
          const data=event.split('\n').filter(line=>line.startsWith('data:')).map(line=>line.slice(5).trim()).join('\n');
          if(!data) continue;
          const call=JSON.parse(data);
          answer(call).catch(e=>onStatus('error',e.message));
        }
      }
      if(open) onStatus('closed','Bryggan stängde förbindelsen.');
    } catch(e) {
      if(open) onStatus('error',e.name==='TypeError'?'Når inte bryggan. Kör den, och kontrollera adress och port.':e.message);
    }
  })();
  return {close(){open=false;controller.abort();onStatus('closed');}};
}
