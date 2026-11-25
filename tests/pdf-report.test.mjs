import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createDirectSimulator} from '../site/src/jit-engine.js';
import {boot,staged,skip} from './support/omc-node.mjs';
import {buildScenarioReport} from '../site/src/pdf-report.js';
const read=name=>JSON.parse(fs.readFileSync(new URL('../data/'+name,import.meta.url)));
const b=read('baseline.json'),{rows:history}=read('history.json');b.planningInputs=read('planning-inputs.json');
// Runs of the model in continuous time, as the page makes them, are the report's input.
const simulate=staged?createDirectSimulator((await boot()).session):null;
function snapshot(overrides={},revenuePath=b.planningInputs.revenuePath){
 return {baseline:b,run:simulate(b,history,overrides,revenuePath),referenceRun:simulate(b,history,{},revenuePath),revenuePath,generatedAt:'2026-11-06T12:00:00Z',charts:Object.fromEntries(['result-chart','debt-chart','population-chart','demand-chart','sensitivity'].map(id=>[id,`<svg data-chart="${id}" viewBox="0 0 760 255"><path d="M0 0L10 10"/></svg>`]))};
}
test('report includes every graph with active values and distinct SKR reference',{skip},()=>{
 const state=snapshot({interestRate:5,investment:321,migrationDelta:120});
 const html=buildScenarioReport(state);
 assert.equal((html.match(/class="report-page"/g)||[]).length,6);
 for(const id of Object.keys(state.charts))assert.ok(html.includes(`data-chart="${id}"`));
 assert.match(html,/5 %/);assert.match(html,/321 mnkr/);assert.match(html,/120 personer/);
 assert.match(html,/Effektiva årsvisa antaganden/);assert.match(html,/Referens: skatt/);
 assert.match(html,/Scenario: summa/);assert.match(html,/Bättre prognosprecision än SKR är inte visad/);
 const total=state.run.rows.at(-1).result;
 const formatted=new Intl.NumberFormat('sv-SE',{maximumFractionDigits:2}).format(total);
 assert.ok(html.includes(formatted));
 assert.match(html,/1 november|1 November/);
});
test('report accurately distinguishes source-off, no revenue import and missing graphs',{skip},()=>{
 const off=structuredClone(b);delete off.planningInputs;
 const html=buildScenarioReport({baseline:off,run:simulate(off,history),referenceRun:simulate(off,history),generatedAt:'2026-11-06'});
 assert.match(html,/Illustrativ intäktsbana/);assert.match(html,/Ingen kommunal intäktsimport aktiv/);
 assert.match(html,/Grafen kunde inte hämtas/);
 assert.doesNotMatch(html,/Importerad Motala-referens, version/);
});
test('report escapes imported labels and preserves a frozen parameter snapshot',{skip},()=>{
 const state=snapshot(),before=JSON.stringify(state);
 state.revenuePath=structuredClone(state.revenuePath);state.revenuePath.populationReference='<img src=x onerror=alert(1)>';
 const frozen=JSON.stringify(state);
 const html=buildScenarioReport(state);
 assert.equal(JSON.stringify(state),frozen);
 assert.match(html,/&lt;img src=x onerror=alert\(1\)&gt;/);
 assert.doesNotMatch(html,/<img src=x/);
 assert.equal(JSON.stringify(snapshot()),before);
 assert.throws(()=>buildScenarioReport({baseline:b}),/beräknat scenario/);
});
