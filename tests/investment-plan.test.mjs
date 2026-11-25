// The municipalities' investment plans (data/investment-plans.json): the figures against the other records of the same
// budgets, and how the page turns a plan into the model's investment path.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {prepareScenario,investmentFactor} from '../site/src/scenario-inputs.js';
import {read} from './support/omc-node.mjs';

const plans=read('data/investment-plans.json').municipalities;
const factorsOf=plan=>Object.keys(plan.plan).map(Number).sort((x,y)=>x-y).map(y=>plan.plan[y]/plan.baseBudget);

test('the plans are the budgets as recorded elsewhere in the project',()=>{
  // Motala's budget 2026 is also read in data/municipal-budgets.json (page 28).
  const motala=read('data/municipal-budgets.json').budgets.find(x=>x.budget===2026);
  assert.deepEqual(Object.values(plans['0583'].plan),motala.investment);
  // The base year's outcome: Motala's annual report, which is also its base year in the model.
  assert.equal(plans['0583'].baseOutcome,read('data/baseline.json').investment);
  for(const [code,plan] of Object.entries(plans)) {
    assert.equal(plan.baseYear,2025,code);
    assert.ok(plan.baseBudget>0&&Object.values(plan.plan).every(x=>x>0),code);
    assert.ok(plan.sources.baseBudget&&plan.sources.plan,`${code} sources`);
    for(const h of plan.history) assert.ok(h.outcome<=h.budget,`${code} ${h.year}: outcome above budget`);
    // The rule for taking a municipality in: half to all of the budget for the base year carried out.
    const share=plan.baseOutcome/plan.baseBudget;
    assert.ok(share>=0.5&&share<=1,`${code}: ${share}`);
  }
  // The others are named with a reason; together they are the 13.
  const excluded=read('data/investment-plans.json').excluded;
  assert.equal(Object.keys(plans).length+Object.keys(excluded).length,13);
  for(const [code,x] of Object.entries(excluded)) assert.ok(!(code in plans)&&x.reason.length>40,code);
});

test('the base year\'s investment follows the plan, and returns to its own level after it',()=>{
  const b={...read('data/baseline.json')},history=read('data/history.json').rows;
  const plan=plans['0583'],factors=factorsOf(plan);
  const planned={...b,investmentPlan:{...plan,factors}};
  const path=prepareScenario(planned,history,{years:8,investmentPlan:true}).fields.investmentPath;
  assert.equal(path.length>=8,true);
  path.slice(0,8).forEach((x,i)=>assert.ok(Math.abs(x-b.investment*(i<factors.length?factors[i]:1))<1e-9,`year ${i+1}`));
  // 413 mnkr in 2025, 55 % of the budget of 750; 755, 897 and 961 in the plan; then 413 again.
  assert.deepEqual(path.slice(0,4).map(Math.round),[416,494,529,413]);
  // A changed level scales the whole path; without the plan every year is the level.
  const scaled=prepareScenario(planned,history,{years:3,investmentPlan:true,investment:300}).fields.investmentPath;
  scaled.slice(0,3).forEach((x,i)=>assert.ok(Math.abs(x-300*factors[i])<1e-9));
  assert.ok(prepareScenario(planned,history,{years:3,investmentPlan:false}).fields.investmentPath.slice(0,3).every(x=>x===b.investment));
  assert.equal(investmentFactor(b,{investmentPlan:true},0),1);
  assert.throws(()=>prepareScenario(b,history,{years:3,investmentPlan:true}),/investeringsplan/);
});
