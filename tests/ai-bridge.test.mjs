// The local AI bridge (mcp/bridge.ts) and the page's tools (site/src/ai-tools.js), with a fake page.
import test from 'node:test';
import assert from 'node:assert/strict';
import {createBridge,parseArgs} from '../mcp/bridge.ts';
import {connect} from '../site/src/ai-link.js';
import {callTool,TOOLS} from '../site/src/ai-tools.js';

function fakeAdapter() {
  const rows=v=>[2025,2026,2027].map((year,i)=>({year,population:43000,tax:2300+i*50,grants:990,cost:3000,depreciation:120,result:60+i*v,investment:400,interest:25,debt:1500,cash:50}));
  let value=0;
  return {
    state:()=>({municipality:'0583',name:'Motala',baseYear:2025,forecastYears:[2026,2027],changed:value?{taxRate:value}:{}}),
    municipalities:()=>[{code:'0583',name:'Motala',startYears:[2026,2025,2022]}],
    assumptions:()=>[{key:'taxRate',label:'Kommunal skattesats',unit:'%',min:19,max:24,value:21.7,default:21.7}],
    results:()=>rows(value?10:0),
    preview:async v=>rows(v.taxRate>21.7?20:0),
    apply:async v=>{value=v.taxRate;return rows(10);},
    reset:async()=>{value=0;return rows(0);},
    select:async()=>{},
    series:async(name)=>({name,rows:[{year:2025,value:1}]})
  };
}

test('tools validate names and ranges', async () => {
  const a=fakeAdapter();
  await assert.rejects(callTool(a,'set_assumptions',{values:{nope:1}}),/Okänt antagande/);
  await assert.rejects(callTool(a,'set_assumptions',{values:{taxRate:30}}),/mellan 19 och 24/);
  await assert.rejects(callTool(a,'get_series',{series:'secret'}),/Okänd serie/);
  const preview=await callTool(a,'preview_scenario',{values:{taxRate:22.2}});
  assert.equal(preview.difference[0].result,20);
  assert.ok(TOOLS.every(t=>t.inputSchema.type==='object'));
});

test('bridge forwards MCP calls to the connected page and requires the token', async t => {
  const options=parseArgs(['--port','0']);
  const bridge=createBridge(options);
  await new Promise(r=>bridge.server.listen(0,'127.0.0.1',r));
  t.after(()=>bridge.close());
  const base=`http://127.0.0.1:${bridge.server.address().port}/`;
  const mcp=(body,token=options.token,headers={})=>fetch(base+'mcp',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`,...headers},body:JSON.stringify(body)});

  assert.equal((await mcp({jsonrpc:'2.0',id:1,method:'ping'},'wrong-token-wrong-token')).status,401);
  assert.equal((await mcp({jsonrpc:'2.0',id:1,method:'ping'},options.token,{Origin:'https://evil.example'})).status,403);
  const init=await (await mcp({jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:'2025-06-18'}})).json();
  assert.equal(init.result.protocolVersion,'2025-06-18');
  const list=await (await mcp({jsonrpc:'2.0',id:2,method:'tools/list'})).json();
  assert.ok(list.result.tools.some(tool=>tool.name==='preview_scenario'));

  const noPage=await (await mcp({jsonrpc:'2.0',id:3,method:'tools/call',params:{name:'get_state',arguments:{}}})).json();
  assert.equal(noPage.result.isError,true);

  assert.throws(()=>connect({address:base,token:'short',adapter:fakeAdapter()}),/Token/);
  const statuses=[];
  const link=connect({address:base,token:options.token,adapter:fakeAdapter(),onStatus:s=>statuses.push(s)});
  t.after(()=>link.close());
  for(let i=0;i<50&&!bridge.pageConnected();i++) await new Promise(r=>setTimeout(r,20));
  assert.ok(bridge.pageConnected());

  const set=await (await mcp({jsonrpc:'2.0',id:4,method:'tools/call',params:{name:'set_assumptions',arguments:{values:{taxRate:22.2},reason:'test'}}})).json();
  assert.equal(set.result.isError,false);
  assert.deepEqual(set.result.structuredContent.set,{taxRate:22.2});
  const bad=await (await mcp({jsonrpc:'2.0',id:5,method:'tools/call',params:{name:'set_assumptions',arguments:{values:{taxRate:99}}}})).json();
  assert.equal(bad.result.isError,true);
  assert.match(bad.result.content[0].text,/mellan 19 och 24/);
  assert.ok(statuses.includes('connected'));
});
