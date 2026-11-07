import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {simulate,sum} from '../site/src/engine.js';
import {modelicaSource} from '../site/src/modelica-adapter.js';
const read=name=>JSON.parse(fs.readFileSync(new URL('../data/'+name,import.meta.url)));
const baseline=read('baseline.json'),planning=read('planning-inputs.json'),{rows:history}=read('history.json');
const active=()=>({...structuredClone(baseline),planningInputs:structuredClone(planning)});
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`);
test('active population follows the anchored source path and preserves all balances',()=>{
  const b=active(),rows=simulate(b,history).rows;
  for(let t=1;t<rows.length;t++){
    const r=rows[t],prev=rows[t-1];
    r.cohorts.forEach((x,i)=>close(x,planning.rows[t-1].cohorts[i]));
    close(r.population,baseline.reportedPopulation*planning.rows[t-1].sourceTotal/planning.sourceBaseTotal);
    close(r.population-prev.population,r.births-r.deaths+r.migration);
    close(r.result,r.tax+r.grants-r.cost-r.depreciation+baseline.financialIncome-r.interest-r.otherFinancialExpense);
    close(r.cash,prev.cash+r.operatingCash-r.investment+r.borrowing-r.repayment);
    close(r.debt,prev.debt+r.borrowing-r.repayment);
    assert.equal(r.officialRevenue,null);
  }
  assert.notEqual(rows.at(-1).population,simulate(baseline,history).rows.at(-1).population);
});
test('dated labour and other-price rates compound independently with scenario offsets',()=>{
  const b=active(),run=simulate(b,history),changed=simulate(b,history,{wageGrowth:b.assumptions.wageGrowth+1});
  let wage=1,price=1;
  for(let t=1;t<run.rows.length;t++){
    wage*=1+planning.rows[t-1].labourCostGrowth/100;
    price*=1+planning.rows[t-1].otherPriceGrowth/100;
    const row=run.rows[t],v=planning.rows[t-1];
    close(row.payroll/b.operatingAccounts.payrollExcludingPensions/(row.otherOperatingExpense/b.operatingAccounts.otherOperatingExpense),wage/price);
    close(changed.inputs[t-1].wageGrowth,v.labourCostGrowth+1);
    close(changed.rows[t].otherOperatingExpense,row.otherOperatingExpense);
    close(changed.rows[t].pensionExpense,row.pensionExpense);
  }
});
test('migration and birth interventions still affect sourced scenarios; inputs stay unchanged',()=>{
  const b=active(),before=JSON.stringify(b),base=simulate(b,history),more=simulate(b,history,{migrationDelta:100}),births=simulate(b,history,{birthChange:10});
  close(more.rows[1].population-base.rows[1].population,100);
  close(births.rows[1].population-base.rows[1].population,b.births*.1);
  assert.ok(more.rows.at(-1).population>base.rows.at(-1).population);
  assert.equal(JSON.stringify(b),before);
});
test('planning inputs fail closed on wrong municipality, years, rates or age values',()=>{
  for(const mutate of [p=>p.municipality='0180',p=>p.baseYear=2024,p=>p.rows.pop(),p=>p.rows.push(p.rows[0]),p=>p.rows[0].cohorts[0]=-1,p=>p.rows[0].labourCostGrowth=NaN]){
    const b=active();mutate(b.planningInputs);assert.throws(()=>simulate(b,history),/Planning|planning/);
  }
});
test('recalculated municipality revenue is traceable and remains distinct from scenario adjustments',()=>{
  const path=planning.revenuePath;
  assert.equal(planning.revenueImport.cachedSelection,583);
  assert.equal(planning.revenueImport.originalSelection,null);
  assert.match(planning.revenueImport.status,/active-recalculated/);
  assert.equal(path.provenance.recalculation.macrosExecuted,false);
  assert.equal(path.provenance.recalculation.vbaRemovedBeforeRecalculation,true);
  const b=active(),run=simulate(b,history,{},path),source=modelicaSource(b,history,{},path);
  for(const r of run.rows.slice(1)){
    const ref=path.rows.find(x=>x.year===r.year);
    close(r.officialRevenue,ref.tax+ref.grants);
    assert.ok(Number.isFinite(r.result));
  }
  close(path.rows[0].tax,2403.874358);
  close(path.rows[0].grants,982.773537739798);
  assert.notEqual(run.rows[1].tax,path.rows[0].tax);
  assert.match(source,/importedRevenue=true/);
  const legacy=simulate(b,history,{},null);
  assert.equal(legacy.rows[1].officialRevenue,null);
});
