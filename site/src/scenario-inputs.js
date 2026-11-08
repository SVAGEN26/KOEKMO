// Validation, historical calibration and source-data preparation. No forecast simulation.
export const sum = a => a.reduce((s,x)=>s+x,0);
export function reconcileHistory(history) {
  return history.map(row=>({...row,population:row.population.map(p=>p*(row.reportedTotal??sum(row.population))/sum(row.population))}));
}
export function mortality(row) {
  const d=[0.0004,0.0001,0.0002,0.0018,0];
  d[4]=(row.deaths-sum(row.population.slice(0,4).map((x,i)=>x*d[i])))/row.population[4];
  return d;
}
export function naturalStep(pop, births, deathRates) {
  const survivors=pop.map((p,i)=>p*(1-deathRates[i]));
  const out=survivors.map((p,i)=>i<4?p/[7,9,3,46][i]:0);
  return survivors.map((p,i)=>p-out[i]+(i?out[i-1]:births));
}
export function calibrate(history) {
  history=reconcileHistory(history);
  if(history.length<2) throw Error('At least two completed years are required');
  const rates=mortality(history.at(-1));
  const residuals=history.slice(-3).slice(1).map((row,i)=>{
    const previous=history.slice(-3)[i];
    const natural=naturalStep(previous.population,row.births,rates);
    return row.population.map((p,j)=>p-natural[j]);
  });
  return {deathRates:rates,migration:rates.map((_,i)=>sum(residuals.map(r=>r[i]))/residuals.length)};
}
export function validate(b,a) {
  const keys=['years','taxGrowth','grantGrowth','wageGrowth','priceGrowth','pensionGrowth','operatingRevenueGrowth','productivity','migrationDelta','birthChange','interestRate','taxRate','investment','adjustment','equalisationOffset','fixedShare','populationRevenueElasticity'];
  for(const k of keys) if(!Number.isFinite(a[k])) throw Error(`Invalid assumption: ${k}`);
  if(a.years<1||a.years>30||!Number.isInteger(a.years)) throw Error('Forecast horizon must be 1–30 years');
  for(const k of ['taxGrowth','grantGrowth','wageGrowth','priceGrowth','pensionGrowth','operatingRevenueGrowth','productivity']) if(a[k]<=-100||a[k]>100) throw Error(`Rate outside supported range: ${k}`);
  if(a.birthChange < -100||a.birthChange>100||a.interestRate<0||a.interestRate>30||a.taxRate<=0||a.taxRate>40||a.investment<0||Math.abs(a.migrationDelta)>3000) throw Error('Scenario outside supported ranges');
  for(const k of ['adjustment','equalisationOffset','fixedShare']) if(a[k]<0||a[k]>1) throw Error(`Fraction outside [0,1]: ${k}`);
  for(const [k,n] of [['sectorCosts',3],['migrationWeights',5],['educationWeights',3]]) if(!Array.isArray(a[k])||a[k].length!==n||a[k].some(x=>!Number.isFinite(x)||x<0)) throw Error(`Invalid vector: ${k}`);
  if(Math.abs(sum(a.sectorCosts)-b.cashCost)>0.001) throw Error('Sector weights must reconcile to base net operating costs');
  for(const k of ['migrationWeights','educationWeights']) if(Math.abs(sum(a[k])-1)>1e-9) throw Error(`${k} must sum to one`);
  for(const k of ['pensionExpensePath','pensionCashPaymentsPath']) {
    if(a[k]!=null && (!Array.isArray(a[k])||a[k].length!==a.years||a[k].some(x=>!Number.isFinite(x)||x<0))) throw Error(`${k} must contain one nonnegative mnkr amount per forecast year`);
  }
  const o=b.operatingAccounts;
  for(const k of ['payrollExcludingPensions','pensionExpense','otherOperatingExpense','operatingRevenue']) if(!Number.isFinite(o?.[k])||o[k]<0) throw Error(`Invalid operating account: ${k}`);
  if(!Number.isFinite(o.netCostRoundingAdjustment)||Math.abs(o.payrollExcludingPensions+o.pensionExpense+o.otherOperatingExpense-o.operatingRevenue+o.netCostRoundingAdjustment-b.cashCost)>1e-7) throw Error('Operating accounts do not reconcile to reported net cost');
  if(!Number.isFinite(b.otherFinancialExpense)||b.otherFinancialExpense<0) throw Error('Invalid non-interest financial expense');
}
export function planningSeries(b,a,c) {
  const source=b.planningInputs;
  if(source && (source.municipality!=='0583'||source.baseYear!==b.baseYear||!Array.isArray(source.rows))) throw Error('Planning inputs must match Motala and the baseline year');
  let previous=[...b.population],taxFactor=1;
  const rows=[];
  for(let t=1;t<=a.years;t++) {
    const row=source?.rows.find(r=>r.year===b.baseYear+t);
    if(source && (!row||source.rows.filter(r=>r.year===row.year).length!==1)) throw Error(`Planning inputs missing or duplicate year ${b.baseYear+t}`);
    if(row && (!Array.isArray(row.cohorts)||row.cohorts.length!==5||row.cohorts.some(x=>!Number.isFinite(x)||x<=0)||!['taxBaseGrowth','labourCostGrowth','otherPriceGrowth'].every(k=>Number.isFinite(row[k])&&row[k]>-100&&row[k]<100))) throw Error('Invalid planning input row');
    const natural=naturalStep(previous,b.births*previous[3]/b.population[3],c.deathRates);
    const migration=row?row.cohorts.map((x,i)=>x-natural[i]):c.migration;
    const wageGrowth=row?row.labourCostGrowth+a.wageGrowth-b.assumptions.wageGrowth:a.wageGrowth;
    const priceGrowth=row?row.otherPriceGrowth+a.priceGrowth-b.assumptions.priceGrowth:a.priceGrowth;
    const taxGrowth=row?row.taxBaseGrowth+a.taxGrowth-b.assumptions.taxGrowth:a.taxGrowth;
    if([wageGrowth,priceGrowth,taxGrowth].some(x=>x<=-100||x>100)) throw Error('Adjusted annual planning rate outside supported range');
    taxFactor*=1+taxGrowth/100;
    rows.push({year:b.baseYear+t,migration:[...migration],wageGrowth,priceGrowth,taxGrowth,referenceTax:b.tax*taxFactor});
    if(row) previous=row.cohorts;
  }
  return rows;
}
export function validateRevenuePath(path,baseYear) {
  if(path?.municipality!=='0583'||!/^\d{4}-\d{2}-\d{2}$/.test(path?.vintage??'')||!Array.isArray(path.rows)||!path.rows.length) throw Error('Expected municipality 0583, vintage YYYY-MM-DD and nonempty rows');
  const years=new Set();
  for(const r of path.rows) {
    if(!Number.isInteger(r.year)||r.year<=baseYear||years.has(r.year)||![r.tax,r.grants,r.population].every(x=>Number.isFinite(x)&&x>0)) throw Error('Invalid, duplicate or nonpositive revenue row');
    years.add(r.year);
  }
  return path;
}
export function prepareScenario(b,history,overrides={},revenuePath=null) {
  const a={...b.assumptions,...overrides}; validate(b,a);
  if(history.length<2||history.at(-1).year!==b.baseYear||history.some((r,i)=>r.year>b.baseYear||(i>0&&r.year!==history[i-1].year+1))) throw Error('Calibration history must be consecutive and end at the baseline year; future observations are not allowed');
  if(revenuePath) { validateRevenuePath(revenuePath,b.baseYear); for(let t=1;t<=a.years;t++) if(!revenuePath.rows.some(r=>r.year===b.baseYear+t)) throw Error(`Imported revenue path missing ${b.baseYear+t}; supply all forecast years`); }
  const c=calibrate(history),inputs=planningSeries(b,a,c),o=b.operatingAccounts;
  const revenuePopulation0=reconcileHistory(history).find(r=>r.year===b.baseYear-1).population;
  const national=year=>{const v=b.nationalPopulation?.population?.[year];if(!Number.isFinite(v))throw Error(`Rikets folkmängd saknas för ${year}`);return v;};
  const fields={p0:b.population,deathRates:c.deathRates,residualMigration:c.migration,migrationWeights:a.migrationWeights,educationWeights:a.educationWeights,sectorCosts:a.sectorCosts,tax0:b.tax,grants0:b.grants,debt0:b.debt,cash0:b.cash,assets0:b.assets,depreciation0:b.depreciation,financialIncome:b.financialIncome,otherFinancialExpense:b.otherFinancialExpense,payroll0:o.payrollExcludingPensions,pension0:o.pensionExpense,otherOperatingExpense0:o.otherOperatingExpense,operatingRevenue0:o.operatingRevenue,netCostRoundingAdjustment:o.netCostRoundingAdjustment,births0:b.births,migrationDelta:a.migrationDelta,taxRate:a.taxRate,baseTaxRate:b.taxRate,investment:a.investment,adjustment:a.adjustment,equalisationOffset:a.equalisationOffset,fixedShare:a.fixedShare,populationRevenueElasticity:a.populationRevenueElasticity};
  for(const k of ['taxGrowth','grantGrowth','wageGrowth','priceGrowth','pensionGrowth','operatingRevenueGrowth','interestRate','birthChange']) fields[k]=a[k]/100;
  fields.productivityGrowth=a.productivity/100;
  fields.revenuePopulation0=revenuePopulation0;
  // Reference growth is national; Motala's share follows its population relative to Sweden's (end of the previous year).
  fields.nationalPopulation0=national(b.baseYear-1);
  fields.nationalPopulationPath=inputs.map(r=>national(r.year-1));
  fields.residualMigrationPath=inputs.map(r=>r.migration);
  fields.wageGrowthPath=inputs.map(r=>r.wageGrowth/100);
  fields.priceGrowthPath=inputs.map(r=>r.priceGrowth/100);
  const refs=inputs.map(r=>revenuePath?.rows.find(p=>p.year===r.year));
  fields.importedRevenue=!!revenuePath;
  fields.referenceTax=inputs.map((r,i)=>refs[i]?.tax??r.referenceTax);
  fields.referenceGrants=inputs.map((r,i)=>refs[i]?.grants??b.grants*(1+a.grantGrowth/100)**(i+1));
  fields.referencePopulation=inputs.map((r,i)=>refs[i]?.population??sum(b.population));
  fields.pensionExpensePath=inputs.map((r,i)=>a.pensionExpensePath?.[i]??o.pensionExpense*(1+a.pensionGrowth/100)**(i+1));
  fields.pensionCashPaymentsPath=inputs.map((r,i)=>a.pensionCashPaymentsPath?.[i]??fields.pensionExpensePath[i]);
  fields.investmentPath=inputs.map(()=>a.investment);
  fields.interestRatePath=inputs.map(()=>a.interestRate/100);
  fields.migrationDeltaPath=inputs.map(()=>a.migrationDelta);
  fields.birthChangePath=inputs.map(()=>a.birthChange/100);
  fields.serviceAdjustment=Array(3).fill(a.adjustment);
  fields.serviceFixedShare=Array(3).fill(a.fixedShare);
  return {assumptions:a,calibration:c,inputs,fields,
    planningStatus:b.planningInputs?'Sourced population and annual SKR assumptions':'Illustrative assumptions',
    revenueStatus:revenuePath?'Imported revenue path':'Illustrative revenue path'};
}
export function baselineRow(b) {
  const o=b.operatingAccounts;
  return {year:b.baseYear,population:sum(b.population),cohorts:[...b.population],cost:b.cashCost,depreciation:b.depreciation,tax:b.tax,grants:b.grants,result:b.publishedResult,debt:b.debt,cash:b.cash,assets:b.assets,investment:b.investment,interest:b.interestExpense,otherFinancialExpense:b.otherFinancialExpense,payroll:o.payrollExcludingPensions,pensionExpense:o.pensionExpense,otherOperatingExpense:o.otherOperatingExpense,operatingRevenue:o.operatingRevenue,pensionCashPayments:null,operatingCash:null,educationIndex:1,careIndex:1,benchmarkRevenue:null,officialRevenue:null};
}
