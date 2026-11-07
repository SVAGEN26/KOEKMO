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

