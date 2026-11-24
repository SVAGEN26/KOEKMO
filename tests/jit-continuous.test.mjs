// The page runs the continuous model (Motala.Continuous) by default. These tests run it in the staged
// compiler the way the page does and check it against the library's own calibration, against SCB's and
// SKR's inputs, against the yearly model where the two must agree, and against native OpenModelica.
// Needs site/omc-web (scripts/stage_omc.py); skipped when the compiler is not staged.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync,spawnSync} from 'node:child_process';
import {boot,read,runModel,staged,skip} from './support/omc-node.mjs';
import {createSession,hasFastFlows} from '../site/src/omc-session.js';
import {createDirectSimulator} from '../site/src/jit-engine.js';
import {calibrateContinuous,continuousYear,extendPlanning,inflowBetween,sum} from '../site/src/scenario-inputs.js';
import {modelicaSource} from '../site/src/modelica-adapter.js';
import {municipalities} from '../site/src/municipalities.js';

let omc,session,simulate;
if(staged) {
  ({omc,session}=await boot());
  simulate=createDirectSimulator(session);
}
const b=read('data/baseline.json'),{rows:history}=read('data/history.json'),planning=read('data/planning-inputs.json');
const sourced={...b,planningInputs:planning},revenue=planning.revenuePath;
const continuous=(baseline,rows,overrides={},revenuePath=null)=>simulate(baseline,rows,{...overrides,timeModel:'continuous'},revenuePath);
const annual=(baseline,rows,overrides={},revenuePath=null)=>simulate(baseline,rows,{...overrides,timeModel:'annual'},revenuePath);
const balances=['populationBalance','assetBalance','cashBalance','debtBalance'];
function assertBooks(run,label) {
  for(const row of run.rows.slice(1)) {
    for(const k of balances) assert.ok(Math.abs(row[k])<1e-6,`${label} ${row.year} ${k} = ${row[k]}`);
    const parts=row.tax+row.grants-row.cost-row.depreciation+b.financialIncome-row.interest-row.otherFinancialExpense;
    if(label.startsWith('Motala')) assert.ok(Math.abs(row.result-parts)<1e-6,`${label} ${row.year} result ${row.result} vs parts ${parts}`);
  }
}
const close=(actual,expected,tolerance,message)=>assert.ok(Math.abs(actual-expected)<=tolerance,`${message}: ${actual} vs ${expected}`);

test('the page starts in continuous time',()=>{
  const html=fs.readFileSync(new URL('../site/src/index.html',import.meta.url),'utf8');
  assert.match(html,/<option value="continuous" selected>/);
  assert.doesNotMatch(html,/<option value="annual" selected>/);
});

test('the flow between two year ends is the one that takes the groups there',()=>{
  const year=continuousYear([0.0004,0.0001,0.0002,0.0018,0.04],334/23000);
  const from=[2900,4600,1600,23000,11000],flow=[-40,60,10,-200,30];
  const to=year.Phi.map((row,i)=>sum(row.map((x,j)=>x*from[j]))+sum(year.Psi[i].map((x,j)=>x*flow[j])));
  inflowBetween(year,from,to).forEach((x,i)=>close(x,flow[i],1e-9,`group ${i+1}`));
  // No deaths, births or flows: the population is kept, and the oldest group only receives.
  const still=continuousYear([0,0,0,0,0]);
  close(sum(still.Phi.map(row=>sum(row.map((x,j)=>x*from[j])))),sum(from),1e-9,'population kept');
});

test('the page\'s calibration is the library\'s: site inputs give Motala.Continuous as written',{skip},()=>{
  const site=continuous({...b,planningInputs:null},history);
  const keys=['population','births','deaths','migration','cost','payroll','otherOperatingExpense','operatingRevenue','depreciation',
    'tax','grants','result','debt','cash','assets','interest','borrowing','repayment','educationIndex','careIndex'];
  const model=runModel(omc,'Motala.Continuous',{start:2025,stop:2033,intervals:96,method:'rungekutta'},keys);
  assert.equal(site.rows.length,9);
  for(const [i,row] of model.entries()) for(const k of keys) {
    close(site.rows[i+1][k],row[k],1e-8*Math.max(1,Math.abs(row[k])),`${row.year} ${k}`);
  }
  assertBooks(site,'Motala');
});

test('with SCB\'s projection the population is the projection at every year end, and tax and grants are the yearly model\'s',{skip},()=>{
  const flow=continuous(sourced,history,{},revenue),yearly=annual(sourced,history,{},revenue);
  for(const [i,row] of flow.rows.slice(1).entries()) {
    const projected=planning.rows.find(r=>r.year===row.year).cohorts;
    row.cohorts.forEach((x,j)=>close(x,projected[j],1e-6,`${row.year} group ${j+1}`));
    for(const k of ['tax','grants','pensionExpense']) close(row[k],yearly.rows[i+1][k],1e-7,`${row.year} ${k}`);
  }
  assertBooks(flow,'Motala');
});

test('wages and prices rise by the stated yearly growth also when it changes between years',{skip},()=>{
  // With the capacity locked the service volume is 1, so payroll and other costs show the wage and price levels alone:
  // the two models then give the same payroll and other costs. What differs otherwise is how capacity follows demand.
  const locked={adjustment:0,costDrift:0,productivity:0};
  const flow=continuous(sourced,history,locked,revenue),yearly=annual(sourced,history,locked,revenue);
  const growth=planning.rows.slice(0,8).map(r=>r.labourCostGrowth);
  assert.ok(Math.max(...growth)-Math.min(...growth)>1,'the test needs a wage path that changes');
  for(const [i,row] of flow.rows.slice(1).entries()) {
    close(row.payroll/yearly.rows[i+1].payroll,1,1e-6,`${row.year} payroll`);
    close(row.otherOperatingExpense/yearly.rows[i+1].otherOperatingExpense,1,1e-6,`${row.year} other costs`);
  }
  // A wage shock that comes and goes: 3, 9, 0, 3 per cent. The yearly means still follow the path.
  const path={...planning,rows:planning.rows.map((r,i)=>({...r,labourCostGrowth:[3,9,0,3,3,3,3,3][i]??3}))};
  const shocked=continuous({...b,planningInputs:path},history,locked,revenue).rows;
  [3,9,0,3,3,3,3,3].forEach((g,i)=>close(shocked[i+1].payroll/shocked[i].payroll-1,g/100,1e-5,`${shocked[i+1].year} payroll growth`));
});

test('the differences from the yearly model are small and of the expected sign',{skip},()=>{
  const flow=continuous(sourced,history,{},revenue).rows,yearly=annual(sourced,history,{},revenue).rows;
  for(const i of [1,2,3,8]) {
    // Debt grows during the year, so interest is higher than on the opening debt alone, and by less than a year's borrowing would cost.
    assert.ok(flow[i].interest>yearly[i].interest,`${flow[i].year} interest`);
    assert.ok(flow[i].interest-yearly[i].interest<flow[i].borrowing*b.assumptions.interestRate/100,`${flow[i].year} interest bound`);
    // Capacity follows demand continuously and costs are counted through the year: within half a per cent of the yearly
    // model's net cost. With the capacity locked the two are equal (the wage and price test above).
    close(flow[i].cost/yearly[i].cost,1,5e-3,`${flow[i].year} net cost`);
    close(flow[i].depreciation/yearly[i].depreciation,1,5e-3,`${flow[i].year} depreciation`);
  }
});

test('optional mechanisms keep the books in continuous time',{skip},()=>{
  const sources=read('data/model-experiments.json'),income=read('data/age-income.json');
  const full={...sourced,experiments:{...sources.municipalities['0583']['2025'],novemberPopulation:43158},
    ageIncome:{weights:income.municipalities['0583']['2024'],countyRate:income.countyRate}};
  const cases={
    'per component':{revenueMode:2,ageTax:true,migrationDelta:300},
    'published path':{revenueMode:1},
    'split payroll':{splitPayroll:true,employerContributionRate:32},
    'construction':{constructionYears:2,constructionShare:0.5,investment:200},
    'inflation and rate shock':{inflationShock:3,rateShock:2,rateFixingYears:3,rateShockMonth:7},
    'cost growth and grant increase':{costDrift:0.5,grantIncrease:3},
    'working capital':{workingCapitalEnabled:true},
    'short payment terms':{workingCapitalEnabled:true,collectionDays:1,paymentDays:0,firstYearGrantAdvance:100},
    'cash policy':{liquidityPolicy:true,cashReserve:100,deferInvestmentShare:0.3,prefinanceShare:0.5},
    'project':{projectChoice:'delay',years:3},
    'observed migration':{demographyMode:'observed'}
  };
  const runs=Object.fromEntries(Object.entries(cases).map(([name,overrides])=>{
    const run=continuous(full,history,overrides,revenue);
    assertBooks(run,`Motala ${name}`);
    return [name,run.rows];
  }));
  const published=runs['published path'];
  published.slice(1).forEach((row,i)=>{close(row.tax,revenue.rows[i].tax,1e-6,'published tax');close(row.grants,revenue.rows[i].grants,1e-6,'published grants');});
  const pay=runs['split payroll'][1];
  close(pay.employerContributions/pay.wages,0.32,1e-8,'employer contributions');
  close(pay.payroll,pay.wages+pay.employerContributions,1e-8,'payroll');
  for(const row of runs['cash policy'].slice(1)) assert.ok(row.cash>=100-0.05,`${row.year} cash ${row.cash} holds the reserve`);
  // Cash above the reserve repays debt, as in the yearly model: the cash ends each year at the reserve in both.
  const idle={liquidityPolicy:true,cashReserve:20,investment:0,years:3};
  const flow=continuous(full,history,idle,revenue).rows,yearly=annual(full,history,idle,revenue).rows;
  for(const [i,row] of flow.slice(1).entries()) {
    close(row.cash,20,0.5,`${row.year} cash at the reserve`);
    close(yearly[i+1].cash,20,1e-6,`${row.year} cash at the reserve, yearly model`);
    close(row.debt,yearly[i+1].debt,15,`${row.year} debt against the yearly model`);
    assert.ok(row.debt<flow[i].debt,`${row.year} debt falls`);
  }
  const project=runs.project.slice(1);
  assert.deepEqual(project.map(r=>Math.round(r.projectPaid)),[4,0,0]);
  assert.deepEqual(project.map(r=>Math.round(r.projectCommissioned)),[0,65,0]);
  assert.deepEqual(project.map(r=>r.projectPlacesInUse),[0,144,144]);
  // Receivables settle at the payment term times the revenue flow.
  const terms=continuous(full,history,{workingCapitalEnabled:true,collectionDays:30,paymentDays:35},revenue).rows[2];
  close(terms.tradeReceivables/(terms.operatingRevenue*30/365),1,0.01,'receivables');
  close(terms.tradePayables/(terms.otherOperatingExpense*35/365),1,0.01,'payables');
});

test('fast flows are run with the implicit solver, and it agrees with DASSL',{skip},()=>{
  const overrides={workingCapitalEnabled:true,liquidityPolicy:true,cashReserve:90,years:4};
  const run=continuous(sourced,history,overrides,revenue);
  assert.ok(hasFastFlows({workingCapitalEnabled:true})&&hasFastFlows({projectPayment:4})&&!hasFastFlows({investment:400}));
  const dassl=createDirectSimulator(createSession(omc,[],{stiffMethod:'dassl'}))(sourced,history,{...overrides,timeModel:'continuous'},revenue);
  for(const [i,row] of run.rows.slice(1).entries()) for(const k of ['result','debt','cash','interest','cost']) {
    close(row[k],dassl.rows[i+1][k],0.01,`${row.year} ${k}`);
  }
  // Without fast flows the explicit solver is within 0.01 mnkr of DASSL as well. Both sessions use the same build.
  const everywhere=createDirectSimulator(createSession(omc,[],{stiffMethod:'dassl',implicitAlways:true}));
  const explicit=continuous(sourced,history,{},revenue);
  const implicit=everywhere(sourced,history,{timeModel:'continuous'},revenue);
  for(const [i,row] of explicit.rows.slice(1).entries()) for(const k of ['result','debt','cash','interest','cost']) {
    close(row[k],implicit.rows[i+1][k],0.01,`${row.year} ${k}`);
  }
  // Lower investment and a higher tax rate make the cash flow change sign during a year. The explicit solver finds
  // that moment by linear interpolation: every stock moves by up to 0.001 %, here 0.03 mnkr in the net cost.
  const turning={taxRate:22.2,investment:300,migrationDelta:150,years:5};
  const stepped=continuous(sourced,history,turning,revenue).rows,exact=everywhere(sourced,history,{...turning,timeModel:'continuous'},revenue).rows;
  assert.ok(stepped.slice(1).some(r=>r.repayment>0)&&stepped.slice(1).some(r=>r.borrowing>0),'the scenario both borrows and repays');
  for(const [i,row] of stepped.slice(1).entries()) for(const k of ['result','debt','cash','interest','cost']) {
    close(row[k],exact[i+1][k],0.1,`${row.year} ${k}`);
  }
});

test('single-year ages run in continuous time for the calibrated and the observed flows',{skip},()=>{
  const sources=read('data/model-experiments.json');
  const full={...sourced,experiments:sources.municipalities['0583']['2025']};
  const yearly=annual(full,history,{demographyMode:'cohort',years:3},revenue).rows;
  const flow=continuous(full,history,{demographyMode:'cohort',years:3},revenue);
  assertBooks(flow,'Motala cohort');
  // Deaths and moves during the year instead of at its end: the two age models stay within a tenth of a per cent.
  for(const [i,row] of flow.rows.slice(1).entries()) {
    close(row.population/yearly[i+1].population,1,1e-3,`${row.year} population`);
    assert.ok(row.population80Plus>0&&row.population80Plus<row.cohorts[4]);
  }
  const observed=continuous(full,history,{demographyMode:'cohort-observed',years:2},revenue);
  const extra=continuous(full,history,{demographyMode:'cohort-observed',years:2,migrationDelta:100},revenue);
  assertBooks(observed,'Motala cohort-observed');
  close(extra.rows[1].migration-observed.rows[1].migration,100,0.5,'changed net migration');
});

test('the exported Scenario.mo is the scenario the page ran',{skip},()=>{
  const overrides={timeModel:'continuous',taxRate:22.2,investment:300,migrationDelta:150,years:5};
  const source=modelicaSource(sourced,history,overrides,revenue);
  assert.match(source,/extends Motala\.Continuous\(/);
  assert.match(source,/mortalityRates=\{/);
  assert.doesNotMatch(source,/deathRates=/);
  assert.equal(String(omc.omc_eval(`loadString(${JSON.stringify(source.replace('model Scenario','model ExportedScenario').replace('end Scenario','end ExportedScenario'))})`)).trim(),'true');
  const keys=['population','tax','grants','cost','result','debt','cash'];
  const exported=runModel(omc,'ExportedScenario',{start:2025,stop:2030,intervals:60,method:'rungekutta'},keys);
  const page=simulate(sourced,history,overrides,revenue).rows;
  // The page's wrapper holds the last year's wage and price growth for a hundred years; the export ends at the horizon.
  for(const [i,row] of exported.entries()) for(const k of keys) close(page[i+1][k],row[k],0.005,`${row.year} ${k}`);
  assert.match(modelicaSource(sourced,history,{timeModel:'annual'},revenue),/extends Motala\.Annual\(/);
});

test('all 13 municipalities run eight years in continuous time from the 2024 and 2025 accounts',{skip},()=>{
  for(const code of Object.keys(municipalities)) for(const [year,file] of [[2024,'web-2024.json'],[2025,'web.json']]) {
    const {baseline,history:local,planning:inputs}=read(`data/municipalities/${code}/${file}`);
    const extended=inputs?extendPlanning(inputs,year+8):null;
    const run=continuous({...baseline,planningInputs:extended},local);
    assert.equal(run.rows.at(-1).year,year+8,code);
    assertBooks(run,code);
    const yearly=annual({...baseline,planningInputs:extended},local).rows;
    for(const [i,row] of run.rows.slice(1).entries()) {
      const projected=extended?.rows.find(r=>r.year===row.year)?.cohorts;
      if(projected) close(row.population,sum(projected),1e-6,`${code} ${row.year} population`);
      else close(row.population/yearly[i+1].population,1,2e-3,`${code} ${row.year} population against the yearly model`);
      close(row.cost/yearly[i+1].cost,1,0.01,`${code} ${row.year} net cost against the yearly model`);
    }
  }
});

const native=process.env.OMC||spawnSync('which',['omc'],{encoding:'utf8'}).stdout.trim();
test('twelve Runge-Kutta steps a year in the browser give native OpenModelica\'s DASSL',{skip:skip||(!native&&'native OpenModelica (OMC or omc on PATH) not found')},()=>{
  const keys=['population','tax','grants','cost','depreciation','interest','result','debt','cash','assets'];
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'continuous-'));
  try {
    const mo=name=>JSON.stringify(fileURLToPath(new URL(`../modelica/${name}`,import.meta.url)));
    fs.writeFileSync(path.join(dir,'run.mos'),`loadFile(${mo('Kommunekonomi.mo')}); loadFile(${mo('Motala.mo')}); getErrorString();
simulate(Motala.Continuous, startTime=2025, stopTime=2033, numberOfIntervals=96, method="dassl", tolerance=1e-8, outputFormat="csv", variableFilter="${keys.join('|')}"); getErrorString();\n`);
    execFileSync(native,['run.mos'],{cwd:dir,stdio:'pipe'});
    const [header,...lines]=fs.readFileSync(path.join(dir,'Motala.Continuous_res.csv'),'utf8').trim().split('\n');
    const names=header.split(',').map(x=>x.replace(/"/g,''));
    const reference=new Map();
    for(const line of lines) {
      const values=line.split(',').map(Number),t=values[0];
      if(Math.abs(t-Math.round(t))<1e-9) reference.set(Math.round(t),Object.fromEntries(names.map((n,i)=>[n,values[i]])));
    }
    const browser=runModel(omc,'Motala.Continuous',{start:2025,stop:2033,intervals:96,method:'rungekutta'},keys);
    for(const row of browser) for(const k of keys) close(row[k],reference.get(row.year)[k],0.01,`${row.year} ${k}`);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
