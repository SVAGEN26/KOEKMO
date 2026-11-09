// The model view draws Motala.Annual by hand. These checks keep it tied to the model:
// every arrow is a connect() in Kommunekonomi.Annual, and every component's code can be shown.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {COMPONENTS,FLOWS,modelicaSection} from '../site/src/model-view.js';

const source=fs.readFileSync(new URL('../modelica/Kommunekonomi.mo',import.meta.url),'utf8');
const annual=source.slice(source.indexOf('partial model Annual'));
const compact=annual.replace(/\s+/g,'');
const app=fs.readFileSync(new URL('../site/src/app.js',import.meta.url),'utf8');

test('every component is a model in Kommunekonomi.Components and instantiated in Annual',()=>{
  for(const c of COMPONENTS) {
    const section=modelicaSection(source,c.model);
    assert.ok(section?.startsWith(`model ${c.model}`),c.model);
    assert.ok(!section.includes('annotation('),`${c.model} code should stop before its annotation`);
    assert.match(annual,new RegExp(`Components\\.${c.model} ${c.id}\\(`),`${c.id} instance`);
  }
});

test('every arrow is a connect() in Kommunekonomi.Annual',()=>{
  for(const f of FLOWS) {
    const m=f.binding.match(/^connect\((\w+)\.(\w+), (\w+)\.(\w+)\)$/);
    assert.ok(m,f.binding);
    assert.ok(compact.includes(`connect(${m[1]}.${m[2]},${m[3]}.${m[4]})`),`${f.binding} not found`);
    for(const instance of [m[1],m[3]]) assert.ok(instance==='scenario'||COMPONENTS.some(c=>c.id===instance),instance);
  }
});

test('every editable assumption is a scenario-lab control',()=>{
  for(const c of COMPONENTS) for(const key of c.keys) assert.ok(app.includes(`['${key}',`),key);
});
