// The site compiles the municipality packages in the browser with OpenModelica (wasm-jit), in continuous time. This
// runs the same staged compiler in Node and checks the mechanisms, base years and municipalities.
// Needs site/omc-web (scripts/stage_omc.py); skipped when the compiler is not staged.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
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
// A shorter horizon gives nearly the same years. In continuous time the wage and price rate at a year's end leans on
// the next year's growth, which a shorter run takes from its last year; the liquidity reserve follows those payments.
// Flows agree within 0.01 mnkr and cash and debt within 1 mnkr (2022 from the 2021 accounts: 0.5).
const near=(a,b,label)=>{for(const [k,tol] of [['population',0.01],['tax',0.01],['grants',0.01],['cost',0.01],['result',0.01],['debt',1],['cash',1]]) assert.ok(Math.abs(a[k]-b[k])<=tol,`${label} ${k}: ${a[k]} vs ${b[k]}`);};

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
  // The base-year row is the 2021 accounts; a shorter horizon gives the same first year.
  assert.equal(forecast.rows[0].result,replay.baseline.publishedResult);
  const short=simulate(historical,replay.history,{years:1},path);
  near(short.rows[1],forecast.rows[1],'one year');
  const source=modelicaSource(historical,replay.history,{},path);
  assert.match(source,/base=Kommunekonomi.Municipalities.Motala.Data.motala2021/);
  assert.match(source,/StartTime=2021, StopTime=2026/);

  const extended=extendPlanning(planning,2055);
  const modern=simulate({...b,planningInputs:extended},history,{years:30},extended.revenuePath);
  assert.equal(modern.rows.at(-1).year,2055);
  simulate({...b,planningInputs:planning},history,{},planning.revenuePath).rows.slice(1).forEach((row,i)=>near(modern.rows[i+1],row,String(row.year)));
  assert.ok(modern.rows[8].officialRevenue>0);
  assert.equal(modern.rows[9].officialRevenue,null);
});

test('equally large migration scenarios move tax and equalisation in opposite directions',{skip},()=>{
  const source=read('../data/age-income.json');
  const baseline={...b,planningInputs:planning,experiments:{novemberPopulation:43158},
    ageIncome:{weights:source.municipalities['0583']['2024'],countyRate:source.countyRate}};
  const opts={years:2,revenueMode:2,ageTax:true,migrationDelta:100};
  const working=simulate(baseline,history,{...opts,migrationProfile:'working'},planning.revenuePath).rows;
  const older=simulate(baseline,history,{...opts,migrationProfile:'older'},planning.revenuePath).rows;
  // Arrivals come during the year, so their ages change the year's births and deaths: older arrivals die more,
  // 2.5 persons in 2026 for Motala. The same number arrives.
  assert.ok(Math.abs(working[1].population-older[1].population)<5,`${working[1].population} vs ${older[1].population}`);
  assert.ok(Math.abs(working[1].tax-older[1].tax)<1e-6,`first-year tax ${working[1].tax} vs ${older[1].tax}`);
  assert.ok(working[2].tax>older[2].tax);
  assert.ok(working[2].grants<older[2].grants);
  assert.ok(working[2].careIndex<older[2].careIndex);
  const taxDelta=working[2].tax-older[2].tax,grantDelta=working[2].grants-older[2].grants;
  // Equalisation takes back the county rate's share of the tax; the rest is the 2.5 persons the profiles differ by
  // (older arrivals die more during the year), about 0.12 mnkr of grants.
  assert.ok(Math.abs(grantDelta+taxDelta*source.countyRate/b.taxRate)<0.2,`${grantDelta} vs ${-taxDelta*source.countyRate/b.taxRate}`);
});

test('Finspång uses its own base year, reacts to migration, and keeps the Motala model isolated',{skip},()=>{
  const {baseline,history:localHistory,skrRevenue}=read('../data/municipalities/0562/web.json');
  const base=simulate(baseline,localHistory,{years:3});
  const alternative=simulate(baseline,localHistory,{years:3,migrationDelta:300,splitPayroll:true,constructionYears:2});
  assert.ok(Math.abs(base.rows[0].population-21502)<1e-8);
  assert.equal(base.rows[0].debt,290);  // own debt: external borrowing 1 777 less 1 487 lent on to the companies
  assert.equal(base.rows.at(-1).year,2028);
  assert.equal(alternative.rows[0].workInProgress,50);
  // 300 more arrive during the year; their births and deaths in that year are a fraction of a person.
  assert.ok(Math.abs(alternative.rows[1].population-base.rows[1].population-300)<1);
  for(const name of ['populationBalance','assetBalance','cashBalance','debtBalance']) {
    assert.ok(alternative.rows.slice(1).every(row=>Math.abs(row[name])<1e-6),name);
  }
  assert.throws(()=>simulate(baseline,localHistory,{years:3},planning.revenuePath),/0562/);
  const aligned=simulate(baseline,localHistory,{years:3,revenueMode:1},skrRevenue);
  assert.ok(Math.abs(aligned.rows[1].tax-skrRevenue.rows[0].tax)<1e-6);
  assert.match(modelicaSource(baseline,localHistory,{years:3}),/extends Kommunekonomi\.Municipalities\.Finspang\.Continuous/);
  assert.equal(simulate(b,history,{years:1}).rows[0].debt,b.debt);
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
      new RegExp(`data=Kommunekonomi\\.Municipalities\\.${packageName}\\.Data\\.SCB\\.${packageName.toLowerCase()}2024`));
    const observed=simulate(current.baseline,current.history,{demographyMode:'cohort-observed',years:1,migrationDelta:100});
    assert.equal(observed.rows[1].year,2026,code);
    assert.ok(Math.abs(observed.rows[1].populationBalance)<1e-7,code);
    assert.equal(current.baseline.experiments.years.at(-1),2024,code);
  }
  t.diagnostic(`2025 absolute population error, mean across 13 municipalities: cohorts ${(cohortError/13).toFixed(1)}, five groups ${(groupError/13).toFixed(1)} people`);
});

// Properties of the model, checked in continuous time. Tax and grants are set at the start of each year; costs and
// interest run during it, so a change that moves cash also moves the year's interest a little.
test('a tax rate change is not cancelled by income equalisation',{skip},()=>{
  const base=simulate(b,history).rows[1],raised=simulate(b,history,{taxRate:b.taxRate+1}).rows[1];
  assert.ok(raised.tax>base.tax);
  assert.ok(Math.abs(raised.grants-base.grants)<1e-6);
  assert.ok(Math.abs(raised.tax-base.tax-base.tax/b.taxRate)<1e-6);
  // Motala 2026: 110 mnkr more tax, so 111 mnkr less borrowed during the year and 1.2 mnkr less interest.
  const gain=raised.result-base.result-base.tax/b.taxRate;
  assert.ok(gain>0&&gain<3,`the result gains the tax and a little less interest: ${gain}`);
});
test('capacity lag holds back the cost reduction from shrinking pupil demand',{skip},()=>{
  const fixed=simulate(b,history,{adjustment:0}).rows[1],flexible=simulate(b,history,{adjustment:1}).rows[1];
  assert.ok(flexible.educationIndex<1);assert.ok(flexible.cost<fixed.cost);
});
test('a pension expense shock is charged once and affects cash only when paid',{skip},()=>{
  const fixed={pensionExpensePath:Array(8).fill(190),pensionCashPaymentsPath:Array(8).fill(190)};
  const base=simulate(b,history,fixed).rows[1];
  const accrued=simulate(b,history,{...fixed,pensionExpensePath:[275,...Array(7).fill(190)]}).rows[1];
  // Up to the solver's tolerance: an accrued cost does not move cash.
  assert.ok(Math.abs(accrued.cost-base.cost-85)<1e-3,`${accrued.cost-base.cost}`);assert.ok(Math.abs(accrued.result-base.result+85)<1e-3);
  for(const k of ['operatingCash','debt','cash']) assert.ok(Math.abs(accrued[k]-base[k])<1e-3,k);
  const paid=simulate(b,history,{...fixed,pensionExpensePath:[275,...Array(7).fill(190)],pensionCashPaymentsPath:[275,...Array(7).fill(190)]}).rows[1];
  // Paid pensions are borrowed during the year, which costs some interest, and raise the reserve by 30 days of the payment.
  assert.ok(Math.abs(paid.result-accrued.result)<2,'only the interest on the extra borrowing');
  assert.ok(paid.debt-base.debt>85&&paid.debt-base.debt<85*(1+30/365)+2,`debt ${paid.debt-base.debt}`);
});
test('productivity lowers payroll and the pension cost with it, not other costs or revenue',{skip},()=>{
  const base=simulate(b,history).rows[1],efficient=simulate(b,history,{productivity:1}).rows[1];
  // One per cent a year, rising through the year from the base year's level.
  assert.ok(efficient.payroll<base.payroll&&efficient.payroll>base.payroll/1.02,`${efficient.payroll} vs ${base.payroll}`);
  for(const k of ['otherOperatingExpense','operatingRevenue']) assert.ok(Math.abs(efficient[k]-base[k])<1e-6,k);
  // The pension cost follows the payroll: the same share of it with fewer hours worked.
  assert.ok(Math.abs(efficient.pensionExpense/efficient.payroll-base.pensionExpense/base.payroll)<1e-6,'pension share');
  assert.ok(Math.abs(efficient.result-base.result-(base.payroll-efficient.payroll)-(base.pensionExpense-efficient.pensionExpense))<1);
});
test('operating revenue and expenditure grow independently',{skip},()=>{
  const base=simulate(b,history).rows[1],higherFees=simulate(b,history,{operatingRevenueGrowth:3}).rows[1];
  for(const k of ['payroll','pensionExpense','otherOperatingExpense']) assert.ok(Math.abs(higherFees[k]-base[k])<1e-6,k);
  assert.ok(higherFees.operatingRevenue>base.operatingRevenue);
  assert.ok(Math.abs(higherFees.result-base.result-(higherFees.operatingRevenue-base.operatingRevenue))<1);
});
test('the liquidity reserve starts at the accounts\' own days and approaches the municipality\'s rule',{skip},()=>{
  const liquidity=read('../data/liquidity.json').municipalities['0583'];
  const motala={...b,planningInputs:planning,liquidity};
  const days=row=>365*(row.cash+liquidity.creditLine)/(row.payroll+row.pensionCashPayments+row.otherOperatingExpense+row.investment+row.interest);
  const held=simulate(motala,history,{},planning.revenuePath).rows,off=simulate(motala,history,{liquidityPolicy:false},planning.revenuePath).rows;
  // No jump in January: the first year's extra borrowing is the slow approach, not the whole gap (78 mnkr for Motala).
  assert.ok(held[1].debt-off[1].debt<40,`extra debt in 2026: ${held[1].debt-off[1].debt}`);
  assert.ok(days(held[1])>days(held[0])-1&&days(held[1])<liquidity.reserveDays,`days 2026: ${days(held[1])}`);
  // After eight years, three time constants and a bit, within two days of the rule.
  assert.ok(Math.abs(days(held.at(-1))-liquidity.reserveDays)<2,`days 2033: ${days(held.at(-1))}`);
  const immediate=simulate(motala,history,{reserveAdjustmentTime:0},planning.revenuePath).rows;
  assert.ok(Math.abs(days(immediate[1])-liquidity.reserveDays)<1,`immediate days 2026: ${days(immediate[1])}`);
});
