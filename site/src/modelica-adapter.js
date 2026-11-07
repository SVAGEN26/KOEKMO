import {prepareScenario} from './scenario-inputs.js';
const literal=x=>typeof x==='boolean'?String(x):Array.isArray(x)?`{${x.map(literal).join(',')}}`:String(x);
export function modelicaSource(b,history,overrides={},path=null) {
  const prepared=prepareScenario(b,history,overrides,path);
  const fields={horizon:prepared.assumptions.years,...prepared.fields};
  return `within ;\nmodel Scenario\n  extends Motala.Annual(\n    ${Object.entries(fields).map(([k,v])=>`${k}=${literal(v)}`).join(',\n    ')});\nend Scenario;\n`;
}
