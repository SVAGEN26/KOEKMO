// Annual stock/flow reference engine. Modelica Annual has identical equations.
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
export function simulate(b,history,overrides={},revenuePath=null) {
  const a={...b.assumptions,...overrides}; validate(b,a);
  if(history.length<2||history.at(-1).year!==b.baseYear||history.some((r,i)=>r.year>b.baseYear||(i>0&&r.year!==history[i-1].year+1))) throw Error('Calibration history must be consecutive and end at the baseline year; future observations are not allowed');
  if(revenuePath) { validateRevenuePath(revenuePath,b.baseYear); for(let t=1;t<=a.years;t++) if(!revenuePath.rows.some(r=>r.year===b.baseYear+t)) throw Error(`Imported revenue path missing ${b.baseYear+t}; supply all forecast years`); }
  const c=calibrate(history), p0=b.population, total0=sum(p0), life=b.assets/b.depreciation;
  const o=b.operatingAccounts;
  let p=[...p0],capacity=[1,1,1],tax=b.tax,grants=b.grants,wageIndex=1,priceIndex=1,revenueIndex=1,productivity=1,debt=b.debt,cash=b.cash,assets=b.assets;
  const rows=[{year:b.baseYear,population:total0,cohorts:p,cost:b.cashCost,depreciation:b.depreciation,tax,grants,result:b.publishedResult,debt,cash,investment:b.investment,interest:b.interestExpense,otherFinancialExpense:b.otherFinancialExpense,payroll:o.payrollExcludingPensions,pensionExpense:o.pensionExpense,otherOperatingExpense:o.otherOperatingExpense,operatingRevenue:o.operatingRevenue,pensionCashPayments:null,operatingCash:null,educationIndex:1,careIndex:1,benchmarkRevenue:null,officialRevenue:null}];
  for(let t=1;t<=a.years;t++) {
    const previousP=p,previousDebt=debt,previousCash=cash,previousAssets=assets;
    const births=b.births*(previousP[3]/p0[3])*(1+a.birthChange/100),deaths=sum(previousP.map((x,i)=>x*c.deathRates[i]));
    const migration=c.migration.map((x,i)=>x+a.migrationDelta*a.migrationWeights[i]);
    p=naturalStep(previousP,births,c.deathRates).map((x,i)=>x+migration[i]);
    if(p.some(x=>x<0)) throw Error('Scenario exhausts a cohort; shorten horizon or change migration');
    const population=sum(p), ratio=population/total0;
    const demand=[sum(a.educationWeights.map((w,i)=>w*p[i]/p0[i])),p[4]/p0[4],ratio];
    capacity=capacity.map((x,i)=>x+a.adjustment*(a.fixedShare+(1-a.fixedShare)*demand[i]-x));
    wageIndex*=1+a.wageGrowth/100;
    priceIndex*=1+a.priceGrowth/100;
    revenueIndex*=1+a.operatingRevenueGrowth/100;
    productivity*=1+a.productivity/100;
    const serviceVolume=sum(a.sectorCosts.map((x,i)=>x*capacity[i]))/b.cashCost;
    const payroll=o.payrollExcludingPensions*wageIndex*serviceVolume/productivity;
    const otherOperatingExpense=o.otherOperatingExpense*priceIndex*serviceVolume;
    const operatingRevenue=o.operatingRevenue*revenueIndex*ratio;
    const pensionExpense=a.pensionExpensePath?.[t-1]??o.pensionExpense*Math.pow(1+a.pensionGrowth/100,t);
    const pensionCashPayments=a.pensionCashPaymentsPath?.[t-1]??pensionExpense;
    const cost=payroll+pensionExpense+otherOperatingExpense-operatingRevenue+o.netCostRoundingAdjustment;
    const depreciation=(previousAssets+0.5*a.investment)/life;
    assets=previousAssets+a.investment-depreciation;
    // Population base is lagged one year. Exact November reference date is not yet modelled.
    const popFactor=Math.pow(sum(previousP)/total0,a.populationRevenueElasticity);
    const imported=revenuePath?.rows.find(r=>r.year===b.baseYear+t);
    const referencePop=imported?.population??total0;
    const referenceTax=imported?.tax??b.tax*Math.pow(1+a.taxGrowth/100,t);
    const referenceGrants=imported?.grants??b.grants*Math.pow(1+a.grantGrowth/100,t);
    const localPopFactor=imported?sum(previousP)/referencePop:popFactor;
    const standardTax=referenceTax*localPopFactor;
    // Working-age composition is a local deviation around the population-based reference.
    const composition=(previousP[3]/p0[3])/(sum(previousP)/total0);
    const deviation=standardTax*(composition-1);
    tax=(standardTax+deviation)*a.taxRate/b.taxRate;
    grants=referenceGrants*localPopFactor-a.equalisationOffset*deviation;
    const interest=previousDebt*a.interestRate/100;
    const result=tax+grants-cost-depreciation+b.financialIncome-interest-b.otherFinancialExpense;
    const operatingCash=result+depreciation+pensionExpense-pensionCashPayments;
    const financingGap=a.investment-operatingCash;
    const borrowing=Math.max(0,financingGap),repayment=Math.min(previousDebt,Math.max(0,-financingGap));
    debt=previousDebt+borrowing-repayment;
    cash=previousCash+operatingCash-a.investment+borrowing-repayment;
    rows.push({year:b.baseYear+t,population,cohorts:[...p],births,deaths,migration:sum(migration),cost,payroll,pensionExpense,pensionCashPayments,otherOperatingExpense,operatingRevenue,operatingCash,otherFinancialExpense:b.otherFinancialExpense,depreciation,tax,grants,result,debt,cash,assets,investment:a.investment,interest,borrowing,repayment,educationIndex:demand[0],careIndex:demand[1],benchmarkRevenue:referenceTax+referenceGrants,officialRevenue:imported?referenceTax+referenceGrants:null});
  }
  return {rows,assumptions:a,calibration:c,engine:'JavaScript reference',revenueStatus:revenuePath?'Imported revenue path':'Illustrative revenue path'};
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
