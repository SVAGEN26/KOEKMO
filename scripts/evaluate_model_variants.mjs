// Compare fixed, pre-specified variants in the same WASM model as the web app.
import fs from 'node:fs';
import {createSession} from '../site/src/omc-session.js';
import {createDirectSimulator} from '../site/src/jit-engine.js';
import {sum} from '../site/src/scenario-inputs.js';

const file=path=>new URL('../'+path,import.meta.url);
const read=path=>JSON.parse(fs.readFileSync(file(path)));
const compiler='site/omc-web/omc';
const omc=await import('../'+compiler+'/OpenModelicaCompiler.js');
globalThis.__omcWasmBlob=name=>{
  try { return new Uint8Array(fs.readFileSync(file('site/omc-web/wasm-blobs/'+name))); }
  catch { return null; }
};
await omc.default({module_or_path:fs.readFileSync(file(compiler+'/OpenModelicaCompiler_bg.wasm'))});
omc.omc_set_env('OPENMODELICAHOME','/usr');
if(!omc.omc_init()) throw Error('OpenModelica could not start');
omc.omc_enable_wasm_blobs?.();
const sources=['Kommunekonomi/package.mo','Kommunekonomi/Municipalities/package.mo','Kommunekonomi/Municipalities/Motala.mo','Browser.mo'].map(name=>({name,text:fs.readFileSync(file('modelica/'+name),'utf8')}));
const simulate=createDirectSimulator(createSession(omc,sources));

const replay=read('data/replay-2022.json');
const experiments=read('data/model-experiments.json');
const inputs=experiments.municipalities['0583'];
const ageIncome=read('data/age-income.json');
const municipal=read('data/municipalities/0583/base-years.json');
const ledgers=read('research/data/annual-ledgers.json');
const budgets=read('research/benchmark/municipal-budget-history.json');
const tax=read('research/data/skr-tax-vintages.json').vintages;
const prices=read('research/data/skr-pkv-vintages.json').vintages;
const revenue=read('research/data/skr-revenue-vintages.json').vintages;
const national=read('data/national-population.json').population;
const demographicOutcomes=read('data/demography-inputs.json').observed.population;
const variants={
  original:{},
  splitPayroll:{splitPayroll:true},
  observedMigration:{demographyMode:'observed'},
  singleYearAges:{demographyMode:'cohort'},
  singleYearObserved:{demographyMode:'cohort-observed'},
  combined:{splitPayroll:true,demographyMode:'cohort-observed'}
};
const replayVariants={...variants,combined:{...variants.combined,revenueMode:2},
  skrDirect:{revenueMode:1},skrComponents:{revenueMode:2},skrAgeIncome:{revenueMode:2,ageTax:true}};

function observations(year) {
  const accounts=ledgers.rows.find(row=>row.year===year);
  const actual=inputs[year];
  return {tax:accounts.tax,grants:accounts.grants,result:accounts.result,
    cost:accounts.netCost-accounts.depreciation, population:municipal.years[year].reportedPopulation.at(-1),
    schoolAge:municipal.years[year].cohorts.at(-1)[1],
    elderly:sum(['1','2'].flatMap(sex=>demographicOutcomes[year][sex].slice(80))),
    wages:actual.wages,employerContributions:actual.employerContributions,
    payroll:actual.wages+actual.employerContributions,
    source:ledgers.sources[accounts.sourceId].url};
}
function measuredRow(origin,row,reference) {
  const budget=budgets.budgets.find(b=>b.stage==='budget'&&b.targetYear===row.year);
  const keys=['tax','grants','result','cost','population','wages','employerContributions','payroll','migration','educationIndex','careIndex'];
  const model={...Object.fromEntries(keys.map(key=>[key,row[key]])),schoolAge:row.cohorts[1],elderly:row.population80Plus};
  return {origin,year:row.year,horizon:row.year-origin,model,
    observed:observations(row.year),
    budget:row.year===origin+1&&budget?{result:budget.value,source:budgets.sources[budget.sourceId].url}:null,
    skr:reference?{tax:reference.tax,grants:reference.grants}:null};
}
const local={};
for(const [name,overrides] of Object.entries(replayVariants)) {
  const origin=2021;
  const base={...replay.baseline,planningInputs:replay.planning,
    ageIncome:{weights:ageIncome.municipalities['0583']['2019'],countyRate:ageIncome.countyRate},
    experiments:{...inputs[origin],novemberPopulation:replay.novemberPopulation.rows.find(r=>r.year===origin).population}};
  const path=replay.planning.revenuePath;
  local[name]=simulate(base,replay.history,{years:4,...overrides},path).rows.slice(1)
    .map(row=>measuredRow(origin,row,path.rows.find(r=>r.year===row.year)));
}

const rolling=Object.fromEntries(Object.keys(variants).map(name=>[name,[]]));
for(let origin=2020;origin<=2024;origin++) {
  const years=Math.min(3,2025-origin);
  const historic=municipal.years[origin];
  const taxVintage=tax.find(row=>row.originYear===origin);
  const priceVintage=prices.find(row=>row.originYear===origin);
  const revenueVintage=revenue.find(row=>row.originYear===origin);
  if(taxVintage.circular!==priceVintage.circular||taxVintage.circular!==revenueVintage.circular) throw Error('Mismatched vintages');
  const pkv=priceVintage.rows.filter(row=>row.year>origin).slice(0,years);
  const rows=pkv.map(row=>({year:row.year,labourCostGrowth:row.laborPercent,
    otherPriceGrowth:row.otherPercent,taxBaseGrowth:taxVintage.rows.find(t=>t.year===row.year).taxBasePercent}));
  const n=year=>revenueVintage.rows.find(row=>row.year===year).nationalNovemberPopulation;
  const nationalPopulation={population:{[origin-1]:national[origin-1],...Object.fromEntries(rows.map(row=>{
    const year=row.year-1;
    return [year,national[origin]*n(year)/n(origin)];
  }))}};
  const cashCost=historic.payroll+historic.pension+historic.otherOperatingExpense-historic.operatingRevenue;
  const historicLedger=ledgers.rows.find(r=>r.year===origin);
  const baseline={...replay.baseline,...historic,baseYear:origin,nationalPopulation,cashCost,publishedResult:historicLedger.result,
    population:historic.cohorts.at(-1), births:historic.births.at(-1), experiments:inputs[origin],
    assumptions:{...replay.baseline.assumptions,years,taxRate:historic.taxRate,investment:historic.investment,
      interestRate:100*historic.interestExpense/historic.openingDebt,
      educationWeights:historic.educationShares.map(x=>x/sum(historic.educationShares)),
      sectorCosts:historic.sectorShares.map(x=>x*cashCost/sum(historic.sectorShares))},
    operatingAccounts:{payrollExcludingPensions:historic.payroll,pensionExpense:historic.pension,
      otherOperatingExpense:historic.otherOperatingExpense,operatingRevenue:historic.operatingRevenue,netCostRoundingAdjustment:0},
    planningInputs:{municipality:'0583',baseYear:origin,demography:'calibrated',rows}};
  const history=historic.cohorts.map((population,i)=>({year:origin+i-2,population,reportedTotal:historic.reportedPopulation[i],
    births:historic.births[i-1],deaths:historic.deaths}));
  for(const [name,overrides] of Object.entries(variants)) {
    const run=simulate(baseline,history,overrides);
    rolling[name].push(...run.rows.slice(1).map(row=>measuredRow(origin,row)));
  }
}
function scores(cases) {
  const keys=['tax','grants','revenue','cost','payroll','result','population','schoolAge','elderly'];
  const score={cases:cases.length};
  for(const key of keys) {
    const errors=cases.map(({model,observed})=>Math.abs(key==='revenue'
      ?model.tax+model.grants-observed.tax-observed.grants
      :model[key]-observed[key]));
    score[key]=sum(errors)/cases.length;
  }
  return score;
}
const summary={
  local:Object.fromEntries(Object.entries(local).map(([name,cases])=>[name,scores(cases)])),
  rolling:Object.fromEntries(Object.entries(rolling).map(([name,cases])=>[name,Object.fromEntries([1,2,3].map(h=>
    [h,scores(cases.filter(r=>r.horizon===h))]))]))
};
const budgetCases=rolling.original.filter(row=>row.budget);
summary.budgetOneYear={cases:budgetCases.length,result:sum(budgetCases.map(row=>Math.abs(row.budget.result-row.observed.result)))/budgetCases.length};
const planning=read('data/planning-inputs.json');
const baseline={...read('data/baseline.json'),planningInputs:planning,
  experiments:{...inputs[2025],novemberPopulation:replay.novemberPopulation.rows.find(row=>row.year===2025).population}};
const history=read('data/history.json').rows;
const options={revenueMode:2,demographyMode:'cohort-observed'};
const ordinary=simulate(baseline,history,options,planning.revenuePath);
const increased=simulate(baseline,history,{...options,migrationDelta:100},planning.revenuePath);
const sensitivity=increased.rows.slice(1).map((row,i)=>({
  year:row.year,
  ...Object.fromEntries(['population','population80Plus','tax','grants','educationIndex','careIndex','cost','result'].map(key=>[key,row[key]-ordinary.rows[i+1][key]]))
}));
const notes=[
  'Local test: 2021 closing accounts plus the September 2021 Motala SKR workbook, verified against the 2022–2025 closing accounts. The closing accounts postdate the workbook.',
  'Rolling test: Motala 2020–2024 closing accounts and the respective December national SKR projection; no local SKR reference in this test. Compare with the adopted budget when available.',
  'The split payroll variant assumes nominal wage growth of 3% and a fixed contribution ratio. The comparison reflects this assumption as well as detaching wages from the labour cost index.',
  'Both single-year-age variants use the five latest observed fertility years at each origin. Observed migration uses only the latest three years available in the 2017–2024 historical series.',
  'Outcomes and budgets are read after simulation; no variant is selected or tuned from these errors. Demographic outcomes are SCB year-end totals.',
  'Figures in mnkr, population in people. Errors are mean absolute errors.'
];
const report={municipality:'0583',notes,sources:experiments.sources,summary,local,rolling,
  sensitivity:{assumptions:options,migrationDelta:100,rows:sensitivity}};
if(process.argv[2]) fs.writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n');
console.table(summary.local);
console.table(Object.fromEntries(Object.entries(summary.rolling).map(([name,rows])=>[name,rows[1]])));
