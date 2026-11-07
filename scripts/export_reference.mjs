import fs from 'node:fs';
import {simulate} from '../site/src/engine.js';
import {modelicaSource} from '../site/src/modelica-adapter.js';
const b=JSON.parse(fs.readFileSync(new URL('../data/baseline.json',import.meta.url))),{rows:history}=JSON.parse(fs.readFileSync(new URL('../data/history.json',import.meta.url)));
b.planningInputs=JSON.parse(fs.readFileSync(new URL('../data/planning-inputs.json',import.meta.url)));
const overrides=JSON.parse(process.argv[2]||'{}');
console.log(JSON.stringify({source:modelicaSource(b,history,overrides,b.planningInputs.revenuePath??null),run:simulate(b,history,overrides,b.planningInputs.revenuePath??null)}));
