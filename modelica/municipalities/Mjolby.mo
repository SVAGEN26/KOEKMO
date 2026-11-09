package Mjolby "Mjölby: kommunens ekonomi år för år med biblioteket Kommunekonomi; belopp i mnkr, tid i kalenderår"
  package Data "Mjölbys basår ur SCB:s räkenskapssammandrag och befolkningsstatistik; genereras av scripts/prepare_municipality.py"
    import Kommunekonomi.Data.BaseYear;

    constant BaseYear mjolby2025 = BaseYear(
      year = 2025,
      cohorts = {{2299, 3187, 1025, 15853, 6212}, {2238, 3197, 1044, 15917, 6299}, {2261, 3170, 1046, 16009, 6352}},
      reportedPopulation = {28576, 28695, 28838},
      births = {291, 272}, deaths = 256,
      relativeTaxCapacity = {0.9152, 0.9114},
      tax = 1611.7, priorYearSettlement = -0.2, grants = 520.3,
      grantComponents = {360.4, 0.1, 75.9, 7.8, 74.5},
      payroll = 1486.6, pension = 119.8, otherOperatingExpense = 816.2, operatingRevenue = 494.7, netCostRoundingAdjustment = 0,
      depreciation = 134.8, financialIncome = 9.2, interestExpense = 29.5, otherFinancialExpense = 10.1,
      debt = 1110, openingDebt = 1045, cash = 273.9, assets = 2875.5, investment = 441.7, taxRate = 21.9,
      sectorShares = {0.4372, 0.2049, 0.3579}, educationShares = {0.2797, 0.5362, 0.1841},
      careCostPerInhabitant = {25528, 171066})
      "SCB:s räkenskapssammandrag och befolkningsstatistik 2025 (kommunen); Kolada för omsorgs- och sektorvikter";
    constant BaseYear mjolby2024 = BaseYear(
      year = 2024,
      cohorts = {{2352, 3123, 1030, 15800, 6166}, {2299, 3187, 1025, 15853, 6212}, {2238, 3197, 1044, 15917, 6299}},
      reportedPopulation = {28471, 28576, 28695},
      births = {272, 291}, deaths = 281,
      relativeTaxCapacity = {0.9227, 0.9152},
      tax = 1561.1, priorYearSettlement = -7.2, grants = 499.1,
      grantComponents = {332.9, -8.7, 87.3, 10.4, 71.3},
      payroll = 1390.4, pension = 163.6, otherOperatingExpense = 810.7, operatingRevenue = 468.6, netCostRoundingAdjustment = 0,
      depreciation = 120.4, financialIncome = 9.5, interestExpense = 20.7, otherFinancialExpense = 30.2,
      debt = 1045, openingDebt = 825, cash = 249.4, assets = 2573.8, investment = 380.5, taxRate = 21.9,
      sectorShares = {0.4454, 0.2059, 0.3487}, educationShares = {0.2815, 0.5364, 0.1821},
      careCostPerInhabitant = {24500, 170007})
      "SCB:s räkenskapssammandrag och befolkningsstatistik 2024 (kommunen); Kolada för omsorgs- och sektorvikter";
    constant BaseYear mjolby2023 = BaseYear(
      year = 2023,
      cohorts = {{2388, 3081, 984, 15767, 6049}, {2352, 3123, 1030, 15800, 6166}, {2299, 3187, 1025, 15853, 6212}},
      reportedPopulation = {28269, 28471, 28576},
      births = {318, 272}, deaths = 288,
      relativeTaxCapacity = {0.9153, 0.9227},
      tax = 1517.1, priorYearSettlement = 7.3, grants = 454.9,
      grantComponents = {329.7, -17.8, 66.4, 7.2, 66.7},
      payroll = 1343.4, pension = 144.9, otherOperatingExpense = 802, operatingRevenue = 452.2, netCostRoundingAdjustment = 0,
      depreciation = 114.5, financialIncome = 18.8, interestExpense = 10.5, otherFinancialExpense = 23.7,
      debt = 825, openingDebt = 705, cash = 125.4, assets = 2317.1, investment = 283.2, taxRate = 21.9,
      sectorShares = {0.4455, 0.2024, 0.3521}, educationShares = {0.2834, 0.5325, 0.1842},
      careCostPerInhabitant = {23706, 165806})
      "SCB:s räkenskapssammandrag och befolkningsstatistik 2023 (kommunen); Kolada för omsorgs- och sektorvikter";
    constant BaseYear mjolby2022 = BaseYear(
      year = 2022,
      cohorts = {{2350, 3081, 929, 15652, 5948}, {2388, 3081, 984, 15767, 6049}, {2352, 3123, 1030, 15800, 6166}},
      reportedPopulation = {27960, 28269, 28471},
      births = {312, 318}, deaths = 256,
      relativeTaxCapacity = {0.9179, 0.9153},
      tax = 1434.1, priorYearSettlement = 8.9, grants = 447.9,
      grantComponents = {308.6, -15.6, 77.9, 7.8, 63.5},
      payroll = 1261.7, pension = 89.8, otherOperatingExpense = 741.7, operatingRevenue = 445.9, netCostRoundingAdjustment = 0,
      depreciation = 110.6, financialIncome = 14.2, interestExpense = 4.4, otherFinancialExpense = 5.7,
      debt = 705, openingDebt = 717, cash = 85.9, assets = 2149.8, investment = 207.3, taxRate = 21.9,
      sectorShares = {0.4545, 0.1999, 0.3456}, educationShares = {0.2819, 0.5257, 0.1924},
      careCostPerInhabitant = {22685, 164425})
      "SCB:s räkenskapssammandrag och befolkningsstatistik 2022 (kommunen); Kolada för omsorgs- och sektorvikter";
    constant BaseYear mjolby2021 = BaseYear(
      year = 2021,
      cohorts = {{2362, 3006, 904, 15561, 5925}, {2350, 3081, 929, 15652, 5948}, {2388, 3081, 984, 15767, 6049}},
      reportedPopulation = {27758, 27960, 28269},
      births = {295, 312}, deaths = 256,
      relativeTaxCapacity = {0.9185, 0.9179},
      tax = 1347.2, priorYearSettlement = 4.6, grants = 435,
      grantComponents = {285.3, -19, 82.9, 9.3, 61.4},
      payroll = 1193.4, pension = 102.8, otherOperatingExpense = 681.1, operatingRevenue = 411.9, netCostRoundingAdjustment = 0,
      depreciation = 103.8, financialIncome = 10.2, interestExpense = 3.2, otherFinancialExpense = 3.5,
      debt = 717, openingDebt = 640, cash = 79, assets = 2054.1, investment = 197.6, taxRate = 21.9,
      sectorShares = {0.4614, 0.2005, 0.3381}, educationShares = {0.2867, 0.5225, 0.1908},
      careCostPerInhabitant = {21877, 165718})
      "SCB:s räkenskapssammandrag och befolkningsstatistik 2021 (kommunen); Kolada för omsorgs- och sektorvikter";
    constant BaseYear mjolby2020 = BaseYear(
      year = 2020,
      cohorts = {{2290, 2984, 897, 15301, 5901}, {2362, 3006, 904, 15561, 5925}, {2350, 3081, 929, 15652, 5948}},
      reportedPopulation = {27373, 27758, 27960},
      births = {302, 295}, deaths = 273,
      relativeTaxCapacity = {0.923, 0.9185},
      tax = 1271.4, priorYearSettlement = -6.6, grants = 424.2,
      grantComponents = {281.5, -5.4, 28.4, 5.2, 57.7},
      payroll = 1170.1, pension = 98.4, otherOperatingExpense = 660.7, operatingRevenue = 395.2, netCostRoundingAdjustment = 0,
      depreciation = 91.8, financialIncome = 11, interestExpense = 3.5, otherFinancialExpense = 4.7,
      debt = 640, openingDebt = 630, cash = 66.7, assets = 1967.6, investment = 273.5, taxRate = 21.9,
      sectorShares = {0.4683, 0.2047, 0.327}, educationShares = {0.2874, 0.5296, 0.1831},
      careCostPerInhabitant = {21976, 164396})
      "SCB:s räkenskapssammandrag och befolkningsstatistik 2020 (kommunen); Kolada för omsorgs- och sektorvikter";

    constant Real olderShares[3] = {0.682305, 0.268419, 0.049276} "Andel av 65+ som är 65-79, 80-89 och 90+ vid slutet av 2025 (SCB)";
    annotation(Documentation(info = "<html><p>Källa: SCB, Statistikdatabasen (CC BY 4.0): räkenskapssammandraget (TAB6777, TAB6779,
TAB6782, TAB4202, TAB5179), befolkningen per ettårsålder och befolkningsförändringar; Kolada för omsorgskostnad per invånare
och nettokostnad per verksamhet. Arkiv data/downloads/20261109T162208Z. Värdena avser kommunen, inte koncernen. Anläggningstillgångarna innehåller
pågående arbeten, som SCB inte särredovisar. Definitionerna står i scripts/prepare_municipality.py.</p></html>"));
  end Data;

  model Annual "Mjölbys ekonomi år för år från bokslutet 2025"
    extends Kommunekonomi.Annual(base = Data.mjolby2025, olderShares = Data.olderShares);
    annotation(experiment(StartTime = 2025, StopTime = 2033, Interval = 1),
      Documentation(info = "<html><p><b>Tid: start 2025, slut 2033.</b> Med standardantagandena (illustrativ tillväxt).
Starta från ett annat år med <code>Annual(base = Data.mjolby2024)</code>.</p></html>"));
  end Annual;

  package Examples "Färdiga modeller att simulera"
    model Hindcast2025 "Starta i bokslutet 2024 och räkna fram 2025; jämför med utfallet i Data.mjolby2025"
      extends Annual(base = Data.mjolby2024, horizon = 1);
      annotation(experiment(StartTime = 2024, StopTime = 2025, Interval = 1));
    end Hindcast2025;
  end Examples;
  annotation(uses(Kommunekonomi(version = "0.1.0")), Documentation(info = "<html><p>Mjölby (kommunkod 0586) med biblioteket
<a href=\"modelica://Kommunekonomi\">Kommunekonomi</a>. Data från SCB och Kolada, genererade av scripts/prepare_municipality.py.
Detta är en forskningsmodell, inte kommunens prognos.</p></html>"));
end Mjolby;
