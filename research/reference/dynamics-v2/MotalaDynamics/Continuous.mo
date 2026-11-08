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
  input Real externalTax=tax0, externalGrants=grants0 "Annual totals at the reference tax rate";
  input Real pensionExpense=pension0*exp(log(1+pensionGrowth)*time/yearSeconds);
  input Real pensionPayments=pensionExpense "Illustrative equality; override independently";

  Real wageIndex(start=1,fixed=true), priceIndex(start=1,fixed=true), productivity(start=1,fixed=true);
  Real taxIndex(start=1,fixed=true), grantIndex(start=1,fixed=true), feeIndex(start=1,fixed=true);
  Real demand[nServices], payrollByService[nServices], otherByService[nServices], revenueByService[nServices];
  output Real modelYear=time/yearSeconds;
  output Real population=demography.population;
  output Real payroll=sum(payrollByService), otherOperatingExpense=sum(otherByService);
  output Real operatingRevenue=sum(revenueByService);
  output Real transitionExpense=wageIndex*sum(staffReductionCost.*services.staffDecrease)
    +priceIndex*sum(capacityClosureCost.*capital.closure);
  output Real netOperatingCost=payroll+otherOperatingExpense+pensionExpense+transitionExpense-operatingRevenue+costRounding;
  output Real depreciation=sum(capital.depreciation), disposalLoss=sum(capital.disposalLoss);
  output Real tax=revenue.tax, grants=revenue.grants;
  output Real interest=finance.interest, resultRate=finance.result;
  output Real debt=finance.debt, cash=finance.cash;
  output Real assets=sum(capital.assets), workInProgress=sum(capital.constructionMoney);
  output Real investment=sum(capital.investment), operatingCash=finance.operatingCash;
  output Real netPosition=assets+workInProgress+cash-debt-finance.pensionAccrualBalance;
  output Real balanceResidual=netPosition-(assets0+sum(constructionMoney0)+cash0-debt0)-finance.cumulativeResult;
  output Real cumulativePayroll(start=0,fixed=true), cumulativeOtherExpense(start=0,fixed=true);
  output Real cumulativeRevenue(start=0,fixed=true), cumulativeTax(start=0,fixed=true), cumulativeGrants(start=0,fixed=true);
  output Real cumulativeDepreciation(start=0,fixed=true), cumulativeDisposal(start=0,fixed=true);
  output Real cumulativeInterest(start=0,fixed=true), cumulativePensionExpense(start=0,fixed=true);
  output Real cumulativeTransitionExpense(start=0,fixed=true);
  output Real cumulativeUnmet[nServices](each start=0,each fixed=true);
  output Real cumulativeDemand[nServices](each start=0,each fixed=true);
  output Real cumulativePurchased[nServices](each start=0,each fixed=true);
  output Real cumulativePayrollByService[nServices](each start=0,each fixed=true);
  output Real cumulativeOtherByService[nServices](each start=0,each fixed=true);

  Demography demography(p0=p0,births0=births0,deathRates=deathRates,ageRates=ageRates,
    enabled=demographyEnabled,migration=migration,fertilityMultiplier=fertilityMultiplier);
  Services services(n=nServices,staff0=staff0,staffPerUnit=staffPerUnit,minimumStaff=minimumStaff,
    hiringYears=hiringYears,reductionYears=reductionYears,demand=demand,capacity=capital.capacity,
    staffingTarget=staffingTarget,purchaseCoverage=purchaseCoverage,productivity=productivity,
    limitStaffChanges=limitStaffChanges,maxStaffIncrease=maxStaffIncrease,maxStaffDecrease=maxStaffDecrease,
    limitExternalService=limitExternalService,externalCapacity=externalServiceCapacity);
  Capital capital(n=nServices,capacity0=capacity0,asset0=assetAllocation,units0=constructionUnits0,
    money0=constructionMoney0,physicalLife=physicalLifeYears,accountingLife=accountingLifeYears,
    constructionYears=constructionYears,closureYears=closureYears,planningYears=planningYears,
    allowClosure=allowClosure,automaticInvestment=automaticInvestment,
    desiredCapacity=capacityTarget.*demand,unitCost=capacityUnitCost*priceIndex,investmentBudget=investmentBudget);
  Revenue revenue(population0=sum(p0),exposure0=sum(incomeWeights.*p0),tax0=tax0,grants0=grants0,
    taxRate0=taxRate0,lagYears=taxLagYears,equalisationOffset=equalisationOffset,useExternal=useExternalRevenue,
    population=population,exposure=sum(incomeWeights.*demography.p),taxRate=taxRate,
    taxIndex=taxIndex,grantIndex=grantIndex,externalTax=externalTax,externalGrants=externalGrants);
  Finance finance(debt0=debt0,cash0=cash0,rate0=interestRate0,rateYears=rateAdjustmentYears,
    cashTarget=cashTarget,liquidityYears=liquidityYears,repaymentYears=repaymentYears,
    resultBeforeInterest=tax+grants-netOperatingCost-depreciation-disposalLoss+financialIncome-otherFinancialExpense,
    marketRate=marketRate,depreciation=depreciation,disposalLoss=disposalLoss,
    pensionExpense=pensionExpense,pensionPayments=pensionPayments,investment=investment);
equation
  der(wageIndex)=log(1+wageGrowth)*wageIndex/yearSeconds;
  der(priceIndex)=log(1+priceGrowth)*priceIndex/yearSeconds;
  der(productivity)=log(1+productivityGrowth)*productivity/yearSeconds;
  der(taxIndex)=log(1+taxBaseGrowth)*taxIndex/yearSeconds;
  der(grantIndex)=log(1+grantGrowth)*grantIndex/yearSeconds;
  der(feeIndex)=log(1+feeGrowth)*feeIndex/yearSeconds;
  for i in 1:nServices loop
    demand[i]=demandMultiplier[i]*sum(serviceWeights[i,j]*demography.p[j] for j in 1:5);
    payrollByService[i]=wageIndex*compensationPerFTE[i]*services.staff[i];
    otherByService[i]=priceIndex*(otherExpense0*otherExpenseShares[i]*(fixedCostShare[i]
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
  assert(min(demandMultiplier)>=0,"Negative demand multiplier");
  assert(abs(balanceResidual)<1e-3,"Combined asset/cash/debt/pension/result identity failed");
  annotation(experiment(StartTime=0,StopTime=252460800,Interval=2629800,Tolerance=1e-8));
end Continuous;
