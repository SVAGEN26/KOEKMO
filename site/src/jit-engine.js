// The dashboard's forecast engine: Motala.mo compiled in the browser by OpenModelica (wasm-jit).
// JavaScript prepares inputs and formats results; the equations live only in Motala.mo.
import {prepareScenario,baselineRow} from './scenario-inputs.js';
import {OUTPUTS} from './omc-session.js';

export const ENGINE='OpenModelica · wasm-jit';

// Validate and prepare one scenario. Throws for inputs the model must not see.
export function prepareJob(b,history,overrides={},revenuePath=null) {
  const prepared=prepareScenario(b,history,overrides,revenuePath);
  return {prepared,job:{fields:prepared.fields,years:prepared.assumptions.years,baseYear:b.baseYear,cohort:prepared.cohort,ageMigration:prepared.ageMigration,municipality:b.municipality,continuous:prepared.continuous}};
}

// Turn the simulation's annual rows into the dashboard's ledger rows.
export function assemble(b,prepared,simRows,revenuePath=null) {
  const {fields}=prepared;
  const rows=[baselineRow(b)];
  for(const row of rows) {
    row.employerContributions=fields.employerContributions0??null;
    row.wages=row.employerContributions==null?null:row.payroll-row.employerContributions;
    row.workInProgress=b.workInProgress??null;
    row.commissioned=null;
    row.tradeReceivables=b.workingCapital?.receivables??null;
    row.tradePayables=b.workingCapital?.payables??null;
    row.deferredGrants=b.workingCapital?.grantAdvances??null;
    row.workingCapitalCash=null;
  }
  simRows.forEach((r,i)=>{
    const row=Object.fromEntries(OUTPUTS.map(name=>[name,r[name]]));
    row.year=b.baseYear+i+1;
    row.cohorts=[1,2,3,4,5].map(j=>r[`p[${j}]`]);
    row.investment=r.annualInvestment;
    row.otherFinancialExpense=b.otherFinancialExpense;
    row.benchmarkRevenue=fields.referenceTax[i]+fields.referenceGrants[i];
    row.officialRevenue=revenuePath&&!revenuePath.rows.find(p=>p.year===row.year)?.projected?row.benchmarkRevenue:null;
    rows.push(row);
  });
  const {fields:_,ageMigration:__,...details}=prepared;
  return {...details,rows,engine:ENGINE};
}

// Synchronous simulator around an omc session (Node tests and scripts).
export function createDirectSimulator(session) {
  return function simulate(b,history,overrides={},revenuePath=null) {
    const {prepared,job}=prepareJob(b,history,overrides,revenuePath);
    return assemble(b,prepared,session.run(job.fields,job.years,job.baseYear,job.cohort,job.ageMigration,job.municipality,job.continuous),revenuePath);
  };
}

// Browser simulator: the compiler runs in a worker. `simulateMany` takes
// [{overrides, revenuePath}] and resolves to [{run} | {error}] in the same order.
export function createWorkerEngine({onProgress=()=>{},onCompiling=()=>{}}={}) {
  const worker=new Worker(new URL('./omc-worker.js',import.meta.url),{type:'module'});
  const pending=new Map();let nextId=1;
  let settle;
  const ready=new Promise((resolve,reject)=>{settle={resolve,reject};});
  worker.onmessage=({data})=>{
    if(data.type==='progress') onProgress(data.loaded,data.total);
    else if(data.type==='compiling') onCompiling();
    else if(data.type==='ready') settle.resolve();
    else if(data.type==='failed') settle.reject(Error(data.error));
    else if(data.type==='result') {pending.get(data.id)?.(data.results);pending.delete(data.id);}
  };
  worker.onerror=e=>settle.reject(Error(e.message||'OpenModelica-tråden avbröts.'));
  worker.postMessage({type:'init'});

  async function simulateMany(b,history,requests) {
    await ready;
    // Validate on the main thread; only valid scenarios reach the model.
    const prepared=requests.map(({overrides={},revenuePath=null})=>{
      try {return prepareJob(b,history,overrides,revenuePath);} catch(e) {return {error:e.message};}
    });
    const jobs=prepared.filter(p=>!p.error).map(p=>p.job);
    const id=nextId++;
    const results=jobs.length?await new Promise(resolve=>{pending.set(id,resolve);worker.postMessage({type:'run',id,jobs});}):[];
    let k=0;
    return prepared.map((p,i)=>{
      if(p.error) return {error:p.error};
      const r=results[k++];
      return r.error?{error:r.error}:{run:assemble(b,p.prepared,r.rows,requests[i].revenuePath??null)};
    });
  }
  async function simulate(b,history,overrides={},revenuePath=null) {
    const [r]=await simulateMany(b,history,[{overrides,revenuePath}]);
    if(r.error) throw Error(r.error);
    return r.run;
  }
  return {ready,simulateMany,simulate};
}
