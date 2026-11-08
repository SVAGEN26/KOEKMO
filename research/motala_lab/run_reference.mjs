// Execute the immutable JavaScript reference, not the editable dashboard engine.
import fs from 'node:fs';
import {simulate} from '../reference/m0/engine.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../reference/m0/${name}`,import.meta.url)));
const run=simulate(read('baseline.json'),read('history.json').rows);
console.log(JSON.stringify(run));
