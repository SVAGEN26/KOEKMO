// The base-year data and the scenario preparation that runs before the model: no simulation here.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {sum,validateRevenuePath,calibrate,naturalStep,prepareScenario} from '../site/src/scenario-inputs.js';
const b=JSON.parse(fs.readFileSync(new URL('../data/baseline.json',import.meta.url))),{rows:history}=JSON.parse(fs.readFileSync(new URL('../data/history.json',import.meta.url)));
const close=(a,b,tolerance=1e-7)=>assert.ok(Math.abs(a-b)<tolerance,`${a} != ${b}`);

test('published initial ledger reconciles within rounding',()=>{
  close(sum(b.population),43131);close(sum(b.assumptions.sectorCosts),b.cashCost);
  close(b.cashCost+b.depreciation,3203);
  close(b.publishedResult-(b.tax+b.grants-b.cashCost-b.depreciation+b.financialIncome-b.interestExpense-b.otherFinancialExpense),1);
  const o=b.operatingAccounts;
  close(o.payrollExcludingPensions+o.pensionExpense+o.otherOperatingExpense,3775);
  close(3775-o.operatingRevenue+o.netCostRoundingAdjustment,b.cashCost);
});
test('base-year deaths calibrate exactly and cohort flows conserve population',()=>{
  const c=calibrate(history);close(sum(b.population.map((p,i)=>p*c.deathRates[i])),468);
  close(sum(naturalStep(b.population,b.births,c.deathRates))-sum(b.population),b.births-b.deaths);
});
test('an imported revenue path must cover every forecast year and the right municipality',()=>{
  const path={municipality:'0583',vintage:'2026-10-06',rows:Array.from({length:8},(_,i)=>({year:2026+i,tax:2400+i*80,grants:1000+i*20,population:43131}))};
  validateRevenuePath(path,2025);
  assert.throws(()=>prepareScenario(b,history,{},{...path,rows:path.rows.slice(0,1)}),/missing 2027/);
  assert.throws(()=>validateRevenuePath({...path,municipality:'0180'},2025));
  assert.throws(()=>validateRevenuePath({...path,rows:[path.rows[0],path.rows[0]]},2025));
});
test('reject nonfinite values, invalid shares, sector mismatch and bad pension paths before the model runs',()=>{
  for(const overrides of [{interestRate:NaN},{adjustment:2},{years:1.5},{sectorCosts:[1,2,3]},{migrationWeights:[1,1,1,1,1]},{productivity:-100}]) assert.throws(()=>prepareScenario(b,history,overrides));
  for(const overrides of [{pensionExpensePath:[190]},{pensionCashPaymentsPath:Array(8).fill(-1)},{pensionExpensePath:Array(8).fill(NaN)}]) assert.throws(()=>prepareScenario(b,history,overrides),/pension/i);
  assert.throws(()=>prepareScenario(b,history,{timeModel:'annual'}),/kontinuerlig/);
});
test('calibration history must be consecutive and end at the base year; future history is not used',()=>{
  assert.throws(()=>prepareScenario(b,[...history,{...history.at(-1),year:2026}]),/future/);
  assert.throws(()=>prepareScenario(b,history.slice(0,-1)),/baseline/);
  assert.throws(()=>prepareScenario(b,[history[0],...history.slice(2)]),/consecutive/);
  const c=calibrate(history.slice(0,2)),changed=structuredClone(history);changed[4].population=[1,1,1,1,1];
  assert.deepEqual(c,calibrate(changed.slice(0,2)));
});
test('observed operating-cost bridge reconciles 2024 and 2025 without hiding the pension change',()=>{
  const {rows:[before,after]}=JSON.parse(fs.readFileSync(new URL('../data/operating-accounts-history.json',import.meta.url)));
  for(const row of [before,after]){
    close(row.grossOperatingExpense,row.payrollExcludingPensions+row.pensionExpense+row.otherOperatingExpense);
    close(row.netOperatingCost,row.grossOperatingExpense-row.operatingRevenue+row.netCostRoundingAdjustment);
  }
  close(after.pensionExpense-before.pensionExpense,-85);
  close(after.netOperatingCost-before.netOperatingCost,-5);
  close(after.payrollExcludingPensions-before.payrollExcludingPensions,30);
  close(after.otherOperatingExpense-before.otherOperatingExpense,28);
  close(before.operatingRevenue-after.operatingRevenue,23);
});
