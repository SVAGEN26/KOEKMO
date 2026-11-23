// Independent legacy reference for regression tests only; not shipped to the dashboard.
import {sum,validate,validateRevenuePath,calibrate,naturalStep,planningSeries,reconcileHistory} from "./scenario-inputs.js";
export {sum,validate,validateRevenuePath,calibrate,naturalStep,planningSeries,reconcileHistory,mortality} from "./scenario-inputs.js";
export function simulate(b,history,overrides={},revenuePath=null) {
  const a={...b.assumptions,...overrides}; validate(b,a);
  if(history.length<2||history.at(-1).year!==b.baseYear||history.some((r,i)=>r.year>b.baseYear||(i>0&&r.year!==history[i-1].year+1))) throw Error('Calibration history must be consecutive and end at the baseline year; future observations are not allowed');
  if(revenuePath) { validateRevenuePath(revenuePath,b.baseYear); for(let t=1;t<=a.years;t++) if(!revenuePath.rows.some(r=>r.year===b.baseYear+t)) throw Error(`Imported revenue path missing ${b.baseYear+t}; supply all forecast years`); }
  const c=calibrate(history), p0=b.population, total0=sum(p0), life=b.assets/b.depreciation;
  // Base-year tax and grants rest on the population a year earlier (folkbokförda 1 november).
  const pTax0=reconcileHistory(history).find(r=>r.year===b.baseYear-1).population, totalTax0=sum(pTax0);
  // Reference growth is national: scale by Motala's population relative to Sweden's.
  const national=year=>b.nationalPopulation.population[year], national0=national(b.baseYear-1);
  const inputs=planningSeries(b,a,c);
  const o=b.operatingAccounts;
  let p=[...p0],capacity=[1,1,1],tax=b.tax,grants=b.grants,wageIndex=1,priceIndex=1,revenueIndex=1,productivity=1,standard=1,debt=b.debt,cash=b.cash,assets=b.assets;
  const rows=[{year:b.baseYear,population:total0,cohorts:p,cost:b.cashCost,depreciation:b.depreciation,tax,grants,result:b.publishedResult,debt,cash,investment:b.investment,interest:b.interestExpense,otherFinancialExpense:b.otherFinancialExpense,payroll:o.payrollExcludingPensions,pensionExpense:o.pensionExpense,otherOperatingExpense:o.otherOperatingExpense,operatingRevenue:o.operatingRevenue,pensionCashPayments:null,operatingCash:null,educationIndex:1,careIndex:1,benchmarkRevenue:null,officialRevenue:null}];
  for(let t=1;t<=a.years;t++) {
    const previousP=p,previousDebt=debt,previousCash=cash,previousAssets=assets;
    const births=b.births*(previousP[3]/p0[3])*(1+a.birthChange/100),deaths=sum(previousP.map((x,i)=>x*c.deathRates[i]));
    const annual=inputs[t-1];
    const migration=annual.migration.map((x,i)=>x+a.migrationDelta*a.migrationWeights[i]);
    p=naturalStep(previousP,births,c.deathRates).map((x,i)=>x+migration[i]);
    if(p.some(x=>x<0)) throw Error('Scenario exhausts a cohort; shorten horizon or change migration');
    const population=sum(p), ratio=population/total0;
    const demand=[sum(a.educationWeights.map((w,i)=>w*p[i]/p0[i])),p[4]/p0[4],ratio];
    capacity=capacity.map((x,i)=>x+a.adjustment*(a.fixedShare+(1-a.fixedShare)*demand[i]-x));
    wageIndex*=1+annual.wageGrowth/100;
    priceIndex*=1+annual.priceGrowth/100;
    revenueIndex*=1+a.operatingRevenueGrowth/100;
    productivity*=1+a.productivity/100;
    standard*=1+(a.costDrift??0)/100;
    const serviceVolume=sum(a.sectorCosts.map((x,i)=>x*capacity[i]))/b.cashCost;
    const payroll=o.payrollExcludingPensions*wageIndex*serviceVolume*standard/productivity;
    const otherOperatingExpense=o.otherOperatingExpense*priceIndex*serviceVolume*standard;
    const operatingRevenue=o.operatingRevenue*revenueIndex*ratio;
    const pensionExpense=a.pensionExpensePath?.[t-1]??o.pensionExpense*Math.pow(1+a.pensionGrowth/100,t);
    const pensionCashPayments=a.pensionCashPaymentsPath?.[t-1]??pensionExpense;
    const cost=payroll+pensionExpense+otherOperatingExpense-operatingRevenue+o.netCostRoundingAdjustment;
    const depreciation=(previousAssets+0.5*a.investment)/life;
    assets=previousAssets+a.investment-depreciation;
    // Population base is lagged one year: last year's population against the one the base-year tax rested on.
    const popFactor=Math.pow((sum(previousP)/totalTax0)/(national(b.baseYear+t-1)/national0),a.populationRevenueElasticity);
    const imported=revenuePath?.rows.find(r=>r.year===b.baseYear+t);
    const referencePop=imported?.population??total0;
    const referenceTax=imported?.tax??annual.referenceTax;
    const increase=(a.grantIncrease??0)*1e3*(t-1)*(imported?referencePop/national(b.baseYear+t-1):totalTax0/national0);
    const referenceGrants=(imported?.grants??b.grants*Math.pow(1+a.grantGrowth/100,t))+increase;
    const localPopFactor=imported?sum(previousP)/referencePop:popFactor;
    const standardTax=referenceTax*localPopFactor;
    // Working-age composition is a local deviation around the population-based reference.
    const composition=(previousP[3]/pTax0[3])/(sum(previousP)/totalTax0);
    // An imported SKR path already reflects the population's composition.
    const deviation=imported?0:standardTax*(composition-1);
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
  return {rows,inputs,planningStatus:b.planningInputs?'Sourced population and annual SKR assumptions':'Illustrative assumptions',assumptions:a,calibration:c,engine:'JavaScript reference',revenueStatus:revenuePath?'Imported revenue path':'Illustrative revenue path'};
}
