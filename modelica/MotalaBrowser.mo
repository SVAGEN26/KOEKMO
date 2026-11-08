within ;
model MotalaBrowser "Omslag för webbläsaren: fast kapacitet på 30 år, alla scenariovärden fria parametrar"
  extends Motala.Annual(
    final horizon=30,
    p0={2894,4629,1575,23019,11022}*(43131/43139),
    deathRates={0.0004,0.0001,0.0002,0.0018,0.03853357878008014},
    residualMigration={-44.63234187162425,62.14678281833085,11.894277120084553,-238.86311941128406,37.964246056899356},
    tax0=2330, grants0=987, debt0=1040, cash0=81, assets0=2997, depreciation0=180,
    financialIncome=15, otherFinancialExpense=4, births0=334,
    payroll0=2288, pension0=190, otherOperatingExpense0=1297, operatingRevenue0=751,
    netCostRoundingAdjustment=-1, interestRate=21/940, taxRate=21.7, baseTaxRate=21.7, investment=413,
    revenuePopulation0={3008,4671,1592,23311,10923},
    nationalPopulation0=10587710,
    nationalPopulationPath={10605529,10617229,10590195,10595683,10607632,10633822,10660739,10688729,10717978,10747029,10776335,10806015,10836448,10867945,10900804,10935214,10970081,11005383,11041168,11077299,11113669,11150098,11186370,11222294,11257590,11292060,11325460,11357521,11388169,11417275},
    residualMigrationPath=zeros(30,5),
    wageGrowthPath=fill(0.03,30),
    priceGrowthPath=fill(0.02,30),
    pensionExpensePath=fill(190,30),
    pensionCashPaymentsPath=fill(190,30),
    referenceTax=fill(2330,30),
    referenceGrants=fill(987,30),
    referencePopulation=fill(43131,30),
    investmentPath=fill(413,30),
    interestRatePath=fill(21/1040,30),
    migrationDeltaPath=zeros(30),
    birthChangePath=zeros(30),
    serviceAdjustment=fill(0.5,3),
    serviceFixedShare=fill(0.25,3));
  annotation(Documentation(info="<html><p>Omslag för webbläsaren; innehåller inga egna ekvationer. OpenModelica kompilerar det en
gång i webbläsaren (wasm-jit), och varje scenario körs sedan om med -override. Alla värden som sajten skriver över har
egna bokstavliga värden här, så att -override når dem; i Motala.Annual räknas utgångsvärdena fram ur basårsposten, och dit
når inte -override. Trettio år är modellens kapacitet, inte prognosens längd: tiden är kalenderår, start 2025, och sajten
sätter sluttiden till 2025 plus antalet år.</p></html>"));
end MotalaBrowser;
