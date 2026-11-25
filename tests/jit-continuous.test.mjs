// The page runs the continuous model (Motala.Continuous) by default. These tests run it in the staged
// compiler the way the page does and check it against the library's own calibration, against SCB's and
// SKR's inputs, and against native OpenModelica.
// Needs site/omc-web (scripts/stage_omc.py); skipped when the compiler is not staged.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync,spawnSync} from 'node:child_process';
import {boot,read,runModel,staged,skip} from './support/omc-node.mjs';
import {createSession,CONTINUOUS_METHOD} from '../site/src/omc-session.js';
import {createDirectSimulator} from '../site/src/jit-engine.js';
import {extendPlanning,sum} from '../site/src/scenario-inputs.js';
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
const balances=['populationBalance','assetBalance','cashBalance','debtBalance'];
function assertBooks(run,label) {
  for(const row of run.rows.slice(1)) {
    // The population balance within 1e-8 of the population (the solver's tolerance on many small stocks; Ydre 2026:
    // 1e-5 persons of 3 500), the money balances within 1e-6 mnkr.
    for(const k of balances) assert.ok(Math.abs(row[k])<(k==='populationBalance'?Math.max(1e-6,1e-8*row.population):1e-6),`${label} ${row.year} ${k} = ${row[k]}`);
    const parts=row.tax+row.grants-row.cost-row.depreciation+b.financialIncome-row.interest-row.otherFinancialExpense;
    if(label.startsWith('Motala')) assert.ok(Math.abs(row.result-parts)<1e-6,`${label} ${row.year} result ${row.result} vs parts ${parts}`);
  }
}
const close=(actual,expected,tolerance,message)=>assert.ok(Math.abs(actual-expected)<=tolerance,`${message}: ${actual} vs ${expected}`);

test('the page has only continuous time',()=>{
  const html=fs.readFileSync(new URL('../site/src/index.html',import.meta.url),'utf8');
  assert.doesNotMatch(html,/id="time-model"/);
  assert.doesNotMatch(html,/Årssteg/);
});

test('the page\'s calibration is the library\'s: site inputs give Motala.Continuous as written',{skip},()=>{
  // Motala's liquidity rule from data/liquidity.json, as the page attaches it; Motala.Continuous has the same in Modelica.
  const site=continuous({...b,planningInputs:null,liquidity:read('data/liquidity.json').municipalities['0583']},history);
  const keys=['population','births','deaths','migration','cost','payroll','otherOperatingExpense','operatingRevenue','depreciation',
    'tax','grants','result','debt','cash','assets','interest','borrowing','repayment','educationIndex','careIndex'];
  const model=runModel(omc,'Motala.Continuous',{start:2025,stop:2033,intervals:96,method:CONTINUOUS_METHOD},keys);
  assert.equal(site.rows.length,9);
  for(const [i,row] of model.entries()) for(const k of keys) {
    close(site.rows[i+1][k],row[k],1e-8*Math.max(1,Math.abs(row[k])),`${row.year} ${k}`);
  }
  assertBooks(site,'Motala');
});

test('with SCB\'s projection the population is the projection at every year end',{skip},()=>{
  const flow=continuous(sourced,history,{},revenue);
  for(const [i,row] of flow.rows.slice(1).entries()) {
    const projected=planning.rows.find(r=>r.year===row.year).cohorts;
    // The solver controls its own steps to a relative tolerance of 1e-6: a thousandth of a person and a hundred kronor.
    row.cohorts.forEach((x,j)=>close(x,projected[j],1e-3,`${row.year} group ${j+1}`));
  }
  assertBooks(flow,'Motala');
});

test('wages and prices rise by the stated yearly growth also when it changes between years',{skip},()=>{
  // With the capacity locked the service volume is 1, so payroll shows the wage level alone.
  const locked={adjustment:0,costDrift:0,productivity:0};
  // A wage shock that comes and goes: 3, 9, 0, 3 per cent. The yearly means still follow the path.
  const path={...planning,rows:planning.rows.map((r,i)=>({...r,labourCostGrowth:[3,9,0,3,3,3,3,3][i]??3}))};
  const shocked=continuous({...b,planningInputs:path},history,locked,revenue).rows;
  [3,9,0,3,3,3,3,3].forEach((g,i)=>close(shocked[i+1].payroll/shocked[i].payroll-1,g/100,1e-5,`${shocked[i+1].year} payroll growth`));
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
    'cash policy':{liquidityPolicy:true,reserveDays:10,creditLine:0,reserveAdjustmentTime:0,deferInvestmentShare:0.3,prefinanceShare:0.5},
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
  // The reserve is days of the year's payments (operations, investment, interest) less the credit line.
  const reserveOf=(row,days,credit=0)=>Math.max(0,days/365*(row.payroll+row.pensionCashPayments+row.otherOperatingExpense+row.investment+row.interest)-credit);
  // In continuous time the reserve follows the payments at each moment, so the year-end cash is near the yearly figure.
  for(const row of runs['cash policy'].slice(1)) assert.ok(row.cash>=0.97*reserveOf(row,10),`${row.year} cash ${row.cash} holds the reserve`);
  // Cash above the reserve repays debt: the cash ends each year at the reserve.
  const idle={liquidityPolicy:true,reserveDays:2,creditLine:0,reserveAdjustmentTime:0,investment:0,years:3};
  const flow=continuous(full,history,idle,revenue).rows;
  for(const [i,row] of flow.slice(1).entries()) {
    close(row.cash,reserveOf(row,2),1,`${row.year} cash at the reserve`);
    assert.ok(row.debt<flow[i].debt,`${row.year} debt falls`);
  }
  const project=runs.project.slice(1);
  assert.deepEqual(project.map(r=>Math.round(r.projectPaid)),[4,0,0]);
  assert.deepEqual(project.map(r=>Math.round(r.projectCommissioned)),[0,65,0]);
  assert.deepEqual(project.map(r=>r.projectPlacesInUse),[0,144,144]);
  // Receivables and payables settle at the payment term times the flow at the year's end. The year's total is the flow's
  // mean, which a growing flow exceeds by half a year's growth at the end: within 2 % (other costs 2027: 1.0 %).
  const terms=continuous(full,history,{workingCapitalEnabled:true,collectionDays:30,paymentDays:35},revenue).rows[2];
  close(terms.tradeReceivables/(terms.operatingRevenue*30/365),1,0.02,'receivables');
  close(terms.tradePayables/(terms.otherOperatingExpense*35/365),1,0.02,'payables');
});

test('the page\'s solver agrees with DASSL, with and without fast flows',{skip},()=>{
  // Both sessions use the same loaded classes; the second builds the wrapper again for DASSL.
  const dassl=createDirectSimulator(createSession(omc,[],{method:'dassl'}));
  const compare=(overrides,tolerance,label)=>{
    const page=continuous(sourced,history,overrides,revenue).rows,reference=dassl(sourced,history,{...overrides,timeModel:'continuous'},revenue).rows;
    for(const [i,row] of page.slice(1).entries()) for(const k of ['result','debt','cash','interest','cost']) {
      close(row[k],reference[i+1][k],tolerance,`${label} ${row.year} ${k}`);
    }
    return page;
  };
  assert.equal(CONTINUOUS_METHOD,'ida');
  compare({},0.01,'base path');
  // Payment terms of days and a cash reserve refilled within a month: flows too fast for a few explicit steps a year.
  compare({workingCapitalEnabled:true,liquidityPolicy:true,reserveDays:10,creditLine:0,reserveAdjustmentTime:0,years:4},0.01,'fast flows');
  // Lower investment and a higher tax rate make the cash flow change sign during a year.
  const turning=compare({taxRate:22.2,investment:300,migrationDelta:150,years:5},0.01,'turning');
  assert.ok(turning.slice(1).some(r=>r.repayment>0)&&turning.slice(1).some(r=>r.borrowing>0),'the scenario both borrows and repays');
});

test('single-year ages run in continuous time for the calibrated and the observed flows',{skip},()=>{
  const sources=read('data/model-experiments.json');
  const full={...sourced,experiments:sources.municipalities['0583']['2025']};
  const flow=continuous(full,history,{demographyMode:'cohort',years:3},revenue);
  const groups=continuous(full,history,{years:3},revenue);
  assertBooks(flow,'Motala cohort');
  // Single-year ages and the five groups are calibrated differently and drift apart slowly: Motala 0.2 % in 2026,
  // 0.6 % in 2027. Two per cent is the bound.
  for(const [i,row] of flow.rows.slice(1).entries()) {
    close(row.population/groups.rows[i+1].population,1,2e-2,`${row.year} population`);
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
  // The calibration is computed by the library's functions, in the exported model as in the page's wrapper.
  assert.match(source,/mortalityRates=Kommunekonomi\.Data\.deathRatesPerYear\(/);
  assert.match(source,/residualMigrationPath=Kommunekonomi\.Data\.projectionResiduals\(/);
  assert.doesNotMatch(source,/deathRates=/);
  assert.equal(String(omc.omc_eval(`loadString(${JSON.stringify(source.replace('model Scenario','model ExportedScenario').replace('end Scenario','end ExportedScenario'))})`)).trim(),'true');
  const keys=['population','tax','grants','cost','result','debt','cash'];
  const exported=runModel(omc,'ExportedScenario',{start:2025,stop:2030,intervals:60,method:CONTINUOUS_METHOD},keys);
  const page=simulate(sourced,history,overrides,revenue).rows;
  // The page's wrapper holds the last year's wage and price growth for a hundred years; the export ends at the horizon.
  // Flows agree within 1e-4. Cash and debt within 0.5 mnkr: the export ends at the horizon, and in its last year the wage
  // and price rate leans on the next year's growth, which the liquidity reserve follows.
  for(const [i,row] of exported.entries()) for(const k of keys) close(page[i+1][k],row[k],['cash','debt'].includes(k)?0.5:Math.max(0.005,1e-4*Math.abs(row[k])),`${row.year} ${k}`);
  assert.throws(()=>modelicaSource(sourced,history,{timeModel:'annual'},revenue),/kontinuerlig/);
});

test('all 13 municipalities run eight years in continuous time from the 2024 and 2025 accounts',{skip},()=>{
  for(const code of Object.keys(municipalities)) for(const [year,file] of [[2024,'web-2024.json'],[2025,'web.json']]) {
    const {baseline,history:local,planning:inputs}=read(`data/municipalities/${code}/${file}`);
    const extended=inputs?extendPlanning(inputs,year+8):null;
    const run=continuous({...baseline,planningInputs:extended},local);
    assert.equal(run.rows.at(-1).year,year+8,code);
    assertBooks(run,code);
    for(const row of run.rows.slice(1)) {
      const projected=extended?.rows.find(r=>r.year===row.year)?.cohorts;
      if(projected) close(row.population,sum(projected),1e-6,`${code} ${row.year} population`);
      assert.ok(row.cost>0&&Number.isFinite(row.result),`${code} ${row.year}`);
    }
  }
});

const native=process.env.OMC||spawnSync('which',['omc'],{encoding:'utf8'}).stdout.trim();
test('the page\'s solver in the browser gives native OpenModelica\'s DASSL',{skip:skip||(!native&&'native OpenModelica (OMC or omc on PATH) not found')},()=>{
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
    const browser=runModel(omc,'Motala.Continuous',{start:2025,stop:2033,intervals:96,method:CONTINUOUS_METHOD},keys);
    for(const row of browser) for(const k of keys) close(row[k],reference.get(row.year)[k],0.01,`${row.year} ${k}`);
  } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
