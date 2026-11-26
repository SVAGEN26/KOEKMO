within ;
model MotalaBrowserContinuous "Omslag för webbläsaren kring Motala.Continuous: lager och flöden i kontinuerlig tid"
  extends Motala.Continuous(
    final horizon=100,
    p0={2894,4629,1575,23019,11022}*(43131/43139),
    deathRates={0.0004,0.0001,0.0002,0.0018,0.03867709722785895},
    mortalityRates=Kommunekonomi.Data.deathRatesPerYear(historyCohorts, historyTotals, historyDeaths),
    residualMigration=if useObservedMigration then observedMigration else Kommunekonomi.Data.calibratedMigrationRates(
      historyCohorts, historyTotals, historyBirths, mortalityRates, ageProfile[1:2, :], olderShares)
      + migrationGroupWeight*(groupMigration - ownMigration) .* p0,
    migrationGroupWeight=0,
    tax0=2330, grants0=987, debt0=1040, cash0=81, assets0=2997, depreciation0=180,
    financialIncome=15, otherFinancialExpense=4, births0=334,
    payroll0=2288, pension0=190, otherOperatingExpense0=1297, operatingRevenue0=751,
    netCostRoundingAdjustment=-1, interestRate=21/990, taxRate=21.7, baseTaxRate=21.7, investment=413,
    revenuePopulation0={3008,4671,1592,23311,10923},
    nationalPopulation0=10587710,
    nationalPopulationPath=fill(10605529,100),
    residualMigrationPath=Kommunekonomi.Data.projectionResiduals(p0, projectedCohorts, followProjection, births0, mortalityRates,
      ageProfile[3:102, :], olderShares, residualMigration),
    employerContributions0=0, employerContributionRatePath=fill(-1,100),
    ageIncomeWeights=ones(5), equalisationCountyRate=0,
    importedRevenueMode=0, novemberPopulation0=43131, importedComponents=revenuePath[:, 4:6],
    wageGrowthPath=fill(0.03,100),
    priceGrowthPath=fill(0.02,100),
    pensionFollowsPayroll=true,
    pensionExpensePath=fill(190,100),
    pensionCashPaymentsPath=fill(190,100),
    referenceTax=revenuePath[:, 1],
    referenceGrants=revenuePath[:, 2],
    referencePopulation=revenuePath[:, 3],
    workingCapitalEnabled=false, receivables0=0, payables0=0, grantAdvances0=0,
    collectionDays=0, paymentDays=0, firstYearGrantAdvance=0,
    liquidityPolicy=true, reserveDays=30, creditLine=0, deferInvestmentShare=0, prefinanceShare=0,
    projectOpeningStock=0, projectPayment=0, projectOpeningStep=1, projectPlaces=0,
    constructionYears=0, constructionShare=0.5, workInProgress0=0,
    investmentPath=fill(413,100),
    interestRatePath=fill(21/990,100),
    rateFixingYears=0, rateShock=0, rateShockTime=2026,
    oneOffCost=0, oneOffCostTime=2027.5, oneOffCostDuration=0.5,
    inflationShockPath=zeros(100), inflationWagePassThrough=0.4, inflationPensionPassThrough=8, inflationRateResponse=0.5, inflationGrantCompensation=0,
    migrationDeltaPath=zeros(100),
    birthChangePath=zeros(100),
    serviceAdjustment=fill(0.5,3),
    serviceFixedShare=fill(0.25,3));
  // Kalibreringen av befolkningen räknas här, i Modelica, när modellen startar: sajten skickar historiken och en eventuell
  // projektion, och -override når dem; dödstal och restflöden räknas om ur dem.
  parameter Units.Persons historyCohorts[3, 5] = {{3202, 4654, 1569, 23540, 10763}, {3008, 4671, 1592, 23311, 10923}, {2894, 4629, 1575, 23019, 11022}}
    "Redovisade invånare per åldersgrupp de tre åren fram till basåret";
  parameter Units.Persons historyTotals[3] = {43728, 43505, 43131} "Redovisad folkmängd samma år";
  parameter Units.Persons historyBirths[2] = {336, 334} "Födda de två senare åren";
  parameter Units.Persons historyDeaths = 468 "Döda under basåret";
  parameter Units.Rate groupMigration[5] = zeros(5) "Flyttnetto per invånare och år i kommunens grupp enligt SKR, medel av basåret och året före";
  parameter Units.Rate ownMigration[5] = zeros(5) "Kommunens eget flyttnetto per invånare och år, samma två år";
  parameter Boolean useObservedMigration = false "Restflödet är det observerade flyttnettot i stället för det kalibrerade";
  parameter Units.PersonsPerYear observedMigration[5] = zeros(5) "Observerat flyttnetto per åldersgrupp, personer per år";
  parameter Units.Persons projectedCohorts[100, 5] = zeros(100, 5) "Befolkningsprojektionens åldersgrupper vid varje årsskifte";
  parameter Boolean followProjection[100] = fill(false, 100) "Året följer projektionen";
  // Intäktsbanan räknas också här: sajten skickar SKR:s bana som den står, och statens ram och förlängningen efter banans
  // sista år räknas av Kommunekonomi.Data.sourcedRevenue.
  parameter Real sourcedRevenue[100, 6] = [fill(2330, 100), fill(987, 100), fill(43131, 100), zeros(100, 3)]
    "Intäktsbanan per år: skatt, bidrag, folkmängd, skatt före slutavräkning, inkomstutjämning och regleringspost";
  parameter Integer sourcedRevenueYears = 0 "Antal år SKR:s bana täcker; 0 = raderna gäller som de står";
  parameter Integer regulationDecidedYears = 0 "Antal år då regleringsposten är statens beslut";
  parameter Boolean stateFrame = true "Statens ram följer rikets skatteunderlag efter de beslutade åren";
  parameter Real taxBaseGrowthPath[100] = fill(0.035, 100) "Rikets skatteunderlag, ökning per år";
  parameter Real revenuePath[100, 6] = Kommunekonomi.Data.sourcedRevenue(sourcedRevenue, sourcedRevenueYears, regulationDecidedYears,
    stateFrame, taxBaseGrowthPath, nationalPopulationPath)
    "Intäktsbanan som modellen använder: skatt, bidrag, folkmängd och de tre delposterna";
  import Units = Kommunekonomi.Units;
  annotation(Documentation(info="<html><p>Omslag kring
<a href=\"modelica://Motala.Continuous\">Motala.Continuous</a>. Sajten kör den med IDA och lagrar tolv värden per
år. Dödstalen (<code>mortalityRates</code>) och restflödet (<code>residualMigration</code>, <code>residualMigrationPath</code>)
räknas här ur historiken och projektionen med <code>Kommunekonomi.Data.deathRatesPerYear</code>,
<code>calibratedMigrationRates</code> och <code>projectionResiduals</code>; sajten skickar bara uppgifterna. Intäktsbanan
(<code>revenuePath</code>) räknas på samma sätt av <code>Kommunekonomi.Data.sourcedRevenue</code>: SKR:s bana som den står,
regleringsposten enligt statens ram efter de beslutade åren, och förlängningen efter banans sista år. Rikets folkmängd står här som ett fast tal och skrivs
alltid över.</p></html>"));
end MotalaBrowserContinuous;
