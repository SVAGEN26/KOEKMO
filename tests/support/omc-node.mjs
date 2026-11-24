// The staged OpenModelica web compiler (site/omc-web, scripts/stage_omc.py) running in Node, with the
// library and every municipality loaded: the same session the page's worker creates.
import fs from 'node:fs';
import {createSession} from '../../site/src/omc-session.js';
import {DEFAULT_MUNICIPALITY,municipalities} from '../../site/src/municipalities.js';

const url=path=>new URL(path,import.meta.url);
export const read=path=>JSON.parse(fs.readFileSync(url(`../../${path}`)));
export const staged=fs.existsSync(url('../../site/omc-web/omc/OpenModelicaCompiler_bg.wasm'));
export const skip=!staged&&'OpenModelica web compiler not staged (scripts/stage_omc.py)';

export async function boot(options) {
  globalThis.__omcWasmBlob=file=>{try{return new Uint8Array(fs.readFileSync(url(`../../site/omc-web/wasm-blobs/${file}`)));}catch{return null;}};
  const omc=await import('../../site/omc-web/omc/OpenModelicaCompiler.js');
  await omc.default({module_or_path:fs.readFileSync(url('../../site/omc-web/omc/OpenModelicaCompiler_bg.wasm'))});
  omc.omc_set_env('OPENMODELICAHOME','/usr');
  if(!omc.omc_init()) throw Error('OpenModelica did not start');
  omc.omc_enable_wasm_blobs?.();
  const names=['Kommunekonomi.mo','Motala.mo','MotalaBrowser.mo',...Object.entries(municipalities)
    .filter(([code])=>code!==DEFAULT_MUNICIPALITY).map(([,item])=>`municipalities/${item.packageName}.mo`)];
  const session=createSession(omc,names.map(name=>({name,text:fs.readFileSync(url(`../../modelica/${name}`),'utf8')})),options);
  return {omc,session};
}

// Build and run a model as written, and return the named series at each whole year (the value after the year's events).
export function runModel(omc,model,{start,stop,intervals,method},names) {
  const built=String(omc.omc_eval(`buildModel(${model},startTime=${start},stopTime=${stop},numberOfIntervals=${intervals},method="${method}")`));
  if(!built.includes(`${model}_init.xml`)) throw Error(String(omc.omc_eval('getErrorString()'))||built);
  if(!omc.omc_sim_start(model,`${model}_res.mat`,'')) throw Error('simulation did not start');
  let code;
  do code=omc.omc_sim_advance(10000); while(code===0);
  if(code!==1) throw Error(String(omc.omc_sim_log()??'simulation failed'));
  const time=omc.omc_sim_time(),index=new Map(omc.omc_sim_series().map((s,i)=>[s.name,i])),at=[];
  for(let i=0;i<time.length;i++) {const y=Math.round(time[i]);if(Math.abs(time[i]-y)<1e-9) at[y]=i;}
  const rows=[];
  for(let y=start+1;y<=stop;y++) rows.push({year:y,...Object.fromEntries(names.map(n=>{
    const c=omc.omc_sim_column(index.get(n));
    return [n,c.length===1?c[0]:c[at[y]]];
  }))});
  return rows;
}
