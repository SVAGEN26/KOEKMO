import {DEFAULT_MUNICIPALITY} from './municipalities.js';
// Validation, historical calibration and source-data preparation. No forecast simulation.
export const sum = a => a.reduce((s,x)=>s+x,0);
const migrationProfiles={families:[0.16,0.20,0.04,0.60,0],working:[0,0,0,1,0],older:[0,0,0,0,1]};
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
// The population calibration of the continuous model (death rates, the residual flow and the flows that follow a
// projection) is computed in Modelica, in the wrapper MotalaBrowserContinuous: the page sends the history and the
// projection (historyCohorts, projectedCohorts ...), and the model computes the rest when it starts.
// Genomsnittlig räntebindning vid basårets slut (data/rate-fixing.json, ur årsredovisningarna); annars tabellens antagande.
// The municipality's liquidity rule as attached to the baseline (b.liquidity), else the standard: 30 days, no credit line.
export const STANDARD_LIQUIDITY={reserveDays:30,creditLine:0,note:'Standard: 30 dagars utbetalningar, ingen känd kredit.'};
export function liquidityRule(b) {return b?.liquidity??STANDARD_LIQUIDITY;}
export function liquidityFor(table,code) {return table?.municipalities?.[code]??table?.default??STANDARD_LIQUIDITY;}
export function rateFixing(table,code,year) {
  return table?.municipalities?.[code]?.[year]??table?.default??{years:3,note:'Antagande: 3 år'};
}
export function validate(b,a) {
  const keys=['years','taxGrowth','grantGrowth','wageGrowth','priceGrowth','pensionGrowth','operatingRevenueGrowth','productivity','migrationDelta','birthChange','interestRate','taxRate','investment','adjustment','equalisationOffset','fixedShare','populationRevenueElasticity'];
  for(const k of keys) if(!Number.isFinite(a[k])) throw Error(`Invalid assumption: ${k}`);
  if(a.years<1||a.years>100||!Number.isInteger(a.years)) throw Error('Forecast horizon must be 1–100 years');
  for(const k of ['taxGrowth','grantGrowth','wageGrowth','priceGrowth','pensionGrowth','operatingRevenueGrowth','productivity']) if(a[k]<=-100||a[k]>100) throw Error(`Rate outside supported range: ${k}`);
  for(const [k,low,high] of [['costDrift',-5,5],['grantIncrease',-30,30]]) if(a[k]!=null&&(!Number.isFinite(a[k])||a[k]<low||a[k]>high)) throw Error(`Antagandet ${k} ska ligga mellan ${low} och ${high}.`);
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
  if(a.revenueMode!=null&&![0,1,2].includes(a.revenueMode)) throw Error('Ogiltig intäktsmodell.');
  if(a.migrationProfile!=null&&a.migrationProfile!=='default'&&!Object.hasOwn(migrationProfiles,a.migrationProfile)) throw Error('Ogiltig flyttprofil.');
  if(a.ageTax&&(!Array.isArray(b.ageIncome?.weights)||b.ageIncome.weights.length!==5||!b.ageIncome.weights.every(x=>Number.isFinite(x)&&x>=0)||
    sum(b.ageIncome.weights)<=0||!Number.isFinite(b.ageIncome?.countyRate)||b.ageIncome.countyRate<=0)) throw Error('Åldersprofil för beskattningsbar inkomst saknas.');
  if(a.projectChoice!=null&&!['none','planned','delay'].includes(a.projectChoice)) throw Error('Ogiltigt projektval.');
  if(a.inflationShock!=null&&(!Number.isFinite(a.inflationShock)||a.inflationShock<-5||a.inflationShock>20)) throw Error('Extra inflation ska vara mellan -5 och 20 procentenheter.');
  for(const [k,low,high] of [['inflationPersistence',0,1],['inflationWagePassThrough',0,2],['inflationPensionPassThrough',0,30],['inflationRateResponse',0,3],['inflationGrantCompensation',0,100]])
    if(a[k]!=null&&(!Number.isFinite(a[k])||a[k]<low||a[k]>high)) throw Error(`${k} ska ligga mellan ${low} och ${high}.`);
  if(a.rateShock!=null&&(!Number.isFinite(a.rateShock)||a.rateShock<-5||a.rateShock>15)) throw Error('Räntehöjningen ska vara mellan -5 och 15 procentenheter.');
  rateEpisode(b,a);
  if(a.investmentPlan&&!(b.investmentPlan?.factors?.length&&b.investmentPlan.factors.every(f=>Number.isFinite(f)&&f>=0))) throw Error('Kommunen saknar investeringsplan för basåret.');
  if(a.rateShockMonth!=null&&(!Number.isInteger(a.rateShockMonth)||a.rateShockMonth<1||a.rateShockMonth>12)) throw Error('Räntehöjningens månad ska vara 1–12.');
  if(a.rateFixingYears!=null&&(!Number.isFinite(a.rateFixingYears)||a.rateFixingYears<0||a.rateFixingYears>15)) throw Error('Räntebindningen ska vara 0–15 år.');
  if(a.projectChoice&&a.projectChoice!=='none'&&(!b.project||b.project.openingStock>b.workInProgress)) throw Error('Projektunderlaget matchar inte valt basår.');
  if(a.timeModel!=null&&a.timeModel!=='continuous') throw Error('Modellen räknar bara i kontinuerlig tid.');
  if(a.demographyMode!=null&&!['legacy','observed','cohort','cohort-observed'].includes(a.demographyMode)) throw Error('Ogiltig befolkningsmodell.');
  if(a.employerContributionRate!=null&&a.employerContributionRate!==-1&&(!Number.isFinite(a.employerContributionRate)||a.employerContributionRate<0||a.employerContributionRate>100)) throw Error('Sociala avgifter måste anges i procent av lönen.');
  if(a.constructionYears!=null&&(!Number.isInteger(a.constructionYears)||a.constructionYears<0||a.constructionYears>5)) throw Error('Byggtiden ska vara 0–5 hela år.');
  if(a.constructionShare!=null&&(!Number.isFinite(a.constructionShare)||a.constructionShare<0||a.constructionShare>1)) throw Error('Byggandelen ska vara mellan 0 och 100 procent.');
  if(a.constructionYears>0&&(!Number.isFinite(b.workInProgress)||b.workInProgress<0)) throw Error('Basårets saldo för pågående arbeten behövs för att räkna med byggtid.');
  if(a.liquidityPolicy!=null&&typeof a.liquidityPolicy!=='boolean') throw Error('Ogiltig kassapolicy.');
  if(a.workingCapitalEnabled!=null&&typeof a.workingCapitalEnabled!=='boolean') throw Error('Ogiltigt val för rörelsekapital.');
  if(a.workingCapitalEnabled&&(![b.workingCapital?.receivables,b.workingCapital?.payables].every(x=>Number.isFinite(x)&&x>=0))) throw Error('Basårets kundfordringar och leverantörsskulder behövs.');
  for(const key of ['collectionDays','paymentDays']) {
    if(a[key]!=null&&(!Number.isFinite(a[key])||a[key]<0||a[key]>365)) throw Error('Betalningstiden ska vara 0–365 dagar.');
  }
  if(a.firstYearGrantAdvance!=null&&(!Number.isFinite(a.firstYearGrantAdvance)||a.firstYearGrantAdvance<0)) throw Error('Bidragsförskottet ska vara minst noll.');
  if(a.reserveDays!=null&&(!Number.isFinite(a.reserveDays)||a.reserveDays<0||a.reserveDays>365)) throw Error('Likviditetsreserven ska vara 0–365 dagar.');
  if(a.creditLine!=null&&(!Number.isFinite(a.creditLine)||a.creditLine<0)) throw Error('Krediten ska vara ett belopp på minst noll.');
  if(a.reserveAdjustmentTime!=null&&(!Number.isFinite(a.reserveAdjustmentTime)||a.reserveAdjustmentTime<0||a.reserveAdjustmentTime>20)) throw Error('Tiden till reserven ska vara 0–20 år.');
  for(const key of ['deferInvestmentShare','prefinanceShare']) {
    if(a[key]!=null&&(!Number.isFinite(a[key])||a[key]<0||a[key]>1)) throw Error('Andelarna för senare betalning och förfinansiering ska vara 0–100 procent.');
  }
}
export function planningSeries(b,a) {
  const source=b.planningInputs;
  if(source && (source.municipality!==(b.municipality??DEFAULT_MUNICIPALITY)||source.baseYear!==b.baseYear||!Array.isArray(source.rows))) throw Error('Planning inputs must match the selected municipality and base year');
  let previous=[...b.population],taxFactor=1;
  const rows=[];
  for(let t=1;t<=a.years;t++) {
    const row=source?.rows.find(r=>r.year===b.baseYear+t);
    if(source && (!row||source.rows.filter(r=>r.year===row.year).length!==1)) throw Error(`Planning inputs missing or duplicate year ${b.baseYear+t}`);
    const cohorts=row?.cohorts;
    const validCohorts=Array.isArray(cohorts)&&cohorts.length===5&&cohorts.every(x=>Number.isFinite(x)&&x>0);
    if(row && (!(validCohorts||(cohorts==null&&(source.demography==='calibrated'||row.projected)))||!['taxBaseGrowth','labourCostGrowth','otherPriceGrowth'].every(k=>Number.isFinite(row[k])&&row[k]>-100&&row[k]<100))) throw Error('Invalid planning input row');
    const wageGrowth=row&&!a.splitPayroll?row.labourCostGrowth+a.wageGrowth-b.assumptions.wageGrowth:a.wageGrowth;
    const priceGrowth=row?row.otherPriceGrowth+a.priceGrowth-b.assumptions.priceGrowth:a.priceGrowth;
    const taxGrowth=row?row.taxBaseGrowth+a.taxGrowth-b.assumptions.taxGrowth:a.taxGrowth;
    if([wageGrowth,priceGrowth,taxGrowth].some(x=>x<=-100||x>100)) throw Error('Adjusted annual planning rate outside supported range');
    taxFactor*=1+taxGrowth/100;
    rows.push({year:b.baseYear+t,cohorts:validCohorts?[...cohorts]:null,wageGrowth,priceGrowth,taxGrowth,referenceTax:(b.tax-(b.priorYearSettlement??0))*taxFactor});
  }
  return rows;
}

// Extend the bundled series for scenarios beyond their publication horizon.
// Keep imported custom paths subject to the ordinary coverage check.
export function extendPlanning(source,endYear) {
  const last=source.rows.at(-1);
  if(endYear<=last.year) return source;
  const years=Array.from({length:endYear-last.year},(_,i)=>last.year+i+1);
  const rows=[...source.rows,...years.map(year=>({
    year,labourCostGrowth:last.labourCostGrowth,otherPriceGrowth:last.otherPriceGrowth,
    taxBaseGrowth:last.taxBaseGrowth,projected:true
  }))];
  const revenuePath=source.revenuePath;
  if(!revenuePath) return {...source,rows};
  const [previous,final]=revenuePath.rows.slice(-2);
  const referenceRows=years.map(year=>{
    const row={year,projected:true};
    for(const k of ['tax','grants','population']) row[k]=final[k]*(final[k]/previous[k])**(year-final.year);
    if(Number.isFinite(final.regulation)) row.regulation=final.regulation*row.population/final.population;
    const components=revenueComponents(revenuePath,final);
    if(components) row.components={
      recurringTax:components.recurringTax*row.tax/final.tax,
      incomeEqualisation:components.incomeEqualisation*row.population/final.population,
      regulation:components.regulation*row.population/final.population
    };
    return row;
  });
  return {...source,rows,revenuePath:{...revenuePath,rows:[...revenuePath.rows,...referenceRows]}};
}
function revenueComponents(path,row) {
  if(!row) return null;
  if(row.components) return row.components;
  const cells=path.provenance?.recalculation?.components?.find(x=>x.year===row.year)?.tkrByOutputRow;
  return cells?{recurringTax:cells[12]/1000,incomeEqualisation:cells[14]/1000,regulation:cells[18]/1000}:null;
}
function toGroups(values) {
  const totals=values[0].map((x,i)=>x+values[1][i]);
  return [[0,7],[7,16],[16,19],[19,65],[65,101]].map(([start,end])=>sum(totals.slice(start,end)));
}
// SKR's revenue path assumes the state's grant frame stays fixed in kronor after the years the
// budget bill has decided, so the regulation grant shrinks each year. Over 2005-2026 the regulation
// grant per inhabitant had no such trend (SCB TAB1981), and SKR's figure for the second and third
// year was too low in every December circular 2021-2023. This keeps the regulation grant per
// inhabitant from `heldFrom` and adds the difference to the grants. The original stays in skrGrants.
export function holdRegulation(path,heldFrom) {
  const from=path?.rows.find(r=>r.year===heldFrom);
  if(!from||!Number.isFinite(from.regulation)) return path;
  const perInhabitant=from.regulation/from.population;
  return {...path,regulationHeldFrom:heldFrom,rows:path.rows.map(r=>{
    if(r.year<=heldFrom||!Number.isFinite(r.regulation)) return r;
    const adjustment=perInhabitant*r.population-r.regulation;
    return {...r,grants:r.grants+adjustment,skrGrants:r.grants,regulationAdjustment:adjustment};
  })};
}
export function validateRevenuePath(path,baseYear,municipality=DEFAULT_MUNICIPALITY) {
  if(path?.municipality!==municipality||!/^\d{4}-\d{2}-\d{2}$/.test(path?.vintage??'')||!Array.isArray(path.rows)||!path.rows.length) throw Error(`SKR-underlaget måste gälla kommun ${municipality}, ha versionsdatum YYYY-MM-DD och innehålla årsbelopp.`);
  const years=new Set();
  for(const r of path.rows) {
    if(!Number.isInteger(r.year)||r.year<=baseYear||years.has(r.year)||![r.tax,r.grants,r.population].every(x=>Number.isFinite(x)&&x>0)) throw Error('Invalid, duplicate or nonpositive revenue row');
    years.add(r.year);
  }
  return path;
}
export function prepareScenario(b,history,overrides={},revenuePath=null) {
  const a={...b.assumptions,...overrides}; validate(b,a);
  if(history.length<3) throw Error('The model calibrates on three completed years up to the base year');
  if(history.at(-1).year!==b.baseYear||history.some((r,i)=>r.year>b.baseYear||(i>0&&r.year!==history[i-1].year+1))) throw Error('Calibration history must be consecutive and end at the baseline year; future observations are not allowed');
  if(revenuePath) { validateRevenuePath(revenuePath,b.baseYear,b.municipality); for(let t=1;t<=a.years;t++) if(!revenuePath.rows.some(r=>r.year===b.baseYear+t)) throw Error(`Imported revenue path missing ${b.baseYear+t}; supply all forecast years`); }
  const o=b.operatingAccounts;
  const observed=['observed','cohort-observed'].includes(a.demographyMode),cohort=a.demographyMode?.startsWith('cohort')??false;
  const evidence=b.experiments;
  if((observed||a.splitPayroll)&&!evidence) throw Error('SCB-underlag saknas för valt basår.');
  const inputs=planningSeries(b,a);
  const revenuePopulation0=reconcileHistory(history).find(r=>r.year===b.baseYear-1).population;
  const national=year=>{
    const population=b.nationalPopulation?.population;
    const last=b.nationalPopulation?.extrapolateAfter;
    // After the last year SCB projects (2070), or after extrapolateAfter, Sweden's population keeps its last growth.
    const end=last??Math.max(...Object.keys(population??{}).map(Number));
    const v=year>end?population[end]*(population[end]/population[end-1])**(year-end):population?.[year];
    if(!Number.isFinite(v))throw Error(`Rikets folkmängd saknas för ${year}`);
    return v;
  };
  const fields={p0:b.population,migrationWeights:a.migrationWeights,educationWeights:a.educationWeights,sectorCosts:a.sectorCosts,tax0:b.tax,grants0:b.grants,debt0:b.debt,cash0:b.cash,assets0:b.assets,depreciation0:b.depreciation,financialIncome:b.financialIncome,otherFinancialExpense:b.otherFinancialExpense,payroll0:o.payrollExcludingPensions,pension0:o.pensionExpense,otherOperatingExpense0:o.otherOperatingExpense,operatingRevenue0:o.operatingRevenue,netCostRoundingAdjustment:o.netCostRoundingAdjustment,births0:b.births,migrationDelta:a.migrationDelta,taxRate:a.taxRate,baseTaxRate:b.taxRate,investment:a.investment,adjustment:a.adjustment,equalisationOffset:a.equalisationOffset,fixedShare:a.fixedShare,populationRevenueElasticity:a.populationRevenueElasticity};
  // The history the model calibrates on: the three years up to the base year (Data.calibratedMigrationRates).
  const recent=history.slice(-3);
  fields.historyCohorts=recent.map(r=>r.population);
  fields.historyTotals=recent.map(r=>r.reportedTotal??sum(r.population));
  fields.historyBirths=recent.slice(1).map(r=>r.births);
  fields.historyDeaths=recent.at(-1).deaths;
  // SCB's observed net migration instead of the calibrated flow; otherwise SCB's projection where it is loaded.
  fields.useObservedMigration=a.demographyMode==='observed';
  if(fields.useObservedMigration) fields.observedMigration=toGroups(evidence.netMigration);
  else {
    fields.projectedCohorts=inputs.map(r=>r.cohorts??[0,0,0,0,0]);
    fields.followProjection=inputs.map(r=>!!r.cohorts);
  }
  if(observed) fields.migrationWeights=toGroups(evidence.arrivalWeights);
  const profile=Object.hasOwn(migrationProfiles,a.migrationProfile)?migrationProfiles[a.migrationProfile]:null;
  if(profile) fields.migrationWeights=profile;
  if(a.splitPayroll) {
    fields.employerContributions0=o.payrollExcludingPensions*evidence.employerContributions/(evidence.wages+evidence.employerContributions);
    const rate=a.employerContributionRate??-1;
    fields.employerContributionRatePath=inputs.map(()=>rate<0?-1:rate/100);
  }
  for(const k of ['taxGrowth','grantGrowth','wageGrowth','priceGrowth','pensionGrowth','operatingRevenueGrowth','interestRate','birthChange']) fields[k]=a[k]/100;
  fields.productivityGrowth=a.productivity/100;
  fields.costDrift=(a.costDrift??0)/100;
  fields.grantIncrease=a.grantIncrease??0; // mdkr i riket per år och år; modellen fördelar per invånare
  fields.revenuePopulation0=revenuePopulation0;
  // Reference growth is national; Motala's share follows its population relative to Sweden's (end of the previous year).
  fields.nationalPopulation0=national(b.baseYear-1);
  fields.nationalPopulationPath=inputs.map(r=>national(r.year-1));
  fields.wageGrowthPath=inputs.map(r=>r.wageGrowth/100);
  fields.priceGrowthPath=inputs.map(r=>r.priceGrowth/100);
  const refs=inputs.map(r=>revenuePath?.rows.find(p=>p.year===r.year));
  fields.importedRevenue=!!revenuePath;
  if(revenuePath&&a.revenueMode) fields.importedRevenueMode=a.revenueMode;
  fields.referenceTax=inputs.map((r,i)=>refs[i]?.tax??r.referenceTax);
  fields.referenceGrants=inputs.map((r,i)=>(a.revenueMode===1?refs[i]?.skrGrants:undefined)??refs[i]?.grants??b.grants*(1+a.grantGrowth/100)**(i+1));
  fields.referencePopulation=inputs.map((r,i)=>refs[i]?.population??sum(b.population));
  if(revenuePath&&a.revenueMode===2) {
    if(!Number.isFinite(evidence?.novemberPopulation)) throw Error('SCB:s novemberbefolkning saknas för valt basår.');
    fields.novemberPopulation0=evidence.novemberPopulation;
    if(a.ageTax) {
      fields.ageIncomeWeights=b.ageIncome.weights;
      fields.equalisationCountyRate=b.ageIncome.countyRate;
    }
    fields.importedComponents=refs.map(row=>{
      const details=revenueComponents(revenuePath,row);
      if(!details) throw Error('SKR-underlaget behöver delposter för vald intäktsmodell.');
      return [details.recurringTax,details.incomeEqualisation,details.regulation+(row.regulationAdjustment??0)];
    });
  }
  // The pension cost follows the payroll in the model; pensionGrowth is its growth beyond the payroll. A given path in
  // mnkr (pensionExpensePath) replaces that.
  fields.pensionFollowsPayroll=!a.pensionExpensePath;
  fields.pensionExpensePath=inputs.map((r,i)=>a.pensionExpensePath?.[i]??o.pensionExpense*(1+a.pensionGrowth/100)**(i+1));
  fields.pensionCashPaymentsPath=inputs.map((r,i)=>a.pensionCashPaymentsPath?.[i]??fields.pensionExpensePath[i]);
  fields.investmentPath=inputs.map((_,i)=>a.investment*investmentFactor(b,a,i));
  if(a.workingCapitalEnabled) {
    const wc=b.workingCapital;
    const days=workingCapitalDays(b);
    fields.workingCapitalEnabled=true;
    fields.receivables0=wc.receivables;
    fields.payables0=wc.payables;
    fields.grantAdvances0=wc.grantAdvances??0;
    fields.collectionDays=a.collectionDays??days.collectionDays;
    fields.paymentDays=a.paymentDays??days.paymentDays;
    fields.firstYearGrantAdvance=a.firstYearGrantAdvance??0;
  }
  // Liquidity reserve (data/liquidity.json, b.liquidity): on unless the scenario turns it off; the municipality's own rule,
  // or 30 days of payments and no credit line.
  const liquidity=liquidityRule(b);
  fields.liquidityPolicy=a.liquidityPolicy??true;
  fields.reserveDays=a.reserveDays??liquidity.reserveDays;
  fields.creditLine=a.creditLine??liquidity.creditLine;
  // From the accounts' own days toward the reserve, with this time constant in years (0: the reserve from the start).
  fields.reserveAdjustmentTime=a.reserveAdjustmentTime??3;
  if(fields.liquidityPolicy) {
    fields.deferInvestmentShare=a.deferInvestmentShare??0;
    fields.prefinanceShare=a.prefinanceShare??0;
  }
  if(a.constructionYears>0) {
    fields.constructionYears=a.constructionYears;
    fields.constructionShare=a.constructionShare??0.5;
    fields.workInProgress0=b.workInProgress;
  }
  if(a.projectChoice&&a.projectChoice!=='none') {
    const p=b.project;
    fields.projectOpeningStock=p.openingStock;
    fields.workInProgress0=b.workInProgress-p.openingStock;
    fields.projectPayment=p.authorisedBudget-p.openingStock;
    fields.projectOpeningStep=p.openingYear-b.baseYear+(a.projectChoice==='delay'?1:0);
    fields.projectPlaces=p.places;
  }
  // A rate stress path (data/rate-stress.json): how the market rate once moved, added to the scenario's rate,
  // never below 0. After the episode its last change stays.
  const episode=rateEpisode(b,a);
  fields.interestRatePath=inputs.map((_,i)=>Math.max(0,a.interestRate+(episode?episode.changes[Math.min(i,episode.changes.length-1)]:0))/100);
  // Med räntebindning är räntan ovan marknadsräntan för nya och omsatta lån; snitträntan startar där och följer efter.
  // Extra inflation år för år; modellen lägger den på priserna samma år och på löner, skatteunderlag, pensioner och ränta
  // åren efter (Components.Scenario).
  fields.inflationShockPath=inputs.map((_,i)=>(a.inflationShock??0)/100*(a.inflationPersistence??0.5)**i);
  fields.inflationWagePassThrough=a.inflationWagePassThrough??0.4;
  fields.inflationPensionPassThrough=a.inflationPensionPassThrough??8;
  fields.inflationRateResponse=a.inflationRateResponse??0.5;
  fields.inflationGrantCompensation=(a.inflationGrantCompensation??0)/100;
  fields.rateFixingYears=a.rateFixingYears??0;
  fields.rateShock=(a.rateShock??0)/100;
  fields.rateShockTime=b.baseYear+1+((a.rateShockMonth??1)-1)/12;
  fields.migrationDeltaPath=inputs.map(()=>a.migrationDelta);
  fields.birthChangePath=inputs.map(()=>a.birthChange/100);
  fields.serviceAdjustment=Array(3).fill(a.adjustment);
  fields.serviceFixedShare=Array(3).fill(a.fixedShare);
  const ageMigration=a.demographyMode==='cohort-observed'?{
    'demography.residualMigration':evidence.netMigration,
    'demography.observedDeltaShape':evidence.arrivalWeights,
    'demography.useObservedDeltaShape':!profile
  }:null;
  return {assumptions:{...a,timeModel:'continuous'},calibration:'Kommunekonomi.Data i Modelica (MotalaBrowserContinuous)',inputs,fields,cohort,ageMigration,
    planningStatus:b.planningInputs?'Sourced population and annual SKR assumptions':'Illustrative assumptions',
    revenueStatus:revenuePath?'Imported revenue path':'Illustrative revenue path'};
}
export function workingCapitalDays(b) {
  const wc=b.workingCapital,o=b.operatingAccounts;
  return {
    collectionDays:o.operatingRevenue>0?Math.min(365,365*(wc?.receivables??0)/o.operatingRevenue):0,
    paymentDays:o.otherOperatingExpense>0?Math.min(365,365*(wc?.payables??0)/o.otherOperatingExpense):0
  };
}
export function baselineRow(b) {
  const o=b.operatingAccounts;
  return {year:b.baseYear,population:sum(b.population),cohorts:[...b.population],births:b.births??null,deaths:b.deaths??null,cost:b.cashCost,depreciation:b.depreciation,tax:b.tax,grants:b.grants,result:b.publishedResult,debt:b.debt,cash:b.cash,assets:b.assets,investment:b.investment,interest:b.interestExpense,otherFinancialExpense:b.otherFinancialExpense,payroll:o.payrollExcludingPensions,pensionExpense:o.pensionExpense,otherOperatingExpense:o.otherOperatingExpense,operatingRevenue:o.operatingRevenue,pensionCashPayments:null,operatingCash:null,educationIndex:1,careIndex:1,benchmarkRevenue:null,officialRevenue:null};
}

// The rate stress path the scenario names (assumption rateEpisode), or null for the scenario's own rate.
export function rateEpisode(b,a) {
  if(a.rateEpisode==null||a.rateEpisode==='none') return null;
  const episode=b.rateEpisodes?.find(e=>e.id===a.rateEpisode);
  if(!episode||!episode.changes?.length||!episode.changes.every(Number.isFinite)) throw Error('Okänd räntebana.');
  return episode;
}

// The municipality's investment plan (data/investment-plans.json): the plan for forecast year i over the budget for
// the base year, so the base year's investment follows the plan with the share of the budget carried out then.
// After the plan's last year the base year's level returns: plans often end with low years because later
// projects are not yet decided. 1 without a plan or when the scenario does not use it.
export function investmentFactor(b,a,i) {
  if(!a.investmentPlan||!b.investmentPlan) return 1;
  const f=b.investmentPlan.factors;
  return i<f.length?f[i]:1;
}
