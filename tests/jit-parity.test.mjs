// The site compiles Motala.mo in the browser with OpenModelica (wasm-jit). This runs the
// same staged compiler in Node and checks it against engine.js, the independent reference.
// Needs site/omc-web (scripts/stage_omc.py); skipped when the compiler is not staged.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {simulate as reference} from '../site/src/engine.js';
import {createSession} from '../site/src/omc-session.js';
import {createDirectSimulator,prepareJob} from '../site/src/jit-engine.js';

const url=path=>new URL(path,import.meta.url);
const read=path=>JSON.parse(fs.readFileSync(url(path)));
const staged=fs.existsSync(url('../site/omc-web/omc/OpenModelicaCompiler_bg.wasm'));

let session,simulate;
if(staged) {
  globalThis.__omcWasmBlob=file=>{try{return new Uint8Array(fs.readFileSync(url(`../site/omc-web/wasm-blobs/${file}`)));}catch{return null;}};
  const omc=await import('../site/omc-web/omc/OpenModelicaCompiler.js');
  await omc.default({module_or_path:fs.readFileSync(url('../site/omc-web/omc/OpenModelicaCompiler_bg.wasm'))});
  omc.omc_set_env('OPENMODELICAHOME','/usr');
  assert.ok(omc.omc_init());
  omc.omc_enable_wasm_blobs?.();
  session=createSession(omc,['Motala.mo','MotalaBrowser.mo'].map(name=>({name,text:fs.readFileSync(url(`../modelica/${name}`),'utf8')})));
  simulate=createDirectSimulator(session);
}
const skip=!staged&&'OpenModelica web compiler not staged (scripts/stage_omc.py)';

const b=read('../data/baseline.json'),{rows:history}=read('../data/history.json'),planning=read('../data/planning-inputs.json');
const keys=['population','births','deaths','migration','cost','payroll','pensionExpense','pensionCashPayments',
  'otherOperatingExpense','operatingRevenue','operatingCash','depreciation','tax','grants','result','debt','cash',
  'assets','interest','borrowing','repayment','educationIndex','careIndex','investment','benchmarkRevenue'];
const scenarios=[{},
  {taxGrowth:2.5,wageGrowth:4,priceGrowth:3,interestRate:4,migrationDelta:-100},
  {migrationDelta:300,investment:250,productivity:0.5,taxRate:22.2},
  {investment:0,interestRate:0},
  {birthChange:-30,migrationDelta:-400,adjustment:1,equalisationOffset:1},
  {years:3},
  {pensionExpensePath:[275,250,220,190,190,190,190,190],pensionCashPaymentsPath:[190,195,200,200,200,200,200,200]}];

for(const sourced of [true,false]) for(const overrides of scenarios) {
  test(`wasm-jit matches the JS reference: ${sourced?'sourced':'illustrative'} ${JSON.stringify(overrides)}`,{skip},()=>{
    const baseline={...b,planningInputs:sourced?planning:null},path=sourced?planning.revenuePath??null:null;
    const expected=reference(baseline,history,overrides,path),actual=simulate(baseline,history,overrides,path);
    assert.equal(actual.rows.length,expected.rows.length);
    expected.rows.slice(1).forEach((row,i)=>{
      const got=actual.rows[i+1];
      for(const k of keys) assert.ok(Math.abs(got[k]-row[k])<=1e-8*Math.max(1,Math.abs(row[k])),`${row.year} ${k}: wasm-jit ${got[k]} vs js ${row[k]}`);
      row.cohorts.forEach((x,j)=>assert.ok(Math.abs(got.cohorts[j]-x)<=1e-8*Math.max(1,x),`${row.year} cohort ${j+1}`));
    });
  });
}

test('the model rejects an invalid year path through its own assertion, and the session survives',{skip},()=>{
  const {job}=prepareJob({...b,planningInputs:planning},history,{},planning.revenuePath);
  job.fields.wageGrowthPath[0]=-1;
  assert.throws(()=>session.run(job.fields,job.years),/wageGrowthPath/);
  const ok=prepareJob({...b,planningInputs:planning},history,{},planning.revenuePath).job;
  assert.equal(session.run(ok.fields,ok.years).length,8);
});
