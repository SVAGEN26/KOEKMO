// Any variable of the model on the first chart: the compiled model is run again with every variable stored
// (-variableFilter=.* at simulation time). It must give the same rows as an ordinary run, list the model's variables
// and return the chosen ones from the base year on.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createDirectSimulator} from '../site/src/jit-engine.js';
import {boot,read,skip} from './support/omc-node.mjs';

test('a run with every variable stored gives the same rows and any variable by year',{skip},async()=>{
  const {session}=await boot();
  const simulate=createDirectSimulator(session);
  const b=read('data/baseline.json'),{rows:history}=read('data/history.json');
  const overrides={years:5,timeModel:'continuous'};
  const plain=simulate(b,history,overrides);
  const names=['result','services.capacity[2]','finance.debt.level'];
  const inspected=simulate(b,history,overrides,null,{names});
  plain.rows.slice(1).forEach((r,i)=>{for(const k of ['result','debt','tax','cost']) assert.ok(Math.abs(r[k]-inspected.rows[i+1][k])<1e-9,`${r.year} ${k}`);});
  const {catalogue,picked}=inspected.inspect;
  assert.ok(catalogue.length>400,`${catalogue.length} variables`);
  assert.ok(catalogue.every(v=>typeof v.name==='string'&&'comment' in v&&'unit' in v));
  assert.ok(catalogue.some(v=>v.name==='services.capacity[2]'&&v.comment.length>0));
  for(const n of names) assert.equal(picked[n].length,6,n);
  // The result by year is the ledger's result, from the base year on.
  picked.result.slice(1).forEach((v,i)=>assert.ok(Math.abs(v-plain.rows[i+1].result)<1e-9,`result ${i}`));
  // The stock of debt is kept with a negative sign in the stock-and-flow components.
  picked['finance.debt.level'].slice(1).forEach((v,i)=>assert.ok(Math.abs(v+plain.rows[i+1].debt)<1e-6,`debt ${i}`));
  assert.ok(Math.abs(picked['services.capacity[2]'][0]-1)<1e-9,'capacity is 1 in the base year');
});
