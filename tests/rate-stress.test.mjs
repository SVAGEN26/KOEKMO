// Rate stress paths (data/rate-stress.json, scripts/prepare_rate_stress.py): how they are built from Riksbank's
// yearly rates, how the page turns one into the model's rate path, and what they do in the compiled model.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {prepareScenario,rateEpisode} from '../site/src/scenario-inputs.js';
import {createDirectSimulator} from '../site/src/jit-engine.js';
import {boot,read,staged,skip} from './support/omc-node.mjs';

const stress=read('data/rate-stress.json');
const b={...read('data/baseline.json'),rateEpisodes:stress.episodes},{rows:history}=read('data/history.json');
const close=(a,e,t,m)=>assert.ok(Math.abs(a-e)<=t,`${m}: ${a} vs ${e}`);

test('each path is the change in the treasury bill rate from the year before the episode',()=>{
  assert.deepEqual(stress.episodes.map(e=>e.id),['rise2022','crisis1990','finance2006','low2013']);
  for(const e of stress.episodes) {
    const [first,last]=e.years;
    assert.equal(e.startRate,stress.yearlyRates[first-1]);
    assert.equal(e.changes.length,last-first+1);
    e.changes.forEach((c,i)=>close(c,stress.yearlyRates[first+i]-e.startRate,0.011,`${e.id} ${first+i}`));
  }
  // Riksbank, 3-month treasury bill, yearly averages: -0.20 % in 2021, 3.57 % in 2023.
  close(stress.yearlyRates['2021'],-0.2,0.005,'2021');close(stress.yearlyRates['2023'],3.57,0.005,'2023');
});

test('a path moves the scenario\'s own rate, holds its last change, and never goes below 0',()=>{
  const plain=prepareScenario(b,history,{years:8}).fields.interestRatePath;
  const rate=b.assumptions.interestRate;
  assert.ok(plain.every(x=>close(x,rate/100,1e-12,'own rate')??true));
  const rise=prepareScenario(b,history,{years:8,rateEpisode:'rise2022'}).fields.interestRatePath,e=rateEpisode(b,{rateEpisode:'rise2022'});
  rise.forEach((x,i)=>close(x,(rate+e.changes[Math.min(i,e.changes.length-1)])/100,1e-12,`rise ${i}`));
  const low=prepareScenario(b,history,{years:8,interestRate:0.5,rateEpisode:'low2013'}).fields.interestRatePath;
  assert.ok(low.every(x=>x>=0)&&low.some(x=>x===0),'floored at 0');
  assert.throws(()=>prepareScenario(b,history,{rateEpisode:'nonesuch'}),/Okänd räntebana/);
  assert.equal(rateEpisode(b,{rateEpisode:'none'}),null);
});

test('in the model a rise costs interest and result, and a fall saves both, and the fixed-rate period delays it',{skip},async()=>{
  const {session}=await boot();
  const simulate=createDirectSimulator(session);
  const run=overrides=>simulate(b,history,{years:8,timeModel:'continuous',...overrides},null).rows.slice(1);
  const fixed={rateFixingYears:3.19};  // Motala's fixed-rate period, annual report 2025
  const base=run(fixed),rise=run({...fixed,rateEpisode:'rise2022'}),low=run({...fixed,rateEpisode:'low2013'});
  for(let i=0;i<base.length;i++) {
    assert.ok(rise[i].interest>=base[i].interest-1e-6&&rise[i].result<=base[i].result+1e-6,`rise ${base[i].year}`);
    assert.ok(low[i].interest<=base[i].interest+1e-6&&low[i].result>=base[i].result-1e-6,`low ${base[i].year}`);
  }
  // The fixed-rate period lets the market rate reach the average rate gradually: less extra interest in the first
  // years than with every loan at the market rate at once.
  const extra=rise.map((r,i)=>r.interest-base[i].interest);
  const at=run({rateFixingYears:0}),atRise=run({rateFixingYears:0,rateEpisode:'rise2022'}),direct=atRise.map((r,i)=>r.interest-at[i].interest);
  assert.ok(extra[0]<direct[0]&&extra[1]<direct[1],`extra interest ${extra.map(x=>x.toFixed(1))} against ${direct.map(x=>x.toFixed(1))}`);
  // Interest is the only line the path moves directly; tax stays.
  rise.forEach((r,i)=>close(r.tax,base[i].tax,1e-4,`tax ${r.year}`));  // within the solver's tolerance
});
