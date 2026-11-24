within ;
model MotalaBrowser "Omslag för webbläsaren: fast kapacitet på 100 år, alla scenariovärden fria parametrar"
  extends Motala.Annual(
    final horizon=100,
    p0={2894,4629,1575,23019,11022}*(43131/43139),
    deathRates={0.0004,0.0001,0.0002,0.0018,0.03853357878008014},
    residualMigration={-44.63234187162425,62.14678281833085,11.894277120084553,-238.86311941128406,37.964246056899356},
    tax0=2330, grants0=987, debt0=1040, cash0=81, assets0=2997, depreciation0=180,
    financialIncome=15, otherFinancialExpense=4, births0=334,
    payroll0=2288, pension0=190, otherOperatingExpense0=1297, operatingRevenue0=751,
    netCostRoundingAdjustment=-1, interestRate=21/940, taxRate=21.7, baseTaxRate=21.7, investment=413,
    revenuePopulation0={3008,4671,1592,23311,10923},
    nationalPopulation0=10587710,
    nationalPopulationPath={10605529,10617229,10590195,10595683,10607632,10633822,10660739,10688729,10717978,10747029,10776335,10806015,10836448,10867945,10900804,10935214,10970081,11005383,11041168,11077299,11113669,11150098,11186370,11222294,11257590,11292060,11325460,11357521,11388169,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275,11417275},
    residualMigrationPath=zeros(100,5),
    employerContributions0=0, employerContributionRatePath=fill(-1,100),
    ageIncomeWeights=ones(5), equalisationCountyRate=0,
    importedRevenueMode=0, novemberPopulation0=43131, importedComponents=zeros(100,3),
    wageGrowthPath=fill(0.03,100),
    priceGrowthPath=fill(0.02,100),
    pensionExpensePath=fill(190,100),
    pensionCashPaymentsPath=fill(190,100),
    referenceTax=fill(2330,100),
    referenceGrants=fill(987,100),
    referencePopulation=fill(43131,100),
    workingCapitalEnabled=false, receivables0=0, payables0=0, grantAdvances0=0,
    collectionDays=0, paymentDays=0, firstYearGrantAdvance=0,
    liquidityPolicy=false, cashReserve=0, deferInvestmentShare=0, prefinanceShare=0,
    projectOpeningStock=0, projectPayment=0, projectOpeningStep=1, projectPlaces=0,
    constructionYears=0, constructionShare=0.5, workInProgress0=0,
    investmentPath=fill(413,100),
    interestRatePath=fill(21/1040,100),
    rateFixingYears=0, rateShock=0, rateShockTime=2026,
    inflationShockPath=zeros(100), inflationWagePassThrough=0.4, inflationPensionPassThrough=8, inflationRateResponse=0.5, inflationGrantCompensation=0,
    migrationDeltaPath=zeros(100),
    birthChangePath=zeros(100),
    serviceAdjustment=fill(0.5,3),
    serviceFixedShare=fill(0.25,3));
  annotation(Documentation(info="<html><p>Omslag för webbläsaren; innehåller inga egna ekvationer. OpenModelica kompilerar det en
gång i webbläsaren (wasm-jit), och varje scenario körs sedan om med -override. Alla värden som sajten skriver över har
egna bokstavliga värden här, så att -override når dem; i Motala.Annual räknas utgångsvärdena fram ur basårsposten, och dit
når inte -override. Hundra år är modellens kapacitet, inte prognosens längd: tiden är kalenderår, start 2025, och sajten
sätter sluttiden till 2025 plus antalet år. Modellen är byggd för 8-10 år framåt, som SKR:s prognoser; längre perioder är räkneexempel.</p></html>"));
end MotalaBrowser;

model MotalaBrowserContinuous "Omslag för webbläsaren kring Motala.Continuous: lager och flöden i kontinuerlig tid"
  extends Motala.Continuous(
    final horizon=100,
    p0={2894,4629,1575,23019,11022}*(43131/43139),
    deathRates={0.0004,0.0001,0.0002,0.0018,0.03867709722785895},
    mortalityRates={0.0004,0.0001,0.0002,0.0018,0.03867709722785895},
    residualMigration={-55.76867645187966,72.77514991631955,13.018386922728377,-241.69945240742777,43.99041944516358},
    tax0=2330, grants0=987, debt0=1040, cash0=81, assets0=2997, depreciation0=180,
    financialIncome=15, otherFinancialExpense=4, births0=334,
    payroll0=2288, pension0=190, otherOperatingExpense0=1297, operatingRevenue0=751,
    netCostRoundingAdjustment=-1, interestRate=21/940, taxRate=21.7, baseTaxRate=21.7, investment=413,
    revenuePopulation0={3008,4671,1592,23311,10923},
    nationalPopulation0=10587710,
    nationalPopulationPath=fill(10605529,100),
    residualMigrationPath=zeros(100,5),
    employerContributions0=0, employerContributionRatePath=fill(-1,100),
    ageIncomeWeights=ones(5), equalisationCountyRate=0,
    importedRevenueMode=0, novemberPopulation0=43131, importedComponents=zeros(100,3),
    wageGrowthPath=fill(0.03,100),
    priceGrowthPath=fill(0.02,100),
    pensionExpensePath=fill(190,100),
    pensionCashPaymentsPath=fill(190,100),
    referenceTax=fill(2330,100),
    referenceGrants=fill(987,100),
    referencePopulation=fill(43131,100),
    workingCapitalEnabled=false, receivables0=0, payables0=0, grantAdvances0=0,
    collectionDays=0, paymentDays=0, firstYearGrantAdvance=0,
    liquidityPolicy=false, cashReserve=0, deferInvestmentShare=0, prefinanceShare=0,
    projectOpeningStock=0, projectPayment=0, projectOpeningStep=1, projectPlaces=0,
    constructionYears=0, constructionShare=0.5, workInProgress0=0,
    investmentPath=fill(413,100),
    interestRatePath=fill(21/1040,100),
    rateFixingYears=0, rateShock=0, rateShockTime=2026,
    inflationShockPath=zeros(100), inflationWagePassThrough=0.4, inflationPensionPassThrough=8, inflationRateResponse=0.5, inflationGrantCompensation=0,
    migrationDeltaPath=zeros(100),
    birthChangePath=zeros(100),
    serviceAdjustment=fill(0.5,3),
    serviceFixedShare=fill(0.25,3));
  annotation(Documentation(info="<html><p>Som <code>MotalaBrowser</code>, men kring
<a href=\"modelica://Motala.Continuous\">Motala.Continuous</a>. Sajten kör den som standard, med Runge-Kutta och tolv steg per
år. Dödstalen (<code>mortalityRates</code>) och restflödet (<code>residualMigration</code>, <code>residualMigrationPath</code>) är
per år i kontinuerlig tid; sajten räknar fram dem på samma sätt som <code>Kommunekonomi.Data.deathRatesPerYear</code> och
<code>calibratedMigrationRates</code> och skriver över dem med -override. Rikets folkmängd står här som ett fast tal och skrivs
alltid över.</p></html>"));
end MotalaBrowserContinuous;
