package Motala "Motala ekonomilabb: kommunens ekonomi år för år; belopp i mnkr, tid i kalenderår"
  package Handledning "Handledning: ordlista och hur modellen läses"
    class Ordlista "Ordlista: ekonomiska begrepp i modellen"
      annotation(DocumentationClass = true, Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}), Text(textColor = {40, 95, 140}, extent = {{-60, -70}, {60, 70}}, textString = "i", fontSize = 60)}), Documentation(info = "<html>
<h3>Ordlista</h3>
<p>Begreppen i kommunens ekonomi, med Motalas utfall för 2025 i miljoner kronor (mnkr). Ett hushåll är en bra jämförelse
rätt långt.</p>

<h4>Årets resultat</h4>
<p>Intäkter minus kostnader under året, som i kommunens resultaträkning:</p>
<table border=\"1\" cellspacing=\"0\" cellpadding=\"3\">
<tr><td>Skatteintäkter</td><td align=\"right\">2 330</td></tr>
<tr><td>Generella statsbidrag och utjämning</td><td align=\"right\">987</td></tr>
<tr><td>Verksamhetens nettokostnad</td><td align=\"right\">−3 023</td></tr>
<tr><td>Avskrivningar</td><td align=\"right\">−180</td></tr>
<tr><td>Finansiella intäkter och kostnader, netto</td><td align=\"right\">−10</td></tr>
<tr><td><b>Årets resultat</b></td><td align=\"right\"><b>105</b></td></tr>
</table>
<p>De avrundade posterna summerar till 104; bokslutet anger 105. I modellen: <code>result</code> i komponenten Finans.</p>

<h4>Skatteintäkter och skatteunderlag</h4>
<p>Kommunalskatten tas ut på den beskattningsbara inkomsten för dem som var folkbokförda i kommunen den 1 november året
före. Summan av inkomsterna är <b>skatteunderlaget</b>; skatten är skatteunderlaget gånger <b>skattesatsen</b>, i Motala
21,70 kronor per hundralapp.</p>
<p>Pengarna kommer i förskott, innan inkomsterna är kända. Staten betalar ut skatten varje månad utifrån skatteunderlaget
två år tidigare, uppräknat med regeringens prognos. När de verkliga inkomsterna är kända görs en <b>slutavräkning</b>; i
bokslutet tar kommunen upp en uppskattad slutavräkning enligt SKR:s prognos i december och kan få rätta den året efter.
Därför ändras skatteintäkterna ofta mellan budget, prognoser och bokslut.</p>
<table border=\"1\" cellspacing=\"0\" cellpadding=\"3\">
<tr><th>Motala, mnkr</th><th>2024</th><th>2025</th></tr>
<tr><td>Preliminär kommunalskatt (förskotten)</td><td align=\"right\">2 254</td><td align=\"right\">2 344</td></tr>
<tr><td>Preliminär slutavräkning innevarande år</td><td align=\"right\">8</td><td align=\"right\">−14</td></tr>
<tr><td>Slutavräkningsdifferens föregående år</td><td align=\"right\">−11</td><td align=\"right\">0</td></tr>
<tr><td><b>Skatteintäkter</b></td><td align=\"right\"><b>2 251</b></td><td align=\"right\"><b>2 330</b></td></tr>
</table>
<p>Källa: årsredovisning 2025, not 6.</p>
<p><b>I modellen</b> (komponenten Intäkter, <code>tax</code>) räknas skatten från en <b>referensbana</b>
(<code>referenceTax</code>): bokslutets skatt som växer med <code>taxGrowth</code>, SKR:s beräkning för Motala, eller
budgetens belopp. Banan justeras på tre sätt:</p>
<ul><li>befolkningen: referensbanans tillväxt gäller hela riket, så banan skalas med Motalas folkmängd i förhållande till
rikets, förra året jämfört med året före basåret (folkbokföringen den 1 november räknas);</li>
<li>åldern: ändras andelen 19-64-åringar, som har de flesta förvärvsinkomsterna, ändras skatten;</li>
<li>skattesatsen: skatten ändras i samma proportion som <code>taxRate</code> mot basårets 21,70.</li></ul>
<p>skatt = referens · befolkningsfaktor · (1 + ålderseffekt) · skattesats / 21,70. Med en importerad SKR-bana, som redan är
Motalas egen, skalas den bara med modellens folkmängd mot SKR:s, och med <code>revenueFromReference</code> tas referensen
rakt av, som i <code>Examples.Budget2026</code>. Förskott och slutavräkning hålls inte isär i modellen.</p>

<h4>Generella statsbidrag och utjämning</h4>
<p>Pengar från staten och, via utjämningssystemet, från andra kommuner. De är generella, alltså inte öronmärkta för en viss
verksamhet. Det kommunalekonomiska utjämningssystemet ska ge alla kommuner ungefär samma förutsättningar, oavsett
invånarnas inkomster och hur dyr befolkningen är att ge service. Det har flera delar:</p>
<ul><li><b>Inkomstutjämning</b>: kommuner vars skattekraft (skatteunderlag per invånare) är lägre än en garantinivå på
115 procent av rikets genomsnitt får ett bidrag som fyller upp större delen av skillnaden; kommuner över den betalar en
avgift. Motala har lägre skattekraft än genomsnittet, och detta är den största delen.</li>
<li><b>Kostnadsutjämning</b>: jämnar ut skillnader i vad verksamheterna kostar på grund av struktur, till exempel
åldersfördelning, socioekonomi och hur glest kommunen är befolkad. Den kostar staten ingenting; kommuner med dyrare
struktur än genomsnittet får bidrag och de andra betalar.</li>
<li><b>LSS-utjämning</b>: samma tanke för kostnaderna för stöd och service till personer med funktionsnedsättning.</li>
<li><b>Regleringsbidrag eller regleringsavgift</b>: ett lika stort belopp per invånare i alla kommuner som stämmer av
systemet mot det anslag riksdagen beslutat. Höjda generella statsbidrag kommer ofta ut här.</li>
<li><b>Kommunal fastighetsavgift</b>: avgiften på bostäder i kommunen går till kommunen.</li>
<li><b>Övriga generella bidrag från staten</b>, till exempel tillfälliga bidrag.</li></ul>
<table border=\"1\" cellspacing=\"0\" cellpadding=\"3\">
<tr><th>Motala, mnkr</th><th>2024</th><th>2025</th></tr>
<tr><td>Inkomstutjämning</td><td align=\"right\">614</td><td align=\"right\">631</td></tr>
<tr><td>Kostnadsutjämning</td><td align=\"right\">31</td><td align=\"right\">32</td></tr>
<tr><td>Regleringsbidrag</td><td align=\"right\">134</td><td align=\"right\">115</td></tr>
<tr><td>Kommunal fastighetsavgift</td><td align=\"right\">114</td><td align=\"right\">119</td></tr>
<tr><td>LSS-utjämning</td><td align=\"right\">39</td><td align=\"right\">40</td></tr>
<tr><td>Övriga generella bidrag från staten</td><td align=\"right\">21</td><td align=\"right\">51</td></tr>
<tr><td><b>Summa</b></td><td align=\"right\"><b>953</b></td><td align=\"right\"><b>987</b></td></tr>
</table>
<p>Källa: årsredovisning 2025, not 7. Beräkningarna görs av SCB och SKR efter lagen om kommunalekonomisk utjämning
(2004:773) och bygger på folkmängden den 1 november året före.</p>
<p><b>I modellen</b> (komponenten Intäkter, <code>grants</code>) delas bidragen inte upp. De utgår från en referensbana
(<code>referenceGrants</code>), skalas med Motalas folkmängd i förhållande till rikets och minskas med 95 procent av
ålderseffekten på skatten (<code>equalisationOffset</code>): får kommunen mer skatt för att fler är i arbetsför ålder, tar
utjämningen tillbaka det mesta. Det är en förenklad känslighet, inte lagens beräkning. Kostnadsutjämningen för ett
snabbare åldrande än rikets ingår ännu inte.</p>

<h4>Befolkningen och intäkterna</h4>
<p>Skatten är ungefär antalet invånare gånger inkomsten per invånare gånger skattesatsen, och de flesta bidragen räknas per
invånare. Rikets skatteunderlag växer både av högre inkomster och av att rikets befolkning ökar; Motalas skatt växer av
samma inkomstökning men av Motalas egen befolkningsförändring. När Motala krymper medan riket växer, växer Motalas skatt
långsammare än rikets skatteunderlag. Utjämningen skyddar mot låga inkomster per invånare, inte mot färre invånare: med
2025 års belopp betyder varje invånare cirka 77 000 kr per år i skatt och bidrag. Minskningen med 374 invånare under 2025
ger cirka 29 mnkr mindre från 2026. I modellen: <code>taxGrowth</code>, <code>nationalPopulationPath</code> och komponenten
Intäkter.</p>

<h4>SKR:s prognos</h4>
<p>Sveriges Kommuner och Regioner beräknar skatteintäkter och bidrag för varje kommun några gånger per år. Kommunen
använder den i sin budget. I modellen är den en referensbana in i Intäkter, inte en del av modellen själv.</p>

<h4>Verksamhetens nettokostnad</h4>
<p>Vad skola, omsorg och annan verksamhet kostar när avgifter och andra egna intäkter har dragits av. Den största delen
är löner. I modellen: komponenten Drift, <code>cost</code> = löner + pensionskostnad + övriga kostnader −
verksamhetens intäkter.</p>

<h4>Avskrivning</h4>
<p>Kostnaden för en investering fördelad över de år den används. En skola för 100 mnkr som håller i 33 år ger cirka
3 mnkr i kostnad per år i stället för 100 mnkr det år den byggs. Motala skriver av cirka 180 mnkr per år på allt som
byggts tidigare. I modellen: komponenten Kapital, <code>depreciation</code>.</p>

<h4>Investering</h4>
<p>Pengar till sådant som varar länge: skolor, vägar, vatten och avlopp. Investeringen syns inte i resultatet det år den
görs, bara som avskrivningar de kommande åren, men den kostar pengar direkt. I modellen: <code>investmentPath</code>.</p>

<h4>Kassaflöde</h4>
<p>Pengar in minus pengar ut. Resultatet är inte samma sak, eftersom avskrivningen är en kostnad utan utbetalning:
kassaflöde från verksamheten = resultat + avskrivningar (plus pensionskostnad minus pensionsutbetalningar).
I modellen: <code>operatingCash</code>.</p>

<h4>Lån, amortering och ränta</h4>
<p>Räcker kassaflödet inte till investeringarna lånar kommunen mellanskillnaden (<code>borrowing</code>). Ett överskott
används till att betala av lån, att <b>amortera</b> (<code>repayment</code>). <b>Räntan</b> betalas på skulden vid
årets början och minskar resultatet. Budget 2026 planerar investeringar på 755 mnkr mot ett kassaflöde på 280 mnkr,
alltså 411 mnkr i nya lån. I modellen: komponenten Finans, <code>debt</code> (låneskulden) och <code>interest</code>
(årets räntekostnad). Vad lånen kostar i förhållande till intäkterna visar <code>interestShare</code>, räntekostnaderna i
procent av skatter och bidrag; <code>cumulativeInterest</code> är räntekostnaderna sammanlagt sedan basåret.</p>

<h4>Balansräkning, tillgångar, skulder och eget kapital</h4>
<p>En ögonblicksbild den 31 december. <b>Tillgångar</b> är det kommunen äger: byggnader, anläggningar, kassa.
<b>Skulder</b> är det kommunen är skyldig, främst banklån (1 040 mnkr vid slutet av 2025). <b>Eget kapital</b> är
tillgångar minus skulder och växer med årets resultat. Resultaträkningen beskriver året, balansräkningen läget vid
årets slut.</p>

<h4>Pensionskostnad och pensionsutbetalning</h4>
<p>Kommunen bokför en kostnad för de pensioner de anställda tjänar in nu; pengarna betalas ut först när de går i
pension. Modellen håller isär dem: kostnaden påverkar resultatet, utbetalningen kassan. I modellen:
<code>pensionExpense</code> och <code>pensionCashPayments</code>.</p>

<h4>Balanskravet och det finansiella målet</h4>
<p>Kommunallagens <b>balanskrav</b> säger att intäkterna ska vara större än kostnaderna, alltså ett positivt resultat
efter vissa justeringar. Motala har dessutom ett eget <b>finansiellt mål</b>: resultatet i procent av skatter och
bidrag, 2,5 procent i budget 2026 (86 mnkr). I modellen: <code>resultShare</code>.</p>

<h4>Löpande priser och index</h4>
<p>Alla belopp är i <b>löpande priser</b>, alltså kronor det året, utan omräkning för inflation. Ett <b>index</b> visar en
nivå i förhållande till basåret, där basåret är 1: ett löneindex på 1,03 betyder tre procent högre löner än basåret.</p>

<h4>Basår, bokslut, budget och prognos</h4>
<p><b>Bokslutet</b> (årsredovisningen) visar vad som faktiskt hände ett år. <b>Basåret</b> är det bokslut modellen startar
från, i dag 2025. <b>Budgeten</b> är fullmäktiges plan för kommande år. En <b>prognos</b> är en bedömning av vad som
kommer att hända; kommunen gör prognoser för innevarande år i april och augusti.</p>

<h4>Hur begreppen hänger ihop i modellen</h4>
<p>Demografi ger befolkningen. Verksamhet räknar behovet av skola och omsorg. Drift ger nettokostnaden, Intäkter ger
skatt och bidrag och Kapital ger avskrivningarna. I Finans möts allt: resultat, kassaflöde, nya lån och skuld. Pilarna i
diagrammet för <a href=\"modelica://Motala.Annual\">Motala.Annual</a> följer den kedjan.</p>
</html>"));
    end Ordlista;
    annotation(DocumentationClass = true, Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Ellipse(lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}), Text(textColor = {40, 95, 140}, extent = {{-60, -70}, {60, 70}}, textString = "i", fontSize = 60)}), Documentation(info = "<html><p>Börja med <a href=\"modelica://Motala.Handledning.Ordlista\">ordlistan</a>
om begreppen är nya. Modellen att simulera finns i <a href=\"modelica://Motala.Examples\">Examples</a>.</p></html>"));
  end Handledning;
  package Data "Utfall för Motalas basår: bokslut (kommunen) och befolkning; en konstant per basår"
    import Kommunekonomi.Data.BaseYear;
    import Kommunekonomi.Data.Budget;

    constant BaseYear motala2025 = BaseYear(
      year = 2025,
      cohorts = {{3202, 4654, 1569, 23540, 10763}, {3008, 4671, 1592, 23311, 10923}, {2894, 4629, 1575, 23019, 11022}},
      reportedPopulation = {43728, 43505, 43131},
      births = {336, 334}, deaths = 468,
      tax = 2330, priorYearSettlement = 0, grants = 987,
      equalisationNextYear = {14734, 1175, 2799, 1230},
      relativeTaxCapacity = {0.8729, 0.8759},
      grantComponents = {631, 32, 115, 40, 119},
      payroll = 2288, pension = 190, otherOperatingExpense = 1297, operatingRevenue = 751, netCostRoundingAdjustment = -1,
      depreciation = 180, financialIncome = 15, interestExpense = 21, otherFinancialExpense = 4,
      debt = 1040, openingDebt = 940, cash = 81, assets = 2997, investment = 413, taxRate = 21.7,
      sectorShares = {0.4314, 0.2151, 0.3535}, educationShares = {0.2647, 0.5462, 0.1891},
      careCostPerInhabitant = {23331, 166483})
      "Årsredovisning 2025 (kommunen), s. 6-7, 47-53, 70; resultat 105 mnkr (avrundade poster ger 104)";
    constant BaseYear motala2024 = BaseYear(
      year = 2024,
      cohorts = {{3277, 4664, 1530, 23694, 10563}, {3202, 4654, 1569, 23540, 10763}, {3008, 4671, 1592, 23311, 10923}},
      reportedPopulation = {43728, 43728, 43505},
      births = {381, 336}, deaths = 402,
      tax = 2251, priorYearSettlement = -11, grants = 953,
      equalisationNextYear = {14473, 724, 2644, 924},
      relativeTaxCapacity = {0.8744, 0.8729},
      grantComponents = {614, 31, 134, 39, 114},
      payroll = 2258, pension = 275, otherOperatingExpense = 1269, operatingRevenue = 774, netCostRoundingAdjustment = 0,
      depreciation = 168, financialIncome = 17, interestExpense = 13, otherFinancialExpense = 11,
      debt = 940, openingDebt = 663, cash = 229, assets = 2782, investment = 417, taxRate = 21.7,
      sectorShares = {0.4292, 0.2148, 0.3559}, educationShares = {0.273, 0.5416, 0.1853},
      careCostPerInhabitant = {22275, 168850})
      "Jämförelsekolumnen i årsredovisning 2025 (kommunen), s. 48-49 och not 8-9; resultat 1 mnkr";
    // Basåren 2020-2023 finns för tester mot historien (scripts/hindcast_vintages.py). Pengar ur
    // research/data/annual-ledgers.json (årsredovisningarna 2021-2024, kommunen); åldersgrupper, folkmängd,
    // födda och döda ur SCB (data/downloads/20261108T124756Z), som stämmer med årsredovisningarnas tabeller.
    constant BaseYear motala2023 = BaseYear(
      year = 2023,
      cohorts = {{3386, 4633, 1550, 23766, 10339}, {3277, 4664, 1530, 23694, 10563}, {3202, 4654, 1569, 23540, 10763}},
      reportedPopulation = {43674, 43728, 43728},
      births = {360, 381}, deaths = 445,
      tax = 2227, priorYearSettlement = 12, grants = 865,
      equalisationNextYear = {14022, 704, 3055, 888},
      relativeTaxCapacity = {0.8768, 0.8744},
      grantComponents = {581, 29, 102, 39, 106},
      payroll = 2183, pension = 248, otherOperatingExpense = 1247, operatingRevenue = 765, netCostRoundingAdjustment = 0,
      depreciation = 150, financialIncome = 11, interestExpense = 11, otherFinancialExpense = 6,
      debt = 663, openingDebt = 664.5, cash = 115, assets = 2389, investment = 299, taxRate = 21.7,
      sectorShares = {0.4395, 0.1974, 0.3631}, educationShares = {0.2744, 0.5392, 0.1864},
      careCostPerInhabitant = {20538, 170510})
      "Årsredovisning 2023 (kommunen), s. 47-54; anläggningar i bruk ur jämförelsekolumnen i årsredovisning 2024, s. 48; resultat 23 mnkr";
    constant BaseYear motala2022 = BaseYear(
      year = 2022,
      cohorts = {{3448, 4559, 1559, 23825, 10249}, {3386, 4633, 1550, 23766, 10339}, {3277, 4664, 1530, 23694, 10563}},
      reportedPopulation = {43640, 43674, 43728},
      births = {420, 360}, deaths = 420,
      tax = 2137.6, priorYearSettlement = 13.9, grants = 794.3,
      equalisationNextYear = {13293, 631, 2336, 885},
      relativeTaxCapacity = {0.8836, 0.8768},
      grantComponents = {531.1, 13.3, 120.5, 19.8, 102},
      payroll = 2009.0, pension = 178.1, otherOperatingExpense = 1187.4, operatingRevenue = 729.5, netCostRoundingAdjustment = 0,
      depreciation = 162.3, financialIncome = 8.1, interestExpense = 5.6, otherFinancialExpense = 2.0,
      debt = 664.5, openingDebt = 830.2, cash = 85.8, assets = 2305.3, investment = 253.9, taxRate = 21.7,
      sectorShares = {0.4337, 0.1987, 0.3675}, educationShares = {0.2857, 0.5266, 0.1877},
      careCostPerInhabitant = {18330, 169826})
      "Årsredovisning 2022 (kommunen), s. 6 och 37-43, not 14; låneskulden inklusive kortfristig del (s. 32); avskrivningarna innehåller en nedskrivning på 12,1 mnkr; resultat 125,1 mnkr";
    constant BaseYear motala2021 = BaseYear(
      year = 2021,
      cohorts = {{3418, 4593, 1531, 23988, 10143}, {3448, 4559, 1559, 23825, 10249}, {3386, 4633, 1550, 23766, 10339}},
      reportedPopulation = {43673, 43640, 43674},
      births = {430, 420}, deaths = 455,
      tax = 2032.2, priorYearSettlement = 7.1, grants = 763.5,
      equalisationNextYear = {12169, 338, 2760, 453},
      relativeTaxCapacity = {0.8878, 0.8836},
      grantComponents = {496, 15.7, 129.7, 17.7, 99.1},
      payroll = 1976.2, pension = 167.3, otherOperatingExpense = 1179.4, operatingRevenue = 728.5, netCostRoundingAdjustment = 0,
      depreciation = 138.4, financialIncome = 5.9, interestExpense = 5.2, otherFinancialExpense = 1.9,
      debt = 830.2, openingDebt = 788.0, cash = 338.2, assets = 2328.5, investment = 272.6, taxRate = 21.7,
      sectorShares = {0.4324, 0.2052, 0.3624}, educationShares = {0.2884, 0.521, 0.1905},
      careCostPerInhabitant = {17287, 168919})
      "Jämförelsekolumnen i årsredovisning 2022 (kommunen), s. 6 och 37-43; anläggningarna inklusive pågående arbeten, som inte är särredovisade; resultat 61,7 mnkr";
    constant BaseYear motala2020 = BaseYear(
      year = 2020,
      cohorts = {{3441, 4611, 1519, 24130, 9986}, {3418, 4593, 1531, 23988, 10143}, {3448, 4559, 1559, 23825, 10249}},
      reportedPopulation = {43687, 43673, 43640},
      births = {438, 430}, deaths = 451,
      tax = 1929.9, priorYearSettlement = -10.7, grants = 760.5,
      equalisationNextYear = {11366, 360, 2973, 406},
      relativeTaxCapacity = {0.8867, 0.8878},
      grantComponents = {491, 18.7, 44.7, 21.1, 91.7},
      payroll = 1926.0, pension = 207.7, otherOperatingExpense = 1044.5, operatingRevenue = 680.8, netCostRoundingAdjustment = 0,
      depreciation = 124.5, financialIncome = 4.7, interestExpense = 4.7, otherFinancialExpense = 3.7,
      debt = 788.0, openingDebt = 801.3, cash = 167.9, assets = 2224.7, investment = 207.1, taxRate = 21.7,
      sectorShares = {0.4473, 0.2043, 0.3484}, educationShares = {0.2911, 0.5146, 0.1943},
      careCostPerInhabitant = {16848, 167639})
      "Jämförelsekolumnen i årsredovisning 2021 (kommunen), s. 37-43, och femårsöversikten i årsredovisning 2022, s. 6; anläggningarna inklusive pågående arbeten; resultat 64,8 mnkr";

    constant Budget budget2026 = Budget(
      year = 2026,
      tax = {2410, 2485, 2570}, grants = {1014, 1046, 1071},
      netCost = {3122, 3182, 3238}, depreciation = {194, 220, 248},
      financialIncome = {9, 8, 8}, financialCost = {31, 49, 71}, result = {86, 88, 92},
      investment = {755, 897, 961}, operatingCash = {280, 308, 340}, newLoans = {411, 589, 621})
      "Budget 2026 med plan 2027-2028 (kommunen), s. 25, 28 och 32; skatt och bidrag enligt SKR:s prognos oktober 2025 (data/municipal-budgets.json)";

    package SCB "Motalas demografiska data från SCB. Genereras av scripts/write_demography_modelica.py; redigera inte för hand"
      extends Kommunekonomi.Data.SCB;

      constant DemographyYear motala2020 = DemographyYear(
        year = 2020,
        population = {{223, 257, 267, 257, 270, 276, 270, 243, 263, 252, 274, 264, 275, 287, 257, 270, 250,
            277, 256, 245, 245, 251, 228, 203, 229, 249, 235, 273, 250, 297, 292, 236, 280, 273,
            266, 296, 241, 229, 248, 236, 234, 254, 250, 252, 233, 256, 288, 280, 299, 305, 321,
            303, 311, 295, 317, 308, 344, 297, 257, 277, 256, 268, 298, 275, 255, 274, 255, 267,
            263, 257, 259, 302, 268, 260, 263, 234, 220, 229, 197, 157, 140, 145, 131, 107, 93,
            94, 63, 51, 55, 46, 41, 37, 28, 20, 13, 7, 9, 2, 1, 1, 2},
           {209, 211, 219, 252, 250, 246, 241, 224, 247, 237, 260, 246, 241, 253, 247, 219, 267,
            251, 258, 219, 217, 153, 159, 166, 184, 198, 217, 232, 230, 261, 285, 251, 259, 248,
            262, 233, 229, 219, 233, 232, 250, 245, 229, 240, 241, 253, 274, 265, 277, 279, 292,
            310, 295, 314, 313, 312, 272, 261, 242, 280, 280, 255, 283, 292, 249, 268, 284, 268,
            251, 283, 268, 284, 263, 252, 271, 259, 277, 221, 187, 182, 167, 167, 163, 157, 138,
            128, 98, 103, 88, 85, 72, 64, 56, 35, 43, 21, 23, 9, 7, 5, 11}},
        deathRisk = {{0.00237151, 0.000182678, 0.000100977, 6.20426e-05, 0.000100746, 9.26088e-05, 6.18775e-05, 4.68211e-05, 7.35537e-05, 2.13968e-05, 5.87313e-05, 7.42975e-05, 9.19203e-05, 8.85817e-05, 0.000132252, 0.000152206, 0.000194033,
            0.000287396, 0.000422966, 0.000482836, 0.000555137, 0.000575781, 0.000558924, 0.000557741, 0.000671656, 0.000777387, 0.000623974, 0.000674561, 0.000739791, 0.000656351, 0.000676327, 0.000641865, 0.00071708, 0.000704093,
            0.000708045, 0.000726379, 0.000788186, 0.000751241, 0.000754643, 0.00085752, 0.00101092, 0.000924522, 0.00106955, 0.0010343, 0.00112724, 0.00125385, 0.0014226, 0.00135682, 0.00158098, 0.00185766, 0.00197277,
            0.00209704, 0.0025169, 0.00276105, 0.00311523, 0.00344983, 0.00396463, 0.00417102, 0.00448439, 0.00510822, 0.00590733, 0.00635284, 0.00742634, 0.00797082, 0.00910655, 0.00992899, 0.01123, 0.0119806,
            0.0131699, 0.0148228, 0.0162641, 0.0173504, 0.0196838, 0.0213962, 0.0238463, 0.0266521, 0.0304742, 0.0339035, 0.0382977, 0.0432246, 0.0493186, 0.0563612, 0.0647402, 0.0724184, 0.0827747,
            0.0941901, 0.107286, 0.121527, 0.135277, 0.152831, 0.18138, 0.197283, 0.217237, 0.241453, 0.265382, 0.286653, 0.311966, 0.338658, 0.366694, 0.396012, 0.599048},
           {0.00204595, 0.000184069, 9.56017e-05, 0.000101664, 9.9973e-05, 7.25164e-05, 7.76484e-05, 5.86041e-05, 4.29527e-05, 3.3085e-05, 6.46238e-05, 6.66034e-05, 6.20864e-05, 7.64531e-05, 0.000128465, 9.23077e-05, 0.000119283,
            0.000134782, 0.000199026, 0.000207247, 0.000248747, 0.000225203, 0.000191137, 0.000279205, 0.000259887, 0.000244026, 0.0002463, 0.000283762, 0.000283469, 0.000235434, 0.000335518, 0.000347013, 0.00037076, 0.000312107,
            0.000367603, 0.000386785, 0.000416668, 0.000430273, 0.000443371, 0.000483258, 0.00056932, 0.000564763, 0.000625831, 0.000731549, 0.000725959, 0.000779844, 0.000946721, 0.00102846, 0.00111804, 0.00131886, 0.00133085,
            0.00152337, 0.00164799, 0.00173058, 0.00195519, 0.00214827, 0.00253017, 0.00268798, 0.00310738, 0.00350483, 0.00382636, 0.00447962, 0.00470272, 0.00530257, 0.00575452, 0.00647198, 0.00741085, 0.00786705,
            0.00899397, 0.00955468, 0.0108171, 0.0121462, 0.0139723, 0.0155316, 0.0168574, 0.0184772, 0.0208633, 0.0234806, 0.0268214, 0.03036, 0.0341482, 0.0396693, 0.0459579, 0.0515532, 0.059675,
            0.0675989, 0.078082, 0.0887122, 0.102444, 0.117831, 0.135861, 0.151816, 0.16947, 0.191495, 0.214936, 0.231998, 0.255349, 0.280421, 0.307227, 0.335747, 0.511872}},
        mortalityImprovement = {{0.01471, 0.01471, 0.01471, 0.01471, 0.01471, 0.01471, 0.01471, 0.01471, 0.01471, 0.01471, 0.01471, 0.01471, 0.01471, 0.01471, 0.01471, 0.01272, 0.01272,
            0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272,
            0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01272, 0.01923,
            0.01923, 0.01923, 0.01923, 0.01923, 0.01923, 0.01923, 0.01923, 0.01923, 0.01923, 0.01923, 0.01923, 0.01923, 0.01923, 0.01923, 0.01658, 0.01658, 0.01658,
            0.01658, 0.01658, 0.01658, 0.01658, 0.01658, 0.01658, 0.01658, 0.01658, 0.01658, 0.01658, 0.01658, 0.01658, 0.01063, 0.01063, 0.01063, 0.01063, 0.01063,
            0.01063, 0.01063, 0.01063, 0.01063, 0.01063, 0.0001448, 0.0001448, 0.0001448, 0.0001448, 0.0001448, 0.0001448, 0.0001448, 0.0001448, 0.0001448, 0.0001448, 0.0001448},
           {0.01109, 0.01109, 0.01109, 0.01109, 0.01109, 0.01109, 0.01109, 0.01109, 0.01109, 0.01109, 0.01109, 0.01109, 0.01109, 0.01109, 0.01109, 0.01161, 0.01161,
            0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161,
            0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.01161, 0.02085,
            0.02085, 0.02085, 0.02085, 0.02085, 0.02085, 0.02085, 0.02085, 0.02085, 0.02085, 0.02085, 0.02085, 0.02085, 0.02085, 0.02085, 0.009572, 0.009572, 0.009572,
            0.009572, 0.009572, 0.009572, 0.009572, 0.009572, 0.009572, 0.009572, 0.009572, 0.009572, 0.009572, 0.009572, 0.009572, 0.01014, 0.01014, 0.01014, 0.01014, 0.01014,
            0.01014, 0.01014, 0.01014, 0.01014, 0.01014, 0.004042, 0.004042, 0.004042, 0.004042, 0.004042, 0.004042, 0.004042, 0.004042, 0.004042, 0.004042, 0.004042}},
        mortalityRatio = {1.06264, 1.04809},
        residualMigration = {{8.888, 10.96, 3.718, 1.699, 6.351, 2.695, 0.353, -0.9858, 0.3483, -1.65, 2.672, 1.354, 1.027, 0.03367, 0.6846, 3.707, -1.288,
            1.729, 0.7593, -1.887, -1.856, -14.84, -12.16, -3.2, -10.18, -4.465, 6.194, 1.854, -2.157, 2.892, 1.509, 4.51, 9.162, 5.537,
            4.171, 3.874, -0.81, -0.4822, 0.204, -1.149, 1.205, -2.716, 2.892, -1.051, -2.053, -0.6741, 1.72, -0.5479, 0.4504, 3.489, -0.0943,
            0.3359, -1.646, 0.1823, -2.636, 1.374, -3.858, 0.5231, -1.435, 1.667, -1.395, -1.479, 1.219, 1.16, 2.918, -0.6955, -0.02174, 0.2974,
            2.169, -1.487, -1.723, -0.2907, 0.875, -0.2301, -1.221, -2.596, 1.818, -1.912, -2.778, 2.748, -0.3127, -1.385, 1.697, 1.409, 0.6927,
            -3.126, 2.252, -1.492, -0.5908, 1.466, 0.3541, 0.7763, -0.461, 1.829, -1.025, 0.7605, -0.1713, -0.2239, -0.9896, -0.5917, 0.3867},
           {-1.554, 9.768, 1.722, 4.02, 0.3599, 9.359, 1.354, 5.344, 0.3487, 2.679, 0.6727, 5.02, 2.017, 0.3419, 2.356, 0.6973, 4.031,
            -2.299, 4.036, -14.29, -11.95, -17.95, -3.95, -3.628, -0.6053, -3.936, -1.613, 1.061, 3.086, 5.083, 3.721, 1.418, 6.765, 3.423,
            5.406, 4.089, -0.903, -0.9031, 7.776, 1.797, -1.203, 2.127, -0.1853, -2.498, -2.454, 2.211, 1.226, 0.5944, -0.009244, -0.3641, 1.077,
            0.4179, -0.8538, -0.4593, 2.229, 2.587, 0.9445, -2.319, -0.2261, -0.7394, 0.01119, -0.233, -0.6527, 0.01398, 0.5137, 1.376, 0.4948, -2.583,
            -1.044, -0.9771, -1.486, 1.791, -0.908, -2.7, -1.086, -1.879, -0.233, -1.86, 2.62, -0.431, -2.172, -1.34, -0.05496, 1.88, -1.124,
            1.732, -2.35, -1.822, 0.258, -0.1656, 0.03828, 2.149, 0.2233, 2.146, -2.259, -0.965, -1.497, -2.173, -0.4226, 0.3588, 1.305}},
        shareBoys = 0.52374,
        totalFertility = 1.82,
        totalFertilityMean5 = 1.946,
        births = 430,
        deaths = 451)
        "Motala vid slutet av 2020; dödlighetskvot 2016-2020, restflöden 2018-2020";
      constant DemographyYear motala2021 = DemographyYear(
        year = 2021,
        population = {{224, 235, 257, 267, 264, 274, 275, 275, 242, 272, 251, 283, 263, 276, 286, 267, 272,
            254, 277, 243, 235, 229, 239, 218, 210, 223, 240, 239, 284, 244, 298, 296, 237, 281,
            274, 264, 304, 242, 232, 254, 236, 227, 260, 252, 253, 230, 258, 293, 275, 299, 306,
            320, 299, 314, 292, 320, 307, 347, 290, 260, 271, 257, 268, 295, 275, 249, 275, 254,
            263, 260, 253, 254, 300, 257, 254, 257, 225, 211, 223, 194, 153, 132, 130, 125, 93,
            83, 90, 56, 47, 51, 37, 35, 29, 23, 18, 8, 5, 7, 0, 1, 1},
           {208, 208, 214, 218, 252, 246, 244, 241, 221, 251, 238, 264, 248, 245, 256, 254, 226,
            267, 254, 233, 198, 187, 163, 161, 169, 185, 197, 224, 230, 239, 252, 278, 258, 267,
            246, 261, 240, 236, 221, 234, 230, 259, 250, 236, 242, 240, 254, 275, 263, 280, 276,
            292, 309, 297, 319, 305, 311, 274, 262, 241, 279, 276, 247, 284, 296, 244, 266, 281,
            267, 241, 282, 263, 277, 256, 248, 268, 254, 270, 218, 184, 174, 159, 160, 159, 152,
            123, 115, 90, 95, 81, 77, 68, 58, 48, 27, 33, 13, 15, 6, 5, 9}},
        deathRisk = {{0.00221465, 0.000177804, 0.000103195, 6.69421e-05, 0.000104826, 7.19561e-05, 4.60647e-05, 5.41118e-05, 6.98733e-05, 3.71976e-05, 5.72165e-05, 8.21363e-05, 9.48679e-05, 8.20111e-05, 0.000126344, 0.000156052, 0.000189689,
            0.000316859, 0.000413656, 0.000510688, 0.000552646, 0.000597287, 0.000529661, 0.000555627, 0.000693785, 0.000728378, 0.000577072, 0.000655598, 0.000770426, 0.00065859, 0.000658825, 0.000626945, 0.000688784, 0.000665756,
            0.000680616, 0.000709758, 0.000790653, 0.000758071, 0.000709224, 0.000811344, 0.00101148, 0.000878139, 0.00099932, 0.000985006, 0.00112494, 0.00121715, 0.00138793, 0.00138805, 0.00152578, 0.0018108, 0.00196091,
            0.00214086, 0.00253717, 0.00265762, 0.00305436, 0.00340288, 0.00389649, 0.00410571, 0.00442974, 0.00510722, 0.00592003, 0.00615679, 0.00725894, 0.00797727, 0.00899832, 0.00978744, 0.0112965, 0.0118816,
            0.0132652, 0.0148351, 0.0161937, 0.0172755, 0.0194955, 0.0210949, 0.024087, 0.0266854, 0.0297255, 0.0339074, 0.0376788, 0.0424603, 0.0478922, 0.0546635, 0.063569, 0.0716545, 0.081168,
            0.0933384, 0.105305, 0.119121, 0.136121, 0.151253, 0.179508, 0.193582, 0.215246, 0.237814, 0.262173, 0.284145, 0.310099, 0.33758, 0.366562, 0.396979, 0.60477},
           {0.00186049, 0.000185624, 9.31958e-05, 8.51778e-05, 8.82742e-05, 6.28994e-05, 6.25666e-05, 5.33909e-05, 3.801e-05, 3.25014e-05, 6.28573e-05, 7.07747e-05, 4.8016e-05, 6.75527e-05, 0.000121035, 0.000101699, 0.000123041,
            0.000146588, 0.000201221, 0.000196223, 0.000267921, 0.000244647, 0.000222748, 0.000253944, 0.00024651, 0.000230381, 0.00023474, 0.000298648, 0.000274809, 0.000228339, 0.000318626, 0.000375623, 0.000335014, 0.000324245,
            0.000369329, 0.000375867, 0.000413944, 0.000465168, 0.000472337, 0.000503908, 0.000523464, 0.000602256, 0.000633298, 0.000697717, 0.000721403, 0.00079436, 0.000920928, 0.00104492, 0.00101888, 0.00126906, 0.00126227,
            0.00153569, 0.00162924, 0.00167129, 0.00197209, 0.00198801, 0.00244724, 0.00267313, 0.00302327, 0.00339829, 0.00361518, 0.00433916, 0.00451493, 0.00522854, 0.00568751, 0.00629531, 0.00721323, 0.00785888,
            0.00885987, 0.00959729, 0.0107205, 0.0119472, 0.0134529, 0.0150635, 0.0168678, 0.0185613, 0.0204596, 0.0231379, 0.0268695, 0.0299356, 0.0332351, 0.0393377, 0.0448361, 0.0504995, 0.0586923,
            0.065789, 0.0766279, 0.0865184, 0.101849, 0.114268, 0.132176, 0.146071, 0.165778, 0.188404, 0.207953, 0.22633, 0.249425, 0.274262, 0.300865, 0.329215, 0.503542}},
        mortalityImprovement = {{0.0244, 0.0244, 0.0244, 0.0244, 0.0244, 0.0244, 0.0244, 0.0244, 0.0244, 0.0244, 0.0244, 0.0244, 0.0244, 0.0244, 0.0244, 0.01389, 0.01389,
            0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389,
            0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01389, 0.01762,
            0.01762, 0.01762, 0.01762, 0.01762, 0.01762, 0.01762, 0.01762, 0.01762, 0.01762, 0.01762, 0.01762, 0.01762, 0.01762, 0.01762, 0.01427, 0.01427, 0.01427,
            0.01427, 0.01427, 0.01427, 0.01427, 0.01427, 0.01427, 0.01427, 0.01427, 0.01427, 0.01427, 0.01427, 0.01427, 0.01205, 0.01205, 0.01205, 0.01205, 0.01205,
            0.01205, 0.01205, 0.01205, 0.01205, 0.01205, 0.001581, 0.001581, 0.001581, 0.001581, 0.001581, 0.001581, 0.001581, 0.001581, 0.001581, 0.001581, 0.001581},
           {0.02288, 0.02288, 0.02288, 0.02288, 0.02288, 0.02288, 0.02288, 0.02288, 0.02288, 0.02288, 0.02288, 0.02288, 0.02288, 0.02288, 0.02288, 0.01158, 0.01158,
            0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158,
            0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.01158, 0.02219,
            0.02219, 0.02219, 0.02219, 0.02219, 0.02219, 0.02219, 0.02219, 0.02219, 0.02219, 0.02219, 0.02219, 0.02219, 0.02219, 0.02219, 0.01065, 0.01065, 0.01065,
            0.01065, 0.01065, 0.01065, 0.01065, 0.01065, 0.01065, 0.01065, 0.01065, 0.01065, 0.01065, 0.01065, 0.01065, 0.01227, 0.01227, 0.01227, 0.01227, 0.01227,
            0.01227, 0.01227, 0.01227, 0.01227, 0.01227, 0.00887, 0.00887, 0.00887, 0.00887, 0.00887, 0.00887, 0.00887, 0.00887, 0.00887, 0.00887, 0.00887}},
        mortalityRatio = {1.05794, 1.05567},
        residualMigration = {{6.47, 10.92, 2.053, 2.693, 6.019, 5.03, 0.02089, 1.348, 0.01772, 2.684, 0.01545, 3.685, -0.9749, 1.359, 1.022, 5.693, -0.9501,
            0.07026, -0.9175, -7.56, -6.846, -15.83, -11.19, -3.546, -7.536, -0.1614, -4.134, 4.488, -0.1729, 0.5595, 1.851, 1.515, 6.509, 5.21,
            3.5, 2.856, 1.859, -1.14, 0.8584, 0.8412, -1.472, -4.413, 4.558, 0.931, -1.745, -1.376, 0.6997, 1.424, -2.212, 1.824, 0.2489,
            -1.002, -3.272, 1.132, -3.127, 2.079, -3.128, 0.6153, -2.776, 2.628, -3.147, 0.1253, 1.559, 0.5189, 3.593, -0.8243, 1.178, 0.2717,
            1.067, -2.05, -0.9148, 0.878, 1.323, -0.6834, -0.6165, -2.151, -0.8071, -1.433, -2.55, 3.141, 1.415, -1.662, -0.3051, 1.958, -0.5351,
            -1.984, 3.856, -1.184, 0.1057, 1.663, -0.2059, 1.666, -0.1787, 2.103, -0.06482, -0.06356, -0.2332, -0.2442, -1.591, -0.3153, -0.144},
           {2.863, 6.408, 1.046, 2.353, -0.6454, 3.36, -0.9851, 2.014, -2.321, 4.008, 1.342, 4.682, 0.01999, 1.347, 0.3556, 1.355, 3.362,
            -2.634, 0.7018, -18.61, -18.63, -23.95, 0.04504, 0.3694, 3.047, -1.607, -0.6108, 1.397, -1.593, 6.735, 0.7208, -1.58, 5.441, 5.074,
            3.743, 3.094, 2.1, 2.767, 5.448, 0.8049, -0.5171, 6.8, 1.486, 1.165, -2.143, 0.8759, 0.5689, -0.3964, -1.697, 1.934, -1.277,
            -1.258, -0.8275, 0.533, 3.248, -0.04075, 0.3009, -0.6605, -0.2702, -0.4668, 0.3486, -0.3235, -1.706, 0.9907, 1.84, 0.6744, 0.8065, -1.289,
            -0.06028, -2.165, -2.5, 0.4526, -0.6597, -1.86, -1.775, 0.2425, 0.4757, -1.88, 4.539, 1.918, -1.58, -2.746, 0.6962, 3.186, -0.491,
            -0.9656, -2.218, -0.3593, -0.09866, 1.439, 1.565, 4.087, 0.6882, 1.527, -1.376, -1.443, -1.841, -1.709, -0.7821, 0.6373, 1.189}},
        shareBoys = 0.523749,
        totalFertility = 1.85,
        totalFertilityMean5 = 1.908,
        births = 420,
        deaths = 455)
        "Motala vid slutet av 2021; dödlighetskvot 2017-2021, restflöden 2019-2021";
      constant DemographyYear motala2022 = DemographyYear(
        year = 2022,
        population = {{189, 233, 242, 260, 268, 273, 267, 279, 277, 244, 277, 250, 285, 262, 274, 294, 263,
            274, 249, 270, 223, 219, 221, 242, 218, 207, 224, 229, 240, 291, 259, 309, 307, 244,
            277, 278, 266, 298, 245, 238, 249, 237, 228, 262, 247, 257, 235, 257, 295, 271, 301,
            307, 322, 300, 311, 297, 320, 306, 341, 285, 257, 273, 257, 267, 290, 275, 248, 277,
            248, 261, 263, 251, 252, 295, 249, 254, 249, 217, 207, 210, 185, 147, 127, 130, 121,
            85, 74, 84, 52, 40, 44, 33, 30, 19, 17, 14, 7, 4, 4, 0, 1},
           {180, 214, 212, 218, 220, 257, 244, 246, 244, 223, 253, 238, 266, 247, 247, 258, 252,
            229, 263, 238, 202, 173, 168, 158, 157, 169, 194, 218, 232, 233, 244, 265, 289, 258,
            262, 255, 263, 242, 237, 228, 228, 232, 265, 253, 240, 239, 245, 249, 275, 263, 284,
            271, 287, 315, 297, 320, 302, 310, 274, 266, 239, 273, 275, 245, 285, 297, 245, 262,
            282, 258, 237, 285, 261, 272, 254, 244, 262, 249, 262, 217, 175, 168, 155, 155, 150,
            143, 114, 108, 82, 86, 72, 69, 57, 49, 36, 20, 29, 7, 11, 5, 11}},
        deathRisk = {{0.00220404, 0.000187332, 0.000105518, 8.55056e-05, 0.000111906, 5.93631e-05, 5.22159e-05, 6.61057e-05, 6.18608e-05, 4.90642e-05, 5.37176e-05, 8.07921e-05, 8.61195e-05, 8.72211e-05, 0.000121022, 0.000151119, 0.000204191,
            0.000321373, 0.000381594, 0.000532408, 0.000541124, 0.000611262, 0.000532032, 0.000548391, 0.000651605, 0.000670348, 0.000588836, 0.000590993, 0.000741949, 0.000606703, 0.000629761, 0.000629275, 0.000654049, 0.000616561,
            0.000686336, 0.000744877, 0.000709258, 0.000761743, 0.00072794, 0.000765324, 0.000978069, 0.00089109, 0.00101206, 0.000981432, 0.00109481, 0.00120244, 0.00127206, 0.00141921, 0.00144009, 0.00172992, 0.00192791,
            0.00212411, 0.00236222, 0.00254027, 0.00302616, 0.00332897, 0.00374079, 0.00399575, 0.00434372, 0.00507885, 0.00584536, 0.00614056, 0.00715336, 0.00762048, 0.0087018, 0.0098361, 0.0112035, 0.011823,
            0.0133353, 0.0146293, 0.0159299, 0.0175581, 0.0194685, 0.0212555, 0.0238678, 0.0266337, 0.0295574, 0.0336062, 0.0367511, 0.0421958, 0.0482912, 0.0537638, 0.0632831, 0.0707642, 0.0795445,
            0.0925362, 0.103395, 0.117722, 0.1343, 0.148131, 0.17665, 0.194991, 0.214839, 0.239573, 0.264258, 0.284191, 0.310226, 0.337805, 0.366895, 0.397437, 0.60587},
           {0.00183575, 0.000207663, 7.50632e-05, 9.83271e-05, 8.06328e-05, 6.3244e-05, 5.23695e-05, 5.78096e-05, 3.22369e-05, 3.70779e-05, 5.92105e-05, 6.56958e-05, 3.87556e-05, 8.71656e-05, 0.000125171, 0.000120487, 0.000111868,
            0.000149186, 0.000193688, 0.000184869, 0.000249017, 0.000227299, 0.000215165, 0.000269116, 0.000223542, 0.000227309, 0.000236809, 0.000285719, 0.000248314, 0.000222981, 0.000327527, 0.000346637, 0.000314608, 0.000327994,
            0.000350338, 0.000380974, 0.000363894, 0.000427569, 0.000508438, 0.000521968, 0.000490014, 0.000604973, 0.000600249, 0.000664157, 0.000689041, 0.00075339, 0.00088348, 0.00100775, 0.000945212, 0.00120436, 0.00125476,
            0.00151149, 0.00161861, 0.00170494, 0.00188695, 0.00201314, 0.00239641, 0.00262321, 0.00299884, 0.00338222, 0.00353565, 0.0041891, 0.00446246, 0.00508149, 0.00549796, 0.00625218, 0.00702966, 0.00785577,
            0.00865169, 0.00965769, 0.0108036, 0.0118749, 0.0133767, 0.0148431, 0.0166301, 0.0184708, 0.0205615, 0.0228535, 0.0265748, 0.0300315, 0.0331329, 0.0389156, 0.0443576, 0.0502107, 0.0579679,
            0.0656165, 0.0754421, 0.0854544, 0.100275, 0.112779, 0.129848, 0.145385, 0.164163, 0.187285, 0.206264, 0.224329, 0.247303, 0.272033, 0.298537, 0.326804, 0.500246}},
        mortalityImprovement = {{0.01831, 0.01831, 0.01831, 0.01831, 0.01831, 0.01831, 0.01831, 0.01831, 0.01831, 0.01831, 0.01831, 0.01831, 0.01831, 0.01831, 0.01831, 0.0156, 0.0156,
            0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156,
            0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0156, 0.0194,
            0.0194, 0.0194, 0.0194, 0.0194, 0.0194, 0.0194, 0.0194, 0.0194, 0.0194, 0.0194, 0.0194, 0.0194, 0.0194, 0.0194, 0.01281, 0.01281, 0.01281,
            0.01281, 0.01281, 0.01281, 0.01281, 0.01281, 0.01281, 0.01281, 0.01281, 0.01281, 0.01281, 0.01281, 0.01281, 0.01102, 0.01102, 0.01102, 0.01102, 0.01102,
            0.01102, 0.01102, 0.01102, 0.01102, 0.01102, -0.0005635, -0.0005635, -0.0005635, -0.0005635, -0.0005635, -0.0005635, -0.0005635, -0.0005635, -0.0005635, -0.0005635, -0.0005635},
           {0.01818, 0.01818, 0.01818, 0.01818, 0.01818, 0.01818, 0.01818, 0.01818, 0.01818, 0.01818, 0.01818, 0.01818, 0.01818, 0.01818, 0.01818, 0.01592, 0.01592,
            0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592,
            0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.01592, 0.02204,
            0.02204, 0.02204, 0.02204, 0.02204, 0.02204, 0.02204, 0.02204, 0.02204, 0.02204, 0.02204, 0.02204, 0.02204, 0.02204, 0.02204, 0.008683, 0.008683, 0.008683,
            0.008683, 0.008683, 0.008683, 0.008683, 0.008683, 0.008683, 0.008683, 0.008683, 0.008683, 0.008683, 0.008683, 0.008683, 0.0105, 0.0105, 0.0105, 0.0105, 0.0105,
            0.0105, 0.0105, 0.0105, 0.0105, 0.0105, 0.00795, 0.00795, 0.00795, 0.00795, 0.00795, 0.00795, 0.00795, 0.00795, 0.00795, 0.00795, 0.00795}},
        mortalityRatio = {1.02622, 1.0482},
        residualMigration = {{1.161, 10.89, 5.721, 0.02781, 5.694, 8.029, -0.9888, 2.684, 1.691, 4.016, 1.353, 3.015, 0.3577, 1.023, 0.02844, 7.033, -0.2913,
            2.401, -1.914, -8.562, -14.51, -16.52, -9.192, -4.204, -7.536, 0.1424, -1.839, -2.184, 2.161, 3.881, 7.176, 5.515, 6.515, 5.831,
            -0.1461, 3.182, 3.539, -2.809, 0.8556, 2.851, -2.147, -3.758, 4.229, 2.932, -2.079, 0.6074, 3.327, 2.011, -1.528, -0.5568, 0.9087,
            0.2996, -0.9256, 1.739, -3.562, 3.023, -1.505, 0.2747, -3.748, 1.949, -4.217, 0.9867, 1.792, 0.4323, 1.87, 1.193, 1.001, 2.109,
            -0.4054, -0.6169, 0.7363, 0.9364, 0.909, -0.7452, -2.297, 0.1217, -0.3663, -0.3627, 0.104, 0.5666, 0.6161, -0.04379, -0.9881, 3.378, 0.1479,
            -3.022, 2.023, 0.8309, 0.8106, 1.948, -0.1594, 1.736, 0.1211, 0.1907, -0.2948, -0.03391, 0.9105, -0.4125, -0.9302, 0.05346, -0.05097},
           {6.505, 4.086, 1.041, 2.686, 0.6859, 3.688, -0.6514, 2.347, -0.9858, 4.338, 2.345, 3.011, 1.019, 1.013, 0.6936, 1.029, 0.7008,
            -1.307, 0.3757, -18.29, -21.96, -26.28, -4.634, -0.2967, -0.2845, -2.295, 2.384, 7.059, 1.06, 6.049, 0.06197, 2.76, 9.767, 3.409,
            2.094, 6.424, 3.424, 2.091, 2.764, 3.136, -3.523, 5.791, 2.83, 3.823, 0.4912, -0.1545, 2.88, -2.072, -1.058, 1.927, 0.369,
            -2.588, -1.822, 4.206, 5.223, -0.6956, -0.7216, -0.592, -0.2824, 1.527, -0.3391, -1.315, -1.139, -0.05129, 2.166, 1.608, 0.765, -2.62,
            0.985, -3.616, -1.62, 2.22, -0.5805, -1.883, 1.073, 1.532, -0.03768, -2, 1.841, 2.98, -3.145, -1.516, 1.344, 2.673, 0.2916,
            -1.891, -2.538, -0.2504, -0.197, 2.497, 2.163, 5.385, 0.4738, 1.429, -1.793, -1.604, 0.3841, -2.709, -0.04779, 0.6724, 2.546}},
        shareBoys = 0.52274,
        totalFertility = 1.57,
        totalFertilityMean5 = 1.806,
        births = 360,
        deaths = 420)
        "Motala vid slutet av 2022; dödlighetskvot 2018-2022, restflöden 2020-2022";
      constant DemographyYear motala2023 = DemographyYear(
        year = 2023,
        population = {{186, 191, 238, 246, 262, 272, 280, 280, 281, 277, 246, 274, 249, 290, 263, 273, 294,
            267, 272, 255, 267, 206, 206, 210, 224, 203, 196, 219, 223, 249, 291, 259, 309, 312,
            248, 290, 283, 279, 300, 249, 239, 252, 243, 224, 257, 248, 258, 241, 258, 296, 274,
            302, 313, 324, 302, 310, 292, 320, 300, 339, 284, 257, 269, 256, 262, 285, 276, 249,
            274, 249, 260, 258, 244, 247, 290, 241, 250, 241, 213, 203, 205, 174, 142, 122, 125,
            111, 80, 64, 74, 46, 35, 39, 29, 19, 12, 15, 11, 4, 3, 2, 0},
           {209, 181, 222, 216, 222, 220, 257, 248, 249, 242, 225, 254, 242, 270, 246, 245, 252,
            252, 232, 240, 218, 173, 164, 162, 145, 155, 161, 198, 214, 242, 244, 249, 275, 296,
            270, 267, 261, 268, 239, 239, 234, 227, 233, 264, 253, 241, 232, 239, 244, 274, 266,
            282, 274, 292, 312, 294, 314, 301, 307, 277, 263, 241, 272, 282, 244, 286, 295, 248,
            264, 281, 257, 235, 282, 258, 272, 247, 241, 251, 244, 247, 212, 172, 163, 148, 147,
            142, 135, 102, 98, 74, 73, 62, 58, 49, 37, 27, 18, 22, 4, 7, 13}},
        deathRisk = {{0.00227577, 0.000174251, 8.42929e-05, 0.00010053, 0.000113859, 6.24177e-05, 6.8968e-05, 5.6768e-05, 6.2672e-05, 6.49863e-05, 5.47716e-05, 8.03738e-05, 7.82366e-05, 8.65497e-05, 0.000123957, 0.000172611, 0.00021798,
            0.000286527, 0.000353517, 0.000545862, 0.000551424, 0.000567165, 0.000529212, 0.000536954, 0.000589974, 0.000661924, 0.00057066, 0.000554684, 0.000707706, 0.000625912, 0.000617335, 0.00063904, 0.00068219, 0.00056597,
            0.000663968, 0.000722793, 0.000706669, 0.000727167, 0.000757398, 0.000791773, 0.000916146, 0.000879687, 0.000978475, 0.0010121, 0.00104598, 0.00118088, 0.00121103, 0.00144706, 0.00146622, 0.00168706, 0.00183357,
            0.00207071, 0.00223678, 0.00239196, 0.00294799, 0.00329339, 0.00367971, 0.00396508, 0.00421427, 0.00492493, 0.00561754, 0.00597333, 0.00694406, 0.00752824, 0.00840104, 0.00960653, 0.0110812, 0.0114459,
            0.0131287, 0.0143836, 0.0157766, 0.0175189, 0.0191669, 0.0210864, 0.0237204, 0.0262538, 0.0289995, 0.0329925, 0.0367306, 0.0413928, 0.0474162, 0.052335, 0.0613535, 0.0690751, 0.0781148,
            0.0906687, 0.101303, 0.115044, 0.132331, 0.146538, 0.17328, 0.192833, 0.215394, 0.238238, 0.264152, 0.283986, 0.310238, 0.338073, 0.367463, 0.398342, 0.607947},
           {0.00182262, 0.000177185, 7.35298e-05, 0.000106411, 9.85108e-05, 4.9911e-05, 5.20125e-05, 5.22169e-05, 3.70766e-05, 3.87971e-05, 5.39488e-05, 6.94643e-05, 5.44556e-05, 8.4913e-05, 0.000103012, 0.000123033, 0.000107135,
            0.000146856, 0.000202618, 0.000164024, 0.000249748, 0.000219878, 0.000235274, 0.000251819, 0.000227388, 0.000245774, 0.000237379, 0.00026274, 0.000227682, 0.000209273, 0.000312309, 0.000350266, 0.000312712, 0.000320675,
            0.000360833, 0.000407971, 0.0003697, 0.000424269, 0.000514479, 0.000549935, 0.00049298, 0.000605312, 0.000612185, 0.000660074, 0.000674883, 0.000744105, 0.000849676, 0.000973989, 0.000947042, 0.00122106, 0.00126951,
            0.00154426, 0.00161204, 0.00172281, 0.00188635, 0.00192652, 0.00237565, 0.00258747, 0.00296763, 0.00341435, 0.00341401, 0.00409748, 0.00420078, 0.00497023, 0.00548035, 0.00621775, 0.00685181, 0.00792362,
            0.00852593, 0.00942477, 0.0105492, 0.0114562, 0.0132611, 0.0144322, 0.0164215, 0.0182697, 0.0204965, 0.0231236, 0.026195, 0.0298501, 0.0327236, 0.038075, 0.0433849, 0.049693, 0.056653,
            0.0646206, 0.0737524, 0.0841833, 0.0979023, 0.110038, 0.126897, 0.144076, 0.162777, 0.185431, 0.205196, 0.222196, 0.244977, 0.269507, 0.295803, 0.323865, 0.495736}},
        mortalityImprovement = {{0.01006, 0.01006, 0.01006, 0.01006, 0.01006, 0.01006, 0.01006, 0.01006, 0.01006, 0.01006, 0.01006, 0.01006, 0.01006, 0.01006, 0.01006, 0.01644, 0.01644,
            0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644,
            0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.01644, 0.02063,
            0.02063, 0.02063, 0.02063, 0.02063, 0.02063, 0.02063, 0.02063, 0.02063, 0.02063, 0.02063, 0.02063, 0.02063, 0.02063, 0.02063, 0.01265, 0.01265, 0.01265,
            0.01265, 0.01265, 0.01265, 0.01265, 0.01265, 0.01265, 0.01265, 0.01265, 0.01265, 0.01265, 0.01265, 0.01265, 0.01201, 0.01201, 0.01201, 0.01201, 0.01201,
            0.01201, 0.01201, 0.01201, 0.01201, 0.01201, -0.001078, -0.001078, -0.001078, -0.001078, -0.001078, -0.001078, -0.001078, -0.001078, -0.001078, -0.001078, -0.001078},
           {0.01759, 0.01759, 0.01759, 0.01759, 0.01759, 0.01759, 0.01759, 0.01759, 0.01759, 0.01759, 0.01759, 0.01759, 0.01759, 0.01759, 0.01759, 0.01259, 0.01259,
            0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259,
            0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.01259, 0.02107,
            0.02107, 0.02107, 0.02107, 0.02107, 0.02107, 0.02107, 0.02107, 0.02107, 0.02107, 0.02107, 0.02107, 0.02107, 0.02107, 0.02107, 0.007989, 0.007989, 0.007989,
            0.007989, 0.007989, 0.007989, 0.007989, 0.007989, 0.007989, 0.007989, 0.007989, 0.007989, 0.007989, 0.007989, 0.007989, 0.01162, 0.01162, 0.01162, 0.01162, 0.01162,
            0.01162, 0.01162, 0.01162, 0.01162, 0.01162, 0.007257, 0.007257, 0.007257, 0.007257, 0.007257, 0.007257, 0.007257, 0.007257, 0.007257, 0.007257, 0.007257}},
        mortalityRatio = {1.00427, 1.03923},
        residualMigration = {{-0.7316, 8.14, 4.042, 2.357, 3.368, 5.702, -0.3196, 7.355, 1.016, 3.683, 2.023, 1.678, 0.02029, 1.683, -0.6352, 5.704, -0.6151,
            3.382, -2.253, -4.577, -10.86, -16.22, -10.86, -5.87, -3.54, -7.88, -6.194, -3.87, 2.154, 3.517, 5.52, 5.177, 4.195, 4.52,
            0.4963, 5.183, 5.221, 2.868, 2.854, 5.542, -1.12, -0.7861, 4.56, 0.2424, -2.724, 0.9445, 2.953, 3.639, -0.2229, -0.553, 2.538,
            0.9154, 2.025, 2.711, -0.6403, 3.287, -0.9604, 1.865, -5.069, -0.08613, -1.953, 2.502, 0.3127, 0.2683, -1.163, -1.303, 2.872, 3.606,
            -1.233, 2.065, 3.132, 0.1538, 1.232, -1.674, -0.4769, 1.496, -0.4643, -1.616, 2.739, 1.195, 1.692, -0.7669, -0.919, 4.173, 0.7458,
            -1.319, 1.955, -0.0895, 1.336, 1.214, -0.2604, 1.809, 0.9836, -2.485, -0.2011, 0.5686, 0.7298, 0.1614, -0.5323, -0.05409, -0.2398},
           {12.4, 2.381, 5.039, 2.351, 2.025, 0.3542, -1.324, 2.014, 1.014, 1.344, 1.679, 1.68, 2.685, 2.351, 1.355, 2.369, -0.2999,
            1.027, 0.7122, -21.28, -23.96, -27.95, -5.964, -2.948, -4.623, -0.2985, 0.04762, 10.71, 0.7251, 7.382, 2.398, 3.758, 9.42, 5.091,
            1.768, 4.43, 5.11, 4.75, 0.09912, 3.453, -0.5305, 3.454, 4.17, 3.156, 2.151, -0.8489, -0.1466, -3.102, -2.073, 0.9533, 1.677,
            -1.936, -0.4916, 4.864, 1.238, -2.709, -2.723, 0.7761, 0.1454, 2.827, -1.037, -1.684, -2.199, 3.186, 2.809, 0.5869, 0.7846, 0.5525,
            2.952, -4.278, 0.6431, 1.58, -0.6121, -1.341, 1.821, -0.2442, 0.2422, -1.991, 0.6148, -0.1973, -1.215, 0.1805, 1.261, 1.855, 0.7893,
            -2.035, -1.146, -0.6203, 0.1133, 0.9027, -0.4628, 2.333, 0.6741, 1.264, -2.213, -1.218, 1.043, -1.496, -0.4241, 0.1324, 2.692}},
        shareBoys = 0.517825,
        totalFertility = 1.71,
        totalFertilityMean5 = 1.764,
        births = 381,
        deaths = 445)
        "Motala vid slutet av 2023; dödlighetskvot 2019-2023, restflöden 2021-2023";
      constant DemographyYear motala2024 = DemographyYear(
        year = 2024,
        population = {{181, 194, 190, 237, 251, 262, 270, 275, 278, 276, 281, 242, 270, 259, 284, 264, 278,
            293, 268, 265, 243, 246, 196, 192, 190, 216, 192, 182, 220, 226, 250, 293, 264, 312,
            312, 250, 291, 286, 275, 294, 249, 239, 258, 244, 221, 256, 247, 254, 235, 256, 295,
            271, 295, 316, 324, 302, 309, 289, 320, 297, 341, 280, 250, 267, 256, 261, 285, 274,
            250, 274, 241, 252, 256, 239, 245, 290, 236, 242, 235, 207, 197, 198, 167, 131, 117,
            117, 105, 74, 63, 63, 43, 33, 32, 23, 15, 10, 10, 8, 3, 2, 2},
           {154, 209, 183, 223, 216, 218, 220, 249, 250, 254, 246, 233, 255, 241, 268, 246, 248,
            252, 253, 224, 219, 182, 156, 144, 149, 142, 146, 168, 195, 214, 253, 258, 256, 278,
            288, 278, 272, 262, 270, 232, 246, 231, 234, 231, 259, 253, 238, 236, 242, 242, 275,
            269, 278, 275, 294, 307, 295, 310, 296, 308, 279, 266, 235, 274, 286, 242, 279, 296,
            251, 258, 283, 254, 234, 278, 259, 269, 245, 238, 250, 235, 239, 204, 166, 154, 142,
            137, 129, 130, 98, 91, 66, 64, 54, 45, 39, 29, 23, 11, 14, 3, 14}},
        deathRisk = {{0.00226146, 0.000178362, 0.000106136, 0.000102293, 0.000112186, 5.52463e-05, 7.47083e-05, 6.45489e-05, 7.09414e-05, 7.4761e-05, 5.48364e-05, 8.03337e-05, 8.64064e-05, 0.000110348, 0.00014174, 0.000160958, 0.000217671,
            0.000263192, 0.000337976, 0.00049978, 0.000463188, 0.000528457, 0.000522042, 0.000546952, 0.000519141, 0.000602438, 0.000552346, 0.000561231, 0.00069259, 0.000628038, 0.000583284, 0.000587656, 0.00061796, 0.000568884,
            0.000656983, 0.000696656, 0.000674035, 0.000695506, 0.000755697, 0.000784723, 0.000861052, 0.000891498, 0.00092703, 0.00103679, 0.00104458, 0.00115216, 0.0011588, 0.00148872, 0.00142855, 0.00161823, 0.00181065,
            0.00202151, 0.00219416, 0.00230122, 0.00285766, 0.00314059, 0.00358259, 0.00369941, 0.00415369, 0.00478617, 0.00535857, 0.00568848, 0.00648124, 0.00730747, 0.00830236, 0.00925332, 0.0104891, 0.0111845,
            0.0127348, 0.0140435, 0.0152679, 0.0172665, 0.0185696, 0.0208805, 0.0232168, 0.0256931, 0.0282457, 0.0322036, 0.0362893, 0.0400916, 0.0457995, 0.051008, 0.0587613, 0.0669111, 0.0762833,
            0.0879337, 0.0978278, 0.11198, 0.12861, 0.144378, 0.168201, 0.189793, 0.210052, 0.231226, 0.259088, 0.278132, 0.304026, 0.331505, 0.360545, 0.391084, 0.597272},
           {0.00177278, 0.000151632, 7.58488e-05, 9.03082e-05, 8.49771e-05, 5.29832e-05, 6.75504e-05, 6.13572e-05, 4.04792e-05, 4.60369e-05, 6.3653e-05, 6.03366e-05, 6.11616e-05, 8.11668e-05, 0.000109327, 0.000112675, 9.71373e-05,
            0.000153755, 0.000163346, 0.000173945, 0.000260818, 0.000206302, 0.000244015, 0.000242733, 0.000194331, 0.000211567, 0.00021925, 0.000241273, 0.000196382, 0.000224104, 0.000313056, 0.000325505, 0.000307891, 0.000332941,
            0.000353979, 0.000385593, 0.000373288, 0.000380843, 0.00051672, 0.000550307, 0.000482628, 0.000565134, 0.00061861, 0.000634048, 0.000620945, 0.000776213, 0.000846781, 0.000905984, 0.000951688, 0.00120775, 0.00130625,
            0.00146868, 0.00156031, 0.00167058, 0.00177229, 0.00186295, 0.00231066, 0.00245676, 0.00295328, 0.00330504, 0.00340354, 0.00392319, 0.00415228, 0.00483285, 0.0053868, 0.00609082, 0.00666306, 0.00786335,
            0.00820198, 0.00944504, 0.0102304, 0.0112246, 0.0129928, 0.0141483, 0.0158571, 0.0178467, 0.0199075, 0.0225772, 0.0258717, 0.0296012, 0.0320301, 0.0377163, 0.0423185, 0.0485027, 0.0556811,
            0.0630832, 0.0712725, 0.0833298, 0.0956639, 0.108611, 0.125974, 0.1427, 0.160465, 0.184443, 0.201937, 0.220193, 0.242784, 0.267117, 0.293203, 0.321045, 0.491483}},
        mortalityImprovement = {{0.009089, 0.009089, 0.009089, 0.009089, 0.009089, 0.009089, 0.009089, 0.009089, 0.009089, 0.009089, 0.009089, 0.009089, 0.009089, 0.009089, 0.009089, 0.02112, 0.02112,
            0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112,
            0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02112, 0.02534,
            0.02534, 0.02534, 0.02534, 0.02534, 0.02534, 0.02534, 0.02534, 0.02534, 0.02534, 0.02534, 0.02534, 0.02534, 0.02534, 0.02534, 0.01597, 0.01597, 0.01597,
            0.01597, 0.01597, 0.01597, 0.01597, 0.01597, 0.01597, 0.01597, 0.01597, 0.01597, 0.01597, 0.01597, 0.01597, 0.01686, 0.01686, 0.01686, 0.01686, 0.01686,
            0.01686, 0.01686, 0.01686, 0.01686, 0.01686, 0.005023, 0.005023, 0.005023, 0.005023, 0.005023, 0.005023, 0.005023, 0.005023, 0.005023, 0.005023, 0.005023},
           {0.02539, 0.02539, 0.02539, 0.02539, 0.02539, 0.02539, 0.02539, 0.02539, 0.02539, 0.02539, 0.02539, 0.02539, 0.02539, 0.02539, 0.02539, 0.01379, 0.01379,
            0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379,
            0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.01379, 0.02226,
            0.02226, 0.02226, 0.02226, 0.02226, 0.02226, 0.02226, 0.02226, 0.02226, 0.02226, 0.02226, 0.02226, 0.02226, 0.02226, 0.02226, 0.0123, 0.0123, 0.0123,
            0.0123, 0.0123, 0.0123, 0.0123, 0.0123, 0.0123, 0.0123, 0.0123, 0.0123, 0.0123, 0.0123, 0.0123, 0.01512, 0.01512, 0.01512, 0.01512, 0.01512,
            0.01512, 0.01512, 0.01512, 0.01512, 0.01512, 0.01001, 0.01001, 0.01001, 0.01001, 0.01001, 0.01001, 0.01001, 0.01001, 0.01001, 0.01001, 0.01001}},
        mortalityRatio = {0.96813, 1.02617},
        residualMigration = {{-1.414, 6.772, 3.701, 2.024, 2.698, 4.366, -0.65, 4.022, 0.6801, -0.9784, 3.687, -2.655, -0.982, 4.688, -2.299, 2.712, 0.3771,
            1.721, -1.936, -2.585, -11.55, -17.9, -10.22, -7.206, -12.54, -8.567, -6.879, -9.872, -1.207, 6.494, 5.502, 4.491, 5.5, 5.178,
            0.145, 6.515, 2.87, 3.514, 0.5228, 1.547, -1.124, 1.538, 4.562, -0.1049, -4.055, 1.605, 1.95, 0.6033, -0.6189, -1.271, 1.77,
            0.1753, 0.924, 2.656, 0.3741, 2.159, -1.057, -0.279, -2.817, -2.098, 0.6836, 0.7096, -2.221, 0.3175, -1.373, 0.2225, 2.4, 2.979,
            0.09751, 2.836, 1.455, -1.194, 0.6221, -0.1287, 0.4365, 3.194, 0.5662, -1.399, 2.209, -0.1034, 1.195, -0.02358, 1.809, 2.036, 3.481,
            -0.4068, 1.035, 0.2902, 2.362, -0.962, 1.461, 2.457, 1.132, -3.109, -1.175, 1.313, 0.2687, -0.1234, -0.06644, -0.2, 0.08915},
           {8.748, 2.718, 4.699, 3.016, 2.029, 0.351, -0.6546, -0.6451, 2.685, 1.679, 2.681, 3.019, 2.347, 0.6833, -0.3127, 0.03599, -1.635,
            1.023, 0.0407, -15.62, -23.95, -29.95, -14.97, -10.29, -9.959, -1.639, -2.628, 10.71, 0.3866, 4.379, 9.059, 10.75, 9.407, 3.431,
            -0.2344, 7.428, 4.44, 2.76, 0.09009, 0.7857, 2.461, -0.5514, 4.803, 0.1568, -0.1718, -0.5242, -1.484, -2.137, -0.4313, -0.7119, 3.01,
            -0.9398, -1.565, 4.485, 0.2139, -1.767, -2.07, -1.232, -1.878, 3.543, -0.08831, 0.6369, -1.585, 3.497, 2.69, 1.526, -0.9051, 1.817,
            4.099, -3.019, 1.595, 2.053, 0.9986, -0.3163, 3.47, -0.4773, 0.9511, -1.162, 1.352, -1.982, -0.7073, 0.5046, 1.391, 0.006988, 0.07796,
            -0.4257, -1.208, 0.839, 1.414, 0.8947, -1.029, 0.5575, -0.2494, -0.3574, -2.188, -1.142, 2.751, -1.637, -0.9569, 0.1433, 3.501}},
        shareBoys = 0.520189,
        totalFertility = 1.47,
        totalFertilityMean5 = 1.684,
        births = 336,
        deaths = 402)
        "Motala vid slutet av 2024; dödlighetskvot 2020-2024, restflöden 2022-2024";
      constant DemographyYear motala2025 = DemographyYear(
        year = 2025,
        population = {{180, 183, 199, 196, 241, 262, 261, 263, 276, 275, 276, 280, 242, 270, 259, 285, 255,
            275, 298, 251, 243, 223, 216, 195, 191, 193, 214, 191, 173, 222, 227, 248, 290, 258,
            311, 307, 248, 301, 289, 274, 291, 250, 242, 256, 249, 221, 252, 242, 253, 236, 250,
            291, 266, 292, 308, 322, 298, 304, 284, 319, 295, 341, 278, 245, 259, 252, 260, 278,
            272, 241, 271, 237, 248, 252, 233, 240, 283, 223, 236, 230, 192, 190, 189, 160, 118,
            109, 106, 98, 66, 58, 56, 38, 24, 31, 17, 12, 8, 4, 3, 3, 4},
           {163, 150, 217, 190, 217, 216, 217, 219, 249, 247, 258, 243, 230, 252, 242, 263, 244,
            245, 249, 234, 196, 183, 176, 151, 142, 165, 138, 150, 167, 196, 218, 255, 249, 257,
            278, 291, 280, 277, 267, 270, 232, 246, 226, 239, 228, 256, 250, 236, 241, 240, 238,
            270, 265, 273, 273, 291, 298, 287, 310, 296, 309, 281, 261, 241, 274, 287, 242, 280,
            290, 248, 255, 284, 251, 232, 278, 254, 262, 240, 228, 242, 222, 236, 194, 149, 145,
            134, 128, 114, 114, 96, 81, 58, 51, 46, 34, 33, 19, 19, 8, 11, 9}},
        deathRisk = {{0.00207355, 0.000158727, 0.000108964, 0.000118402, 0.00012408, 5.43765e-05, 7.7932e-05, 5.59708e-05, 6.59338e-05, 7.129e-05, 4.48773e-05, 6.58185e-05, 6.2138e-05, 0.000108373, 0.000122362, 0.000185461, 0.000188406,
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
            0.0608351, 0.0690991, 0.0811102, 0.0920682, 0.104318, 0.123329, 0.138694, 0.15742, 0.178304, 0.195214, 0.215042, 0.237162, 0.261003, 0.28658, 0.313899, 0.480401}},
        mortalityImprovement = {{0.01508, 0.01508, 0.01508, 0.01508, 0.01508, 0.01508, 0.01508, 0.01508, 0.01508, 0.01508, 0.01508, 0.01508, 0.01508, 0.01508, 0.01508, 0.02595, 0.02595,
            0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595,
            0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02595, 0.02829,
            0.02829, 0.02829, 0.02829, 0.02829, 0.02829, 0.02829, 0.02829, 0.02829, 0.02829, 0.02829, 0.02829, 0.02829, 0.02829, 0.02829, 0.018, 0.018, 0.018,
            0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.018, 0.01995, 0.01995, 0.01995, 0.01995, 0.01995,
            0.01995, 0.01995, 0.01995, 0.01995, 0.01995, 0.008992, 0.008992, 0.008992, 0.008992, 0.008992, 0.008992, 0.008992, 0.008992, 0.008992, 0.008992, 0.008992},
           {0.02585, 0.02585, 0.02585, 0.02585, 0.02585, 0.02585, 0.02585, 0.02585, 0.02585, 0.02585, 0.02585, 0.02585, 0.02585, 0.02585, 0.02585, 0.02081, 0.02081,
            0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081,
            0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02081, 0.02647,
            0.02647, 0.02647, 0.02647, 0.02647, 0.02647, 0.02647, 0.02647, 0.02647, 0.02647, 0.02647, 0.02647, 0.02647, 0.02647, 0.02647, 0.01493, 0.01493, 0.01493,
            0.01493, 0.01493, 0.01493, 0.01493, 0.01493, 0.01493, 0.01493, 0.01493, 0.01493, 0.01493, 0.01493, 0.01493, 0.01685, 0.01685, 0.01685, 0.01685, 0.01685,
            0.01685, 0.01685, 0.01685, 0.01685, 0.01685, 0.01017, 0.01017, 0.01017, 0.01017, 0.01017, 0.01017, 0.01017, 0.01017, 0.01017, 0.01017, 0.01017}},
        mortalityRatio = {0.953743, 1.06303},
        residualMigration = {{0.07489, 4.378, 3.027, 3.025, 3.695, 5.031, 1.35, 0.3583, 0.343, -2.649, 2.015, -2.652, -1.65, 5.018, -1.639, 0.3704, -1.274,
            0.05339, 1.384, -5.926, -12.24, -19.24, -17.57, -8.558, -12.89, -6.579, -7.892, -6.558, -4.552, 4.802, 0.8212, 0.1471, 0.814, 0.8447,
            1.146, 3.533, 1.502, 8.848, 0.508, -0.7968, -0.4544, 1.512, 5.207, -1.468, -0.7533, 0.2458, -1.039, -0.7201, -1.653, 0.3667, -0.9383,
            -1.511, -1.463, 1.315, -1.307, -0.2228, -2.474, -1.646, -2.603, -0.7529, 0.9742, 0.02783, -2.942, -1.166, -2.551, -1.297, 2.315, -0.1794,
            1.371, 0.2563, -0.6333, -2.115, -0.2881, -0.3387, 0.7021, 1.333, 0.9003, -3.16, 1.471, 2.334, -1.021, -0.08941, 1.182, -0.2834, 0.07282,
            -0.3415, 0.876, 0.06051, 1.279, 0.03888, 1.675, 1.986, -0.7179, -0.1657, -1.414, 1.127, -0.02178, -1.419, -0.7214, 0.1117, 0.6901},
           {6.258, -0.6604, 6.025, 4.015, -0.6458, -1.307, -0.3221, -1.647, 1.686, 0.01926, 3.348, 2.023, 0.6777, 0.02175, -0.6488, -2.302, -1.637,
            -0.9751, 0.3711, -16.63, -22.95, -33.61, -10.62, -10.28, -9.304, 3.701, -6.967, 5.031, -2.616, 3.714, 8.712, 7.069, 2.74, 3.779,
            1.432, 5.439, 4.458, 3.765, 1.443, -1.544, 4.459, -1.196, 1.139, 0.8212, -2.497, -0.5284, -4.138, -1.14, 1.218, -1.401, 0.355,
            -0.9261, -1.267, 0.771, -0.4636, -3.124, -4.05, -3.605, -1.876, 2.211, 0.9173, 3.28, -2.941, 6.124, 2.354, 1.494, -1.248, 3.428,
            1.823, -0.997, 1.927, 1.402, 0.6868, 0.4773, 4.294, -0.7048, 0.6537, -1.325, 0.5642, -3.952, -1.462, 2.423, -0.08715, -3.951, 0.03717,
            -0.3122, -0.8471, -1.424, 0.07558, 3.498, -0.8747, 0.354, -1.011, 0.007874, -2.006, 0.188, 0.5242, -0.01791, -0.9329, 0.3227, 2.574}},
        shareBoys = 0.518762,
        totalFertility = 1.57,
        totalFertilityMean5 = 1.634,
        births = 337,
        deaths = 459)
        "Motala vid slutet av 2025; dödlighetskvot 2021-2025, restflöden 2023-2025";

      function forYear "SCB-data för ett basår"
        input Integer year "Basår";
        output DemographyYear data "Motala vid basårets slut";
      algorithm
        assert(year >= 2020 and year <= 2025, "Motala.Data.SCB har basåren 2020-2025, inte " + String(year));
        data := if year == 2020 then motala2020 elseif year == 2021 then motala2021 elseif year == 2022 then motala2022 elseif year == 2023 then motala2023 elseif year == 2024 then motala2024 else motala2025;
      end forYear;

      function populationForYear "Befolkning per ettårsålder och kön vid ett basårs slut"
        input Integer year "Basår";
        output Real population[2, 101] "Befolkning per ettårsålder och kön";
      protected
        DemographyYear data;
      algorithm
        data := forYear(year);
        population := data.population;
      end populationForYear;

      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Text(textColor = {35, 50, 65}, extent = {{-92, -30}, {92, 40}}, textString = "SCB"), Text(textColor = {90, 110, 130}, extent = {{-92, -80}, {92, -35}}, textString = "demografi")}), Documentation(info = "<html><p>Källa: SCB, Statistikdatabasen (CC BY 4.0). Tabeller: BefProgDodstalNb, BefProgFruktTotNb, BefProgOsiktRegN, BefolkningCKM, BefolkningNy, DodaHandelseK, DodaHandelseKCKM, FoddaK, FoddaKCKM, FruktsamhetSum, LivslangdEttariga.
  Arkiv data/downloads/20261108T124756Z; bearbetat av scripts/prepare_demography.py till data/demography-inputs.json.</p>
  <p>Varje basår använder bara data fram till det året, så att en prognos från det kan jämföras med det som hände sedan.
  Varje basår har en egen dödlighetstrend, skattad ur rikets livslängdstabeller de tio åren fram till basåret.
  SCB:s framskrivna dödlighet och fruktsamhet kommer från framskrivningen 2026 och är bara rättvisa för basåret 2025.</p></html>"));
    end SCB;
    annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Text(textColor = {35, 50, 65}, extent = {{-92, -30}, {92, 40}}, textString = "Data"), Text(textColor = {90, 110, 130}, extent = {{-92, -80}, {92, -35}}, textString = "basår")}), 
      Documentation(info = "<html><p>Varje konstant innehåller det som publicerats för ett basår. Modellen kalibrerar
dödlighet och restflöden från den (se Assumptions). Starta från ett annat år med
<code>Annual(base = Data.motala2024)</code>. Värdena avser kommunen, inte koncernen.</p>
<p>Källor: Motala kommuns årsredovisningar, SCB och Kolada; se respektive post och paketet <code>SCB</code>.</p></html>"));
  end Data;

  model Annual "Motalas ekonomi år för år: demografi, verksamhet, drift, intäkter, kapital och finans"
    extends Kommunekonomi.Annual(base = Data.motala2025, olderShares = Data.SCB.olderShares(Data.SCB.motala2025.population));
    annotation(experiment(StartTime = 2025, StopTime = 2033, Interval = 1),
      Documentation(info = "<html><p><b>Tid: start 2025 (bokslutet 31 december 2025), slut 2033.</b> Med ett annat basår
(<code>base</code>) ska starttiden vara det året.</p>
<p><a href=\"modelica://Kommunekonomi.Annual\">Kommunekonomi.Annual</a> med Motalas bokslut 2025 (<code>Data.motala2025</code>)
som standard. Starta från ett annat år med <code>Annual(base = Data.motala2024)</code>; basåren 2020-2025 finns.
Uppdelningen av de äldre i femgruppsdemografin är SCB:s för 2025.</p></html>"));
  end Annual;
  model Continuous "Motalas ekonomi med kontinuerlig tid inom året: lager och flöden"
    extends Kommunekonomi.Continuous.Economy(base = Data.motala2025, olderShares = Data.SCB.olderShares(Data.SCB.motala2025.population));
    annotation(experiment(StartTime = 2025, StopTime = 2033, Interval = 0.0833333333333333),
      Documentation(info = "<html><p><b>Tid: start 2025 (bokslutet 31 december 2025), slut 2033.</b> Samma antaganden och utdata som
<a href=\"modelica://Motala.Annual\">Annual</a>, men pengarna är lager och flöden i kontinuerlig tid inom året
(<a href=\"modelica://Kommunekonomi.Continuous.Economy\">Kommunekonomi.Continuous.Economy</a>). Årsvärdena gäller vid
årsskiftena; mellan dem visas året månad för månad.</p></html>"));
  end Continuous;
  package Examples "Färdiga modeller att simulera"
    model Hindcast2025 "Starta i bokslutet 2024 och räkna fram 2025; jämför med utfallet 105 och budgeten 96 mnkr"
      extends Annual(base = Data.motala2024, horizon = 1);
      annotation(experiment(StartTime = 2024, StopTime = 2025, Interval = 1),
        Documentation(info = "<html><p><b>Tid: start 2024 (bokslutet 2024), slut 2025.</b></p>
<p>Ett år från bokslutet 2024 med modellens standardantaganden. Utfall 2025: resultat 105 mnkr. Budget 2025: 96 mnkr.
De antaganden som var kända hösten 2024 (SKR, budget, pensionsprognos) är ännu inte inlagda.</p></html>"));
    end Hindcast2025;

    model AnnualCohort "Annual med ettårsåldrar per kön (SCB-data); summerad fruktsamhet 1,41 om inget annat anges"
      extends Annual(revenuePopulation0 = Data.SCB.groups(Data.SCB.populationForYear(base.year - 1)),
        redeclare Kommunekonomi.Components.CohortDemography demography(data = Data.SCB.forYear(base.year), reportedTotal = sum(p0),
        migrationWeights = migrationWeights));
      annotation(experiment(StartTime = 2025, StopTime = 2033, Interval = 1),
        Documentation(info = "<html><p><b>Tid: start 2025 (bokslutet 2025), slut 2033.</b></p>
<p>Samma ekonomi som Annual, men demografin är Kommunekonomi.Components.CohortDemography: ettårsåldrar per kön, dödsrisker som fortsätter
sjunka i den historiska takten (sätt <code>improvement = Data.SCB.mortalityImprovement</code> för SCB:s framskrivning) och
äldreomsorgen viktad efter 65-79, 80-89 och 90+. Byt födelsemodell i demografins parameterdialog eller med
<code>redeclare Kommunekonomi.Components.Fertility.Projected fertility(firstYear = 2026)</code>.</p></html>"));
    end AnnualCohort;

    model ContinuousCohort "Continuous med ettårsåldrar per kön (SCB-data)"
      extends Continuous(revenuePopulation0 = Data.SCB.groups(Data.SCB.populationForYear(base.year - 1)),
        redeclare Kommunekonomi.Components.CohortDemography demography(data = Data.SCB.forYear(base.year), reportedTotal = sum(p0),
        migrationWeights = migrationWeights));
      annotation(experiment(StartTime = 2025, StopTime = 2033, Interval = 0.0833333333333333),
        Documentation(info = "<html><p>Som <a href=\"modelica://Motala.Examples.AnnualCohort\">AnnualCohort</a>, men med kontinuerlig tid
inom året. Demografin flyttar ettårsåldrarna en gång per år och räknar fram årets slut när året börjar.</p></html>"));
    end ContinuousCohort;

    model Budget2026 "Kommunens budget 2026-2028: budgetens investeringar, skatt och bidrag; modellens kostnader, räntor och lån"
      extends AnnualCohort(horizon = 3, investmentPath = Data.budget2026.investment, referenceTax = Data.budget2026.tax,
        referenceGrants = Data.budget2026.grants, revenueFromReference = true);
      // Budgetens siffror för samma år, att plotta mot modellens. Vid starttiden 2025 visas modellens värden.
      Real budgetResult = if year > 2025 then Data.budget2026.result[year - 2025] else result "Årets resultat enligt budgeten, mnkr";
      Real budgetNetCost = if year > 2025 then Data.budget2026.netCost[year - 2025] else cost "Verksamhetens nettokostnad enligt budgeten, mnkr";
      Real budgetDepreciation = if year > 2025 then Data.budget2026.depreciation[year - 2025] else depreciation "Avskrivningar enligt budgeten, mnkr";
      Real financialCost = interest + otherFinancialExpense "Finansiella kostnader i modellen: räntor och övriga, mnkr";
      Real budgetFinancialCost = if year > 2025 then Data.budget2026.financialCost[year - 2025] else financialCost "Finansiella kostnader enligt budgeten, mnkr";
      Real budgetNewLoans = if year > 2025 then Data.budget2026.newLoans[year - 2025] else 0 "Nya lån enligt budgeten, mnkr";
      Real resultDifference = result - budgetResult "Modellens resultat minus budgetens, mnkr";
      Real netCostDifference = cost - budgetNetCost "Modellens nettokostnad minus budgetens, mnkr";
      annotation(experiment(StartTime = 2025, StopTime = 2028, Interval = 1),
        Documentation(info = "<html><p><b>Tid: start 2025 (bokslutet 2025), slut 2028.</b></p>
<p>Följer kommunens budget 2026 med plan 2027-2028 där budgeten fattar beslut eller gör antaganden: investeringarna
(755, 897 och 961 mnkr) och skatt och bidrag enligt budgetens belopp, som bygger på SKR:s prognos från oktober 2025.
Modellen räknar resten: verksamhetens kostnader utifrån befolkning, löner och priser, avskrivningar, räntor och nya lån.</p>
<p>Jämför med budgetens egna siffror: plotta <code>result</code> mot <code>budgetResult</code>, <code>cost</code> mot
<code>budgetNetCost</code>, <code>depreciation</code> mot <code>budgetDepreciation</code>, <code>financialCost</code> mot
<code>budgetFinancialCost</code> och <code>borrowing</code> mot <code>budgetNewLoans</code>.</p>
<p>Kända skillnader: modellen startar i bokslutet 2025 (kassa 81 mnkr), medan budgeten räknade med 164 mnkr och tar 64 mnkr
ur kassan 2026; modellen lånar i stället hela gapet. Räntan är modellens standardantagande, 2,23 procent på
ingående skuld (basårets räntekostnad delad med skulden vid årets början). Löne- och prisökningar är modellens standardvärden, inte budgetens.</p></html>"));
    end Budget2026;

    model Hindcast2025Cohort "Starta i bokslutet 2024 med ettårsåldrar och räkna fram 2025"
      extends AnnualCohort(base = Data.motala2024, horizon = 1);
      annotation(experiment(StartTime = 2024, StopTime = 2025, Interval = 1),
        Documentation(info = "<html><p><b>Tid: start 2024 (bokslutet 2024), slut 2025.</b></p></html>"));
    end Hindcast2025Cohort;

    model DemographyOnly "Demografin ensam, från valfritt basår 2020-2025, utan scenarioförändringar"
      parameter Integer horizon = 5 "Antal år att räkna fram";
      inner Kommunekonomi.Components.Calendar calendar(horizon = horizon, baseYear = demography.data.year) "Gemensam årskalender";
      replaceable Kommunekonomi.Components.CohortDemography demography(data = Data.SCB.motala2020) constrainedby Kommunekonomi.Components.DemographyBase "Demografi"
        annotation(choicesAllMatching = true);
    equation
      demography.drivers.residualMigration = zeros(5);
      demography.drivers.migrationDelta = 0;
      demography.drivers.birthChange = 0;
      annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Text(textColor = {35, 50, 65}, extent = {{-92, -30}, {92, 40}}, textString = "Befolkning"), Text(textColor = {90, 110, 130}, extent = {{-92, -80}, {92, -35}}, textString = "pröva 2020-2025")}), experiment(StartTime = 2020, StopTime = 2025, Interval = 1),
        Documentation(info = "<html><p><b>Tid: start 2020 (basåret), slut 2025.</b> Med ett annat basår ska starttiden vara det
året.</p>
<p>För att pröva demografin mot det som hände: starta i ett basår och jämför födda, döda och folkmängd med SCB:s utfall
åren efter (scripts/hindcast_demography.py).</p></html>"));
    end DemographyOnly;
    annotation(Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {90, 110, 130}, fillColor = {245, 248, 250}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Polygon(lineColor = {35, 115, 85}, fillColor = {35, 115, 85}, fillPattern = FillPattern.Solid, points = {{-35, 55}, {55, 0}, {-35, -55}, {-35, 55}})}));
  end Examples;
  annotation(uses(Kommunekonomi(version = "0.1.0")), Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {Rectangle(lineColor = {40, 95, 140}, fillColor = {235, 245, 252}, fillPattern = FillPattern.Solid, extent = {{-100, -100}, {100, 100}}, radius = 25), Rectangle(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, extent = {{-70, -70}, {-35, 0}}), Rectangle(lineColor = {40, 95, 140}, fillColor = {40, 95, 140}, fillPattern = FillPattern.Solid, extent = {{-17, -70}, {18, 30}}), Rectangle(lineColor = {35, 115, 85}, fillColor = {35, 115, 85}, fillPattern = FillPattern.Solid, extent = {{35, -70}, {70, 60}})}), Documentation(info = "<html>
<p><b>Motala ekonomilabb</b> räknar Motala kommuns ekonomi år för år: befolkning, verksamhet, drift, skatt och bidrag,
investeringar, resultat och lån. Belopp i mnkr och löpande priser; tiden är kalenderår.</p>
<ul>
<li><a href=\"modelica://Motala.Handledning.Ordlista\">Ordlista</a>: de ekonomiska begreppen.</li>
<li><a href=\"modelica://Motala.Annual\">Annual</a>: modellen som webbplatsen kör, från bokslutet 2025.</li>
<li><a href=\"modelica://Motala.Examples.AnnualCohort\">Examples.AnnualCohort</a>: samma modell med ettårsåldrar och
äldreomsorgen viktad efter ålder.</li>
<li><a href=\"modelica://Motala.Examples.Hindcast2025\">Examples.Hindcast2025</a>: från bokslutet 2024 fram till 2025,
för att jämföra med utfallet.</li>
</ul>
<p>Modellen bygger på biblioteket <a href=\"modelica://Kommunekonomi\">Kommunekonomi</a>; det här paketet har Motalas data
och exempel.</p>
<p>Källor: Motala kommuns årsredovisningar och budgetar, SCB och Kolada; se <a href=\"modelica://Motala.Data\">Data</a>.
Detta är en forskningsmodell, inte kommunens officiella prognos.</p></html>"));
end Motala;
