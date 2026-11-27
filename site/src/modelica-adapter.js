import {DEFAULT_MUNICIPALITY,municipalities,cohortModifiers} from './municipalities.js';
import {prepareScenario} from './scenario-inputs.js';
const literal=x=>typeof x==='boolean'||typeof x==='string'?String(x):Array.isArray(x)?`{${x.map(literal).join(',')}}`:String(x);
export function modelicaSource(b,history,overrides={},path=null) {
  const municipality=b.municipality??DEFAULT_MUNICIPALITY;
  const settings=municipalities[municipality];
  if(!settings) throw Error('Kommunen saknar modellpaket.');
  const prepared=prepareScenario(b,history,overrides,path);
  const fields={horizon:prepared.assumptions.years,...prepared.fields};
  const data=`Kommunekonomi.Municipalities.${settings.packageName}.Data`,year=b.baseYear;
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
  // The base-year record carries the group's and the municipality's own migration rates; the wrapper's copies go.
  delete fields.groupMigration; delete fields.ownMigration;
  fields.residualMigration=useObservedMigration?observedMigration
    :`Kommunekonomi.Data.calibratedMigrationRates(${literal(historyCohorts)},${literal(historyTotals)},${literal(historyBirths)},mortalityRates,ageProfile[1:2,:],olderShares)+migrationGroupWeight*(base.groupMigration-base.ownMigration).*p0`;
  // The revenue path too: SKR's rows become a call of the library's function, declared in the scenario model.
  const {sourcedRevenue,sourcedRevenueYears,regulationDecidedYears,stateFrame,taxBaseGrowthPath}=fields;
  for(const k of ['sourcedRevenue','sourcedRevenueYears','regulationDecidedYears','stateFrame','taxBaseGrowthPath']) delete fields[k];
  Object.assign(fields,{referenceTax:'revenuePath[:,1]',referenceGrants:'revenuePath[:,2]',referencePopulation:'revenuePath[:,3]'});
  if(fields.importedRevenueMode===2) fields.importedComponents='revenuePath[:,4:6]';
  const revenue=`  parameter Real revenuePath[${fields.horizon},6]=Kommunekonomi.Data.sourcedRevenue(${literal(sourcedRevenue)},${sourcedRevenueYears},${regulationDecidedYears},${stateFrame},${literal(taxBaseGrowthPath)},nationalPopulationPath)\n    "Intäktsbanan: skatt, bidrag, folkmängd, skatt före slutavräkning, inkomstutjämning och regleringspost";\n`;
  if(projectedCohorts) fields.residualMigrationPath=`Kommunekonomi.Data.projectionResiduals(p0,${literal(projectedCohorts)},${literal(followProjection)},births0,mortalityRates,ageProfile[3:${fields.horizon}+2,:],olderShares,residualMigration)`;
  return `within ;\nmodel Scenario\n  extends Kommunekonomi.Municipalities.${settings.packageName}.Continuous(\n    ${base}${ageModel}${Object.entries(fields).map(([k,v])=>`${k}=${literal(v)}`).join(',\n    ')});\n${revenue}  annotation(experiment(StartTime=${b.baseYear}, StopTime=${b.baseYear+fields.horizon}, Interval=${1/12}));\nend Scenario;\n`;
}
