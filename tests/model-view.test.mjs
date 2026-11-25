// The model view draws Kommunekonomi.Continuous.Economy by hand. These checks keep it tied to the model:
// every arrow is a connection or equation in Economy, and every component's code can be shown.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {COMPONENTS,FLOWS,modelicaSection} from '../site/src/model-view.js';

const source=fs.readFileSync(new URL('../modelica/Kommunekonomi.mo',import.meta.url),'utf8');
const continuous=source.slice(source.indexOf('package Continuous '));
const economy=continuous.slice(continuous.indexOf('partial model Economy'));
const compact=economy.replace(/\s+/g,'');
const app=fs.readFileSync(new URL('../site/src/app.js',import.meta.url),'utf8');

test('every component is a model in Kommunekonomi.Continuous (Revenue in Components) and instantiated in Economy',()=>{
  for(const c of COMPONENTS) {
    const section=modelicaSection(c.id==='revenues'?source:continuous,c.model);
    assert.ok(section?.startsWith(`model ${c.model}`),c.model);
    assert.ok(!section.includes('annotation('),`${c.model} code should stop before its annotation`);
    assert.match(economy,new RegExp(`(Components\\.)?${c.model} ${c.id}\\(`),`${c.id} instance`);
  }
});

test('every arrow is a connection or an equation in Kommunekonomi.Continuous.Economy',()=>{
  for(const f of FLOWS) {
    assert.ok(compact.includes(f.binding.replace(/\s+/g,'')),`${f.binding} not found`);
    const m=f.binding.match(/^connect\((\w+)\.(\w+), (\w+)\.(\w+)\)$/);
    if(m) for(const instance of [m[1],m[3]]) assert.ok(['scenario','payments'].includes(instance)||COMPONENTS.some(c=>c.id===instance),instance);
  }
});

test('every editable assumption is a scenario-lab control',()=>{
  for(const c of COMPONENTS) for(const key of c.keys) assert.ok(app.includes(`['${key}',`),key);
});
