import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {simulate,sum,validateRevenuePath,calibrate,naturalStep} from '../site/src/engine.js';
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
test('population, fiscal, asset and cash identities hold across stress scenarios',()=>{
  for(const changes of [{},{migrationDelta:300,investment:250},{wageGrowth:5,taxGrowth:1,interestRate:5},{investment:0,taxGrowth:7}]){
    const r=simulate(b,history,changes).rows;
    for(let i=1;i<r.length;i++){
      const row=r[i],prev=r[i-1];
      close(row.population-prev.population,row.births-row.deaths+row.migration);
      close(row.result,row.tax+row.grants-row.cost-row.depreciation+b.financialIncome-row.interest-row.otherFinancialExpense);
      close(row.debt,prev.debt+row.borrowing-row.repayment);assert.ok(row.debt>=0);
      close(row.operatingCash,row.result+row.depreciation+row.pensionExpense-row.pensionCashPayments);
      close(row.cash,prev.cash+row.operatingCash-row.investment+row.borrowing-row.repayment);
      close(row.assets,(prev.assets??b.assets)+row.investment-row.depreciation);
      assert.ok(row.cohorts.every(x=>x>=0));
    }
  }
});
test('tax rate change is not cancelled by income equalisation',()=>{
  const base=simulate(b,history).rows[1],raised=simulate(b,history,{taxRate:22.7}).rows[1];
  assert.ok(raised.tax>base.tax);close(raised.grants,base.grants);close(raised.result-base.result,base.tax/21.7);
});
test('capacity lag suppresses immediate cost reduction from shrinking pupil demand',()=>{
  const fixed=simulate(b,history,{adjustment:0}).rows[1],flexible=simulate(b,history,{adjustment:1}).rows[1];
  assert.ok(flexible.educationIndex<1);assert.ok(flexible.cost<fixed.cost);
});
test('base-year deaths calibrate exactly and cohort flows conserve population',()=>{
  const c=calibrate(history);close(sum(b.population.map((p,i)=>p*c.deathRates[i])),468);
  close(sum(naturalStep(b.population,b.births,c.deathRates))-sum(b.population),b.births-b.deaths);
});
test('imported benchmark exactly reconciles in year one with reference population and tax rate',()=>{
  const path={municipality:'0583',vintage:'2026-10-06',rows:Array.from({length:8},(_,i)=>({year:2026+i,tax:2400+i*80,grants:1000+i*20,population:43131}))};
  validateRevenuePath(path,2025);const run=simulate(b,history,{},path);
  close(run.rows[1].tax,2400);close(run.rows[1].grants,1000);close(run.rows[1].officialRevenue,3400);
  assert.throws(()=>simulate(b,history,{}, {...path,rows:path.rows.slice(0,1)}),/missing 2027/);
  assert.throws(()=>validateRevenuePath({...path,municipality:'0180'},2025));
  assert.throws(()=>validateRevenuePath({...path,rows:[path.rows[0],path.rows[0]]},2025));
});
test('reject nonfinite values, invalid shares, sector mismatch and impossible cohorts',()=>{
  for(const overrides of [{interestRate:NaN},{adjustment:2},{years:1.5},{sectorCosts:[1,2,3]},{migrationWeights:[1,1,1,1,1]},{productivity:-100}])assert.throws(()=>simulate(b,history,overrides));
  assert.throws(()=>simulate(b,history,{years:30,migrationDelta:-3000}),/exhausts/);
});
test('future history is not used when fitting a truncated history',()=>{
  const c=calibrate(history.slice(0,2)),changed=structuredClone(history);changed[4].population=[1,1,1,1,1];
  assert.deepEqual(c,calibrate(changed.slice(0,2)));
});
test('pension expense shock is charged once and affects cash only when paid',()=>{
  const fixed={pensionExpensePath:Array(8).fill(190),pensionCashPaymentsPath:Array(8).fill(190)};
  const base=simulate(b,history,fixed).rows[1];
  const accrued=simulate(b,history,{...fixed,pensionExpensePath:[275,...Array(7).fill(190)]}).rows[1];
  close(accrued.cost-base.cost,85);close(accrued.result-base.result,-85);
  close(accrued.operatingCash,base.operatingCash);close(accrued.debt,base.debt);close(accrued.cash,base.cash);
  const paid=simulate(b,history,{...fixed,pensionExpensePath:[275,...Array(7).fill(190)],pensionCashPaymentsPath:[275,...Array(7).fill(190)]}).rows[1];
  // Paid pensions are borrowed, and they also raise the liquidity reserve by 30 days of the payment.
  close(paid.result,accrued.result);close(paid.operatingCash-base.operatingCash,-85);close(paid.debt-base.debt,85*(1+30/365));
});
test('productivity changes payroll without silently reducing pension obligations or revenue',()=>{
  const base=simulate(b,history).rows[1],efficient=simulate(b,history,{productivity:1}).rows[1];
  close(efficient.payroll,base.payroll/1.01);close(efficient.pensionExpense,base.pensionExpense);
  close(efficient.otherOperatingExpense,base.otherOperatingExpense);close(efficient.operatingRevenue,base.operatingRevenue);
  close(efficient.result-base.result,base.payroll-efficient.payroll);
});
test('operating revenue and expenditure grow independently',()=>{
  const base=simulate(b,history).rows[1],higherFees=simulate(b,history,{operatingRevenueGrowth:3}).rows[1];
  close(higherFees.payroll,base.payroll);close(higherFees.pensionExpense,base.pensionExpense);
  close(higherFees.otherOperatingExpense,base.otherOperatingExpense);
  close(higherFees.result-base.result,higherFees.operatingRevenue-base.operatingRevenue);
});
test('reject incomplete pension paths and future or discontinuous calibration history',()=>{
  for(const overrides of [{pensionExpensePath:[190]},{pensionCashPaymentsPath:Array(8).fill(-1)},{pensionExpensePath:Array(8).fill(NaN)}]) assert.throws(()=>simulate(b,history,overrides),/pension/);
  assert.throws(()=>simulate(b,[...history,{...history.at(-1),year:2026}]),/future/);
  assert.throws(()=>simulate(b,history.slice(0,-1)),/baseline/);
  assert.throws(()=>simulate(b,[history[0],...history.slice(2)]),/consecutive/);
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
