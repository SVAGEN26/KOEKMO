import {DEFAULT_MUNICIPALITY,municipalities,cohortModifiers} from './municipalities.js';
// Drives OpenModelica's in-browser compiler (wasm-jit). It compiles Motala.mo once,
// then re-runs the compiled model with -override for every scenario.
// There are no forecast equations here: they live only in Motala.mo.

// Annual outputs read from the simulation, per forecast year.
export const OUTPUTS=['population','population80Plus','births','deaths','migration','cost','payroll','wages','employerContributions','pensionExpense',
  'pensionCashPayments','otherOperatingExpense','operatingRevenue','operatingCash','tradeReceivables','tradePayables','deferredGrants','workingCapitalCash',
  'depreciation','tax','grants','recurringTaxAdjustment','incomeEqualisationAdjustment','regulationPopulationAdjustment','result','debt','cash','assets','commissioned','workInProgress','interest','borrowing',
  'repayment','prefinancing','outstandingDeferredInvestment','projectPaid','projectCommissioned','projectWorkInProgress',
  'projectPlacesInUse','missingProjectPlaces','educationIndex','careIndex','populationBalance','assetBalance','cashBalance','debtBalance'];
// The wrapper around Motala.Continuous: stocks and flows in continuous time.
export const MODEL='MotalaBrowserContinuous';
export const MAX_YEARS=100;
// Continuous time is integrated with IDA, an implicit solver with its own step control; twelve values a year are
// stored. It gives the values of native OpenModelica's DASSL within 0.01 mnkr, and it also takes the flows with
// time constants of days to weeks (payment terms, the cash reserve, a project taken into use). The explicit
// Runge-Kutta solver used until November 2026 was twice as fast but does not start in OpenModelica's web compiler
// after September 2026.
export const STEPS_PER_YEAR=12;
export const CONTINUOUS_METHOD='ida';
// Simulation time is the calendar year: the wrapper starts at the 2025 accounts.
export const BASE_YEAR=2025;

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

export function createSession(omc,sources,{method=CONTINUOUS_METHOD,stepsPerYear=STEPS_PER_YEAR}={}) {
  const errors=()=>String(omc.omc_eval('getErrorString()')).trim().replace(/^"|"$/g,'');
  for(const {name,text} of sources) {
    const reply=String(omc.omc_eval(`loadString(${JSON.stringify(text)},${JSON.stringify(name)})`)).trim();
    if(reply!=='true') throw Error(`OpenModelica kunde inte läsa ${name}: ${errors()||reply}`);
  }
  const models=new Map();
  function compile(baseYear,cohort=false,observed=false,municipality=DEFAULT_MUNICIPALITY) {
    const settings=municipalities[municipality];
    if(!settings) throw Error('Kommunen saknar modellpaket.');
    const key=`${municipality}/${baseYear}/${cohort}/${observed}`;
    if(models.has(key)) return models.get(key);
    if(!Number.isInteger(baseYear)||baseYear<2020||baseYear>BASE_YEAR) throw Error('Basåret saknar modellunderlag.');
    const motala=municipality===DEFAULT_MUNICIPALITY;
    if(!motala&&!settings.firstYears.includes(baseYear+1)) throw Error('Basåret eller demografin saknar underlag för kommunen.');
    const wrapper=MODEL;
    const model=`${motala?wrapper:settings.packageName+'BrowserContinuous'}${baseYear===BASE_YEAR?'':baseYear}${cohort?'Cohort':''}${observed?'Observed':''}`;
    if(model!==wrapper) {
      const ageModel=cohort?`,
        redeclare Kommunekonomi.Continuous.CohortDemography demography(
          ${cohortModifiers(settings.packageName,baseYear)}
          ${observed?', residualMigration=zeros(2,101), observedDeltaShape=zeros(2,101), useObservedDeltaShape=false':''})`:'';
      const data=`${settings.packageName}.Data`;
      const base=`${data}.${settings.packageName.toLowerCase()}${baseYear}`;
      const olderShares=motala?`${data}.SCB.olderShares(${data}.SCB.motala${baseYear}.population)`:`${data}.olderShares${baseYear}`;
      const source=`model ${model}
        extends ${wrapper}(base=${base}, olderShares=${olderShares}${ageModel});
      end ${model};`;
      if(String(omc.omc_eval(`loadString(${JSON.stringify(source)})`)).trim()!=='true') throw Error(errors());
    }
    // Only the series the page reads are stored: writing every variable at every step costs more than the equations.
    // Besides the outputs: the population calibration the model computed (mortalityRates, residualMigration).
    const stored=JSON.stringify(`^(${[...OUTPUTS,'annualInvestment'].join('|')}|p\\[[1-5]\\]|mortalityRates\\[[1-5]\\]|residualMigration\\[[1-5]\\])$`);
    const built=String(omc.omc_eval(`buildModel(${model},startTime=${baseYear},stopTime=${baseYear+MAX_YEARS},variableFilter=${stored},numberOfIntervals=${MAX_YEARS*stepsPerYear},method="${method}")`));
    if(!built.includes(`${model}_init.xml`)) throw Error(`OpenModelica kunde inte kompilera modellen: ${errors()||built}`);
    models.set(key,model);
    return model;
  }
  compile(BASE_YEAR);

  // One simulation; returns per-year rows of OUTPUTS plus cohorts and investment.
  // inspect: {names} reruns the compiled model with every variable stored (-variableFilter=.* at simulation time, no new
  // compilation) and returns, besides the rows, the model's variables (name, comment, unit) and the named ones per year.
  function run(fields,years,baseYear=BASE_YEAR,cohort=false,ageMigration=null,municipality=DEFAULT_MUNICIPALITY,inspect=null) {
    if(!Number.isInteger(years)||years<1||years>MAX_YEARS) throw Error(`Modellen stöder 1–${MAX_YEARS} år.`);
    const model=compile(baseYear,cohort,!!ageMigration,municipality);
    // The wrapper has a hundred years of paths. The wage and price rate at a year's end depends on the next year's
    // growth: after the scenario's last year the growth stays, so that only the scenario shapes it.
    const extend=path=>[...path,...Array(MAX_YEARS-path.length).fill(path.at(-1))];
    fields={...fields,wageGrowthPath:extend(fields.wageGrowthPath),priceGrowthPath:extend(fields.priceGrowthPath)};
    // With single-year ages the 202 age stocks make IDA's Jacobian cost 20 s a run; its matrix-free linear solver takes 1.5 s.
    const solver=cohort&&method==='ida'?' -idaLS=spgmr':'';
    // The stop time is a flag of its own: the runtime does not read simulation options from -override (it warns
    // and simulates the wrapper's whole hundred years).
    const flags=`-stopTime=${baseYear+years} -override=${overrideFlags({...fields,...ageMigration})}${solver}${inspect?' -variableFilter=.*':''}`;
    if(!omc.omc_sim_start(model,`${model}_res.mat`,flags)) throw Error(`Modelica: ${errors()||'simuleringen startade inte'}`);
    let code;
    do code=omc.omc_sim_advance(10000); while(code===0);
    if(code!==1) {
      // Prefer the model's own assertion text, e.g. "wageGrowthPath … måste vara större än -1".
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
    const names=[...OUTPUTS,...[1,2,3,4,5].flatMap(j=>[`p[${j}]`,`mortalityRates[${j}]`,`residualMigration[${j}]`]),'annualInvestment'];
    const columns=Object.fromEntries(names.map(n=>[n,column(n)]));
    const rows=[];
    for(let t=1;t<=years;t++) {
      const y=baseYear+t;
      if(at[y]===undefined) throw Error(`Simuleringen saknar år ${y}`);
      const row={};
      for(const n of names) {
        const c=columns[n],v=c.length===1?c[0]:c[at[y]];
        if(!Number.isFinite(v)) throw Error(`Modelica gav ett ogiltigt värde för ${n}.`);
        row[n]=v;
      }
      rows.push(row);
    }
    if(!inspect) return rows;
    const catalogue=series.filter(s=>!s.constant).map(s=>({name:s.name,comment:s.comment??'',unit:s.unit??''}));
    const picked={};
    for(const n of inspect.names??[]) {
      if(!index.has(n)) continue;
      const c=column(n);
      picked[n]=Array.from({length:years+1},(_,t)=>{const i=at[baseYear+t];return c.length===1?c[0]:c[i];});  // base year first
    }
    return {rows,inspect:{catalogue,picked}};
  }
  return {run};
}
