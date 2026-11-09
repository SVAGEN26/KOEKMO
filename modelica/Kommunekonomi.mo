package Kommunekonomi "Kommunekonomi: en svensk kommuns ekonomi år för år; belopp i mnkr, tid i kalenderår"
  package Data "Posttyper för bokslut, budget och befolkning, rikets data från SCB och funktioner för kalibrering"
    record BaseYear "Utfall vid basårets slut; mnkr och personer"
      Integer year "Basår";
      Real cohorts[3, 5] "Redovisade invånare 0-6, 7-15, 16-18, 19-64 och 65+ vid slutet av de två föregående åren och basåret";
      Real reportedPopulation[3] "Redovisad folkmängd samma tre år";
      Real births[2] "Födda föregående år och basåret";
      Real deaths "Döda under basåret";
      Real tax "Skatteintäkter, mnkr";
      Real grants "Generella statsbidrag och utjämning, mnkr";
      Real grantComponents[5] "Därav inkomstutjämning, kostnadsutjämning, regleringsbidrag (avgift negativ), LSS-utjämning och fastighetsavgift, mnkr; resten är övriga generella bidrag";
      Real payroll "Lönekostnader exklusive pensioner, mnkr";
      Real pension "Pensionskostnad, mnkr";
      Real otherOperatingExpense "Verksamhetens bruttokostnader minus löner och pensioner, mnkr";
      Real operatingRevenue "Verksamhetens intäkter (avgifter, försäljning, riktade bidrag), mnkr";
      Real netCostRoundingAdjustment "Avrundning som stämmer av delposterna mot redovisad nettokostnad, mnkr";
      Real depreciation "Avskrivningar, mnkr";
      Real financialIncome "Finansiella intäkter, mnkr";
      Real interestExpense "Räntekostnader, mnkr";
      Real otherFinancialExpense "Finansiella kostnader utöver räntor, mnkr";
      Real debt "Låneskuld till banker och kreditinstitut vid årets slut, mnkr";
      Real openingDebt "Låneskuld vid årets början (föregående års slut), mnkr";
      Real cash "Kassa och bank, mnkr";
      Real assets "Byggnader, anläggningar, maskiner och inventarier exklusive pågående investeringar, mnkr";
      Real investment "Investeringar, mnkr";
      Real taxRate "Kommunal skattesats, procent";
      Real careCostPerInhabitant[2] "Äldreomsorgens kostnad per invånare 65-79 och 80+, kr; Kolada, treårsmedel (data/care-weights.json)";
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {40, 95, 140}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}), Rectangle(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, extent = {{-100, 50}, {100, 100}}), Text(textColor = {255, 255, 255}, extent = {{-92, 55}, {92, 95}}, textString = "Basår"), Line(points = {{-100, 0}, {100, 0}}, color = {40, 95, 140}), Line(points = {{-100, -50}, {100, -50}}, color = {40, 95, 140}), Line(points = {{0, 50}, {0, -100}}, color = {40, 95, 140})}));
    end BaseYear;

    record Budget "Kommunens budget: tre år, belopp i mnkr (kostnader som positiva tal)"
      Integer year "Budgetår; planen gäller detta år och de två följande";
      Real tax[3] "Skatteintäkter";
      Real grants[3] "Generella statsbidrag och utjämning";
      Real netCost[3] "Verksamhetens nettokostnad exklusive avskrivningar";
      Real depreciation[3] "Avskrivningar";
      Real financialIncome[3] "Finansiella intäkter";
      Real financialCost[3] "Finansiella kostnader";
      Real result[3] "Årets resultat";
      Real investment[3] "Investeringsram";
      Real operatingCash[3] "Kassaflöde från den löpande verksamheten";
      Real newLoans[3] "Nya lån";
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {40, 95, 140}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}), Rectangle(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, extent = {{-100, 50}, {100, 100}}), Text(textColor = {255, 255, 255}, extent = {{-92, 55}, {92, 95}}, textString = "Budget"), Line(points = {{-100, 0}, {100, 0}}, color = {40, 95, 140}), Line(points = {{-100, -50}, {100, -50}}, color = {40, 95, 140}), Line(points = {{0, 50}, {0, -100}}, color = {40, 95, 140})}));
    end Budget;

    function reconcile "Skala redovisade åldersgrupper till redovisad folkmängd"
      input Real cohorts[5] "Redovisade invånare per åldersgrupp";
      input Real total "Redovisad folkmängd";
      output Real reconciled[5] "Invånare per åldersgrupp, summerade till folkmängden";
    algorithm
      reconciled := cohorts*total/sum(cohorts);
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(lineColor = {90, 110, 130}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}), Text(textColor = {90, 110, 130}, extent = {{-92, -50}, {92, 50}}, textString = "f(x)")}));
    end reconcile;

    function mortality "Illustrativa dödsrisker under 65 år; risken för 65+ ger observerat antal döda"
      input Real p[5] "Invånare per åldersgrupp";
      input Real deaths "Döda under året";
      output Real rates[5] "Dödsrisk per åldersgrupp och år";
    algorithm
      rates := {0.0004, 0.0001, 0.0002, 0.0018, 0};
      rates[5] := (deaths - sum(p[1:4] .* rates[1:4]))/p[5];
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(lineColor = {90, 110, 130}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}), Text(textColor = {90, 110, 130}, extent = {{-92, -50}, {92, 50}}, textString = "f(x)")}));
    end mortality;

    function naturalStep "Ett år av överlevnad, åldrande och födslar, utan flyttningar"
      input Real p[5] "Invånare per åldersgrupp vid årets början";
      input Real births "Födda under året";
      input Real deathRates[5] "Dödsrisk per åldersgrupp";
      output Real next[5] "Invånare per åldersgrupp vid årets slut, utan flyttningar";
    protected
      Real survivors[5] "Överlevande";
      Real ageOut[5] "Åldras upp till nästa grupp";
    algorithm
      survivors := p .* (ones(5) - deathRates);
      ageOut := {survivors[1]/7, survivors[2]/9, survivors[3]/3, survivors[4]/46, 0};
      next := {survivors[i] - ageOut[i] + (if i == 1 then births else ageOut[i - 1]) for i in 1:5};
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(lineColor = {90, 110, 130}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}), Text(textColor = {90, 110, 130}, extent = {{-92, -50}, {92, 50}}, textString = "f(x)")}));
    end naturalStep;

    function calibratedMigration "Genomsnittligt restflöde per åldersgrupp under de två senaste åren"
      input Real cohorts[3, 5] "Redovisade invånare per åldersgrupp, tre år i följd";
      input Real totals[3] "Redovisad folkmängd samma tre år";
      input Real births[2] "Födda de två senare åren";
      input Real deathRates[5] "Dödsrisk per åldersgrupp";
      output Real residual[5] "Genomsnittligt restflöde per åldersgrupp och år, personer";
    algorithm
      residual := zeros(5);
      for k in 1:2 loop
        residual := residual + (reconcile(cohorts[k + 1, :], totals[k + 1])
          - naturalStep(reconcile(cohorts[k, :], totals[k]), births[k], deathRates))/2;
      end for;
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(lineColor = {90, 110, 130}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}), Text(textColor = {90, 110, 130}, extent = {{-92, -50}, {92, 50}}, textString = "f(x)")}));
    end calibratedMigration;

    package SCB "Rikets demografiska data från SCB och posttypen för en kommuns ettårsdata. Genereras av scripts/write_demography_modelica.py; redigera inte för hand"
      record DemographyYear "En kommun vid ett basårs slut, ettårsåldrar 0-100+ (index 1-101) per kön (1 män, 2 kvinnor)"
        Integer year "Basår";
        Real population[2, 101] "Befolkning vid årets slut";
        Real deathRisk[2, 101] "Rikets dödsrisk vid basåret: fem livslängdstabeller flyttade längs trenden och medelvärdesbildade, andel";
        Real mortalityImprovement[2, 101] "Årlig minskning av dödsrisken, rikets trend de tio åren fram till basåret";
        Real mortalityRatio[2] "Kommunens dödlighet i förhållande till rikets livslängdstabell, de fem åren fram till basåret";
        Real residualMigration[2, 101] "Genomsnittlig årlig förändring som inte förklaras av döda, åldrande och födda, de tre åren fram till basåret";
        Real shareBoys "Andel pojkar bland de födda, de tio åren fram till basåret";
        Real totalFertility "Kommunens summerade fruktsamhet basåret";
        Real totalFertilityMean5 "Kommunens genomsnittliga summerade fruktsamhet de fem åren fram till basåret";
        Real births "Födda under basåret";
        Real deaths "Döda under basåret";
        annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {40, 95, 140}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}), Rectangle(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, extent = {{-100, 50}, {100, 100}}), Text(textColor = {255, 255, 255}, extent = {{-92, 55}, {92, 95}}, textString = "SCB-år"), Line(points = {{-100, 0}, {100, 0}}, color = {40, 95, 140}), Line(points = {{-100, -50}, {100, -50}}, color = {40, 95, 140}), Line(points = {{0, 50}, {0, -100}}, color = {40, 95, 140})}));
      end DemographyYear;

      constant Real fertilityProfile[101] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0.000139247, 0.00020887, 0.000556987, 0.00125322, 0.0029938, 0.00591798, 0.00995614, 0.0147601, 0.0190768,
          0.0232542, 0.0307039, 0.0409385, 0.0511732, 0.06099, 0.0696233, 0.0766553, 0.0808327, 0.0811808, 0.0779085, 0.0718513, 0.0635661,
          0.0537492, 0.0433057, 0.0337673, 0.025691, 0.0184502, 0.0132284, 0.0104435, 0.0074497, 0.00452552, 0.00257606, 0.00146209, 0.000765857,
          0.000556987, 0.000487363, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0}
        "Andel av en kvinnas barn som föds vid varje ålder, SCB:s framskrivning 2026; summerar till 1";
      constant Integer projectionFirstYear = 2026 "Första året i SCB:s framskrivning";
      constant Real projectedTotalFertility[30] = {1.4363, 1.4414, 1.4489, 1.4811, 1.5138, 1.5478, 1.5829, 1.6175, 1.6229, 1.629,
          1.6317, 1.6342, 1.6366, 1.6399, 1.6431, 1.6428, 1.6432, 1.6442, 1.6453, 1.6471,
          1.6495, 1.6522, 1.6556, 1.6594, 1.6626, 1.667, 1.6715, 1.6763, 1.6806, 1.6854}
        "Rikets summerade fruktsamhet enligt SCB:s antagande, 2026-2055";
      constant Real mortalityImprovement[2, 101] = {{0.009534, 0.01171, 0.008234, 0, 0, 0.01484, 0, 0.01713, 0, 0, 0.02026, 0, 0.01484, 0.01171, 0.008894, 0.01391, 0.01112,
          0.01362, 0.01484, 0.01236, 0.01141, 0.01011, 0.009668, 0.009462, 0.009265, 0.006736, 0.006603, 0.006474, 0.00839, 0.008084, 0.008084, 0.009839, 0.009668, 0.01131,
          0.01112, 0.01076, 0.01413, 0.01189, 0.01309, 0.01104, 0.01059, 0.01004, 0.01213, 0.01264, 0.01436, 0.01558, 0.01568, 0.01653, 0.01713, 0.01738, 0.01875,
          0.01913, 0.01902, 0.01925, 0.01881, 0.01943, 0.01959, 0.01979, 0.01983, 0.0201, 0.02006, 0.02017, 0.02045, 0.02047, 0.02026, 0.02053, 0.02018, 0.02037,
          0.02036, 0.02063, 0.02071, 0.02069, 0.02067, 0.02065, 0.02045, 0.02061, 0.02041, 0.0203, 0.02004, 0.01963, 0.01912, 0.01854, 0.01788, 0.01719, 0.01635,
          0.01548, 0.01442, 0.01342, 0.01242, 0.01131, 0.01016, 0.009025, 0.007987, 0.007027, 0.006138, 0.005218, 0.004068, 0.00295, 0.002043, 0.000988, -0.0005757},
         {0.009762, 0.005421, 0.01059, 0.01484, 0.01713, 0.01713, 0, 0.02026, 0, 0, 0, 0.02026, 0, 0, 0, 0.01171, 0.009668,
          0.008234, 0.007171, 0.01236, 0.01171, 0.01059, 0.01059, 0.01059, 0.01059, 0.005169, 0.005169, 0.01011, 0.01011, 0.004729, 0.009265, 0.008551, 0.01213, 0.01131,
          0.01059, 0.009957, 0.01236, 0.01171, 0.01112, 0.01309, 0.009883, 0.01171, 0.01101, 0.01236, 0.01331, 0.01391, 0.0159, 0.016, 0.01713, 0.01786, 0.01747,
          0.01881, 0.01894, 0.01863, 0.01905, 0.0194, 0.01861, 0.01897, 0.01963, 0.0193, 0.01896, 0.01815, 0.0176, 0.01721, 0.01636, 0.01651, 0.01569, 0.01531,
          0.01503, 0.01484, 0.01465, 0.01447, 0.01461, 0.01473, 0.01438, 0.01462, 0.01438, 0.01436, 0.01424, 0.01407, 0.01398, 0.01367, 0.01349, 0.0133, 0.01297,
          0.01268, 0.01212, 0.01164, 0.01102, 0.01031, 0.00961, 0.008822, 0.008016, 0.007261, 0.006533, 0.005831, 0.004935, 0.004223, 0.003529, 0.002624, 0.0002209}}
        "Årlig minskning av dödsrisken per ålder och kön i SCB:s framskrivning 2026-2035; ett alternativ till basårets historiska trend";

      function groups "Ettårsåldrar summerade till 0-6, 7-15, 16-18, 19-64 och 65+, båda könen"
        input Real population[2, 101] "Befolkning per ettårsålder och kön";
        output Real cohorts[5] "Invånare per åldersgrupp";
      algorithm
        cohorts := {sum(population[:, 1:7]), sum(population[:, 8:16]), sum(population[:, 17:19]), sum(population[:, 20:65]), sum(population[:, 66:101])};
      end groups;

      constant Integer nationalFirstYear = 2010 "Första året i tabellen över rikets folkmängd";
      constant Real nationalPopulation[61] = {9415570, 9482855, 9555893, 9644864, 9747355, 9851017, 9995153, 10120242,
          10230185, 10327589, 10379295, 10452326, 10521556, 10551707, 10587710, 10605529,
          10617229, 10590195, 10595683, 10607632, 10633822, 10660739, 10688729, 10717978,
          10747029, 10776335, 10806015, 10836448, 10867945, 10900804, 10935214, 10970081,
          11005383, 11041168, 11077299, 11113669, 11150098, 11186370, 11222294, 11257590,
          11292060, 11325460, 11357521, 11388169, 11417275, 11444857, 11470900, 11495591,
          11519087, 11541712, 11563698, 11585398, 11607075, 11629002, 11651376, 11674358,
          11698073, 11722553, 11747835, 11773818, 11800473}
        "Rikets folkmängd 31 december 2010-2070: utfall till 2025, sedan SCB:s framskrivning (data/downloads/20261108T145741Z)";

      function nationalPopulationAt "Rikets folkmängd 31 december ett visst år"
        input Integer year "Kalenderår";
        output Real population "Folkmängd";
      algorithm
        assert(year >= nationalFirstYear and year < nationalFirstYear + size(nationalPopulation, 1), "Data.SCB.nationalPopulation saknar år " + String(year));
        population := nationalPopulation[year - nationalFirstYear + 1];
      end nationalPopulationAt;

      function olderShares "Andelar av 65+ som är 65-79, 80-89 och 90+"
        input Real population[2, 101] "Befolkning per ettårsålder och kön";
        output Real shares[3] "Andel av 65+ som är 65-79, 80-89 och 90+";
      algorithm
        shares := {sum(population[:, 66:80]), sum(population[:, 81:90]), sum(population[:, 91:101])}/sum(population[:, 66:101]);
        annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(lineColor = {90, 110, 130}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}), Text(textColor = {90, 110, 130}, extent = {{-92, -50}, {92, 50}}, textString = "f(x)")}));
      end olderShares;
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Text(textColor = {35, 50, 65}, extent = {{-92, -30}, {92, 40}}, textString = "SCB"), Text(textColor = {90, 110, 130}, extent = {{-92, -80}, {92, -35}}, textString = "demografi")}), Documentation(info = "<html><p>Källa: SCB, Statistikdatabasen (CC BY 4.0). Tabeller: BefProgDodstalNb, BefProgFruktTotNb, BefProgOsiktRegN, BefolkningCKM, BefolkningNy, DodaHandelseK, DodaHandelseKCKM, FoddaK, FoddaKCKM, FruktsamhetSum, LivslangdEttariga.
  Arkiv data/downloads/20261108T124756Z; bearbetat av scripts/prepare_demography.py till data/demography-inputs.json.</p>
  <p>Rikets folkmängd, fruktsamhet och dödlighet är desamma för alla kommuner. En kommuns paket ärver det här paketet och
  lägger till sina basår som <code>DemographyYear</code>. SCB:s framskrivna dödlighet och fruktsamhet kommer från
  framskrivningen 2026.</p></html>"));
    end SCB;
    annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Text(textColor = {35, 50, 65}, extent = {{-92, -30}, {92, 40}}, textString = "Data"), Text(textColor = {90, 110, 130}, extent = {{-92, -80}, {92, -35}}, textString = "basår")}),
      Documentation(info = "<html><p>Posttyper som en kommuns paket fyller med sina utfall: <code>BaseYear</code> (bokslut och
befolkning vid basårets slut), <code>Budget</code> och <code>SCB.DemographyYear</code> (ettårsåldrar). Paketet
<code>SCB</code> har också rikets folkmängd, fruktsamhet och dödlighet, som är desamma för alla kommuner.</p></html>"));
  end Data;

  partial model Assumptions "Gemensamma scenarioparametrar: basår, antaganden och årsvisa banor"
    parameter Integer horizon(min = 1) = 8 "Antal årssteg som räknas fram; tiden mäts i år från basåret";
    parameter Data.BaseYear base "Basår med utfall från bokslutet; kommunens paket ger ett värde, till exempel Motala.Data.motala2025";
    // Befolkning och demografi
    parameter Real p0[5] = Data.reconcile(base.cohorts[3, :], base.reportedPopulation[3]) "Invånare 0-6, 7-15, 16-18, 19-64 och 65+ vid basårets slut, avstämda mot redovisad folkmängd";
    parameter Real revenuePopulation0[5] = Data.reconcile(base.cohorts[2, :], base.reportedPopulation[2]) "Invånare per åldersgrupp vid slutet av året före basåret: den folkmängd basårets skatt och bidrag bygger på";
    parameter Real deathRates[5] = Data.mortality(p0, base.deaths) "Dödsrisk per åldersgrupp och år; 65+ ger basårets observerade antal döda";
    parameter Real residualMigration[5] = Data.calibratedMigration(base.cohorts, base.reportedPopulation, base.births, deathRates) "Kalibrerat restflöde per åldersgrupp, personer per år (flyttningar och statistiska justeringar)";
    parameter Real olderShares[3] "Fast uppdelning av 65+ i 65-79, 80-89 och 90+ för femgruppsdemografin; kommunens paket ger den ur SCB-data";
    parameter Real migrationWeights[5] = {0.15, 0.12, 0.03, 0.65, 0.05} "Hur ett förändrat flyttnetto fördelas på åldersgrupperna; summerar till 1";
    parameter Real births0 = base.births[2] "Födda under basåret";
    parameter Real migrationDelta = 0 "Förändrat årligt flyttnetto jämfört med kalibreringen, personer";
    parameter Real birthChange = 0 "Relativ förändring av antalet födda, andel (0,1 = tio procent fler)";
    // Verksamhet
    parameter Real educationWeights[3] = {0.25, 0.60, 0.15} "Vikter för 0-6, 7-15 och 16-18 år i utbildningsbehovet; summerar till 1";
    parameter Real sectorCosts[3] = {1250, 600, 1173} "Kostnadsvikter för utbildning, äldreomsorg och övrig verksamhet, mnkr (illustrativa)";
    parameter Real adjustment = 0.5 "Andel av glappet mellan behov och kapacitet som stängs varje år (0 = låst, 1 = direkt)";
    parameter Real fixedShare = 0.25 "Andel av kapaciteten som inte följer behovet";
    parameter Real serviceAdjustment[3] = fill(adjustment, 3) "Årlig kapacitetsanpassning för utbildning, äldreomsorg och övrigt";
    parameter Real serviceFixedShare[3] = fill(fixedShare, 3) "Fast andel av kapaciteten för utbildning, äldreomsorg och övrigt";
    parameter Real oldestRelativeCare = 1 "Omsorgskostnad per invånare 90+ jämfört med 80-89; Kolada saknar uppdelning, därför 1 tills data finns";
    parameter Real careWeights[3] = {base.careCostPerInhabitant[1], base.careCostPerInhabitant[2], base.careCostPerInhabitant[2]*oldestRelativeCare}
      "Äldreomsorgens kostnad per invånare 65-79, 80-89 och 90+, kr (Kolada)";
    // Drift: utfall i basåret
    parameter Real payroll0 = base.payroll "Lönekostnader exklusive pensioner i basåret, mnkr";
    parameter Real pension0 = base.pension "Pensionskostnad i basåret, mnkr";
    parameter Real otherOperatingExpense0 = base.otherOperatingExpense "Övriga verksamhetskostnader i basåret, mnkr";
    parameter Real operatingRevenue0 = base.operatingRevenue "Verksamhetens intäkter i basåret (avgifter, försäljning, riktade bidrag), mnkr";
    parameter Real netCostRoundingAdjustment = base.netCostRoundingAdjustment "Avrundningsjustering som stämmer av delposterna mot redovisad nettokostnad, mnkr";
    // Intäkter, kapital och finansiering: utfall i basåret
    parameter Real tax0 = base.tax "Skatteintäkter i basåret, mnkr";
    parameter Real grants0 = base.grants "Generella statsbidrag och utjämning i basåret, mnkr";
    parameter Real debt0 = base.debt "Låneskuld till banker och kreditinstitut vid basårets slut, mnkr";
    parameter Real cash0 = base.cash "Kassa och bank vid basårets slut, mnkr";
    parameter Real assets0 = base.assets "Byggnader, anläggningar, maskiner och inventarier vid basårets slut, exklusive pågående investeringar, mnkr";
    parameter Real depreciation0 = base.depreciation "Avskrivningar i basåret, mnkr";
    parameter Real financialIncome = base.financialIncome "Finansiella intäkter per år, mnkr";
    parameter Real otherFinancialExpense = base.otherFinancialExpense "Finansiella kostnader utöver räntor per år, mnkr";
    // Tillväxt och priser
    parameter Real taxGrowth = 0.035 "Rikets skatteunderlag, årlig tillväxt, andel; inklusive rikets befolkningsökning, så kommunens skatt växer långsammare när kommunen krymper och riket växer";
    parameter Real grantGrowth = 0.02 "Generella bidrag i riket, årlig tillväxt, andel; kommunens del följer folkmängden i förhållande till rikets";
    parameter Real wageGrowth = 0.03 "Årlig löneökning, andel";
    parameter Real priceGrowth = 0.02 "Årlig prisökning för övriga kostnader, andel";
    parameter Real productivityGrowth = 0 "Årlig produktivitetsökning, andel; minskar lönekostnaden för samma volym";
    parameter Real pensionGrowth = 0.02 "Pensionskostnadens årliga ökning, andel";
    parameter Real operatingRevenueGrowth = 0.02 "Verksamhetsintäkternas årliga ökning, andel";
    parameter Real taxRate = base.taxRate "Kommunal skattesats i scenariot, procent";
    parameter Real baseTaxRate = base.taxRate "Kommunal skattesats i basåret, procent";
    parameter Real equalisationOffset = 0.95 "Andel av en lokal avvikelse i skatteunderlaget som utjämningen tar tillbaka (förenklad)";
    parameter Real populationRevenueElasticity = 1 "Hur starkt skatt och bidrag följer kommunens folkmängd i förhållande till rikets (1 = proportionellt: en invånare färre ger cirka 77 000 kr mindre per år, 2025 års nivå)";
    parameter Real interestRate = base.interestExpense/base.openingDebt "Genomsnittlig låneränta på ingående skuld, andel; basårets räntekostnad delad med skulden vid basårets början";
    parameter Real investment = base.investment "Årliga investeringar, mnkr";
    // Årsvisa banor; första värdet gäller år 1
    parameter Real residualMigrationPath[horizon, 5] = {residualMigration for i in 1:horizon} "Restflöde per år och åldersgrupp, personer; från en extern befolkningsbana eller kalibreringen";
    parameter Real wageGrowthPath[horizon] = fill(wageGrowth, horizon) "Löneökning per år, andel";
    parameter Real priceGrowthPath[horizon] = fill(priceGrowth, horizon) "Prisökning per år, andel";
    parameter Real pensionExpensePath[horizon] = {pension0*(1 + pensionGrowth)^i for i in 1:horizon} "Pensionskostnad per år, mnkr";
    parameter Real pensionCashPaymentsPath[horizon] = pensionExpensePath "Pensionsutbetalningar per år, mnkr; illustrativa tills en egen källa finns";
    parameter Real referenceTax[horizon] = {tax0*(1 + taxGrowth)^i for i in 1:horizon} "Referensbana för skatteintäkter, mnkr; växer i rikets takt och skalas i Intäkter med kommunens folkmängd i förhållande till rikets (en importerad SKR-bana är redan kommunens egen)";
    parameter Real referenceGrants[horizon] = {grants0*(1 + grantGrowth)^i for i in 1:horizon} "Referensbana för generella bidrag, mnkr; växer i rikets takt och skalas i Intäkter med kommunens folkmängd i förhållande till rikets (en importerad SKR-bana är redan kommunens egen)";
    parameter Real referencePopulation[horizon] = fill(sum(p0), horizon) "Folkmängd som referensbanan bygger på, personer";
    parameter Real nationalPopulation0 = Data.SCB.nationalPopulationAt(base.year - 1) "Rikets folkmängd vid slutet av året före basåret, personer (SCB)";
    parameter Real nationalPopulationPath[horizon] = {Data.SCB.nationalPopulationAt(base.year + i - 1) for i in 1:horizon}
      "Rikets folkmängd vid slutet av året före varje prognosår, personer (SCB: utfall, sedan framskrivning)";
    parameter Boolean importedRevenue = false "Sant när referensbanan är importerad från SKR";
    // Generella bidrag per del (används med grantsByComponent)
    parameter Boolean grantsByComponent = false "Bidragen räknas per del: inkomstutjämning, kostnads- och LSS-utjämning, regleringsbidrag, fastighetsavgift och övriga";
    parameter Real grantComponents0[5] = base.grantComponents "Basårets inkomstutjämning, kostnadsutjämning, regleringsbidrag, LSS-utjämning och fastighetsavgift, mnkr";
    final parameter Real grantPerCapita0[4] = grantComponents0[1:4]*1e6/sum(revenuePopulation0) "Basårets inkomst-, kostnads-, reglerings- och LSS-del, kr per invånare";
    parameter Real incomeEqualisationPerCapitaPath[horizon] = {grantPerCapita0[1]*(referenceTax[i]/tax0)/(nationalPopulationPath[i]/nationalPopulation0) for i in 1:horizon}
      "Inkomstutjämning per år, kr per invånare; följer rikets skatteunderlag per invånare (referensbanans tillväxt delad med rikets folkmängd)";
    parameter Real costEqualisationPerCapitaPath[horizon] = fill(grantPerCapita0[2], horizon) "Kostnadsutjämning per år, kr per invånare; basårets belopp om inget annat anges";
    parameter Real regulationPerCapitaPath[horizon] = fill(grantPerCapita0[3], horizon)
      "Regleringsbidrag per år, kr per invånare; basårets belopp om inget annat anges. Samma för alla kommuner; staten beslutar det i budgeten";
    parameter Real lssEqualisationPerCapitaPath[horizon] = fill(grantPerCapita0[4], horizon) "LSS-utjämning per år, kr per invånare; basårets belopp om inget annat anges";
    parameter Real propertyFeeGrowth = 0.035 "Fastighetsavgiftens årliga ökning, andel; taket följer inkomstbasbeloppet (3,8 procent om året 2020-2026)";
    parameter Real propertyFeePath[horizon] = {grantComponents0[5]*(1 + propertyFeeGrowth)^i for i in 1:horizon} "Kommunal fastighetsavgift per år, mnkr";
    parameter Real otherGeneralGrantsPath[horizon] = zeros(horizon) "Övriga generella bidrag per år, mnkr; noll om inget annat anges, eftersom de oftast är tillfälliga";
    parameter Boolean revenueFromReference = false "Skatt och bidrag följer referensbanan exakt (till exempel budgetens belopp)";
    parameter Real investmentPath[horizon] = fill(investment, horizon) "Investeringar per år, mnkr; tas i bruk samma år";
    parameter Real interestRatePath[horizon] = fill(interestRate, horizon) "Låneränta på ingående skuld per år, andel";
    parameter Real migrationDeltaPath[horizon] = fill(migrationDelta, horizon) "Förändrat flyttnetto per år, personer";
    parameter Real birthChangePath[horizon] = fill(birthChange, horizon) "Relativ förändring av födda per år, andel";
    final parameter Real life = assets0/depreciation0 "Sammanvägd avskrivningstid, år";
  initial equation
    assert(horizon >= 1, "horizon måste vara minst ett år");
    assert(min(p0) > 0, "p0: varje åldersgrupp måste ha invånare");
    assert(min(deathRates) >= 0 and max(deathRates) <= 1, "deathRates måste ligga mellan 0 och 1");
    assert(min(migrationWeights) >= 0 and abs(sum(migrationWeights) - 1) < 1e-10, "migrationWeights måste vara icke-negativa och summera till 1");
    assert(min(educationWeights) >= 0 and abs(sum(educationWeights) - 1) < 1e-10, "educationWeights måste vara icke-negativa och summera till 1");
    assert(min(sectorCosts) >= 0 and sum(sectorCosts) > 0, "sectorCosts måste ge positiva kostnadsvikter");
    assert(min(serviceAdjustment) >= 0 and max(serviceAdjustment) <= 1, "serviceAdjustment måste ligga mellan 0 och 1");
    assert(min(serviceFixedShare) >= 0 and max(serviceFixedShare) <= 1, "serviceFixedShare måste ligga mellan 0 och 1");
    assert(assets0 > 0 and depreciation0 > 0 and depreciation0 <= assets0, "assets0 och depreciation0 måste ge en avskrivningstid på minst ett år");
    assert(debt0 >= 0 and cash0 >= 0, "debt0 och cash0 får inte vara negativa");
    assert(baseTaxRate > 0 and taxRate >= 0, "baseTaxRate måste vara positiv och taxRate icke-negativ");
    assert(min(referencePopulation) > 0, "referencePopulation måste vara positiv varje år");
    assert(min(investmentPath) >= 0, "investmentPath får inte vara negativ; försäljningar av tillgångar modelleras inte");
    assert(births0 >= 0 and min(birthChangePath) >= -1, "births0 och birthChangePath får inte ge negativt antal födda");
    assert(min(pensionExpensePath) >= 0 and min(pensionCashPaymentsPath) >= 0, "pensionExpensePath och pensionCashPaymentsPath får inte vara negativa");
    assert(taxGrowth > -1 and grantGrowth > -1 and wageGrowth > -1 and priceGrowth > -1 and productivityGrowth > -1 and pensionGrowth > -1 and operatingRevenueGrowth > -1, "Årliga tillväxttakter måste vara större än -1 (andelar, inte procent)");
// Årsbanorna ersätter skalärerna ovan och behöver samma gränser.
// Utan dem nollställer wageGrowthPath[k] = -1 lönerna och en negativ ränta bokförs som intäkt.
    assert(min(wageGrowthPath) > -1 and min(priceGrowthPath) > -1, "wageGrowthPath och priceGrowthPath måste vara större än -1 varje år (andelar, inte procent)");
    assert(min(interestRatePath) >= 0 and max(interestRatePath) <= 0.3, "interestRatePath måste ligga mellan 0 och 0,3 varje år (andelar, inte procent)");
    assert(min(referenceTax) > 0 and min(referenceGrants) > 0, "referenceTax och referenceGrants måste vara positiva varje år");
    assert(equalisationOffset >= 0 and equalisationOffset <= 1, "equalisationOffset måste ligga mellan 0 och 1");
    assert(payroll0 >= 0 and pension0 >= 0 and otherOperatingExpense0 >= 0 and operatingRevenue0 >= 0, "Driftens utgångsvärden får inte vara negativa");
    annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, pattern = LinePattern.Dash, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 8), Text(textColor = {35, 50, 65}, extent = {{-92, 0}, {92, 60}}, textString = "Antaganden"), Text(textColor = {90, 110, 130}, extent = {{-92, -70}, {92, -10}}, textString = "basklass")}), Documentation(info = "<html><p>Alla parametrar som ett scenario kan ändra. Utgångsvärdena hämtas från basårsposten
<code>base</code> (bokslutet), antagandena har illustrativa standardvärden och de årsvisa banorna gör det möjligt att ange
ett värde per prognosår. Tillväxt anges som andel (0,03 = tre procent), belopp i mnkr och löpande priser.</p></html>"));
  end Assumptions;

  package Interfaces "Riktade årsvärden mellan komponenterna"
    connector Signal = Real "Ett värde för året" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {90, 110, 130}, fillColor = {90, 110, 130}, fillPattern = FillPattern.Solid)}));

    connector Cohorts "Befolkning per åldersgrupp, de äldre uppdelade och totalt, personer"
      Real p[5] "Invånare 0-6, 7-15, 16-18, 19-64 och 65+";
      Real older[3] "Invånare 65-79, 80-89 och 90+";
      Real population "Folkmängd";
      annotation(
        Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid)}));
    end Cohorts;

    connector DemographyDrivers "Årets demografiska antaganden"
      Real residualMigration[5] "Restflöde per åldersgrupp, personer";
      Real migrationDelta "Förändrat flyttnetto, personer";
      Real birthChange "Relativ förändring av antalet födda, andel";
      annotation(
        Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {90, 110, 130}, fillColor = {90, 110, 130}, fillPattern = FillPattern.Solid)}));
    end DemographyDrivers;

    connector CostDrivers "Årets kostnadsantaganden"
      Real wageGrowth "Löneökning, andel";
      Real priceGrowth "Prisökning, andel";
      Real pensionExpense "Pensionskostnad, mnkr";
      Real pensionCashPayments "Pensionsutbetalningar, mnkr";
      annotation(
        Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {90, 110, 130}, fillColor = {90, 110, 130}, fillPattern = FillPattern.Solid)}));
    end CostDrivers;

    connector RevenueReference "Årets referensvärden för skatt och bidrag (SKR eller illustrativa) och folkmängden de bygger på"
      Real tax "Skatteintäkter, mnkr";
      Real grants "Generella bidrag och utjämning, mnkr";
      Real population "Folkmängd, personer";
      Real nationalPopulation "Rikets folkmängd vid slutet av föregående år, personer";
      annotation(
        Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {90, 110, 130}, fillColor = {90, 110, 130}, fillPattern = FillPattern.Solid)}));
    end RevenueReference;

    connector OperatingCost "Driftens nettokostnad och dess pensionsdelar, mnkr"
      Real cost "Verksamhetens nettokostnad, mnkr";
      Real pensionExpense "Pensionskostnad, mnkr";
      Real pensionCashPayments "Pensionsutbetalningar, mnkr";
      annotation(
        Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {35, 115, 85}, fillColor = {35, 115, 85}, fillPattern = FillPattern.Solid)}));
    end OperatingCost;

    connector TaxAndGrants "Skatteintäkter och generella bidrag, mnkr"
      Real tax "Skatteintäkter, mnkr";
      Real grants "Generella statsbidrag och utjämning, mnkr";
      annotation(
        Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid)}));
    end TaxAndGrants;
    connector SignalInput = input Signal "Ingång: årsvärde" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {90, 110, 130}, fillColor = {90, 110, 130}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector SignalOutput = output Signal "Utgång: årsvärde" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {90, 110, 130}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector CohortsInput = input Cohorts "Ingång: befolkning" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector CohortsOutput = output Cohorts "Utgång: befolkning" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {40, 95, 140}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector DemographyDriversInput = input DemographyDrivers "Ingång: demografiska antaganden" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {90, 110, 130}, fillColor = {90, 110, 130}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector DemographyDriversOutput = output DemographyDrivers "Utgång: demografiska antaganden" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {90, 110, 130}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector CostDriversInput = input CostDrivers "Ingång: kostnadsantaganden" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {90, 110, 130}, fillColor = {90, 110, 130}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector CostDriversOutput = output CostDrivers "Utgång: kostnadsantaganden" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {90, 110, 130}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector RevenueReferenceInput = input RevenueReference "Ingång: referens för skatt och bidrag" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {90, 110, 130}, fillColor = {90, 110, 130}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector RevenueReferenceOutput = output RevenueReference "Utgång: referens för skatt och bidrag" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {90, 110, 130}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector OperatingCostInput = input OperatingCost "Ingång: driftens kostnader" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {35, 115, 85}, fillColor = {35, 115, 85}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector OperatingCostOutput = output OperatingCost "Utgång: driftens kostnader" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {35, 115, 85}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector TaxAndGrantsInput = input TaxAndGrants "Ingång: skatt och bidrag" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    connector TaxAndGrantsOutput = output TaxAndGrants "Utgång: skatt och bidrag" annotation(
      Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Polygon(lineColor = {40, 95, 140}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, points = {{-100, 100}, {100, 0}, {-100, -100}, {-100, 100}})}));
    annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Polygon(lineColor = {40, 95, 140}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, points = {{-80, 40}, {-20, 0}, {-80, -40}, {-80, 40}}), Line(points = {{-20, 0}, {20, 0}}, color = {40, 95, 140}, thickness = 0.5), Polygon(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, points = {{20, 40}, {80, 0}, {20, -40}, {20, 40}})}), 
      Documentation(info = "<html><p>Kopplingarna för årets värden från en komponent till nästa. Varje koppling har en
avsändare (utgång, ihålig triangel) och en eller flera mottagare (ingång, fylld triangel). Det är orsakssamband, inte
fysiska flöden: bokföringens samband skrivs ut i komponenterna.</p></html>"));
  end Interfaces;

  package Components "Modellens delar; alla räknar ett steg per år med samma kalender"
    model Calendar "Gemensam årskalender: ett steg per år, inga efter prognoshorisonten"
      parameter Integer horizon(min = 1) "Antal årssteg";
      parameter Integer baseYear "Basår: simuleringen startar vid tiden baseYear, som är bokslutet 31 december detta år";
      Integer year = baseYear + yearIndex "Kalenderår för det senast beräknade året";
      Boolean tick "Sant i det ögonblick ett år räknas fram";
      discrete Integer yearIndex(start = 0, fixed = true) "Antal beräknade år";
      Integer pathIndex "Vilket värde i de årsvisa banorna som gäller; första årets värde vid tiden 0";
    equation
      tick = sample(baseYear + 1, 1) and time <= baseYear + horizon;
      when tick then
        yearIndex = pre(yearIndex) + 1;
      end when;
      pathIndex = max(1, yearIndex);
      annotation(
        defaultComponentName = "calendar",
        defaultComponentPrefixes = "inner",
        Icon(coordinateSystem(extent = {{-100, -60}, {100, 60}}), graphics = {Rectangle(extent = {{-100, -60}, {100, 60}}, lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 5}, {95, 50}}, textString = "Kalender", fontSize = 18, textColor = {35, 50, 65}), Text(extent = {{-95, -50}, {95, 0}}, textString = "Start: bokslut %baseYear", fontSize = 14, textColor = {90, 110, 130})}),
        Documentation(info = "<html><p>Deklareras en gång som <code>inner</code>; alla komponenter läser den som <code>outer</code>.
Tiden är kalenderår: simuleringen startar vid <code>baseYear</code> (bokslutet 31 december det året) och räknar fram ett år
i taget, så att tiden 2026 är 31 december 2026. Sätt simuleringens starttid till basåret och sluttiden till basåret plus
antalet år.</p></html>"));
    end Calendar;

    model Scenario "Årets antaganden, hämtade ur de årsvisa banorna"
      outer Calendar calendar;
      parameter Integer horizon(min = 1) "Antal årssteg";
      parameter Real residualMigrationPath[horizon, 5] "Restflöde per år och åldersgrupp, personer";
      parameter Real migrationDeltaPath[horizon] "Förändrat flyttnetto per år, personer";
      parameter Real birthChangePath[horizon] "Relativ förändring av födda per år, andel";
      parameter Real wageGrowthPath[horizon] "Löneökning per år, andel";
      parameter Real priceGrowthPath[horizon] "Prisökning per år, andel";
      parameter Real pensionExpensePath[horizon] "Pensionskostnad per år, mnkr";
      parameter Real pensionCashPaymentsPath[horizon] "Pensionsutbetalningar per år, mnkr";
      parameter Real referenceTax[horizon] "Referensbana för skatteintäkter, mnkr";
      parameter Real referenceGrants[horizon] "Referensbana för generella bidrag, mnkr";
      parameter Real referencePopulation[horizon] "Folkmängd som referensbanan bygger på, personer";
      parameter Real nationalPopulationPath[horizon] "Rikets folkmängd vid slutet av året före varje prognosår, personer";
      parameter Real investmentPath[horizon] "Investeringar per år, mnkr";
      parameter Real interestRatePath[horizon] "Låneränta per år, andel";
      Interfaces.DemographyDriversOutput demography "Årets demografiska antaganden" annotation(
        Placement(transformation(origin = {-624, -43}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {-260, -25}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      Interfaces.CostDriversOutput operations "Årets löne-, pris- och pensionsantaganden" annotation(
        Placement(transformation(origin = {648, -43}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {270, -25}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      Interfaces.RevenueReferenceOutput revenue "Årets referens för skatt och bidrag" annotation(
        Placement(transformation(origin = {-720, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 180), iconTransformation(origin = {-300, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 180)));
      Interfaces.SignalOutput investment "Årets investeringar, mnkr" annotation(
        Placement(transformation(origin = {240, -43}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {100, -25}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      Interfaces.SignalOutput interestRate "Årets låneränta på ingående skuld, andel" annotation(
        Placement(transformation(origin = {720, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {300, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
    equation
      demography.residualMigration = residualMigrationPath[calendar.pathIndex, :];
      demography.migrationDelta = migrationDeltaPath[calendar.pathIndex];
      demography.birthChange = birthChangePath[calendar.pathIndex];
      operations.wageGrowth = wageGrowthPath[calendar.pathIndex];
      operations.priceGrowth = priceGrowthPath[calendar.pathIndex];
      operations.pensionExpense = pensionExpensePath[calendar.pathIndex];
      operations.pensionCashPayments = pensionCashPaymentsPath[calendar.pathIndex];
      revenue.tax = referenceTax[calendar.pathIndex];
      revenue.grants = referenceGrants[calendar.pathIndex];
      revenue.population = referencePopulation[calendar.pathIndex];
      revenue.nationalPopulation = nationalPopulationPath[calendar.pathIndex];
      investment = investmentPath[calendar.pathIndex];
      interestRate = interestRatePath[calendar.pathIndex];
      annotation(
        Icon(coordinateSystem(extent = {{-300, -25}, {300, 25}}), graphics = {Rectangle(extent = {{-300, -25}, {300, 25}}, lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-290, -20}, {290, 20}}, textString = "Scenario: årets antaganden", fontSize = 16, textColor = {35, 50, 65})}),
        Documentation(info = "<html><p>Plockar ut årets värden ur de årsvisa banorna. Beslutsparametrar (investeringar,
skattesats) och yttre antaganden (löner, priser, ränta, SKR:s referens för skatt och bidrag, befolkningsbanan) kommer in i
modellen här, så att varje komponent får dem genom en koppling.</p></html>"));
    end Scenario;

    partial model DemographyBase "Det varje demografimodell ska ge: antaganden in, befolkning ut"
      outer Calendar calendar;
      Interfaces.DemographyDriversInput drivers "Årets demografiska antaganden" annotation(
        Placement(transformation(origin = {0, 130}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {0, 75}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      Interfaces.CohortsOutput cohorts "Befolkning per åldersgrupp vid årets slut" annotation(
        Placement(transformation(origin = {240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
      discrete output Real population "Folkmängd vid årets slut";
      discrete output Real births "Födda under året";
      discrete output Real deaths "Döda under året";
      discrete output Real migration "Flyttnetto och restflöden under året";
      discrete output Real populationBalance "Kontroll av befolkningsbalansen, personer; ska vara noll";
    equation
      assert(population > 0, "Scenariot tömmer befolkningen");
      assert(abs(populationBalance) < 1e-7*max(1, population), "Befolkningsbalansen stämmer inte");
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, pattern = LinePattern.Dash, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 8), Text(textColor = {35, 50, 65}, extent = {{-92, 0}, {92, 60}}, textString = "Demografi"), Text(textColor = {90, 110, 130}, extent = {{-92, -70}, {92, -10}}, textString = "basklass")}), Documentation(info = "<html><p>En demografimodell som bygger på denna klass kan ersätta den i
<code>Annual</code> (<code>redeclare</code>). Resten av modellen ser bara kopplingen <code>cohorts</code>.</p></html>"));
    end DemographyBase;

    package Fertility "Valbara födelsemodeller för CohortDemography"
      partial model Partial "Födda under året utifrån befolkningen vid årets början"
        outer Calendar calendar;
        input Real population[2, 101] "Befolkning vid årets början, ettårsåldrar 0-100+ per kön (1 män, 2 kvinnor)";
        parameter Real births0 "Födda under basåret";
        parameter Real population0[2, 101] "Befolkning vid basårets slut";
        output Real births "Födda under året";
      protected
        Real exposure[101] = cat(1, {0.5*population[2, 1]}, {0.5*(population[2, a] + population[2, a - 1]) for a in 2:101})
          "Kvinnor i varje ålder under året: hälften av dem i åldern och hälften av dem ett år yngre vid årets början";
        annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, pattern = LinePattern.Dash, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 8), Text(textColor = {35, 50, 65}, extent = {{-92, 0}, {92, 60}}, textString = "Födda"), Text(textColor = {90, 110, 130}, extent = {{-92, -70}, {92, -10}}, textString = "basklass")}), Documentation(info = "<html><p>Barn föds under året, så en kvinna räknas till hälften i sin ålder vid årets
början och till hälften i nästa. CohortDemography delar upp de födda i pojkar och flickor.</p></html>"));
      end Partial;

      model Constant "Konstant summerad fruktsamhet; standard 1,41 barn per kvinna"
        extends Partial;
        parameter Real totalFertility = 1.41 "Summerad fruktsamhet: barn per kvinna under ett liv med årets fruktsamhet";
        parameter Real profile[101] = Data.SCB.fertilityProfile "Andel av de födda vid varje ålder hos modern";
      equation
        births = totalFertility*profile*exposure;
        annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 15), Text(textColor = {40, 95, 140}, extent = {{-92, 10}, {92, 70}}, textString = "Födda"), Text(textColor = {35, 50, 65}, extent = {{-92, -70}, {92, -5}}, textString = "TFR %totalFertility")}));
      end Constant;

      model Projected "Summerad fruktsamhet enligt SCB:s riksframskrivning, år för år"
        extends Partial;
        parameter Integer firstYear "Kalenderår för det första årssteget";
        parameter Real scale = 1 "Kommunens fruktsamhet i förhållande till rikets";
        parameter Real profile[101] = Data.SCB.fertilityProfile "Andel av de födda vid varje ålder hos modern";
        Real totalFertility = scale*Data.SCB.projectedTotalFertility[max(1, min(size(Data.SCB.projectedTotalFertility, 1), firstYear - Data.SCB.projectionFirstYear + max(1, calendar.yearIndex)))] "Årets summerade fruktsamhet";
      equation
        births = totalFertility*profile*exposure;
        annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 15), Text(textColor = {40, 95, 140}, extent = {{-92, 10}, {92, 70}}, textString = "Födda"), Text(textColor = {35, 50, 65}, extent = {{-92, -70}, {92, -5}}, textString = "SCB-prognos")}));
      end Projected;

      model Legacy "Födda följer antalet 19-64-åringar, som i femgruppsmodellen"
        extends Partial;
      equation
        births = births0*sum(population[:, 20:65])/sum(population0[:, 20:65]);
        annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 15), Text(textColor = {40, 95, 140}, extent = {{-92, 10}, {92, 70}}, textString = "Födda"), Text(textColor = {35, 50, 65}, extent = {{-92, -70}, {92, -5}}, textString = "följer 19-64")}));
      end Legacy;
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Text(textColor = {35, 50, 65}, extent = {{-92, -30}, {92, 40}}, textString = "Födda"), Text(textColor = {90, 110, 130}, extent = {{-92, -80}, {92, -35}}, textString = "modeller")}), Documentation(info = "<html><p>Välj med till exempel <code>redeclare Fertility.Projected fertility(firstYear = 2026)</code>.
Alla utom Legacy använder SCB:s åldersprofil för fruktsamheten. Prövning mot utfallet 2021-2025
(scripts/hindcast_demography.py) gav minst fel med Constant och 1,41.</p></html>"));
    end Fertility;

    model CohortDemography "Kohort-komponentmodell: ettårsåldrar 0-100+ per kön, som i SCB:s framskrivningar"
      extends DemographyBase(population(start = sum(population0), fixed = true), births(start = data.births, fixed = true),
        deaths(start = data.deaths, fixed = true), migration(start = 0, fixed = true), populationBalance(start = 0, fixed = true));
      parameter Data.SCB.DemographyYear data "Basår: befolkning, dödsrisk och kalibrering (SCB); kommunens paket ger ett värde";
      parameter Real reportedTotal = sum(data.population) "Folkmängd att starta från; ettårsåldrarna skalas till den";
      parameter Real population0[2, 101] = data.population*reportedTotal/sum(data.population) "Befolkning vid basårets slut, ettårsåldrar per kön";
      parameter Real mortalityRatio[2] = data.mortalityRatio "Kommunens dödlighet i förhållande till rikets livslängdstabell, män och kvinnor";
      parameter Boolean mortalityImprovement = true "Låt dödsriskerna fortsätta sjunka";
      parameter Real improvement[2, 101] = if mortalityImprovement then data.mortalityImprovement else zeros(2, 101)
        "Årlig minskning av dödsrisken; basårets historiska trend, eller Data.SCB.mortalityImprovement för SCB:s framskrivning";
      parameter Real residualMigration[2, 101] = data.residualMigration "Kalibrerat restflöde per ålder och kön, personer per år";
      parameter Real migrationWeights[5] = {0.15, 0.12, 0.03, 0.65, 0.05} "Hur ett förändrat flyttnetto fördelas på 0-6, 7-15, 16-18, 19-64 och 65+";
      parameter Real shareBoys = data.shareBoys "Andel pojkar bland de födda";
      replaceable Fertility.Constant fertility constrainedby Fertility.Partial(births0 = data.births, population0 = population0)
        "Födelsemodell" annotation(choicesAllMatching = true);
      discrete output Real p[2, 101](start = population0, each fixed = true) "Befolkning vid årets slut, ettårsåldrar per kön";
      discrete output Real older[3](start = {sum(population0[:, 66:80]), sum(population0[:, 81:90]), sum(population0[:, 91:101])}, each fixed = true)
        "Invånare 65-79, 80-89 och 90+";
    protected
      parameter Integer width[5] = {7, 9, 3, 46, 36} "Antal ettårsåldrar i varje åldersgrupp";
      parameter Integer group[101] = {if a <= 7 then 1 elseif a <= 16 then 2 elseif a <= 19 then 3 elseif a <= 65 then 4 else 5 for a in 1:101} "Åldersgrupp för varje ettårsålder";
      parameter Real deltaShape[2, 101] = {{0.5*migrationWeights[group[a]]/width[group[a]] for a in 1:101} for s in 1:2}
        "Ett förändrat flyttnetto på en person, fördelat på ålder och kön";
      discrete Real q[2, 101](start = zeros(2, 101), each fixed = true) "Årets dödsrisk";
      discrete Real survivors[2, 101](start = zeros(2, 101), each fixed = true) "Överlevande från årets början";
      discrete Real delta[2, 101](start = zeros(2, 101), each fixed = true) "Årets förändrade flyttnetto per ålder och kön";
      discrete Real natural[2, 101](start = zeros(2, 101), each fixed = true) "Befolkning vid årets slut utan flyttningar";
    equation
      fertility.population = pre(p);
      cohorts.p = {sum(p[:, 1:7]), sum(p[:, 8:16]), sum(p[:, 17:19]), sum(p[:, 20:65]), sum(p[:, 66:101])};
      cohorts.older = older;
      cohorts.population = population;
    algorithm
      when calendar.tick then
        q := {{min(1, data.deathRisk[s, a]*mortalityRatio[s]*exp(-improvement[s, a]*calendar.yearIndex)) for a in 1:101} for s in 1:2};
        births := fertility.births*(1 + drivers.birthChange);
        survivors := pre(p) .* (ones(2, 101) - q);
        deaths := sum(pre(p)) - sum(survivors);
        delta := drivers.migrationDelta*deltaShape;
        for s in 1:2 loop
          natural[s, 1] := births*(if s == 1 then shareBoys else 1 - shareBoys);
          for a in 2:100 loop
            natural[s, a] := survivors[s, a - 1];
          end for;
          natural[s, 101] := survivors[s, 100] + survivors[s, 101];
        end for;
        // Restflödet kan inte ta bort fler än som finns i en ålder; det som inte kan tas bort räknas inte som flyttning.
        p := {{max(0, natural[s, a] + residualMigration[s, a] + delta[s, a]) for a in 1:101} for s in 1:2};
        older := {sum(p[:, 66:80]), sum(p[:, 81:90]), sum(p[:, 91:101])};
        population := sum(p);
        migration := sum(p) - sum(natural);
        populationBalance := population - pre(population) - births + deaths - migration;
      end when;
      annotation(
        Icon(coordinateSystem(extent = {{-100, -75}, {100, 75}}), graphics = {Rectangle(lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, extent = {{-100, -75}, {100, 75}}, radius = 8), Text(textColor = {40, 95, 140}, extent = {{-95, 30}, {95, 65}}, textString = "Demography", fontSize = 21), Text(textColor = {35, 50, 65}, extent = {{-95, -27}, {95, 25}}, textString = "Åldrar 0-100+ per kön", fontSize = 16), Text(textColor = {40, 95, 140}, extent = {{-95, -68}, {95, -35}}, textString = "%name", fontSize = 14)}),
        Documentation(info = "<html><p>Kohort-komponentmetoden som SCB använder. Varje år blir alla ett år äldre, en andel dör
enligt rikets livslängdstabell skalad till kommunens nivå, födslarna kommer från en valbar fruktsamhetsmodell, och
kalibrerade restflöden plus scenariots förändrade flyttnetto läggs till. Data: <code>Data.SCB</code> (Källa: SCB).</p>
<p>Dödsrisken vid basåret är de fem senaste livslängdstabellerna flyttade längs trenden och medelvärdesbildade, så att
ett enskilt ovanligt år inte sätter nivån. Trenden fortsätter framåt om <code>mortalityImprovement</code> är sant.</p>
<p>Den externa befolkningsbanan i <code>drivers.residualMigration</code> används inte; modellen kalibrerar egna
restflöden per ettårsålder. <code>older</code> delar 65+ i 65-79, 80-89 och 90+.</p></html>"));
    end CohortDemography;

    model Demography "Fem åldersgrupper med kontrollerad befolkningsbalans"
      parameter Real p0[5] "Invånare 0-6, 7-15, 16-18, 19-64 och 65+ vid basårets slut";
      parameter Real deathRates[5] "Dödsrisk per åldersgrupp och år";
      parameter Real migrationWeights[5] "Fördelning av ett förändrat flyttnetto på åldersgrupperna";
      parameter Real births0 "Födda under basåret";
      extends DemographyBase(population(start = sum(p0), fixed = true), births(start = births0, fixed = true),
        deaths(start = 0, fixed = true), migration(start = 0, fixed = true), populationBalance(start = 0, fixed = true));
      discrete output Real p[5](start = p0, each fixed = true) "Invånare per åldersgrupp vid årets slut";
      parameter Real olderShares[3] "Fast uppdelning av 65+ i 65-79, 80-89 och 90+ (SCB)";
    protected
      discrete Real survivors[5](each start = 0, each fixed = true) "Överlevande från årets början";
      discrete Real ageOut[5](each start = 0, each fixed = true) "Åldras upp till nästa grupp under året";
    equation
      assert(min(p) >= 0, "Scenariot tömmer en åldersgrupp");
      cohorts.p = p;
      cohorts.older = p[5]*olderShares;
      cohorts.population = population;
    algorithm
      when calendar.tick then
        births := births0*pre(p[4])/p0[4]*(1 + drivers.birthChange);
        deaths := sum(pre(p).*deathRates);
        survivors := pre(p).*(ones(5) - deathRates);
        ageOut := {survivors[1]/7, survivors[2]/9, survivors[3]/3, survivors[4]/46, 0};
        for i in 1:5 loop
          p[i] := survivors[i] - ageOut[i] + (if i == 1 then births else ageOut[i - 1]) + drivers.residualMigration[i] + drivers.migrationDelta*migrationWeights[i];
        end for;
        population := sum(p);
        migration := sum(drivers.residualMigration) + drivers.migrationDelta*sum(migrationWeights);
        populationBalance := population - pre(population) - births + deaths - migration;
      end when;
      annotation(
        Icon(coordinateSystem(extent = {{-100, -75}, {100, 75}}), graphics = {Rectangle(extent = {{-100, -75}, {100, 75}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 30}, {95, 65}}, textString = "Demography", fontSize = 21, textColor = {40, 95, 140}), Text(extent = {{-95, -27}, {95, 25}}, textString = "Fem åldersgrupper", fontSize = 16, textColor = {35, 50, 65}), Text(extent = {{-95, -68}, {95, -35}}, textString = "%name", fontSize = 14, textColor = {40, 95, 140})}),
        Diagram(coordinateSystem(extent = {{-240, -130}, {240, 130}}), graphics = {Text(extent = {{-235, 85}, {235, 125}}, textString = "Demography", fontSize = 22, textColor = {35, 50, 65}), Rectangle(extent = {{-230, -55}, {-100, 65}}, lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{-65, -55}, {65, 65}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{100, -55}, {230, 65}}, lineColor = {50, 120, 90}, fillColor = {236, 248, 240}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-225, 35}, {-105, 60}}, textString = "Indata / antaganden", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, 35}, {60, 60}}, textString = "Tillstånd / årssteg", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, 35}, {225, 60}}, textString = "Utdata", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-225, -48}, {-105, 32}}, textString = "Antaganden\nFödda, flyttnetto\nDödsrisker", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, -48}, {60, 32}}, textString = "p[1:5]\nÅrets steg", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, -48}, {225, 32}}, textString = "Folkmängd\nFödda / döda\nFlyttnetto", fontSize = 13, textColor = {35, 50, 65}), Line(points = {{-100, 5}, {-65, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Line(points = {{65, 5}, {100, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Text(extent = {{-235, -125}, {235, -75}}, textString = "Befolkningsbalans per år i personer; restflödet innehåller statistiska justeringar.", fontSize = 12, textColor = {35, 50, 65})}),
        Documentation(info = "<html><p>Befolkningsbalans för fem breda åldersgrupper, i personer. Varje år åldras en jämnt fördelad
andel upp till nästa grupp, födda tillkommer i 0-6 och restflödet lägger till flyttningar och statistiska justeringar.
Används av sajten; CohortDemography är den finare modellen.</p></html>"));
    end Demography;

    model Services "Verksamhetens behov och kapacitet per sektor"
      parameter Real educationWeights[3] "Vikter för 0-6, 7-15 och 16-18 år i utbildningsbehovet";
      parameter Real sectorCosts[3] "Kostnadsvikter för utbildning, äldreomsorg och övrigt, mnkr";
      parameter Real adjustment[3] "Årlig kapacitetsanpassning per sektor (0 = låst, 1 = direkt)";
      parameter Real fixedShare[3] "Fast andel av kapaciteten per sektor";
      parameter Real careWeights[3] = {1, 1, 1} "Äldreomsorgens kostnad per invånare 65-79, 80-89 och 90+; bara förhållandet mellan dem spelar roll";
      outer Calendar calendar;
      Interfaces.CohortsInput cohorts "Befolkning per åldersgrupp" annotation(
        Placement(transformation(origin = {-240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {-100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
      discrete output Real capacity[3](each start = 1, each fixed = true) "Kapacitet för utbildning, äldreomsorg och övrigt, index (basår = 1)";
      discrete output Real demand[3](each start = 1, each fixed = true) "Behov för utbildning, äldreomsorg och övrigt, index (basår = 1)";
      discrete output Real educationIndex(start = 1, fixed = true) "Utbildningsbehov, index (basår = 1)";
      discrete output Real careIndex(start = 1, fixed = true) "Äldreomsorgsbehov viktat efter ålder, index (basår = 1)";
      discrete Interfaces.SignalOutput serviceVolume(start = 1, fixed = true) "Verksamhetens volym: kostnadsviktad kapacitet, index (basår = 1)" annotation(
        Placement(transformation(origin = {240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
    protected
      parameter Real careBase(fixed = false) "Viktat antal äldre vid start";
      parameter Real cohorts0[5](each fixed = false) "Invånare per åldersgrupp vid start";
    initial equation
      careBase = careWeights*cohorts.older;
      cohorts0 = cohorts.p;
    algorithm
      when calendar.tick then
        educationIndex := sum({educationWeights[i]*cohorts.p[i]/cohorts0[i] for i in 1:3});
        careIndex := careWeights*cohorts.older/careBase;
        demand := {educationIndex, careIndex, sum(cohorts.p)/sum(cohorts0)};
        capacity := pre(capacity) + adjustment.*(fixedShare + (ones(3) - fixedShare).*demand - pre(capacity));
        serviceVolume := sum(sectorCosts.*capacity)/sum(sectorCosts);
      end when;
      annotation(
        Icon(coordinateSystem(extent = {{-100, -75}, {100, 75}}), graphics = {Rectangle(extent = {{-100, -75}, {100, 75}}, lineColor = {35, 115, 85}, fillColor = {234, 248, 240}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 30}, {95, 65}}, textString = "Verksamhet", fontSize = 21, textColor = {35, 115, 85}), Text(extent = {{-95, -27}, {95, 25}}, textString = "Behov / kapacitet", fontSize = 16, textColor = {35, 50, 65}), Text(extent = {{-95, -68}, {95, -35}}, textString = "%name", fontSize = 14, textColor = {35, 115, 85})}),
        Diagram(coordinateSystem(extent = {{-240, -130}, {240, 130}}), graphics = {Text(extent = {{-235, 85}, {235, 125}}, textString = "Verksamhet", fontSize = 22, textColor = {35, 50, 65}), Rectangle(extent = {{-230, -55}, {-100, 65}}, lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{-65, -55}, {65, 65}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{100, -55}, {230, 65}}, lineColor = {50, 120, 90}, fillColor = {236, 248, 240}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-225, 35}, {-105, 60}}, textString = "Indata / antaganden", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, 35}, {60, 60}}, textString = "Tillstånd / årssteg", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, 35}, {225, 60}}, textString = "Utdata", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-225, -48}, {-105, 32}}, textString = "Befolkning\nKostnadsvikter\nAnpassningstakt", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, -48}, {60, 32}}, textString = "capacity[1:3]\nÅrlig anpassning", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, -48}, {225, 32}}, textString = "Behov\nUtbildning / omsorg\nVolym", fontSize = 13, textColor = {35, 50, 65}), Line(points = {{-100, 5}, {-65, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Line(points = {{65, 5}, {100, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Text(extent = {{-235, -125}, {235, -75}}, textString = "Tre index för utbildning, äldreomsorg och övrig verksamhet.", fontSize = 12, textColor = {35, 50, 65})}),
        Documentation(info = "<html><p>Behovet av utbildning, äldreomsorg och övrig verksamhet räknas som index från
befolkningen. Kapaciteten följer behovet med fördröjning, och en fast andel ändras inte. Kapaciteten vägs ihop med
kostnadsvikterna till verksamhetens volym, som styr driftens kostnader.</p>
<p>Äldreomsorgens behov viktar 65-79, 80-89 och 90+ efter kostnad per invånare (careWeights, från Kolada). En person 80+
kostar ungefär sju gånger så mycket som en person 65-79. Med lika vikter blir det antalet invånare 65+.</p></html>"));
    end Services;

    model OperatingAccounts "Driftens kostnader och intäkter; pensionskostnad skild från pensionsutbetalning"
      parameter Real population0 "Folkmängd vid basårets slut";
      parameter Real payroll0 "Lönekostnader exklusive pensioner i basåret, mnkr";
      parameter Real pension0 "Pensionskostnad i basåret, mnkr";
      parameter Real otherOperatingExpense0 "Övriga verksamhetskostnader i basåret, mnkr";
      parameter Real operatingRevenue0 "Verksamhetens intäkter i basåret, mnkr";
      parameter Real netCostRoundingAdjustment "Avrundningsjustering, mnkr";
      parameter Real operatingRevenueGrowth "Verksamhetsintäkternas årliga ökning, andel";
      parameter Real productivityGrowth "Årlig produktivitetsökning, andel";
      outer Calendar calendar;
      Interfaces.CohortsInput cohorts "Befolkning" annotation(
        Placement(transformation(origin = {-240, -87}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {-100, -50}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
      Interfaces.SignalInput serviceVolume "Verksamhetens volym, index" annotation(
        Placement(transformation(origin = {-240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {-100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
      Interfaces.CostDriversInput drivers "Årets löne-, pris- och pensionsantaganden" annotation(
        Placement(transformation(origin = {0, 130}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {0, 75}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      Interfaces.OperatingCostOutput accounts "Nettokostnad och pensioner till finansieringen" annotation(
        Placement(transformation(origin = {0, -130}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {0, -75}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      discrete output Real wageIndex(start = 1, fixed = true) "Lönenivå, index (basår = 1)";
      discrete output Real priceIndex(start = 1, fixed = true) "Prisnivå för övriga kostnader, index (basår = 1)";
      discrete output Real revenueIndex(start = 1, fixed = true) "Taxor och avgifter, index (basår = 1)";
      discrete output Real productivity(start = 1, fixed = true) "Produktivitet, index (basår = 1)";
      discrete output Real payroll(start = payroll0, fixed = true) "Lönekostnader exklusive pensioner, mnkr";
      discrete output Real pensionExpense(start = pension0, fixed = true) "Pensionskostnad, mnkr";
      discrete output Real pensionCashPayments(start = pension0, fixed = true) "Pensionsutbetalningar, mnkr; utgångsvärdet är illustrativt, inte ett utfall";
      discrete output Real otherOperatingExpense(start = otherOperatingExpense0, fixed = true) "Övriga verksamhetskostnader, mnkr";
      discrete output Real operatingRevenue(start = operatingRevenue0, fixed = true) "Verksamhetens intäkter, mnkr";
      discrete output Real cost(start = payroll0 + pension0 + otherOperatingExpense0 - operatingRevenue0 + netCostRoundingAdjustment, fixed = true) "Verksamhetens nettokostnad exklusive avskrivningar, mnkr";
    equation
      accounts.cost = cost;
      accounts.pensionExpense = pensionExpense;
      accounts.pensionCashPayments = pensionCashPayments;
    algorithm
      when calendar.tick then
        wageIndex := pre(wageIndex)*(1 + drivers.wageGrowth);
        priceIndex := pre(priceIndex)*(1 + drivers.priceGrowth);
        revenueIndex := pre(revenueIndex)*(1 + operatingRevenueGrowth);
        productivity := pre(productivity)*(1 + productivityGrowth);
        payroll := payroll0*wageIndex*serviceVolume/productivity;
        otherOperatingExpense := otherOperatingExpense0*priceIndex*serviceVolume;
        operatingRevenue := operatingRevenue0*revenueIndex*cohorts.population/population0;
        pensionExpense := drivers.pensionExpense;
        pensionCashPayments := drivers.pensionCashPayments;
        cost := payroll + pensionExpense + otherOperatingExpense - operatingRevenue + netCostRoundingAdjustment;
      end when;
      annotation(
        Icon(coordinateSystem(extent = {{-100, -75}, {100, 75}}), graphics = {Rectangle(extent = {{-100, -75}, {100, 75}}, lineColor = {35, 115, 85}, fillColor = {234, 248, 240}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 30}, {95, 65}}, textString = "Drift", fontSize = 21, textColor = {35, 115, 85}), Text(extent = {{-95, -27}, {95, 25}}, textString = "Löner / pensioner\nÖvrigt / avgifter", fontSize = 16, textColor = {35, 50, 65}), Text(extent = {{-95, -68}, {95, -35}}, textString = "%name", fontSize = 14, textColor = {35, 115, 85})}),
        Diagram(coordinateSystem(extent = {{-240, -130}, {240, 130}}), graphics = {Text(extent = {{-235, 85}, {235, 125}}, textString = "Drift", fontSize = 22, textColor = {35, 50, 65}), Rectangle(extent = {{-230, -55}, {-100, 65}}, lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{-65, -55}, {65, 65}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{100, -55}, {230, 65}}, lineColor = {50, 120, 90}, fillColor = {236, 248, 240}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-225, 35}, {-105, 60}}, textString = "Indata / antaganden", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, 35}, {60, 60}}, textString = "Tillstånd / årssteg", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, 35}, {225, 60}}, textString = "Utdata", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-225, -48}, {-105, 32}}, textString = "Befolkning\nVolym\nPensionsbanor", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, -48}, {60, 32}}, textString = "Löne- och prisindex\nProduktivitet\nÅrets bokslut", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, -48}, {225, 32}}, textString = "Löner / pension\nÖvrigt / avgifter\nNettokostnad", fontSize = 13, textColor = {35, 50, 65}), Line(points = {{-100, 5}, {-65, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Line(points = {{65, 5}, {100, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Text(extent = {{-235, -125}, {235, -75}}, textString = "Pensionskostnad och utbetalning hålls isär; belopp i mnkr, löpande priser.", fontSize = 12, textColor = {35, 50, 65})}),
        Documentation(info = "<html><p>Driftens nettokostnad byggs upp från bokslutets delar i basåret:</p>
<ul><li>löner = löner<sub>0</sub> · löneindex · volym / produktivitet</li>
<li>övriga kostnader = övrigt<sub>0</sub> · prisindex · volym</li>
<li>verksamhetsintäkter = intäkter<sub>0</sub> · intäktsindex · folkmängd / folkmängd<sub>0</sub></li>
<li>nettokostnad = löner + pensionskostnad + övriga kostnader - verksamhetsintäkter + avrundning</li></ul>
<p>Pensionskostnaden och pensionsutbetalningarna hålls isär, eftersom kostnaden påverkar resultatet och utbetalningen
kassaflödet. Belopp i mnkr, löpande priser.</p></html>"));
    end OperatingAccounts;

    model Revenue "Skatt och generella bidrag: referensbana, föregående års befolkning och förenklad utjämning"
      parameter Real p0[5] "Invånare per åldersgrupp som basårets skatt och bidrag bygger på (slutet av året före basåret)";
      parameter Real tax0 "Skatteintäkter i basåret, mnkr";
      parameter Real grants0 "Generella bidrag och utjämning i basåret, mnkr";
      parameter Real taxRate "Kommunal skattesats i scenariot, procent";
      parameter Real baseTaxRate "Kommunal skattesats i basåret, procent";
      parameter Real equalisationOffset "Andel av en lokal avvikelse i skatteunderlaget som utjämningen tar tillbaka";
      parameter Real populationRevenueElasticity "Hur starkt skatt och bidrag följer folkmängden";
      parameter Boolean importedRevenue "Sant när referensbanan är importerad från SKR";
      parameter Boolean followReference = false "Skatt och bidrag följer referensbanan exakt, utan befolkningseffekt (till exempel budgetens belopp)";
      parameter Real nationalPopulation0 "Rikets folkmängd vid slutet av året före basåret, personer";
      parameter Boolean grantsByComponent = false "Bidragen räknas per del i stället för som en referensbana (gäller inte en importerad SKR-bana eller budgetens belopp)";
      parameter Integer horizon(min = 1) = 1 "Antal årssteg i bidragsbanorna";
      parameter Real grantComponents0[5] = zeros(5) "Basårets inkomstutjämning, kostnadsutjämning, regleringsbidrag, LSS-utjämning och fastighetsavgift, mnkr";
      parameter Real incomeEqualisationPerCapita[horizon] = zeros(horizon) "Inkomstutjämning per år, kr per invånare";
      parameter Real costEqualisationPerCapita[horizon] = zeros(horizon) "Kostnadsutjämning per år, kr per invånare (avgift negativ)";
      parameter Real regulationPerCapita[horizon] = zeros(horizon) "Regleringsbidrag per år, kr per invånare (avgift negativ)";
      parameter Real lssEqualisationPerCapita[horizon] = zeros(horizon) "LSS-utjämning per år, kr per invånare (avgift negativ)";
      parameter Real propertyFee[horizon] = zeros(horizon) "Kommunal fastighetsavgift per år, mnkr";
      parameter Real otherGeneralGrants[horizon] = zeros(horizon) "Övriga generella bidrag per år, mnkr";
      outer Calendar calendar;
      Interfaces.CohortsInput cohorts "Befolkning" annotation(
        Placement(transformation(origin = {0, 130}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {0, 75}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      Interfaces.RevenueReferenceInput reference "Årets referens för skatt och bidrag" annotation(
        Placement(transformation(origin = {-240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {-100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
      Interfaces.TaxAndGrantsOutput taxAndGrants "Skatt och bidrag till finansieringen" annotation(
        Placement(transformation(origin = {240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
      discrete output Real tax(start = tax0, fixed = true) "Skatteintäkter, mnkr: referensbana · kommunens folkmängd i förhållande till rikets · ålderseffekt · skattesats / basårets skattesats";
      discrete output Real grants(start = grants0, fixed = true) "Generella statsbidrag och utjämning, mnkr: referensbana · kommunens folkmängd i förhållande till rikets, minus utjämning av ålderseffekten";
      discrete output Real grantParts[6](start = cat(1, grantComponents0, {grants0 - sum(grantComponents0)}), each fixed = true)
        "Bidragen per del med grantsByComponent: inkomstutjämning, kostnadsutjämning, regleringsbidrag, LSS-utjämning, fastighetsavgift och övriga, mnkr";
    protected
      discrete Real popFactor(start = 1, fixed = true) "kommunens folkmängd i förhållande till rikets, jämfört med året före basåret";
      discrete Real standardTax(start = 0, fixed = true) "Skatt vid basårets skattesats och sammansättning, mnkr";
      discrete Real composition(start = 1, fixed = true) "Andel 19-64 år i förhållande till basåret";
      discrete Real deviation(start = 0, fixed = true) "Skatteeffekt av en ändrad andel i arbetsför ålder, mnkr";
    equation
      taxAndGrants.tax = tax;
      taxAndGrants.grants = grants;
    algorithm
      when calendar.tick then
        // Referensbanans tillväxt gäller hela riket; kommunens del följer folkmängden i förhållande till rikets.
        popFactor := if importedRevenue then sum(pre(cohorts.p))/reference.population else ((sum(pre(cohorts.p))/sum(p0))/(reference.nationalPopulation/nationalPopulation0))^populationRevenueElasticity;
        standardTax := reference.tax*popFactor;
        composition := (pre(cohorts.p[4])/p0[4])/(sum(pre(cohorts.p))/sum(p0));
        deviation := if importedRevenue or followReference then 0 else standardTax*(composition - 1);
        tax := if followReference then reference.tax*taxRate/baseTaxRate else (standardTax + deviation)*taxRate/baseTaxRate;
        // Per del: belopp per invånare gånger folkmängden året före; inkomstutjämningen tar tillbaka ålderseffekten.
        grantParts := if grantsByComponent then {incomeEqualisationPerCapita[calendar.pathIndex]*sum(pre(cohorts.p))/1e6 - equalisationOffset*deviation,
          costEqualisationPerCapita[calendar.pathIndex]*sum(pre(cohorts.p))/1e6, regulationPerCapita[calendar.pathIndex]*sum(pre(cohorts.p))/1e6,
          lssEqualisationPerCapita[calendar.pathIndex]*sum(pre(cohorts.p))/1e6, propertyFee[calendar.pathIndex], otherGeneralGrants[calendar.pathIndex]} else zeros(6);
        grants := if followReference then reference.grants elseif grantsByComponent and not importedRevenue then sum(grantParts)
          else reference.grants*popFactor - equalisationOffset*deviation;
      end when;
      annotation(
        Icon(coordinateSystem(extent = {{-100, -75}, {100, 75}}), graphics = {Rectangle(extent = {{-100, -75}, {100, 75}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 30}, {95, 65}}, textString = "Intäkter", fontSize = 21, textColor = {40, 95, 140}), Text(extent = {{-95, -27}, {95, 25}}, textString = "Skatt / bidrag", fontSize = 16, textColor = {35, 50, 65}), Text(extent = {{-95, -68}, {95, -35}}, textString = "%name", fontSize = 14, textColor = {40, 95, 140})}),
        Diagram(coordinateSystem(extent = {{-240, -130}, {240, 130}}), graphics = {Text(extent = {{-235, 85}, {235, 125}}, textString = "Intäkter", fontSize = 22, textColor = {35, 50, 65}), Rectangle(extent = {{-230, -55}, {-100, 65}}, lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{-65, -55}, {65, 65}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{100, -55}, {230, 65}}, lineColor = {50, 120, 90}, fillColor = {236, 248, 240}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-225, 35}, {-105, 60}}, textString = "Indata / antaganden", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, 35}, {60, 60}}, textString = "Tillstånd / årssteg", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, 35}, {225, 60}}, textString = "Utdata", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-225, -48}, {-105, 32}}, textString = "Befolkning\nSkattesats\nReferensbanor", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, -48}, {60, 32}}, textString = "Årets skatt\nÅrets bidrag", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, -48}, {225, 32}}, textString = "Skatt / bidrag", fontSize = 13, textColor = {35, 50, 65}), Line(points = {{-100, 5}, {-65, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Line(points = {{65, 5}, {100, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Text(extent = {{-235, -125}, {235, -75}}, textString = "Förenklad befolkningseffekt och utjämning kring en referensbana (SKR eller illustrativ).", fontSize = 12, textColor = {35, 50, 65})}),
        Documentation(info = "<html><p>Skatt och generella bidrag utgår från en referensbana: SKR:s beräkning för kommunen när den
är importerad, annars en illustrativ tillväxt. Banan skalas med föregående års folkmängd. En ändrad andel i arbetsför ålder
ändrar skatten, och utjämningen tar tillbaka det mesta av avvikelsen via bidragen. En annan skattesats ändrar bara skatten.</p>
<p>Utjämningen är en förenklad känslighet, inte lagens beräkning av inkomst-, kostnads- och LSS-utjämning.</p>
<p>Med <code>grantsByComponent</code> räknas bidragen per del: inkomstutjämning, kostnadsutjämning, regleringsbidrag och
LSS-utjämning som belopp per invånare gånger folkmängden året före, fastighetsavgiften och övriga bidrag i mnkr. Banorna
kommer från Assumptions. Inkomstutjämningen följer rikets skattekraft per invånare, regleringsbidraget statens beslut;
SCB publicerar alla delar per kommun (tabell TAB1981 och TAB4011). <code>grantParts</code> visar delarna.</p>
<p>Med <code>followReference</code> tas referensbanan rakt av, till exempel budgetens belopp; bara en ändrad skattesats
påverkar då skatten. En importerad SKR-bana innehåller redan befolkningens sammansättning, så då läggs ingen ålderseffekt
till; banan skalas bara med modellens folkmängd mot SKR:s.</p>
<p>Befolkningseffekten jämför med <code>p0</code>, folkmängden vid slutet av året före basåret, eftersom basårets skatt
bygger på folkbokföringen den 1 november året före. Referensbanans tillväxt (till exempel <code>taxGrowth</code>) gäller
hela rikets skatteunderlag och bidrag, så kommunens del skalas med kommunens folkmängd i förhållande till rikets: växer riket
medan kommunen krymper, minskar dess andel.</p>
<p>Både skatten och de flesta bidragen räknas per invånare. Utjämningen skyddar mot låga inkomster per invånare, inte mot
färre invånare. Varje invånare som försvinner tar därför med sig både sin skatt och sin del av bidragen: med Motalas 2025 års
belopp (2 330 + 987 mnkr för 43 131 invånare) cirka 77 000 kr per år. Motala minskade med 374 invånare under 2025, vilket
ger cirka 29 mnkr mindre i skatt och bidrag från 2026.</p></html>"));
    end Revenue;

    model Capital "Tillgångar och avskrivningar med en sammanvägd avskrivningstid"
      parameter Real assets0 "Tillgångar vid basårets slut, mnkr";
      parameter Real depreciation0 "Avskrivningar i basåret, mnkr";
      parameter Real life "Sammanvägd avskrivningstid, år";
      outer Calendar calendar;
      Interfaces.SignalInput investment "Årets investeringar, mnkr" annotation(
        Placement(transformation(origin = {0, 130}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {0, 75}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      discrete output Real assets(start = assets0, fixed = true) "Tillgångar vid årets slut, mnkr";
      discrete Interfaces.SignalOutput depreciation(start = depreciation0, fixed = true) "Årets avskrivningar, mnkr" annotation(
        Placement(transformation(origin = {240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
      discrete output Real assetBalance(start = 0, fixed = true) "Kontroll av tillgångsbalansen, mnkr; ska vara noll";
    equation
      assert(assets >= 0, "Avskrivningarna tömmer tillgångarna");
      assert(abs(assetBalance) < 1e-7*max(1, assets), "Tillgångsbalansen stämmer inte");
    algorithm
      when calendar.tick then
        depreciation := (pre(assets) + 0.5*investment)/life;
        assets := pre(assets) + investment - depreciation;
        assetBalance := assets - pre(assets) - investment + depreciation;
      end when;
      annotation(
        Icon(coordinateSystem(extent = {{-100, -75}, {100, 75}}), graphics = {Rectangle(extent = {{-100, -75}, {100, 75}}, lineColor = {155, 95, 35}, fillColor = {255, 246, 230}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 30}, {95, 65}}, textString = "Kapital", fontSize = 21, textColor = {155, 95, 35}), Text(extent = {{-95, -27}, {95, 25}}, textString = "Tillgångar / avskrivning", fontSize = 16, textColor = {35, 50, 65}), Text(extent = {{-95, -68}, {95, -35}}, textString = "%name", fontSize = 14, textColor = {155, 95, 35})}),
        Diagram(coordinateSystem(extent = {{-240, -130}, {240, 130}}), graphics = {Text(extent = {{-235, 85}, {235, 125}}, textString = "Kapital", fontSize = 22, textColor = {35, 50, 65}), Rectangle(extent = {{-230, -55}, {-100, 65}}, lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{-65, -55}, {65, 65}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{100, -55}, {230, 65}}, lineColor = {50, 120, 90}, fillColor = {236, 248, 240}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-225, 35}, {-105, 60}}, textString = "Indata / antaganden", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, 35}, {60, 60}}, textString = "Tillstånd / årssteg", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, 35}, {225, 60}}, textString = "Utdata", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-225, -48}, {-105, 32}}, textString = "Investeringar\nAvskrivningstid", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, -48}, {60, 32}}, textString = "Tillgångar\nÅrets steg", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, -48}, {225, 32}}, textString = "Avskrivningar\nKontroll", fontSize = 13, textColor = {35, 50, 65}), Line(points = {{-100, 5}, {-65, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Line(points = {{65, 5}, {100, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Text(extent = {{-235, -125}, {235, -75}}, textString = "Investeringar tas i bruk samma år; belopp i mnkr.", fontSize = 12, textColor = {35, 50, 65})}),
        Documentation(info = "<html><p>Investeringar tas i bruk samma år. Avskrivningen räknas med en sammanvägd avskrivningstid
härledd ur bokslutet (tillgångar / avskrivningar, cirka 17 år):</p>
<ul><li>avskrivning = (tillgångar föregående år + halva årets investering) / avskrivningstid</li>
<li>tillgångar = föregående år + investering - avskrivning</li></ul>
<p>Ingen uppdelning på anläggningar, pågående projekt eller försäljningar.</p></html>"));
    end Capital;

    model Finance "Årets resultat, kassaflöde, upplåning och amortering"
      parameter Real debt0 "Låneskuld vid basårets slut, mnkr";
      parameter Real cash0 "Kassa vid basårets slut, mnkr";
      parameter Real interest0 "Räntekostnader i basåret, mnkr (bokslut)";
      parameter Real result0 "Årets resultat i basåret enligt modellens poster, mnkr";
      parameter Real financialIncome "Finansiella intäkter per år, mnkr";
      parameter Real otherFinancialExpense "Finansiella kostnader utöver räntor per år, mnkr";
      parameter Real revenue0 "Skatt och generella bidrag i basåret, mnkr";
      outer Calendar calendar;
      Interfaces.TaxAndGrantsInput taxAndGrants "Skatt och bidrag" annotation(
        Placement(transformation(origin = {0, -130}, extent = {{-18, -18}, {18, 18}}, rotation = 90), iconTransformation(origin = {0, -75}, extent = {{-9, -9}, {9, 9}}, rotation = 90)));
      Interfaces.OperatingCostInput operations "Nettokostnad och pensioner" annotation(
        Placement(transformation(origin = {0, 130}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {0, 75}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      Interfaces.SignalInput depreciation "Avskrivningar, mnkr" annotation(
        Placement(transformation(origin = {-240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {-100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
      Interfaces.SignalInput investment "Investeringar, mnkr" annotation(
        Placement(transformation(origin = {-144, 130}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {-60, 75}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      Interfaces.SignalInput interestRate "Låneränta, andel" annotation(
        Placement(transformation(origin = {240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 180), iconTransformation(origin = {100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 180)));
      discrete output Real result(start = result0, fixed = true) "Årets resultat, mnkr";
      discrete output Real interest(start = interest0, fixed = true) "Räntekostnader, mnkr";
      discrete output Real operatingCash(start = 0, fixed = true) "Kassaflöde från den löpande verksamheten, mnkr";
      discrete output Real debt(start = debt0, fixed = true) "Låneskuld vid årets slut, mnkr";
      discrete output Real cash(start = cash0, fixed = true) "Kassa vid årets slut, mnkr";
      discrete output Real borrowing(start = 0, fixed = true) "Nya lån under året, mnkr";
      discrete output Real repayment(start = 0, fixed = true) "Amortering under året, mnkr";
      discrete output Real cashBalance(start = 0, fixed = true) "Kontroll av kassabalansen, mnkr; ska vara noll";
      discrete output Real debtBalance(start = 0, fixed = true) "Kontroll av skuldbalansen, mnkr; ska vara noll";
      discrete output Real resultShare(start = 100*result0/revenue0, fixed = true) "Årets resultat i procent av skatter och bidrag (kommunens finansiella mål)";
      discrete output Real interestShare(start = 100*interest0/revenue0, fixed = true) "Räntekostnader i procent av skatter och bidrag";
      discrete output Real cumulativeInterest(start = 0, fixed = true) "Räntekostnader sammanlagt sedan basåret, mnkr";
    protected
      discrete Real financingGap(start = 0, fixed = true) "Investeringar som kassaflödet inte täcker, mnkr";
    equation
      assert(debt >= 0, "Låneskulden får inte bli negativ");
      assert(abs(debtBalance) < 1e-7*max(1, debt), "Skuldbalansen stämmer inte");
      assert(abs(cashBalance) < 1e-7*max(1, abs(operatingCash)), "Kassabalansen stämmer inte");
    algorithm
      when calendar.tick then
        interest := pre(debt)*interestRate;
        result := taxAndGrants.tax + taxAndGrants.grants - operations.cost - depreciation + financialIncome - interest - otherFinancialExpense;
        operatingCash := result + depreciation + operations.pensionExpense - operations.pensionCashPayments;
        resultShare := 100*result/(taxAndGrants.tax + taxAndGrants.grants);
        interestShare := 100*interest/(taxAndGrants.tax + taxAndGrants.grants);
        cumulativeInterest := pre(cumulativeInterest) + interest;
        financingGap := investment - operatingCash;
        borrowing := max(0, financingGap);
        repayment := min(pre(debt), max(0, -financingGap));
        debt := pre(debt) + borrowing - repayment;
        cash := pre(cash) + operatingCash - investment + borrowing - repayment;
        debtBalance := debt - pre(debt) - borrowing + repayment;
        cashBalance := cash - pre(cash) - operatingCash + investment - borrowing + repayment;
      end when;
      annotation(
        Icon(coordinateSystem(extent = {{-100, -75}, {100, 75}}), graphics = {Rectangle(extent = {{-100, -75}, {100, 75}}, lineColor = {105, 75, 145}, fillColor = {245, 238, 252}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 30}, {95, 65}}, textString = "Finans", fontSize = 21, textColor = {105, 75, 145}), Text(extent = {{-95, -27}, {95, 25}}, textString = "Resultat / kassa / lån", fontSize = 16, textColor = {35, 50, 65}), Text(extent = {{-95, -68}, {95, -35}}, textString = "%name", fontSize = 14, textColor = {105, 75, 145})}),
        Diagram(coordinateSystem(extent = {{-240, -130}, {240, 130}}), graphics = {Text(extent = {{-235, 85}, {235, 125}}, textString = "Finans", fontSize = 22, textColor = {35, 50, 65}), Rectangle(extent = {{-230, -55}, {-100, 65}}, lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{-65, -55}, {65, 65}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{100, -55}, {230, 65}}, lineColor = {50, 120, 90}, fillColor = {236, 248, 240}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-225, 35}, {-105, 60}}, textString = "Indata / antaganden", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, 35}, {60, 60}}, textString = "Tillstånd / årssteg", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, 35}, {225, 60}}, textString = "Utdata", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-225, -48}, {-105, 32}}, textString = "Skatt / bidrag\nKostnader / investering\nPension / ränta", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, -48}, {60, 32}}, textString = "Lån / kassa\nÅrets kassaflöde", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, -48}, {225, 32}}, textString = "Resultat / ränta\nNya lån / amortering\nKontroller", fontSize = 13, textColor = {35, 50, 65}), Line(points = {{-100, 5}, {-65, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Line(points = {{65, 5}, {100, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Text(extent = {{-235, -125}, {235, -75}}, textString = "Ränta på ingående skuld. Pensionskostnad och pensionsutbetalning hålls isär.", fontSize = 12, textColor = {35, 50, 65})}),
        Documentation(info = "<html><p>Här möts allt:</p>
<ul><li>ränta = låneskuld vid årets början · ränta</li>
<li>årets resultat = skatt + bidrag - nettokostnad - avskrivningar + finansiella intäkter - ränta - övriga finansiella kostnader</li>
<li>kassaflöde = resultat + avskrivningar + pensionskostnad - pensionsutbetalningar</li>
<li>räcker kassaflödet inte till investeringarna lånar kommunen mellanskillnaden; ett överskott amorterar, och det som blir
över läggs i kassan</li></ul>
<p>Nyckeltal: <code>resultShare</code> (resultatet i procent av skatter och bidrag, kommunens finansiella mål),
<code>interestShare</code> (räntekostnaderna i procent av skatter och bidrag) och <code>cumulativeInterest</code>
(räntekostnaderna sammanlagt sedan basåret).</p>
<p>Rörelsekapital, borgen och leasing ingår inte.</p></html>"));
    end Finance;
    annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Text(textColor = {35, 50, 65}, extent = {{-92, -40}, {92, 40}}, textString = "Delar")}));
  end Components;

  partial model Annual "Kommunens ekonomi år för år: demografi, verksamhet, drift, intäkter, kapital och finans"
    extends Assumptions;
    Integer yearIndex "Antal beräknade år";
    Integer year "Kalenderår för det senast beräknade året (samma som tiden)";
    // Befolkning och verksamhet
    Real p[5] "Invånare 0-6, 7-15, 16-18, 19-64 och 65+ vid årets slut";
    Real population "Folkmängd vid årets slut";
    Real births "Födda under året";
    Real deaths "Döda under året";
    Real migration "Flyttnetto och restflöden under året";
    Real educationIndex "Utbildningsbehov, index (basår = 1)";
    Real careIndex "Äldreomsorgsbehov viktat efter ålder, index (basår = 1)";
    Real demand[3] "Behov för utbildning, äldreomsorg och övrigt, index";
    Real capacity[3] "Kapacitet för utbildning, äldreomsorg och övrigt, index";
    Real serviceVolume "Verksamhetens volym, index (basår = 1)";
    // Drift
    Real wageIndex "Lönenivå, index (basår = 1)";
    Real priceIndex "Prisnivå för övriga kostnader, index (basår = 1)";
    Real revenueIndex "Taxor och avgifter, index (basår = 1)";
    Real productivity "Produktivitet, index (basår = 1)";
    Real payroll "Lönekostnader exklusive pensioner, mnkr";
    Real pensionExpense "Pensionskostnad, mnkr";
    Real pensionCashPayments "Pensionsutbetalningar, mnkr";
    Real otherOperatingExpense "Övriga verksamhetskostnader, mnkr";
    Real operatingRevenue "Verksamhetens intäkter, mnkr";
    Real cost "Verksamhetens nettokostnad exklusive avskrivningar, mnkr";
    // Intäkter, kapital och finansiering
    Real tax "Skatteintäkter, mnkr; följer rikets skatteunderlag och kommunens folkmängd i förhållande till rikets (se komponenten Intäkter)";
    Real grants "Generella statsbidrag och utjämning, mnkr; följer referensbanan och kommunens folkmängd i förhållande till rikets (se komponenten Intäkter)";
    Real grantParts[6] "Bidragen per del med grantsByComponent: inkomstutjämning, kostnadsutjämning, regleringsbidrag, LSS-utjämning, fastighetsavgift och övriga, mnkr";
    Real depreciation "Avskrivningar, mnkr";
    Real assets "Tillgångar vid årets slut, mnkr";
    Real interest "Räntekostnader, mnkr";
    Real result "Årets resultat, mnkr";
    Real operatingCash "Kassaflöde från den löpande verksamheten, mnkr";
    Real borrowing "Nya lån under året, mnkr";
    Real repayment "Amortering under året, mnkr";
    Real debt "Låneskuld vid årets slut, mnkr";
    Real cash "Kassa vid årets slut, mnkr";
    // Nyckeltal
    Real resultShare "Årets resultat i procent av skatter och bidrag (kommunens finansiella mål)";
    Real interestShare "Räntekostnader i procent av skatter och bidrag";
    Real cumulativeInterest "Räntekostnader sammanlagt sedan basåret, mnkr";
    // Kontroller: ska vara noll
    Real populationBalance "Kontroll av befolkningsbalansen, personer";
    Real assetBalance "Kontroll av tillgångsbalansen, mnkr";
    Real cashBalance "Kontroll av kassabalansen, mnkr";
    Real debtBalance "Kontroll av skuldbalansen, mnkr";
    Real annualInvestment "Årets investeringar, mnkr";
    Real annualInterestRate "Årets låneränta, andel";
    inner Components.Calendar calendar(horizon = horizon, baseYear = base.year) "Gemensam årskalender" annotation(
      Placement(transformation(origin = {370, 305}, extent = {{-40, -20}, {40, 20}})));
    Components.Scenario scenario(horizon = horizon, residualMigrationPath = residualMigrationPath, migrationDeltaPath = migrationDeltaPath, birthChangePath = birthChangePath, wageGrowthPath = wageGrowthPath, priceGrowthPath = priceGrowthPath, pensionExpensePath = pensionExpensePath, pensionCashPaymentsPath = pensionCashPaymentsPath, referenceTax = referenceTax, referenceGrants = referenceGrants, referencePopulation = referencePopulation, nationalPopulationPath = nationalPopulationPath, investmentPath = investmentPath, interestRatePath = interestRatePath) "Årets antaganden" annotation(
      Placement(transformation(origin = {-20, 240}, extent = {{-300, -25}, {300, 25}})));
    replaceable Components.Demography demography(p0 = p0, olderShares = olderShares, deathRates = deathRates, migrationWeights = migrationWeights, births0 = births0) constrainedby Components.DemographyBase "Demografi: fem åldersgrupper som standard; Examples.AnnualCohort använder ettårsåldrar" annotation(choicesAllMatching = true, 
      Placement(transformation(origin = {-280, 110}, extent = {{-75, -56}, {75, 56}})));
    Components.Services services(careWeights = careWeights, educationWeights = educationWeights, sectorCosts = sectorCosts, adjustment = serviceAdjustment, fixedShare = serviceFixedShare) "Verksamhet" annotation(
      Placement(transformation(origin = {-20, 110}, extent = {{-75, -56}, {75, 56}})));
    Components.OperatingAccounts operations(population0 = sum(p0), payroll0 = payroll0, pension0 = pension0, otherOperatingExpense0 = otherOperatingExpense0, operatingRevenue0 = operatingRevenue0, netCostRoundingAdjustment = netCostRoundingAdjustment, operatingRevenueGrowth = operatingRevenueGrowth, productivityGrowth = productivityGrowth) "Drift" annotation(
      Placement(transformation(origin = {250, 110}, extent = {{-75, -56}, {75, 56}})));
    Components.Revenue revenues(p0 = revenuePopulation0, tax0 = tax0, grants0 = grants0, taxRate = taxRate, baseTaxRate = baseTaxRate, equalisationOffset = equalisationOffset, populationRevenueElasticity = populationRevenueElasticity, importedRevenue = importedRevenue, followReference = revenueFromReference, nationalPopulation0 = nationalPopulation0, grantsByComponent = grantsByComponent, horizon = horizon, grantComponents0 = grantComponents0, incomeEqualisationPerCapita = incomeEqualisationPerCapitaPath, costEqualisationPerCapita = costEqualisationPerCapitaPath, regulationPerCapita = regulationPerCapitaPath, lssEqualisationPerCapita = lssEqualisationPerCapitaPath, propertyFee = propertyFeePath, otherGeneralGrants = otherGeneralGrantsPath) "Intäkter" annotation(
      Placement(transformation(origin = {-280, -110}, extent = {{-75, -56}, {75, 56}})));
    Components.Capital capital(assets0 = assets0, depreciation0 = depreciation0, life = life) "Kapital" annotation(
      Placement(transformation(origin = {-20, -110}, extent = {{-75, -56}, {75, 56}})));
    Components.Finance finance(debt0 = debt0, cash0 = cash0, interest0 = base.interestExpense, result0 = tax0 + grants0 - (payroll0 + pension0 + otherOperatingExpense0 - operatingRevenue0 + netCostRoundingAdjustment) - depreciation0 + financialIncome - base.interestExpense - otherFinancialExpense, financialIncome = financialIncome, otherFinancialExpense = otherFinancialExpense, revenue0 = tax0 + grants0) "Finans" annotation(
      Placement(transformation(origin = {250, -110}, extent = {{-75, -56}, {75, 56}})));
  equation
    connect(scenario.demography, demography.drivers) annotation(
      Line(points = {{-280, 215}, {-280, 166}}, color = {90, 110, 130}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(scenario.operations, operations.drivers) annotation(
      Line(points = {{250, 215}, {250, 166}}, color = {90, 110, 130}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(scenario.revenue, revenues.reference) annotation(
      Line(points = {{-320, 240}, {-400, 240}, {-400, -110}, {-355, -110}}, color = {90, 110, 130}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(scenario.investment, capital.investment) annotation(
      Line(points = {{80, 215}, {80, -20}, {-20, -20}, {-20, -54}}, color = {155, 95, 35}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(scenario.investment, finance.investment) annotation(
      Line(points = {{80, -20}, {205, -20}, {205, -54}}, color = {155, 95, 35}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(scenario.interestRate, finance.interestRate) annotation(
      Line(points = {{280, 240}, {400, 240}, {400, -110}, {325, -110}}, color = {90, 110, 130}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(demography.cohorts, services.cohorts) annotation(
      Line(points = {{-205, 110}, {-95, 110}}, color = {40, 95, 140}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(demography.cohorts, operations.cohorts) annotation(
      Line(points = {{-205, 110}, {-190, 110}, {-190, 40}, {165, 40}, {165, 73}, {175, 73}}, color = {40, 95, 140}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(demography.cohorts, revenues.cohorts) annotation(
      Line(points = {{-190, 40}, {-190, -20}, {-280, -20}, {-280, -54}}, color = {40, 95, 140}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(services.serviceVolume, operations.serviceVolume) annotation(
      Line(points = {{55, 110}, {175, 110}}, color = {35, 115, 85}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(operations.accounts, finance.operations) annotation(
      Line(points = {{250, 54}, {250, -54}}, color = {35, 115, 85}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(revenues.taxAndGrants, finance.taxAndGrants) annotation(
      Line(points = {{-205, -110}, {-190, -110}, {-190, -195}, {250, -195}, {250, -166}}, color = {40, 95, 140}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    connect(capital.depreciation, finance.depreciation) annotation(
      Line(points = {{55, -110}, {175, -110}}, color = {155, 95, 35}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}, arrowSize = 6));
    yearIndex = calendar.yearIndex;
    year = calendar.year;
    // Vid starttiden visas basårets utfall, därefter scenariots värden.
    annualInvestment = if yearIndex == 0 then base.investment else scenario.investment;
    annualInterestRate = if yearIndex == 0 then base.interestExpense/base.openingDebt else scenario.interestRate;
    p = demography.cohorts.p;
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
    grantParts = revenues.grantParts;
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
    resultShare = finance.resultShare;
    interestShare = finance.interestShare;
    cumulativeInterest = finance.cumulativeInterest;
    annotation(
      Icon(coordinateSystem(extent = {{-100, -75}, {100, 75}}), graphics = {Rectangle(extent = {{-100, -75}, {100, 75}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 30}, {95, 65}}, textString = "Kommun", fontSize = 21, textColor = {40, 95, 140}), Text(extent = {{-95, -27}, {95, 25}}, textString = "Ekonomin\når för år", fontSize = 16, textColor = {35, 50, 65}), Text(extent = {{-95, -68}, {95, -35}}, textString = "%name", fontSize = 14, textColor = {40, 95, 140})}),
      Diagram(coordinateSystem(extent = {{-430, -285}, {430, 335}}), graphics = {Text(textColor = {35, 50, 65}, extent = {{-420, 290}, {300, 330}}, textString = "Kommunens ekonomi år för år", fontSize = 24), Text(textColor = {35, 50, 65}, extent = {{-185, 115}, {-110, 140}}, textString = "Åldersgrupper", fontSize = 13), Text(textColor = {35, 50, 65}, extent = {{60, 115}, {170, 140}}, textString = "Volym", fontSize = 13), Text(origin = {-132, 20}, textColor = {35, 50, 65}, extent = {{-60, 25}, {60, 50}}, textString = "Befolkning", fontSize = 13), Text(textColor = {35, 50, 65}, extent = {{255, -25}, {390, 25}}, textString = "Nettokostnad / pensioner", fontSize = 13), Text(textColor = {35, 50, 65}, extent = {{85, 0}, {190, 25}}, textString = "Investeringar", fontSize = 13), Text(textColor = {35, 50, 65}, extent = {{60, -140}, {170, -115}}, textString = "Avskrivningar", fontSize = 13), Text(textColor = {35, 50, 65}, extent = {{-155, -220}, {135, -195}}, textString = "Skatt / bidrag", fontSize = 13), Text(textColor = {35, 50, 65}, extent = {{-425, 60}, {-405, 140}}, textString = "Referens skatt/bidrag", fontSize = 13), Text(textColor = {35, 50, 65}, extent = {{405, 60}, {425, 140}}, textString = "Ränta", fontSize = 13), Text(textColor = {35, 50, 65}, extent = {{-420, -280}, {420, -235}}, textString = "Varje pil är en koppling (connect) från en utgång till en ingång. En gemensam kalender styr alla årssteg.
Tid: kalenderår från basårets bokslut. Belopp: mnkr, löpande priser. Antagandena kommer in via Scenario.", fontSize = 13)}),
      Documentation(info = "<html><p><b>Tid: kalenderår.</b> Starttiden ska vara basårets år (<code>base.year</code>).</p>
<p>Kommunens ekonomi år för år, i sex delar som delar en kalender: demografi, verksamhet, drift, intäkter, kapital och
finans. Antagandena kommer in via Scenario och flödar längs kopplingarna. Alla belopp i mnkr, löpande priser.</p>
<p>Modellen är partiell: en kommuns paket ger basåret (<code>base</code>) och uppdelningen av de äldre
(<code>olderShares</code>), som <a href=\"modelica://Motala.Annual\">Motala.Annual</a>. Utgångsläget är bokslutet för basåret. Årsvisa banor (<code>investmentPath</code>,
<code>interestRatePath</code>, <code>migrationDeltaPath</code> med flera) tar ett värde per prognosår. Befolknings-,
tillgångs-, skuld- och kassabalansen kontrolleras varje år.</p>
<p>Detta är inte en validerad prognos. Fem breda åldersgrupper, illustrativa kostnadsvikter, förenklad utjämning,
sammanvägd avskrivning och ränta på ingående skuld behöver bättre data. Pensionsutbetalningarna sätts lika med
kostnaden tills en egen källa finns. Rörelsekapital, anläggningsregister, lånens löptider och pensionsskulden modelleras
inte. Att modellen stämmer med en referensimplementation visar att räkningen är rätt, inte att prognosen är träffsäker.</p></html>"));
  end Annual;
  annotation(version = "0.1.0", Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Rectangle(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, extent = {{-70, -70}, {-35, 0}}), Rectangle(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, extent = {{-17, -70}, {18, 30}}), Rectangle(lineColor = {35, 115, 85}, fillColor = {35, 115, 85}, fillPattern = FillPattern.Solid, extent = {{35, -70}, {70, 60}})}),
    Documentation(info = "<html><p><b>Kommunekonomi</b> är komponenter för en svensk kommuns ekonomi år för år: befolkning,
verksamhet, drift, skatt och bidrag, investeringar, resultat och lån. Belopp i mnkr och löpande priser; tiden är kalenderår.</p>
<p>En kommun använder biblioteket i ett eget paket: basårens utfall som <code>Data.BaseYear</code>, demografin som
<code>Data.SCB.DemographyYear</code> och en modell som ärver <a href=\"modelica://Kommunekonomi.Annual\">Annual</a>
med sitt basår. <a href=\"modelica://Motala\">Motala</a> är exemplet.</p>
<p>Komponenterna kopplas med riktade kopplingar (<code>Interfaces</code>) och räknar ett steg per år med en gemensam
kalender. Demografin är utbytbar (<code>replaceable</code>): fem åldersgrupper eller ettårsåldrar.</p></html>"));
end Kommunekonomi;
