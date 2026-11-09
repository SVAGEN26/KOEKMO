# Projektminne: Motala ekonomilabb

Uppdaterat 2026-11-06.

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

## Återstår

1. Lokal SKR-intäktsimport är nu genomförd, inget manuellt kommunval återstår. Se `data/skr-motala/selection-receipt.json` och `skr-map.json`.
2. Granska PDF:ernas innehåll och kontrollera definitioner/enheter i befolknings- och Kolada-data före modelländringar. Bevara skillnader mellan hemkommun, lägeskommun och egen regi.
3. Delårsrapport/tertialrapport 2026 har inte hämtats. Offentligt diarium: https://diariet.motala.se/. Sökning på delårsrapport, dokumenttyp 64, 2026-01-01–2026-11-06 gav noll träffar; frånvaro är inte fastställd.
4. Detaljerad lokalkapacitet, personalanpassning, lånevillkor och pensionsprognos kan kräva ytterligare underlag.
5. Historiska SKR- och kommunprognosversioner med ursprungliga publiceringsdatum behövs för en rättvis träffsäkerhetsjämförelse. Aktuella nedladdningar är inte historiska dataversioner.

## Modellens evidensläge

En bokslutsserie 1998–2025 finns redan. Bättre precision än SKR är inte visad. SKR:s prisprognoser (PKV) är inte dess skatte- och bidragsmodell. Separata forskningsmodeller M1/M2 ska inte blandas ihop med webblabbets JavaScript-motor. Se README.md för historiska försök och deras begränsningar.

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
