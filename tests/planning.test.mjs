import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {sum,prepareScenario} from '../site/src/scenario-inputs.js';
import {createDirectSimulator} from '../site/src/jit-engine.js';
import {boot,staged,skip} from './support/omc-node.mjs';
import {modelicaSource} from '../site/src/modelica-adapter.js';
const read=name=>JSON.parse(fs.readFileSync(new URL('../data/'+name,import.meta.url)));
const baseline=read('baseline.json'),planning=read('planning-inputs.json'),{rows:history}=read('history.json');
const active=()=>({...structuredClone(baseline),planningInputs:structuredClone(planning)});
const close=(a,b,tolerance=1e-7)=>assert.ok(Math.abs(a-b)<tolerance,`${a} != ${b}`);
// The model in continuous time, as the page runs it.
const simulate=staged?createDirectSimulator((await boot()).session):null;
test('active population follows the anchored source path and preserves all balances',{skip},()=>{
  const b=active(),rows=simulate(b,history).rows;
  for(let t=1;t<rows.length;t++){
    const r=rows[t],prev=rows[t-1];
    // The residual flow is calibrated so that the groups reach the source path at each year end.
    r.cohorts.forEach((x,i)=>close(x,planning.rows[t-1].cohorts[i],1e-3));
    close(r.population,baseline.reportedPopulation*planning.rows[t-1].sourceTotal/planning.sourceBaseTotal,1e-3);
    for(const k of ['populationBalance','cashBalance','debtBalance','assetBalance']) close(r[k],0,1e-6);
    close(r.result,r.tax+r.grants-r.cost-r.depreciation+r.annualFinancialIncome-r.interest-r.otherFinancialExpense,1e-6);
    assert.equal(r.officialRevenue,null);
  }
  assert.notEqual(rows.at(-1).population,simulate(baseline,history).rows.at(-1).population);
});
test('dated labour and other-price rates move independently with scenario offsets',{skip},()=>{
  const b=active(),run=simulate(b,history),changed=simulate(b,history,{wageGrowth:b.assumptions.wageGrowth+1});
  for(let t=1;t<run.rows.length;t++){
    const row=run.rows[t],v=planning.rows[t-1];
    close(changed.inputs[t-1].wageGrowth,v.labourCostGrowth+1);
    assert.ok(changed.rows[t].payroll>row.payroll);
    // Equal up to the solver's tolerance: a different wage path changes its steps.
    close(changed.rows[t].otherOperatingExpense,row.otherOperatingExpense,1e-3);
    // The pension cost follows the payroll, so it rises with the wages and keeps its share of the payroll.
    close(changed.rows[t].pensionExpense/changed.rows[t].payroll,row.pensionExpense/row.payroll,1e-6);
  }
});
test('migration and birth interventions still affect sourced scenarios; inputs stay unchanged',{skip},()=>{
  const b=active(),before=JSON.stringify(b),base=simulate(b,history),more=simulate(b,history,{migrationDelta:100}),births=simulate(b,history,{birthChange:10});
  // Arrivals and births come during the year; a few of them die in it.
  close(more.rows[1].population-base.rows[1].population,100,1);
  close(births.rows[1].population-base.rows[1].population,b.births*.1,1);
  assert.ok(more.rows.at(-1).population>base.rows.at(-1).population);
  assert.equal(JSON.stringify(b),before);
});
test('planning inputs fail closed on wrong municipality, years, rates or age values',()=>{
  for(const mutate of [p=>p.municipality='0180',p=>p.baseYear=2024,p=>p.rows.pop(),p=>p.rows.push(p.rows[0]),p=>p.rows[0].cohorts[0]=-1,p=>p.rows[0].labourCostGrowth=NaN]){
    const b=active();mutate(b.planningInputs);assert.throws(()=>prepareScenario(b,history),/Planning|planning/);
  }
});
test('recalculated municipality revenue is traceable and remains distinct from scenario adjustments',{skip},()=>{
  const path=planning.revenuePath;
  assert.equal(planning.revenueImport.cachedSelection,583);
  assert.equal(planning.revenueImport.originalSelection,null);
  assert.match(planning.revenueImport.status,/active-recalculated/);
  assert.equal(path.provenance.recalculation.macrosExecuted,false);
  assert.equal(path.provenance.recalculation.vbaRemovedBeforeRecalculation,true);
  const b=active(),run=simulate(b,history,{},path),source=modelicaSource(b,history,{},path);
  for(const r of run.rows.slice(1)){
    const ref=path.rows.find(x=>x.year===r.year);
    close(r.officialRevenue,ref.tax+ref.grants,1e-6);
    assert.ok(Number.isFinite(r.result));
  }
  close(path.rows[0].tax,2403.874358);
  close(path.rows[0].grants,982.773537739798);
  assert.notEqual(run.rows[1].tax,path.rows[0].tax);
  assert.match(source,/importedRevenue=true/);
  const legacy=simulate(b,history,{},null);
  assert.equal(legacy.rows[1].officialRevenue,null);
});

test('the state frame marks the path and leaves SKR\'s rows as they are',async()=>{
  // The model computes the regulation grant after the decided year (Kommunekonomi.Data.sourcedRevenue; tests/fast).
  const {followStateFrame}=await import('../site/src/scenario-inputs.js');
  const skr=planning.revenuePath,rule=planning.regulationRule;
  assert.equal(rule.heldFrom,Number(skr.vintage.slice(0,4))+1);
  const framed=followStateFrame(skr,rule.heldFrom);
  assert.equal(framed.stateFrameFrom,rule.heldFrom);
  assert.deepEqual(framed.rows,skr.rows);
  const bare={...skr,rows:skr.rows.map(({regulation,...r})=>r)};
  assert.equal(followStateFrame(bare,rule.heldFrom).stateFrameFrom,undefined,'without regulation data the path is unchanged');
});
