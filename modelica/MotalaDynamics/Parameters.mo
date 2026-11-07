within MotalaDynamics;
partial model Parameters "Observed totals and explicitly illustrative scenario parameters"
  parameter Integer nServices(min=1)=3 "Education, elderly care, other; override all service arrays together";
  parameter Real p0[5]={2894,4629,1575,23019,11022}*(43131/43139) "Reconciled 2025 persons";
  parameter Real births0=334 "Observed annual births";
  parameter Real deathRates[5]={0.0004,0.0001,0.0002,0.0018,0.03853357878008014}
    "Per year; first four assumed, last reconciles baseline total deaths to 468";
  parameter Real ageRates[5]={1/7,1/9,1/3,1/46,0} "Per year; mixed-cohort approximation";
  parameter Real migration0[5]=-239*{0.15,0.12,0.03,0.65,0.05}
    "Observed total net migration, assumed age allocation; persons/year";
  parameter Boolean demographyEnabled=true "False freezes population for controlled experiments";
  parameter Real tax0=2330, grants0=987, payroll0=2288, pension0=190;
  parameter Real otherExpense0=1297, operatingRevenue0=751;
  parameter Real costRounding=-1 "mnkr/year, reconciles rounded gross costs to 3023 net";
  parameter Real assets0=2997, depreciation0=180, debt0=1040, cash0=81;
  parameter Real financialIncome=15, otherFinancialExpense=4, investment0=413;
  parameter Real taxRate0=0.217 "Fraction, not percentage points";
  parameter Real interestRate0=21/1040 "Closing-debt proxy, not measured portfolio yield";
  parameter Real taxReceivable0=0
    "Opening net tax receivable, mnkr; negative is payable. Zero is an assumption without a local reconciliation";
  parameter Real extraCostPath[:]={0}
    "Additional nominal operating expense by simulation year, mnkr; first entry is year 1, zero after the path ends";
  parameter Real extraCostPaymentPath[size(extraCostPath,1)]=extraCostPath
    "Cash payments for the same additional costs; defaults to expense, may differ in timing";

  parameter Real sectorShares[nServices]={1250,600,1173}/3023
    "Legacy fallback allocation, NOT audited gross sector accounts";
  parameter Real payrollShares[nServices]=sectorShares "Separate payroll allocation; replace with observed sector accounts";
  parameter Real otherExpenseShares[nServices]=sectorShares "Separate allocation of other operating expense";
  parameter Real operatingRevenueShares[nServices]=sectorShares "Separate fees/grants/sales allocation";
  parameter Real assetShares[nServices]=sectorShares "Separate allocation of opening book assets";
  parameter Real investmentShares[nServices]=sectorShares "Separate allocation of the investment spending path";
  parameter Real serviceWeights[nServices,5]=[1,1,1,0,0;0,0,0,0,1;1,1,1,1,1]
    "Demographic service equivalents/person; replace with local use/intensity data";
  parameter Real demand0[nServices]={sum(serviceWeights[i,j]*p0[j] for j in 1:5) for i in 1:nServices};
  parameter Real compensationPerFTE[nServices]=fill(0.65,nServices)
    "Illustrative mnkr/FTE/year excluding pensions; includes other payroll charges";
  parameter Real staff0[nServices]=payroll0*payrollShares./compensationPerFTE "Derived, NOT observed FTE";
  parameter Real staffPerUnit[nServices]=staff0./demand0 "FTE per annual service equivalent";
  parameter Real minimumStaff[nServices]=zeros(nServices);
  parameter Real hiringYears[nServices]=fill(1,nServices);
  parameter Real reductionYears[nServices]=fill(3,nServices);
  parameter Boolean limitStaffChanges=false "Enable explicit limits on net staffing changes";
  parameter Real maxStaffIncrease[nServices]=0.10*staff0 "FTE/year; illustrative when limits enabled, not gross recruitment";
  parameter Real maxStaffDecrease[nServices]=0.10*staff0 "FTE/year; illustrative when limits enabled";
  parameter Boolean limitExternalService=false "Enable supplier capacity limits";
  parameter Real externalCapacity0[nServices]=0.05*demand0 "Annual service equivalents; illustrative when enabled";
  parameter Real fixedCostShare[nServices]=fill(0.15,nServices);
  parameter Real facilityCostShare[nServices]=fill(0.25,nServices);
  parameter Real staffReductionCost[nServices]=zeros(nServices)
    "One-off mnkr per net FTE removed, at baseline wage level; zero assumes no transition cost";
  parameter Real capacityClosureCost[nServices]=zeros(nServices)
    "One-off mnkr per capacity unit closed, at baseline price level; excludes book disposal";
  parameter Real purchaseUnitCost[nServices]=(payroll0*payrollShares+otherExpense0*otherExpenseShares)./demand0
    "Illustrative mnkr per externally purchased equivalent";

  parameter Real capacity0[nServices]=demand0 "Assumed initial capacity equals baseline demand";
  parameter Real assetAllocation[nServices]=assets0*assetShares;
  parameter Real workInProgress0=99 "Observed municipal WIP at 2025 year end, annual report pp 48 and 53, mnkr";
  parameter Real constructionMoney0[nServices]=workInProgress0*assetShares "Observed total, assumed sector allocation";
  parameter Real constructionUnits0[nServices]=constructionMoney0./capacityUnitCost
    "Opening physical WIP inferred at scenario unit costs, NOT observed project capacity";
  parameter Real capacityUnitCost[nServices]=2*assetAllocation./capacity0
    "Replacement-cost scenario: twice opening book value per equivalent; NOT a valuation";
  parameter Real physicalLifeYears[nServices]=fill(40,nServices);
  parameter Real accountingLifeYears[nServices]=fill(assets0/depreciation0,nServices)
    "Blended exponential book-value proxy; not straight-line component accounting";
  parameter Real constructionYears[nServices]=fill(2,nServices);
  parameter Real closureYears[nServices]=fill(8,nServices);
  parameter Real planningYears[nServices]=fill(2,nServices);
  parameter Boolean allowClosure=true;
  parameter Boolean automaticInvestment=false "False executes specified investment spending; true limits goal-seeking orders by it";

  parameter Real wageGrowth=0.03, priceGrowth=0.02, productivityGrowth=0;
  parameter Boolean annualFlowAnchoring=true
    "Treat baseline money flows as previous annual totals; false retains v2 instantaneous-rate convention";
  parameter Real wageOpening=if annualFlowAnchoring then annualOpeningFactor(wageGrowth) else 1;
  parameter Real priceOpening=if annualFlowAnchoring then annualOpeningFactor(priceGrowth) else 1;
  parameter Real taxOpening=if annualFlowAnchoring then annualOpeningFactor(taxBaseGrowth) else 1;
  parameter Real grantOpening=if annualFlowAnchoring then annualOpeningFactor(grantGrowth) else 1;
  parameter Real feeOpening=if annualFlowAnchoring then annualOpeningFactor(feeGrowth) else 1;
  parameter Real pensionOpening=if annualFlowAnchoring then annualOpeningFactor(pensionGrowth) else 1;
  parameter Real taxBaseGrowth=0.035, grantGrowth=0.02, feeGrowth=0.02, pensionGrowth=0.02;
  parameter Real incomeWeights[5]={0,0,0,1,0.55} "Illustrative taxable-income exposure; includes pensions";
  parameter Real taxLagYears=1 "Smoothing proxy, NOT statutory population reference date";
  parameter Real equalisationOffset=0.95 "Sensitivity, NOT statutory equalisation rules";
  parameter Boolean useExternalRevenue=false "External totals replace the simplified internal revenue calculation";
  parameter Boolean useExternalTax=false "Replace only tax; keep the internal grant and equalisation path unchanged";
  parameter Real rateAdjustmentYears=3 "Illustrative debt repricing delay";
  parameter Real cashTarget=cash0, liquidityYears=0.25, repaymentYears=0.25;
initial equation
  assert(size(extraCostPath,1)>0 and min(extraCostPath)>=0 and min(extraCostPaymentPath)>=0,
    "Extra cost and payment paths must be nonempty and nonnegative");
  assert(min(p0)>0 and births0>=0,"Positive opening cohorts and nonnegative births required");
  assert(min(deathRates)>=0 and min(ageRates)>=0 and abs(ageRates[5])<1e-15,"Invalid demographic rates/open age group");
  assert(min(sectorShares)>=0 and abs(sum(sectorShares)-1)<1e-10,"sectorShares must sum to one");
  assert(min(payrollShares)>=0 and abs(sum(payrollShares)-1)<1e-10,"payrollShares must sum to one");
  assert(min(otherExpenseShares)>=0 and abs(sum(otherExpenseShares)-1)<1e-10,"otherExpenseShares must sum to one");
  assert(min(operatingRevenueShares)>=0 and abs(sum(operatingRevenueShares)-1)<1e-10,"operatingRevenueShares must sum to one");
  assert(min(assetShares)>=0 and abs(sum(assetShares)-1)<1e-10,"assetShares must sum to one");
  assert(min(investmentShares)>=0 and abs(sum(investmentShares)-1)<1e-10,"investmentShares must sum to one");
  assert(min({min(serviceWeights[i,:]) for i in 1:nServices})>=0 and min(demand0)>0,"Invalid service weights or reference demand");
  assert(min(compensationPerFTE)>0 and min(staff0)>0 and min(staffPerUnit)>0 and min(minimumStaff)>=0,"Invalid staffing parameters");
  assert(min(hiringYears)>0 and min(reductionYears)>0,"Staff adjustment times must be positive");
  assert(min(maxStaffIncrease)>=0 and min(maxStaffDecrease)>=0 and min(externalCapacity0)>=0,"Negative staffing or external capacity limit");
  assert(min(fixedCostShare)>=0 and min(facilityCostShare)>=0 and max(fixedCostShare+facilityCostShare)<=1,"Invalid cost shares");
  assert(min(purchaseUnitCost)>=0,"Negative purchased-service price");
  assert(min(staffReductionCost)>=0 and min(capacityClosureCost)>=0,"Negative transition cost");
  assert(min(capacity0)>0 and min(capacityUnitCost)>0 and min(assetAllocation)>=0,"Invalid capacity/asset parameters");
  assert(abs(sum(assetAllocation)-assets0)<1e-7,"Asset allocation must reconcile to assets0");
  assert(workInProgress0>=0 and min(constructionUnits0)>=0 and min(constructionMoney0)>=0,"Negative initial construction");
  assert(min(physicalLifeYears)>0 and min(accountingLifeYears)>0 and min(constructionYears)>0 and min(closureYears)>0 and min(planningYears)>0,"Capital times must be positive");
  assert(min({wageGrowth,priceGrowth,productivityGrowth,taxBaseGrowth,grantGrowth,feeGrowth,pensionGrowth})>-1,"Annual growth fractions must exceed -1");
  assert(min(incomeWeights)>=0 and sum(incomeWeights.*p0)>0 and taxRate0>0 and taxLagYears>0,"Invalid tax exposure parameters");
  assert(equalisationOffset>=0 and equalisationOffset<=1,"Equalisation sensitivity must be in [0,1]");
  assert(debt0>=0 and cash0>=0 and cashTarget>=0 and rateAdjustmentYears>0 and liquidityYears>0 and repaymentYears>0,"Invalid financing parameters");
  assert(min({tax0,grants0,payroll0,pension0,otherExpense0,operatingRevenue0,assets0,depreciation0,investment0})>=0,"Negative initial ledger component");
end Parameters;
