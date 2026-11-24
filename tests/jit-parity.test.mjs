// The site compiles Motala.mo in the browser with OpenModelica (wasm-jit). This runs the
// same staged compiler in Node and checks it against engine.js, the independent reference.
// Needs site/omc-web (scripts/stage_omc.py); skipped when the compiler is not staged.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {simulate as reference} from '../site/src/engine.js';
import {boot,staged,skip} from './support/omc-node.mjs';
import {createDirectSimulator,prepareJob} from '../site/src/jit-engine.js';
import {extendPlanning} from '../site/src/scenario-inputs.js';
import {modelicaSource} from '../site/src/modelica-adapter.js';
import {municipalities} from '../site/src/municipalities.js';

const url=path=>new URL(path,import.meta.url);
const read=path=>JSON.parse(fs.readFileSync(url(path)));

let session,simulate;
if(staged) {
  ({session}=await boot());
  simulate=createDirectSimulator(session);
}

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
  {costDrift:0.8,grantIncrease:4},
  {costDrift:-0.5,grantIncrease:-2,years:5},
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

test('switching the base year keeps the calendar and financial inputs aligned',{skip},()=>{
  const replay=read('../data/replay-2022.json');
  const historical={...replay.baseline,planningInputs:replay.planning};
  const path=replay.planning.revenuePath;
  const forecast=simulate(historical,replay.history,{},path);
  assert.deepEqual(forecast.rows.map(r=>r.year),[2021,2022,2023,2024,2025,2026]);
  const expected=reference(historical,replay.history,{},path);
  for(const [i,row] of forecast.rows.slice(1).entries()) {
    for(const key of keys) assert.ok(Math.abs(row[key]-expected.rows[i+1][key])<1e-6,`${row.year} ${key}`);
  }
  const short=simulate(historical,replay.history,{years:1},path);
  assert.deepEqual(short.rows,forecast.rows.slice(0,2));
  const source=modelicaSource(historical,replay.history,{},path);
  assert.match(source,/base=Motala.Data.motala2021/);
  assert.match(source,/StartTime=2021, StopTime=2026/);

  const extended=extendPlanning(planning,2055);
  const modern=simulate({...b,planningInputs:extended},history,{years:30},extended.revenuePath);
  assert.equal(modern.rows.at(-1).year,2055);
  assert.deepEqual(modern.rows.slice(0,9),simulate({...b,planningInputs:planning},history,{},planning.revenuePath).rows);
  assert.ok(modern.rows[8].officialRevenue>0);
  assert.equal(modern.rows[9].officialRevenue,null);
});

test('optional mechanisms preserve the accounting identities and use the selected inputs',{skip},()=>{
  const replay=read('../data/replay-2022.json');
  const sources=read('../data/model-experiments.json');
  const baseline={...replay.baseline,planningInputs:replay.planning,
    experiments:{...sources.municipalities['0583']['2021'],novemberPopulation:43647}};
  const path=replay.planning.revenuePath;
  const direct=simulate(baseline,replay.history,{revenueMode:1},path);
  const components=simulate(baseline,replay.history,{revenueMode:2},path);
  for(const [i,row] of direct.rows.slice(1).entries()) {
    assert.ok(Math.abs(row.tax-path.rows[i].tax)<1e-7);
    assert.ok(Math.abs(row.grants-path.rows[i].grants)<1e-7);
  }
  const ref=path.rows[0],ratio=43647/ref.population;
  assert.ok(Math.abs(components.rows[1].tax-ref.tax-ref.components.recurringTax*(ratio-1))<1e-8);
  assert.ok(Math.abs(components.rows[1].grants-ref.grants-(ref.components.incomeEqualisation+ref.components.regulation)*(ratio-1))<1e-8);
  const pay=simulate(baseline,replay.history,{splitPayroll:true,employerContributionRate:32},path).rows[1];
  assert.ok(Math.abs(pay.payroll-pay.wages-pay.employerContributions)<1e-8);
  assert.ok(Math.abs(pay.employerContributions/pay.wages-0.32)<1e-8);
  const observed=simulate(baseline,replay.history,{years:2,demographyMode:'cohort-observed'},path);
  const calibrated=simulate(baseline,replay.history,{years:2,demographyMode:'cohort'},path);
  const extra=simulate(baseline,replay.history,{years:2,demographyMode:'cohort-observed',migrationDelta:100},path);
  for(const row of observed.rows.slice(1)) assert.ok(Math.abs(row.populationBalance)<1e-8);
  assert.notEqual(observed.rows[1].population,calibrated.rows[1].population);
  assert.ok(Math.abs(extra.rows[1].migration-observed.rows[1].migration-100)<0.1);
});

test('construction delays depreciation while payments still finance the investment',{skip},()=>{
  const baseline={...b,planningInputs:planning};
  const baseRun=simulate(baseline,history,{years:4,investment:200},planning.revenuePath).rows;
  const delayed=simulate(baseline,history,{years:4,investment:200,constructionYears:2,constructionShare:0.5},planning.revenuePath).rows;
  assert.equal(delayed[0].workInProgress,99);
  for(const [i,expected] of [[1,149.5],[2,149.5],[3,200],[4,200]]) {
    // The opening 99 mnkr matures in equal shares in years one and two.
    const row=delayed[i],previous=delayed[i-1];
    assert.equal(row.commissioned,expected);
    assert.ok(Math.abs(row.workInProgress-(previous.workInProgress+200-expected))<1e-8);
    assert.ok(Math.abs(row.assetBalance)<1e-8);
    for(const key of ['cash','debt','interest','operatingCash']) assert.ok(Math.abs(row[key]-baseRun[i][key])<1e-8,key);
  }
  assert.ok(delayed[1].depreciation<baseRun[1].depreciation);
  const noBuild=simulate(baseline,history,{years:1,investment:200,constructionYears:2,constructionShare:0},planning.revenuePath).rows[1];
  assert.equal(noBuild.workInProgress,49.5);
  assert.equal(noBuild.commissioned,249.5);
});

test('prefinancing carries the deferred payment across year-end and charges interest on opening debt',{skip},()=>{
  const baseline={...b,planningInputs:planning};
  const opts={years:3,investment:400,liquidityPolicy:true,cashReserve:40,deferInvestmentShare:0.5};
  const without=simulate(baseline,history,opts,planning.revenuePath).rows;
  const withLoan=simulate(baseline,history,{...opts,prefinanceShare:1},planning.revenuePath).rows;
  assert.deepEqual(withLoan.slice(1).map(row=>row.investment),[200,600,400]);
  assert.deepEqual(withLoan.slice(1).map(row=>row.outstandingDeferredInvestment),[200,0,0]);
  assert.deepEqual(withLoan.slice(1).map(row=>row.prefinancing),[200,0,0]);
  for(const key of ['cash','debt','borrowing']) assert.ok(Math.abs(withLoan[1][key]-without[1][key]-200)<1e-8,key);
  assert.equal(withLoan[1].interest,without[1].interest);
  assert.ok(Math.abs(withLoan[2].interest-without[2].interest-200*b.assumptions.interestRate/100)<1e-8);
  for(const row of withLoan.slice(1)) {
    assert.ok(row.cash>=40-1e-8);
    for(const key of ['cashBalance','debtBalance','assetBalance']) assert.ok(Math.abs(row[key])<1e-8,key);
  }
  const short=simulate(baseline,history,{...opts,years:1,prefinanceShare:1},planning.revenuePath).rows;
  assert.deepEqual(short,withLoan.slice(0,2));
});

test('working capital moves cash at payment time and preserves the accrual result',{skip},()=>{
  const baseline={...b,planningInputs:planning};
  const opts={years:2,workingCapitalEnabled:true,collectionDays:30,paymentDays:35};
  const ordinary=simulate(baseline,history,opts,planning.revenuePath).rows;
  const advance=simulate(baseline,history,{...opts,firstYearGrantAdvance:100},planning.revenuePath).rows;
  assert.equal(advance[0].deferredGrants,29);
  assert.deepEqual(advance.slice(1).map(r=>r.deferredGrants),[100,0]);
  assert.equal(advance[1].result,ordinary[1].result);
  const close=(actual,expected)=>assert.ok(Math.abs(actual-expected)<1e-7,`${actual} vs ${expected}`);
  close(advance[1].operatingCash-ordinary[1].operatingCash,100);
  close(advance[2].workingCapitalCash-ordinary[2].workingCapitalCash,-100);
  for(const [i,r] of advance.slice(1).entries()) {
    const p=advance[i];
    close(r.tradeReceivables,r.operatingRevenue*30/365);
    close(r.tradePayables,r.otherOperatingExpense*35/365);
    close(r.workingCapitalCash,(p.tradeReceivables-r.tradeReceivables)+(r.tradePayables-p.tradePayables)+(r.deferredGrants-p.deferredGrants));
    close(r.operatingCash,r.result+r.depreciation+r.pensionExpense-r.pensionCashPayments+r.workingCapitalCash);
    close(r.cashBalance,0);
    close(r.debtBalance,0);
  }
});

test('equally large migration scenarios move tax and equalisation in opposite directions',{skip},()=>{
  const source=read('../data/age-income.json');
  const baseline={...b,planningInputs:planning,experiments:{novemberPopulation:43158},
    ageIncome:{weights:source.municipalities['0583']['2024'],countyRate:source.countyRate}};
  const opts={years:2,revenueMode:2,ageTax:true,migrationDelta:100};
  const working=simulate(baseline,history,{...opts,migrationProfile:'working'},planning.revenuePath).rows;
  const older=simulate(baseline,history,{...opts,migrationProfile:'older'},planning.revenuePath).rows;
  assert.ok(Math.abs(working[1].population-older[1].population)<1e-7);
  assert.equal(working[1].tax,older[1].tax);
  assert.ok(working[2].tax>older[2].tax);
  assert.ok(working[2].grants<older[2].grants);
  assert.ok(working[2].careIndex<older[2].careIndex);
  const taxDelta=working[2].tax-older[2].tax,grantDelta=working[2].grants-older[2].grants;
  assert.ok(Math.abs(grantDelta+taxDelta*source.countyRate/b.taxRate)<1e-7);
});

test('project timing defers commissioning and capacity but preserves the payment',{skip},()=>{
  const baseline={...b,planningInputs:planning};
  const planned=simulate(baseline,history,{years:2,projectChoice:'planned'},planning.revenuePath).rows;
  const delayed=simulate(baseline,history,{years:2,projectChoice:'delay'},planning.revenuePath).rows;
  assert.deepEqual(planned.slice(1).map(r=>r.projectPaid),[4,0]);
  assert.deepEqual(delayed.slice(1).map(r=>r.projectPaid),[4,0]);
  assert.deepEqual(planned.slice(1).map(r=>r.projectCommissioned),[65,0]);
  assert.deepEqual(delayed.slice(1).map(r=>r.projectCommissioned),[0,65]);
  assert.deepEqual(delayed.slice(1).map(r=>r.projectWorkInProgress),[65,0]);
  assert.deepEqual(delayed.slice(1).map(r=>r.projectPlacesInUse),[0,144]);
  assert.deepEqual(delayed.slice(1).map(r=>r.missingProjectPlaces),[144,0]);
  for(const [i,r] of delayed.slice(1).entries()) {
    assert.ok(Math.abs(r.assetBalance)<1e-8);
    assert.ok(Math.abs(r.debt-planned[i+1].debt)<1e-8);
  }
  assert.ok(delayed[1].depreciation<planned[1].depreciation);
});


test('Finspång uses its own base year, reacts to migration, and keeps the Motala model isolated',{skip},()=>{
  const {baseline,history:localHistory,skrRevenue}=read('../data/municipalities/0562/web.json');
  const base=simulate(baseline,localHistory,{years:3});
  const alternative=simulate(baseline,localHistory,{years:3,migrationDelta:300,splitPayroll:true,constructionYears:2});
  assert.ok(Math.abs(base.rows[0].population-21502)<1e-8);
  assert.equal(base.rows[0].debt,1777);
  assert.equal(base.rows.at(-1).year,2028);
  assert.equal(alternative.rows[0].workInProgress,50);
  assert.ok(Math.abs(alternative.rows[1].population-base.rows[1].population-300)<1e-8);
  for(const name of ['populationBalance','assetBalance','cashBalance','debtBalance']) {
    assert.ok(alternative.rows.slice(1).every(row=>Math.abs(row[name])<1e-8),name);
  }
  assert.throws(()=>simulate(baseline,localHistory,{years:3},planning.revenuePath),/0562/);
  const aligned=simulate(baseline,localHistory,{years:3,revenueMode:1},skrRevenue);
  assert.equal(aligned.rows[1].tax,skrRevenue.rows[0].tax);
  assert.match(modelicaSource(baseline,localHistory,{years:3}),/extends Finspang\.Annual/);
  assert.equal(simulate(b,history,{years:1}).rows[0].debt,b.debt);
});


test('all 13 Östergötland municipalities run eight years from either 2024 or 2025 accounts',{skip},()=>{
  assert.equal(Object.keys(municipalities).length,13);
  for(const [code,{packageName}] of Object.entries(municipalities)) {
    for(const [year,file] of [[2024,'web-2024.json'],[2025,'web.json']]) {
      const {baseline,history,planning}=read(`../data/municipalities/${code}/${file}`);
      assert.equal(baseline.municipality,code);
      assert.equal(history.at(-1).year,year);
      if(year===2024) {
        assert.equal(planning.sources.skrCircular,'24:56');
        assert.notEqual(baseline.nationalPopulation.population['2025'],10605529);
        assert.match(modelicaSource(baseline,history),new RegExp(`base=${packageName}.Data.${packageName.toLowerCase()}2024`));
      }
      const inputs={...baseline,planningInputs:planning?extendPlanning(planning,year+8):null};
      const run=simulate(inputs,history);
      assert.equal(run.rows[0].year,year,code);
      assert.equal(run.rows[0].result,baseline.publishedResult,code);
      assert.equal(run.rows.at(-1).year,year+8,code);
      for(const row of run.rows.slice(1)) {
        for(const balance of ['populationBalance','assetBalance','cashBalance','debtBalance']) {
          assert.ok(Math.abs(row[balance])<1e-7,`${code} ${row.year} ${balance} = ${row[balance]}`);
        }
      }
    }
  }
});

test('the same cohort component runs for every municipality from both county base years',{skip},t=>{
  let cohortError=0,groupError=0;
  for(const [code,{packageName}] of Object.entries(municipalities)) {
    const current=read(`../data/municipalities/${code}/web.json`);
    const previous=read(`../data/municipalities/${code}/web-2024.json`);
    const baseline={...previous.baseline,planningInputs:extendPlanning(previous.planning,2032)};
    const groups=simulate(baseline,previous.history,{years:1});
    const cohort=simulate(baseline,previous.history,{demographyMode:'cohort'});
    const first=cohort.rows[1];
    cohortError+=Math.abs(first.population-current.baseline.reportedPopulation);
    groupError+=Math.abs(groups.rows[1].population-current.baseline.reportedPopulation);
    assert.equal(cohort.rows.at(-1).year,2032,code);
    assert.ok(Math.abs(first.populationBalance)<1e-7,code);
    assert.ok(first.population80Plus>0&&first.population80Plus<first.cohorts[4],code);
    assert.match(modelicaSource(baseline,previous.history,{demographyMode:'cohort'}),
      new RegExp(`data=${packageName}\\.Data\\.SCB\\.${packageName.toLowerCase()}2024`));
    const observed=simulate(current.baseline,current.history,{demographyMode:'cohort-observed',years:1,migrationDelta:100});
    assert.equal(observed.rows[1].year,2026,code);
    assert.ok(Math.abs(observed.rows[1].populationBalance)<1e-7,code);
    assert.equal(current.baseline.experiments.years.at(-1),2024,code);
  }
  t.diagnostic(`2025 absolute population error, mean across 13 municipalities: cohorts ${(cohortError/13).toFixed(1)}, five groups ${(groupError/13).toFixed(1)} people`);
});
