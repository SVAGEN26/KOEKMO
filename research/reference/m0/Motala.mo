within ;
package Motala "Annual municipal scenario model; money in mnkr, time in model years"
  partial model Assumptions "Shared public scenario parameters"
    parameter Integer horizon(min=1)=8 "Number of annual transitions; time is measured in model years";
    parameter Real p0[5]={2894,4629,1575,23019,11022}*(43131/43139)
      "Published cohorts proportionally reconciled to published total";
    parameter Real deathRates[5]={0.0004,0.0001,0.0002,0.0018,0.03853357878008014};
    parameter Real residualMigration[5]={-44.63234187162425,62.14678281833085,11.894277120084553,-238.86311941128406,37.964246056899356}
      "Calibrated cohort residuals, including statistical adjustments";
    parameter Real migrationWeights[5]={0.15,0.12,0.03,0.65,0.05};
    parameter Real educationWeights[3]={0.25,0.60,0.15};
    parameter Real sectorCosts[3]={1250,600,1173};
    parameter Real tax0=2330, grants0=987, debt0=1040, cash0=81, assets0=2997;
    parameter Real depreciation0=180, financialIncome=15, otherFinancialExpense=4, births0=334;
    parameter Real payroll0=2288, pension0=190, otherOperatingExpense0=1297, operatingRevenue0=751;
    parameter Real netCostRoundingAdjustment=-1 "Reconciles rounded gross components to reported net cost";
    parameter Real taxGrowth=0.035, grantGrowth=0.02, wageGrowth=0.03, priceGrowth=0.02;
    parameter Real productivityGrowth=0, migrationDelta=0, birthChange=0;
    parameter Real interestRate=21/1040, taxRate=21.7, baseTaxRate=21.7;
    parameter Real investment=413, adjustment=0.5, equalisationOffset=0.95;
    parameter Real fixedShare=0.25, populationRevenueElasticity=1;
    parameter Real pensionGrowth=0.02, operatingRevenueGrowth=0.02;
    parameter Real pensionExpensePath[horizon]={pension0*(1+pensionGrowth)^i for i in 1:horizon};
    parameter Real pensionCashPaymentsPath[horizon]=pensionExpensePath
      "Illustrative until an independently sourced pension cash-payment path is available";
    parameter Real referenceTax[horizon]={tax0*(1+taxGrowth)^i for i in 1:horizon};
    parameter Real referenceGrants[horizon]={grants0*(1+grantGrowth)^i for i in 1:horizon};
    parameter Real referencePopulation[horizon]=fill(sum(p0),horizon);
    parameter Boolean importedRevenue=false;
    parameter Real investmentPath[horizon]=fill(investment,horizon)
      "Annual investment, mnkr; commissioned in the same year";
    parameter Real interestRatePath[horizon]=fill(interestRate,horizon)
      "Annual effective interest rate on opening debt, fraction";
    parameter Real migrationDeltaPath[horizon]=fill(migrationDelta,horizon);
    parameter Real birthChangePath[horizon]=fill(birthChange,horizon);
    parameter Real serviceAdjustment[3]=fill(adjustment,3)
      "Annual capacity adaptation by education, care, other services";
    parameter Real serviceFixedShare[3]=fill(fixedShare,3);
    final parameter Real life=assets0/depreciation0;
  initial equation
    assert(horizon >= 1,"horizon must be at least one year");
    assert(min(p0) > 0,"Every initial cohort must be positive");
    assert(min(deathRates) >= 0 and max(deathRates) <= 1,"deathRates must lie in [0,1]");
    assert(min(migrationWeights) >= 0 and abs(sum(migrationWeights)-1) < 1e-10,
      "migrationWeights must be nonnegative and sum to one");
    assert(min(educationWeights) >= 0 and abs(sum(educationWeights)-1) < 1e-10,
      "educationWeights must be nonnegative and sum to one");
    assert(min(sectorCosts) >= 0 and sum(sectorCosts) > 0,"sectorCosts must define positive total service weights");
    assert(min(serviceAdjustment) >= 0 and max(serviceAdjustment) <= 1,"serviceAdjustment must lie in [0,1]");
    assert(min(serviceFixedShare) >= 0 and max(serviceFixedShare) <= 1,"serviceFixedShare must lie in [0,1]");
    assert(assets0 > 0 and depreciation0 > 0 and depreciation0 <= assets0,
      "Initial depreciable assets and depreciation must imply a life of at least one year");
    assert(debt0 >= 0 and cash0 >= 0,"Initial debt and cash must be nonnegative");
    assert(baseTaxRate > 0 and taxRate >= 0,"baseTaxRate must be positive and taxRate nonnegative");
    assert(min(referencePopulation) > 0,"referencePopulation must be positive in every year");
    assert(min(investmentPath) >= 0,"investmentPath must be nonnegative; disposals are not modelled");
    assert(births0 >= 0 and min(birthChangePath) >= -1,"Birth assumptions must not produce negative births");
    assert(min(pensionExpensePath) >= 0 and min(pensionCashPaymentsPath) >= 0,"Pension paths must be nonnegative");
    assert(taxGrowth > -1 and grantGrowth > -1 and wageGrowth > -1 and priceGrowth > -1
      and productivityGrowth > -1 and pensionGrowth > -1 and operatingRevenueGrowth > -1,
      "Annual growth rates must exceed -1 (rates are fractions, not percentages)");
    assert(equalisationOffset >= 0 and equalisationOffset <= 1,"equalisationOffset must lie in [0,1]");
    assert(payroll0 >= 0 and pension0 >= 0 and otherOperatingExpense0 >= 0 and operatingRevenue0 >= 0,
      "Initial operating components must be nonnegative");
  end Assumptions;

  package Components "Annual components sharing one event clock"
    model Demography "Five cohorts with explicit population conservation"
      parameter Real p0[5];
      parameter Real deathRates[5];
      parameter Real residualMigration[5];
      parameter Real migrationWeights[5];
      parameter Real births0;
      input Boolean tick;
      input Real migrationDelta;
      input Real birthChange;
      discrete output Real p[5](start=p0,each fixed=true);
      discrete output Real population(start=sum(p0),fixed=true);
      discrete output Real births(start=births0,fixed=true);
      discrete output Real deaths(start=0,fixed=true);
      discrete output Real migration(start=0,fixed=true);
      discrete output Real populationBalance(start=0,fixed=true) "Persons; must be zero";
    protected
      discrete Real survivors[5](each start=0,each fixed=true);
      discrete Real ageOut[5](each start=0,each fixed=true);
    equation
      assert(min(p) >= 0,"Scenario exhausts an age cohort");
      assert(population > 0,"Scenario exhausts the population");
      assert(abs(populationBalance) < 1e-7*max(1,population),"Population balance failed");
    algorithm
      when tick then
        births := births0*pre(p[4])/p0[4]*(1+birthChange);
        deaths := sum(pre(p).*deathRates);
        survivors := pre(p).*(ones(5)-deathRates);
        ageOut := {survivors[1]/7,survivors[2]/9,survivors[3]/3,survivors[4]/46,0};
        for i in 1:5 loop
          p[i] := survivors[i]-ageOut[i]+(if i==1 then births else ageOut[i-1])
            +residualMigration[i]+migrationDelta*migrationWeights[i];
        end for;
        population := sum(p);
        migration := sum(residualMigration)+migrationDelta*sum(migrationWeights);
        populationBalance := population-pre(population)-births+deaths-migration;
      end when;
    end Demography;

    model Services "Demand and separate sector capacity adjustment"
      parameter Real p0[5];
      parameter Real educationWeights[3];
      parameter Real sectorCosts[3];
      parameter Real adjustment[3];
      parameter Real fixedShare[3];
      input Boolean tick;
      input Real p[5];
      discrete output Real capacity[3](each start=1,each fixed=true);
      discrete output Real demand[3](each start=1,each fixed=true);
      discrete output Real educationIndex(start=1,fixed=true);
      discrete output Real careIndex(start=1,fixed=true);
      discrete output Real serviceVolume(start=1,fixed=true);
    algorithm
      when tick then
        educationIndex := sum({educationWeights[i]*p[i]/p0[i] for i in 1:3});
        careIndex := p[5]/p0[5];
        demand := {educationIndex,careIndex,sum(p)/sum(p0)};
        capacity := pre(capacity)+adjustment.*(fixedShare+(ones(3)-fixedShare).*demand-pre(capacity));
        serviceVolume := sum(sectorCosts.*capacity)/sum(sectorCosts);
      end when;
    end Services;

    model OperatingAccounts "Accrual expenses separated from pension payments"
      parameter Real population0;
      parameter Real payroll0;
      parameter Real pension0;
      parameter Real otherOperatingExpense0;
      parameter Real operatingRevenue0;
      parameter Real netCostRoundingAdjustment;
      parameter Real wageGrowth;
      parameter Real priceGrowth;
      parameter Real operatingRevenueGrowth;
      parameter Real productivityGrowth;
      input Boolean tick;
      input Real population;
      input Real serviceVolume;
      input Real pensionExpenseInput;
      input Real pensionCashPaymentsInput;
      discrete output Real wageIndex(start=1,fixed=true);
      discrete output Real priceIndex(start=1,fixed=true);
      discrete output Real revenueIndex(start=1,fixed=true);
      discrete output Real productivity(start=1,fixed=true);
      discrete output Real payroll(start=payroll0,fixed=true);
      discrete output Real pensionExpense(start=pension0,fixed=true);
      discrete output Real pensionCashPayments(start=pension0,fixed=true)
        "Initial value is an illustrative placeholder, not an observed payment";
      discrete output Real otherOperatingExpense(start=otherOperatingExpense0,fixed=true);
      discrete output Real operatingRevenue(start=operatingRevenue0,fixed=true);
      discrete output Real cost(start=payroll0+pension0+otherOperatingExpense0-operatingRevenue0+netCostRoundingAdjustment,fixed=true);
    algorithm
      when tick then
        wageIndex := pre(wageIndex)*(1+wageGrowth);
        priceIndex := pre(priceIndex)*(1+priceGrowth);
        revenueIndex := pre(revenueIndex)*(1+operatingRevenueGrowth);
        productivity := pre(productivity)*(1+productivityGrowth);
        payroll := payroll0*wageIndex*serviceVolume/productivity;
        otherOperatingExpense := otherOperatingExpense0*priceIndex*serviceVolume;
        operatingRevenue := operatingRevenue0*revenueIndex*population/population0;
        pensionExpense := pensionExpenseInput;
        pensionCashPayments := pensionCashPaymentsInput;
        cost := payroll+pensionExpense+otherOperatingExpense-operatingRevenue+netCostRoundingAdjustment;
      end when;
    end OperatingAccounts;

    model Revenue "Lagged population and illustrative tax-base equalisation"
      parameter Real p0[5];
      parameter Real tax0;
      parameter Real grants0;
      parameter Real taxRate;
      parameter Real baseTaxRate;
      parameter Real equalisationOffset;
      parameter Real populationRevenueElasticity;
      parameter Boolean importedRevenue;
      input Boolean tick;
      input Real p[5];
      input Real referenceTax;
      input Real referenceGrants;
      input Real referencePopulation;
      discrete output Real tax(start=tax0,fixed=true);
      discrete output Real grants(start=grants0,fixed=true);
    protected
      discrete Real popFactor(start=1,fixed=true);
      discrete Real standardTax(start=0,fixed=true);
      discrete Real composition(start=1,fixed=true);
      discrete Real deviation(start=0,fixed=true);
    algorithm
      when tick then
        popFactor := if importedRevenue then sum(pre(p))/referencePopulation
          else (sum(pre(p))/sum(p0))^populationRevenueElasticity;
        standardTax := referenceTax*popFactor;
        composition := (pre(p[4])/p0[4])/(sum(pre(p))/sum(p0));
        deviation := standardTax*(composition-1);
        tax := (standardTax+deviation)*taxRate/baseTaxRate;
        grants := referenceGrants*popFactor-equalisationOffset*deviation;
      end when;
    end Revenue;

    model Capital "Blended depreciation proxy; no asset-vintage data assumed"
      parameter Real assets0;
      parameter Real depreciation0;
      parameter Real life;
      input Boolean tick;
      input Real investment;
      discrete output Real assets(start=assets0,fixed=true);
      discrete output Real depreciation(start=depreciation0,fixed=true);
      discrete output Real assetBalance(start=0,fixed=true) "mnkr; must be zero";
    equation
      assert(assets >= 0,"Depreciation exhausts assets");
      assert(abs(assetBalance) < 1e-7*max(1,assets),"Asset balance failed");
    algorithm
      when tick then
        depreciation := (pre(assets)+0.5*investment)/life;
        assets := pre(assets)+investment-depreciation;
        assetBalance := assets-pre(assets)-investment+depreciation;
      end when;
    end Capital;

    model Finance "Result, cash bridge and debt repayment waterfall"
      parameter Real debt0;
      parameter Real cash0;
      parameter Real interestRate0;
      parameter Real result0;
      parameter Real financialIncome;
      parameter Real otherFinancialExpense;
      input Boolean tick;
      input Real tax;
      input Real grants;
      input Real cost;
      input Real depreciation;
      input Real pensionExpense;
      input Real pensionCashPayments;
      input Real investment;
      input Real interestRate;
      discrete output Real result(start=result0,fixed=true);
      discrete output Real interest(start=debt0*interestRate0,fixed=true);
      discrete output Real operatingCash(start=0,fixed=true);
      discrete output Real debt(start=debt0,fixed=true);
      discrete output Real cash(start=cash0,fixed=true);
      discrete output Real borrowing(start=0,fixed=true);
      discrete output Real repayment(start=0,fixed=true);
      discrete output Real cashBalance(start=0,fixed=true) "mnkr; must be zero";
      discrete output Real debtBalance(start=0,fixed=true) "mnkr; must be zero";
    protected
      discrete Real financingGap(start=0,fixed=true);
    equation
      assert(debt >= 0,"Debt must not become negative");
      assert(abs(debtBalance) < 1e-7*max(1,debt),"Debt balance failed");
      assert(abs(cashBalance) < 1e-7*max(1,abs(operatingCash)),"Cash balance failed");
    algorithm
      when tick then
        interest := pre(debt)*interestRate;
        result := tax+grants-cost-depreciation+financialIncome-interest-otherFinancialExpense;
        operatingCash := result+depreciation+pensionExpense-pensionCashPayments;
        financingGap := investment-operatingCash;
        borrowing := max(0,financingGap);
        repayment := min(pre(debt),max(0,-financingGap));
        debt := pre(debt)+borrowing-repayment;
        cash := pre(cash)+operatingCash-investment+borrowing-repayment;
        debtBalance := debt-pre(debt)-borrowing+repayment;
        cashBalance := cash-pre(cash)-operatingCash+investment-borrowing+repayment;
      end when;
    end Finance;
  end Components;

  model Annual "Composed annual scenario; public parameters and outputs remain compatible"
    extends Assumptions;
    discrete Integer yearIndex(start=0,fixed=true);
    Real p[5], population, capacity[3], demand[3];
    Real wageIndex, priceIndex, revenueIndex, productivity, serviceVolume;
    Real payroll, pensionExpense, pensionCashPayments, otherOperatingExpense, operatingRevenue;
    Real operatingCash, tax, grants, cost, depreciation, result, interest;
    Real debt, cash, assets, educationIndex, careIndex, births, deaths, migration, borrowing, repayment;
    Real populationBalance "Population conservation residual, persons";
    Real assetBalance, cashBalance, debtBalance "Accounting residuals, mnkr";
    Real annualInvestment, annualInterestRate "Current forecast inputs; first-year inputs at time zero";
    Components.Demography demography(
      p0=p0,deathRates=deathRates,residualMigration=residualMigration,
      migrationWeights=migrationWeights,births0=births0,
      tick=tick,migrationDelta=migrationDeltaPath[pathIndex],birthChange=birthChangePath[pathIndex]);
    Components.Services services(
      p0=p0,educationWeights=educationWeights,sectorCosts=sectorCosts,
      adjustment=serviceAdjustment,fixedShare=serviceFixedShare,tick=tick,p=demography.p);
    Components.OperatingAccounts operations(
      population0=sum(p0),payroll0=payroll0,pension0=pension0,
      otherOperatingExpense0=otherOperatingExpense0,operatingRevenue0=operatingRevenue0,
      netCostRoundingAdjustment=netCostRoundingAdjustment,wageGrowth=wageGrowth,
      priceGrowth=priceGrowth,operatingRevenueGrowth=operatingRevenueGrowth,
      productivityGrowth=productivityGrowth,tick=tick,population=demography.population,
      serviceVolume=services.serviceVolume,pensionExpenseInput=pensionExpensePath[pathIndex],
      pensionCashPaymentsInput=pensionCashPaymentsPath[pathIndex]);
    Components.Revenue revenues(
      p0=p0,tax0=tax0,grants0=grants0,taxRate=taxRate,baseTaxRate=baseTaxRate,
      equalisationOffset=equalisationOffset,populationRevenueElasticity=populationRevenueElasticity,
      importedRevenue=importedRevenue,tick=tick,p=demography.p,
      referenceTax=referenceTax[pathIndex],referenceGrants=referenceGrants[pathIndex],
      referencePopulation=referencePopulation[pathIndex]);
    Components.Capital capital(
      assets0=assets0,depreciation0=depreciation0,life=life,tick=tick,investment=annualInvestment);
    Components.Finance finance(
      debt0=debt0,cash0=cash0,interestRate0=interestRate,
      result0=tax0+grants0-(payroll0+pension0+otherOperatingExpense0-operatingRevenue0+netCostRoundingAdjustment)
        -depreciation0+financialIncome-debt0*interestRate-otherFinancialExpense,
      financialIncome=financialIncome,otherFinancialExpense=otherFinancialExpense,tick=tick,
      tax=revenues.tax,grants=revenues.grants,cost=operations.cost,depreciation=capital.depreciation,
      pensionExpense=operations.pensionExpense,pensionCashPayments=operations.pensionCashPayments,
      investment=annualInvestment,interestRate=annualInterestRate);
  protected
    Boolean tick "One common event per forecast year; no updates beyond horizon";
    Integer pathIndex;
  equation
    tick = sample(1,1) and time <= horizon;
    when tick then
      yearIndex = pre(yearIndex)+1;
    end when;
    pathIndex = max(1,yearIndex);
    annualInvestment = investmentPath[pathIndex];
    annualInterestRate = interestRatePath[pathIndex];
    p = demography.p;
    population = demography.population;
    births = demography.births;
    deaths = demography.deaths;
    migration = demography.migration;
    populationBalance = demography.populationBalance;
    capacity = services.capacity;
    demand = services.demand;
    educationIndex = services.educationIndex;
    careIndex = services.careIndex;
    serviceVolume = services.serviceVolume;
    wageIndex = operations.wageIndex;
    priceIndex = operations.priceIndex;
    revenueIndex = operations.revenueIndex;
    productivity = operations.productivity;
    payroll = operations.payroll;
    pensionExpense = operations.pensionExpense;
    pensionCashPayments = operations.pensionCashPayments;
    otherOperatingExpense = operations.otherOperatingExpense;
    operatingRevenue = operations.operatingRevenue;
    cost = operations.cost;
    tax = revenues.tax;
    grants = revenues.grants;
    assets = capital.assets;
    depreciation = capital.depreciation;
    assetBalance = capital.assetBalance;
    result = finance.result;
    interest = finance.interest;
    operatingCash = finance.operatingCash;
    debt = finance.debt;
    cash = finance.cash;
    borrowing = finance.borrowing;
    repayment = finance.repayment;
    cashBalance = finance.cashBalance;
    debtBalance = finance.debtBalance;
    annotation(experiment(StartTime=0,StopTime=8,Interval=1),
      Documentation(info="<html><p>Annual scenario model with a shared clock and six separately inspectable components.
Time zero is the closing base-year balance; each integer time advances one year. All amounts are nominal mnkr.
Set the simulation stop time to horizon; longer runs hold the final state. No annual transition occurs at initialization.
The default experiment is eight years and does not automatically follow a changed horizon.</p>
<p>The original Annual parameter and output names remain available. Optional investmentPath, interestRatePath,
migrationDeltaPath and birthChangePath accept one value per forecast year. serviceAdjustment and serviceFixedShare
allow independent responses for education, care and other services. These new inputs are currently Modelica-only.
Initial cost and result reconcile from operating components; sectorCosts only weight service volume.
Population, asset, debt and cash residuals are exposed and asserted at annual transitions.</p>
<p>This is not a validated municipal forecast. Five broad cohorts assume uniform ageing; births use working-age
population as a proxy. Migration residuals include statistical adjustments. The 65+ care index, illustrative service
weights, approximate equalisation, blended depreciation, opening-debt interest and simplified liquidity policy still
require better data. Pension cash payments default to expense and the initial payment is not an observation.
No working-capital, asset-vintage, debt-maturity or complete pension-liability model is implied.
Agreement with a reference implementation establishes numerical compatibility, not forecasting accuracy.</p></html>"));
  end Annual;
end Motala;
