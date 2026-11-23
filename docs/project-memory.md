# Projektminne: Motala ekonomilabb

Uppdaterat 2026-11-23. Överst läget och det som är öppet; därunder daterade avsnitt,
inte i strikt ordning (de senaste, 2026-11-20, ligger sist).

## Läget 2026-11-23

- Mål: ett interaktivt verktyg för beslutsfattare. Bakåttestet är en kontroll, inte målet.
- Webbplatsen kör `Kommunekonomi.Annual` i webbläsaren (OpenModelica wasm-jit) för alla 13 kommuner i
  Östergötland, med start 2025 eller 2026. Scenarier: Högre ränta, Högre inflation, flytt- och stressbanor.
- `Kommunekonomi.Continuous.Economy` (lager och flöden) och den lokala MCP-servern (`scripts/mcp_server.py`)
  finns men är inte kopplade till webbplatsen.
- Bakåttest från SKR:s decembercirkulär 2020–2024: Motalas resultat ett år fram fel med i snitt 40 mnkr,
  budgeten 24. Största felen: löner och bidrag efter tre år.
- Dokumentation omskriven 2026-11-23: ny README, `modelica/README.md` och `docs/methodology.md`.
  M2-delen av README flyttad till `research/M2.md`; `docs/dynamics-equations.md` flyttad till
  `research/dynamics-equations.md`. Lokal gren `master` (gammal historik från 2026-11-06) raderad.

## Öppet

1. PR #1 (räntebindning, Högre ränta och inflation, dokumentation) är sammanslagen i main 2026-11-23.
2. Ränte- och inflationsscenarierna provades i headless Chromium 2026-11-23 för Linköping och Motala:
   de räknar och flaggar underskott. Siffrorna är inte granskade mot något utfall.
3. Beslut för beslutsfattare: daterade beslut på webben och förklaring av vad som ändrade resultatet.
   MCP-servern har beslut med motivering; webben har det inte. (Startvy med kommunkort, grupperade
   antaganden med förklaringar, scenarioknappar, balanskravsflagga med valfritt resultatmål och delbar
   adress byggdes 2026-11-23 på grenen `site-navigation`. Balanskravet: kommunallagen 11 kap. 5 § och
   12 §, kontrollerat i två sammanfattningar av lagtexten på riksdagen.se och lagen.nu, inte ordagrant.)
4. Var den kontinuerliga modellen och MCP-servern ska höra hemma. Webbläsaren tar ett Euler-steg per år.
5. Lönefelet efter tre år (−103 mnkr för Motala): kontrollera löneglidning och bemanning mot
   årsredovisningarna innan en ny mekanism läggs till.
6. Från granskningen av länsgrenen: arbetaren laddar alla 13 kommunpaket vid start; kommunlistan finns i
   både `municipalities.js` och `base-years.json`; Finspångs novemberbefolkning läses ur två arkiv.
7. Underlag: delårsrapport 2026 ej funnen i diariet; historiska SKR- och budgetversioner med datum bara
   delvis insamlade; Linköpings ränta saknar källa för 2020, 2021 och 2023.
8. Norrköpings resultat 2025 i kommunkorten är +3 596 mnkr, 33,6 % av skatt och bidrag, ur SCB TAB6777.
   Ovanligt högt; inte kontrollerat mot årsredovisningen.

## Sparade scenarier, åldersviktad skatt och Bråta Hagar

- Jämförelser kan spara namngivna körningar, hela körningens utdata,
  reglage och Modelica-fingeravtryck i webbläsaren. Sparade utdata
  används vid jämförelse; öppning i labbet gör en ny körning. Vyn
  ”Varför skiljer sig banorna?” visar befolkning, behov, finansiering
  och en resultatskillnad uppdelad på intäkter och kostnader per år.
- Tillval i det importerade SKR-delpostläget: åldersprofil från SCB
  TAB744, 2019 för basår 2021 respektive 2024 för basår 2025.
  Källan grupperar 20–64 år; motsvarar modellens 19–64 med en
  mindre avgränsningsskillnad. Relativa inkomster väger åldersmixen
  mot basåret; befolkningsnivån följer fortfarande novembermekanismen.
  Inkomstutjämningen motverkar åldersmixens skatteunderlagsändring
  med länssatsen 18,93 procent (förordning 2004:881, 2 §).
  Avräkningar och andra delposter följer den befintliga programlogiken.
  Åldersprofilerna för flyttscenarier är illustrativa.
- Omkörning av `scripts/evaluate_model_variants.mjs` återgav tidigare
  modellvärden till numerisk tolerans för grundmodellen och tidigare
  varianter, inklusive fem bokslutsbasår 2020–2024. Den nya
  åldersvikten gav 181,0 mnkr i absolut medelfel för samlade intäkter
  2022–2025 mot 180,3 i det tidigare delpostläget. Absolut
  resultatmedelfel var 58,0 mot 57,8. Hittills stöd för
  scenariomekaniken, ingen visad prognosvinst.
- `python3 scripts/evaluate_migration_profiles.py` testar samma
  regel i native Modelica för Motala och Mjölby. Två flyttprofiler
  med +100 per år ger samma total i första prognosåret. Följande år
  får 19–64-profilen högre skatt, lägre bidrag och lägre omsorgsbehov
  än 65+-profilen i båda kommunerna. Referensbeloppen hålls konstanta
  för detta mekaniktest; det är ingen jämförelse med bokslut.
- Förskolan Bråta Hagar har 144 platser enligt kommunens verksamhetssida.
  AR 2025 s. 64–65 anger projektbudget 65, ackumulerat 61 mnkr och
  planerad färdigställning i februari 2026. Modellen behandlar 61 mnkr
  som del av basårets pågående arbeten på 99 mnkr och antar att
  budgetresten 4 mnkr betalas 2026 utöver det vanliga investeringsreglaget.
  Båda öppningsalternativen har samma betalning. Försening för över
  driftsättning, avskrivning och tillgängliga projektplatser till 2027.
  Verksamhetsdelen visar platser som saknas mot projektplanen.
  Ingen separat uppgift om nettotillskott av platser eller kostnad
  för ersättningslokaler har använts. Fullt ekonomiskt bokslut 2026
  kan inte kontrolleras ännu.
  Källor: https://www.motala.se/media/uploads/Arsredovisning-2025.pdf
  och https://www.motala.se/skola-och-forskola/forskola-och-barnomsorg/forskolor/forskolan-brata-hagar/ .

## Rörelsekapital i årsmodellen (2026-11-18)

- Valbart läge för kundfordringar, leverantörsskulder och förutbetalda
  bidrag. Fordringar beräknas som valt antal dagar av
  verksamhetsintäkterna, skulder som dagar av övriga driftkostnader.
  Det är förenklade omsättningsrelationer baserade på årsslutssaldon.
  Ingående bidragsförskott antas höra till första prognosåret.
  Ett nytt scenarioförskott betalas första året och avser intäkter som
  redan ingår året därpå. Endast förändrade saldon går till
  kassaflödet. Finansieringen kan sedan ändra nästa års ränta.
- SCB TAB6779 rader 045/086 i `data/downloads/20261109T162149Z`:
  kundfordringar/leverantörsskulder 29,909/216,898 mnkr 2021 och
  16,111/181,275 mnkr 2025. AR 2021 not 18 s. 43 visar kundfordringar
  29,9 och AR 2022 not 24 visar jämförelsebeloppet 216,9.
  AR 2025 not 16 s. 53 respektive not 22 s. 54–55 visar 16/180.
  Modellen använder SCB:s handelsbelopp. AR 2025 not 22 anger
  29 mnkr i förskott för riktade bidrag och kostnadsersättningar.
  2021 saknar separat förskottsbelopp, vilket antas noll i simuleringen.
- Verifierat totalt kassaflöde före/efter rörelsekapital i de kommunala
  årsredovisningarna: 2022 306,9/79,8, 2023 211/334, 2024 183/255
  och 2025 286/162 mnkr (AR 2022 s. 39, AR 2023–25 s. 49).
  I 2022–2025-omkörningen från bokslut 2021 med SKR 21:35 och
  basårets betalningstider minskade medelabsolutfelet i driftkassan
  från 91,9 till 89,4 mnkr. Modellerat rörelsekapital förändrades
  4–5 mnkr per år, medan bokslutets bredare mått varierade mellan
  −227,1 och +123 mnkr. Bland annat saknas lager och exploateringsfastigheter.
- Separat ettårstest från bokslut 2024 med daterat nationellt
  decemberunderlag från SKR 24:56, samma prognosantaganden i båda varianter.
  SCB-saldon 16,768/195,325 mnkr och 139 mnkr förutbetalda bidrag i
  AR 2024 not 24 användes som ingångsvärden. Utan antagande om nytt förskott
  för 2025 blev modellerad rörelsekapitaleffekt −134,8 mnkr. Driftkassan
  blev 144,9 mnkr mot 279,7 utan arbetande rörelsekapital och 162 i bokslutet.
  Ett enda startår; de faktiska 29 mnkr i utgående bidragsförskott 2025
  matades inte in.

## Förstudie efter byggtidsmodellen (2026-11-18)

- Årsmodellen har ett valbart scenario för kassa och förfinansiering.
  En andel av första årets investering kan betalas andra året och en
  andel av det uppskjutna beloppet lånas första året. Byggtid räknas
  från den faktiska utbetalningen. I kassapolicyn används befintlig
  kassa över vald reserv före vanlig nyupplåning. Förfinansiering är
  ett separat lånebeslut vid årets slut och ökar nästa års
  ingående skuld och ränta. Reserven är illustrativ.
- 2022–2025 från bokslut 2021 och SKR 21:35, samma investeringar:
  kassapolicy med noll reserv och utan uppskjuten betalning/förfinansiering
  ger MAE 127,7 mnkr för kassa och 99,5 för skuld, mot 210,5 och 253,3
  i ordinarie läge. Jämförelse mot AR 2022–2025 balansräkningar, en
  körning. Noll är ett testvärde och är inte kommunens likviditetsmål.
  Rörelsekapital ingick inte i den jämförelsen.
- I 2026-scenariot med 413 mnkr per år och halva första betalningen
  uppskjuten flyttas 206,5 mnkr till 2027. Med hela beloppet förfinansierat
  har kassa och skuld +206,5 mnkr 2026 och räntan är +4,6 mnkr 2027
  jämfört med samma betalningsplan utan förfinansieringen.

- Kassaflöde före/efter rörelsekapital 183/255 mnkr 2024 och 286/162
  mnkr 2025 enligt AR 2025 s. 49, kommunen. AR 2024 s. 49 bekräftar
  183/255 för 2024. Påverkan +72 respektive −124 mnkr. AR 2025 not 22
  anger förutbetalda generella/riktade bidrag 30+109 → 0+29 mnkr.
  Det är en tänkbar separat stock i en modell av rörelsekapitalet.
  Kassabryggan 2024 är 115+255−418+277=229 och 2025
  229+162−412+101=80 mot redovisat 81 mnkr, med avrundning.
- Motalas finanspolicy s. 4–5 kräver likviditetsreserv men hänvisar
  limiter till separat bilaga. Reserven kan omfatta mer än kassan.
  AR 2025 s. 40–41 anger ränteförfall inom ett år vid årsslutet på
  40 procent. Not 21, s. 54, redovisar kapitalförfall separat.
  Källor: https://www.motala.se/media/uploads/Finanspolicy.pdf och
  https://www.motala.se/media/uploads/Arsredovisning-2025.pdf .
- Motalas bildningsnämnd beskriver delningstal och svårighet att
  anpassa bemanning vid mindre elevantal i AR 2023 s. 57, samt
  lokalomställningen i AR 2025 s. 59. En första pilot kan följa
  åk 1–9 som hemkommunselever (Kolada N15829, 15 oktober) och frysa
  elevkvoten mot SCB:s 7–15-åringar vid basåret. Snabbdiagnostik
  för fem ettårsfall 2021–2025: 35,5 elever i absolut medelfel med
  kvot av modellens ettårsåldrar och observerat flyttnetto,
  jämfört med 33,8 vid oförändrat elevantal och 82,5 med modellens
  antal 7–15 år direkt. Kontrollen använder arkiverad Kolada efteråt
  och 31 december som ungefärlig nämnare. Lokaler och lärartäthet
  kräver data för kommunal huvudman och samma årskurser, samt
  daterade lokalbeslut. Källor finns i `data/downloads/20261106T090534Z`
  och Motalas årsredovisningar 2023–2025.

## Byggtid, driftsättning och finansiering

- Årsmodellens kapitaldel har valbar byggtid 0–5 år och andel av
  investeringsutbetalningarna med byggtid. Utbetalningar förs till
  pågående arbeten tills de tas i bruk. Modellen börjar skriva av
  halva värdet första året i bruk enligt den tidigare årsregeln.
  Ingående pågående arbeten fördelas lika över byggtidens år.
  Samma betalningar ger samma kassa, skuld och ränta i nuvarande
  finansmodell, där avskrivningen återläggs i kassaflödet.
- Verifierat mot Motalas bokslutsnoter för kommunen. 2021 har ett tomt
  fält i AR 2021:s not 12 och ett streck i samma jämförelsekolumn i
  AR 2022:s not 12, s. 42. Därför används 0 som ingående separat saldo
  i den historiska körningen. 2022: 114,7 mnkr i AR 2022 och avrundat 115
  som ingång till 2023 i AR 2024. 2023/2024: 238/86 mnkr i AR 2024,
  not 13, s. 52–53. 2024/2025: 86/99 mnkr i AR 2025, not 12, s. 53.
  För skulder och avskrivningar bekräftar SCB TAB6779 respektive
  TAB6777 samma nivåer inom 0,5 mnkr. 2022 års avskrivningar i
  resultaträkningen omfattar en nedskrivning på 12,1 mnkr (not 5).
- Retrotest 2022–2025, samma SKR 21:35, betalningar och övriga antaganden
  i samtliga varianter. Medelabsolutfel i mnkr för pågående arbeten,
  avskrivningar och skuld: samma år 134,4/9,8/253,3, ett år för halva
  investeringen 52,7/14,4/253,3, två år för halva 104,1/19,2/253,3.
  Hälften är ett illustrativt scenarioantagande. Resultaten används
  inte för att välja byggtiden.

## SKR som huvudreferens

### Skatteunderlag efter ålder, undersökt 2026-11-18

- SCB TAB744, `BeskForvInk`, kan ge åldersvikter för en
  känslighetsberäkning av lokalt skatteunderlag. Källa:
  https://www.statistikdatabasen.scb.se/goto/sv/ssd/TAB744 .
  Hämtad fråga och originalsvaret (Motala, Mjölby och riket, 2019
  och 2024) i `data/downloads/20261118T164436Z` med SHA-256 i manifestet.
- Motala 2024, båda könen, totalsummor i mnkr: 0–19 år 40,9,
  20–64 år 8 222,3, 65+ 2 063,0. Totalsumma enligt totalraden
  10 326,1 mnkr. SCB SkatteKraft för utjämningsåret 2026
  (inkomståret 2024) ger 10 325,5372 mnkr. Skillnaden är 0,56 mnkr.
  Åldersandelar är ett möjligt sätt att fördela det officiella
  underlaget och pröva flyttscenarier. De ska inte läsas som löner.
- En hypotes att testa är att låta inkomstutjämningen svara på samma
  lokala skatteunderlag enligt SFS 2004:773, 3–7 §§. Dagens importerade
  delpostläge har samma befolkningskvot för skatten före avräkning
  och inkomstutjämningen. Daterad åldersprofil måste ha publicerats
  före respektive teststart. Inga nya indata är aktiverade i modellen.

### Prövade modellvarianter 2026-11-18

- Förinställningarna i Scenariolabbet kördes i wasm-Modelica från
  bokslutet 2021 till 2026 med SKR 21:35, utan ändrade reglage.
  Absolut medelfel 2022–2025 för resultat/folkmängd vid årsskiftet:
  Grundbana 58,0 mnkr/190 personer, Svagare ekonomi 179,6/177,
  Ökad inflyttning 53,9/874 och Lägre investeringstakt 56,9/190.
  Grundbana med SKR:s publicerade bana direkt 51,8/190. Den ger
  41,7 mnkr i resultat 2026 jämfört med antagen budget 86 mnkr
  (Mål- och resursplan s. 25) och grundbanans −33,3 mnkr.
  2026 års resultat ingår inte i felmåtten.
- Kontrollerat Motalas kommunfullmäktiges protokoll 26 oktober 2026,
  s. 25, § 156 (ärende KS-2026/00008, delårsrapport januari–augusti).
  Helårsprognos +52,6 mnkr, budgetavvikelse −33,4 mnkr, väntad
  investeringsvolym 453 mnkr. Detta är en prognos och ligger inte i
  modellens indata eller felmått. PDF SHA-256
  `c3149fa96152760cea36a99838f76b9ed6739f3946695c53d8f72ed63103850d`.
  Källa: https://diariet.motala.se/download/document?filename=UHJvdG9rb2xsLnNpZ25lcmFkLnB1Yi5wZGY=&id=120190

- Scenariolabbet har valfria modeller för SKR-intäkter, löner/sociala
  avgifter och demografi. Standardläget är kvar. I delpostläget justeras
  skatt före avräkning, inkomstutjämning och regleringspost mot SCB:s
  novemberutfall vid basåret och uppskattade novembernivåer därefter.
  Slutavräkningar, fastighetsavgift, kostnads-/LSS-utjämning och övriga
  bidrag följer referensen. Det är en förenklad känslighetsberäkning.
  SKR-läget utan justering använder de publicerade referensvärdena.
- SCB TAB1212 (Flyttningar97, inflyttningar BE0101AU och utflyttningar
  BE0101AV, ettårsåldrar och kön), hämtad 2026-11-18 till
  `data/downloads/20261118T142244Z`, råfilens SHA-256
  `b6cbfda316d91d0224124f5e536f85abe59a76a24a5de80aeaef63727c223407`.
  `scripts/prepare_model_experiments.py` använder högst tre kända år,
  senast 2024 i den serien. En scenarioändring av flyttnettot fördelas
  som de tidigare inflyttarnas åldrar. Ettårsmodellerna använder
  fruktsamhetsmedel för fem år fram till respektive basår.
- SCB TAB4202, rader 100/110, anger fördelningen mellan löner och sociala
  avgifter. Relationen läggs på basårets samlade personalkostnad. Avgifter
  sätts som en andel av lön och pension fortsätter med egen kostnads- och
  utbetalningsbana. Testet använder 3 procent nominell årlig löneökning,
  oförändrad lokal avgiftsandel och ingen daterad lokal pensionsprognos.
- `node scripts/evaluate_model_variants.mjs /tmp/model-variants.json`
  kör appens wasm-Modelica. 2022–2025 från decemberbokslutet 2021:
  genomsnittligt absolut intäktsfel 181,47 mnkr i ordinarie modell,
  180,28 med delpostjustering och 147,97 med SKR 21:35 direkt. Det finns
  bara en omräknad historisk lokal SKR-version i detta test. Bokslutet
  för basåret publicerades efter versionens septemberdatum.
- Fem ettårstest från bokslut 2020–2024 med respektive års daterade
  nationella SKR-underlag ger nettodriftens absoluta medelfel 37,75 mnkr
  i ordinarie läge och 70,41 med den förenklade delade lönebanan.
  I 2022-körningen sjunker samma fel från 131,54 till 111,56 mnkr.
  För antal 80+ ett år fram går absoluta medelfelet från 91,9 till 25,3
  personer med ettårsåldrar och kalibrerade restflöden. Totalt
  befolkningsfel går från 127,3 till 140,6 personer i samma jämförelse.
  Kraftigare detaljering i ålder förbättrar alltså främst
  åldersfördelningen i dessa fall. Resultaten gäller endast Motala.
- Alla ändringar tillsammans i 2022-körningen minskar nettodriftens
  absoluta medelfel från 131,54 till 91,00 mnkr och ökar resultatfelet
  från 57,96 till 103,09 mnkr. Kommunens antagna budget har ett
  resultatfel på 24,28 mnkr över fem ettårsfall (2021–2025).
- Scenariot +100 i flyttnetto varje år från 2026, med ettårsåldrar,
  observerade flyttflöden och delpostjustering av den ojusterade
  SKR 26:28-banan, ger två körningars skillnad på +100 invånare 2026,
  0 mnkr i skatt och bidrag och +0,72 mnkr i nettodrift. År 2027
  ger det +201,7 invånare, +4,86 mnkr i skatt och +1,51 mnkr i bidrag.

- Jämförelsefliken har separata tabeller för skatt, bidrag, resultat och
  befolkning vid jämförelse med SKR. Modellbanor jämförs vid årsskiftet.
  Mot SKR visas kalenderåret för 1 november (året före intäktsåret),
  med modellens linjära uppskattning endast när båda intilliggande
  årsskiften finns i körningen. `prepare_replay_2022.py` lägger till
  SCB:s redan arkiverade novemberutfall 2021–2025 efter kontroll av
  arkivens SHA-256. Utfallen används enbart i tabellen.

- Kontrollerade SKR:s aktuella sida Skatteunderlagsprognoser den
  2026-11-18. Där anges kommununderlag 26:28, 2026–2033. Webbens
  Jämförelser kan nu välja de två befintliga Motala-utdragen, 21:35
  (2022–2028 efter bokslutsåret) och 26:28 (2026–2033). Tabellen använder
  originalutdragen utan webbens förlängning eller justering av
  regleringsbidraget. Skillnad avser modell minus SKR. I 2022-läget
  visas även redan verifierade bokslut och budgetar för tillgängliga år.
  Källa: https://skr.se/ekonomiochbudgetplanering/skatteunderlagsprognoserochmodellverktyg.8271.html
- Kontrollerade delposterna för intäktsåret 2026 i de två omräknade
  Motala-arbetsböckerna, Blad 1 Totala intäkter (21:35 kolumn G, 26:28
  kolumn B). Inkomstutjämning 630,0/635,8, kostnadsutjämning 14,4/50,7,
  regleringspost 52,4/120,8 mnkr. Dessa är värden från två prognosversioner.
  Blad 2 Indata rad 100–101 innehåller PKV för arbetskraft och övrig
  förbrukning. De årsvisa indexen är modellindata i SKR-läget.

- Användaren vill främst jämföra Motala-modellen med SKR. SCB:s registrerade
  folkmängd är utfall och SCB:s egna framskrivningar en kompletterande referens.
  Jämför SKR:s novemberbana med samma datum i SCB när befolkningen utvärderas.
- Jämförelse den 1 november 2022–2025 för intäktsåren 2023–2026.
  Modellens novembernivå approximeras med 10/12 av förändringen mellan
  två årsskiften. Modellen 43666/43651/43632/43608, SKR 21:35
  44047/44244/44437/44633, SCB 43733/43776/43572/43158.
  Modellen närmare samtliga fyra datum. November 2021 ligger före
  modellens start från bokslutet 2021. SCB:s publicerade total för
  2025 hämtad från TAB6725 till data/downloads/20261118T111419Z.
  Ingen modelländring, interpolationen används bara i jämförelsen.
- Utjämningslagen (2004:773), 17–18 §§, använder folkbokföringen 1 november
  föregående år, och Skatteverket beslutar om beloppen. SKR:s prognos beräknar
  vad regler och antaganden väntas ge. En särskild koppling till bokslutet
  finns enligt RKR R2: årets SKR-prognos i december används i periodiseringen
  av skatteavräkningen. Håll isär den posten, slutligt beskattningsutfall
  och beslutade bidrag. Källor: riksdagens SFS 2004:773 och RKR R2 Intäkter
  (avsnitt Periodisering av skatteintäkter).

## Webbens prognosår 2022 och 2026 (2026-11-18)

- Webbappen har val för första prognosår 2022 och 2026, med respektive
  bokslut 2021 och 2025. Normala slutår är 2026 och 2033. Årsväljaren
  medger 1–30 årssteg. Efter sista källåret (2028 respektive 2033) används
  sista årets prisantaganden, kalibrerade flyttflöden och sista årsförändringen
  i den importerade intäktsreferensen. Webben och PDF märker förlängningen
  som beräknad. En egen intäktsimport behöver täcka det valda intervallet.
- Samma Motala.Annual körs i wasm-jit för båda perioder. Webbläsarens omslag
  kompileras per basår. Scenario.mo exporterar motsvarande basår och tider.
  Firefox verifierade växling åt båda hållen och slutår 2023, 2026, 2051 och
  2055. Native OpenModelica körde den historiska exporten med samma skatter,
  bidrag och resultat som webbmodellen.
- 2022-läget använder SCB:s bokslut och befolkning till och med 2021 från
  data/downloads/20261109T162149Z, inklusive TAB6777/6779/6782/4202/5179
  och SCB:s befolkning per ettårsålder (summerad till modellens fem grupper).
  TAB6777 hämtades på nytt 2026-11-18 med samma fråga och var byteidentisk
  (SHA-256 9d235b767ae5c0b71149f6b5cf7f6b03504f04890bfed1cb402740b80a8d6ba7).
  Senare lokala utfall används bara i jämförelsetabellen. Bokslutet 2021
  publicerades 2022, så kombinationen med septemberprognosen är en historisk
  omkörning från stängt 2021 och inte ett test av informationsläget i september.
- SKR 21:35 (2021-09-30) omräknades för kommun 583. Läste den äldre filen
  med msoffcrypto, konverterade till XLSX i LibreOffice med makron spärrade,
  satte B1 i arbetskopian, tömde formelcacherna och räknade om. B1/C1
  verifierades i Prognosunderlag. Skatt och bidrag lästes ur Blad 1 rad 38/40
  och stämdes av mot rad 36. Befolkning och priser från Blad 2 (rad 26/29
  och 100/101). Arbetsböckerna ligger lokalt och är ignorerade.
  scripts/prepare_replay_2022.py skapar data/replay-2022.json med källor.
- Jämförelsen visar SKR:s ursprungliga intäktsreferens, modellvärden, Motalas
  bokslut (AR 2022 s. 37, AR 2023–25 s. 47), SCB TAB6777 och respektive års
  budget. Budget 2026, s. 25, ger 86 mnkr i resultat. Utfall 2026 saknas
  före bokslut. SCB:s resultat avviker från AR bland annat 2022 (126,563 mot
  125,1) och 2023 (22,033 mot 23 i ursprunglig AR, 24 i AR 2024). Ingen
  förklaring fastställd till de skillnaderna.
- Direkt jämförelse av standardkörningen från bokslut 2021 med SKR 21:35
  mot årsredovisningarna 2022–2025. Medelabsolutfel i mnkr, modell/SKR:
  skatt 65,45/40,75, bidrag 116,01/107,22 och summa 181,47/147,97.
  Samtliga prognosvärden för båda delarna ligger under utfall i alla fyra år.
  Modellens sammanlagda intäkter är 11,0, 25,5, 40,7, 56,7 och 74,1 mnkr
  lägre än den ojusterade SKR-banan 2022–2026. Vid oförändrad skattesats
  kommer skillnaden från skalningen med föregående års modellbefolkning
  delad med SKR:s novemberreferens (Kommunekonomi.mo, Revenue).
  Jämförelsen gäller en SKR-version. För 2026 saknas årsutfallet.
- Omkörning med samma basår 2021 och SKR 21:35 till 2028 i native OpenModelica.
  Överlappande år 2022–2026 gav samma belopp som den kortare körningen.
  Modellens skatter och bidrag 2026–2028 är 3140,3/3220,1/3301,2 mnkr,
  SKR:s är 3214,3/3312,8/3413,8. Modellresultat −33,3/−61,8/−91,5 mnkr.
  Motalas budget och plan 86/88/92 mnkr i resultat och 3424/3531/3641 mnkr
  i skatt och bidrag verifierades i resultatbudgeten på s. 25. Budgetens
  intäktsbana bygger på SKR oktober 2025. Årsutfall 2026–2028 saknas.
- Granskat fler jämförelsevariabler i SKR 21:35 den 2026-11-18. Raden
  ”Antal invånare i kommunen enligt riksprognos” (Prognosunderlag rad 42,
  Blad 2 Indata rad 29) avser 1 november året före intäktsåret. Hämtat
  SCB FolkmangdNov för Motala, 2020–2024, till data/downloads/20261118T110040Z
  med manifest och kontrollsumma. För intäktsåren 2022–2025 är SKR:s referens
  43842/44047/44244/44437 mot SCB:s faktiska novemberbefolkning
  43647/43733/43776/43572. Modellens skattejustering använder däremot
  föregående års befolkning 31 december. Håll referensdagarna isär.
- SKR-blad 1 2022 (kolumn C) jämfört med AR 2022 s. 42, not 6–7, och
  SCB TAB6782: preliminär skatt 2072,769 mot 2072,6/2072,538 mnkr;
  slutavräkningar sammanlagt 8,286 mot 65,0/65,050. Inkomstutjämning
  544,561 mot 531,1/531,140, regleringsbidrag 110,314 mot 120,5/120,475,
  kostnadsutjämning 14,161 mot 13,3/14,753. Skillnaden mellan SCB:s och
  AR:s kostnadsutjämning är inte utredd. Webbens importerade referens skalar
  totalsummorna och gör ingen egen prognos per bidragspost i det läget.
- Hämtat SCB:s regionala befolkningsframskrivningar för Motala för
  2022–2028 från juni 2021 (TAB5999, BefProgOsiktNetN21, basår 2020)
  och maj 2022 (BefProgOsiktNetN22, basår 2021). Arkiv
  data/downloads/20261118T110525Z med frågor och SHA-256.
  Jämfört omkörningen från basår 2021 med framskrivningarna och SCB:s
  utfall summerat över ettårsåldrar. All folkmängd avser 31 december.
  För 2022–2025 är SCB-utfallen 43728/43728/43505/43113,
  modellutfallen 43664/43649/43629/43604, SCB juni 2021
  43734/43767/43779/43808 och SCB maj 2022 43743/43799/43846/43883.
  Medelabsolutfel 189,6/253,5/299,2 personer (modell/juni/maj).
  SCB ligger närmare ett år framåt, modellen närmare 2024–2025.
  AR 2025 anger 43131, uppgiften från SCB är 18 lägre.
  För 2028 ger modellen 43506, SCB juni 2021 43930, maj 2022 43976.

## Startår, slutår och användarens besked om historiken (2026-11-18)

- Användaren har uttryckligen sagt att rensning av git-historiken inte behövs.
  Lämna historiken som den är; återuppta inte den åtgärden på eget initiativ.
- Granskat Motala.mo och webbens årsinställningar: färdiga ekonomiska basår
  är 2020, 2021, 2022, 2023, 2024 och 2025. Ettårsåldersdemografin har samma
  basår. Basåret avser bokslut vid årets slut; första beräknade året är året efter.
  Äldre bokslut i research/ är inte färdiga basår i webbens Modelica-modell.
- Före tillägget ovan saknade webbappen reglage för startår och slutår.
  baseline.json har basår 2025 och years=8, omc-session.js har BASE_YEAR=2025;
  standardkörningen slutar 2033. Motorn/wrappern stöder 1–30 prognosår, men
  aktiva planning-inputs.json och skr-revenue-path.json täcker bara 2026–2033.
  Kortare horisont kan kopplas till befintlig parameter. En längre horisont
  kräver ytterligare årsunderlag eller uttryckliga antaganden om förlängning;
  prepareScenario avvisar luckor i de aktiva banorna. Startårsval behöver även
  byta basårsdata, kalibrering, antagandeversion och simuleringens starttid.
  Ingen ändring av webbappen eller modellen gjord vid denna kontroll.

## SKR: publicering av siffror och Excel (2026-11-18)

- Användaren vill kunna dela siffror på git men hålla fullständiga Excelunderlag
  utanför. Inriktningen är begränsade Motala-utdrag/egna analyser med källa,
  cirkulärdatum, kommun, enhet och cellhänvisning. Original och omräknade
  arbetsböcker förblir lokala. Detta är inte ett konstaterande om en fri licens.
- Granskat SKR:s prognossida, öppna-data-sida och sökbar celltext i
  xlsm-originalen 2022–2024 samt 2026. Ingen uttrycklig återpubliceringslicens
  för just prognosarbetsböckerna hittad. Generell öppna-data-information visar
  inte säkert vilka villkor som gäller för dem. Källor och avgränsning finns i
  data/skr-historical/README.md, avsnitt Publicering och rättigheter.
- PRV (https://www.prv.se/sv/upphovsratt/for-myndigheter/) skiljer fakta från
  skyddad utformning. Upphovsrättslagen 49 § kan skydda sammanställningar;
  en filformatsändring eller källhänvisning ger inte automatiskt rätt till stora
  uttag. Något licensbesked från SKR har inte inhämtats och inget meddelande skickats.
- `git ls-files '*.xls' '*.xlsx' '*.xlsm'` är tomt; de nya originalen och
  arbetskopiorna ignoreras, webbbygget har en explicit lista över datafiler,
  och inga Excel-filer hittades i site/dist. `git rev-list --all --objects`
  visar däremot fyra äldre Excel-objekt, bland annat från 95f2df9. De togs bort
  ur filträdet i 1881eda men ligger kvar i historiken. Ingen historikomskrivning
  eller publicering utförd här. Remote finns nu: SVAGEN26/Motala_Ekonomilab;
  äldre minnesuppgifter om att remote saknas är därmed inaktuella.

## Motala bekräftat i alla fyra historiska underlag (2026-11-18)

- Kommunförekomsten är nu kontrollerad även i 2021 års XLS-fil. Samtliga fyra
  har `Data!A56 = 583`, `Data!B56 = Motala` och numeriska lokala grunduppgifter;
  även kommunkoder!G27/H27 har Motala/583. Internt cirkulär och årsrubrik stämmer.
- XLS-filen från 2021 är krypterad med Excels standardlösenord VelvetSweatshop.
  Läste den i minnet med msoffcrypto-tool 6.1.0 och xlrd 2.0.2, tillfälligt
  installerade i /tmp. Inga makron eller formler kördes. Originalhash oförändrad.
  Detta ersätter föregående granskningsstatus att 2021 inte var cellgranskad.
- Kommunval B1 är tomt i alla fyra. Lokala prognosbelopp är fortfarande inte
  omräknade/importerade eller jämförda mot utfall. Inga modelländringar gjorda.
  README och manifest i data/skr-historical är uppdaterade med cellkontrollen.

## Historiska SKR-original återfunna (2026-11-17)

- På användarens fråga om de saknade historiska Motalaunderlagen söktes SKR,
  kommunhandlingar, Motalas diarium och Internet Archive. Fyra ursprungliga
  generella SKR-arbetsböcker är nu lokalt sparade: 21:35 (2021-09-30),
  22:28 (2022-08-25), 23:56 (2023-12-14), 24:56 (2024-12-12).
  Se `data/skr-historical/README.md` och `manifest.json` för adresser,
  arkivdatum, hämtningsdatum, SHA-256 och arkivets SHA-1. Alla fyra SHA-1
  stämmer med webbarkivets index. Originalen finns i dess ignorerade
  `originals/`; `scripts/fetch_historical_skr.py` återhämtar och verifierar dem.
- Detta ändrar tidigare status: december 2023 och 2024 saknas inte längre som
  källfiler. Båda, samt augusti 2022, har rätt internt cirkulärnummer, årsrubrik
  och Motala i Data!B56. Kommunval B1 är tomt, så lokala intäkter måste först
  räknas om i makrofria kopior. 2021-filen är äldre .xls: format och kontrollsumma
  verifierade, cellinnehåll ännu inte granskat. Inga makron eller omräkningar körda.
- Dessa är original för skatt och generella bidrag/utjämning, inte kompletta
  prognoser för kommunens kostnader och årsresultat. Ingen modellimport eller ny
  validering gjord. 21:35 och 22:28 får inte ersätta decemberversioner i befintligt
  test. Decemberfilerna 20:57, 21:49 och 22:54 återstår att hitta.
- Originaladresserna för de två decemberfilerna ger 404 hos skr.se och
  extra.skr.se. Arkivkopiorna kunde hämtas. Arkivdatum ligger efter cirkulärdatum;
  oförändrad tillgänglighet exakt på publiceringsdagen är inte självständigt styrkt.
  Länken till 20:57 återfanns i sidan arkiverad 2021-01-19, men filen gav 404 och
  dess exakta arkivindex ingen träff. Detta bevisar inte att kopior saknas överallt.
- Diariet är åtkomligt med nätåtkomst. Offentlig `download/config.js` anger
  att sökfunktionen är inaktiv. Ingen begäran har skickats till SKR eller kommunen.

## Granskning av löneantaganden (2026-11-17)

- Kontrollerat webbens aktivering i `site/src/app.js`, överföringen i
  `scenario-inputs.js` och driftens ekvationer i `Kommunekonomi.mo`. Standardläget
  använder `planning-inputs.json`: arbetskraft 2026–2033 = 3,1240; 2,6962;
  4,0885; 3,9309; 3,2767; 3,2767; 3,2767; 3,2767 procent. Verifierat mot
  originalarbetsbokens `Blad 2 Indata!C100:J100`, årsrubriker C99:J99.
  Reglaget lägger en avvikelse i procentenheter på varje år. Utan underlagen
  används 3 procent per år. Lönekostnad = basbelopp × sammansatt löneindex
  × verksamhetsvolym / produktivitetsindex; produktivitetsökningen är normalt noll.
- Basbeloppet 2 288 mnkr är **personalkostnader exklusive pensionskostnader**,
  verifierat i AR 2025 not 4, tryckt s. 52 (PDF-s. 27, kommunen). Det är inte
  en separat serie över rena löneutbetalningar. Pension 190 mnkr redovisas på
  egen rad i samma not. Webbens pensionsbana är fortfarande illustrativ:
  +2 procent per år och pensionsutbetalningar lika med kostnaden.
- SKR:s officiella beskrivning av PKV, granskad 2026-11-17:
  https://skr.se/ekonomiochbudgetplanering/prisindex.8274.html
  anger att arbetskraftsindex påverkas av PO-pålägg och pensioner. Modellens
  användning av detta index på personalkostnader exklusive pensioner är därför
  en approximation. Förslag: separata banor för löner, avgifter och lokala
  pensioner; undvik att föra pensionsdriven indexförändring till lönerna.
  Ingen storlek på denna möjliga snedvridning har fastställts.
- Webbens femgruppsdemografi håller andelarna 65–79/80–89/90+ fasta;
  `AnnualCohort` finns separat. Mer detaljerad bemanning per verksamhet och
  aktivering av ettårsåldrar i webben är förbättringar att pröva historiskt.
  Inga modellantaganden eller ekvationer ändrade vid granskningen.

### Uppföljning: omfattning, validering och flyttnetto (2026-11-17)

- SCB-arkivet `data/downloads/20261109T162149Z/TAB4202.json` har redan separata
  poster: 100 Löner m.m., 110 Sociala avgifter enligt lag och avtal exklusive
  särskild löneskatt på pensionsavsättning. För 2025: 1 712,644 + 575,434 =
  2 288,078 mnkr. `prepare_municipality.py` slår i dag ihop dem till payroll.
  Pensionsposterna 115/120/180/185/186 och deras skatteavgränsning måste
  stämmas av före en uppdelning; delrader märkta därav får inte adderas igen.
  Separata löne-/avgiftsbanor är en avgränsad ändring i drift, basår, indata,
  webböverföring och rapporter/tester. Full personal- och pensionsmodell är större.
- Granskat `scripts/hindcast_vintages.py` och nuvarande `data/vintage-hindcast.json`.
  Senaste resultatets MAE ett år fram, fem fall 2021–2025: skr 40,38 mnkr,
  hold 38,14, standard 59,35, budget 24,28, föregående utfall 58,92. Dessa
  värden ersätter äldre resultatsiffror i minnesanteckningar när dagens test avses.
  Ingen ny simulering gjord. Detta är inte en jämförelse med SKR:s kompletta
  historiska Motalaprognos (saknas). Testet använder decembercirkulär 2020–2024
  och bokslut publicerade följande vår; ingen exakt återgivning av decemberläget.
  `skr` räknar även upp pensioner med arbetskraftsindex; webbens standard gör
  det inte. Detaljerade bidragsvarianter körs i testet, webbens intäkter kommer
  från den importerade SKR-banan från oktober 2026 med scenariojusteringar.
- Utfall återkontrollerade i lokala originaltabeller: AR 2022 s. 37
  (2021 61,7; 2022 125,1), AR 2023 s. 47 (2023 23), AR 2024 s. 47
  (2024 1; reviderat 2023 24), AR 2025 s. 47 (2025 105; 2024 1).
  SCB TAB6777 post 120 i samma SCB-arkiv: 2021 61,681; 2022 126,563;
  2023 22,033; 2024 1,105; 2025 104,583. Testet behåller årsredovisningarnas
  ursprungliga flödesversioner; skillnaderna 2022 och 2023 är inte förklarade
  eller utjämnade. Prognosprecision över SKR är inte visad.
- Flyttnetto i webben: `app.js` reglage Förändrat årligt flyttnetto,
  -400 till +600 personer/år, normalt 0. Det är en avvikelse mot grundbanans
  restflöde och tillkommer varje år, fördelad 15/12/3/65/5 procent på
  0–6/7–15/16–18/19–64/65+. Med aktiva underlag beräknas grundbanans
  restflöden för att följa befolkningsprognosen, utan underlagen ur de två
  senaste historiska övergångarna. Restflödena är inte observerat flyttnetto.

## Användarens önskemål

- Förbättra Motala-modellen med relevanta data och jämför sakligt med SKR.
- Hämta offentliga underlag själv när det går, i stället för att bara be användaren ladda ned dem.
- Spara källor, hämtningsdatum, metadata och status beständigt.
- En jämförelse med SKR finns i webbplatsen. Kommunens logotyp togs bort 2026-11-06 på användarens begäran: projektet är oberoende och loggan får inte licensieras med koden.

## Befintligt och nyhämtat

- Användarens SKR-fil finns i `data/Prognosunderlag-K-2026-2033-26028.xlsm`. Granskad: `Prognosunderlag!B1` är tom och cachade kommunintäkter är noll. Originalfilen är bevarad. En arbetskopia har nu kommunval 583 och är omräknad med LibreOffice 24.2.7.2; `data/skr-revenue-path.json` är aktiv i webbens grundbana. Kör aldrig makron; projektet har `scripts/import_skr.py` för cachade Excel-värden.
- Budget 2026 fanns i `data/Budget-Mal-och-resursplan-for-2026-med-plan-for-2027-2028.pdf`. Filen finns kvar lokalt men är borttagen ur git (dubblett av arkivkopian, med bilder).
- Nytt källarkiv: `data/downloads/20261106T090534Z/`. Läs dess README.md och manifest.json.
- Hämtat: budget 2026/plan 2027–2028, budget 2025/plan 2026–2027, årsredovisningar 2022–2025, två befolkningsuttag för Motala 2005–2035 och 20 Kolada-serier inom 2010–2025.
- Befolkningsdetaljerna är FEMÅRSÅLDRAR, inte ettårsåldrar. Ursprungligt påstående i samtalet om ettårsåldrar rättades efter metadatakontroll. Äldre kan grupperas 65–79, 80–89 och 90+.
- 651 respektive 124 befolkningsvärden; 384 Kolada-rader. Alla 20 nyckeltal har värden men inte nödvändigtvis för varje år. SHA-256, kommunurval, radantal och metadata kontrollerades.
- Återskapningsskript: `scripts/fetch_planning_data.py`. Källarkivering ändrar inte modellens indata. `scripts/prepare_planning_inputs.py` bearbetar det granskade urvalet till `data/planning-inputs.json`.

## Återstod (2026-11-06; se Öppet överst för dagens läge)

1. Lokal SKR-intäktsimport är nu genomförd, inget manuellt kommunval återstår. Se `data/skr-motala/selection-receipt.json` och `skr-map.json`.
2. Granska PDF:ernas innehåll och kontrollera definitioner/enheter i befolknings- och Kolada-data före modelländringar. Bevara skillnader mellan hemkommun, lägeskommun och egen regi.
3. Delårsrapport/tertialrapport 2026 har inte hämtats. Offentligt diarium: https://diariet.motala.se/. Sökning på delårsrapport, dokumenttyp 64, 2026-01-01–2026-11-06 gav noll träffar; frånvaro är inte fastställd.
4. Detaljerad lokalkapacitet, personalanpassning, lånevillkor och pensionsprognos kan kräva ytterligare underlag.
5. Historiska SKR- och kommunprognosversioner med ursprungliga publiceringsdatum behövs för en rättvis träffsäkerhetsjämförelse. Aktuella nedladdningar är inte historiska dataversioner.

## Modellens evidensläge

En bokslutsserie 1998–2025 finns redan. Bättre precision än SKR är inte visad. SKR:s prisprognoser (PKV) är inte dess skatte- och bidragsmodell. Separata forskningsmodeller M1/M2 ska inte blandas ihop med webblabbets JavaScript-motor. Se `research/M2.md` för historiska försök och deras begränsningar.

Det finns inget tillgängligt verktyg för att ändra kontoövergripande minne i denna session. Denna fil och hänvisningen i projektets AGENTS.md är det beständiga projektminnet.

## Aktivering efter användarens godkännande

Användaren bad uttryckligen att aktivera underlagen. Webbens grundbana laddar nu
`planning-inputs.json` och kan växlas till tidigare antaganden med en kryssruta.
Nationell SKR-skattetrend och årsvisa kostnadsindex samt den förankrade
befolkningsbanan påverkar beräkningarna. SKR:s omräknade Motala-intäkter är nu importerade som referens; modellens lokala scenariojusteringar är fortfarande förenklade. Femårsåldrar omfördelas
proportionellt vid modellgränser; befolkningsbanan följs via årsvisa restflöden,
inte observerad migration. Kolada visas som jämförelse och sex PDF:er som
nedladdningsbara original. Budgetbelopp och investeringsplaner är inte importerade.

Scenarioexporten innehåller aktiva källor och årsvisa inputs. Modelica-exporten
har samma årsbanor. Direktöppnad Motala.Annual behåller illustrativa standarder;
exportera Scenario.mo från webben för att återskapa den aktiva beräkningen.
35 tester passerade och native Modelica matchade JavaScript för fyra scenarier,
åtta år och 23 outputs per år. Startsidan med aktiva underlag har även kontrollerats i headless Firefox; skärmbild finns i `build/planning-preview.png`. Tabeller och dokumentlänkar kontrollerades statiskt. Interaktiv webbläsartestning av alla reglage och flikar är inte utförd.
Aktiveringen bevisar inte bättre prognosprecision.

## Senaste ändring: kommunval och mindre logga

Användaren bad att jag själv fyller i kommunvalet och minskar loggan. Detta är
gjort. Logo är nu 100 px på desktop och 80 px på mobil (tidigare 170/140 px).
LibreOffice hämtades via `apt-get download` och packades upp under
`.local/calc-runtime/`, utan systeminstallation. Lokala bibliotekssökvägar och
register anpassades. `scripts/recalculate_skr.py` bevarar originalet, väljer 583,
tar bort VBA före omräkning och verifierar alla åtta intäktsår. Utfilen är
`data/skr-motala/recalculated/Prognosunderlag-Motala-0583.xlsx` och finns även som
nedladdning i webben. 2026-referensen är skatt 2403.874358 mnkr och bidrag/
utjämning inklusive fastighetsavgift 982.773537739798 mnkr.

Webbens grundbana och native-export använder denna referens som standard.
Referensbeloppen visas separat eftersom modellens lokala befolknings-, skatte-
och utjämningsjusteringar ger avvikande scenariobelopp. Intäktsimporten inkluderar
slutavräkningar och fastighetsavgift; referensbefolkningen avser 1 november året
före intäktsåret. 35 tester och native-paritet för fyra scenarier passerade efter
inkopplingen. Ingen manuell Excel-åtgärd behövs nu.

Den slutliga startsidan med mindre logga och aktiv Motala-intäktsbana granskades i Firefox i desktop- och mobilstorlek. Mobilreglagens grid fick minmax(0,1fr) och panelerna width:100% för att förhindra horisontell överbredd.

Användaren tyckte fortfarande loggan var för stor. Senaste storlek är nu 64 px på dator och 56 px på mobil, med kompaktare sidhuvud. CSS-länken versionsmärks för att undvika gammal cachad logostorlek.

## PDF-export med grafspecifika parametrar

Användaren bad om PDF-export med grafer och relevanta aktuella parametrar per
graf samt en tydlig jämförelse med SKR. Knappen `Exportera PDF` finns vid
visningsflikarna. Den öppnar en fryst rapport i en ny flik och webbläsarens
utskriftsdialog; användaren väljer Spara som PDF. Ingen servertjänst eller extern
PDF-kod används. `site/src/pdf-report.js` skapar rapporten från en ny beräkning
av aktuella reglage, aktiva källor och importerad intäktsbana.

Rapporten har sex avsnitt/sidor i A4 liggande: resultat, skuld, befolkning,
verksamhetsbehov, känslighet och SKR/källor. De fyra SVG-graferna och känslighetens
staplar följer med. Årsvisa arbetskrafts-/prisvärden, pensioner, finansieringsflöden,
befolkningsparametrar och verksamhetsvikter redovisas vid respektive graf.
SKR-referensen jämförs separat med scenariobeloppen; inga precisionsvinster påstås.

38 tester passerade. Riktig Firefox-kontroll via befintlig geckodriver ändrade
låneräntan till 5 %, klickade på exportknappen, kontrollerade fem grafer och
skapade `build/motala-scenario-export.pdf` med Firefox WebDriver Print. pdfinfo
bekräftade sex A4-sidor. Utskriftsdialogen ersattes av en räknare i automationen;
WebDriver Print skapade en faktisk PDF. Modellsambanden har inte ändrats.

## Webbappens motor: OpenModelica wasm-jit (2026-11-06)

Användarens avsikt: statisk webbapp på GitHub Pages där Modelica-modellen är den
enda modellen och besökarens webbläsare kompilerar och simulerar den lokalt med
OpenModelicas webbkompilator (wasm-jit). Detta är nu genomfört.

- `site/src/omc-worker.js` hämtar kompilatorn från `omc-web/`, laddar `Motala.mo`
  och `MotalaBrowser.mo` och kör `buildModel(MotalaBrowser)` en gång (~1 s).
  Varje scenario körs sedan med `omc_sim_start` och `-override` (20–90 ms).
- Den förkompilerade FMU-vägen (`site/wasm`, `build_wasm.py`, `fmi_bridge.c`,
  `wasm-engine.js`) är borttagen. `engine.js` finns kvar enbart som testreferens.
- Kompilatorn byggs från användarens OpenModelica-checkout med `-DOM_OMC_WASM=ON`
  (se README). Ubuntu 24.04:s binaryen 108 klarar inte sista steget; använd
  emsdk:s `wasm-opt` (124). PR för versionskontroll i OpenModelica:
  https://github.com/OpenModelica/OpenModelica/pull/17869
- `scripts/stage_omc.py` kopierar kompilatorn till `site/omc-web/` (ej i git) med
  manifest och licens. `scripts/deploy_pages.py <remote>` publicerar `site/dist`
  som en enda commit på `gh-pages`. Ingen publicering har gjorts.
- Licens: OpenModelica är OSMC-PL/AGPL. Publicera bara en kompilator byggd från
  en commit som finns publikt. Nuvarande lokala bygge kommer från grenen
  `test/omedit-lsp-navigation` med lokala ändringar (`OMCompiler/3rdParty`).
- Projektet ligger nu i git (lokal repo, ingen remote). Nedladdade källfiler och
  CSV lagras byte för byte (`-text`) så att manifestens SHA-256 stämmer.

## Källmaterial och rättigheter (2026-11-06)

- Bilder i kommunens PDF:er är borttagna på användarens begäran, eftersom foton kan ha
  tredje parts rättigheter. `scripts/strip_pdf_images.py <arkiv>` ersätter varje bild med
  en tom och skriver "Bild borttagen" där den syntes. Text och vektorgrafik behålls.
  Bilder på högst 4×4 pixlar behålls, eftersom Budget 2026 ritar sin text som små bilder
  med mjuka masker. Manifestet har originalets hash som `originalSha256`.
  Kör skriptet efter varje ny nedladdning med `fetch_planning_data.py`.
- SKR:s arbetsböcker är borttagna ur git och sajten och ignoreras. Sajten och
  `data/skr-motala/README.md` länkar till SKR:s original. Lokala kopior finns kvar för
  skripten.
- Git-historiken (commit 95f2df9) innehåller fortfarande originalen. Repot har ingen
  remote; historiken bör rensas innan den första pushen.


## Katalogstruktur (2026-11-08)

- `modelica/` innehåller bara det sajten kör: `Motala.mo`, `MotalaBrowser.mo` och `validate.py`.
- `research/` (tidigare under `modelica/`) innehåller M1 (`MotalaResearch`), M2 (`MotalaDynamics`),
  frysta versioner, historiska omkörningar, deras data, granskningar och tester. Inget där används av sajten.
  Sökvägar i arkiverade JSON-protokoll och granskningar är historiska och anger fortfarande `modelica/`.
- Forskningstester: `PYTHONPATH=research python3 -m unittest discover -s research/tests -p 'test_*.py'`.
- Simuleringstiden är kalenderår (ändrat 2026-11-08): `Annual` startar 2025, `Hindcast2025` 2024, `DemographyOnly` 2020. Webbläsaren bygger med startTime=2025 (`BASE_YEAR` i site/src/omc-session.js).
- Beskrivningar, dokumentation och assert-meddelanden i Motala.mo är på svenska (användarens val). Namn i koden är ASCII: Modelica 3.x och Base Modelica tillåter bara ASCII i namn, även citerade (spec 2.1, Q-CHAR; ModelicaSpecification #1176). Rust-parsern i webbläsaren accepterar å/ä/ö, den inbyggda OpenModelica-lexern gör det inte.
- Webbplatsen har fliken Modellen (`site/src/model-view.js`): flödesdiagram, ekvationer, Modelica-kod
  och redigerbara antaganden kopplade till Scenariolabbets kontroller.

## Demografi per ettårsålder (2026-11-08)

- SCB-data hämtade till `data/downloads/20261108T124756Z/` (README där). Källa: SCB, CC BY 4.0; användaren har godkänt användning med källhänvisning.
- `Motala.Components.CohortDemography`: kohort-komponentmetoden. Väljbar fertilitetsmodell; användarens önskade standard är summerad fruktsamhet 1,41.
- Kalibrering per basår 2020–2025 utan framtidsdata. Testet mot historien: `scripts/hindcast_demography.py` → `data/demography-hindcast.json`.
- `Annual` och sajten använder fortfarande femgruppsdemografin; `Examples.AnnualCohort` använder den nya.
- Nästa steg enligt plan: åldersviktad omsorgsefterfrågan (Kolada: hemtjänsttagare 65–79 och 80+), antaganden per prognostillfälle (hösten 2024) för ett rättvist test av ekonomin, klockade ekvationer.
- OMEdit från `OpenModelica/build/` skriver över `Motala.mo` vid sparande; använd den installerade (PATH i ~/.bashrc).
- Åldersviktad omsorg genomförd 2026-11-08: Kolada-arkiv `data/downloads/20261108T131731Z/`, vikter i `data/care-weights.json`, `Services.careWeights`. 80+ kostar 7,1 gånger 65–79 (2023–2025). Sektorvikterna (`sectorCosts`, äldreomsorg 600 mnkr) är fortfarande illustrativa; Kolada anger cirka 790 mnkr för äldreomsorgen 2025.

## Granskning och rättningar (2026-11-08)

En fristående granskning (Opus) hittade inga fel i bokföringens kärna men åtta brister, alla rättade i modellen och,
där sajten påverkas, i JavaScript-referensen:
- Skatt och bidrag skalas nu mot folkmängden året före basåret (`revenuePopulation0`), som basårets skatt bygger på.
- Räntesatsen räknas på ingående skuld: 21/940 = 2,23 % (`Data.BaseYear.openingDebt`; baseline.json ändrad).
- Med importerad SKR-bana eller `revenueFromReference` läggs ingen ålderseffekt ovanpå banan.
- `AnnualCohort` hämtar SCB-data för basåret (`Data.SCB.forYear`); verksamhetens index räknas mot befolkningen vid start.
- Basårets rad visar bokslutets ränta, investering och resultat; `Budget2026` har `financialCost` att jämföra med budgeten.
- Restflödet per ettårsålder kan inte göra en ålder negativ.
- Kvar: OpenModelicas runtime ignorerar assert som fallerar mellan samplade händelser ("Found event, previous asserts are
  ignored"); bara sluttiden stoppar. Gäller både ekvations- och when-placering (i when ignoreras även sluttiden). Möjlig OM-issue.
- Skatt och bidrag skalas med Motalas folkmängd i förhållande till rikets (SCB, `data/national-population.json`), eftersom referenstillväxten är nationell.
- Nya siffror med standardantaganden: `Annual` resultat 76 (2026) och 8 (2033); `AnnualCohort` 72 och -42. Testet 2024→2025 ger skatt 2 299 mot utfallet 2 330: den illustrativa tillväxten räcker inte, så nästa steg är antaganden per prognostillfälle (SKR hösten 2024).

## Test mot SKR:s decembercirkulär 2020-2024 (2026-11-09)

- `scripts/hindcast_vintages.py` → `data/vintage-hindcast.json`. Basår 2020-2024 (`Data.motala2020`-`motala2023` nya), `Annual`,
  upp till tre år fram men inte efter 2025. Två uppsättningar: `skr` (cirkulärets skatteunderlag, PKV arbetskraft på löner och
  pensioner, PKV övrigt, rikets befolkning) och `standard` (modellens 3,5/3/2/2/2 %). Bidrag 2 % i båda.
- Basårens pengar ur `research/data/annual-ledgers.json`; åldersgrupper, födda och döda ur SCB-arkivet, som stämmer med
  årsredovisningarna. AR 2022:s 4 644 i 7-15 år 2022 är fel, SCB och AR 2025 har 4 664. Låneskuld inklusive kortfristig del
  (AR 2022 s. 32): 801,3 (2019), 788,0, 830,2, 664,5. Not 23 visar bara den långfristiga delen.
- Ett år fram, resultat, medelabsolutfel: modellen med SKR 36 mnkr, standard 66, budgeten 24, förra årets utfall 59.
  Modellen ligger i snitt 36 mnkr för lågt, budgeten 22. Bidragen underskattas 2023-2024 (+71 och +88 mnkr i utfall).
- SKR:s egen Motalaprognos från respektive tillfälle finns inte: de gamla prognosunderlagen är borta från SKR:s webb.
- Budgetens skatt och bidrag för 2021-2025 är inte hämtade; bara budgetens resultat finns.

## Generella bidrag per del: underlag för antaganden (2026-11-09)

- Motala, not 7 (AR 2023 PDF-s. 52, AR 2024 PDF-s. 27): 2022→2024 inkomstutjämning 531→581→614, regleringsbidrag
  120→102→134, kostnadsutj. 13→29→31, LSS 20→39→39, fastighetsavgift 102→106→114, övriga 8→7→21.
- SKR:s Motalaprognos (arbetsboken 2026-10-06, Blad 1): inkomstutjämning 636→847 (2026→2033, +4,2 %/år), regleringspost
  121→15 (oförändrad statlig ram i kronor), kostnadsutj. ~51-54, LSS ~53-57, fastighetsavgift 122→127, sedan oförändrad.
  Summa bidrag +1,6 %/år mot skatt +3,9 %/år.
- Regleringsbidrag per invånare: SKR:s år 1 har träffat (23:56 för 2024: 3046 mot 3055). År 2-3 har varje gång varit för
  lågt: 21:49 för 2023 1803 mot 2336; 22:54 för 2024 2294 mot 3055; 23:56 för 2025 2386 mot ~2643. Motalas regleringsbidrag
  2021-2025: 130, 121, 102, 134, 115 mnkr, ingen trend.
- SCB TAB6777 (research/data/scb-budget-response-accounts.json): bidrag/skatt 0,30 (1998), 0,22 (2004), 0,31 (2010),
  0,32 (2019), 0,42 (2025). 2010-2019 växte både skatt och bidrag 3,3 %/år.
- Inkomstbasbeloppet (styr fastighetsavgiftens tak) 66 800 (2020) → 83 400 (2026), 3,8 %/år.
- Inga modelländringar gjorda ännu; förslag lämnat till användaren.

## Bibliotek: Kommunekonomi (2026-11-09)

- `modelica/Kommunekonomi.mo` (version 0.1.0): posttyper (`Data.BaseYear`, `Data.Budget`, `Data.SCB.DemographyYear`), rikets
  SCB-data, kalibreringsfunktioner, `Assumptions`, `Interfaces`, `Components` och `partial model Annual`. Inget Motala-specifikt.
- `modelica/Motala.mo`: Handledning, `Data` (basår, budget, `SCB extends Kommunekonomi.Data.SCB` med ettårsdata),
  `Annual extends Kommunekonomi.Annual(base = Data.motala2025, olderShares = ...)`, Examples. `uses(Kommunekonomi(version = "0.1.0"))`.
- Ladda alltid Kommunekonomi.mo före Motala.mo (skript, tester, webbläsaren, OMEdit).
- `scripts/write_demography_modelica.py` skriver båda SCB-paketen. Delningen verifierad: alla sju exempelmodeller gav
  bit för bit samma resultat före och efter, liksom båda testerna mot historien och wasm-jit-pariteten.
- Nästa: en andra kommun som pilot (skripten tar ännu inte kommunkod), och bidragen per del som utbytbar komponent.

## Generella bidrag per del och regleringsregeln (2026-11-09)

- `scripts/fetch_equalisation.py` → `data/equalisation.json` (arkiv `data/downloads/20261109T160234Z`): SCB TAB1981 och
  TAB4011, alla 290 kommuner, kr/inv 2005-2026 (2026 preliminärt). Motala 2023: inkomstutjämning 13 293 kr ger 581 mnkr = not 7.
  Regleringsbidraget per invånare (lika för alla): -490 till +1 024 kr 2005-2019 utan trend, 2 336-3 055 kr 2021-2026.
- `BaseYear.grantComponents` (inkomst, kostnad, reglering, LSS, fastighetsavgift; resten övriga). Kontrollerat mot AR 2022 not 7
  (2021-2022), AR 2023-2025 not 7 och SCB per invånare (2020).
- `Revenue` har `grantsByComponent` (standard av) och `grantParts[6]`; banor per invånare i Assumptions.
- Hindcast med tre nya varianter (`components`, `hold`): regleringsbidraget ett år fram träffar exakt ur cirkuläret, men totalen
  blir inte bättre än 2 %-regeln år 1 (MAE 36 mot 31) eftersom övriga bidrag (21, 50 mnkr 2024-2025) och kostnads-/LSS-utjämningens
  hopp 2023 (+35) saknas. År 2-3: hålla regleringsbidraget per invånare (MAE 58, 96) slår cirkulärets frysta ram (74, 135).
  Alla varianter underskattar bidragen 2021-2025 (+6,6 %/år i utfall).
- SKR:s regleringspost (rad 18) importeras nu per år (`regulation` i skr-revenue-path.json). Webbens standard: regleringsbidraget
  per invånare ligger kvar efter 2027 (`holdRegulation`, kryssruta). 2033: bidrag 1 178 i stället för 1 083 mnkr, resultat 155
  i stället för 56, skuld 1 541 i stället för 1 853 (headless Firefox).

## Slutavräkning och sektorvikter (2026-11-09)

- `BaseYear.priorYearSettlement` (not 6: 2020 -10,7; 2021 7,1; 2022 13,9; 2023 12; 2024 -11; 2025 0, två årsredovisningar per år
  utom 2020). Referensbanan växer från skatten utan korrigeringen (`recurringTax0`). Skattefel i testet mot cirkulären 35/56/74
  i stället för 38/64/80 mnkr (1-3 år).
- `scripts/fetch_sector_costs.py` → `data/sector-costs.json` (Kolada, SCB:s räkenskapssammandrag; tar kommunkod). Andelar av
  nettokostnaden 2025: utbildning 43,1 %, äldreomsorg 21,5 %, övrigt 35,4 %; utbildning 0-6/7-15/16-18 = 0,26/0,55/0,19.
  `BaseYear.sectorShares` och `educationShares` per basår; biblioteket räknar `sectorCosts` och `educationWeights` ur basåret.
  `data/baseline.json` har samma vikter för 2025. Effekt 2033: Annual 8 → 6, AnnualCohort -42 → -56 mnkr.
- Nettokostnadens fel i testet mot cirkulären kommer främst från pensionskostnadens svängningar och enskilda år för övriga
  kostnader; ingen robust rättning med fem år.

## Andra kommun: Mjölby (0586) som pilot (2026-11-09)

- `scripts/fetch_municipality.py CODE` arkiverar SCB TAB6777, TAB6779, TAB6782, TAB4202, TAB5179, befolkning per ettårsålder,
  födda/döda och skattesats 2017-2025. `scripts/prepare_municipality.py` bygger basår 2020-2025 och skriver
  `modelica/municipalities/<Paket>.mo`. Omsorgsvikter och sektorandelar via `fetch_care_data.py CODE`, `prepare_care.py
  --output`, `fetch_sector_costs.py CODE`. Allt under `data/municipalities/<kod>/`.
- Kontroll mot Motalas årsredovisningar (`tests/test_municipality.py`): SCB-vägen ger samma skatt, bidrag, avskrivning, ränta
  (post 380; 390 är koncernens), skuld (081+082+136+134), kassa och investering inom 2 mnkr. Löner/pension skiljer 2020-2022
  (annan uppdelning, summan inom 16 mnkr). 2021 bokar SCB 19,5 mnkr som generellt bidrag där årsredovisningen har
  verksamhetsintäkt. Anläggningar inkl. pågående arbeten (85-177 mnkr mer).
- Folkmängd Motala 31 dec 2025: SCB ettårsåldrar 43 113, årsredovisningen 43 131, årsredovisningens åldersgrupper 43 139.
- `hindcast_vintages.py 0586 Mjolby` → `data/municipalities/0586/vintage-hindcast.json`. Samma mönster som Motala: skatt
  -22/-39/-52 och nettokostnad -24/-63/-153 mnkr i medelfel 1-3 år; bidragsfelen små (11-23). Resultat MAE år 1: 33-41 mot 44
  för förra årets utfall.
- Gemensam kvarvarande felkälla: kostnaderna växte 2021-2024 snabbare än PKV och demografi förklarar; SKR:s skatteunderlag låg lågt.

## Var felen kommer ifrån (2026-11-09)

- `scripts/cost_residual.py` → `data/cost-residual.json`: nettokostnad exkl. avskrivning (SCB TAB6777) deflaterad med SKR:s
  PKV-utfall 2009-2025 (`data/downloads/20261109T162833Z/PKV-2610.xlsx`, oktober 2026) minus demografiskt behov viktat som
  modellens sektorer. Resten är i snitt 0,2 %/år i Motala (2016-2025) och -0,2 % i Mjölby (2018-2025), men ±4 % enskilda år
  (2022 ned, 2023 upp i båda). Ingen systematisk standardökning saknas i modellen.
- Rikets skatteunderlag, utfall per inkomstår: 2021 5,3; 2022 5,8; 2023 4,8; 2024 3,5 %. SCB SkatteKraft år t = inkomstår t-2
  (2026-värdet = SKR:s arbetsbok Blad 2 rad 19, inkomstår 2024); stämmer med SKR:s cirkulär 22:54, 23:56, 24:56. 2025 saknar utfall.
- Testet mot cirkulären med facit för priser och skatteunderlag (`prices`, `hindsight`, diagnostik, inte prognos): medelfel
  skatt -10/-11/-14 (Motala) och -6/-11/-13 (Mjölby), nettokostnad +8/+21/+5 och -8/-11/-35 mnkr. Modellens struktur håller;
  prognosfelen kommer från SKR:s pris- och skatteunderlagsprognoser och, för Motala, statens bidragsbeslut (+6,6 %/år 2020-2025).
- SKR:s arbetsbok har själv ett val "värdesäkrat" för statens ram (131,9 → 150,2 mdkr 2025-2030) mot "ej värdesäkrat" (127,4 mdkr
  fryst). Regeln att hålla regleringsbidraget per invånare ligger mellan dem.

## Bidragens ökning: Motala jämfört med riket (2026-11-09)

- SCB TAB6777 (generella statsbidrag och utjämning): riket 130 805 → 146 053 mnkr 2021-2025 (+2,8 %/år); Motala 783 → 987
  (+6,0 %/år; +6,6 % räknat från årsredovisningens 763,5, där SCB bokför 19,5 mnkr annorlunda 2021); Mjölby +4,6 %/år.
  Medianen bland 280 kommuner +3,8 %/år; Motala plats 242 av 280.
- Motalas extra ökning per invånare 2021-2025 jämfört med medianen: inkomstutjämning +3 107 mot +2 760 kr (skattekraften föll
  från 89,2 till 87,3-87,6 % av riket, SCB SkatteKraft), LSS-utjämning +518 mot +84 kr, kostnadsutjämning +364 mot +299 kr.
  Regleringsbidraget är lika för alla (-329 kr). Övriga generella bidrag 5 → 51 mnkr.

## Inkomstutjämningen enligt lagen (2026-11-09)

- `scripts/fetch_tax_capacity.py` → `data/tax-capacity.json` (SCB OE0101 SkatteKraft, alla kommuner 2010-2026). År t =
  utjämningsår t (inkomster år t-2), känt i december år t-1. Motala 90,1 % av rikets medelskattekraft 2010, 87,3 % 2025, 87,6 % 2026.
- Lag 2004:773: garanti 115 % av medelskattekraften (4 §); bidrag med 95 % och avgift med 85 % av länsvis skattesats byggd på
  2003 års medelskattesats (7 §); regleringsbidraget är resten av anslaget, lika per invånare (15-16 §§); Skatteverket beslutar
  (preliminärt 20 jan, fastställt 15 april); SCB räknar ur RTB, IoT, beskattningsutfallet och Socialstyrelsens LSS-statistik.
- Implicit utjämningsskattesats ur SCB-data: Motala 19,3-20,6 %, Mjölby 19,6-20,7 % 2012-2026; avgiftskommuner (Stockholm) lägre.
- `BaseYear.relativeTaxCapacity[2]` (basår, året efter). `Revenue` med `grantsByComponent`: inkomstutjämningen skalas med
  `Data.equalisationShare(1,15 - r·composition)` mot basåret. Testet mot cirkulären: inkomstutjämningens MAE 19,8 → 15,0 mnkr
  (Motala); bidragens MAE 36/58/96 → 31/52/92. Standard (webben, Motala.Annual) är fortfarande av; webbens SKR-bana har redan
  SKR:s egen inkomstutjämning.
- Användaren vill ha svenska för ekonomiska begrepp.
- Uppföljning samma dag: `BaseYear.equalisationNextYear` (inkomst-, kostnads-, reglerings- och LSS-del per invånare året efter
  basåret, SCB TAB1981/TAB4011, publiceras i december under basåret). Med dem träffar utjämningsdelarna år 1 inom 1 mnkr i
  testet mot cirkulären; ålderseffekten räknas bara från år 2 (`incomeEqualisationComposition`). Övriga generella bidrag ligger
  kvar på basårets nivå: Motalas 51 mnkr 2025 är ett riktat statsbidrag som omklassats till generellt (AR 2025 s. 29). Rikets
  övriga generella bidrag var 225 kr/inv 2025, Motalas 1 155 kr. Bidragens MAE (hold) Motala 27/48/67 mnkr mot 31/65/104 med 2 %;
  Mjölby 13/22/25 mot 11/19/17 (pandemibidraget 2020 följer med som övriga bidrag). `grantsByComponent` är fortfarande av som standard.

## Finspång (0562) i scenariolabbet

- Finspång använder `Kommunekonomi.Annual` med ett eget Modelica-paket, `modelica/municipalities/Finspang.mo`. Webben väljer data och paket per kommunkod och har egna sparade scenarier per kommun. Finspångs första prognosår är 2026 med bokslut 2025, valbart slutår och fem åldersgrupper. Grundbanan använder historiska flyttrestflöden och illustrativa tillväxtantaganden.
- SCB:s kommunräkenskaper TAB6777, TAB6779, TAB6782, TAB4202 och TAB5179 samt demografi och skattesats arkiverades i `data/downloads/20261118T203655Z`. Koladas omsorgsvikter och sektorkostnader finns i `20261118T203656Z` och `20261118T203657Z`. SCB:s novemberbefolkning TAB6725 finns i `20261118T204714Z`. Kör `scripts/prepare_municipality.py 0562 Finspang Finspång data/downloads/20261118T203655Z --modelica` för att återskapa grundpaketet och `scripts/prepare_web_municipality.py 0562 2025 <årsredovisningens URL>` för webbpaketet.
- Stämt av Årsredovisning 2025, s. 9 och 41, mot SCB TAB6777 för kommunens resultat, skatter och bidrag 2024–2025. Årsredovisning 2024, s. 41, bekräftar 2024 års utfall avrundat till mnkr. För 2025 summerar SCB:s enskilda åldersceller med CKM-röjandeskydd till 21 577. Årsredovisningen (s. 6 och 9) och Kolada N01951 anger 21 502 vid årsskiftet. Ålderscellerna skalas proportionellt till 21 502. SCB:s novemberfolkmängd är separat, 21 485 den 1 november 2025.
- SCB:s rader för långfristiga banklån och kortfristig del gav 1 263 mnkr 2025. Modellen använder externupplåningen inklusive lån som förfallit till betalning i årsredovisningen 2025 (s. 9 och 27 och not 20–21), 1 777 mnkr, varav 290 mnkr hänförs till kommunen själv. Modellen håller ränteintäkter från vidareutlåning fasta och utvecklar en samlad banklåneskuld. Not 9 ger ränta på lån, not 11–12 ger 50 mnkr pågående investeringar och not 21 ger 0 mnkr förutbetalda generella statsbidrag 2025. Källor och definitioner finns i `data/municipalities/0562/annual-report-inputs.json`.
- `python3 scripts/recalculate_skr.py 0562` räknade om SKR:s offentliga prognosunderlag för cirkulär 26:28 med `Prognosunderlag!B1=562` och verifierad kommun `C1=Finspång`. Makron togs bort före omräkning. Skatter och bidrag stämdes av mot delposternas summor för 2026–2033. Siffror, cellkarta och källhash finns i `data/municipalities/0562/skr-revenue-path.json`. Arbetsbokskopiorna ligger lokalt i `.local/skr-0562`. Appen kan jämföra valfri Finspångsbana mot SKR, eller använda JSON-utdraget som indata via import.
- Historisk kontroll i native OpenModelica med `python3 scripts/hindcast_vintages.py 0562 Finspang`. Basår 2020–2024 med respektive års bokslut och åldersvikter samt daterade rikssiffror från SKR. SCB:s utfall 2021–2025 finns med som jämförelse. För 2025 gav basår 2024 och nationella SKR-antaganden 83,7 mnkr i resultat mot SCB:s 89,9 mnkr och kommunens budget 26 mnkr. Året före gav samma metod −87,4 mot +24,2 mnkr i bokslut och budget 33 mnkr. Absolutfel i resultat efter ett år var i snitt 38,5 mnkr över fem fall mot 38,0 mnkr för föregående års resultat. Historiska kommunvisa SKR-intäktsbanor ingår inte. Budgetjämförelsen täcker alla fem år med kommunens årsredovisningar. Detaljer i `data/municipalities/0562/vintage-hindcast.json`.

## Alla 13 kommuner i Östergötland

- Kommunväljaren använder SCB:s officiella lista för länskod 05. Alla kommuner kör `Kommunekonomi.Annual` med egna startvärden. Första prognosår 2026 använder bokslut 2025 och slutar som standard 2033. Första prognosår 2025 använder bokslut 2024 och slutar som standard 2032. Motala har även den tidigare körningen från 2022. Slutår kan väljas och appen behåller första prognosåret vid kommunbyte när den nya kommunen har samma period.
- SCB:s TAB6777, TAB6779, TAB6782, TAB4202 och TAB5179 samt befolkningsserier och skattesats hämtades per kommun 19 november 2026. Varje kommuns `base-years.json` pekar på sitt arkiv, med frågor och SHA-256 i manifestet. Koladas omsorgs- och sektorarkiv finns i respektive `care-weights.json` och `sector-costs.json`. Omsorgsvikter bygger på tillgängliga år t.o.m. basåret, normalt ett treårsmedel. Vid luckor hämtas vikterna från närmast föregående tillgängliga år.
- Gemensamt arkiv `data/downloads/20261119T090538Z-county` innehåller SCB:s novembertabeller för 2024 och 2025 samt Kolada N01951 för folkmängden den 31 december. De röjandeskyddade ålderscellerna för 2025 skalas till den publicerade totalen i Kolada. I samma arkiv finns en kontroll mot Kolada N03100 och N03102. För båda åren och alla kommuner överensstämmer SCB-radernas härledda nettokostnads- och resultatandelar med Koladas visade precision. Kolada hämtar själv de båda nyckeltalen från SCB.
- Körningen från bokslut 2024 använder rikets skatteunderlag, prisindex och befolkningsförändring ur SKR 24:56 för tillgängliga år. Därefter håller modellen kvar den sista förändringstakten. Rikets observerade serie slutar vid basåret och 2025 års kommunbokslut används i jämförelsefliken. Ekonomitabellen visar skillnad mot bokslut och har även budgetresultat när det finns i webbens källor. Befolkningen jämförs per den 31 december.
- Linköpings ränta i körningen från bokslut 2024 är 1,54 %, den redovisade genomsnittsräntan för den kort- och långfristiga upplåningen i årsredovisning 2024, not 24. Årets bokförda ränta dividerad med ingående SCB-låneskuld gav en orimlig scenarioränta eftersom posterna förändrades kraftigt mellan 2023 och 2024. Den bokförda räntekostnaden finns kvar på basårsraden. Källänken finns i `data/municipalities/0580/annual-report-inputs.json`.
- SKR 26:28 räknades om för respektive kommun och urvalet verifierades mot kommunnamnet i kalkylbladets formelcell. Alla referenser innehåller skatt, bidrag och novemberbefolkning 2026–2033. De kommunvisa JSON-utdragen och cellkartorna publiceras med appen. Excel-filerna ligger lokalt. SKR 26:28 visas som en jämförelse för gemensamma år även om modellen startar 2025. Det är en senare prognosversion än de nationella antaganden som användes för körningens start.
- Återskapa kommunpaket med `python3 scripts/prepare_municipality.py CODE Package Namn ARKIV --modelica` (för Motala används den befintliga `modelica/Motala.mo`), omräkna vid behov SKR med `python3 scripts/recalculate_skr.py CODE` och kör `python3 scripts/prepare_web_municipality.py CODE 2025` samt motsvarande för 2024. Behåll en direkt bokslutslänk där kompletterande kommunuppgifter används. `npm run build` inkluderar webbundelag och Modelica-paket för alla kommuner.

## Ettårsåldrar för alla 13 kommuner

- `Kommunekonomi.Components.CohortDemography` är valbar för samtliga kommuner med basår 2024 och 2025. Fem åldersgrupper är fortfarande appens standard. Samma ekonomikomponenter och gränssnitt används oavsett demografival. Webbkörning och Modelica-export använder samma kommunspecifika `Data.SCB`-post och fruktsamhetsinställning.
- Befolkning per ålder och kön kommer från de befintliga kommunarkiven. Födda och döda efter kön samt kommunal summerad fruktsamhet hämtades i `data/downloads/20261120T104926Z-cohorts`. Rikets livslängdstabeller och fruktsamhetstal efter moderns åldersgrupp kommer från `data/downloads/20261108T124756Z`. För äldre basår använder appen den då observerade nationella åldersprofilen. Vid luckor i Ydres publicerade fruktsamhetstal skattas den lokala nivån utifrån antalet födda och åldersviktad lokal befolkning. Folkmängden stäms av mot samma årsslutstotal som tidigare.
- Kalibreringen använder fem års dödlighet, upp till tio års uppgifter om könsfördelning vid födsel och tre års restflöden fram till basåret. Det separata läget med observerat flyttnetto använder SCB TAB1212 per ålder och kön, arkiv `data/downloads/20261120T105146Z-migration`, och medel för 2022–2024 i båda länets basperioder. Motala från 2022 använder sina tidigare daterade flyttserier.
- `scripts/prepare_municipality.py` genererar de nya kommunernas `DemographyYear`-poster från de lokala befolkningsarkiven och länets manifest. `scripts/write_demography_modelica.py` skriver de historiska nationella fruktsamhetsprofilerna. `scripts/prepare_web_municipality.py` förbereder flyttdata till webben. Länets nya källor registreras i `data/municipalities/ostergotland-sources.json`.
- Modelltestet körde ettårsåldrar från bokslut 2024 och det observerade flyttläget från bokslut 2025 för alla 13 kommuner. Kontroll mot folkmängden 31 december 2025 (Kolada N01951, länsarkiv `20261119T090538Z-county`) gav ett genomsnittligt absolut fel på 85,1 personer med ettårsåldrar och kalibrerade restflöden, jämfört med 45,1 i femgruppsvarianten. Jämförelsen gäller en prognostidpunkt och total folkmängd. Den värderar inte äldregrupperna separat. Firefox verifierade bägge ettårslägena i Finspång och Ydre. Ett exporterat Ydre-scenario från 2024 kördes även i native OpenModelica.

## Bakåttest per åldersgrupp för Östergötland

- `python3 scripts/hindcast_county_ages.py` kör Modelicas faktiska demografikomponenter för alla 13 kommuner, från basåren 2022, 2023 och 2024 fram till 2025. Inga scenariovärden ändras. Femgruppsmodellen använder två års restflöden och håller de tre äldregruppernas andelar inom 65+ fasta. Ettårsmodellen använder antingen tre års kalibrerade restflöden eller tre års observerat flyttnetto per ålder och kön. Alla kalibreringsfönster slutar i basåret. Koden jämför total folkmängd samt 7–15, 80–89 och 90+ per 31 december.
- SCB:s utfall 2023–2024 kommer från BefolkningNy i kommunernas arkiv. För 2025 hämtades publicerade CKM-celler för hela folkmängden, 7–15 summerat över åldrar, 80–89 samt 90–99 och 100+ från BefolkningCKM. Manifest och tilläggsåren 2020–2021 för flyttningar i TAB1212 finns i `data/downloads/20261120T121135Z-age-backtest`. Kolada N01951 bekräftar total folkmängd för alla kontrollår. Kolada N01957 överensstämmer för 80+ 2023–2024 och avviker 2025 med högst sex personer från summan av SCB:s publicerade åldersgrupper. SCB:s röjandeskyddade 2025-celler har egna avrundningar och perturbationer.
- Testet innehåller 78 kommun–basår–utfallsår per variant. Efter ett år var genomsnittligt absolut fel för totalbefolkning 93,1 / 125,4 / 115,3 personer, för 7–15 år 31,1 / 24,4 / 23,5, för 80–89 år 83,5 / 13,7 / 14,2 och för 90+ 9,5 / 6,8 / 8,6, i ordningen fem grupper / ettårsåldrar med kalibrerade restflöden / ettårsåldrar med observerat flyttnetto. Samma rangordning för 80–89 och totalbefolkning gäller två och tre år. 90+ har lägst fel med kalibrerade restflöden efter ett år och med observerat flyttnetto efter två och tre år. Resultat per kommun och prognoslängd finns i `research/data/age-group-hindcast.json`. De längre prognoserna bygger på färre basår och bedömer folkmängd per åldersgrupp.

## Källarkiv, licenser och git (2026-11-20)

- Användarens besked: nedladdade arkiv hör inte hemma i git. De 98 filer i 12 arkiv som redan är incheckade (SCB, Kolada, Motalas årsredovisningar och budgetar utan bilder) får ligga kvar. `.gitignore` släpper från och med nu bara igenom `manifest.json` och `README.md` för nya arkiv under `data/downloads/`, alltså källa, fråga, licens, hämtningstid och SHA-256. `20261118T142244Z` saknar manifest och syns därför inte i git alls.
- SCB-data får delas med källhänvisning (CC BY 4.0). SKR-data har egna villkor: siffrorna får användas i forskning, men hela dataset får inte publiceras. Arbetsböckerna förblir ignorerade.
- Användaren godkände att de kommunvisa SKR-utdragen (`skr-revenue-path.json`, skatt, bidrag och novemberbefolkning 2026–2033 ur 26:28) publiceras med källhänvisning. Varje utdrag har nu ett `source`-block med utgivare, titel, cirkulär, datum, länk och villkor. `scripts/recalculate_skr.py` skriver samma block vid omräkning.

## Granskning av länsgrenen (2026-11-20)

- Finspång: SCB:s materiella anläggningstillgångar (TAB6779 post 025) innehåller pågående arbeten. Kontroll: Motalas SCB-värde 2025 är 3 095,9 mnkr, årsredovisningens 2 997 plus 99 i pågående arbeten. Med byggtid räknades Finspångs 50 mnkr (årsredovisning 2025 s. 47) två gånger. `prepare_web_municipality.py` drar nu av dem från tillgångarna i bruk när årsredovisningen anger dem: 1 261,8 i stället för 1 311,8 mnkr.
- Linköping: skuldposterna i SCB (081+082+136+134) är 0, 600, 600, 14 382 och 10 424 mnkr 2020–2025 medan räntekostnaden är 1–361 mnkr. Den härledda räntan blev 47,9 % för 2024 och division med noll för 2020–2021. `Data.BaseYear` har nu fältet `interestRate` (−1 = härled). Generatorn sätter det från `forecastInterestRate` i `annual-report-inputs.json` (Linköping 2024: 1,54 %, AR 2024 not 24) och varnar för år utan rimlig ränta: Linköping 2020, 2021 och 2023 saknar fortfarande källa. Native körning av `Linkoping.Examples.Hindcast2025` ger 221 mnkr i ränta 2025 mot bokförda 361; skillnaden är troligen vidareutlåning till bolagen, ej kontrollerat i årsredovisningen.
- Mjölbys bakåttest kördes om med dagens arkiv och åldersandelar per basår. Felmåtten är oförändrade på 0,1 mnkr; arkivhänvisning och förbehåll var inaktuella. Motalaspecifika förbehåll skrivs nu bara för Motala.
- Förvalsscenariernas flyttnetto (−100 och +300) skalas med folkmängden utanför Motala. Ålderseffekten på skatten beror inte längre på länets utjämningssats.
- Valdemarsvik 2020–2022 använder Koladas äldreomsorgsvikter från 2018. Generatorn varnar nu när vikterna är mer än två år äldre än basåret.
- Ej åtgärdat: arbetaren laddar alla 13 kommunpaket vid start; kommunlistan finns både i `municipalities.js` och i `base-years.json`; novemberbefolkningen för Finspång läses ur två arkiv där det andra alltid vinner.

## Lager och flöden i kontinuerlig tid (2026-11-20)

- Användaren vill ha en mer kontinuerlig modell, byggd med lager, flöden och kopplingar, och projektet ska vara interaktivt. `Kommunekonomi.Continuous` (gren `continuous-time`) har `StockPort` (nivå och flöde), `Stock`, `Transfer`, `Inflow`, `Outflow`, `Meter` och `Clock`. `Continuous.Economy` har samma antaganden och utdata (`Report`) som `Annual`. Skulder har negativ nivå; `equityBalance` kontrollerar att lagren ändras med årets resultat.
- Demografi och intäkter är oförändrade årskomponenter som körs med en kalender som slår vid årets början (`baseYear = base.year - 1`). Befolkningen och skatten blir därför identiska med Annual; testet `tests/test_continuous.py` kräver det.
- Med standardantaganden är räntan 2–5 mnkr högre och nettokostnaden 5–25 mnkr högre per år 2026–2033 än i Annual (ränta på aktuell skuld; kostnader efter årets genomsnittliga befolkning). Bakåttest från SKR:s decembercirkulär 2020–2024 mot Motalas årsredovisningar: resultatets medelfel inom cirka 2 mnkr av Annual efter ett till tre år, skattefelen identiska (`data/vintage-hindcast-continuous.json`). Ingen träffsäkerhetsvinst.
- Webbplatsen kör fortfarande Annual. Webbläsarens `buildModel` använder `method="euler"` med ett steg per år, vilket inte räcker för den kontinuerliga modellen.
- Nästa steg enligt användaren: lokal MCP-server likt OMEdits (OMEdit/OMEditLIB/MCP, HTTP på localhost, generiska verktyg) men med projektets verktyg, så att en lokal AI kan fatta beslut år för år.
- Lokal MCP-server: `scripts/mcp_server.py` (stdio eller `--http PORT`, endast 127.0.0.1, standardbibliotek). Verktyg: kommunlista, parameterkatalog ur `Assumptions`, session per kommun och basår, beslut per år med motivering, `advance` år för år, SKR-referens och SCB-utfall, `save_session` med Modelica-fil för OMEdit. `.mcp.json` registrerar den för Claude Code. Skattesatsen kan nu sättas per år (`taxRatePath`, standard `taxRate` varje år). Webbplatsen är ännu inte kopplad till servern.

## Fler poster i bakåttestet (2026-11-20)

- Användaren: målet är ett interaktivt verktyg för beslutsfattare, inte i första hand bättre prognoser än SKR. Bakåttestet är en kontroll, inte målet.
- `hindcast_vintages.py` poängsätter nu även löner, pensioner, övriga kostnader, verksamhetsintäkter, avskrivningar, ränta, skuld och kassa. Utfall: Motalas årsredovisningar (`research/data/annual-ledgers.json`) och SCB för övriga. `scripts/compare_hindcasts.py CODE` visar Annual och Continuous parvis.
- Med SKR-antagandena (medelfel modell minus utfall efter 1/2/3 år, mnkr). Motala: löner −10/−24/−103, pensioner +10/−9/−38 (medelabsfel 41/65/43), övriga kostnader −18/−25/−50, ränta −2/−5/−9, skuld +57/+94/+22. Mjölby: löner −21/−34/−74, skuld +1/−69/−286. Kassan ändras inte i modellen utan kassapolicy, så kassafelet är kassans faktiska förändring.
- Parvis skillnad Continuous − Annual: Motala inom 2 mnkr för alla poster utom skulden (−5 efter tre år). Mjölby: nettokostnaden −3/−8/−11, varav löner −3/−6/−8, och resultatet +3/+7/+11. Tecknet stämmer med att den kontinuerliga modellens efterfrågan släpar ett halvår efter befolkningen; mekanismen är inte isolerad i ett eget test.

## Räntebindning och scenariot Högre ränta (2026-11-20)

- Användaren: att lägga in de faktiska räntehöjningarna 2022–2023 i bakåttestet vore fusk. I stället kan modellen visa hur en plötslig höjning slår igenom, som ett scenario.
- Motalas genomsnittliga räntebindning (lån och derivat) vid årets slut: 3,77 år 2023 (årsredovisning 2023 s. 41), 3,5 år 2024 (2024 s. 21), 3,19 år 2025 (2025 s. 21); riktlinje 2–4 år. Lagrat i `data/rate-fixing.json`. Andra kommuner: antagande 3 år.
- Båda modellerna har `rateFixingYears`, `rateShock` och `rateShockTime` (decimalår). Med räntebindning är `interestRatePath` marknadsräntan för nya och omsatta lån. Årsmodellen omsätter andelen 1 - exp(-1/τ) av skulden per år; den kontinuerliga har en räntekostnad med bundna räntor som närmar sig marknadsräntan gånger skulden med tidskonstanten τ. Med τ = 0 är resultaten oförändrade (paritetstesten passerar).
- Scenariot Högre ränta (+3 procentenheter från 1 januari första prognosåret) finns på webben och i MCP-servern. Motala från 2025: snitträntan 3,0 % 2026 och 4,7 % 2029; räntan 32 i stället för 23 mnkr 2026 och 71 i stället för 33 mnkr 2029.
- `-override` når inte parametrar vars standard beror på basåret (OpenModelica fäller dem vid kompileringen); `MotalaBrowser.mo` har därför bokstavliga standardvärden.
- Scenariot Högre inflation (användarens förslag, med högre ränta som en del): `inflationShockPath` i `Components.Scenario` når priserna samma år, lönerna och skatteunderlaget året därpå, pensionskostnaden samma år och marknadsräntan med 0,5 procentenheter per procentenhet; bidragen är fasta i kronor om inte `inflationGrantCompensation` sätts. Andelarna är illustrativa antaganden. Motala från 2025 med 3 procentenheter första året och hälften kvar per år: resultatet 49 mnkr lägre 2026 och 107 mnkr lägre 2033 än grundbanan. Webbläsarens wasm-körning är inte provad för de nya reglagen; native `-override` av `MotalaBrowser` är det.

## Norrköping och Linköping i kommunkorten (2026-11-23)

- Norrköping 2025: årets resultat 3 596 mnkr (SCB TAB6777 rad 120, kommunen). Varav 3 232 mnkr är en
  jämförelsestörande kostnadsreducering: återföring av avsättningen för medfinansiering av Ostlänken, eftersom
  kommunen bedömer att medfinansieringen inte blir av. Exklusive den 364 mnkr. Källa: Norrköpings kommun,
  Årsredovisning 2025 del 1, s. 60 (resultat mot budget) och s. 6 (femårsöversikt, not 2–5), hämtad
  2026-11-23 från https://norrkoping.se/kommun-och-politik/om-norrkoping/ekonomi-fakturor-och-budget/arsredovisning
  (sha256 se arkivet när det sparas). SCB TAB6779 rad 131 (avsättning för bidrag till infrastruktur) stämmer:
  28,8 → 3 299,6 mnkr 2021–2022, 3 293,3 (2024) → 45,8 (2025). Femårsöversikten anger också −3 281 (2022),
  −80 (2023) och +129 mnkr (2024) i samma post. Modellens basår 2025 räknar därför nettokostnaden 3,2 mdkr för
  låg, och alla Norrköpings banor från 2026 blev för höga. Åtgärdat 2026-11-23: `annual-report-inputs.json`
  har `nonRecurring` per år (2025: +3 232 i nettokostnaden; 2024: +230 i nettokostnaden och −101 finansiell
  kostnad, Årsredovisning 2024 del 1 s. 55) och `prepare_municipality.py` lägger tillbaka dem i basåret.
  Nettokostnaden blir 9 674 (2025) och 9 610 mnkr (2024), samma som raden Verksamhetens intäkter och kostnader i
  respektive årsredovisning. Resultatet 2026 blir 375 mnkr i grundbanan. 2022 (−3 281) och 2023 (−80) är inte
  inlagda: femårsöversikten ger bara nettot, inte uppdelningen på drift och finans.
- Linköping: grundbanan från 2026 ger resultatet 634 mnkr 2026 och 1 839 mnkr 2033. Skatten följer SKR 26:28
  nära (12 831 mot 12 977 mnkr 2033), men nettokostnaden växer 2,2 %/år i modellen (löner 3 %, priser 2 %,
  utbildningsbehovet ned till 0,88) mot 4,3 %/år 2017–2025 enligt SCB TAB6777 (skatt och bidrag 4,2 %/år).
  Räntan faller från 361 till 261 mnkr 2026 när skulden föll 2025 medan finansiella intäkter hålls på
  1 134 mnkr. De tolv kommunerna utom Motala kör från 2026 med de illustrativa standardantagandena, inte
  SKR:s årsvisa pris- och skatteunderlagsbanor; Motala har dem. Åtgärdat 2026-11-23: `prepare_web_municipality.py`
  ger basår 2025 SKR 26:28:s nationella banor (samma rader som Motala) och kommunens SKR-intäktsbana, med samma
  regel för regleringsbidraget. Linköping stiger ändå, 466 mnkr 2026 till 1 748 mnkr 2033: skatten +4,4 %/år
  enligt SKR, nettokostnaden +2,8 %/år (SKR:s index gånger demografin, invånarna +0,3 %/år). Modellen saknar
  kostnadsökning utöver demografi och pris. Inte jämfört med Linköpings egen budget och plan.

## Årsredovisningar för länets kommuner (2026-11-23)

- 61 årsredovisningar 2021–2025 för de 13 kommunerna ligger i det privata repot
  https://github.com/SVAGEN26/ekonomilabb-kallor (manifest med URL, tid och SHA-256). Sex kommer från
  Wayback Machine. Saknas: Kinda 2021–2022, Mjölby 2021 och 2024.
- `scripts/extract_annual_reports.py` läser resultaträkningen och stämmer av mot SCB TAB6777:
  `data/annual-reports/`. 881 av 1 232 rader stämmer inom 1,5 mnkr.
- Linköping redovisar pensioner avvikande ("med undantag av pensionsredovisningen", AR 2025 s. 61):
  resultat 594/233 mnkr 2025/2024 i rapporten mot 418/161 hos SCB. Modellen använder SCB. Ej utrett.
- Boxholm och Åtvidaberg 2023 har resultaträkningen som bild; inget OCR-verktyg finns installerat.

## Kritisk granskning av modellen (2026-11-23)

Oberoende granskning av koden (underagent); kontrollerad genom omkörning av `compare_hindcasts.py 0583`.
- Webbens `Annual` har inga `der()`; `Continuous.Economy` är en hybrid (lager med `der()`, årliga regler för
  skatt, bidrag, nivåer och demografi). Presentera som hybrid.
- Bakåttestet: med facit för priser och skatteunderlag blir Motalas resultatfel större (MAE 55/90/117 mot
  40/59/58 mnkr) på grund av bidragen. Det lilla felet efter tre år med SKR:s antaganden är fel som tar ut
  varandra (nettokostnad −187, skatt och bidrag −175). README och metodtexten rättade 2026-11-23.
- Kostnaden saknar ökning utöver demografi och pris; i Linköping växer intäkterna cirka en procentenhet
  snabbare per år. För Motala med facit för priser är nettokostnadsfelet +8/+21/+5 mnkr. Ej åtgärdat.
- Biblioteket har inga `unit=`. `life` = bokfört värde/avskrivning används på nya investeringar (i praktiken
  degressivt). Ränta bara på ingående skuld ger fel med samma tecken (−2/−5/−9). Ej åtgärdat.
