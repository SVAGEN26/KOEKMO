package Kommunekonomi "Kommunekonomi: en svensk kommuns ekonomi år för år; belopp i mnkr, tid i kalenderår"
  package Units "Enheter: belopp i miljoner kronor (mnkr), tid i år, personer"
    type Money = Real(final quantity = "Money", final unit = "MSEK") "Belopp, mnkr: lager, eller ett års summa av ett flöde";
    type MoneyRate = Real(final quantity = "MoneyRate", final unit = "MSEK/a") "Flöde, mnkr per år (kontinuerlig tid)";
    type MoneyPerPerson = Real(final quantity = "MoneyPerPerson", final unit = "SEK") "Kronor per invånare";
    type Persons = Real(final quantity = "Population", final unit = "1") "Antal personer";
    type Duration = Real(final quantity = "Time", final unit = "a") "Tid i år";
    type PersonsPerYear = Real(final quantity = "PopulationFlow", final unit = "1/a") "Personer per år: flyttnetto och restflöden";
    type Rate = Real(final quantity = "Rate", final unit = "1/a") "Takt per år i kontinuerlig tid: tillväxt, dödstal, åldrande";
    constant Duration year = 1 "Ett år: ett årsbelopp delat med year är ett flöde i mnkr per år";
    annotation(Documentation(info = "<html><p>Enhetstyper för bibliotekets variabler. <code>MSEK</code> är miljoner kronor (mnkr),
<code>a</code> år. Modelica har ingen valutaenhet; strängarna följer enhetssyntaxen, och <code>M</code> är prefixet mega.
Flödena är <code>MSEK/a</code> och lagren <code>MSEK</code>; ett årsbelopp som sprids över året blir
ett flöde genom division med <code>year</code>. Modelicas <code>time</code> räknas här i år, inte i sekunder som standarden
antar. Andelar, index och tillväxttakter är
dimensionslösa. Antagna flyttflöden är personer per år (<code>PersonsPerYear</code>); årets antal blir flödet gånger
<code>year</code>. Skattesatsen är i procent och har ingen enhet angiven.</p></html>"));
  end Units;

  package Data "Posttyper för bokslut, budget och befolkning, rikets data från SCB och funktioner för kalibrering"
    record BaseYear "Utfall vid basårets slut; mnkr och personer"
      Integer year "Basår";
      Real cohorts[3, 5] "Redovisade invånare 0-6, 7-15, 16-18, 19-64 och 65+ vid slutet av de två föregående åren och basåret";
      Real reportedPopulation[3] "Redovisad folkmängd samma tre år";
      Units.Persons births[2] "Födda föregående år och basåret";
      Units.Persons deaths "Döda under basåret";
      Units.Money tax "Skatteintäkter, mnkr";
      Units.Money priorYearSettlement "Därav korrigering av föregående års slutavräkning (slutavräkningsdifferens), mnkr; återkommer inte";
      Units.Money grants "Generella statsbidrag och utjämning, mnkr";
      Units.MoneyPerPerson equalisationNextYear[4] "Inkomstutjämning, kostnadsutjämning, regleringsbidrag och LSS-utjämning året efter basåret, kr per invånare; SCB publicerar dem i december under basåret";
      Real relativeTaxCapacity[2] "Skattekraft i förhållande till rikets medelskattekraft för utjämningsåret, basåret och året efter (SCB; året efters värde är känt vid basårets slut), andel";
      Units.Money grantComponents[5] "Därav inkomstutjämning, kostnadsutjämning, regleringsbidrag (avgift negativ), LSS-utjämning och fastighetsavgift, mnkr; resten är övriga generella bidrag";
      Units.Money payroll "Lönekostnader exklusive pensioner, mnkr";
      Units.Money pension "Pensionskostnad, mnkr";
      Units.Money otherOperatingExpense "Verksamhetens bruttokostnader minus löner och pensioner, mnkr";
      Units.Money operatingRevenue "Verksamhetens intäkter (avgifter, försäljning, riktade bidrag), mnkr";
      Units.Money netCostRoundingAdjustment "Avrundning som stämmer av delposterna mot redovisad nettokostnad, mnkr";
      Units.Money depreciation "Avskrivningar, mnkr";
      Units.Money financialIncome "Finansiella intäkter, mnkr";
      Units.Money interestExpense "Räntekostnader, mnkr";
      Units.Money otherFinancialExpense "Finansiella kostnader utöver räntor, mnkr";
      Units.Money debt "Låneskuld till banker och kreditinstitut vid årets slut, mnkr";
      Units.Money openingDebt "Låneskuld vid årets början (föregående års slut), mnkr";
      Units.Money cash "Kassa och bank, mnkr";
      Units.Money assets "Byggnader, anläggningar, maskiner och inventarier exklusive pågående investeringar, mnkr";
      Units.Money investment "Investeringar, mnkr";
      Real taxRate "Kommunal skattesats, procent";
      Real sectorShares[3] "Utbildning (0-18 år), äldreomsorg och övrig verksamhet, andel av nettokostnaden; Kolada (SCB:s räkenskapssammandrag)";
      Real educationShares[3] "Utbildningens fördelning på 0-6, 7-15 och 16-18 år, andel; Kolada";
      Units.MoneyPerPerson careCostPerInhabitant[2] "Äldreomsorgens kostnad per invånare 65-79 och 80+, kr; Kolada, treårsmedel (data/care-weights.json)";
      Real infrastructureShare = 0 "Gator och vägar som andel av övrig verksamhet: nettokostnaden för väg- och järnvägsnät samt parkering (Kolada N07024) delad med övrig verksamhets nettokostnad; 0 när uppgiften saknas";
      Units.Persons ages[101] = zeros(101) "Invånare per ettårsålder 0-100+ vid basårets slut, båda könen (SCB); nollor när uppgiften saknas";
      Real interestRate = -1 "Genomsnittlig ränta på upplåningen enligt årsredovisningen, andel; -1 när den saknas och räntan härleds ur räntekostnaden och årets medelskuld";
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

    function equalisationShare "Inkomstutjämningens andel av skattekraftsgapet: 95 procent för bidrag, 85 procent för avgift (lag 2004:773, 7 §)"
      input Real gap "Garantinivå minus egen skattekraft, andel av rikets medelskattekraft";
      output Real share "Gapet vägt med kompensationsgraden";
    algorithm
      share := (if gap > 0 then 0.95 else 0.85)*gap;
    end equalisationShare;

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

    function deathRatesPerYear "Dödstal per åldersgrupp: döda per person och år; 65+ ger basårets döda delat med medelfolkmängden"
      input Real cohorts[3, 5] "Redovisade invånare per åldersgrupp, tre år i följd";
      input Real totals[3] "Redovisad folkmängd samma tre år";
      input Real deaths "Döda under basåret";
      output Real rates[5] "Dödstal per åldersgrupp, per år";
    protected
      Real mean[5] "Medelfolkmängd under basåret: medel av årets början och slut";
    algorithm
      mean := (reconcile(cohorts[2, :], totals[2]) + reconcile(cohorts[3, :], totals[3]))/2;
      rates := {0.0004, 0.0001, 0.0002, 0.0018, 0};
      rates[5] := (deaths - sum(mean[1:4] .* rates[1:4]))/mean[5];
      annotation(Documentation(info = "<html><p>Dödstalet är SCB:s definition: döda delat med medelfolkmängden. Under 65 år samma
illustrativa tal som <code>mortality</code>; de är så små att risk och dödstal är samma sak.</p></html>"));
    end deathRatesPerYear;

    function ageProfile "Åldrande och dödlighet år för år ur basårets ettårsåldrar: vad som gör lagren till en åldringskedja"
      input Real ages[101] "Invånare per ettårsålder 0-100+ vid basårets slut, båda könen; bara nollor när uppgiften saknas";
      input Real births0 "Födda under basåret";
      input Integer horizon "Antal prognosår";
      input Real olderShares[3] "Uppdelning av 65+ vid basårets slut; används när ages saknas";
      output Real profile[horizon + 2, 12] "Rad 1-2: året före basåret och basåret; rad 2 + t: prognosår t. Kolumn 1-6: andel per år som åldras ur 0-6, 7-15, 16-18, 19-64, 65-79 och 80-89; 7-9: dödstal för 65-79, 80-89 och 90+ i förhållande till 65+ under basåret; 10-12: uppdelningen av 65+ vid årets början";
    protected
      constant Integer first[7] = {1, 8, 17, 20, 66, 81, 91} "Första index (ålder + 1) i varje lager";
      constant Integer last[7] = {7, 16, 19, 65, 80, 90, 101} "Sista index i varje lager";
      constant Real stationary[6] = {1/7, 1/9, 1/3, 1/46, 0.056, 0.060} "Utan ettårsåldrar: jämn åldersfördelning, och rikets livslängdstabell för en stationär befolkning i 65+";
      constant Real stationaryMortality[3] = {1, 3.84, 12.98} "Utan ettårsåldrar: dödstal i förhållande till 65-79 (rikets tabell 2025)";
      Real risk[2, 101] = SCB.combinedDeathRisk() "Dödsrisk och dess årliga minskning, båda könen";
      Real q[101] "Årets dödsrisk per ålder";
      Real start[101] "Invånare per ålder vid årets början";
      Real finish[101] "Invånare per ålder vid årets slut";
      Real before[7];
      Real after[7];
      Real mean[7] "Lagrens medelfolkmängd under året";
      Real deaths;
      Real level "65+:s dödstal under basåret i tabellen; dödstalen anges i förhållande till det";
    algorithm
      if sum(ages) <= 0 then
        for y in 1:horizon + 2 loop
          profile[y, 1:6] := stationary;
          profile[y, 7:9] := stationaryMortality/(stationaryMortality*olderShares);
          profile[y, 10:12] := olderShares;
        end for;
        return;
      end if;
      // Två år bakåt: de som i dag är a + 1 år var a år för ett år sedan, och fler, eftersom några har dött.
      finish := ages;
      for y in 0:-1:-1 loop
        q := {min(0.99, risk[1, a]*(1 - risk[2, a])^y) for a in 1:101};
        start[1:99] := {finish[a + 1]/(1 - q[a]) for a in 1:99};
        start[100] := 0.5*finish[101]/(1 - q[100]);
        start[101] := 0.5*finish[101]/(1 - q[101]);
        finish := start;
      end for;
      level := 1;
      for y in -1:horizon loop
        q := {min(0.99, risk[1, a]*(1 - risk[2, a])^y) for a in 1:101};
        if y <= 0 then
          // Historiken är känd: basårets åldrar, ett eller noll år bakåt.
          finish := ages;
          for k in 0:-1:y + 1 loop
            finish := cat(1, {finish[a + 1]/(1 - min(0.99, risk[1, a]*(1 - risk[2, a])^k)) for a in 1:99},
              {0.5*finish[101]/(1 - min(0.99, risk[1, 100]*(1 - risk[2, 100])^k)), 0.5*finish[101]/(1 - min(0.99, risk[1, 101]*(1 - risk[2, 101])^k))});
          end for;
        else
          // Framåt: alla blir ett år äldre, årets födda är basårets, och dödsrisken sjunker med rikets trend.
          finish[1] := births0;
          finish[2:100] := {start[a]*(1 - q[a]) for a in 1:99};
          finish[101] := start[100]*(1 - q[100]) + start[101]*(1 - q[101]);
        end if;
        for g in 1:7 loop
          before[g] := sum(start[first[g]:last[g]]);
          after[g] := sum(finish[first[g]:last[g]]);
          mean[g] := max(1e-9, (before[g] + after[g])/2);
        end for;
        for g in 1:6 loop
          // De som fyller år över gränsen under året: de äldsta i lagret vid årets början som lever till födelsedagen.
          profile[y + 2, g] := start[last[g]]*(1 - q[last[g]]/2)/mean[g];
        end for;
        for j in 1:3 loop
          deaths := sum(start[a]*q[a] for a in first[4 + j]:last[4 + j]);
          profile[y + 2, 6 + j] := deaths/mean[4 + j];
          profile[y + 2, 9 + j] := before[4 + j]/max(1e-9, sum(before[5:7]));
        end for;
        if y == 0 then
          level := max(1e-9, sum(profile[2, 6 + j]*mean[4 + j] for j in 1:3)/sum(mean[5:7]));
        end if;
        start := finish;
      end for;
      profile[:, 7:9] := profile[:, 7:9]/level;
      annotation(Documentation(info = "<html><p>De sju lagren (0-6, 7-15, 16-18, 19-64, 65-79, 80-89, 90+) är breda, men vilka som
fyller år över en gräns ett visst år är känt ur basårets ettårsåldrar: de som fyller 65 år under första prognosåret är
basårets 64-åringar, året därpå 63-åringarna. Funktionen låter basårets befolkning åldras ett år i taget, med rikets
dödsrisker som sjunker med rikets trend och med basårets födda, och läser av för varje år</p>
<ul><li>andelen av varje lager som fyller år över gränsen (kolumn 1-6): årets flöde ur lagret är andelen gånger lagret;</li>
<li>dödstalen i 65-79, 80-89 och 90+ i förhållande till 65+:s dödstal under basåret (kolumn 7-9): modellen multiplicerar dem
med kommunens kalibrerade dödstal för 65+;</li>
<li>uppdelningen av 65+ vid årets början (kolumn 10-12).</li></ul>
<p>Flyttningar ingår inte här; de är restflödet. De två första raderna gäller året före basåret och basåret och används när
restflödet kalibreras. Saknas ettårsåldrarna (bara nollor) antas jämn åldersfördelning och en stationär befolkning i 65+.</p></html>"));
    end ageProfile;

    function chainYear "Ett år i kontinuerlig tid för lagren 0-6, 7-15, 16-18, 19-64 och åldringskedjan 65-79, 80-89, 90+"
      input Real rates[5] "Dödstal per åldersgrupp, per år; 65+:s dödstal under basåret";
      input Real ageing[6] "Andel per år som åldras ur 0-6, 7-15, 16-18, 19-64, 65-79 och 80-89";
      input Real olderMortality[3] "Dödstal för 65-79, 80-89 och 90+ i förhållande till 65+:s";
      input Real birthsPerAdult = 0 "Födda per invånare 19-64 och år; 0 = födda räknas som ett inflöde utanför";
      output Real Phi[7, 7] "Invånare vid årets slut per invånare vid årets början";
      output Real Psi[7, 7] "Invånare vid årets slut per person och år i jämnt inflöde under året";
    protected
      Real A[7, 7] "der(x) = A*x utan inflöden";
      Real term[7, 7];
    algorithm
      A := zeros(7, 7);
      for i in 1:6 loop
        A[i, i] := -ageing[i] - (if i < 5 then rates[i] else rates[5]*olderMortality[i - 4]);
        A[i + 1, i] := ageing[i];
      end for;
      A[7, 7] := -rates[5]*olderMortality[3];
      A[1, 4] := birthsPerAdult;
      // Phi = exp(A), Psi = A^-1 (exp(A) - I) som serier; normen av A är under 1.
      Phi := identity(7);
      Psi := identity(7);
      term := identity(7);
      for k in 1:40 loop
        term := term*A/k;
        Phi := Phi + term;
        Psi := Psi + term/(k + 1);
      end for;
    end chainYear;

    function solve "Löser A*x = b med Gausselimination och radbyte; för små system utan standardbiblioteket"
      input Real A[:, size(A, 1)];
      input Real b[size(A, 1)];
      output Real x[size(A, 1)];
    protected
      Integer n = size(A, 1);
      Real M[size(A, 1), size(A, 1) + 1];
      Real row[size(A, 1) + 1];
      Integer pivot;
      Real factor;
    algorithm
      for i in 1:n loop
        M[i, 1:n] := A[i, :];
        M[i, n + 1] := b[i];
      end for;
      for i in 1:n loop
        pivot := i;
        for k in i + 1:n loop
          if abs(M[k, i]) > abs(M[pivot, i]) then
            pivot := k;
          end if;
        end for;
        row := M[i, :];
        M[i, :] := M[pivot, :];
        M[pivot, :] := row;
        for k in 1:n loop
          if k <> i then
            factor := M[k, i]/M[i, i];
            M[k, :] := M[k, :] - factor*M[i, :];
          end if;
        end for;
      end for;
      for i in 1:n loop
        x[i] := M[i, n + 1]/M[i, i];
      end for;
    end solve;

    function groupResponse "Fem gruppers folkmängd vid årets slut per person och år i jämnt restflöde per grupp; restflödet till 65+ fördelas på kedjan"
      input Real Psi[7, 7];
      input Real olderShares[3] "Fördelning av restflödet till 65+ på 65-79, 80-89 och 90+";
      output Real B[5, 5];
    algorithm
      for i in 1:5 loop
        for j in 1:5 loop
          B[i, j] := if i < 5 and j < 5 then Psi[i, j] elseif i < 5 then sum(Psi[i, 4 + l]*olderShares[l] for l in 1:3)
            elseif j < 5 then sum(Psi[4 + m, j] for m in 1:3) else sum(Psi[4 + m, 4 + l]*olderShares[l] for m in 1:3, l in 1:3);
        end for;
      end for;
    end groupResponse;

    function projectionResiduals "Restflöde per år som tar de fem grupperna till en befolkningsprojektion vid varje årsskifte"
      input Real p0[5] "Invånare per åldersgrupp vid basårets slut";
      input Real projected[:, 5] "Projektionens invånare per åldersgrupp vid varje årsskifte";
      input Boolean useProjection[size(projected, 1)] "Året följer projektionen; annars gäller fallback";
      input Real births0 "Födda under basåret";
      input Real rates[5] "Dödstal per åldersgrupp, per år";
      input Real profile[size(projected, 1), 12] "Prognosårens rader ur ageProfile";
      input Real olderShares[3] "Uppdelning av 65+ vid basårets slut";
      input Real fallback[5] "Restflöde de år projektionen inte gäller, personer per år";
      output Real residual[size(projected, 1), 5] "Restflöde per år och åldersgrupp, personer per år";
    protected
      Real Phi[7, 7];
      Real Psi[7, 7];
      Real x[7] "Lagren vid årets början: fyra grupper och åldringskedjan i 65+";
      Real y[7];
      Real r[5];
    algorithm
      x := cat(1, p0[1:4], p0[5]*olderShares);
      for t in 1:size(projected, 1) loop
        // Födda följer 19-64 som i modellen (births0/p0[4] per person och år).
        (Phi, Psi) := chainYear(rates, profile[t, 1:6], profile[t, 7:9], births0/p0[4]);
        y := Phi*x;
        if useProjection[t] then
          r := solve(groupResponse(Psi, olderShares), projected[t, :] - cat(1, y[1:4], {sum(y[5:7])}));
        else
          r := fallback;
        end if;
        residual[t, :] := r;
        // Kedjan går vidare med årets restflöde, så uppdelningen av 65+ följer åldrandet.
        x := y + Psi*cat(1, r[1:4], r[5]*olderShares);
      end for;
      annotation(Documentation(info = "<html><p>Restflödet år för år är det jämna inflöde som, med modellens födda, döda och
åldrande (<code>chainYear</code> med årets rad ur <code>ageProfile</code>), tar de fem grupperna från förra årsskiftet till
projektionens grupper vid årets slut. Restflödet till 65+ fördelas på kedjan efter basårets andelar.</p></html>"));
    end projectionResiduals;

    function calibratedMigrationRates "Restflöde per åldersgrupp och år som i kontinuerlig tid ger de två senaste årens förändring"
      input Real cohorts[3, 5] "Redovisade invånare per åldersgrupp, tre år i följd";
      input Real totals[3] "Redovisad folkmängd samma tre år";
      input Real births[2] "Födda de två senare åren";
      input Real rates[5] "Dödstal per åldersgrupp, per år";
      input Real profile[2, 12] "Raderna för året före basåret och basåret ur ageProfile";
      input Real olderShares[3] "Uppdelning av 65+ vid basårets slut";
      output Real residual[5] "Genomsnittligt restflöde per åldersgrupp, personer per år";
    protected
      Real Phi[7, 7];
      Real Psi[7, 7];
      Real from[5];
      Real x[7];
      Real inflow[5];
    algorithm
      residual := zeros(5);
      for k in 1:2 loop
        (Phi, Psi) := chainYear(rates, profile[k, 1:6], profile[k, 7:9]);
        from := reconcile(cohorts[k, :], totals[k]);
        // 65+ delas vid årets början som åldrarna ger (kolumn 10-12).
        x := Phi*cat(1, from[1:4], from[5]*profile[k, 10:12]);
        inflow := solve(groupResponse(Psi, olderShares), reconcile(cohorts[k + 1, :], totals[k + 1]) - cat(1, x[1:4], {sum(x[5:7])}));
        inflow[1] := inflow[1] - births[k];
        residual := residual + inflow/2;
      end for;
      annotation(Documentation(info = "<html><p>Restflödet är det jämna inflöde per år som, med de två årens åldrande och dödlighet
(<code>chainYear</code> med raderna ur <code>ageProfile</code>), tar varje åldersgrupp från ett årsskifte till nästa, med
årets födda som ett jämnt flöde in i 0-6 år. Eftersom åldrandet följer de faktiska årskullarna är restflödet i huvudsak
flyttningar, inte skillnaden mellan en jämn åldersfördelning och den verkliga.</p></html>"));
    end calibratedMigrationRates;

    function meanPreservingRates "Takt vid varje årsskifte så att årsmedlens ökning blir banans"
      input Real growth[:] "Ökning av årsmedlet per år, andel";
      output Real rate[size(growth, 1) + 1] "Takt (ln per år) vid början av varje år och vid det sista årets slut";
    protected
      Integer n = size(growth, 1);
      Real c[size(growth, 1)];
      Real d[size(growth, 1)];
      Real excess[size(growth, 1) + 1] "ln(årsmedel) minus årsmedlet av ln(nivå), för basåret och varje år";
      Real target;
      Real pivot;
      Real integral;
      Real a;
      Real b;
      Real u;
      constant Integer m = 16 "Delintervall i Simpsons regel";
    algorithm
      // En ökning på -100 % eller lägre stoppas av modellens egen kontroll (Assumptions); här hålls logaritmen definierad.
      // Takten går linjärt mellan årsskiftena. Mellan två årsmedel ökar ln(nivå) då med (förra + 4*årets + nästa takt)/6.
      // Det ska bli ln(1 + ökning) minus skillnaden mellan ln(medel) och medel(ln), som räknas om tre gånger:
      // ett tridiagonalt system. Basåret och tiden efter sista året växer med närmaste årsskiftes takt.
      excess := zeros(n + 1);
      for iteration in 1:4 loop
        if n == 1 then
          rate := fill(log(max(1e-9, 1 + growth[1])) - excess[2] + excess[1], 2);
        else
          for i in 1:n loop
            target := 6*(log(max(1e-9, 1 + growth[i])) - excess[i + 1] + excess[i]);
            if i == 1 then
              c[1] := 1/5;
              d[1] := target/5;
            else
              pivot := (if i == n then 5 else 4) - c[i - 1];
              c[i] := 1/pivot;
              d[i] := (target - d[i - 1])/pivot;
            end if;
          end for;
          rate[n] := d[n];
          for i in n - 1:-1:1 loop
            rate[i] := d[i] - c[i]*rate[i + 1];
          end for;
          rate[n + 1] := rate[n];
        end if;
        // År i (0 = basåret, med takten rate[1] hela året): ln(nivå) = a*u + (b - a)*u^2/2 efter andelen u av året.
        for i in 0:n loop
          a := rate[max(1, i)];
          b := rate[i + 1];
          integral := 0;
          for k in 0:m loop
            u := k/m;
            integral := integral + (if k == 0 or k == m then 1 elseif mod(k, 2) == 1 then 4 else 2)*exp(a*u + (b - a)*u^2/2);
          end for;
          excess[i + 1] := log(integral/(3*m)) - (a/3 + b/6);
        end for;
      end for;
      annotation(Documentation(info = "<html><p>En bana anger ökningen av årsmedlet (SKR:s timlön och PKV, eller reglagens
procent). I kontinuerlig tid behövs en takt för varje dag. Här väljs takterna vid årsskiftena så att nivån, när takten går
linjärt mellan dem, får just banans ökning mellan årsmedlen. Med samma ökning varje år är takten konstant. När ökningen
ändras mellan åren svänger takten mer än ökningen: 3 och 5 procent vartannat år ger takter mellan ungefär 1 och 7 procent.</p></html>"));
    end meanPreservingRates;

    function startLevel "Indexnivå vid basårets slut när basårets medel är 1 och nivån växte med takten rate"
      input Real rate "Takt per år";
      output Real level "Nivå vid årets slut";
    algorithm
      level := if abs(rate) < 1e-9 then 1 + rate/2 else rate/(1 - exp(-rate));
    end startLevel;

    package SCB "Rikets demografiska data från SCB och posttypen för en kommuns ettårsdata. Genereras av scripts/write_demography_modelica.py; redigera inte för hand"
      record DemographyYear "En kommun vid ett basårs slut, ettårsåldrar 0-100+ (index 1-101) per kön (1 män, 2 kvinnor)"
        Integer year "Basår";
        Units.Persons population[2, 101] "Befolkning vid årets slut";
        Real deathRisk[2, 101] "Rikets dödsrisk vid basåret: fem livslängdstabeller flyttade längs trenden och medelvärdesbildade, andel";
        Real mortalityImprovement[2, 101] "Årlig minskning av dödsrisken, rikets trend de tio åren fram till basåret";
        Real mortalityRatio[2] "Kommunens dödlighet i förhållande till rikets livslängdstabell, de fem åren fram till basåret";
        Real residualMigration[2, 101] "Genomsnittlig årlig förändring som inte förklaras av döda, åldrande och födda, de tre åren fram till basåret";
        Real shareBoys "Andel pojkar bland de födda, de tio åren fram till basåret";
        Real totalFertility "Kommunens summerade fruktsamhet basåret";
        Real totalFertilityMean5 "Kommunens genomsnittliga summerade fruktsamhet de fem åren fram till basåret";
        Units.Persons births "Födda under basåret";
        Units.Persons deaths "Döda under basåret";
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
      constant Real historicalFertilityProfile[4, 101] = {{0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0014802385, 0.0014802385, 0.0014802385, 0.0014802385, 0.0014802385, 0.019087286, 0.019087286, 0.019087286, 0.019087286, 0.019087286, 0.056854343, 0.056854343, 0.056854343, 0.056854343, 0.056854343, 0.073214874, 0.073214874, 0.073214874, 0.073214874, 0.073214874, 0.039528961, 0.039528961, 0.039528961, 0.039528961, 0.039528961, 0.0092769604, 0.0092769604, 0.0092769604, 0.0092769604, 0.0092769604, 0.00055733677, 0.00055733677, 0.00055733677, 0.00055733677, 0.00055733677, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
          {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0013156596, 0.0013156596, 0.0013156596, 0.0013156596, 0.0013156596, 0.018557379, 0.018557379, 0.018557379, 0.018557379, 0.018557379, 0.057270664, 0.057270664, 0.057270664, 0.057270664, 0.057270664, 0.072644147, 0.072644147, 0.072644147, 0.072644147, 0.072644147, 0.039732921, 0.039732921, 0.039732921, 0.039732921, 0.039732921, 0.0097161464, 0.0097161464, 0.0097161464, 0.0097161464, 0.0097161464, 0.00076308259, 0.00076308259, 0.00076308259, 0.00076308259, 0.00076308259, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
          {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0012632887, 0.0012632887, 0.0012632887, 0.0012632887, 0.0012632887, 0.017755074, 0.017755074, 0.017755074, 0.017755074, 0.017755074, 0.05652354, 0.05652354, 0.05652354, 0.05652354, 0.05652354, 0.073622808, 0.073622808, 0.073622808, 0.073622808, 0.073622808, 0.04030098, 0.04030098, 0.04030098, 0.04030098, 0.04030098, 0.0097542455, 0.0097542455, 0.0097542455, 0.0097542455, 0.0097542455, 0.00078006351, 0.00078006351, 0.00078006351, 0.00078006351, 0.00078006351, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
          {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0010353995, 0.0010353995, 0.0010353995, 0.0010353995, 0.0010353995, 0.017042116, 0.017042116, 0.017042116, 0.017042116, 0.017042116, 0.055190989, 0.055190989, 0.055190989, 0.055190989, 0.055190989, 0.07472366, 0.07472366, 0.07472366, 0.07472366, 0.07472366, 0.041199105, 0.041199105, 0.041199105, 0.041199105, 0.041199105, 0.0099202463, 0.0099202463, 0.0099202463, 0.0099202463, 0.0099202463, 0.00088848468, 0.00088848468, 0.00088848468, 0.00088848468, 0.00088848468, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}}
        "SCB:s historiska fruktsamhetstal för riket 2021–2024, jämnt fördelade inom moderns åldersgrupp och normaliserade";
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
      constant Real deathRisk[2, 101] = {{0.00207355, 0.000158727, 0.000108964, 0.000118402, 0.00012408, 5.43765e-05, 7.7932e-05, 5.59708e-05, 6.59338e-05, 7.129e-05, 4.48773e-05, 6.58185e-05, 6.2138e-05, 0.000108373, 0.000122362, 0.000185461, 0.000188406,
          0.000227493, 0.000304839, 0.000427119, 0.000416501, 0.000493011, 0.00053261, 0.000498113, 0.000468582, 0.000545598, 0.000526701, 0.000567414, 0.000632076, 0.000592982, 0.000567652, 0.000579602, 0.000589389, 0.000546025,
          0.000663152, 0.00067511, 0.000668891, 0.000653403, 0.00075867, 0.00079572, 0.000785959, 0.000882537, 0.000875566, 0.00099299, 0.00104689, 0.00115536, 0.001111, 0.00142655, 0.0013828, 0.00157736, 0.00172928,
          0.00199536, 0.00210802, 0.00215384, 0.00270772, 0.00296911, 0.00337198, 0.00355233, 0.00395854, 0.00444667, 0.00501413, 0.00542901, 0.00614793, 0.00694098, 0.00785558, 0.00880495, 0.0100161, 0.010752,
          0.012036, 0.0135399, 0.0146184, 0.0167047, 0.0179765, 0.0203771, 0.0224516, 0.0247097, 0.027234, 0.0310273, 0.0347532, 0.0383324, 0.0439892, 0.048778, 0.0545883, 0.0635745, 0.0716966,
          0.0833656, 0.0927464, 0.106106, 0.122933, 0.137902, 0.157393, 0.180744, 0.202134, 0.220083, 0.247034, 0.267403, 0.293084, 0.320441, 0.34945, 0.380056, 0.582038},
         {0.00171741, 0.000143013, 6.60244e-05, 8.71519e-05, 8.436e-05, 4.20045e-05, 7.05117e-05, 6.49583e-05, 4.81474e-05, 5.5313e-05, 6.72007e-05, 5.06738e-05, 6.47643e-05, 7.39224e-05, 0.000123183, 0.000115117, 8.99284e-05,
          0.000149104, 0.000161903, 0.000167761, 0.000221909, 0.000199453, 0.000268263, 0.000201955, 0.000188138, 0.000210645, 0.000195011, 0.000237797, 0.00018817, 0.000207599, 0.000286413, 0.000275227, 0.000325953, 0.00034484,
          0.000337756, 0.000395537, 0.000324316, 0.000393121, 0.00046955, 0.000508857, 0.000505913, 0.000586013, 0.000563506, 0.000572138, 0.000539368, 0.000724709, 0.000788537, 0.000857731, 0.000943543, 0.00118621, 0.0012976,
          0.00142095, 0.00149376, 0.0016292, 0.00169925, 0.00180679, 0.00226239, 0.00242411, 0.00273344, 0.00307284, 0.00332311, 0.00370312, 0.00401364, 0.00469699, 0.00503341, 0.00591905, 0.00624811, 0.00750551,
          0.00816209, 0.00916428, 0.0100345, 0.0111186, 0.0124575, 0.0136372, 0.0153954, 0.0171792, 0.019109, 0.0219212, 0.0251317, 0.0288019, 0.0313392, 0.0360721, 0.0409338, 0.046851, 0.0531295,
          0.0608351, 0.0690991, 0.0811102, 0.0920682, 0.104318, 0.123329, 0.138694, 0.15742, 0.178304, 0.195214, 0.215042, 0.237162, 0.261003, 0.28658, 0.313899, 0.480401}}
        "Rikets dödsrisk per ålder och kön 2025: fem livslängdstabeller flyttade längs trenden och medelvärdesbildade";
      constant Integer fertilityFirstYear = 2000 "Första året i tabellen över rikets summerade fruktsamhet";
      constant Real totalFertility[26] = {1.54, 1.57, 1.65, 1.71, 1.75, 1.77, 1.85, 1.88, 1.91, 1.93, 1.98, 1.9, 1.9,
          1.89, 1.88, 1.85, 1.85, 1.78, 1.75, 1.7, 1.66, 1.67, 1.52, 1.45, 1.43, 1.42}
        "Rikets summerade fruktsamhet 2000-2025 (SCB)";

      function totalFertilityMean5 "Rikets genomsnittliga summerade fruktsamhet de fem åren fram till ett år"
        input Integer year "Sista året";
        output Real mean "Medel av fem år";
      protected
        Integer last = min(max(year, fertilityFirstYear + 4), fertilityFirstYear + size(totalFertility, 1) - 1) - fertilityFirstYear + 1;
      algorithm
        mean := sum(totalFertility[last - 4:last])/5;
      end totalFertilityMean5;

      function combinedDeathRisk "Dödsrisk (rad 1) och dess årliga minskning (rad 2) per ålder för båda könen tillsammans"
        output Real combined[2, 101];
      protected
        Real alive[2] "Kvar i livet av lika många födda pojkar och flickor";
        Real weight "Männens andel vid åldern";
      algorithm
        alive := {1, 1};
        for a in 1:101 loop
          weight := alive[1]/(alive[1] + alive[2]);
          combined[1, a] := weight*deathRisk[1, a] + (1 - weight)*deathRisk[2, a];
          combined[2, a] := (weight*deathRisk[1, a]*mortalityImprovement[1, a] + (1 - weight)*deathRisk[2, a]*mortalityImprovement[2, a])/max(1e-12, combined[1, a]);
          alive := {alive[1]*(1 - deathRisk[1, a]), alive[2]*(1 - deathRisk[2, a])};
        end for;
      end combinedDeathRisk;

      function ages "Invånare per ettårsålder, båda könen"
        input Real population[2, 101] "Befolkning per ettårsålder och kön";
        output Real total[101];
      algorithm
        total := population[1, :] + population[2, :];
      end ages;

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

      constant Integer nationalLastOutcome = 2025 "Sista året med utfall i tabellen över rikets folkmängd";

      function nationalPopulationAt "Rikets folkmängd 31 december ett visst år, som den var känd ett givet år"
        input Integer year "Kalenderår";
        input Integer knownAt = nationalLastOutcome "Året då uppgiften ska vara känd: ett basår före sista utfallsåret ser inte senare utfall";
        output Real population "Folkmängd";
      protected
        Integer known = min(max(knownAt, nationalFirstYear + 1), nationalLastOutcome);
      algorithm
        assert(year >= nationalFirstYear and year < nationalFirstYear + size(nationalPopulation, 1), "Data.SCB.nationalPopulation saknar år " + String(year));
        if year <= known or known >= nationalLastOutcome then
          population := nationalPopulation[year - nationalFirstYear + 1];
        else
          // Efter det kända året: folkmängden fortsätter växa som det senast kända året. Senare utfall och den senaste
          // framskrivningen fanns inte då.
          population := nationalPopulation[known - nationalFirstYear + 1]*(nationalPopulation[known - nationalFirstYear + 1]/nationalPopulation[known - nationalFirstYear])^(year - known);
        end if;
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
    parameter Units.Persons p0[5] = Data.reconcile(base.cohorts[3, :], base.reportedPopulation[3]) "Invånare 0-6, 7-15, 16-18, 19-64 och 65+ vid basårets slut, avstämda mot redovisad folkmängd";
    parameter Units.Persons revenuePopulation0[5] = Data.reconcile(base.cohorts[2, :], base.reportedPopulation[2]) "Invånare per åldersgrupp vid slutet av året före basåret: den folkmängd basårets skatt och bidrag bygger på";
    parameter Real deathRates[5] = Data.mortality(p0, base.deaths) "Dödsrisk per åldersgrupp och år; 65+ ger basårets observerade antal döda";
    parameter Units.PersonsPerYear residualMigration[5] = Data.calibratedMigration(base.cohorts, base.reportedPopulation, base.births, deathRates) "Kalibrerat restflöde per åldersgrupp, personer per år (flyttningar och statistiska justeringar)";
    parameter Real olderShares[3] "Uppdelning av 65+ i 65-79, 80-89 och 90+ vid basårets slut för femgruppsdemografin; kommunens paket ger den ur SCB-data";
    parameter Real ageProfile[horizon + 2, 12] = Data.ageProfile(base.ages, births0, horizon, olderShares) "Åldrande och dödlighet år för år ur basårets ettårsåldrar (Data.ageProfile): rad 1-2 året före basåret och basåret, sedan prognosåren; kolumn 1-6 andel per år som åldras ur varje lager, 7-9 dödstal i 65-79, 80-89 och 90+ i förhållande till 65+:s, 10-12 uppdelningen av 65+ vid årets början";
    parameter Real migrationWeights[5] = {0.15, 0.12, 0.03, 0.65, 0.05} "Hur ett förändrat flyttnetto fördelas på åldersgrupperna; summerar till 1";
    parameter Units.Persons births0 = base.births[2] "Födda under basåret";
    parameter Units.PersonsPerYear migrationDelta = 0 "Förändrat årligt flyttnetto jämfört med kalibreringen, personer per år";
    parameter Real birthChange = 0 "Relativ förändring av antalet födda, andel (0,1 = tio procent fler)";
    // Verksamhet
    parameter Real educationWeights[3] = base.educationShares/sum(base.educationShares) "Vikter för 0-6, 7-15 och 16-18 år i utbildningsbehovet; basårets nettokostnader (Kolada), summerar till 1";
    parameter Real sectorCosts[3] = base.sectorShares/sum(base.sectorShares)*(base.payroll + base.pension + base.otherOperatingExpense - base.operatingRevenue + base.netCostRoundingAdjustment)
      "Kostnadsvikter för utbildning, äldreomsorg och övrig verksamhet, mnkr; basårets nettokostnad fördelad efter Kolada";
    parameter Real adjustment = 0.5 "Andel av glappet mellan behov och kapacitet som stängs varje år (0 = låst, 1 = direkt)";
    parameter Real fixedShare = 0.25 "Andel av kapaciteten som inte följer behovet";
    parameter Real serviceAdjustment[3] = fill(adjustment, 3) "Årlig kapacitetsanpassning för utbildning, äldreomsorg och övrigt";
    parameter Real serviceFixedShare[3] = fill(fixedShare, 3) "Fast andel av kapaciteten för utbildning, äldreomsorg och övrigt";
    parameter Real oldestRelativeCare = 1 "Omsorgskostnad per invånare 90+ jämfört med 80-89; Kolada saknar uppdelning, därför 1 tills data finns";
    parameter Real careWeights[3] = {base.careCostPerInhabitant[1], base.careCostPerInhabitant[2], base.careCostPerInhabitant[2]*oldestRelativeCare}
      "Äldreomsorgens kostnad per invånare 65-79, 80-89 och 90+, kr (Kolada)";
    // Drift: utfall i basåret
    parameter Units.Money payroll0 = base.payroll "Lönekostnader exklusive pensioner i basåret, mnkr";
    parameter Units.Money pension0 = base.pension "Pensionskostnad i basåret, mnkr";
    parameter Units.Money otherOperatingExpense0 = base.otherOperatingExpense "Övriga verksamhetskostnader i basåret, mnkr";
    parameter Units.Money operatingRevenue0 = base.operatingRevenue "Verksamhetens intäkter i basåret (avgifter, försäljning, riktade bidrag), mnkr";
    parameter Units.Money netCostRoundingAdjustment = base.netCostRoundingAdjustment "Avrundningsjustering som stämmer av delposterna mot redovisad nettokostnad, mnkr";
    // Intäkter, kapital och finansiering: utfall i basåret
    parameter Units.Money tax0 = base.tax "Skatteintäkter i basåret, mnkr";
    parameter Units.Money recurringTax0 = tax0 - base.priorYearSettlement "Basårets skatt utan korrigeringen av föregående års slutavräkning, mnkr; utgångspunkten för referensbanan";
    parameter Units.Money grants0 = base.grants "Generella statsbidrag och utjämning i basåret, mnkr";
    parameter Units.Money debt0 = base.debt "Låneskuld till banker och kreditinstitut vid basårets slut, mnkr";
    parameter Units.Money cash0 = base.cash "Kassa och bank vid basårets slut, mnkr";
    parameter Units.Money assets0 = base.assets "Byggnader, anläggningar, maskiner och inventarier vid basårets slut, exklusive pågående investeringar, mnkr";
    parameter Units.Money depreciation0 = base.depreciation "Avskrivningar i basåret, mnkr";
    parameter Units.Money financialIncome = base.financialIncome "Finansiella intäkter per år, mnkr";
    parameter Units.Money otherFinancialExpense = base.otherFinancialExpense "Finansiella kostnader utöver räntor per år, mnkr";
    // Tillväxt och priser
    parameter Real taxGrowth = 0.035 "Rikets skatteunderlag, årlig tillväxt, andel; inklusive rikets befolkningsökning, så kommunens skatt växer långsammare när kommunen krymper och riket växer";
    parameter Real grantGrowth = 0.02 "Generella bidrag i riket, årlig tillväxt, andel; kommunens del följer folkmängden i förhållande till rikets";
    parameter Real wageGrowth = 0.03 "Årlig löneökning, andel";
    parameter Real priceGrowth = 0.02 "Årlig prisökning för övriga kostnader, andel";
    parameter Real productivityGrowth = 0 "Årlig produktivitetsökning, andel; minskar lönekostnaden för samma volym";
    parameter Real costDrift = 0 "Kostnadsökning utöver demografi och pris, andel per år: höjd standard, nya uppgifter; 2010-2025 i medel -0,1 till 0,6 procent i länets kommuner (data/cost-residual.json), men standard 0: historikens medel gav för höga kostnader åtta år fram (data/long-hindcast.json)";
    parameter Real grantIncrease = 0 "Statens höjning av de generella bidragen utöver referensbanan, miljarder kronor i riket per år och år: från andra prognosåret, lika per invånare (riket 2021-2025 cirka 3,8)";
    parameter Boolean pensionFollowsPayroll = true "Pensionskostnaden följer lönesumman (löner, volym och produktivitet); false när pensionExpensePath anger kostnaden i mnkr";
    parameter Real pensionGrowth = 0 "Pensionskostnadens årliga ökning utöver lönesumman, andel; utan pensionFollowsPayroll dess årliga ökning";
    parameter Real operatingRevenueGrowth = 0.02 "Verksamhetsintäkternas årliga ökning, andel";
    parameter Real taxRate = base.taxRate "Kommunal skattesats i scenariot, procent";
    parameter Real taxRatePath[horizon] = fill(taxRate, horizon) "Kommunal skattesats per år, procent; standard taxRate varje år";
    parameter Real baseTaxRate = base.taxRate "Kommunal skattesats i basåret, procent";
    parameter Real equalisationOffset = 0.95 "Andel av en lokal avvikelse i skatteunderlaget som utjämningen tar tillbaka (förenklad)";
    parameter Real populationRevenueElasticity = 1 "Hur starkt skatt och bidrag följer kommunens folkmängd i förhållande till rikets (1 = proportionellt: en invånare färre ger cirka 77 000 kr mindre per år, 2025 års nivå)";
    parameter Real interestRate = if base.interestRate >= 0 then base.interestRate else base.interestExpense/max((base.openingDebt + base.debt)/2, 1e-9)
      "Genomsnittlig låneränta på ingående skuld, andel; årsredovisningens ränta när basåret har den (base.interestRate), annars basårets räntekostnad delad med skulden vid basårets början";
    parameter Units.Money investment = base.investment "Årliga investeringar, mnkr";
    // Årsvisa banor; första värdet gäller år 1
    parameter Units.PersonsPerYear residualMigrationPath[horizon, 5] = {residualMigration for i in 1:horizon} "Restflöde per år och åldersgrupp, personer; från en extern befolkningsbana eller kalibreringen";
    parameter Units.Money employerContributions0 = 0 "Sociala avgifter exklusive pensionskostnader, mnkr (del av payroll0)";
    parameter Real employerContributionRatePath[horizon] = fill(-1, horizon) "Sociala avgifter som andel av löner, eller -1 för oförändrad andel från basåret";
    parameter Real wageGrowthPath[horizon] = fill(wageGrowth, horizon) "Löneökning per år, andel";
    parameter Real priceGrowthPath[horizon] = fill(priceGrowth, horizon) "Prisökning per år, andel";
    parameter Units.Money pensionExpensePath[horizon] = {pension0*(1 + pensionGrowth)^i for i in 1:horizon} "Pensionskostnad per år, mnkr";
    parameter Units.Money pensionCashPaymentsPath[horizon] = pensionExpensePath "Pensionsutbetalningar per år, mnkr; illustrativa tills en egen källa finns";
    parameter Units.Money referenceTax[horizon] = {recurringTax0*(1 + taxGrowth)^i for i in 1:horizon} "Referensbana för skatteintäkter, mnkr; växer i rikets takt och skalas i Intäkter med kommunens folkmängd i förhållande till rikets (en importerad SKR-bana är redan kommunens egen)";
    parameter Units.Money referenceGrants[horizon] = {grants0*(1 + grantGrowth)^i for i in 1:horizon} "Referensbana för generella bidrag, mnkr; växer i rikets takt och skalas i Intäkter med kommunens folkmängd i förhållande till rikets (en importerad SKR-bana är redan kommunens egen)";
    parameter Units.Persons referencePopulation[horizon] = fill(sum(p0), horizon) "Folkmängd som referensbanan bygger på, personer";
    parameter Units.Persons nationalPopulation0 = Data.SCB.nationalPopulationAt(base.year - 1) "Rikets folkmängd vid slutet av året före basåret, personer (SCB)";
    parameter Real nationalPopulationPath[horizon] = {Data.SCB.nationalPopulationAt(base.year + i - 1, base.year) for i in 1:horizon}
      "Rikets folkmängd vid slutet av året före varje prognosår, personer (SCB: utfall, sedan framskrivning)";
    parameter Boolean importedRevenue = false "Sant när referensbanan är importerad från SKR";
    parameter Real ageIncomeWeights[5] = ones(5) "Relativ beskattningsbar inkomst per invånare i modellens åldersgrupper";
    parameter Real equalisationCountyRate(min=0) = 0 "Länsvis skattesats för inkomstutjämningsbidrag, procent";
    parameter Integer importedRevenueMode(min=0,max=2) = 0 "Importerad SKR: 0 proportionell, 1 publicerad bana, 2 justering per delpost";
    parameter Units.Persons novemberPopulation0 = sum(p0) "Folkmängd 1 november under basåret; sätt observation om känd";
    parameter Units.Money importedComponents[horizon, 3] = zeros(horizon,3) "Importerad skatt före avräkning, inkomstutjämning och regleringspost, mnkr";
    // Generella bidrag per del (används med grantsByComponent)
    parameter Boolean grantsByComponent = false "Bidragen räknas per del: inkomstutjämning, kostnads- och LSS-utjämning, regleringsbidrag, fastighetsavgift och övriga";
    parameter Units.Money grantComponents0[5] = base.grantComponents "Basårets inkomstutjämning, kostnadsutjämning, regleringsbidrag, LSS-utjämning och fastighetsavgift, mnkr";
    final parameter Units.MoneyPerPerson grantPerCapita0[4] = grantComponents0[1:4]*1e6/sum(revenuePopulation0) "Basårets inkomst-, kostnads-, reglerings- och LSS-del, kr per invånare";
    final parameter Real taxCapacityIndex[horizon] = {(referenceTax[i]/recurringTax0)/(nationalPopulationPath[i]/nationalPopulation0) for i in 1:horizon}
      "Rikets skatteunderlag per invånare i förhållande till basåret (referensbanans tillväxt delad med rikets folkmängd)";
    parameter Real incomeEqualisationPerCapitaPath[horizon] = {base.equalisationNextYear[1]*taxCapacityIndex[i]/taxCapacityIndex[1] for i in 1:horizon}
      "Inkomstutjämning per år vid relativ skattekraft incomeEqualisationCapacity, kr per invånare: året efter basåret enligt SCB, sedan i takt med rikets skatteunderlag per invånare";
    parameter Real incomeEqualisationCapacity = base.relativeTaxCapacity[2] "Den relativa skattekraft som incomeEqualisationPerCapitaPath gäller, andel";
    parameter Real incomeEqualisationComposition = (p0[4]/revenuePopulation0[4])/(sum(p0)/sum(revenuePopulation0))
      "Andelen 19-64 år vid basårets slut i förhållande till året före: SCB:s belopp för året efter basåret bygger redan på den";
    parameter Real equalisationGuarantee = 1.15 "Garantinivå i inkomstutjämningen, andel av rikets medelskattekraft (lag 2004:773, 4 §)";
    parameter Real relativeTaxCapacityPath[horizon] = fill(base.relativeTaxCapacity[2], horizon)
      "Skattekraft i förhållande till rikets medel per utjämningsår; året efter basåret är känt (SCB), sedan oförändrad om inget annat anges";
    parameter Units.MoneyPerPerson costEqualisationPerCapitaPath[horizon] = fill(base.equalisationNextYear[2], horizon) "Kostnadsutjämning per år, kr per invånare; året efter basåret enligt SCB, sedan oförändrad";
    parameter Real regulationPerCapitaPath[horizon] = fill(base.equalisationNextYear[3], horizon)
      "Regleringsbidrag per år, kr per invånare; året efter basåret enligt SCB, sedan oförändrat. Samma för alla kommuner; staten beslutar det i budgeten";
    parameter Units.MoneyPerPerson lssEqualisationPerCapitaPath[horizon] = fill(base.equalisationNextYear[4], horizon) "LSS-utjämning per år, kr per invånare; året efter basåret enligt SCB, sedan oförändrad";
    parameter Real propertyFeeGrowth = 0.035 "Fastighetsavgiftens årliga ökning, andel; taket följer inkomstbasbeloppet (3,8 procent om året 2020-2026)";
    parameter Units.Money propertyFeePath[horizon] = {grantComponents0[5]*(1 + propertyFeeGrowth)^i for i in 1:horizon} "Kommunal fastighetsavgift per år, mnkr";
    parameter Real otherGeneralGrantsPath[horizon] = fill(grants0 - sum(grantComponents0), horizon)
      "Övriga generella bidrag per år, mnkr; basårets belopp om inget annat anges (Motalas 51 mnkr 2025 är ett omklassat riktat statsbidrag; sätt noll för tillfälliga bidrag)";
    parameter Boolean revenueFromReference = false "Skatt och bidrag följer referensbanan exakt (till exempel budgetens belopp)";
    parameter Units.Money investmentPath[horizon] = fill(investment, horizon) "Årets investeringsutbetalningar, mnkr";
    parameter Boolean workingCapitalEnabled = false "Modellera kundfordringar, leverantörsskulder och bidragsförskott";
    parameter Units.Money receivables0(min=0) = 0 "Ingående kundfordringar, mnkr";
    parameter Units.Money payables0(min=0) = 0 "Ingående leverantörsskulder, mnkr";
    parameter Units.Money grantAdvances0(min=0) = 0 "Ingående förutbetalda bidrag, mnkr";
    parameter Real collectionDays(min=0,max=365) = 0 "Kundfordringar i dagar av verksamhetsintäkterna";
    parameter Real paymentDays(min=0,max=365) = 0 "Leverantörsskulder i dagar av övriga driftkostnader";
    parameter Units.Money firstYearGrantAdvance(min=0) = 0 "Bidrag inbetalt första året som hör till året efter, mnkr";
    parameter Boolean liquidityPolicy = true "Styr kassan mot likviditetsreserven; false = kassan ligger kvar på basårets nivå så länge kommunen har skuld";
    parameter Real reserveDays(min=0,max=365) = 30 "Likviditetsreserv i dagar av årets utbetalningar (drift, investering och ränta); standard 30 dagar (data/liquidity.json)";
    parameter Units.Duration reserveAdjustmentTime(min=0) = 3 "Tidskonstant för kassans väg från bokslutets nivå (i dagar av utbetalningarna) till reserveDays, år; 0 = reserven gäller från start";
    parameter Units.Money creditLine(min=0) = 0 "Outnyttjad checkkredit och bekräftade kreditlöften, mnkr; räknas av från reserven";
    parameter Real deferInvestmentShare(min=0,max=1) = 0 "Andel av första årets planerade investering som betalas året efter";
    parameter Real prefinanceShare(min=0,max=1) = 0 "Andel av uppskjuten betalning som lånas första året";
    parameter Integer constructionYears(min = 0, max = 5) = 0 "Årssteg mellan utbetalning och driftsättning för byggprojekt";
    parameter Real constructionShare(min = 0, max = 1) = 0.5 "Andel av årets investeringar som tar byggtid";
    parameter Units.Money projectOpeningStock(min=0) = 0 "Projektets ansamlade investering före första prognosåret, mnkr";
    parameter Units.Money projectPayment(min=0) = 0 "Projektets extra utbetalning första prognosåret, mnkr";
    parameter Integer projectOpeningStep(min=1) = 1 "Årssteg då projektet tas i bruk";
    parameter Real projectPlaces(min=0) = 0 "Projektets lokalkapacitet vid öppning, platser";
    parameter Units.Money workInProgress0(min = 0) = 0 "Pågående arbeten vid basårets slut utöver assets0, mnkr";
    parameter Real interestRatePath[horizon] = fill(interestRate, horizon) "Låneränta på ingående skuld per år, andel";
    parameter Units.Duration rateFixingYears(min = 0) = 0 "Genomsnittlig räntebindningstid för lånen, år (årsredovisningens avsnitt om finansiella risker); 0 = hela skulden till årets ränta. Med räntebindning är interestRatePath marknadsräntan för nya och omsatta lån";
    parameter Real rateShock = 0 "Plötslig höjning av marknadsräntan, andel (0,03 = tre procentenheter)";
    parameter Real rateShockTime = base.year + 1 "Datum för räntehöjningen som decimalår: 2026,0 = 1 januari 2026, 2026,5 = 1 juli 2026";
    parameter Real inflationShock = 0 "Extra inflation första prognosåret utöver prisbanan, andel (0,03 = tre procentenheter)";
    parameter Real inflationPersistence(min = 0, max = 1) = 0.5 "Andel av den extra inflationen som finns kvar året därpå";
    parameter Real inflationShockPath[horizon] = {inflationShock*inflationPersistence^(i - 1) for i in 1:horizon} "Extra inflation per år, andel";
    parameter Real inflationRevenuePassThrough = 0.3 "Andel av årets extra inflation som når verksamhetens intäkter (taxor, avgifter, riktade bidrag); 2022-2025 var medianen i länets 13 kommuner 0,05-0,5 med stor spridning (data/outcome-explanation*.json), ett antagande";
    parameter Real depositSpread(min = 0) = 0.005 "Skillnad mellan låneräntan och räntan på kassan, andel; ett antagande, ingen kommuns uppgift";
    parameter Real infrastructureShare(min = 0, max = 1) = base.infrastructureShare "Andel av övrig verksamhet som följer vägnätet och inte befolkningen (gator och vägar)";
    parameter Real networkGrowth = 0 "Vägnätets årliga tillväxt, andel; 0 = nätet är som i basåret";
    parameter Real inflationWagePassThrough = 0.4 "Andel av den fördröjda extra inflationen (medel av de två föregående åren) som når lönerna och skatteunderlaget; 2022-2025 cirka 0,35-0,45 (SKR:s arbetskraftsindex och rikets skatteunderlag mot decembercirkuläret 2021)";
    parameter Real inflationPensionPassThrough = 8 "Pensionskostnadens ökning över banan per enhet fördröjd extra inflation (uppräkning av pensionsskulden med prisbasbeloppet); går tillbaka när inflationen gör det. 2023-2025 cirka 7-10 i länets kommuner, med 2023 års pensionsavtal oseparerat";
    parameter Real inflationRateResponse = 0.5 "Höjning av marknadsräntan per procentenhet fördröjd extra inflation (medel av de två föregående åren); den betalda räntan steg 2023-2024 cirka 0,4 per enhet i länets kommuner";
    parameter Real inflationGrantCompensation = 0 "Andel av förra årets extra inflation som staten kompenserar i de generella bidragen; 0 = bidragen fasta i kronor";
    parameter Units.PersonsPerYear migrationDeltaPath[horizon] = fill(migrationDelta, horizon) "Förändrat flyttnetto per år, personer";
    parameter Real birthChangePath[horizon] = fill(birthChange, horizon) "Relativ förändring av födda per år, andel";
    final parameter Units.Duration life = assets0/depreciation0*Units.year "Sammanvägd avskrivningstid, år";
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
    assert(min({receivables0,payables0,grantAdvances0,collectionDays,paymentDays,firstYearGrantAdvance}) >= 0 and collectionDays <= 365 and paymentDays <= 365,
      "Ogiltiga antaganden för rörelsekapital");
    assert(reserveDays >= 0 and reserveDays <= 365 and creditLine >= 0 and deferInvestmentShare >= 0 and deferInvestmentShare <= 1 and prefinanceShare >= 0 and prefinanceShare <= 1,
      "Ogiltig likviditetsreserv eller andel för uppskjuten betalning och förfinansiering");
    assert(min(investmentPath) >= 0, "investmentPath får inte vara negativ; försäljningar av tillgångar modelleras inte");
    assert(births0 >= 0 and min(birthChangePath) >= -1, "births0 och birthChangePath får inte ge negativt antal födda");
    assert(min(pensionExpensePath) >= 0 and min(pensionCashPaymentsPath) >= 0, "pensionExpensePath och pensionCashPaymentsPath får inte vara negativa");
    assert(taxGrowth > -1 and grantGrowth > -1 and wageGrowth > -1 and priceGrowth > -1 and productivityGrowth > -1 and costDrift > -1 and abs(grantIncrease) <= 100 and pensionGrowth > -1 and operatingRevenueGrowth > -1, "Årliga tillväxttakter måste vara större än -1 (andelar, inte procent)");
// Årsbanorna ersätter skalärerna ovan och behöver samma gränser.
// Utan dem nollställer wageGrowthPath[k] = -1 lönerna och en negativ ränta bokförs som intäkt.
    assert(min(wageGrowthPath) > -1 and min(priceGrowthPath) > -1, "wageGrowthPath och priceGrowthPath måste vara större än -1 varje år (andelar, inte procent)");
    assert(base.interestRate >= 0 or base.openingDebt + base.debt > 0 or interestRate <= 0.3, "Basåret saknar låneskuld, så räntan kan inte härledas; ange base.interestRate ur årsredovisningen eller interestRate");
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
      Units.Persons p[5] "Invånare 0-6, 7-15, 16-18, 19-64 och 65+";
      Units.Persons older[3] "Invånare 65-79, 80-89 och 90+";
      Units.Persons population "Folkmängd";
      annotation(
        Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid)}));
    end Cohorts;

    connector DemographyDrivers "Årets demografiska antaganden"
      Units.PersonsPerYear residualMigration[5] "Restflöde per åldersgrupp, personer per år";
      Units.PersonsPerYear migrationDelta "Förändrat flyttnetto, personer per år";
      Real birthChange "Relativ förändring av antalet födda, andel";
      annotation(
        Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {90, 110, 130}, fillColor = {90, 110, 130}, fillPattern = FillPattern.Solid)}));
    end DemographyDrivers;

    connector CostDrivers "Årets kostnadsantaganden"
      Real wageGrowth "Löneökning, andel";
      Real priceGrowth "Prisökning, andel";
      Real wageRate "Lönenivåns takt vid årets början, ln per år; den kontinuerliga modellen går linjärt mot nästa";
      Real wageRateNext "Lönenivåns takt vid årets slut, ln per år";
      Real priceRate "Prisnivåns takt vid årets början, ln per år";
      Real priceRateNext "Prisnivåns takt vid årets slut, ln per år";
      Units.Money pensionExpense "Pensionskostnad, mnkr";
      Units.Money pensionCashPayments "Pensionsutbetalningar, mnkr";
      Real extraInflation "Årets extra inflation utöver prisbanan, andel";
      annotation(
        Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {90, 110, 130}, fillColor = {90, 110, 130}, fillPattern = FillPattern.Solid)}));
    end CostDrivers;

    connector RevenueReference "Årets referensvärden för skatt och bidrag (SKR eller illustrativa) och folkmängden de bygger på"
      Units.Money tax "Skatteintäkter, mnkr";
      Units.Money grants "Generella bidrag och utjämning, mnkr";
      Units.Persons population "Folkmängd, personer";
      Units.Persons nationalPopulation "Rikets folkmängd vid slutet av föregående år, personer";
      annotation(
        Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {90, 110, 130}, fillColor = {90, 110, 130}, fillPattern = FillPattern.Solid)}));
    end RevenueReference;


    connector TaxAndGrants "Skatteintäkter och generella bidrag, mnkr"
      Units.Money tax "Skatteintäkter, mnkr";
      Units.Money grants "Generella statsbidrag och utjämning, mnkr";
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
      parameter Units.PersonsPerYear residualMigrationPath[horizon, 5] "Restflöde per år och åldersgrupp, personer";
      parameter Units.PersonsPerYear migrationDeltaPath[horizon] "Förändrat flyttnetto per år, personer";
      parameter Real birthChangePath[horizon] "Relativ förändring av födda per år, andel";
      parameter Real wageGrowthPath[horizon] "Löneökning per år, andel";
      parameter Real priceGrowthPath[horizon] "Prisökning per år, andel";
      parameter Units.Money pensionExpensePath[horizon] "Pensionskostnad per år, mnkr";
      parameter Units.Money pensionCashPaymentsPath[horizon] "Pensionsutbetalningar per år, mnkr";
      parameter Units.Money referenceTax[horizon] "Referensbana för skatteintäkter, mnkr";
      parameter Units.Money referenceGrants[horizon] "Referensbana för generella bidrag, mnkr";
      parameter Units.Persons referencePopulation[horizon] "Folkmängd som referensbanan bygger på, personer";
      parameter Units.Persons nationalPopulationPath[horizon] "Rikets folkmängd vid slutet av året före varje prognosår, personer";
      parameter Units.Money investmentPath[horizon] "Investeringar per år, mnkr";
      parameter Real deferInvestmentShare = 0;
      parameter Real projectPayment = 0;
      final parameter Real deferredAmount = investmentPath[1]*deferInvestmentShare;
      parameter Real interestRatePath[horizon] "Låneränta per år, andel";
      parameter Real inflationShockPath[horizon] = zeros(horizon) "Extra inflation per år utöver prisbanan, andel";
      parameter Real inflationWagePassThrough = 0.4 "Andel av den fördröjda extra inflationen som når lönerna och skatteunderlaget";
      parameter Real inflationPensionPassThrough = 8 "Pensionskostnadens ökning över banan per enhet fördröjd extra inflation";
      parameter Real inflationRateResponse = 0.5 "Höjning av marknadsräntan per procentenhet fördröjd extra inflation";
      final parameter Real inflationDelayed[horizon] = {((if i > 1 then inflationShockPath[i - 1] else 0) + (if i > 2 then inflationShockPath[i - 2] else 0))/2 for i in 1:horizon}
        "Fördröjd extra inflation: medel av de två föregående årens, andel. Den når löner, pensioner och ränta";
      parameter Real inflationGrantCompensation = 0 "Andel av förra årets extra inflation som staten kompenserar i bidragen";
      final parameter Real inflationGrantFactor[horizon] = {product({1 + (if j == 1 then 0 else inflationGrantCompensation*inflationShockPath[j - 1]) for j in 1:i}) for i in 1:horizon} "Bidragens faktor mot referensbanan";
      final parameter Real inflationWage[horizon] = inflationWagePassThrough*inflationDelayed "Extra löneökning per år, andel";
      final parameter Real inflationTaxFactor[horizon] = {product({1 + inflationWage[j] for j in 1:i}) for i in 1:horizon} "Skatteunderlaget följer lönerna: faktor mot referensbanan";
      final parameter Real wageRate[horizon + 1] = Data.meanPreservingRates(wageGrowthPath + inflationWage) "Lönenivåns takt vid varje årsskifte i kontinuerlig tid, ln per år";
      final parameter Real priceRate[horizon + 1] = Data.meanPreservingRates(priceGrowthPath + inflationShockPath) "Prisnivåns takt vid varje årsskifte i kontinuerlig tid, ln per år";
      final parameter Real inflationPensionFactor[horizon] = {1 + inflationPensionPassThrough*inflationDelayed[i] for i in 1:horizon} "Pensionskostnadens faktor mot banan; tillbaka på 1 när inflationen är över";
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
      operations.wageGrowth = wageGrowthPath[calendar.pathIndex] + inflationWage[calendar.pathIndex];
      operations.priceGrowth = priceGrowthPath[calendar.pathIndex] + inflationShockPath[calendar.pathIndex];
      operations.wageRate = wageRate[calendar.pathIndex];
      operations.wageRateNext = wageRate[calendar.pathIndex + 1];
      operations.priceRate = priceRate[calendar.pathIndex];
      operations.priceRateNext = priceRate[calendar.pathIndex + 1];
      operations.pensionExpense = pensionExpensePath[calendar.pathIndex]*inflationPensionFactor[calendar.pathIndex];
      operations.pensionCashPayments = pensionCashPaymentsPath[calendar.pathIndex]*inflationPensionFactor[calendar.pathIndex];
      operations.extraInflation = inflationShockPath[calendar.pathIndex];
      revenue.tax = referenceTax[calendar.pathIndex]*inflationTaxFactor[calendar.pathIndex];
      revenue.grants = referenceGrants[calendar.pathIndex]*inflationGrantFactor[calendar.pathIndex];
      revenue.population = referencePopulation[calendar.pathIndex];
      revenue.nationalPopulation = nationalPopulationPath[calendar.pathIndex];
      investment = investmentPath[calendar.pathIndex] +
        (if calendar.pathIndex == 1 then projectPayment - deferredAmount elseif calendar.pathIndex == 2 then deferredAmount else 0);
      interestRate = interestRatePath[calendar.pathIndex] + inflationRateResponse*inflationDelayed[calendar.pathIndex];
      annotation(
        Icon(coordinateSystem(extent = {{-300, -25}, {300, 25}}), graphics = {Rectangle(extent = {{-300, -25}, {300, 25}}, lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-290, -20}, {290, 20}}, textString = "Scenario: årets antaganden", fontSize = 16, textColor = {35, 50, 65})}),
        Documentation(info = "<html><p>Plockar ut årets värden ur de årsvisa banorna. Beslutsparametrar (investeringar,
skattesats) och yttre antaganden (löner, priser, ränta, SKR:s referens för skatt och bidrag, befolkningsbanan) kommer in i
modellen här, så att varje komponent får dem genom en koppling.</p>
<p>En extra inflation (<code>inflationShockPath</code>) når kommunen i två steg. Priserna på övriga kostnader stiger samma
år. Löner, pensionskostnad och marknadsränta följer den fördröjda inflationen, medelvärdet av de två föregående årens
(<code>inflationDelayed</code>): avtal, prisbasbelopp och räntor sätts i efterhand. Lönerna och skatteunderlaget tar
<code>inflationWagePassThrough</code> av den (0,4), pensionskostnaden stiger <code>inflationPensionPassThrough</code> gånger
den över sin bana (8) och går tillbaka när inflationen är över, marknadsräntan stiger <code>inflationRateResponse</code> per
procentenhet (0,5). De generella bidragen är fasta i kronor tills staten beslutar annat;
<code>inflationGrantCompensation</code> anger hur stor del av förra årets extra inflation staten kompenserar. Talen är
satta efter 2022–2025 i länets 13 kommuner (<code>scripts/explain_outcome.py</code>), en enda period. Med noll extra
inflation är banorna oförändrade.</p></html>"));
    end Scenario;

    partial model DemographyBase "Det varje demografimodell ska ge: antaganden in, befolkning ut"
      outer Calendar calendar;
      Interfaces.DemographyDriversInput drivers "Årets demografiska antaganden" annotation(
        Placement(transformation(origin = {0, 130}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {0, 75}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      Interfaces.CohortsOutput cohorts "Befolkning per åldersgrupp vid årets slut" annotation(
        Placement(transformation(origin = {240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
      discrete output Units.Persons population "Folkmängd vid årets slut";
      discrete output Units.Persons births "Födda under året";
      discrete output Units.Persons deaths "Döda under året";
      discrete output Real migration "Flyttnetto och restflöden under året";
      discrete output Units.Persons populationBalance "Kontroll av befolkningsbalansen, personer; ska vara noll";
    equation
      assert(population > 0, "Scenariot tömmer befolkningen");
      assert(abs(populationBalance) < 1e-7*max(1, population), "Befolkningsbalansen stämmer inte");
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, pattern = LinePattern.Dash, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 8), Text(textColor = {35, 50, 65}, extent = {{-92, 0}, {92, 60}}, textString = "Demografi"), Text(textColor = {90, 110, 130}, extent = {{-92, -70}, {92, -10}}, textString = "basklass")}), Documentation(info = "<html><p>En demografimodell som bygger på denna klass kan ersätta en annan
(<code>redeclare</code>). Resten av modellen ser bara kopplingen <code>cohorts</code>.</p></html>"));
    end DemographyBase;

    package Fertility "Valbara födelsemodeller för CohortDemography"
      partial model Partial "Födda under året utifrån befolkningen vid årets början"
        outer Calendar calendar;
        input Units.Persons population[2, 101] "Befolkning vid årets början, ettårsåldrar 0-100+ per kön (1 män, 2 kvinnor)";
        parameter Units.Persons births0 "Födda under basåret";
        parameter Units.Persons population0[2, 101] "Befolkning vid basårets slut";
        output Units.Persons births "Födda under året";
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
      parameter Units.Persons reportedTotal = sum(data.population) "Folkmängd att starta från; ettårsåldrarna skalas till den";
      parameter Units.Persons population0[2, 101] = data.population*reportedTotal/sum(data.population) "Befolkning vid basårets slut, ettårsåldrar per kön";
      parameter Real mortalityRatio[2] = data.mortalityRatio "Kommunens dödlighet i förhållande till rikets livslängdstabell, män och kvinnor";
      parameter Boolean mortalityImprovement = true "Låt dödsriskerna fortsätta sjunka";
      parameter Real improvement[2, 101] = if mortalityImprovement then data.mortalityImprovement else zeros(2, 101)
        "Årlig minskning av dödsrisken; basårets historiska trend, eller Data.SCB.mortalityImprovement för SCB:s framskrivning";
      parameter Units.PersonsPerYear residualMigration[2, 101] = data.residualMigration "Kalibrerat restflöde per ålder och kön, personer per år";
      parameter Real migrationWeights[5] = {0.15, 0.12, 0.03, 0.65, 0.05} "Hur ett förändrat flyttnetto fördelas på 0-6, 7-15, 16-18, 19-64 och 65+";
      parameter Real observedDeltaShape[2,101] = zeros(2,101) "Andelar efter ålder och kön för ändrad inflyttning";
      parameter Boolean useObservedDeltaShape = false;
      parameter Real shareBoys = data.shareBoys "Andel pojkar bland de födda";
      replaceable Fertility.Constant fertility constrainedby Fertility.Partial(births0 = data.births, population0 = population0)
        "Födelsemodell" annotation(choicesAllMatching = true);
      discrete output Units.Persons p[2, 101](start = population0, each fixed = true) "Befolkning vid årets slut, ettårsåldrar per kön";
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
      discrete Units.Persons natural[2, 101](start = zeros(2, 101), each fixed = true) "Befolkning vid årets slut utan flyttningar";
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
        delta := drivers.migrationDelta*Units.year*(if useObservedDeltaShape then observedDeltaShape else deltaShape);
        for s in 1:2 loop
          natural[s, 1] := births*(if s == 1 then shareBoys else 1 - shareBoys);
          for a in 2:100 loop
            natural[s, a] := survivors[s, a - 1];
          end for;
          natural[s, 101] := survivors[s, 100] + survivors[s, 101];
        end for;
        // Restflödet kan inte ta bort fler än som finns i en ålder; det som inte kan tas bort räknas inte som flyttning.
        p := {{max(0, natural[s, a] + residualMigration[s, a]*Units.year + delta[s, a]) for a in 1:101} for s in 1:2};
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
      parameter Units.Persons p0[5] "Invånare 0-6, 7-15, 16-18, 19-64 och 65+ vid basårets slut";
      parameter Real deathRates[5] "Dödsrisk per åldersgrupp och år";
      parameter Real migrationWeights[5] "Fördelning av ett förändrat flyttnetto på åldersgrupperna";
      parameter Units.Persons births0 "Födda under basåret";
      extends DemographyBase(population(start = sum(p0), fixed = true), births(start = births0, fixed = true),
        deaths(start = 0, fixed = true), migration(start = 0, fixed = true), populationBalance(start = 0, fixed = true));
      discrete output Units.Persons p[5](start = p0, each fixed = true) "Invånare per åldersgrupp vid årets slut";
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
          p[i] := survivors[i] - ageOut[i] + (if i == 1 then births else ageOut[i - 1]) + (drivers.residualMigration[i] + drivers.migrationDelta*migrationWeights[i])*Units.year;
        end for;
        population := sum(p);
        migration := (sum(drivers.residualMigration) + drivers.migrationDelta*sum(migrationWeights))*Units.year;
        populationBalance := population - pre(population) - births + deaths - migration;
      end when;
      annotation(
        Icon(coordinateSystem(extent = {{-100, -75}, {100, 75}}), graphics = {Rectangle(extent = {{-100, -75}, {100, 75}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 30}, {95, 65}}, textString = "Demography", fontSize = 21, textColor = {40, 95, 140}), Text(extent = {{-95, -27}, {95, 25}}, textString = "Fem åldersgrupper", fontSize = 16, textColor = {35, 50, 65}), Text(extent = {{-95, -68}, {95, -35}}, textString = "%name", fontSize = 14, textColor = {40, 95, 140})}),
        Diagram(coordinateSystem(extent = {{-240, -130}, {240, 130}}), graphics = {Text(extent = {{-235, 85}, {235, 125}}, textString = "Demography", fontSize = 22, textColor = {35, 50, 65}), Rectangle(extent = {{-230, -55}, {-100, 65}}, lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{-65, -55}, {65, 65}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{100, -55}, {230, 65}}, lineColor = {50, 120, 90}, fillColor = {236, 248, 240}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-225, 35}, {-105, 60}}, textString = "Indata / antaganden", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, 35}, {60, 60}}, textString = "Tillstånd / årssteg", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, 35}, {225, 60}}, textString = "Utdata", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-225, -48}, {-105, 32}}, textString = "Antaganden\nFödda, flyttnetto\nDödsrisker", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, -48}, {60, 32}}, textString = "p[1:5]\nÅrets steg", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, -48}, {225, 32}}, textString = "Folkmängd\nFödda / döda\nFlyttnetto", fontSize = 13, textColor = {35, 50, 65}), Line(points = {{-100, 5}, {-65, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Line(points = {{65, 5}, {100, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Text(extent = {{-235, -125}, {235, -75}}, textString = "Befolkningsbalans per år i personer; restflödet innehåller statistiska justeringar.", fontSize = 12, textColor = {35, 50, 65})}),
        Documentation(info = "<html><p>Befolkningsbalans för fem breda åldersgrupper, i personer. Varje år åldras en jämnt fördelad
andel upp till nästa grupp, födda tillkommer i 0-6 och restflödet lägger till flyttningar och statistiska justeringar.
Används av sajten; CohortDemography är den finare modellen.</p></html>"));
    end Demography;



    model Revenue "Skatt och generella bidrag: referensbana, föregående års befolkning och förenklad utjämning"
      parameter Units.Persons p0[5] "Invånare per åldersgrupp som basårets skatt och bidrag bygger på (slutet av året före basåret)";
      parameter Units.Money tax0 "Skatteintäkter i basåret, mnkr";
      parameter Units.Money grants0 "Generella bidrag och utjämning i basåret, mnkr";
      parameter Real taxRate "Kommunal skattesats i scenariot, procent";
      parameter Real taxRatePath[horizon] = fill(taxRate, horizon) "Kommunal skattesats per år, procent";
      parameter Real baseTaxRate "Kommunal skattesats i basåret, procent";
      parameter Real equalisationOffset "Andel av en lokal avvikelse i skatteunderlaget som utjämningen tar tillbaka";
      parameter Real populationRevenueElasticity "Hur starkt skatt och bidrag följer folkmängden";
      parameter Boolean importedRevenue "Sant när referensbanan är importerad från SKR";
      parameter Boolean followReference = false "Skatt och bidrag följer referensbanan exakt, utan befolkningseffekt (till exempel budgetens belopp)";
      parameter Units.Persons nationalPopulation0 "Rikets folkmängd vid slutet av året före basåret, personer";
      parameter Boolean grantsByComponent = false "Bidragen räknas per del i stället för som en referensbana (gäller inte en importerad SKR-bana eller budgetens belopp)";
      parameter Integer horizon(min = 1) = 1 "Antal årssteg i bidragsbanorna";
      parameter Integer importedRevenueMode(min=0,max=2) = 0;
      parameter Real novemberPopulation0 = 0;
      parameter Real openingCohorts[5] = ones(5);
      parameter Real ageIncomeWeights[5] = ones(5);
      parameter Real equalisationCountyRate = 0;
      final parameter Real openingIncomePerPerson = sum(openingCohorts .* ageIncomeWeights)/sum(openingCohorts);
      parameter Real importedComponents[horizon, 3] = zeros(horizon,3);
      parameter Units.Money grantComponents0[5] = zeros(5) "Basårets inkomstutjämning, kostnadsutjämning, regleringsbidrag, LSS-utjämning och fastighetsavgift, mnkr";
      parameter Units.MoneyPerPerson incomeEqualisationPerCapita[horizon] = zeros(horizon) "Inkomstutjämning per år vid basårets relativa skattekraft, kr per invånare";
      parameter Real equalisationGuarantee = 1.15 "Garantinivå i inkomstutjämningen, andel av rikets medelskattekraft (lag 2004:773, 4 §)";
      parameter Real relativeTaxCapacity0 = 1 "Den relativa skattekraft som incomeEqualisationPerCapita gäller, andel";
      parameter Real incomeEqualisationComposition = 1 "Andelen i arbetsför ålder (composition) som incomeEqualisationPerCapita redan bygger på";
      parameter Real relativeTaxCapacity[horizon] = fill(relativeTaxCapacity0, horizon) "Kommunens skattekraft i förhållande till rikets medel per utjämningsår, före ålderseffekten, andel";
      parameter Units.MoneyPerPerson costEqualisationPerCapita[horizon] = zeros(horizon) "Kostnadsutjämning per år, kr per invånare (avgift negativ)";
      parameter Units.MoneyPerPerson regulationPerCapita[horizon] = zeros(horizon) "Regleringsbidrag per år, kr per invånare (avgift negativ)";
      parameter Units.MoneyPerPerson lssEqualisationPerCapita[horizon] = zeros(horizon) "LSS-utjämning per år, kr per invånare (avgift negativ)";
      parameter Units.Money propertyFee[horizon] = zeros(horizon) "Kommunal fastighetsavgift per år, mnkr";
      parameter Units.Money otherGeneralGrants[horizon] = zeros(horizon) "Övriga generella bidrag per år, mnkr";
      parameter Real grantIncrease = 0 "Statens höjning utöver referensbanan, miljarder kronor i riket per år och år från andra prognosåret";
      parameter Boolean novemberObserved = false "Folkmängden 1 november året före läses från ingångarna (kontinuerlig demografi) i stället för att interpoleras mellan årsskiftena";
      input Units.Persons novemberCohortsObserved[5] = openingCohorts "Invånare per åldersgrupp 1 november året före, med novemberObserved";
      input Units.Persons novemberPopulationObserved = novemberPopulation0 "Folkmängd 1 november året före, med novemberObserved";
      outer Calendar calendar;
      Interfaces.CohortsInput cohorts "Befolkning" annotation(
        Placement(transformation(origin = {0, 130}, extent = {{-18, -18}, {18, 18}}, rotation = -90), iconTransformation(origin = {0, 75}, extent = {{-9, -9}, {9, 9}}, rotation = -90)));
      Interfaces.RevenueReferenceInput reference "Årets referens för skatt och bidrag" annotation(
        Placement(transformation(origin = {-240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {-100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
      Interfaces.TaxAndGrantsOutput taxAndGrants "Skatt och bidrag till finansieringen" annotation(
        Placement(transformation(origin = {240, 0}, extent = {{-18, -18}, {18, 18}}, rotation = 0), iconTransformation(origin = {100, 0}, extent = {{-9, -9}, {9, 9}}, rotation = 0)));
      discrete output Units.Money recurringTaxAdjustment(start = 0, fixed = true) "Justering av skatt före slutavräkning, mnkr";
      discrete output Units.Money incomeEqualisationAdjustment(start = 0, fixed = true) "Befolkningseffekt på inkomstutjämning, mnkr";
      discrete output Units.Money regulationPopulationAdjustment(start = 0, fixed = true) "Befolkningseffekt på regleringsposten, mnkr";
      discrete output Units.Money stateIncrease(start = 0, fixed = true) "Statens höjning utöver referensbanan (grantIncrease), kommunens del, mnkr";
      discrete output Units.Money tax(start = tax0, fixed = true) "Skatteintäkter, mnkr: referensbana · kommunens folkmängd i förhållande till rikets · ålderseffekt · skattesats / basårets skattesats";
      discrete output Units.Money grants(start = grants0, fixed = true) "Generella statsbidrag och utjämning, mnkr: referensbana · kommunens folkmängd i förhållande till rikets, minus utjämning av ålderseffekten";
      discrete output Real grantParts[6](start = cat(1, grantComponents0, {grants0 - sum(grantComponents0)}), each fixed = true)
        "Bidragen per del med grantsByComponent: inkomstutjämning, kostnadsutjämning, regleringsbidrag, LSS-utjämning, fastighetsavgift och övriga, mnkr";
    protected
      discrete Real previousEndCohorts[5](start=openingCohorts,each fixed=true);
      discrete Real novemberCohorts[5](start=openingCohorts,each fixed=true);
      discrete Real previousEndPopulation(start=sum(openingCohorts),fixed=true);
      discrete Real ageTaxDelta(start=0,fixed=true) "Skatt vid basskattesats från ändrad ålderssammansättning";
      discrete Real novemberPopulation(start = novemberPopulation0, fixed = true);
      discrete Real popFactor(start = 1, fixed = true) "kommunens folkmängd i förhållande till rikets, jämfört med året före basåret";
      discrete Units.Money standardTax(start = 0, fixed = true) "Skatt vid basårets skattesats och sammansättning, mnkr";
      discrete Real composition(start = 1, fixed = true) "Andel 19-64 år i förhållande till basåret";
      discrete Real deviation(start = 0, fixed = true) "Skatteeffekt av en ändrad andel i arbetsför ålder, mnkr";
    equation
      taxAndGrants.tax = tax;
      taxAndGrants.grants = grants;
    algorithm
      when calendar.tick then
        // Referensbanans tillväxt gäller hela riket; kommunens del följer folkmängden i förhållande till rikets.
        novemberCohorts := if calendar.pathIndex == 1 then openingCohorts elseif novemberObserved then novemberCohortsObserved else
          pre(previousEndCohorts) + (pre(cohorts.p) - pre(previousEndCohorts))*10/12;
        novemberPopulation := if calendar.pathIndex == 1 then novemberPopulation0 elseif novemberObserved then novemberPopulationObserved else
          pre(previousEndPopulation) + (sum(pre(cohorts.p)) - pre(previousEndPopulation))*10/12;
        previousEndCohorts := pre(cohorts.p);
        previousEndPopulation := sum(pre(cohorts.p));
        popFactor := if importedRevenue then
          (if importedRevenueMode == 2 then novemberPopulation else sum(pre(cohorts.p)))/reference.population else ((sum(pre(cohorts.p))/sum(p0))/(reference.nationalPopulation/nationalPopulation0))^populationRevenueElasticity;
        standardTax := reference.tax*popFactor;
        composition := (pre(cohorts.p[4])/p0[4])/(sum(pre(cohorts.p))/sum(p0));
        deviation := if importedRevenue or followReference then 0 else standardTax*(composition - 1);
        ageTaxDelta := if importedRevenue and importedRevenueMode == 2 then
          importedComponents[calendar.pathIndex,1]*popFactor*
          (sum(novemberCohorts .* ageIncomeWeights)/sum(novemberCohorts)/openingIncomePerPerson - 1) else 0;
        recurringTaxAdjustment := if importedRevenue and importedRevenueMode == 2 then
          importedComponents[calendar.pathIndex,1]*(popFactor*taxRatePath[calendar.pathIndex]/baseTaxRate - 1) + ageTaxDelta*taxRatePath[calendar.pathIndex]/baseTaxRate else 0;
        incomeEqualisationAdjustment := if importedRevenue and importedRevenueMode == 2 then
          importedComponents[calendar.pathIndex,2]*(popFactor - 1) - ageTaxDelta*equalisationCountyRate/baseTaxRate else 0;
        regulationPopulationAdjustment := if importedRevenue and importedRevenueMode == 2 then
          importedComponents[calendar.pathIndex,3]*(popFactor - 1) else 0;
        tax := if importedRevenue and importedRevenueMode == 1 then reference.tax
          elseif importedRevenue and importedRevenueMode == 2 then reference.tax + recurringTaxAdjustment
          elseif followReference then reference.tax*taxRatePath[calendar.pathIndex]/baseTaxRate else (standardTax + deviation)*taxRatePath[calendar.pathIndex]/baseTaxRate;
        // Per del: belopp per invånare gånger folkmängden året före; inkomstutjämningen tar tillbaka ålderseffekten.
        // Inkomstutjämningen enligt lagen: bidrag = skattesats · (garantinivå - egen skattekraft) · rikets medelskattekraft · invånare,
        // med 95 procent av skattesatsen för bidrag och 85 procent för avgift (7 §). Banan per invånare gäller basårets relativa
        // skattekraft; en ändrad andel i arbetsför ålder (composition) ändrar den egna skattekraften.
        // Statens höjning: grantIncrease miljarder mer i riket för varje år efter det första, lika per invånare.
        stateIncrease := grantIncrease*1e3*(calendar.pathIndex - 1)*sum(pre(cohorts.p))/reference.nationalPopulation;
        grantParts := if grantsByComponent then {incomeEqualisationPerCapita[calendar.pathIndex]*sum(pre(cohorts.p))/1e6
          *Data.equalisationShare(equalisationGuarantee - relativeTaxCapacity[calendar.pathIndex]*composition/incomeEqualisationComposition)/Data.equalisationShare(equalisationGuarantee - relativeTaxCapacity0),
          costEqualisationPerCapita[calendar.pathIndex]*sum(pre(cohorts.p))/1e6, regulationPerCapita[calendar.pathIndex]*sum(pre(cohorts.p))/1e6 + stateIncrease,
          lssEqualisationPerCapita[calendar.pathIndex]*sum(pre(cohorts.p))/1e6, propertyFee[calendar.pathIndex], otherGeneralGrants[calendar.pathIndex]} else zeros(6);
        grants := if grantsByComponent and not importedRevenue and not followReference then sum(grantParts) else stateIncrease +
          (if importedRevenue and importedRevenueMode == 1 then reference.grants
          elseif importedRevenue and importedRevenueMode == 2 then
            reference.grants + incomeEqualisationAdjustment + regulationPopulationAdjustment
          elseif followReference then reference.grants
          else reference.grants*popFactor - equalisationOffset*deviation);
      end when;
      annotation(
        Icon(coordinateSystem(extent = {{-100, -75}, {100, 75}}), graphics = {Rectangle(extent = {{-100, -75}, {100, 75}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 30}, {95, 65}}, textString = "Intäkter", fontSize = 21, textColor = {40, 95, 140}), Text(extent = {{-95, -27}, {95, 25}}, textString = "Skatt / bidrag", fontSize = 16, textColor = {35, 50, 65}), Text(extent = {{-95, -68}, {95, -35}}, textString = "%name", fontSize = 14, textColor = {40, 95, 140})}),
        Diagram(coordinateSystem(extent = {{-240, -130}, {240, 130}}), graphics = {Text(extent = {{-235, 85}, {235, 125}}, textString = "Intäkter", fontSize = 22, textColor = {35, 50, 65}), Rectangle(extent = {{-230, -55}, {-100, 65}}, lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{-65, -55}, {65, 65}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Rectangle(extent = {{100, -55}, {230, 65}}, lineColor = {50, 120, 90}, fillColor = {236, 248, 240}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-225, 35}, {-105, 60}}, textString = "Indata / antaganden", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, 35}, {60, 60}}, textString = "Tillstånd / årssteg", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, 35}, {225, 60}}, textString = "Utdata", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-225, -48}, {-105, 32}}, textString = "Befolkning\nSkattesats\nReferensbanor", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{-60, -48}, {60, 32}}, textString = "Årets skatt\nÅrets bidrag", fontSize = 13, textColor = {35, 50, 65}), Text(extent = {{105, -48}, {225, 32}}, textString = "Skatt / bidrag", fontSize = 13, textColor = {35, 50, 65}), Line(points = {{-100, 5}, {-65, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Line(points = {{65, 5}, {100, 5}}, color = {70, 95, 120}, thickness = 0.5, arrow = {Arrow.None, Arrow.Filled}), Text(extent = {{-235, -125}, {235, -75}}, textString = "Förenklad befolkningseffekt och utjämning kring en referensbana (SKR eller illustrativ).", fontSize = 12, textColor = {35, 50, 65})}),
        Documentation(info = "<html><p>Skatt och generella bidrag utgår från en referensbana: SKR:s beräkning för kommunen när den
är importerad, annars en illustrativ tillväxt. Banan skalas med föregående års folkmängd. En ändrad andel i arbetsför ålder
ändrar skatten, och utjämningen tar tillbaka det mesta av avvikelsen via bidragen. En annan skattesats ändrar bara skatten.</p>
<p>Utjämningen är en förenklad känslighet, inte lagens beräkning av inkomst-, kostnads- och LSS-utjämning.</p>
<p>Inkomstutjämningen följer lagen (2004:773): kommunen får 95 procent av en skattesats gånger glappet mellan 115 procent av
rikets medelskattekraft och sin egen, och betalar 85 procent av den när den ligger över (<code>Data.equalisationShare</code>).
Den egna skattekraften i förhållande till riket (<code>relativeTaxCapacity</code>, SCB) är känd ett år framåt; en ändrad andel i
arbetsför ålder ändrar den. Sjunker Motalas relativa skattekraft från 87,6 till 86,6 procent ökar bidraget med cirka 3,6 procent.</p>
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



    annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Text(textColor = {35, 50, 65}, extent = {{-92, -40}, {92, 40}}, textString = "Delar")}));
  end Components;

  partial model Report "Utdata år för år för Continuous.Economy"
    Integer yearIndex "Antal beräknade år";
    Integer year "Kalenderår för det senast beräknade året (samma som tiden)";
    // Befolkning och verksamhet
    Units.Persons p[5] "Invånare 0-6, 7-15, 16-18, 19-64 och 65+ vid årets slut";
    Units.Persons population80Plus "Invånare 80 år och äldre vid årets slut";
    Units.Persons population "Folkmängd vid årets slut";
    Units.Persons births "Födda under året";
    Units.Persons deaths "Döda under året";
    Units.Money recurringTaxAdjustment "Justering av skatt före slutavräkning, mnkr";
    Units.Money incomeEqualisationAdjustment "Befolkningseffekt på inkomstutjämning, mnkr";
    Units.Money regulationPopulationAdjustment "Befolkningseffekt på regleringsposten, mnkr";
    Units.Money wages "Löner, mnkr";
    Units.Money employerContributions "Sociala avgifter exklusive pensioner, mnkr";
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
    Units.Money payroll "Lönekostnader exklusive pensioner, mnkr";
    Units.Money pensionExpense "Pensionskostnad, mnkr";
    Units.Money pensionCashPayments "Pensionsutbetalningar, mnkr";
    Units.Money otherOperatingExpense "Övriga verksamhetskostnader, mnkr";
    Units.Money operatingRevenue "Verksamhetens intäkter, mnkr";
    Units.Money cost "Verksamhetens nettokostnad exklusive avskrivningar, mnkr";
    // Intäkter, kapital och finansiering
    Units.Money tax "Skatteintäkter, mnkr; följer rikets skatteunderlag och kommunens folkmängd i förhållande till rikets (se komponenten Intäkter)";
    Units.Money grants "Generella statsbidrag och utjämning, mnkr; följer referensbanan och kommunens folkmängd i förhållande till rikets (se komponenten Intäkter)";
    Units.Money grantParts[6] "Bidragen per del med grantsByComponent: inkomstutjämning, kostnadsutjämning, regleringsbidrag, LSS-utjämning, fastighetsavgift och övriga, mnkr";
    Units.Money depreciation "Avskrivningar, mnkr";
    Units.Money assets "Tillgångar i bruk vid årets slut, mnkr";
    Units.Money commissioned "Anläggningar tagna i bruk under året, mnkr";
    Units.Money projectPaid "Projektutbetalning, mnkr";
    Units.Money projectCommissioned "Driftsatt projektkapital, mnkr";
    Units.Money projectWorkInProgress "Projektets pågående arbeten vid årets slut, mnkr";
    Real projectPlacesInUse "Förskoleplatser i bruk i projektet vid årets slut";
    Real missingProjectPlaces "Saknade projektplatser jämfört med öppningsplan";
    Units.Money workInProgress "Pågående arbeten vid årets slut, mnkr";
    Units.Money interest "Räntekostnader, mnkr";
    Units.Money result "Årets resultat, mnkr";
    Units.Money operatingCash "Kassaflöde från den löpande verksamheten, mnkr";
    Units.Money tradeReceivables "Kundfordringar vid årets slut, mnkr";
    Units.Money tradePayables "Leverantörsskulder vid årets slut, mnkr";
    Units.Money deferredGrants "Förutbetalda bidrag vid årets slut, mnkr";
    Units.Money workingCapitalCash "Kassaeffekt av ändrat rörelsekapital, mnkr";
    Units.Money borrowing "Nya lån under året, mnkr";
    Units.Money repayment "Amortering under året, mnkr";
    Units.Money debt "Låneskuld vid årets slut, mnkr";
    Units.Money cash "Kassa vid årets slut, mnkr";
    // Nyckeltal
    Real resultShare "Årets resultat i procent av skatter och bidrag (kommunens finansiella mål)";
    Real interestShare "Räntekostnader i procent av skatter och bidrag";
    Units.Money cumulativeInterest "Räntekostnader sammanlagt sedan basåret, mnkr";
    // Kontroller: ska vara noll
    Units.Persons populationBalance "Kontroll av befolkningsbalansen, personer";
    Units.Money assetBalance "Kontroll av tillgångsbalansen, mnkr";
    Units.Money cashBalance "Kontroll av kassabalansen, mnkr";
    Units.Money debtBalance "Kontroll av skuldbalansen, mnkr";
    Units.Money annualInvestment "Årets investeringsutbetalningar, mnkr";
    Units.Money outstandingDeferredInvestment "Uppskjuten betalning som återstår vid årets slut, mnkr";
    Units.Money prefinancing "Förfinansiering genom lån under året, mnkr";
    Real annualInterestRate "Årets låneränta, andel";
    annotation(Documentation(info = "<html><p>Variablerna som en körning redovisar per år. Pengar i mnkr, befolkning i personer.</p></html>"));
  end Report;


  package Continuous "Kontinuerlig tid: lager och flöden för pengar och befolkning; bara årliga beslut och bokslutet är händelser"
    connector StockPort "Koppling till ett lager: nivån och flödet in i den anslutna komponenten"
      Units.Money level "Lagrets nivå, mnkr (skulder negativa)";
      flow Real rate "Flöde in i komponenten, mnkr per år";
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(extent = {{-100, -100}, {100, 100}}, lineColor = {155, 95, 35}, fillColor = {155, 95, 35}, fillPattern = FillPattern.Solid)}));
    end StockPort;

    model Clock "Bokslut: ett steg vid varje års slut"
      parameter Integer horizon(min = 1) "Antal år";
      parameter Integer baseYear "Basår; simuleringen startar vid tiden baseYear (bokslutet 31 december)";
      Boolean yearEnd "Sant i det ögonblick ett år avslutas";
      discrete Integer yearsClosed(start = 0, fixed = true) "Antal avslutade år";
    equation
      yearEnd = sample(baseYear + 1, 1) and time <= baseYear + horizon;
      when yearEnd then
        yearsClosed = pre(yearsClosed) + 1;
      end when;
      annotation(defaultComponentName = "clock", defaultComponentPrefixes = "inner",
        Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(extent = {{-90, -90}, {90, 90}}, lineColor = {90, 110, 130}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid), Line(points = {{0, 0}, {0, 70}}, color = {90, 110, 130}, thickness = 1), Line(points = {{0, 0}, {50, -20}}, color = {90, 110, 130}, thickness = 1), Text(extent = {{-100, -100}, {100, -140}}, textString = "bokslut")}),
        Documentation(info = "<html><p>Deklareras en gång som <code>inner</code>. <code>yearEnd</code> är sant vid varje årsskifte
efter basåret; flödena lägger då ihop årets belopp och lagren visar sin nivå vid årets slut.</p></html>"));
    end Clock;

    partial model Annualised "Ett flöde med årssumma"
      outer Clock clock;
      parameter Units.Money annual0 = 0 "Basårets belopp, mnkr (visas vid starttiden)";
      input Units.MoneyRate rate "Flöde, mnkr per år";
      discrete output Units.Money annual(start = annual0, fixed = true) "Årets belopp, mnkr";
      Units.Money accumulated(start = 0, fixed = true) "Summerat sedan årets början, mnkr";
    equation
      der(accumulated) = rate;
      when clock.yearEnd then
        annual = accumulated;
        reinit(accumulated, 0);
      end when;
    end Annualised;

    model Stock "Lager: nivån ändras med summan av flödena in"
      outer Clock clock;
      parameter Units.Money level0 "Nivå vid basårets slut, mnkr (skulder negativa)";
      StockPort port annotation(Placement(transformation(extent = {{-10, -110}, {10, -90}}), iconTransformation(extent = {{-10, -110}, {10, -90}})));
      Units.Money level(start = level0, fixed = true) "Nivå, mnkr";
      discrete output Units.Money closing(start = level0, fixed = true) "Nivå vid årets slut, mnkr";
    equation
      port.level = level;
      der(level) = port.rate;
      when clock.yearEnd then
        closing = level;
      end when;
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-80, -90}, {80, 60}}, lineColor = {155, 95, 35}, fillColor = {255, 246, 230}, fillPattern = FillPattern.Solid), Rectangle(extent = {{-80, -90}, {80, -20}}, lineColor = {155, 95, 35}, fillColor = {230, 190, 140}, fillPattern = FillPattern.Solid), Text(extent = {{-100, 100}, {100, 65}}, textString = "%name")}),
        Documentation(info = "<html><p>Ett konto i balansräkningen. Nivån ändras bara genom flöden: <code>der(level)</code> är summan
av flödena in genom kopplingen. Skulder har negativ nivå, så att summan av alla lager är kommunens nettoförmögenhet och
ändras bara med flöden över gränsen, alltså med årets resultat.</p></html>"));
    end Stock;

    model Transfer "Flöde från ett lager till ett annat"
      extends Annualised;
      StockPort from annotation(Placement(transformation(extent = {{-110, -10}, {-90, 10}}), iconTransformation(extent = {{-110, -10}, {-90, 10}})));
      StockPort to annotation(Placement(transformation(extent = {{90, -10}, {110, 10}}), iconTransformation(extent = {{90, -10}, {110, 10}})));
    equation
      from.rate = rate;
      to.rate = -rate;
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Line(points = {{-90, 0}, {90, 0}}, color = {155, 95, 35}, thickness = 1, arrow = {Arrow.None, Arrow.Filled}), Polygon(points = {{-20, 30}, {20, 30}, {-20, -30}, {20, -30}, {-20, 30}}, lineColor = {155, 95, 35}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid), Text(extent = {{-100, 80}, {100, 40}}, textString = "%name")}));
    end Transfer;

    model Inflow "Flöde in över gränsen: intäkt"
      extends Annualised;
      StockPort to annotation(Placement(transformation(extent = {{90, -10}, {110, 10}}), iconTransformation(extent = {{90, -10}, {110, 10}})));
    equation
      to.rate = -rate;
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(extent = {{-100, -30}, {-40, 30}}, lineColor = {90, 110, 130}), Line(points = {{-40, 0}, {90, 0}}, color = {40, 120, 80}, thickness = 1, arrow = {Arrow.None, Arrow.Filled}), Text(extent = {{-100, 80}, {100, 40}}, textString = "%name")}));
    end Inflow;

    model Outflow "Flöde ut över gränsen: kostnad"
      extends Annualised;
      StockPort from annotation(Placement(transformation(extent = {{-110, -10}, {-90, 10}}), iconTransformation(extent = {{-110, -10}, {-90, 10}})));
    equation
      from.rate = rate;
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(extent = {{40, -30}, {100, 30}}, lineColor = {90, 110, 130}), Line(points = {{-90, 0}, {40, 0}}, color = {170, 60, 50}, thickness = 1, arrow = {Arrow.None, Arrow.Filled}), Text(extent = {{-100, 80}, {100, 40}}, textString = "%name")}));
    end Outflow;

    model Meter "Mäter flödet genom en punkt, som en amperemeter"
      outer Clock clock;
      StockPort a "Sidan där de uppmätta flödena ansluter" annotation(Placement(transformation(extent = {{-110, -10}, {-90, 10}}), iconTransformation(extent = {{-110, -10}, {-90, 10}})));
      StockPort b "Lagret" annotation(Placement(transformation(extent = {{90, -10}, {110, 10}}), iconTransformation(extent = {{90, -10}, {110, 10}})));
      output Units.MoneyRate rate "Flöde från a till b, mnkr per år";
      discrete output Units.Money annual(start = 0, fixed = true) "Årets belopp, mnkr";
    protected
      Real accumulated(start = 0, fixed = true);
    equation
      a.level = b.level;
      a.rate + b.rate = 0;
      rate = a.rate;
      der(accumulated) = rate;
      when clock.yearEnd then
        annual = accumulated;
        reinit(accumulated, 0);
      end when;
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(extent = {{-60, -60}, {60, 60}}, lineColor = {90, 110, 130}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid), Line(points = {{-90, 0}, {-60, 0}}, color = {155, 95, 35}), Line(points = {{60, 0}, {90, 0}}, color = {155, 95, 35}), Line(points = {{0, 0}, {35, 35}}, color = {90, 110, 130}, thickness = 1), Text(extent = {{-100, 100}, {100, 65}}, textString = "%name")}));
    end Meter;

    partial model DemographyBase "Det en demografi i kontinuerlig tid ska ge: befolkningen just nu och årets födda, döda och flyttnetto"
      outer Components.Calendar calendar;
      outer Clock clock;
      parameter Units.Persons births0Shown = 0 "Födda som visas vid starttiden (basåret)";
      parameter Units.Persons deaths0Shown = 0 "Döda som visas vid starttiden (basåret)";
      Interfaces.DemographyDriversInput drivers "Årets demografiska antaganden" annotation(
        Placement(transformation(origin = {0, 120}, extent = {{-20, -20}, {20, 20}}, rotation = -90), iconTransformation(origin = {0, 110}, extent = {{-10, -10}, {10, 10}}, rotation = -90)));
      Interfaces.CohortsOutput cohorts "Befolkningen just nu, efter ålder just nu" annotation(
        Placement(transformation(origin = {120, 0}, extent = {{-20, -20}, {20, 20}}), iconTransformation(origin = {110, 0}, extent = {{-10, -10}, {10, 10}})));
      Units.PersonsPerYear birthRate "Födda per år just nu";
      Units.PersonsPerYear deathRate "Döda per år just nu";
      Units.PersonsPerYear migrationRate "Flyttnetto och restflöden per år just nu";
      discrete output Units.Persons births(start = births0Shown, fixed = true) "Födda under året";
      discrete output Units.Persons deaths(start = deaths0Shown, fixed = true) "Döda under året";
      discrete output Units.Persons migration(start = 0, fixed = true) "Flyttnetto och restflöden under året";
      discrete output Units.Persons populationBalance(start = 0, fixed = true) "Kontroll: årets förändring av folkmängden minus födda, döda och flyttnetto, personer; ska vara noll";
    protected
      Units.Persons accumulated[3](each start = 0, each fixed = true) "Födda, döda och flyttnetto sedan årets början";
      discrete Units.Persons closing(fixed = false) "Folkmängd vid förra årsskiftet";
    initial equation
      closing = cohorts.population;
    equation
      der(accumulated[1]) = birthRate;
      der(accumulated[2]) = deathRate;
      der(accumulated[3]) = migrationRate;
      when clock.yearEnd then
        births = accumulated[1];
        deaths = accumulated[2];
        migration = accumulated[3];
        closing = cohorts.population;
        populationBalance = cohorts.population - pre(closing) - accumulated[1] + accumulated[2] - accumulated[3];
        reinit(accumulated, zeros(3));
      end when;
      assert(cohorts.population > 0, "Scenariot tömmer befolkningen");
      assert(abs(populationBalance) < 1e-6*max(1, cohorts.population), "Befolkningsbalansen stämmer inte");
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, pattern = LinePattern.Dash, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 8), Text(textColor = {35, 50, 65}, extent = {{-92, 0}, {92, 60}}, textString = "Demografi"), Text(textColor = {90, 110, 130}, extent = {{-92, -70}, {92, -10}}, textString = "basklass")}),
        Documentation(info = "<html><p>Basklass för demografin i <code>Economy</code>. Befolkningen är lager; födda, döda och flyttnetto
är flöden som summeras till årets antal vid bokslutet. Befolkningsbalansen kontrolleras varje år.</p></html>"));
    end DemographyBase;

    model Demography "Fem åldersgrupper som lager: födda, döda, åldrande och flyttningar är flöden"
      parameter Units.Persons p0[5] "Invånare 0-6, 7-15, 16-18, 19-64 och 65+ vid basårets slut";
      parameter Units.Rate deathRates[5] "Dödstal per åldersgrupp: döda per person och år";
      parameter Real migrationWeights[5] "Fördelning av ett förändrat flyttnetto på åldersgrupperna";
      parameter Units.Persons births0 "Födda under basåret";
      parameter Real olderShares[3] "Uppdelning av 65+ i 65-79, 80-89 och 90+ vid basårets slut (SCB)";
      parameter Integer horizon "Antal år i banorna";
      parameter Units.Rate ageingRatePath[horizon, 6] "Andel per år som åldras ur 0-6, 7-15, 16-18, 19-64, 65-79 och 80-89, år för år (Data.ageProfile)";
      parameter Real olderMortalityPath[horizon, 3] "Dödstal i 65-79, 80-89 och 90+ i förhållande till deathRates[5], år för år (Data.ageProfile)";
      extends DemographyBase(births0Shown = births0);
      Units.Persons p[5] "Invånare per åldersgrupp; 65+ är summan av åldringskedjan";
      Units.Persons young[4](start = p0[1:4], each fixed = true) "Lager: 0-6, 7-15, 16-18 och 19-64 år";
      Units.Persons older[3](start = p0[5]*olderShares, each fixed = true) "Lager: 65-79, 80-89 och 90+ år, en åldringskedja";
      Units.PersonsPerYear born "Födda per år";
      Units.PersonsPerYear died[5] "Döda per år och åldersgrupp";
      Units.PersonsPerYear ageing[4] "Åldras upp till nästa grupp, personer per år";
      Units.PersonsPerYear moved[5] "Flyttnetto och restflöde per år och åldersgrupp";
      Units.PersonsPerYear olderAgeing[2] "Går från 65-79 till 80-89 och från 80-89 till 90+, personer per år";
      Units.PersonsPerYear olderDied[3] "Döda per år i 65-79, 80-89 och 90+";
      Units.PersonsPerYear olderMoved[3] "Flyttnetto och restflöde per år i 65-79, 80-89 och 90+";
      Units.Rate ageingRate[6] "Årets andel som åldras ur 0-6, 7-15, 16-18, 19-64, 65-79 och 80-89";
      Units.Rate olderRate[3] "Årets dödstal i 65-79, 80-89 och 90+";
    protected
      Units.PersonsPerYear trend "Födda per år utan scenariots förändring";
    equation
      // Skalära ekvationer, så att enhetskontrollen (scripts/check_units.py) prövar dem; vektorekvationer prövas inte.
      trend = births0/Units.year*p[4]/p0[4];
      born = trend*(1 + drivers.birthChange);
      for i in 1:5 loop
        moved[i] = drivers.residualMigration[i] + drivers.migrationDelta*migrationWeights[i];
      end for;
      for i in 1:4 loop
        p[i] = young[i];
        died[i] = deathRates[i]*young[i];
        ageing[i] = ageingRate[i]*young[i];
      end for;
      der(young[1]) = born - ageing[1] - died[1] + moved[1];
      for i in 2:4 loop
        der(young[i]) = ageing[i - 1] - ageing[i] - died[i] + moved[i];
      end for;
      // Vilka som fyller år över en gräns följer årskullarna: årets andel ur basårets ettårsåldrar (Data.ageProfile).
      for i in 1:6 loop
        ageingRate[i] = ageingRatePath[calendar.pathIndex, i];
      end for;
      // 65+ är en åldringskedja: in från 19-64, uppåt med årets andelar och ut genom död med dödstal som stiger med åldern
      // och sjunker med rikets trend. Flyttningarna till 65+ fördelas efter basårets andelar. Gruppens döda är kedjans.
      for j in 1:2 loop
        olderAgeing[j] = ageingRate[4 + j]*older[j];
      end for;
      for j in 1:3 loop
        olderRate[j] = deathRates[5]*olderMortalityPath[calendar.pathIndex, j];
        olderDied[j] = olderRate[j]*older[j];
        olderMoved[j] = moved[5]*olderShares[j];
      end for;
      der(older[1]) = ageing[4] - olderAgeing[1] - olderDied[1] + olderMoved[1];
      der(older[2]) = olderAgeing[1] - olderAgeing[2] - olderDied[2] + olderMoved[2];
      der(older[3]) = olderAgeing[2] - olderDied[3] + olderMoved[3];
      p[5] = older[1] + older[2] + older[3];
      died[5] = olderDied[1] + olderDied[2] + olderDied[3];
      birthRate = born;
      deathRate = sum(died);
      migrationRate = sum(moved);
      cohorts.p = p;
      cohorts.older = older;
      cohorts.population = sum(p);
      assert(min(p) >= 0, "Scenariot tömmer en åldersgrupp");
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -60}, {100, 60}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 25}, {95, -25}}, textString = "Demografi")}),
        Documentation(info = "<html><p>Fem åldersgrupper som lager. Under året:</p>
<ul><li>födda = födda<sub>0</sub> · (19-64)/(19-64)<sub>0</sub> · (1 + förändring), in i 0-6 år;</li>
<li>döda = dödstal · invånare i gruppen; dödstalet är döda per person och år (<code>Data.deathRatesPerYear</code>);</li>
<li>åldrande = årets andel · invånare i lagret; andelen kommer ur basårets ettårsåldrar (<code>Data.ageProfile</code>): de som
fyller 65 år första prognosåret är basårets 64-åringar, och så vidare;</li>
<li>flyttnetto = kalibrerat restflöde plus scenariots ändring, jämnt under året.</li></ul>
<p>65+ är en åldringskedja av tre lager, 65-79 → 80-89 → 90+ (<code>older</code>), och <code>p[5]</code> är deras summa.
In kommer de som fyller 65 och flyttningar i basårets proportioner. Dödstalen stiger med åldern och sjunker med rikets
trend (<code>olderMortalityPath</code> gånger kommunens kalibrerade dödstal för 65+). Gruppens döda är kedjans: när 80+ växer
dör fler. Kalibreringen räknar med samma kedja (<code>Data.chainYear</code>).</p>
<p>Årsmodellen flyttar 1/bredd av de överlevande en gång per år; här sker det jämnt. Restflödet är kalibrerat för de
kontinuerliga flödena (<code>Data.calibratedMigrationRates</code>), så att basårens förändring återskapas.</p></html>"));
    end Demography;

    model CohortDemography "Ettårsåldrar 0-100+ per kön som lager: födda, döda och flyttningar är flöden; åldern räknas vid årets slut"
      extends DemographyBase(births0Shown = data.births, deaths0Shown = data.deaths);
      parameter Data.SCB.DemographyYear data "Basår: befolkning, dödsrisk och kalibrering (SCB); kommunens paket ger ett värde";
      parameter Units.Persons reportedTotal = sum(data.population) "Folkmängd att starta från; ettårsåldrarna skalas till den";
      parameter Units.Persons population0[2, 101] = data.population*reportedTotal/sum(data.population) "Befolkning vid basårets slut, ettårsåldrar per kön";
      parameter Real mortalityRatio[2] = data.mortalityRatio "Kommunens dödlighet i förhållande till rikets livslängdstabell, män och kvinnor";
      parameter Boolean mortalityImprovement = true "Låt dödsriskerna fortsätta sjunka";
      parameter Real improvement[2, 101] = if mortalityImprovement then data.mortalityImprovement else zeros(2, 101) "Årlig minskning av dödsrisken";
      parameter Units.PersonsPerYear residualMigration[2, 101] = data.residualMigration "Kalibrerat restflöde per ålder vid årets slut och kön, personer per år";
      parameter Real migrationWeights[5] = {0.15, 0.12, 0.03, 0.65, 0.05} "Hur ett förändrat flyttnetto fördelas på 0-6, 7-15, 16-18, 19-64 och 65+";
      parameter Real observedDeltaShape[2, 101] = zeros(2, 101) "Andelar efter ålder och kön för ändrad inflyttning";
      parameter Boolean useObservedDeltaShape = false;
      parameter Real shareBoys = data.shareBoys "Andel pojkar bland de födda";
      parameter Units.Persons outflowFloor = 1 "Under så många personer i en ålder minskar utflyttningen i proportion, så att lagret inte blir negativt";
      replaceable Components.Fertility.Constant fertility constrainedby Components.Fertility.Partial(births0 = data.births, population0 = population0)
        "Födelsemodell" annotation(choicesAllMatching = true);
      Units.Persons p[2, 101](start = population0, each fixed = true) "Invånare efter ålder vid årets slut (födelseår) och kön";
      Units.Rate mortality[2, 101] "Dödstal per år för varje födelseårsgrupp";
      Units.PersonsPerYear moved[2, 101] "Flyttnetto och restflöde per år";
      Units.PersonsPerYear born "Födda per år";
      Units.Persons ageNow[2, 101] "Invånare efter ålder just nu, med födelsedagarna jämnt fördelade över året";
      Real share "Andel av året som gått";
    protected
      parameter Integer width[5] = {7, 9, 3, 46, 36} "Antal ettårsåldrar i varje åldersgrupp";
      parameter Integer group[101] = {if a <= 7 then 1 elseif a <= 16 then 2 elseif a <= 19 then 3 elseif a <= 65 then 4 else 5 for a in 1:101};
      parameter Real deltaShape[2, 101] = {{0.5*migrationWeights[group[a]]/width[group[a]] for a in 1:101} for s in 1:2};
      discrete Units.Duration labelYearEnd(fixed = false) "Det årsslut som åldrarna i p avser";
      Units.PersonsPerYear wanted[2, 101] "Restflöde och scenariots ändring innan gränsen för tomma åldrar";
    initial equation
      labelYearEnd = time;
    equation
      // Ålder vid årets slut är födelseåret: vid årsskiftet byter varje grupp etikett, ingen person flyttas.
      when calendar.tick then
        labelYearEnd = time + Units.year;
        for s in 1:2 loop
          reinit(p[s, 1], 0);
          for a in 2:100 loop
            reinit(p[s, a], pre(p[s, a - 1]));
          end for;
          reinit(p[s, 101], pre(p[s, 100]) + pre(p[s, 101]));
        end for;
      end when;
      share = 1 - (labelYearEnd - time)/Units.year;
      // Dödsrisken gäller åldern vid förra årsskiftet; de födda under året har ingen.
      mortality = {cat(1, {0}, {-log(max(1e-6, 1 - min(1, data.deathRisk[s, a]*mortalityRatio[s]*exp(-improvement[s, a]*calendar.yearIndex)))) for a in 1:100}) for s in 1:2}/Units.year;
      wanted = residualMigration + drivers.migrationDelta*(if useObservedDeltaShape then observedDeltaShape else deltaShape);
      // Fruktsamheten läser åldern vid årets början: födelseårsgruppen a + 1 var a år då.
      fertility.population = cat(2, p[:, 2:101], zeros(2, 1));
      born = fertility.births/Units.year*(1 + drivers.birthChange);
      // Skalära ekvationer, så att enhetskontrollen prövar dem.
      for s in 1:2 loop
        for a in 1:101 loop
          moved[s, a] = if wanted[s, a] >= 0 then wanted[s, a] else wanted[s, a]*noEvent(min(1, p[s, a]/outflowFloor));
        end for;
        der(p[s, 1]) = born*(if s == 1 then shareBoys else 1 - shareBoys) + moved[s, 1];
        for a in 2:101 loop
          der(p[s, a]) = -mortality[s, a]*p[s, a] + moved[s, a];
        end for;
      end for;
      ageNow = cat(2, p[:, 1:1] + (1 - share)*p[:, 2:2], share*p[:, 2:100] + (1 - share)*p[:, 3:101], share*p[:, 101:101]);
      birthRate = born;
      deathRate = sum(mortality .* p);
      migrationRate = sum(moved);
      cohorts.p = {sum(ageNow[:, 1:7]), sum(ageNow[:, 8:16]), sum(ageNow[:, 17:19]), sum(ageNow[:, 20:65]), sum(ageNow[:, 66:101])};
      cohorts.older = {sum(ageNow[:, 66:80]), sum(ageNow[:, 81:90]), sum(ageNow[:, 91:101])};
      cohorts.population = sum(p);
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -60}, {100, 60}}, lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 25}, {95, -25}}, textString = "Ettårsåldrar")}),
        Documentation(info = "<html><p>Som <code>Components.CohortDemography</code>, men födda, döda och flyttningar är flöden under året.
Lagren är födelseårsgrupper, märkta med åldern vid årets slut, som i SCB:s statistik. Vid årsskiftet byter varje grupp etikett
(<code>reinit</code>); ingen person flyttas och folkmängden ändras inte. Det är den enda händelsen.</p>
<p>Under året räknas åldern just nu med födelsedagarna jämnt fördelade: andelen <code>share</code> av en födelseårsgrupp har
fyllt år. Åldersgrupperna till verksamheten och intäkterna går därför jämnt mellan årsskiftena. Dödsrisken
<code>q</code> blir dödstalet -ln(1 - q), så att en grupp utan flyttningar har överlevnaden 1 - q på ett år. Fruktsamheten räknas på kvinnorna just nu, efter deras ålder vid årets början.</p></html>"));
    end CohortDemography;

    model Services "Verksamhetens behov och kapacitet per sektor; kapaciteten följer behovet kontinuerligt"
      parameter Real educationWeights[3] "Vikter för 0-6, 7-15 och 16-18 år i utbildningsbehovet";
      parameter Units.Money sectorCosts[3] "Kostnadsvikter för utbildning, äldreomsorg och övrigt, mnkr";
      parameter Real adjustment[3] "Andel av glappet mellan behov och kapacitet som stängs på ett år (0 = låst, 1 = direkt)";
      parameter Real fixedShare[3] "Fast andel av kapaciteten per sektor";
      parameter Real careWeights[3] = {1, 1, 1} "Äldreomsorgens kostnad per invånare 65-79, 80-89 och 90+";
      parameter Real plannedProjectPlaces = 0;
      parameter Real infrastructureShare = 0 "Andel av övrig verksamhet som följer vägnätet och inte befolkningen";
      parameter Real networkGrowth = 0 "Vägnätets årliga tillväxt, andel";
      final parameter Real adjustmentRate[3] = {-log(max(1e-6, 1 - adjustment[i])) for i in 1:3} "Anpassningstakt per år; stänger samma andel av ett konstant glapp på ett år som adjustment";
      outer Clock clock;
      input Real projectPlacesInUse;
      output Real missingProjectPlaces = if clock.yearsClosed > 0 then max(0, plannedProjectPlaces - projectPlacesInUse) else 0 "Projektplatser som saknas jämfört med öppningsplanen";
      Interfaces.CohortsInput cohorts "Befolkning just nu" annotation(
        Placement(transformation(extent = {{-120, -20}, {-80, 20}}), iconTransformation(extent = {{-110, -10}, {-90, 10}})));
      Real capacity[3](each start = 1, each fixed = true) "Kapacitet för utbildning, äldreomsorg och övrigt, index (basår = 1)";
      Real demand[3] "Behov för utbildning, äldreomsorg och övrigt, index (basår = 1)";
      Real educationIndex "Utbildningsbehov, index (basår = 1)";
      Real careIndex "Äldreomsorgsbehov viktat efter ålder, index (basår = 1)";
      Real network(start = 1, fixed = true) "Vägnätet: lager, index (basår = 1); växer bara med networkGrowth";
      Interfaces.SignalOutput serviceVolume "Verksamhetens volym: kostnadsviktad kapacitet, index (basår = 1)" annotation(
        Placement(transformation(extent = {{80, -20}, {120, 20}}), iconTransformation(extent = {{90, -10}, {110, 10}})));
    protected
      parameter Real careBase(fixed = false) "Viktat antal äldre vid start";
      parameter Units.Persons cohorts0[5](each fixed = false) "Invånare per åldersgrupp vid start";
    initial equation
      careBase = careWeights*cohorts.older;
      cohorts0 = cohorts.p;
    equation
      educationIndex = sum({educationWeights[i]*cohorts.p[i]/cohorts0[i] for i in 1:3});
      careIndex = careWeights*cohorts.older/careBase;
      // Gator och vägar ligger kvar när invånarna blir färre: den delen av övrig verksamhet följer vägnätet.
      der(network) = log(1 + networkGrowth)*network;
      demand = {educationIndex, careIndex, infrastructureShare*network + (1 - infrastructureShare)*sum(cohorts.p)/sum(cohorts0)};
      der(capacity) = adjustmentRate .* (fixedShare + (ones(3) - fixedShare) .* demand - capacity);
      serviceVolume = sum(sectorCosts .* capacity)/sum(sectorCosts);
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -60}, {100, 60}}, lineColor = {35, 115, 85}, fillColor = {230, 245, 238}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 25}, {95, -25}}, textString = "Verksamhet")}),
        Documentation(info = "<html><p>Verksamhetens behov följer befolkningen under året, och kapaciteten närmar sig
behovet kontinuerligt: <code>der(capacity) = takt · (mål - capacity)</code>. Takten är vald så att ett konstant glapp
stängs med andelen <code>adjustment</code> på ett år.</p></html>"));
    end Services;

    model OperatingAccounts "Driftens kostnader och intäkter som flöden; löne-, pris- och kostnadsnivåer växer kontinuerligt"
      parameter Units.Persons population0 "Folkmängd vid basårets slut";
      parameter Units.Money payroll0 "Lönekostnader exklusive pensioner i basåret, mnkr";
      parameter Units.Money employerContributions0 = 0 "Sociala avgifter exklusive pensioner, mnkr";
      parameter Integer horizon = 1;
      parameter Real employerContributionRatePath[horizon] = fill(-1, horizon) "Sociala avgifter som andel av löner";
      parameter Units.Money pension0 "Pensionskostnad i basåret, mnkr";
      parameter Units.Money otherOperatingExpense0 "Övriga verksamhetskostnader i basåret, mnkr";
      parameter Units.Money operatingRevenue0 "Verksamhetens intäkter i basåret, mnkr";
      parameter Units.Money netCostRoundingAdjustment "Avrundningsjustering, mnkr";
      parameter Real operatingRevenueGrowth "Verksamhetsintäkternas årliga ökning, andel";
      parameter Real inflationRevenuePassThrough = 0 "Andel av årets extra inflation som når verksamhetens intäkter";
      parameter Boolean pensionFollowsPayroll = false "Pensionskostnaden följer lönesumman; banan anger då kostnaden vid basårets lönesumma";
      parameter Real productivityGrowth "Årlig produktivitetsökning, andel";
      parameter Real costDrift = 0 "Kostnadsökning utöver demografi och pris, andel per år";
      outer Components.Calendar calendar;
      outer Clock clock;
      Interfaces.CohortsInput cohorts "Befolkning just nu" annotation(
        Placement(transformation(extent = {{-120, 20}, {-80, 60}}), iconTransformation(extent = {{-110, 30}, {-90, 50}})));
      Interfaces.SignalInput serviceVolume "Verksamhetens volym, index" annotation(
        Placement(transformation(extent = {{-120, -20}, {-80, 20}}), iconTransformation(extent = {{-110, -10}, {-90, 10}})));
      Interfaces.CostDriversInput drivers "Årets löne-, pris- och pensionsantaganden" annotation(
        Placement(transformation(extent = {{-120, -60}, {-80, -20}}), iconTransformation(extent = {{-110, -50}, {-90, -30}})));
      output Units.MoneyRate wagesRate "Löner, mnkr per år";
      output Units.MoneyRate employerContributionsRate "Sociala avgifter exklusive pensioner, mnkr per år";
      output Units.MoneyRate pensionExpenseRate "Pensionskostnad, mnkr per år";
      output Units.MoneyRate pensionCashPaymentsRate "Pensionsutbetalningar, mnkr per år";
      output Units.MoneyRate otherOperatingExpenseRate "Övriga verksamhetskostnader, mnkr per år";
      output Units.MoneyRate operatingRevenueRate "Verksamhetens intäkter, mnkr per år";
      Real level[5](each fixed = false) "Löne-, pris-, taxe-, produktivitets- och standardnivå just nu, index (basårets medel = 1)";
      Units.Rate growth[5] "Nivåernas tillväxttakt just nu";
      Real payrollIndex "Lönesumman just nu i förhållande till basårets, när pensionskostnaden följer den; annars 1";
      Real share "Andel av året som gått";
      discrete output Real wageIndex(start = 1, fixed = true) "Lönenivå, årets medel, index (basår = 1)";
      discrete output Real priceIndex(start = 1, fixed = true) "Prisnivå för övriga kostnader, årets medel, index (basår = 1)";
      discrete output Real revenueIndex(start = 1, fixed = true) "Taxor och avgifter, årets medel, index (basår = 1)";
      discrete output Real productivity(start = 1, fixed = true) "Produktivitet, årets medel, index (basår = 1)";
      discrete output Real standard(start = 1, fixed = true) "Kostnadsnivå utöver demografi och pris, årets medel, index (basår = 1)";
      discrete output Units.Money wages(start = payroll0 - employerContributions0, fixed = true) "Löner, mnkr";
      discrete output Units.Money employerContributions(start = employerContributions0, fixed = true) "Sociala avgifter exklusive pensioner, mnkr";
      discrete output Units.Money payroll(start = payroll0, fixed = true) "Lönekostnader exklusive pensioner, mnkr";
      discrete output Units.Money pensionExpense(start = pension0, fixed = true) "Pensionskostnad, mnkr";
      discrete output Units.Money pensionCashPayments(start = pension0, fixed = true) "Pensionsutbetalningar, mnkr";
      discrete output Units.Money otherOperatingExpense(start = otherOperatingExpense0, fixed = true) "Övriga verksamhetskostnader, mnkr";
      discrete output Units.Money operatingRevenue(start = operatingRevenue0, fixed = true) "Verksamhetens intäkter, mnkr";
      discrete output Units.Money cost(start = payroll0 + pension0 + otherOperatingExpense0 - operatingRevenue0 + netCostRoundingAdjustment, fixed = true) "Verksamhetens nettokostnad exklusive avskrivningar, mnkr";
    protected
      Units.Money accumulated[7](each start = 0, each fixed = true) "Löner, sociala avgifter, pensionskostnad, pensionsutbetalningar, övriga kostnader, verksamhetsintäkter och avrundning sedan årets början";
      Units.Duration levelSum[5](each start = 0, each fixed = true) "Nivåerna summerade över tiden sedan årets början";
      Units.Rate rateNow[5] "Takten för det pågående årets ökning";
      Units.Rate rateNext[5] "Takten för nästa års ökning";
    initial equation
      level = {Data.startLevel(rateNow[i]*Units.year) for i in 1:5};
    equation
      share = (time - (calendar.baseYear + calendar.pathIndex)*Units.year)/Units.year;
      // Taxor och avgifter följer sin egen ökning och en del av årets extra inflation.
      rateNow = {drivers.wageRate, drivers.priceRate, log(1 + operatingRevenueGrowth + inflationRevenuePassThrough*drivers.extraInflation), log(1 + productivityGrowth), log(1 + costDrift)}/Units.year;
      rateNext = {drivers.wageRateNext, drivers.priceRateNext, log(1 + operatingRevenueGrowth + inflationRevenuePassThrough*drivers.extraInflation), log(1 + productivityGrowth), log(1 + costDrift)}/Units.year;
      // Banans ökning gäller årsmedlet. Takterna vid årsskiftena är valda så att årsmedlen får den ökningen (Data.meanPreservingRates).
      growth = rateNow + (rateNext - rateNow)*share;
      der(level) = growth .* level;
      wagesRate = (payroll0 - employerContributions0)/Units.year*level[1]*serviceVolume*level[5]/level[4];
      employerContributionsRate = if employerContributionRatePath[calendar.pathIndex] < 0 then employerContributions0/Units.year*level[1]*serviceVolume*level[5]/level[4] else wagesRate*employerContributionRatePath[calendar.pathIndex];
      // Pensionskostnaden är en andel av lönesumman: följer lönerna, volymen och produktiviteten. Med en given bana i mnkr
      // (pensionFollowsPayroll = false) gäller banan.
      payrollIndex = if pensionFollowsPayroll then (wagesRate + employerContributionsRate)*Units.year/payroll0 else 1;
      pensionExpenseRate = drivers.pensionExpense/Units.year*payrollIndex;
      pensionCashPaymentsRate = drivers.pensionCashPayments/Units.year*payrollIndex;
      otherOperatingExpenseRate = otherOperatingExpense0/Units.year*level[2]*serviceVolume*level[5];
      operatingRevenueRate = operatingRevenue0/Units.year*level[3]*cohorts.population/population0;
      der(accumulated[1]) = wagesRate;
      der(accumulated[2]) = employerContributionsRate;
      der(accumulated[3]) = pensionExpenseRate;
      der(accumulated[4]) = pensionCashPaymentsRate;
      der(accumulated[5]) = otherOperatingExpenseRate;
      der(accumulated[6]) = operatingRevenueRate;
      der(accumulated[7]) = netCostRoundingAdjustment/Units.year;
      der(levelSum) = level;
      when clock.yearEnd then
        wageIndex = levelSum[1]/Units.year;
        priceIndex = levelSum[2]/Units.year;
        revenueIndex = levelSum[3]/Units.year;
        productivity = levelSum[4]/Units.year;
        standard = levelSum[5]/Units.year;
        wages = accumulated[1];
        employerContributions = accumulated[2];
        payroll = accumulated[1] + accumulated[2];
        pensionExpense = accumulated[3];
        pensionCashPayments = accumulated[4];
        otherOperatingExpense = accumulated[5];
        operatingRevenue = accumulated[6];
        cost = accumulated[1] + accumulated[2] + accumulated[3] + accumulated[5] - accumulated[6] + accumulated[7];
        reinit(accumulated, zeros(7));
        reinit(levelSum, zeros(5));
      end when;
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -60}, {100, 60}}, lineColor = {35, 115, 85}, fillColor = {230, 245, 238}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 25}, {95, -25}}, textString = "Drift")}),
        Documentation(info = "<html><p>Kostnaderna är flöden som följer verksamhetens volym och befolkningen under året. Löne-, pris-,
taxe-, produktivitets- och standardnivån är lager som växer kontinuerligt: <code>der(nivå) = takt · nivå</code>.</p>
<p>Banornas årliga ökning (till exempel SKR:s timlön och PKV) är ökningen av årsmedlet. Takten går linjärt mellan
årsskiftena, och takterna där är valda så att årsmedlet ökar som banan anger
(<a href=\"modelica://Kommunekonomi.Data.meanPreservingRates\">Data.meanPreservingRates</a>). Löne- och prisnivåns årsmedel följer
därför banan också när ökningen ändras mellan åren. Priset är att takten inom året
svänger mer än de årliga ökningarna när de ändras mycket. Nivån vid basårets slut sätts så att basårets medel är 1 om
basåret växte med takten vid första årsskiftet.</p>
<p>Pensionskostnaden och pensionsutbetalningarna är årsbanor och flyter jämnt under året. Årets belopp är summan av
flödena; <code>wageIndex</code> och de andra indexen i utdata är årets medelnivå. Pengarnas väg genom kassa och skulder
finns i <code>Payments</code>.</p></html>"));
    end OperatingAccounts;

    model Capital "Investeringar, pågående arbeten, tillgångar i bruk och avskrivning som lager och flöden"
      parameter Integer baseYear "Basår";
      parameter Units.Money assets0 "Tillgångar i bruk vid basårets slut, mnkr";
      parameter Units.Money depreciation0 "Avskrivningar i basåret, mnkr";
      parameter Units.Duration life "Sammanvägd avskrivningstid, år";
      parameter Integer constructionYears(min = 0, max = 5) = 0;
      parameter Real constructionShare(min = 0, max = 1) = 0.5;
      parameter Real workInProgress0(min = 0) = 0;
      parameter Real projectOpeningStock = 0;
      parameter Real projectPayment = 0;
      parameter Integer projectOpeningStep = 1;
      parameter Real projectOpeningTime = baseYear + projectOpeningStep - 0.5 "Tidpunkt då projektet tas i bruk; standard mitt i öppningsåret, som en halvårsavskrivning";
      parameter Real projectPlaces = 0;
      parameter Units.Duration commissioningTime = 1/52 "Tid för att ta ett färdigt projekt i bruk, år";
      final parameter Real depreciationRate = -log(1 - 1/max(life, 1.000001)) "Avskrivningstakt per år; skriver av samma andel på ett år som 1/life";
      final parameter Integer releaseYears = max(1, constructionYears);
      outer Components.Calendar calendar;
      outer Clock clock;
      Interfaces.SignalInput investment "Investeringsutbetalningar, mnkr per år" annotation(
        Placement(transformation(origin = {-120, 80}, extent = {{-20, -20}, {20, 20}}), iconTransformation(origin = {0, 110}, extent = {{-10, -10}, {10, 10}}, rotation = -90)));
      StockPort cash "Kassan som betalar" annotation(
        Placement(transformation(extent = {{-130, -10}, {-110, 10}}), iconTransformation(extent = {{-110, -10}, {-90, 10}})));
      Stock assets(level0 = assets0) "Tillgångar i bruk" annotation(Placement(transformation(origin = {60, 0}, extent = {{-20, -20}, {20, 20}})));
      Stock pending(level0 = workInProgress0) "Pågående arbeten" annotation(Placement(transformation(origin = {0, 40}, extent = {{-20, -20}, {20, 20}})));
      Stock project(level0 = projectOpeningStock) "Projektets pågående arbeten" annotation(Placement(transformation(origin = {0, -50}, extent = {{-20, -20}, {20, 20}})));
      Transfer payDirect "Investering som tas i bruk samma år" annotation(Placement(transformation(origin = {-50, 0}, extent = {{-10, -10}, {10, 10}})));
      Transfer payPending "Investering till pågående arbeten" annotation(Placement(transformation(origin = {-50, 40}, extent = {{-10, -10}, {10, 10}})));
      Transfer payProject "Projektutbetalning" annotation(Placement(transformation(origin = {-50, -50}, extent = {{-10, -10}, {10, 10}})));
      Transfer commission "Driftsättning av pågående arbeten" annotation(Placement(transformation(origin = {40, 40}, extent = {{-10, -10}, {10, 10}})));
      Transfer openProject "Projektet tas i bruk" annotation(Placement(transformation(origin = {40, -50}, extent = {{-10, -10}, {10, 10}})));
      Outflow depreciation(annual0 = depreciation0) "Avskrivning" annotation(Placement(transformation(origin = {100, 0}, extent = {{-10, -10}, {10, 10}})));
      discrete Boolean opened(start = false, fixed = true) "Projektet är i bruk";
      Units.MoneyRate regular "Investeringar utöver projektet, mnkr per år";
      output Real projectPlacesNow = if opened then projectPlaces else 0 "Projektplatser i bruk";
      discrete output Units.Money workInProgress(start = workInProgress0 + projectOpeningStock, fixed = true) "Pågående arbeten vid årets slut, mnkr";
      discrete output Units.Money commissioned(start = 0, fixed = true) "Anläggningar tagna i bruk under året, mnkr";
      discrete output Real projectPlacesInUse(start = 0, fixed = true) "Projektplatser i bruk vid årets slut";
      discrete output Units.Money assetBalance(start = 0, fixed = true) "Kontroll av tillgångsbalansen, mnkr; ska vara noll";
    protected
      Units.MoneyRate delayed "Investering som tas i bruk efter byggtiden, mnkr per år";
    equation
      payProject.rate = if calendar.pathIndex == 1 then projectPayment/Units.year else 0;
      regular = investment - payProject.rate;
      payDirect.rate = if constructionYears == 0 then regular else (1 - constructionShare)*regular;
      payPending.rate = if constructionYears == 0 then 0 else constructionShare*regular;
      delayed = if constructionYears > 0 and time >= baseYear + constructionYears then constructionShare*delay(regular, constructionYears, 5) else 0;
      commission.rate = delayed + (if time < baseYear + releaseYears then workInProgress0/releaseYears else 0);
      openProject.rate = if opened then project.level/commissioningTime else 0;
      depreciation.rate = depreciationRate*assets.level;
      when time >= projectOpeningTime then
        opened = true;
      end when;
      connect(cash, payDirect.from);
      connect(cash, payPending.from);
      connect(cash, payProject.from);
      connect(payDirect.to, assets.port);
      connect(payPending.to, pending.port);
      connect(payProject.to, project.port);
      connect(pending.port, commission.from);
      connect(commission.to, assets.port);
      connect(project.port, openProject.from);
      connect(openProject.to, assets.port);
      connect(assets.port, depreciation.from);
      when clock.yearEnd then
        workInProgress = pending.level + project.level;
        commissioned = payDirect.annual + commission.annual + openProject.annual;
        projectPlacesInUse = projectPlacesNow;
        assetBalance = assets.level + pending.level + project.level - pre(assets.closing) - pre(workInProgress)
          - (payDirect.annual + payPending.annual + payProject.annual) + depreciation.annual;
      end when;
      assert(min({assets.level, pending.level, project.level}) >= -1e-6, "Kapitalets lager får inte bli negativa");
      assert(abs(assetBalance) < 1e-6*max(1, assets.level), "Tillgångsbalansen stämmer inte");
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -60}, {100, 60}}, lineColor = {155, 95, 35}, fillColor = {255, 246, 230}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 25}, {95, -25}}, textString = "Kapital")}),
        Diagram(coordinateSystem(extent = {{-140, -100}, {140, 100}})),
        Documentation(info = "<html><p>Tre lager: pågående arbeten, projektets pågående arbeten och tillgångar i bruk. Investeringen betalas
ur kassan under året. Byggandelen ligger som pågående arbete i byggtidens antal år och tas sedan i bruk; resten tas i bruk
direkt. Ingående pågående arbeten tas i bruk jämnt under byggtiden. Projektet tas i bruk vid <code>projectOpeningTime</code>,
till exempel februari, i stället för ett helt år. Avskrivningen är ett flöde ut ur tillgångarna i bruk, i proportion till
nivån, med en takt som ger den sammanvägda avskrivningstidens årliga andel.</p></html>"));
    end Capital;

    model Payments "Driftens pengar: kassa, kundfordringar, leverantörsskulder, pensionsavsättning och förutbetalda bidrag"
      parameter Boolean active = false "Rörelsekapitalet modelleras; annars går driftens flöden direkt till kassan";
      parameter Real receivables0 = 0;
      parameter Real payables0 = 0;
      parameter Real grantAdvances0 = 0;
      parameter Real collectionDays = 0;
      parameter Real paymentDays = 0;
      parameter Real firstYearGrantAdvance = 0;
      parameter Real netCostRoundingAdjustment = 0;
      outer Components.Calendar calendar;
      outer Clock clock;
      input Units.MoneyRate wages "mnkr per år";
      input Units.MoneyRate employerContributions "mnkr per år";
      input Units.MoneyRate pensionExpense "mnkr per år";
      input Units.MoneyRate pensionCashPayments "mnkr per år";
      input Units.MoneyRate otherOperatingExpense "mnkr per år";
      input Units.MoneyRate operatingRevenue "mnkr per år";
      StockPort cash "Kassan" annotation(Placement(transformation(extent = {{130, -10}, {150, 10}}), iconTransformation(extent = {{90, -10}, {110, 10}})));
      Stock receivables(level0 = receivables0) "Kundfordringar" annotation(Placement(transformation(origin = {40, 60}, extent = {{-20, -20}, {20, 20}})));
      Stock payables(level0 = -payables0) "Leverantörsskulder (negativ nivå)" annotation(Placement(transformation(origin = {40, -10}, extent = {{-20, -20}, {20, 20}})));
      Stock pensionProvision(level0 = 0) "Pensionsavsättning, förändring sedan basåret (negativ nivå)" annotation(Placement(transformation(origin = {40, -70}, extent = {{-20, -20}, {20, 20}})));
      Stock grantAdvances(level0 = -grantAdvances0) "Förutbetalda bidrag (negativ nivå)" annotation(Placement(transformation(origin = {-40, -70}, extent = {{-20, -20}, {20, 20}})));
      Outflow payroll "Löner och sociala avgifter" annotation(Placement(transformation(origin = {100, 90}, extent = {{-10, -10}, {10, 10}})));
      Outflow rounding "Avrundningsjustering" annotation(Placement(transformation(origin = {100, -100}, extent = {{-10, -10}, {10, 10}})));
      Inflow revenueDirect "Verksamhetens intäkter, betalda direkt" annotation(Placement(transformation(origin = {100, 60}, extent = {{-10, -10}, {10, 10}})));
      Inflow revenueBooked "Fakturerade verksamhetsintäkter" annotation(Placement(transformation(origin = {0, 60}, extent = {{-10, -10}, {10, 10}})));
      Transfer collection "Kunderna betalar" annotation(Placement(transformation(origin = {80, 40}, extent = {{-10, -10}, {10, 10}})));
      Outflow otherDirect "Övriga kostnader, betalda direkt" annotation(Placement(transformation(origin = {100, 20}, extent = {{-10, -10}, {10, 10}})));
      Outflow otherBooked "Bokförda övriga kostnader" annotation(Placement(transformation(origin = {0, -10}, extent = {{-10, -10}, {10, 10}})));
      Transfer supplierPayment "Betalning till leverantörer" annotation(Placement(transformation(origin = {80, -30}, extent = {{-10, -10}, {10, 10}}, rotation = 180)));
      Outflow pensionCost "Pensionskostnad" annotation(Placement(transformation(origin = {0, -70}, extent = {{-10, -10}, {10, 10}})));
      Transfer pensionPayment "Pensionsutbetalning" annotation(Placement(transformation(origin = {80, -70}, extent = {{-10, -10}, {10, 10}}, rotation = 180)));
      Transfer grantAdvance "Ändring av förutbetalda bidrag" annotation(Placement(transformation(origin = {-40, -30}, extent = {{-10, -10}, {10, 10}})));
      discrete output Units.Money tradeReceivables(start = receivables0, fixed = true) "Kundfordringar vid årets slut, mnkr";
      discrete output Units.Money tradePayables(start = payables0, fixed = true) "Leverantörsskulder vid årets slut, mnkr";
      discrete output Units.Money deferredGrants(start = grantAdvances0, fixed = true) "Förutbetalda bidrag vid årets slut, mnkr";
      discrete output Units.Money cashEffect(start = 0, fixed = true) "Kassaeffekt av ändrat rörelsekapital under året, mnkr";
    protected
      discrete Units.MoneyRate grantChange(start = 0, fixed = true) "Årets ändring av förutbetalda bidrag, mnkr per år";
    equation
      payroll.rate = wages + employerContributions;
      rounding.rate = netCostRoundingAdjustment/Units.year;
      revenueDirect.rate = if active then 0 else operatingRevenue;
      revenueBooked.rate = if active then operatingRevenue else 0;
      collection.rate = if active then receivables.level*365/max(collectionDays, 0.5) else 0;
      otherDirect.rate = if active then 0 else otherOperatingExpense;
      otherBooked.rate = if active then otherOperatingExpense else 0;
      supplierPayment.rate = if active then -payables.level*365/max(paymentDays, 0.5) else 0;
      pensionCost.rate = pensionExpense;
      pensionPayment.rate = pensionCashPayments;
      when calendar.tick then
        grantChange = if active then ((if calendar.pathIndex == 1 then firstYearGrantAdvance else 0) + grantAdvances.level)/Units.year else 0;
      end when;
      grantAdvance.rate = grantChange;
      connect(cash, payroll.from);
      connect(cash, rounding.from);
      connect(revenueDirect.to, cash);
      connect(revenueBooked.to, receivables.port);
      connect(receivables.port, collection.from);
      connect(collection.to, cash);
      connect(cash, otherDirect.from);
      connect(payables.port, otherBooked.from);
      connect(cash, supplierPayment.from);
      connect(supplierPayment.to, payables.port);
      connect(pensionProvision.port, pensionCost.from);
      connect(cash, pensionPayment.from);
      connect(pensionPayment.to, pensionProvision.port);
      connect(grantAdvances.port, grantAdvance.from);
      connect(grantAdvance.to, cash);
      when clock.yearEnd then
        tradeReceivables = receivables.level;
        tradePayables = -payables.level;
        deferredGrants = -grantAdvances.level;
        cashEffect = collection.annual - revenueBooked.annual + otherBooked.annual - supplierPayment.annual + grantAdvance.annual;
      end when;
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -60}, {100, 60}}, lineColor = {35, 115, 85}, fillColor = {230, 245, 238}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 25}, {95, -25}}, textString = "Betalningar")}),
        Diagram(coordinateSystem(extent = {{-140, -120}, {140, 120}})),
        Documentation(info = "<html><p>Driftens kostnader och intäkter blir flöden till och från kassan. Med rörelsekapital går fakturerade
intäkter först till kundfordringar och kostnader till leverantörsskulder; de betalas efter betalningstiden, så lagret blir
ungefär årets flöde gånger dagar/365. Pensionskostnaden ökar avsättningen och utbetalningarna minskar den. Skulder har
negativ nivå. Utan rörelsekapital betalas intäkter och övriga kostnader direkt.</p></html>"));
    end Payments;

    model Finance "Kassa och låneskuld: skatt, bidrag, ränta och finansiering som flöden; ränta på aktuell skuld"
      parameter Units.Money debt0 "Låneskuld vid basårets slut, mnkr";
      parameter Units.Money cash0 "Kassa vid basårets slut, mnkr";
      parameter Units.Money interest0 "Räntekostnader i basåret, mnkr";
      parameter Units.Money tax0 = 0 "Skatteintäkter i basåret, mnkr";
      parameter Units.Money grants0 = 0 "Generella bidrag i basåret, mnkr";
      parameter Units.Money financialIncome "Finansiella intäkter per år vid basårets kassa, mnkr";
      parameter Units.Money otherFinancialExpense "Finansiella kostnader utöver räntor per år, mnkr";
      parameter Real depositSpread = 0 "Skillnad mellan låneräntan och räntan på kassan, andel";
      parameter Boolean liquidityPolicy = false "Styr kassan mot likviditetsreserven";
      parameter Real reserveDays = 0 "Likviditetsreserv i dagar av utbetalningarna";
      parameter Units.Duration reserveAdjustmentTime = 0 "Tidskonstant från bokslutets dagar till reserveDays, år; 0 = reserveDays från start";
      parameter Real reserveDays0(fixed = false) "Bokslutets kassa och kredit i dagar av utbetalningarna vid start";
      parameter Real startTime0(fixed = false) "Simuleringens starttid: bokslutet";
      parameter Units.Money creditLine = 0 "Checkkredit och kreditlöften som räknas av från reserven, mnkr";
      parameter Units.Money plannedPrefinancing = 0 "Förutbestämd ny upplåning första året, mnkr";
      parameter Units.Duration reserveRestoreTime = 1/12 "Tid för att låna upp till kassareserven när kassan understiger den, år";
      parameter Real averageRate0 = 0 "Snittränta på skulden vid basårets slut, andel";
      parameter Units.Duration rateFixingYears(min = 0) = 0 "Genomsnittlig räntebindningstid, år; 0 = hela skulden till årets ränta";
      parameter Real rateShock = 0 "Plötslig höjning av marknadsräntan, andel (0,03 = tre procentenheter)";
      parameter Real rateShockTime = 1e9 "Datum för höjningen som decimalår (2026,5 = 1 juli 2026)";
      outer Components.Calendar calendar;
      outer Clock clock;
      Interfaces.TaxAndGrantsInput taxAndGrants "Skatt och bidrag, mnkr per år" annotation(
        Placement(transformation(extent = {{-160, 60}, {-120, 100}}), iconTransformation(extent = {{-110, 30}, {-90, 50}})));
      Interfaces.SignalInput interestRate "Låneränta, andel" annotation(
        Placement(transformation(extent = {{-160, -100}, {-120, -60}}), iconTransformation(extent = {{-110, -50}, {-90, -30}})));
      StockPort operating "Driftens betalningar" annotation(Placement(transformation(extent = {{-150, -10}, {-130, 10}}), iconTransformation(extent = {{-10, 90}, {10, 110}})));
      StockPort investing "Investeringarnas betalningar" annotation(Placement(transformation(extent = {{-150, -50}, {-130, -30}}), iconTransformation(extent = {{-10, -110}, {10, -90}})));
      Stock cash(level0 = cash0) "Kassa och bank" annotation(Placement(transformation(origin = {0, 0}, extent = {{-20, -20}, {20, 20}})));
      Stock debt(level0 = -debt0) "Låneskuld (negativ nivå)" annotation(Placement(transformation(origin = {100, 0}, extent = {{-20, -20}, {20, 20}})));
      Meter operations "Kassaflöde från den löpande verksamheten" annotation(Placement(transformation(origin = {-60, 0}, extent = {{-10, -10}, {10, 10}})));
      Meter investments "Kassaflöde från investeringar" annotation(Placement(transformation(origin = {-60, -40}, extent = {{-10, -10}, {10, 10}})));
      Inflow tax(annual0 = tax0) "Skatteintäkter" annotation(Placement(transformation(origin = {-100, 60}, extent = {{-10, -10}, {10, 10}})));
      Inflow grants(annual0 = grants0) "Generella bidrag och utjämning" annotation(Placement(transformation(origin = {-100, 40}, extent = {{-10, -10}, {10, 10}})));
      Inflow financial(annual0 = financialIncome) "Finansiella intäkter" annotation(Placement(transformation(origin = {-100, 20}, extent = {{-10, -10}, {10, 10}})));
      Outflow interest(annual0 = interest0) "Räntekostnader" annotation(Placement(transformation(origin = {-100, -20}, extent = {{-10, -10}, {10, 10}}, rotation = 180)));
      Outflow otherFinancial(annual0 = otherFinancialExpense) "Övriga finansiella kostnader" annotation(Placement(transformation(origin = {-100, -60}, extent = {{-10, -10}, {10, 10}}, rotation = 180)));
      Transfer borrowing "Nya lån" annotation(Placement(transformation(origin = {50, 30}, extent = {{-10, -10}, {10, 10}}, rotation = 180)));
      Transfer prefinancing "Lån i förväg" annotation(Placement(transformation(origin = {50, 60}, extent = {{-10, -10}, {10, 10}}, rotation = 180)));
      Transfer repayment "Amortering" annotation(Placement(transformation(origin = {50, -30}, extent = {{-10, -10}, {10, 10}})));
      Units.MoneyRate net "Kassaflöde före finansiering, mnkr per år";
      Real marketRate "Marknadsränta för nya och omsatta lån just nu, andel";
      Real depositRate "Ränta på kassan just nu, andel";
      Units.MoneyRate fixedInterest(start = averageRate0*debt0, fixed = true) "Årlig räntekostnad på lånen med deras bundna räntor, mnkr per år";
      Real averageRate "Snittränta på skulden just nu, andel";
      input Units.MoneyRate operatingPayments "Driftens utbetalningar: löner med sociala avgifter, pensionsutbetalningar och övriga kostnader, mnkr per år";
      Units.Money cashReserve "Likviditetsreserv just nu: dagar av utbetalningarna minus krediten, mnkr";
      Units.Money reserve "Kassareserven just nu: likviditetsreserven plus det som lånats i förväg under första året, mnkr";
      Real reserveDaysNow "Reservens dagar just nu: från bokslutets dagar mot reserveDays";
      Units.MoneyRate financingNeed "Behov av finansiering: underskottet plus det som fattas till reserven, fördelat på reserveRestoreTime, mnkr per år";
      discrete output Units.Money debtLevel(start = debt0, fixed = true) "Låneskuld vid årets slut, mnkr";
      discrete output Units.Money cashBalance(start = 0, fixed = true) "Kontroll av kassabalansen, mnkr; ska vara noll";
      discrete output Units.Money debtBalance(start = 0, fixed = true) "Kontroll av skuldbalansen, mnkr; ska vara noll";
      discrete output Units.Money cumulativeInterest(start = 0, fixed = true) "Räntekostnader sammanlagt sedan basåret, mnkr";
    initial equation
      startTime0 = time;
      reserveDays0 = 365*(cash0 + creditLine)/max(1e-6, operatingPayments - investments.rate + interest.rate);
    equation
      tax.rate = taxAndGrants.tax/Units.year;
      grants.rate = taxAndGrants.grants/Units.year;
      // Kassan utöver basårets ger ränta: marknadsräntan minus depositSpread. Basårets finansiella intäkter gäller basårets kassa.
      depositRate = max(0, marketRate - depositSpread);
      financial.rate = financialIncome/Units.year + depositRate*(cash.level - cash0)/Units.year;
      marketRate = interestRate + (if time >= rateShockTime - 1 then rateShock else 0) "Tiden t är den 31 december år t; datumet rateShockTime är tiden rateShockTime - 1";
      // Lånen omsätts med takten 1/rateFixingYears; nya lån och omsatta lån får marknadsräntan, amortering tar bort snitträntan.
      der(fixedInterest) = if rateFixingYears > 0 then marketRate*(borrowing.rate + prefinancing.rate) - averageRate*repayment.rate
        + (marketRate*(-debt.level) - fixedInterest)/rateFixingYears else 0;
      averageRate = if rateFixingYears > 0 and -debt.level > 1e-9 then fixedInterest/(-debt.level) else marketRate;
      interest.rate = if rateFixingYears > 0 then fixedInterest else marketRate*(-debt.level);
      otherFinancial.rate = otherFinancialExpense/Units.year;
      net = operations.rate + investments.rate;
      prefinancing.rate = if liquidityPolicy and calendar.pathIndex == 1 then plannedPrefinancing/Units.year else 0;
      // Utbetalningarna just nu: drift, investering (investments.rate är negativ när pengar går ut) och ränta.
      // Bokslutet är utgångsläget: kassan börjar på sina egna dagar (med krediten) och går mot reserveDays med tidskonstanten
      // reserveAdjustmentTime, så att kommunen inte lånar upp eller amorterar skillnaden i januari första året.
      reserveDaysNow = if reserveAdjustmentTime > 0 then reserveDays + (reserveDays0 - reserveDays)*exp(-(time - startTime0)/reserveAdjustmentTime) else reserveDays;
      cashReserve = if liquidityPolicy then max(0, reserveDaysNow/365*(operatingPayments - investments.rate + interest.rate) - creditLine) else 0;
      // Det som lånats i förväg hålls i kassan tills den uppskjutna investeringen betalas, jämnt under år två.
      reserve = cashReserve + (if calendar.pathIndex == 1 then prefinancing.accumulated
        elseif calendar.pathIndex == 2 and liquidityPolicy then plannedPrefinancing*max(0, 1 - (time - (calendar.baseYear + 2)*Units.year)/Units.year) else 0);
      // Med kassapolicy styrs kassan mot reserven: behovet är underskottet plus avvikelsen från reserven delad med
      // reserveRestoreTime. Det är kontinuerligt i kassan, så lån och amortering växlar inte fram och tillbaka vid reserven.
      // Ett negativt behov amorterar, dock högst så att skulden går mot noll; finns ingen skuld stannar överskottet i kassan.
      financingNeed = if liquidityPolicy then (reserve - cash.level)/reserveRestoreTime - net else -net;
      borrowing.rate = max(0, financingNeed);
      repayment.rate = if liquidityPolicy then min(max(0, -financingNeed), -debt.level/reserveRestoreTime)
        else (if net > 0 and debt.level < 0 then net else 0);
      connect(operating, tax.to);
      connect(operating, grants.to);
      connect(operating, financial.to);
      connect(operating, interest.from);
      connect(operating, otherFinancial.from);
      connect(operating, operations.a);
      connect(operations.b, cash.port);
      connect(investing, investments.a);
      connect(investments.b, cash.port);
      connect(debt.port, borrowing.from);
      connect(borrowing.to, cash.port);
      connect(debt.port, prefinancing.from);
      connect(prefinancing.to, cash.port);
      connect(cash.port, repayment.from);
      connect(repayment.to, debt.port);
      when clock.yearEnd then
        debtLevel = -debt.level;
        cumulativeInterest = pre(cumulativeInterest) + interest.annual;
        debtBalance = debtLevel - pre(debtLevel) - borrowing.annual - prefinancing.annual + repayment.annual;
        cashBalance = cash.level - pre(cash.closing) - operations.annual - investments.annual
          - borrowing.annual - prefinancing.annual + repayment.annual;
      end when;
      assert(debt.level <= 1e-6, "Låneskulden får inte bli negativ");
      assert(abs(debtBalance) < 1e-6*max(1, debtLevel), "Skuldbalansen stämmer inte");
      assert(abs(cashBalance) < 1e-6*max(1, abs(cash.level)), "Kassabalansen stämmer inte");
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(extent = {{-100, -60}, {100, 60}}, lineColor = {155, 95, 35}, fillColor = {255, 246, 230}, fillPattern = FillPattern.Solid, radius = 8), Text(extent = {{-95, 25}, {95, -25}}, textString = "Finans")}),
        Diagram(coordinateSystem(extent = {{-140, -100}, {140, 100}})),
        Documentation(info = "<html><p>Kassan och låneskulden är lager. Skatt, bidrag och finansiella poster flödar in och ut över gränsen;
driftens och investeringarnas betalningar kommer genom kopplingarna och mäts (<code>operations</code>,
<code>investments</code>). Räntan är ett flöde på den aktuella skulden, inte på årets ingående skuld.</p>
<p>Med räntebindning (<code>rateFixingYears</code> &gt; 0) är <code>fixedInterest</code> den årliga räntekostnaden med lånens
bundna räntor. Den närmar sig marknadsräntan gånger skulden med tidskonstanten <code>rateFixingYears</code>; nya lån tas till
marknadsräntan. En räntechock (<code>rateShock</code> från <code>rateShockTime</code>) slår därför igenom gradvis.</p>
<ul><li>Underskott före finansiering lånas när det uppstår; ett överskott amorterar, och när skulden är noll växer kassan.</li>
<li>Med kassapolicy (standard) går kassan mot likviditetsreserven <code>reserveDays</code>/365 av utbetalningarna just nu
(drift, investering och ränta) minus <code>creditLine</code>. Kassan börjar på bokslutets egna dagar och går mot
<code>reserveDays</code> med tidskonstanten <code>reserveAdjustmentTime</code> (standard tre år): kassan över reserven finansierar underskott
och amorterar lån, och en kassa under reserven fylls på genom lån, båda inom ungefär <code>reserveRestoreTime</code>.
Behovet av finansiering är kontinuerligt i kassan, så lån och amortering växlar inte vid reserven. Utan skuld stannar
överskottet i kassan. Det som lånas i förväg första året hålls i kassan till året därpå. Kommunernas regler och källor
står i data/liquidity.json; standard är 30 dagar och ingen kredit.</li></ul></html>"));
    end Finance;

    partial model Economy "Kommunens ekonomi i kontinuerlig tid: lager och flöden"
      extends Assumptions(residualMigration = Data.calibratedMigrationRates(base.cohorts, base.reportedPopulation, base.births, mortalityRates, ageProfile[1:2, :], olderShares));
      extends Report;
      parameter Units.Rate mortalityRates[5] = Data.deathRatesPerYear(base.cohorts, base.reportedPopulation, base.deaths)
        "Dödstal per åldersgrupp och år för demografin i kontinuerlig tid; 65+ ger basårets döda delat med medelfolkmängden";
      discrete Units.Money equityBalance(start = 0, fixed = true) "Kontroll: förändringen av alla lager minus årets resultat, mnkr; ska vara noll";
      discrete Units.Money revenueBalance(start = 0, fixed = true) "Kontroll: skatt och bidrag som flutit in under året minus årets beslut, mnkr; ska vara noll";
      inner Components.Calendar calendar(horizon = horizon, baseYear = base.year - 1) "Årets regler: räknas fram när året börjar" annotation(
        Placement(transformation(origin = {-200, 140}, extent = {{-10, -10}, {10, 10}})));
      inner Clock clock(horizon = horizon, baseYear = base.year) "Bokslut vid årets slut" annotation(
        Placement(transformation(origin = {-170, 140}, extent = {{-10, -10}, {10, 10}})));
      Components.Scenario scenario(horizon = horizon, residualMigrationPath = residualMigrationPath, migrationDeltaPath = migrationDeltaPath, birthChangePath = birthChangePath, wageGrowthPath = wageGrowthPath, priceGrowthPath = priceGrowthPath, pensionExpensePath = pensionExpensePath, pensionCashPaymentsPath = pensionCashPaymentsPath, referenceTax = referenceTax, referenceGrants = referenceGrants, referencePopulation = referencePopulation, nationalPopulationPath = nationalPopulationPath, investmentPath = investmentPath, deferInvestmentShare = deferInvestmentShare, projectPayment = projectPayment, interestRatePath = interestRatePath, inflationShockPath = inflationShockPath, inflationWagePassThrough = inflationWagePassThrough, inflationPensionPassThrough = inflationPensionPassThrough, inflationRateResponse = inflationRateResponse, inflationGrantCompensation = inflationGrantCompensation) "Årets antaganden" annotation(
        Placement(transformation(origin = {-200, 60}, extent = {{-20, -40}, {20, 40}})));
      replaceable Demography demography(p0 = p0, olderShares = olderShares, horizon = horizon, ageingRatePath = ageProfile[3:horizon + 2, 1:6], olderMortalityPath = ageProfile[3:horizon + 2, 7:9], deaths0Shown = base.deaths, deathRates = mortalityRates, migrationWeights = migrationWeights, births0 = births0) constrainedby DemographyBase "Demografi: lager med födda, döda, åldrande och flyttningar som flöden" annotation(
        Placement(transformation(origin = {-90, 100}, extent = {{-20, -15}, {20, 15}})));
      Services services(careWeights = careWeights, educationWeights = educationWeights, sectorCosts = sectorCosts, adjustment = serviceAdjustment, fixedShare = serviceFixedShare, plannedProjectPlaces = projectPlaces, infrastructureShare = infrastructureShare, networkGrowth = networkGrowth) "Verksamhet" annotation(
        Placement(transformation(origin = {0, 100}, extent = {{-20, -15}, {20, 15}})));
      OperatingAccounts operations(population0 = sum(p0), payroll0 = payroll0, employerContributions0 = employerContributions0, horizon = horizon, employerContributionRatePath = employerContributionRatePath, pension0 = pension0, otherOperatingExpense0 = otherOperatingExpense0, operatingRevenue0 = operatingRevenue0, netCostRoundingAdjustment = netCostRoundingAdjustment, operatingRevenueGrowth = operatingRevenueGrowth, inflationRevenuePassThrough = inflationRevenuePassThrough, pensionFollowsPayroll = pensionFollowsPayroll, productivityGrowth = productivityGrowth, costDrift = costDrift) "Drift" annotation(
        Placement(transformation(origin = {60, 100}, extent = {{-20, -15}, {20, 15}})));
      Components.Revenue revenues(p0 = revenuePopulation0, tax0 = tax0, grants0 = grants0, taxRate = taxRate, taxRatePath = taxRatePath, baseTaxRate = baseTaxRate, equalisationOffset = equalisationOffset, populationRevenueElasticity = populationRevenueElasticity, importedRevenue = importedRevenue, importedRevenueMode = importedRevenueMode, novemberPopulation0 = novemberPopulation0, openingCohorts = p0, ageIncomeWeights = ageIncomeWeights, equalisationCountyRate = equalisationCountyRate, importedComponents = importedComponents, followReference = revenueFromReference, nationalPopulation0 = nationalPopulation0, grantsByComponent = grantsByComponent, horizon = horizon, grantComponents0 = grantComponents0, incomeEqualisationPerCapita = incomeEqualisationPerCapitaPath, equalisationGuarantee = equalisationGuarantee, relativeTaxCapacity0 = incomeEqualisationCapacity, incomeEqualisationComposition = incomeEqualisationComposition, relativeTaxCapacity = relativeTaxCapacityPath, costEqualisationPerCapita = costEqualisationPerCapitaPath, regulationPerCapita = regulationPerCapitaPath, lssEqualisationPerCapita = lssEqualisationPerCapitaPath, propertyFee = propertyFeePath, otherGeneralGrants = otherGeneralGrantsPath, grantIncrease = grantIncrease, novemberObserved = true, novemberCohortsObserved = novemberCohorts, novemberPopulationObserved = novemberPopulation) "Intäkter: årets belopp beslutas när året börjar och betalas jämnt under året" annotation(
        Placement(transformation(origin = {-120, 20}, extent = {{-20, -15}, {20, 15}})));
      Payments payments(active = workingCapitalEnabled, receivables0 = receivables0, payables0 = payables0, grantAdvances0 = grantAdvances0, collectionDays = collectionDays, paymentDays = paymentDays, firstYearGrantAdvance = firstYearGrantAdvance, netCostRoundingAdjustment = netCostRoundingAdjustment) "Driftens betalningar" annotation(
        Placement(transformation(origin = {60, 40}, extent = {{-20, -15}, {20, 15}})));
      Finance finance(debt0 = debt0, cash0 = cash0, interest0 = base.interestExpense, tax0 = tax0, grants0 = grants0, financialIncome = financialIncome, otherFinancialExpense = otherFinancialExpense, depositSpread = depositSpread, liquidityPolicy = liquidityPolicy, reserveDays = reserveDays, reserveAdjustmentTime = reserveAdjustmentTime, creditLine = creditLine, plannedPrefinancing = investmentPath[1]*deferInvestmentShare*prefinanceShare,
        averageRate0 = interestRate, rateFixingYears = rateFixingYears, rateShock = rateShock, rateShockTime = rateShockTime) "Kassa och lån" annotation(
        Placement(transformation(origin = {0, -20}, extent = {{-20, -15}, {20, 15}})));
      Capital capital(baseYear = base.year, assets0 = assets0, depreciation0 = depreciation0, life = life, constructionYears = constructionYears, constructionShare = constructionShare, workInProgress0 = workInProgress0, projectOpeningStock = projectOpeningStock, projectPayment = projectPayment, projectOpeningStep = projectOpeningStep, projectPlaces = projectPlaces) "Kapital" annotation(
        Placement(transformation(origin = {0, -80}, extent = {{-20, -15}, {20, 15}})));
      discrete Units.Persons novemberCohorts[5](start = p0, each fixed = true) "Invånare per åldersgrupp den 1 november, underlag för nästa års skatt och bidrag";
      discrete Units.Persons novemberPopulation(start = novemberPopulation0, fixed = true) "Folkmängd den 1 november";
    protected
      discrete Real revenueYear[11](each fixed = false) "Skatt, bidrag, tre befolkningsjusteringar och sex bidragsdelar för det avslutade året";
      discrete Real interestRateYear(fixed = false) "Årets räntekostnad delad med årets genomsnittliga skuld, andel";
      discrete Units.Money netWorth(fixed = false) "Summan av alla lager vid årets slut, mnkr";
      Units.Money netWorthNow "Summan av alla lager just nu, mnkr";
    initial equation
      revenueYear = cat(1, {revenues.tax, revenues.grants, revenues.recurringTaxAdjustment, revenues.incomeEqualisationAdjustment, revenues.regulationPopulationAdjustment}, revenues.grantParts);
      interestRateYear = scenario.interestRate;
      netWorth = netWorthNow;
    equation
      connect(scenario.demography, demography.drivers);
      connect(scenario.operations, operations.drivers);
      connect(scenario.revenue, revenues.reference);
      connect(scenario.investment, capital.investment);
      connect(scenario.interestRate, finance.interestRate);
      finance.operatingPayments = operations.wagesRate + operations.employerContributionsRate + operations.pensionCashPaymentsRate + operations.otherOperatingExpenseRate;
      connect(demography.cohorts, revenues.cohorts);
      connect(demography.cohorts, services.cohorts);
      connect(demography.cohorts, operations.cohorts);
      // Folkbokföringen den 1 november bestämmer nästa års skatt och bidrag (mode 2); här läses lagret den dagen.
      when sample(base.year + 10/12, 1) then
        novemberCohorts = demography.cohorts.p;
        novemberPopulation = demography.cohorts.population;
      end when;
      connect(services.serviceVolume, operations.serviceVolume);
      connect(revenues.taxAndGrants, finance.taxAndGrants);
      connect(payments.cash, finance.operating);
      connect(capital.cash, finance.investing);
      payments.wages = operations.wagesRate;
      payments.employerContributions = operations.employerContributionsRate;
      payments.pensionExpense = operations.pensionExpenseRate;
      payments.pensionCashPayments = operations.pensionCashPaymentsRate;
      payments.otherOperatingExpense = operations.otherOperatingExpenseRate;
      payments.operatingRevenue = operations.operatingRevenueRate;
      services.projectPlacesInUse = capital.projectPlacesNow;
      netWorthNow = finance.cash.level + finance.debt.level + capital.assets.level + capital.pending.level + capital.project.level
        + payments.receivables.level + payments.payables.level + payments.pensionProvision.level + payments.grantAdvances.level;
      when clock.yearEnd then
        revenueYear = cat(1, {pre(revenues.tax), pre(revenues.grants), pre(revenues.recurringTaxAdjustment), pre(revenues.incomeEqualisationAdjustment), pre(revenues.regulationPopulationAdjustment)}, pre(revenues.grantParts));
        interestRateYear = if pre(finance.debtLevel) + finance.debtLevel > 1e-6 then
          finance.interest.annual/((pre(finance.debtLevel) + finance.debtLevel)/2) else pre(finance.marketRate);
        netWorth = netWorthNow;
        revenueBalance = finance.tax.annual + finance.grants.annual - pre(revenues.tax) - pre(revenues.grants);
        equityBalance = netWorthNow - pre(netWorth) - (finance.tax.annual + finance.grants.annual - operations.cost - capital.depreciation.annual
          + finance.financial.annual - finance.interest.annual - finance.otherFinancial.annual);
      end when;
      assert(abs(equityBalance) < 1e-6*max(1, abs(netWorth)), "Lagren och resultatet stämmer inte");
      assert(abs(revenueBalance) < 1e-6*max(1, abs(finance.tax.annual + finance.grants.annual)), "Skatt och bidrag under året stämmer inte med årets beslut");
      yearIndex = clock.yearsClosed;
      year = base.year + clock.yearsClosed;
      annualInvestment = if yearIndex == 0 then base.investment else finance.investments.annual*(-1);
      annualInterestRate = if yearIndex == 0 then (if base.openingDebt + base.debt > 0 then base.interestExpense/((base.openingDebt + base.debt)/2) else interestRate) else interestRateYear;
      p = demography.cohorts.p;
      population = demography.cohorts.population;
      population80Plus = sum(demography.cohorts.older[2:3]);
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
      wages = operations.wages;
      employerContributions = operations.employerContributions;
      pensionExpense = operations.pensionExpense;
      pensionCashPayments = operations.pensionCashPayments;
      otherOperatingExpense = operations.otherOperatingExpense;
      operatingRevenue = operations.operatingRevenue;
      cost = operations.cost;
      tax = finance.tax.annual;
      grants = finance.grants.annual;
      recurringTaxAdjustment = revenueYear[3];
      incomeEqualisationAdjustment = revenueYear[4];
      regulationPopulationAdjustment = revenueYear[5];
      grantParts = revenueYear[6:11];
      assets = capital.assets.closing;
      commissioned = capital.commissioned;
      projectPaid = capital.payProject.annual;
      projectCommissioned = capital.openProject.annual;
      projectWorkInProgress = capital.project.closing;
      projectPlacesInUse = capital.projectPlacesInUse;
      missingProjectPlaces = services.missingProjectPlaces;
      workInProgress = capital.workInProgress;
      depreciation = capital.depreciation.annual;
      assetBalance = capital.assetBalance;
      interest = finance.interest.annual;
      result = tax + grants - cost - depreciation + finance.financial.annual - interest - finance.otherFinancial.annual;
      operatingCash = finance.operations.annual;
      tradeReceivables = payments.tradeReceivables;
      tradePayables = payments.tradePayables;
      deferredGrants = payments.deferredGrants;
      workingCapitalCash = payments.cashEffect;
      prefinancing = finance.prefinancing.annual;
      outstandingDeferredInvestment = if yearIndex == 1 then investmentPath[1]*deferInvestmentShare else 0;
      debt = finance.debtLevel;
      cash = finance.cash.closing;
      borrowing = finance.borrowing.annual + finance.prefinancing.annual;
      repayment = finance.repayment.annual;
      cashBalance = finance.cashBalance;
      debtBalance = finance.debtBalance;
      resultShare = 100*result/(tax + grants);
      interestShare = 100*interest/(tax + grants);
      cumulativeInterest = finance.cumulativeInterest;
      annotation(
        Diagram(coordinateSystem(extent = {{-220, -120}, {120, 160}})),
        Documentation(info = "<html><p><b>Tid: kalenderår, kontinuerlig tid.</b> Starttiden ska vara basårets år.</p>
<p>Antagandena står i <code>Assumptions</code> och utdata i <code>Report</code>. Allt som ändras gradvis är lager och flöden:</p>
<ul><li>Pengar: kassa, låneskuld, tillgångar, pågående arbeten, kundfordringar, leverantörsskulder, pensionsavsättning och
förutbetalda bidrag (<code>Continuous.Stock</code>, <code>Transfer</code>, <code>Inflow</code>, <code>Outflow</code>). Skulder har
negativ nivå. Summan av lagren ändras bara med årets resultat (<code>equityBalance</code>).</li>
<li>Befolkningen: födda, döda, åldrande och flyttningar är flöden (<code>Continuous.Demography</code>; ettårsåldrar med
<code>Continuous.CohortDemography</code>). Befolkningsbalansen stäms av vid varje årsslut.</li>
<li>Löne-, pris-, taxe-, produktivitets- och standardnivån växer kontinuerligt (<code>OperatingAccounts</code>).</li>
<li>Verksamhetens kapacitet, kostnaderna, rörelsekapitalet, avskrivningen, räntan på aktuell skuld och upplåningen.</li></ul>
<p>Händelser finns bara där regeln är årlig:</p>
<ul><li>Bokslutet 31 december (<code>clock</code>): flödena summeras till årets belopp och lagren läses av.</li>
<li>Beslut som gäller från 1 januari (<code>calendar</code>): skattesatsen, årets skatt och generella bidrag, som betalas ut
med en tolftedel i månaden och därför flyter jämnt under året, och sociala avgifter. Årsbanorna (investeringar, pensioner,
flyttnetto, räntebana) läses vid samma tidpunkt och flyter jämnt under året.</li>
<li>Folkbokföringen 1 november: befolkningen den dagen är underlag för nästa års skatt och bidrag.</li>
<li>Med ettårsåldrar byter födelseårsgrupperna etikett vid årsskiftet; ingen person flyttas.</li></ul>
<p>Årsvärdena i utdata är summor av flödena eller nivåer vid årets slut. Ränta räknas på aktuell skuld, kostnader efter
befolkning och kapacitet under året, avskrivning på tillgångarnas aktuella nivå, och åldrande och död sker under året.</p></html>"));
    end Economy;
    annotation(Documentation(info = "<html><p>Lager och flöden för en modell i kontinuerlig tid. Ett <code>Stock</code> är ett konto, ett
<code>Transfer</code> flyttar pengar mellan två konton och <code>Inflow</code>/<code>Outflow</code> korsar gränsen som intäkt
eller kostnad. Varje flöde summerar sitt årsbelopp vid bokslutet (<code>Clock</code>). Befolkningen är lager i
<code>Demography</code> och <code>CohortDemography</code>. <code>Economy</code> sätter ihop kommunen.</p></html>"));
  end Continuous;
  annotation(version = "0.1.0", Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Rectangle(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, extent = {{-70, -70}, {-35, 0}}), Rectangle(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, extent = {{-17, -70}, {18, 30}}), Rectangle(lineColor = {35, 115, 85}, fillColor = {35, 115, 85}, fillPattern = FillPattern.Solid, extent = {{35, -70}, {70, 60}})}),
    Documentation(info = "<html><p><b>Kommunekonomi</b> är komponenter för en svensk kommuns ekonomi år för år: befolkning,
verksamhet, drift, skatt och bidrag, investeringar, resultat och lån. Belopp i mnkr och löpande priser; tiden är kalenderår.</p>
<p>En kommun använder biblioteket i ett eget paket: basårens utfall som <code>Data.BaseYear</code>, demografin som
<code>Data.SCB.DemographyYear</code> och en modell som ärver <a href=\"modelica://Kommunekonomi.Continuous.Economy\">Continuous.Economy</a>
med sitt basår. <a href=\"modelica://Motala\">Motala</a> är exemplet.</p>
<p>Komponenterna kopplas med riktade kopplingar (<code>Interfaces</code>) och räknar ett steg per år med en gemensam
kalender. Demografin är utbytbar (<code>replaceable</code>): fem åldersgrupper eller ettårsåldrar.</p></html>"));
end Kommunekonomi;
