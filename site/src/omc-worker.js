import {municipalities} from './municipalities.js';
// Module worker hosting OpenModelica's in-browser compiler, so compiling and
// simulating never block the page. Protocol:
//   → {type:'init'}                     ← {type:'progress', loaded, total} … {type:'ready'} | {type:'failed', error}
//   → {type:'run', id, jobs:[{fields, years, baseYear, …, inspect?}]}
//   ← {type:'runProgress', id, done, total, compiling} before each job and once all are done
//   ← {type:'result', id, results:[{rows, inspect?} | {error}]}
import init,* as omc from './omc-web/omc/OpenModelicaCompiler.js';
import {createSession} from './omc-session.js';

const base=new URL('./',import.meta.url);
let session=null;

// omc asks for wasm side modules synchronously from inside a call; a worker may use sync XHR.
globalThis.__omcWasmBlob=file=>{
  const xhr=new XMLHttpRequest();
  xhr.open('GET',new URL(`omc-web/wasm-blobs/${file}`,base),false);
  xhr.responseType='arraybuffer';
  try {xhr.send();} catch {return null;}
  return xhr.status===200&&xhr.response?new Uint8Array(xhr.response):null;
};

async function download(url) {
  const response=await fetch(url);
  if(!response.ok) throw Error(`Kunde inte hämta ${url.pathname.split('/').pop()} (HTTP ${response.status})`);
  const total=Number(response.headers.get('content-length'))||0,reader=response.body.getReader(),chunks=[];
  let loaded=0;
  for(;;) {
    const {done,value}=await reader.read();
    if(done) break;
    chunks.push(value);loaded+=value.length;
    self.postMessage({type:'progress',loaded,total});
  }
  const bytes=new Uint8Array(loaded);let offset=0;
  for(const c of chunks){bytes.set(c,offset);offset+=c.length;}
  return bytes;
}

async function start() {
  const wasm=await download(new URL('omc-web/omc/OpenModelicaCompiler_bg.wasm',base));
  self.postMessage({type:'compiling'});
  await init({module_or_path:wasm});
  omc.omc_set_env('OPENMODELICAHOME','/usr');
  if(!omc.omc_init()) throw Error('OpenModelica kunde inte starta.');
  omc.omc_enable_wasm_blobs?.();
  const sources=await Promise.all(['Kommunekonomi.mo',...Object.values(municipalities).map(item=>item.packageName+'.mo'),'MotalaBrowser.mo'].map(async name=>{
    const r=await fetch(new URL(name,base));
    if(!r.ok) throw Error(`Kunde inte läsa ${name}`);
    return {name,text:await r.text()};
  }));
  session=createSession(omc,sources);
}

self.onmessage=async({data})=>{
  if(data.type==='init') {
    try {await start();self.postMessage({type:'ready'});}
    catch(e) {self.postMessage({type:'failed',error:e.message});}
    return;
  }
  if(data.type==='run') {
    const total=data.jobs.length;
    const results=data.jobs.map((job,i)=>{
      self.postMessage({type:'runProgress',id:data.id,done:i,total,compiling:!session.isCompiled(job.baseYear,job.cohort,!!job.ageMigration,job.municipality)});
      try {
        const out=session.run(job.fields,job.years,job.baseYear,job.cohort,job.ageMigration,job.municipality,job.inspect??null);
        return job.inspect?out:{rows:out};
      }
      catch(e) {return {error:e.message};}
    });
    self.postMessage({type:'runProgress',id:data.id,done:total,total,compiling:false});
    self.postMessage({type:'result',id:data.id,results});
  }
};
