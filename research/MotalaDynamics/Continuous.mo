within MotalaDynamics;
model Continuous "M2 component: instantiate inside a scenario so input bindings are equations"
  extends Parameters;
  input Real migration[5]=migration0;
  input Real fertilityMultiplier=1;
  input Real demandMultiplier[nServices]=ones(nServices);
  input Real staffingTarget[nServices]=ones(nServices);
  input Real capacityTarget[nServices]=ones(nServices);
  input Real purchaseCoverage[nServices]=ones(nServices) "Desired share of internal shortfall bought externally";
  input Real externalServiceCapacity[nServices]=externalCapacity0 "Supplier capacity; applied when limitExternalService=true";
  input Real investmentBudget[nServices]=investment0*investmentShares "mnkr/year";
  input Real taxRate=taxRate0;
  input Real marketRate=interestRate0;
  input Real externalTax=tax0, externalGrants=grants0 "Instantaneous annualised rates at the reference tax rate";
  input Real externalTaxSettlement=0 "Collective settlement excluded from externalTax, signed mnkr/year";
  input Real taxPayments=tax "Signed tax cash receipt; same-year payment is the default assumption";
  input Real pensionExpense=pension0*pensionOpening*exp(log(1+pensionGrowth)*time/yearSeconds);
  input Real pensionPayments=pensionExpense "Illustrative equality; override independently";
  input Real laborPriceMultiplier=1 "External cost path; set wageGrowth=0 when supplying the full index";
  input Real otherPriceMultiplier=1 "External cost path; set priceGrowth=0 when supplying the full index";
  Integer extraCostYear=integer(floor(time/yearSeconds))+1;
  input Real extraExpense=if extraCostYear<=size(extraCostPath,1) then
    extraCostPath[min(size(extraCostPath,1),max(1,extraCostYear))] else 0
    "Nominal mnkr/year; override for a subannual cost profile";
  input Real extraPayments=if extraCostYear<=size(extraCostPaymentPath,1) then
    extraCostPaymentPath[min(size(extraCostPaymentPath,1),max(1,extraCostYear))] else 0
    "Nominal mnkr/year, independently specified payment profile";

  Real wageIndex(start=wageOpening,fixed=true), priceIndex(start=priceOpening,fixed=true), productivity(start=1,fixed=true);
  Real taxIndex(start=taxOpening,fixed=true), grantIndex(start=grantOpening,fixed=true), feeIndex(start=feeOpening,fixed=true);
  output Real effectiveWageIndex=wageIndex*laborPriceMultiplier;
  output Real effectivePriceIndex=priceIndex*otherPriceMultiplier;
  Real demand[nServices], payrollByService[nServices], otherByService[nServices], revenueByService[nServices];
  output Real modelYear=time/yearSeconds;
  output Real population=demography.population;
  output Real payroll=sum(payrollByService), otherOperatingExpense=sum(otherByService);
  output Real operatingRevenue=sum(revenueByService);
  output Real transitionExpense=effectiveWageIndex*sum(staffReductionCost.*services.staffDecrease)
    +effectivePriceIndex*sum(capacityClosureCost.*capital.closure);
  output Real netOperatingCost=payroll+otherOperatingExpense+pensionExpense+transitionExpense+extraExpense-operatingRevenue+costRounding;
  output Real depreciation=sum(capital.depreciation), disposalLoss=sum(capital.disposalLoss);
  output Real tax=revenue.tax, grants=revenue.grants, taxSettlement=revenue.taxSettlement;
  output Real taxReceivable=finance.taxReceivable;
  output Real interest=finance.interest, resultRate=finance.result;
  output Real debt=finance.debt, cash=finance.cash;
  output Real assets=sum(capital.assets), workInProgress=sum(capital.constructionMoney);
  output Real investment=sum(capital.investment), operatingCash=finance.operatingCash;
  output Real netPosition=assets+workInProgress+cash+taxReceivable-debt-finance.pensionAccrualBalance-finance.extraAccrualBalance;
  output Real balanceResidual=netPosition-(assets0+sum(constructionMoney0)+cash0+taxReceivable0-debt0)-finance.cumulativeResult;
  output Real cumulativePayroll(start=0,fixed=true), cumulativeOtherExpense(start=0,fixed=true);
  output Real cumulativeRevenue(start=0,fixed=true), cumulativeTax(start=0,fixed=true), cumulativeGrants(start=0,fixed=true);
  output Real cumulativeDepreciation(start=0,fixed=true), cumulativeDisposal(start=0,fixed=true);
  output Real cumulativeInterest(start=0,fixed=true), cumulativePensionExpense(start=0,fixed=true);
  output Real cumulativeTransitionExpense(start=0,fixed=true);
  output Real cumulativeExtraExpense(start=0,fixed=true), cumulativeExtraPayments(start=0,fixed=true);
  output Real cumulativeTaxSettlement(start=0,fixed=true);
  output Real cumulativeUnmet[nServices](each start=0,each fixed=true);
  output Real cumulativeDemand[nServices](each start=0,each fixed=true);
  output Real cumulativePurchased[nServices](each start=0,each fixed=true);
  output Real cumulativePayrollByService[nServices](each start=0,each fixed=true);
  output Real cumulativeOtherByService[nServices](each start=0,each fixed=true);

  Demography demography(p0=p0,births0=births0,deathRates=deathRates,ageRates=ageRates,
    enabled=demographyEnabled,migration=migration,fertilityMultiplier=fertilityMultiplier)
    annotation(Placement(transformation(origin={-270,0},extent={{-75,-56},{75,56}})));
  Services services(n=nServices,staff0=staff0,staffPerUnit=staffPerUnit,minimumStaff=minimumStaff,
    hiringYears=hiringYears,reductionYears=reductionYears,demand=demand,capacity=capital.capacity,
    staffingTarget=staffingTarget,purchaseCoverage=purchaseCoverage,productivity=productivity,
    limitStaffChanges=limitStaffChanges,maxStaffIncrease=maxStaffIncrease,maxStaffDecrease=maxStaffDecrease,
    limitExternalService=limitExternalService,externalCapacity=externalServiceCapacity)
    annotation(Placement(transformation(origin={0,110},extent={{-75,-56},{75,56}})));
  Capital capital(n=nServices,capacity0=capacity0,asset0=assetAllocation,units0=constructionUnits0,
    money0=constructionMoney0,physicalLife=physicalLifeYears,accountingLife=accountingLifeYears,
    constructionYears=constructionYears,closureYears=closureYears,planningYears=planningYears,
    allowClosure=allowClosure,automaticInvestment=automaticInvestment,
    desiredCapacity=capacityTarget.*demand,unitCost=capacityUnitCost*effectivePriceIndex,investmentBudget=investmentBudget)
    annotation(Placement(transformation(origin={0,-110},extent={{-75,-56},{75,56}})));
  Revenue revenue(population0=sum(p0),exposure0=sum(incomeWeights.*p0),tax0=tax0,grants0=grants0,
    taxRate0=taxRate0,lagYears=taxLagYears,equalisationOffset=equalisationOffset,useExternal=useExternalRevenue,
    useExternalTax=useExternalTax,
    population=population,exposure=sum(incomeWeights.*demography.p),taxRate=taxRate,
    taxIndex=taxIndex,grantIndex=grantIndex,externalTax=externalTax,externalGrants=externalGrants,
    externalTaxSettlement=externalTaxSettlement)
    annotation(Placement(transformation(origin={270,110},extent={{-75,-56},{75,56}})));
  Finance finance(debt0=debt0,cash0=cash0,rate0=interestRate0,rateYears=rateAdjustmentYears,
    cashTarget=cashTarget,liquidityYears=liquidityYears,repaymentYears=repaymentYears,
    resultBeforeInterest=tax+grants-netOperatingCost-depreciation-disposalLoss+financialIncome-otherFinancialExpense,
    marketRate=marketRate,depreciation=depreciation,disposalLoss=disposalLoss,
    pensionExpense=pensionExpense,pensionPayments=pensionPayments,investment=investment,
    extraExpense=extraExpense,extraPayments=extraPayments,
    taxReceivable0=taxReceivable0,taxRevenue=tax,taxPayments=taxPayments)
    annotation(Placement(transformation(origin={270,-110},extent={{-75,-56},{75,56}})));
equation
  der(wageIndex)=log(1+wageGrowth)*wageIndex/yearSeconds;
  der(priceIndex)=log(1+priceGrowth)*priceIndex/yearSeconds;
  der(productivity)=log(1+productivityGrowth)*productivity/yearSeconds;
  der(taxIndex)=log(1+taxBaseGrowth)*taxIndex/yearSeconds;
  der(grantIndex)=log(1+grantGrowth)*grantIndex/yearSeconds;
  der(feeIndex)=log(1+feeGrowth)*feeIndex/yearSeconds;
  for i in 1:nServices loop
    demand[i]=demandMultiplier[i]*sum(serviceWeights[i,j]*demography.p[j] for j in 1:5);
    payrollByService[i]=effectiveWageIndex*compensationPerFTE[i]*services.staff[i];
    otherByService[i]=effectivePriceIndex*(otherExpense0*otherExpenseShares[i]*(fixedCostShare[i]
      +facilityCostShare[i]*capital.capacity[i]/capacity0[i]
      +(1-fixedCostShare[i]-facilityCostShare[i])*services.ownService[i]/demand0[i])
      +purchaseUnitCost[i]*services.purchasedService[i]);
    revenueByService[i]=operatingRevenue0*operatingRevenueShares[i]*feeIndex*services.delivered[i]/demand0[i];
    der(cumulativeUnmet[i])=services.unmetService[i]/yearSeconds;
    der(cumulativeDemand[i])=demand[i]/yearSeconds;
    der(cumulativePurchased[i])=services.purchasedService[i]/yearSeconds;
    der(cumulativePayrollByService[i])=payrollByService[i]/yearSeconds;
    der(cumulativeOtherByService[i])=otherByService[i]/yearSeconds;
  end for;
  der(cumulativePayroll)=payroll/yearSeconds;
  der(cumulativeOtherExpense)=otherOperatingExpense/yearSeconds;
  der(cumulativeRevenue)=operatingRevenue/yearSeconds;
  der(cumulativeTax)=tax/yearSeconds;
  der(cumulativeGrants)=grants/yearSeconds;
  der(cumulativeDepreciation)=depreciation/yearSeconds;
  der(cumulativeDisposal)=disposalLoss/yearSeconds;
  der(cumulativeInterest)=interest/yearSeconds;
  der(cumulativePensionExpense)=pensionExpense/yearSeconds;
  der(cumulativeTransitionExpense)=transitionExpense/yearSeconds;
  der(cumulativeExtraExpense)=extraExpense/yearSeconds;
  der(cumulativeExtraPayments)=extraPayments/yearSeconds;
  der(cumulativeTaxSettlement)=taxSettlement/yearSeconds;
  assert(min(demandMultiplier)>=0,"Negative demand multiplier");
  assert(laborPriceMultiplier>0 and otherPriceMultiplier>0,"External cost indices must be positive");
  assert(abs(balanceResidual)<1e-3,"Combined asset/cash/debt/accrual/result identity failed");
  annotation(Icon(coordinateSystem(extent={{-100,-75},{100,75}}),graphics={
      Rectangle(extent={{-100,-75},{100,75}},lineColor={40,95,140},fillColor={235,245,252},fillPattern=FillPattern.Solid,radius=8),
      Text(extent={{-95,30},{95,65}},textString="M2",fontSize=21,textColor={40,95,140}),
      Text(extent={{-95,-27},{95,25}},textString="Continuous municipal\nservice and finance",fontSize=16,textColor={35,50,65}),
      Text(extent={{-95,-68},{95,-35}},textString="%name",fontSize=14,textColor={40,95,140})}),
    Diagram(coordinateSystem(extent={{-410,-250},{410,280}}),graphics={
      Text(extent={{-400,235},{400,270}},textString="M2: continuous service and finance scenarios",fontSize=24,textColor={35,50,65}),
      Line(points={{-195,20},{-135,20},{-135,110},{-75,110}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-190,115},{-80,150}},textString="Service demand",fontSize=13,textColor={35,50,65}),
      Line(points={{-195,-20},{-135,-20},{-135,-110},{-75,-110}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-225,-160},{-85,-125}},textString="Capacity target\nfrom demand",fontSize=13,textColor={35,50,65}),
      Line(points={{-270,56},{-270,195},{270,195},{270,166}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{-150,197},{155,225}},textString="Population / income exposure",fontSize=14,textColor={35,50,65}),
      Line(points={{0,-54},{0,54}},color={155,95,35},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{5,-30},{105,30}},textString="Available\ncapacity",fontSize=13,textColor={35,50,65}),
      Line(points={{75,110},{135,110},{135,-80},{195,-80}},color={35,115,85},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{135,5},{265,55}},textString="Operating costs\nless fees",fontSize=13,textColor={35,50,65}),
      Line(points={{270,54},{270,-54}},color={70,95,120},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{275,-22},{400,22}},textString="Tax / grants",fontSize=13,textColor={35,50,65}),
      Line(points={{75,-110},{195,-110}},color={155,95,35},thickness=0.5,arrow={Arrow.None,Arrow.Filled}),
      Text(extent={{80,-180},{195,-125}},textString="Investment /\ndepreciation /\ndisposal losses",fontSize=12,textColor={35,50,65}),
      Text(extent={{-400,-240},{400,-195}},textString="Selected equation bindings, shown as schematic arrows. Double-click a component to inspect it.\nPolicy inputs and cost aggregation are defined in Continuous. Time: seconds; flow rates: per year.",fontSize=13,textColor={35,50,65})}),
    experiment(StartTime=0,StopTime=252460800,Interval=2629800,Tolerance=1e-8));
end Continuous;
