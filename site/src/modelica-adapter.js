import {DEFAULT_MUNICIPALITY,municipalities,cohortModifiers} from './municipalities.js';
import {prepareScenario} from './scenario-inputs.js';
const literal=x=>typeof x==='boolean'?String(x):Array.isArray(x)?`{${x.map(literal).join(',')}}`:String(x);
export function modelicaSource(b,history,overrides={},path=null) {
  const municipality=b.municipality??DEFAULT_MUNICIPALITY;
  const settings=municipalities[municipality];
  if(!settings) throw Error('Kommunen saknar modellpaket.');
  const prepared=prepareScenario(b,history,overrides,path);
  const fields={horizon:prepared.assumptions.years,...prepared.fields};
  const data=`${settings.packageName}.Data`,year=b.baseYear;
  const shares=municipality===DEFAULT_MUNICIPALITY?`${data}.SCB.olderShares(${data}.SCB.motala${year}.population)`:`${data}.olderShares${year}`;
  const base=year===2025?'':`base=${data}.${settings.packageName.toLowerCase()}${year},
    olderShares=${shares},
    `;
  const ageModel=prepared.cohort?`redeclare Kommunekonomi.Continuous.CohortDemography demography(
      ${cohortModifiers(settings.packageName,year)}${prepared.ageMigration?
        `, residualMigration=${literal(prepared.ageMigration['demography.residualMigration'])},
        observedDeltaShape=${literal(prepared.ageMigration['demography.observedDeltaShape'])}, useObservedDeltaShape=${prepared.ageMigration['demography.useObservedDeltaShape']}`:''}),\n    `:'';
  // The model takes its death rates as mortalityRates; a month between the points plotted.
  delete fields.deathRates;
  return `within ;\nmodel Scenario\n  extends ${settings.packageName}.Continuous(\n    ${base}${ageModel}${Object.entries(fields).map(([k,v])=>`${k}=${literal(v)}`).join(',\n    ')});\n  annotation(experiment(StartTime=${b.baseYear}, StopTime=${b.baseYear+fields.horizon}, Interval=${1/12}));\nend Scenario;\n`;
}
