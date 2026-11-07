import fs from 'node:fs';
import {calibrate,naturalStep,sum,reconcileHistory} from '../site/src/engine.js';
const rows=reconcileHistory(JSON.parse(fs.readFileSync(new URL('../data/history.json',import.meta.url))).rows);
const results=[];
for(let i=2;i<rows.length;i++) {
  const train=rows.slice(0,i),last=train.at(-1),previous=train.at(-2),c=calibrate(train);
  const predicted=naturalStep(last.population,last.births,c.deathRates).map((p,j)=>p+c.migration[j]);
  const actual=sum(rows[i].population),persistence=sum(last.population),trend=persistence+(persistence-sum(previous.population));
  results.push({origin:last.year,target:rows[i].year,actual,cohort:sum(predicted),persistence,trend,cohortAgeMAE:sum(predicted.map((p,j)=>Math.abs(p-rows[i].population[j])))/5});
}
const scores=Object.fromEntries(['cohort','persistence','trend'].map(k=>[k,sum(results.map(r=>Math.abs(r[k]-r.actual)))/results.length]));
const wins=scores.cohort<Math.min(scores.persistence,scores.trend);
const conclusion=wins?'Åldersmodellen har lägre fel i dessa tre år. Underlaget är för litet för att visa säker förbättring.':'Åldersmodellen slår inte det bästa enkla alternativet i dessa tre år. Det behövs bättre åldersdata och fler utvärderingsår.';
const output={method:'One-year rolling-origin retrospective population test; no true historical release vintages',results,scores,conclusion,forecastSuperiorityProven:false};
const serialized=JSON.stringify(output,null,2)+'\n';
fs.writeFileSync(new URL('../data/backtest.json',import.meta.url),serialized);
if(fs.existsSync(new URL('../site/dist/',import.meta.url)))fs.writeFileSync(new URL('../site/dist/backtest.json',import.meta.url),serialized);
console.log(JSON.stringify(output,null,2));
