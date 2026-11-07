// Drives OpenModelica's in-browser compiler (wasm-jit). It compiles Motala.mo once,
// then re-runs the compiled model with -override for every scenario.
// There are no forecast equations here: they live only in Motala.mo.

// Annual outputs read from the simulation, per forecast year.
export const OUTPUTS=['population','births','deaths','migration','cost','payroll','pensionExpense',
  'pensionCashPayments','otherOperatingExpense','operatingRevenue','operatingCash',
  'depreciation','tax','grants','result','debt','cash','assets','interest','borrowing',
  'repayment','educationIndex','careIndex','populationBalance','assetBalance','cashBalance','debtBalance'];
export const MODEL='MotalaBrowser';
export const MAX_YEARS=30;

// fields: {name: number | boolean | nested arrays} → "name=…,name[i]=…,name[i,j]=…"
export function overrideFlags(fields) {
  const parts=[];
  const add=(name,value,indices=[])=>{
    if(Array.isArray(value)) {value.forEach((v,i)=>add(name,v,[...indices,i+1]));return;}
    if(typeof value!=='boolean'&&!Number.isFinite(value)) throw Error(`Ogiltigt värde för ${name}`);
    parts.push(`${indices.length?`${name}[${indices.join(',')}]`:name}=${value}`);
  };
  for(const [name,value] of Object.entries(fields)) add(name,value);
  return parts.join(',');
}

export function createSession(omc,sources) {
  const errors=()=>String(omc.omc_eval('getErrorString()')).trim().replace(/^"|"$/g,'');
  for(const {name,text} of sources) {
    const reply=String(omc.omc_eval(`loadString(${JSON.stringify(text)},${JSON.stringify(name)})`)).trim();
    if(reply!=='true') throw Error(`OpenModelica kunde inte läsa ${name}: ${errors()||reply}`);
  }
  const built=String(omc.omc_eval(`buildModel(${MODEL},stopTime=${MAX_YEARS},numberOfIntervals=${MAX_YEARS},method="euler")`));
  if(!built.includes(`${MODEL}_init.xml`)) throw Error(`OpenModelica kunde inte kompilera modellen: ${errors()||built}`);

  // One simulation; returns per-year rows of OUTPUTS plus cohorts and investment.
  function run(fields,years) {
    if(!Number.isInteger(years)||years<1||years>MAX_YEARS) throw Error(`Modellen stöder 1–${MAX_YEARS} år.`);
    const flags=`-override=stopTime=${years},${overrideFlags(fields)}`;
    if(!omc.omc_sim_start(MODEL,`${MODEL}_res.mat`,flags)) throw Error(`Modelica: ${errors()||'simuleringen startade inte'}`);
    let code;
    do code=omc.omc_sim_advance(10000); while(code===0);
    if(code!==1) {
      // Prefer the model's own assertion text, e.g. "wageGrowthPath … must exceed -1".
      const text=`${errors()}\n${String(omc.omc_sim_log()??'')}`;
      const message=text.match(/Error:\s*([^\n[]+)/)?.[1]??text.match(/assert[^\n]*\|\s*([^\n]+)/i)?.[1];
      throw Error(`Modelica: ${(message??'beräkningen avbröts').trim().slice(0,300)}`);
    }
    const time=omc.omc_sim_time(),series=omc.omc_sim_series(),index=new Map(series.map((s,i)=>[s.name,i]));
    const column=name=>{
      const i=index.get(name);
      if(i===undefined) throw Error(`Simuleringen saknar ${name}`);
      return omc.omc_sim_column(i);
    };
    // The last row at each whole year is the post-event state.
    const at=[];
    for(let i=0;i<time.length;i++) {const y=Math.round(time[i]);if(Math.abs(time[i]-y)<1e-9)at[y]=i;}
    const names=[...OUTPUTS,...[1,2,3,4,5].map(j=>`p[${j}]`),'annualInvestment'];
    const columns=Object.fromEntries(names.map(n=>[n,column(n)]));
    const rows=[];
    for(let t=1;t<=years;t++) {
      if(at[t]===undefined) throw Error(`Simuleringen saknar år ${t}`);
      const row={};
      for(const n of names) {
        const c=columns[n],v=c.length===1?c[0]:c[at[t]];
        if(!Number.isFinite(v)) throw Error(`Modelica gav ett ogiltigt värde för ${n}.`);
        row[n]=v;
      }
      rows.push(row);
    }
    return rows;
  }
  return {run};
}
