import {DEFAULT_MUNICIPALITY,municipalities,cohortModifiers} from './municipalities.js';
import {prepareScenario} from './scenario-inputs.js';
const literal=x=>typeof x==='boolean'||typeof x==='string'?String(x):Array.isArray(x)?`{${x.map(literal).join(',')}}`:String(x);
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
  // The population calibration is computed in Modelica, as in the page's wrapper: the history and the projection become
  // calls of the library's functions, so the exported model calibrates itself the same way.
  const {historyCohorts,historyTotals,historyBirths,historyDeaths,useObservedMigration,observedMigration,projectedCohorts,followProjection}=fields;
  for(const k of ['deathRates','historyCohorts','historyTotals','historyBirths','historyDeaths','useObservedMigration','observedMigration','projectedCohorts','followProjection']) delete fields[k];
  fields.mortalityRates=`Kommunekonomi.Data.deathRatesPerYear(${literal(historyCohorts)},${literal(historyTotals)},${historyDeaths})`;
  fields.residualMigration=useObservedMigration?observedMigration
    :`Kommunekonomi.Data.calibratedMigrationRates(${literal(historyCohorts)},${literal(historyTotals)},${literal(historyBirths)},mortalityRates,ageProfile[1:2,:],olderShares)`;
  if(projectedCohorts) fields.residualMigrationPath=`Kommunekonomi.Data.projectionResiduals(p0,${literal(projectedCohorts)},${literal(followProjection)},births0,mortalityRates,ageProfile[3:${fields.horizon}+2,:],olderShares,residualMigration)`;
  return `within ;\nmodel Scenario\n  extends ${settings.packageName}.Continuous(\n    ${base}${ageModel}${Object.entries(fields).map(([k,v])=>`${k}=${literal(v)}`).join(',\n    ')});\n  annotation(experiment(StartTime=${b.baseYear}, StopTime=${b.baseYear+fields.horizon}, Interval=${1/12}));\nend Scenario;\n`;
}
