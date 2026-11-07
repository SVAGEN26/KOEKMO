MOTALA: MODELL OCH REPRODUCERBARA PROGNOSFÖRSÖK
=============================================

Visa modellerna i OMEdit
-----------------------
Öppna MotalaDynamics/package.mo och välj Continuous i diagramvyn för att se
M2:s fem delmodeller. Examples.Base och övriga exempel kan simuleras direkt;
dubbelklicka på plant i ett exempel för att öppna delmodellerna. Diagrammen har
komponentikoner, placeringar och namngivna pilar som beskriver ekvationsbindningar.
Pilarna är grafiska förklaringar; ändra indatabindningar i Modelica-texten.
M2 använder sekunder: åtta år motsvarar 252460800 sekunder.

Motala.mo innehåller webbmodellens diagram under Motala.Annual.
MotalaResearch/package.mo innehåller M1:s diagram under Annual. M1 kräver
en genererad Scenario.mo med skattade indata för simulering, se snabbstarten nedan.
Frysta modeller i reference/ används av testerna och uppdateras inte med nya diagram.

Källor och lokala resultat i Git
------------------------------
runs/, data/raw/, nedladdade PDF:er och kompilator-/cachefiler ignoreras av Git.
Befintliga körningar finns kvar lokalt. Daterade rapportlänkar i denna text
fungerar därför först när motsvarande arkiv finns lokalt; de ingår inte i en
ny klon. Källkod, granskade JSON-indata, protokoll, review-texter, tester och
reference/ ska versionshanteras. Senare återspelningssteg behöver sina tidigare
körningsarkiv som indata. Dessa kan distribueras separat från källkoden.

Forskningsunderlag och beslutsstöd
--------------------------------
papers/README.txt och papers/sources.json listar forskningsunderlag, originallänkar
och hämtningsstatus. python3 papers/fetch.py hämtar original-PDF:er när nätverket
är tillgängligt och bevarar befintliga filer. Misslyckanden sparas som kvittenser.
decision-support-design.txt beskriver den föreslagna kopplingen mellan källor,
Modelica-komponenter och ett begripligt gränssnitt för beslutsfattare.
M2 implementerar nu de kontinuerliga mekanismerna med en separat rapport.
Befintlig webbplats använder fortfarande den äldre modellen.

Aktuell väg framåt för Motala/M2 finns i
reviews/full-goal-reconsideration-20261015.txt, som ersätter den äldre
rekommendationen i reviews/full-goal-status-20261015.txt. Tekniken och
delprövningarna är granskade, men hela prognosens precision är ännu inte godkänd.
Omprövningen prioriterade längre, avstämd Motala-historik och det låsta försöket
med laggad budgetreaktion i data/budget-response-protocol.json. Den separata,
granskade SCB-serien 1998–2025 är nu införd och utvärderad enligt samma protokoll.
Default-boksluten 2020–2025 behålls som separat underlag och räcker inte ensamma
för skattning. Resultat, källskillnader och återstående prövning beskrivs nedan.
Historiska lokala KPA-/SKR-prognosbanor är valfria indata till en egen modell.
De behövs för jämförelser med just dessa prognoser på samma informationsgrund.
Ursprungliga publiceringsdatum krävs för realtidsprövning; reviderade observationer
kan användas i en uttryckligt retrospektiv prövning. Observerade verksamhetskostnader
och volymer är därefter prioriterade för att pröva sektorsandelar och anpassningstider.
data/completion-audit.json beskriver ett äldre modellskede; dess formulering om
SKR-överlägsenhet är inte ett nytt krav på det aktuella målet.

Status för den längre bokslutshistoriken, 2026-10-23
-------------------------------------------------
python3 fetch_scb_accounts.py försöktes för samtliga fyra tabeller. Alla anrop
misslyckades vid DNS-uppslagning. Slutsatsen att data saknades var däremot fel:
en lyckad SCB-hämtning från 2026-10-16 fanns redan lokalt. Resultattabellens
originalsvar, fråga och kvittenser är nu bevarade i
reference/scb-accounts-20261016/ och filhasharna är verifierade.

python3 prepare_scb_accounts.py --out /tmp/motala-scb-accounts.json
python3 run_budget_response.py --format aggregate \
  --accounts /tmp/motala-scb-accounts.json --out /tmp/motala-budget-response-scb

Utdatafiler och kataloger ska vara nya. Normaliseringen fungerar helt offline.
data/scb-budget-response-mapping.json anger definitioner, enheter och tecken.
data/scb-budget-response-accounts.json innehåller 28 observerade år 1998–2025
och en separat jämförelse med de sex överlappande årsredovisningsboksluten.
Pensionsränta räknas från separat kolumn till och med 2010. Extraordinära poster
behålls i rapporterat resultat och dess avstämningsrest. Båda resultatbryggorna
stämmer exakt i källans tkr för samtliga år. Saknade fält i äldre/nyare
kolumnformat fylls inte med observationer. SCB-serien och årsredovisningsserien
blandas inte; bland annat finns omkring 19,5 mnkr skillnad i 2021 års bidrag
och nettokostnad, vilket inte kan beskrivas som enbart avrundning.

Körning runs/budget-response-20261023-scb/report.json ger 42 origin/horisont-fall,
fyra modeller per fall, 15 skattade öppningar och inga överhoppade fall. För
öppningsåren 2020–2024 är lambda fryst till 0,8813 från 17 övergångar till 2019.
Protokoll, trösklar och prognosregler har inte ändrats.

Resultat-MAE, mnkr, alla öppningar     ett år    två år    tre år
Antal origin/horisont-fall                 15        14        13
Budgetreaktion                        47,82     51,77     46,71
Identisk bas med lambda=0              44,64     64,71     55,32
Senast rapporterat resultat            43,71     62,72     47,35
Expanderande historiskt medel           39,47     40,39     38,05

Reaktionen förbättrar den identiska basen vid två och tre år, men försämrar
ettårsfelet och slår inte historiskt medel vid någon horisont. Det är
retrospektiv utvecklingsevidens. Ingen kandidat upphöjs till godkänd prognos.
Komponentfel, källrevisioner och redovisningsförändringar kvarstår; frysta M2
behöver jämföras på matchade fall före en eventuell promotion.
data/history-extension-status.json innehåller källhashar, komponentpoäng och
periodsammanställningar. Den gamla kontrollen med enbart default-boksluten
2020–2025 bevaras där och gav fortsatt no_evaluable_cases, exit-kod 2.

Snabbstart M2: dynamiska scenarier (kör från denna katalog)
----------------------------------------------------------
python3 run_dynamics.py --scenario base
python3 run_dynamics.py --scenario school-decline
python3 run_dynamics.py --scenario fast-adjustment
python3 run_dynamics.py --parameters data/dynamics-example-parameters.json
python3 run_dynamics.py --scenario supply-constraint
python3 run_dynamics.py --parameters data/extra-cost-example.json
python3 run_dynamics.py --scenario tax-settlement --years 3
python3 run_experiments.py data/dynamics-sensitivity.json

Experimentkommandot gör parade jämförelser under flera antaganden och skapar
en gemensam HTML-rapport. Standarddesignen ger 20 körningar över löner,
byggfördröjning, lokalkostnadsandel, omställningskostnad och en kombinerad stress.
Ändra data/dynamics-sensitivity.json för att välja andra beslut/intervall.
Skillnader mäts mot referensen under samma omvärld; spännvidden är inte ett
konfidensintervall. Misslyckade körningar redovisas och ger exit-kod 1.

Python 3.9+ och OpenModelica krävs, inga Python-tillägg. Kommandot skriver ut
sökvägen till runs/dynamics-<tid>/report.html. Rapporten öppnas som lokal fil;
årsflöden integreras över året och bestånd redovisas vid årets slut. CSV/JSON,
kompilatorlogg, källkod, dataunderlag och filhashar sparas bredvid rapporten.
--years väljer horisont, --output en ny eller tom katalog. Befintliga körningar
skrivs inte över. OMC kan ange kompilatorns absoluta sökväg.

MotalaDynamics/Parameters.mo innehåller vanliga Modelica-parametrar för bland
annat initiala bestånd, personalanpassning, kostnadsandelar och livslängder.
JSON-filen kan ändra dessa och konstanta indata; vektorer är JSON-listor,
matriser är listor av rader. Verksamhetsordningen är utbildning, äldreomsorg,
övrigt. Exempel: {"reductionYears": [0.5, 3, 3]} ändrar utbildningens
anpassningstid nedåt till ett halvt år. Räntor anges som andelar: 0.05 = 5 %.
Tidsberoende beslut binds i en Modelica-scenariomodell, se Examples.mo.

Extra kostnader anges även som vanliga parametrar, utan att skriva om ekvationer:
{"extraCostPath": [0, 50, 0], "extraCostPaymentPath": [0, 20, 30]}
I standardkörningen motsvarar första posten 2026. Exemplet bokför 50 mnkr extra
driftkostnad 2027 och betalar 20 mnkr 2027 samt 30 mnkr 2028. Utelämnas
extraCostPaymentPath följer betalningarna kostnaderna. Båda listorna ska ha samma
längd. Efter sista posten är tillägget noll, så en engångskostnad upprepas inte.
Beloppen är nominella mnkr per år och räknas inte upp en gång till med prisindex.
Återkommande tillägg anges för varje önskat år. Lägg bara till kostnader som inte
redan ingår i övrig drift eller pensionsbanan; investeringar har egna indata.
Rapporten visar kostnad, betalning och periodiseringssaldo var för sig. Positivt
saldo är obetald kostnad och negativt saldo är förskottsbetalning. Det är en brygga
för tilläggen sedan simuleringens start, inte kommunens hela avsättningsskuld.
Scenariot --scenario extra-cost visar samma exempel. För variation inom ett år
kan input extraExpense och extraPayments bindas explicit i Modelica.

V2 har separata payrollShares, otherExpenseShares, operatingRevenueShares,
assetShares och investmentShares. Varje vektor summerar till ett; sectorShares
är gemensam fallback. limitStaffChanges och limitExternalService aktiverar tak
för personalförändring respektive köpt service. supply-constraint demonstrerar
ett ökat omsorgsbehov med sådana tak. staffReductionCost och capacityClosureCost
anger engångskostnader vid omställning; default noll är ett scenarioantagande.
Ingående byggprojekt är nu 99 mnkr enligt bokslutet, med antagen fördelning.

native/resolved-parameters.json visar kompilatorns beräknade parametervärden,
även beroende standardvärden. evidence.json skiljer observerade belopp från
härledningar och antaganden. Årsrapporten visar också kostnader per verksamhet,
köpt service och integrerad servicebrist. Inga antagna årsarbetskrafter har
ersatts med bokslutets antal anställda, eftersom måtten inte är samma sak.

I OMEdit: öppna MotalaDynamics/package.mo och simulera Examples.Base eller
ett annat exempel. Continuous är komponenten inuti scenariot; input-bindningar
ska lösas där, inte lämnas åt simuleringens toppnivåindata. Tiden mäts internt
i sekunder; åtta år är 252460800 sekunder. Alla exponerade kostnadsflöden är
mnkr/år. resultRate vid årsslut är inte samma sak som hela årets resultat.

SchoolDecline och FastAdjustment fryser befolkningen och minskar utbildningens
behov med 15 procent efter ett år. Enbart personalens anpassningstid skiljer
dem åt: tre år respektive ett halvår. Övriga exempel är staffing-cut,
interest-shock och pension-accrual. Det är kontrollerade mekanismexperiment.

M2 har kontinuerliga tillstånd för befolkning, personal, fysisk kapacitet,
byggprojekt, bokförda tillgångar, ränta, skuld och kassa. Intäktsdelen är en
schablon med separat skattesats och utjämningskänslighet; den ersätter inte
SKR:s regelverk. Externa intäkter kan bindas med useExternalRevenue=true,
externalTax och externalGrants. externalTax anges vid taxRate0; den räknas
om med taxRate/taxRate0. En sådan körning är beroende av det externa underlaget.
externalTaxSettlement kan ange kollektiv avräkning separat i mnkr/år.
Den multipliceras inte med egen skattesats och får då inte också ingå i
externalTax. taxPayments anger nettoinbetalning av skatt; förvalet är tax.
taxReceivable0 anger ingående nettoskattefordran; förval noll är ett antagande.
Skillnaden mellan bokförd skatt och betalning ändrar fordran, inte kassan.
Rapporten visar intäkt, separat avräkning, betalning och utgående fordran.
tax-settlement visar 50 mnkr avräkning 2027 som betalas 2028, med konstant
referensskatt och konstanta bidrag. Det är ett mekanismexempel, inte en prognos.
useExternalTax=true ersätter enbart skatten med externalTax och lämnar den
interna bidrags-/utjämningsbanan kvar. Det är användbart för en isolerad
känslighet, men utjämningen reagerar då inte på den externa skattebanan.

Härledning, källor och antaganden: ../docs/dynamics-equations.md.
Sektorandelar, personal, kapacitet och anpassningstider är ännu inte skattade
för Motala. Balanser och mekanismer är testade; den historiska prövningen nedan
visar precisionen och dess begränsningar.

Historisk prövning av M2 (kräver även NumPy för jämförelsen med M1)
----------------------------------------------------------------
Motala är huvudfallet. Modellens användbarhet bedöms i första hand mot Motalas
historiska bokslut och lokala planeringsbehov. Prövningen på andra kommuner nedan
är en separat kontroll av överförbarhet och överanpassning.

python3 run_historical.py --out runs/min-historiska-provning

V3 skiljer föregående årsbelopp från momentana öppningsflöden. Vid oförändrad
kvantitet ger exempelvis 3 procents tillväxt exakt 3 procent högre integrerat
årsbelopp. annualFlowAnchoring=false behåller äldre konvention för kontroll.

Historiska startvärden från 2020–2024 jämförs med bokslut 2021–2025. Rapporten
visar M2, fryst v2, M1, oförändrat resultat och fast dämpad trend på samma år.
Detta är utvecklingsevidens med reviderade data och okända publiceringsdatum.
Byggprojekt saknas för2020/2021; antaganden redovisas separat från observationer.
Ingen parameter optimeras mot utfallet. Framtida perioder hålls utanför varje
prognos och native-tester kontrollerar att ändrade framtida utfall inte läcker in.

Granskad körning: runs/historical-v3-20261015-audited/report.html.
Ettårs-MAE för resultat: M2 61,93mnkr, oförändrat resultat58,92mnkr.
Modellen är ännu inte en verifierad förbättring av punktprognosen.
Källor/konflikter: data/annual-ledgers.json. Låsta antaganden:
data/historical-protocol.json. Ingen jämförelse med SKR på matchade datum är gjord.

Prövning med daterade SKR-kostnadsprognoser
-----------------------------------------
python3 run_historical.py --protocol data/historical-protocol-pkv.json --out runs/min-pkv-provning

Rapport: runs/historical-v3-20261015-pkv/report.html.
Samma fem starter används. SKR:s decembercirkulär från respektive startår ger
årsvisa faktorer för total personalkostnad inklusive pension och övrig förbrukning.
Lön och pension indexeras gemensamt, utan ett ytterligare pensionspåslag.
De enskilda löne-/pensionsposterna är beräkningsposter, inte separata prognoser.
Den enkla jämförelsen PKV-accounting använder samma kostnadsbanor men håller
volymer, avskrivning och finansnetto oförändrade. Inga parametrar optimeras.

Resultat-MAE, mnkr              ett år    två år    tre år
Antal målår                       5         4         3
M2, ursprungliga prisantaganden  61,93     81,69     56,05
M2-PKV                          25,21     49,20     83,02
PKV-accounting                  24,25     39,73     96,82
Oförändrat resultat             58,92     76,28     40,87
Historiskt medel                51,47     54,09     32,43

Förbättringen på ett års sikt kvarstår när valfritt målår tas bort från jämförelsen
mot oförändrat resultat eller historiskt medel. Detta är en känslighetskontroll,
inte ett konfidensintervall. Precisionen på tre års sikt försämras. Den dynamiska
modellens mervärde för punktprognoser är inte fastställt jämfört med PKV-accounting.
Personalkostnadens ettårs-MAE förbättras från 82,19 till 37,20 mnkr; andra
komponenter och lokala pensionsförhållanden kan fortfarande ge stora fel.
Skatt och generella bidrag underskattas i samtliga fem ettårsfall. Kostnadsfel
kompenserar ibland för intäktsfel, så ett lägre resultatfel räcker inte för att
validera de underliggande komponenterna eller effekten av politiska åtgärder.
Det låsta budgetreaktionsförsöket har därefter körts med den längre SCB-serien;
se resultat och kvarstående källskillnader i början av dokumentet. Daterade
lokala intäkts- och personalantaganden är kompletterande underlag. Kontroll av
Motalas egna engångsposter utgår från respektive öppningsårs källor.

Källor: data/skr-pkv-vintages.json. Originalcirkulärens datum är verifierade.
Bokslutens ursprungliga publiceringsversioner är inte fullständigt verifierade;
övningen är fortfarande utveckling efter att utfallen redan har granskats.
PKV är ett nationellt prisindex, inte SKR:s kommunvisa modell Skatter och bidrag.
2020/2021 års PKV innehåller en kvalitetsjustering av arbetskraft. SKR tog bort
denna i april 2022 (cirkulär 22:15 s. 14). Oförändrad bemanning motsvarar därför
inte exakt samma volymdefinition i alla cirkulär. Ingen efterhandskorrigering
har lagts till för att förbättra utfallet.

Not 10-kostnadsbas och separat intäktskänslighet
----------------------------------------------
python3 run_historical.py --protocol data/historical-protocol-events.json --out runs/min-notprovning

Rapport: runs/historical-v4-20261015-notes/report.html.
Regeln och båda varianterna låstes före första omräkningen. Redan bokförda
PFAS-/deponikostnader och försäljningsförlust enligt not 10 upprepas inte i den
återkommande kostnadsbasen. Alla observerade slutstockar och hela bokslutsutfallet
behålls. Det är inte fullständig engångsrensning; andra noter lämnas utanför.
data/motala-noted-events.json visar samtliga noter, tecken och källkonflikter.

Resultat-MAE, mnkr                       ett år    två år    tre år
Antal målår                                5         4         3
M2-PKV, ursprunglig bas                   25,21     49,20     83,02
M2-PKV-costbase, not 10-kostnadsbas        16,03     57,61    104,24
PKV-accounting-costbase                   21,80     48,13    117,63
M2-PKV-no-repeat, intäktskänslighet        35,01     90,87     86,52

Intäktskänsligheten antar även att notens tillfälliga inkomster inte upprepas
eller ersätts med annan finansiering. Den är inte ett sannolikhetsintervall.
Ettårsfelet förbättras med kostnadsbasen, men två- och treårsfelen ökar. Intäkts-
och kostnadsfel tar fortfarande delvis ut varandra. Alla fall finns kvar, och
ingen scenarioselektion efter resultat har gjorts. Extra kostnadsbanor är noll
i dessa historiska körningar. Framtida nya kostnader, betalningar och omvärdering
är skilda antaganden; att en tidigare kostnad inte upprepas tar inte bort en skuld.

Separat prövning av nationellt skatteunderlag
--------------------------------------------
python3 run_historical.py --protocol data/historical-protocol-tax.json --out runs/min-skatteprovning

Rapport: runs/historical-v5-20261015-tax/report.html.
Samtliga fem startår använder samma decembercirkulär som PKV. Tax-only antar
konstant lokal andel av rikets faktiska nominella skatteunderlag. Befolkningen
multipliceras inte in en gång till. Varje variants bidragsbana är oförändrad,
även den förenklade utjämningen. Skuld och ränta får reagera på ändrad skatt.
Ändringen omfattar både tillväxtunderlag och demografisk skattemekanism; effekten
kan därför inte tillskrivas enbart den daterade tillväxtprognosen.

Resultat-MAE, mnkr                       ett år    två år    tre år
Antal målår                                5         4         3
M2-PKV-costbase                          16,03     57,61    104,24
M2-PKV-costbase-tax-only                 20,94     55,63     93,47
M2-PKV-no-repeat                         35,01     90,87     86,52
M2-PKV-no-repeat-tax-only                47,01     88,90     74,70

Själva skattefelet försämras på alla horisonter: MAE 27,48/55,19/49,19 blir
30,94/62,37/57,03 mnkr. Bidrag/utjämning står för den största systematiska
intäktsunderskattningen, med oförändrad bias -29,51/-74,76/-120,44 mnkr.
Nettokostnadens bias är samtidigt -35,89/-78,35/-199,19 mnkr. Mindre resultatfel
på längre sikt visar därför inte en bättre skatteprognos.

Alla gamla prognoser, 12 målfall, båda notvarianterna och WIP-känsligheter är
bevarade. Källor: data/skr-tax-vintages.json. Diagnostiken är inte godkänd som
kommunvis SKR-prognos. Öppningsskatten innehåller slutavräkningar, och ändrade
skatteregler kan kompenseras genom statsbidrag som inte ingår i denna ändring.
Nästa intäktssteg behöver stämma av bidragskomponenter och skatteavräkning mot
daterade primärkällor. data/local-forecast-catalog.json dokumenterar sökningen;
politiska förslag och senare återgivna budgetar har inte använts som indata.

Underlag för en uppdelad intäktsmodell
-------------------------------------
data/motala-revenue-components.json stämmer av not 6 och 7 för 2020–2024
mot bokslutens skatt och bidrag. data/skr-revenue-vintages.json innehåller
de fem decembercirkulärens befolkning, medelskattekraft, reglering och
avräkningar. Källorna och härledningen i ../docs/dynamics-equations.md §7.1
har granskats separat, se reviews/revenue-sources-20261015.txt.
motala_lab/revenue_bridge.py prövar enheter, referensdatum och algebra.
Den används också för källurval i den normaliserade delprövningen nedan.
Modelica har separat avräkningsindata och skattefordran, men hela den
regelbaserade prognosen och historiska betalningsunderlag återstår.

python3 fetch_revenue_sources.py

Kommandot hämtar sju SCB-tabeller till en ny katalog i data/raw/revenue,
med URL, hämtningstid och filhash. Misslyckanden sparas i receipts.json.
Lokal novemberbefolkning och administrativa underlag återstår att verifiera.
Korrigerade tabeller är kontrollunderlag tills deras historiska versioner
har fastställts. Framtida skatteunderlag, avräkningar och kategoriövergångar
behöver låsta regler före nästa prövning. Källgranskningen innebär inget
godkännande av flerårig prognosprecision.

Normaliserad prövning av preliminär skatt och inkomstutjämning
------------------------------------------------------------
python3 run_normalized_revenue.py --out runs/historical-v6-normalized-PI

Protokoll: data/historical-protocol-normalized-revenue.json. De två delarna
följer samma förändring i nationell skattekraft under antagandet om konstant
relativ lokal skattekraft och referensbefolkning. Första året använder det
daterade cirkulärets regeringsvärde, senare år SKR:s prognostiserade nivå.
Inget saknat novemberantal fylls i och ingen lokal faktor anpassas till utfall.

Alla tidigare prognoser kopieras oförändrade från det hashkontrollerade v5-
arkivet. Två nya Modelica-varianter och två bokföringsvarianter läggs till.
Den återstående intäktsdelen behåller jämförelsens antaganden och är ingen
fullständig avräknings-/bidragsprognos. P/I-komponenterna, hela resultatet och
finansieringens effekt visas separat. 2025 års komponentutfall finns i en
separat målfil och används aldrig som prognosindata för starter 2020–2024.
Årsutfallen är redan granskade utvecklingsdata, inte ett blint slutprov.

Den låsta körningen finns i
runs/historical-v6-20261015-normalized-PI-reviewed/report.html.
För costbase blir MAE i mnkr, med 5/4/3 fall för 1/2/3 år:

                                      1 år      2 år      3 år
Tidigare allokerad preliminär skatt    28,79     33,68     32,57
Ny preliminär skatt                    8,72     19,50     37,29
Tidigare allokerad inkomstutjämning    19,47     45,23     75,28
Ny inkomstutjämning                    9,82     24,30     46,58
Tidigare allokerad summa P+I          46,66     68,07    104,27
Ny summa P+I                          4,08     35,46     78,01
Tidigare hela årsresultatet          16,03     57,61    104,24
Nytt hela årsresultatet              45,52     88,00    102,00

Komponentvinsten räcker inte för att ersätta tidigare kandidat. Skattens
totalfel försämras när den ärvda avräkningsdelen ligger kvar, och personalens
flerårsfel är oförändrat. Treårsfelet i preliminär skatt blir också sämre.
Båda notpolicys och samtliga ogynnsamma resultat finns kvar i rapporten.
Den mycket lilla P+I-summans ettårsfel får inte dölja motriktade komponentfel.
Källsamlingarnas ursprungliga statusetiketter bevaras i protokollets hashade
filer; deras användning i just detta experiment anges i det separata protokollet.

Arkivet innehåller hela v5-referensen, nya källor, datakopior och native-körningar.
För reproduktion från ett sådant arkiv, från projektets modelica-katalog:
PYTHONDONTWRITEBYTECODE=1 python3 runs/<id>/sources/run_normalized_revenue.py \
  --parent-run runs/<id>/reference --out /tmp/motala-normalized-reproduction

Separat prövning av daterad skatteavräkning
-----------------------------------------
python3 run_settlements.py --out runs/historical-v7-settlements

Protokoll: data/historical-protocol-settlements.json. Hela v6:s ärvda skatterest
ersätts av första årets daterade avräkningsprognos, med Motalas årsslutsbefolkning
som uttrycklig proxy för 1 november samma startår. För senare år och framtida
revisionsdifferenser antas noll. Källornas null ligger kvar separat. P/I, bidrag
och kostnader behålls från v6. Avräkningen är signerad och skalas inte med egen
skattesats. Alla tidigare prognoser och målutfall bevaras, inklusive båda
notpolicys, accounting-kontroller och WIP-alternativ. Ingen kandidat byts ut.

Rapporten visar avräkning plus revision, preliminär skatt, hela skatten,
bidrag, personal och samtliga huvudmått. Finansieringens effekt visas separat.
Befolkningskänsligheten s*deltaN/1e6 är en direkt intäktseffekt av hypotetiska
proxyfel, inte en uppmätt felgräns eller ett fullständigt resultatintervall.
Samma års skattebetalning och noll öppningsfordran är fortfarande antaganden.

För reproduktion från sparade källor och den kopierade v6-referensen:
PYTHONDONTWRITEBYTECODE=1 python3 runs/<id>/sources/run_settlements.py \
  --parent-run runs/<id>/reference --out /tmp/motala-settlement-reproduction

Första låsta körningen: runs/historical-v7-20261015-settlements/report.html.
Costbase, MAE i mnkr mot motsvarande v6-variant, samma 5/4/3 fall:

                                      1 år      2 år      3 år
Avräkning inklusive revision, v6      37,84     65,29     81,76
Avräkning inklusive revision, v7      40,98     32,00     21,00
Hela skatten, v6                      41,88     77,22     95,42
Hela skatten, v7                      37,65     51,50     56,29
Skatt och bidrag tillsammans, v6      22,25     55,34    103,06
Skatt och bidrag tillsammans, v7      50,27     83,53    132,84
Hela resultatet, v6                   45,52     88,00    102,00
Hela resultatet, v7                   29,13     65,11     90,46

Första årets avräknings-MAE försämras trots lägre RMSE; första årets skattevinst
är skör vid utelämning av ett målår. Resultatvinsten mot v6 är stabil i dessa
utelämningar på ett och två års sikt, men inte på tre års sikt. Tidigare
M2-PKV-costbase har fortfarande lägre resultat-MAE på ett och två år
(16,03/57,61); på tre år är det historiska medelvärdet bättre (32,43).
V7:s no-repeat-resultat ger MAE 57,11/98,35/84,99. Dessa jämförelser behålls.
Bidrag och personalkostnader är oförändrade. Lägre sammanlagt resultatfel
innebär därför inte att de kvarvarande komponentfelen har lösts. Skatt och
bidrag tillsammans får större fel på samtliga horisonter, trots lägre fel i
hela skatten separat. Resultatvinsten måste läsas tillsammans med att
intäkts- och kostnadsunderskattningar tar ut varandra.

Separat prövning av regleringsbidraget
------------------------------------
python3 run_regulation.py --out runs/min-regleringsprovning

data/historical-protocol-regulation.json låser försöket före första poängsättning.
Det bygger vidare på den frysta v7-prövningen och ändrar endast regleringsbidraget
och den överförda flykting-/välfärdskategorin. SKR:s daterade kronor per invånare
multipliceras med startårets lokala årsslutsbefolkning. Samma folkmängd hålls
konstant vid alla horisonter som proxy för november året före respektive målår.
Den ärvda proportionella regleringskategorin tas bort innan den nya läggs till.
Vid start2020 tas också flykting-/välfärdskategorin bort enligt övergången2021;
no-repeat-policyens tidigare borttagning av82,1 mnkr upprepas inte.

Preliminär skatt, inkomstutjämning, avräkning och kostnader behåller v7:s regler.
Båda notpolicyer, tolv prognosfall, WIP-alternativ och tidigare jämförelser finns
kvar. Reglering plus överförd kategori, återstående bidrag, totalbidrag och hela
resultatet bedöms separat. Befolkningskänslighet är hypotetisk direkt effekt,
inte en statistisk felgräns. Försöket innebär ingen ny godkänd huvudprognos.
Costbase behåller 2020 års 82,1 mnkr i övriga bidrag. Dess avgränsning mot senare
nationella tillskott är fortfarande osäker; de två policyerna är scenarier.

Fryst körning: runs/historical-v8-20261015-regulation/report.html.
104 tester passerade. Arkivet innehåller 18 nya native-körningar, 12 prognosfall
och 1262 hashade filer. Tidigare prognoser och utfall är bevarade.
MAE i mnkr, ett/två/tre år framåt, samma 5/4/3 fall:

                                      v7                 v8
Reglering + överförd kategori     31,35/28,42/19,23   2,56/20,66/42,16
Totalbidrag, costbase             20,44/53,84/91,74  41,91/83,43/124,45
Totalbidrag, no-repeat            35,38/75,14/120,64 27,73/83,70/153,34
Resultat, costbase                29,13/65,11/90,46  33,69/45,45/92,02
Resultat, no-repeat               57,11/98,35/84,99  41,09/78,68/77,86

Ettårsvinsten för reglering håller när ett målår i taget utelämnas. Treårsfelet
för samma komponent ökar vid samtliga sådana utelämningar. V8 förbättrar därför
inte alla horisonter. Totalbidragets costbase-fel ökar på samtliga horisonter;
för no-repeat minskar ettårsfelet men den vinsten håller inte vid varje
utelämning. I costbase är 2021 års återstående bidrag överskattat med 79,96 mnkr,
samtidigt som regleringsfelet bara är +0,09 mnkr. Den gamla regleringsmissen
döljde alltså en del av felet i resten. No-repeat ger -3,74 mnkr i samma rest.

Personalkostnadernas MAE är oförändrat 37,20/98,69/137,04 mnkr. V8-costbase:s
treårsresultatfel 92,02 är större än historiskt medelvärdes 32,43 och oförändrat
resultats 40,87 mnkr. Lägre tvåårsresultatfel innebär inte att intäkterna blivit
bättre: skatt plus bidrags MAE ökar där från 83,53 till 92,08 mnkr. Kostnads- och
intäktsfel måste fortsatt bedömas separat. Ingen huvudkandidat har bytts.

Återkör enbart de sparade källorna, från projektets rot:
PYTHONDONTWRITEBYTECODE=1 python3 modelica/runs/historical-v8-20261015-regulation/sources/run_regulation.py \
  --protocol modelica/runs/historical-v8-20261015-regulation/protocol.json \
  --parent-run modelica/runs/historical-v8-20261015-regulation/reference \
  --out /tmp/motala-v8-egen-aterkorning
Utmatningskatalogen måste vara ny. Äldre hashlistade cachefiler bevaras endast
som historiska artefakter; körkommandot skriver inte nya Python-cachefiler.
Oberoende återkörning gav byteidentisk evaluation.json och samtliga 18 native.csv.
Granskaren verifierade även samtliga 1262 arkivhashar och 1043 parenthashar,
bevarade äldre resultat samt 11393 separat räknade poäng- och identitetstal.
Tekniskt reproducerbar betyder här inte att hela prognosen är godkänd.
Slutbeslutet i reviews/regulation-20261015.txt godkänner delprövningens teknik,
men varken kandidatbyte eller hela Motala-prognosens precision. Nästa diagnos
kan dela upp den återstående bidragsresten med befintliga noter och oförändrade
prognoser; detta ger inga nya validerade administrativa prognosbanor.

Diagnos av återstående bidrag i v8
--------------------------------
python3 run_grant_audit.py --run runs/historical-v8-20261015-regulation \
  --out runs/min-bidragsdiagnos

runs/grant-audit-20261015/report.html visar den granskade körningen.
Öppningsbeloppen för kostnadsutjämning, LSS, fastighetsavgift, andra generella
bidrag och signerad avrundning multipliceras med samma faktor: den frysta
restprognosen dividerad med det notjusterade restankaret. Det är en diagnostisk
allokering, inte nya administrativa delprognoser. Inga prognoser har ändrats.
82,1 mnkr tas enbart bort från öppningsårets andra generella bidrag under
no-repeat. Målutfallen behålls i sin helhet, med avrundningen separat.

Alla tolv fall, två policyer och två beräkningsvarianter ger 48 redovisade rader,
inte 48 oberoende observationer. Rest-MAE för native är, ett/två/tre år framåt:
costbase 34,10/56,89/64,58 mnkr och no-repeat 18,86/38,74/64,60 mnkr.
Signerade fel och bias summerar till resten; komponenternas MAE gör det inte.

Några konkreta avvikelser under den deklarerade allokeringen:
- 2020 till 2021, costbase: andra generella bidrag +78,50 mnkr, hela resten
  +79,96. No-repeat ger -5,20 respektive -3,74 i samma fall.
- 2022 till 2023: kostnadsutjämning -15,44 och LSS -18,82 mnkr, medan andra
  generella bidrag bara avviker -0,25 mnkr.
- 2022 till 2025: andra generella bidrag -43,01, kostnadsutjämning -18,01,
  LSS -19,18, fastighetsavgift -11,74 och avrundning +1,00 mnkr.
Olika starter missar således olika kategorier. Detta motiverar daterade
administrativa underlag, inte en ny gemensam tillväxtfaktor vald efter utfallet.

reviews/grant-audit-20261015.txt godkänner diagnosen tekniskt. Oberoende
återkörning gav fem byteidentiska filer. Granskaren räknade 1494 tal separat,
verifierade exakta källkopior och kontrollerade att v8:s 1262 hashposter var
oförändrade. Hela prognosens precisionsmål är fortsatt inte uppnått.

data/grant-forecast-discovery.json identifierar daterade SKR-underlag 22:58
för kostnads-/LSS-utjämning och 22:57/23:60 för kommunal fastighetsavgift.
De är daterade efter de specifika decembervintager som v8 använder men före
dess årsslutsgräns. En ny prövning behöver en uttryckligt ändrad källvalsregel
för alla startår och originaltabeller för Motala; själva datumgränsen behöver
inte ändras. Fastighetsavgiftens aktuella prognos, föregående års korrigering och
betalning måste också skiljas åt. Bilaga 5:s standardkorrigering förutsätter att
kommunen använde den angivna tidigare prognosen; Motalas faktiskt bokförda
uppskattning måste verifieras eller antagandet märkas. Hela not 7-raden kan
innehålla en äldre korrigering och ersätter därför inte automatiskt denna
uppskattning. Inga saknade kommunbelopp har fyllts i. Den oberoende granskningen
finns i reviews/grant-source-discovery-20261015.txt.

data/motala-property-fee-vintage-2025.json innehåller nu Motalas avgiftsbelopp
ur bilagorna till SKR 25:62: prognoser för 2025–2027 samt den villkorade
bokslutsbryggan för 2025. Beloppen avser aktuell avgiftsperiod; föregående års
korrigering och betalning är egna storheter. Detta är en senare informationsversion
för framtida prognosarbete och definitionskontroll. Den fyller inte luckorna i
2020–2024 års originalprognoser och används inte av de historiska körningarna.
Originalfilens tryckta datumkonflikt, arkivåtergivning och åtkomstbegränsningar
är dokumenterade. Ingen ny prognosprecision följer av transkriptionen.
reviews/property-fee-vintage-2025-20261015.txt bekräftar beloppen och fem
exakta heltalsidentiteter. Både aktuell avgift 119,132088 mnkr och villkorad
bokslutsintäkt 118,633784 mnkr avrundas till 119; årsredovisningens avrundade
rad bevisar därför inte att Motala använde standardkorrigeringen.

Diagnos av kostnadsfelen i den frysta v7-prövningen
-------------------------------------------------
python3 run_cost_audit.py --run runs/historical-v7-20261015-settlements \
  --out runs/min-kostnadsdiagnos

Detta skapar inga nya prognoser och passar inga parametrar. För varje gammalt
fall och båda notpolicys delas personalfelet exakt i felet i bokföringsprognosen
med oförändrade kvantiteter och modellens kvantitetsbidrag. Den första termen
är inte ett identifierat pris- eller pensionsfel: faktisk bemanning, löne- och
pensionssammansättning samt källskillnader ingår också. Nettokostnadsfelet
delas dessutom i personal, övrig drift, minus driftintäkt, avskrivning och
angivna modellflöden/avrundning. Biasbidrag kan summeras, komponent-MAE kan inte.

Definitionskontrollen i data/motala-personnel-sources.json och
reviews/personnel-definitions-20261015.txt visar att personal/pension
omklassificerats mellan2022/2023. Den summerade personalen är betydligt mer
jämförbar än delarna, med en bevarad versions-/avrundningsskillnad på-1,1mnkr
för2022. Exakt placering av löneskatt i2024/2025 är inte verifierad från enbart
notrubriken. Ingen historisk bokslutsrad skrivs om av denna diagnos.

En lokal KPA-bana kräver separata definitioner för driftspension, löneskatt,
pensionsfinans och betalningar. De gamla delarna måste ersättas en gång i
rätt bas. Att lägga en ny pensionsprognos ovanpå PKV inklusive pension och
arbetsgivaravgifter skulle dubbelräkna. Fullständiga daterade lokala banor
har ännu inte återfunnits; den framåtblickande uppgiften över100mnkr i
årsredovisning2022 är ingen exakt punktprognos.

Diagnosen kan återköras med enbart standard-Python från sin sparade kopia:
PYTHONDONTWRITEBYTECODE=1 python3 runs/<id>/run_cost_audit.py \
  --input-packet runs/<id>/input-packet.json --out /tmp/motala-cost-reproduction

Den oberoende reproducerade rapporten finns i
runs/cost-audit-20261015-reviewed/report.html; granskning i
reviews/cost-audit-20261015.txt. Den tidigare rapportversionen bevaras;
endast en formulering som kunde läsas som kausal ändrades. Alla siffror
och indata är exakt lika mellan versionerna.

Personalkostnadens MAE i mnkr, samma 5/4/3 fall:
                                      1 år      2 år      3 år
Native-modellen                      37,20     98,69    137,04
PKV med oförändrade kvantiteter       37,29     99,46    143,99

Modellens kvantitetsbidrag till personalen ligger mellan0,06 och8,67mnkr.
Stora fel finns således kvar i jämförelsen med fasta kvantiteter. Det visar
inte att faktisk bemanning saknar betydelse och identifierar inte ett rent
pensions- eller prisfel. Diagnosen är granskad; hela flerårsprognosen är
fortfarande inte godkänd som tillräckligt validerad.

Separat prövning på tre andra kommuner
-------------------------------------
python3 run_external_pkv.py --out runs/min-externa-pkv-provning

Kräver bara Python 3:s standardbibliotek. Före insamlingen av kommunernas utfall
låstes PKV-accounting, ursprung2022–2024, horisonter1–3 och målår till2025.
Kommunerna är Vadstena, Mjölby och Norrköping. Inga parametrar har sedan ändrats.
Detta är ett kompletterande test. Ett fel i prognosen för en annan kommun är
inte ett fel i Motalas bokslutsdata och ändrar inte Motalas redovisade prognosfel.
En ny mekanism i huvudmodellen behöver motiveras av Motalas förhållanden eller
av en allmän redovisningsidentitet, inte enbart av ett annat kommunfall.
Protokoll: data/external-pkv-protocol.json. Fryst källa: reference/pkv-accounting-v1.
Rapport: runs/external-pkv-v1-20261015-audited/report.html.

Alla18 fall behålls.15 går att poängsätta:8/9 ettåriga,5/6 tvååriga och2/3 treåriga.
Exakt Norrköpingsresultat2025 saknas i läsbar primärtabell. Kommunens pressmeddelande
anger knappt3,6mdkr efter återföring av Ostlänkenavsättning. Det tidigare preliminära
resultatet215mnkr är överspelat och används inte som utfall.

Ettårs-MAE, mnkr    PKV-accounting   Oförändrat resultat   Historiskt medel
Vadstena                  4,26                  13,77              12,34
Mjölby                   46,01                  54,17              68,46
Norrköping (2 målår)    1942,71                1680,50             727,62

Norrköpings engångskostnad för Ostlänken2022 följer med som återkommande kostnad
i den frysta regeln. Det är ett strukturellt prognosfel. Kommunen eller posten har
inte tagits bort efteråt. Den samlade prövningen ger inte stöd för generell automatisk
resultatprognos. Bättre resultat i två kommuner är inte ett nytt oberoende urval.

Huvudmåttet är absolutfel som procentenheter av öppningsårets skatt+generella bidrag,
med lika vikt för varje kommun. Rapporten visar även alla horisonter, bias, RMSE,
målårsvisa jämförelser och känslighet när ett målår utelämnas. Ofullständiga jämförelser
märks som preliminära. Gemensamma målår är gemensamma makrochocker.

data/external-pkv-ledgers.json redovisar kommun-/koncernavgränsning, sidnummer,
omklassificeringar, senare jämförelsekolumner och källprecision. Bokföringsidentiteter
får endast avvika inom möjlig avrundning; större oförklarade fel stoppar körningen.
Detta är ett retrospektivt test och inte en prognos med fullständigt verifierade
historiska informationsdatum. För självständig återkörning av ett arkiv:
python3 <arkiv>/sources/run_external_pkv.py --out <ny-katalog>

Snabbstart M1: statistiskt prognosförsök (kör från denna katalog)
---------------------------------------------------------------
python3 -m motala_lab run --forecast-date 2026-10-13

Kommandot skattar M1, gör kronologiska historiska jämförelser, kör M1:s
Modelicamodellen med OpenModelica och skapar runs/<körnings-id>/report.html.
Öppna HTML-filen lokalt. CSV och JSON ligger bredvid rapporten. Ingen webbserver
eller publicering behövs. Den befintliga webbplatsen är inte uppdaterad till M1.

Python 3 och NumPy krävs. OpenModelica söks i PATH eller via OMC. Den befintliga
lokala installationen upptäcks också. Node används för den frysta referensen.
--skip-native skapar en tydligt märkt, EJ native-verifierad rapport.

Vad som finns nu
----------------
M0: reference/m0 innehåller en oföränderlig kopia av tidigare Modelica,
JavaScript och basdata. Alla filer har SHA256. Motala.mo är fortsatt tillgänglig.

M1: MotalaResearch är en separat Modelica-modell med läsbara delmodeller:

  Clock ----> Demography ----> FiscalLedger ----> Financing
                befolkning       resultat            skuld/kassa
                                     ^                    ^
                                     |                    |
                              egna prognosbanor       Capital
                                                   tillgångar/avskrivningar

  Demography: överlevnad, åldrande, födslar och dämpade migrationsresidualer.
  FiscalLedger: skatter + bidrag - nettokostnad + finansnetto = resultat.
  Capital: investeringar, avskrivningar och tillgångsbalans.
  Financing: resultat till kassaflöde, upplåning, amortering och kassa.

Alla belopp är nominella mnkr. Nettokostnaden i M1 INKLUDERAR avskrivningar.
Avskrivning ska därför inte dras av en gång till vid resultatberäkningen.
Finansieringen är fortfarande ett scenario, med schabloner för avskrivningar,
investeringarnas genomförande och pensionsutbetalningar. Den är inte en
validerad prognos av faktiska kassaflöden. Finansnettot prognostiseras statistiskt;
modellen skattar ännu inte hur ändrad skuld påverkar räntan i ett politiskt scenario.

För att öppna en konkret körning i OMEdit: ladda MotalaResearch/package.mo och
sedan runs/<id>/native/Scenario.mo. Simulera Scenario från 0 till dess horizon.
I terminalen kan OMC=/absolut/sökväg/till/omc anges. Klockan räknar modellår.
Python skattar de ekonomiska banorna per invånare; Modelica räknar själv ut
befolkningen, totalbeloppen och balanserna. Detta är en hybridmodell.

Skattning och ärliga jämförelser
-------------------------------
M1 anpassas ENBART till år som föregår prognosmålet. Även val av dämpning och
regularisering görs inne i det tidigare träningsfönstret. Inga SKR-prognoser
läses av modellen. SKR jämförs separat med benchmark/compare.py.

Första ekonomiska modellen är en linjär kommunpanel med ridge-regularisering
på förändringen i belopp per invånare. Förklaringar: senaste nivå, senaste
förändring, befolkningstillväxt, andel barn 0-18 och andel 65+. Kommunvisa
effekter regulariseras mot gemensamma samband. Skalning skattas bara på
träningsdata; varje kommun får samma sammanlagda träningsvikt. Saknas åldersdata
utelämnas motsvarande förklaringsvariabler från den skattningen; de fylls inte med noll. Möjliga
regulariseringsnivåer är 0.1, 1, 10 och 100. Val görs med tidigare kalenderår.

Panelen aktiveras först med minst fem kommuner och 40 träningsövergångar samt
minst ett giltigt inre valideringsår. Vårt faktiska underlag når INTE detta.
Då används senaste nivå per invånare eller dämpad trend. Trendval kräver minst
fem lokala observationsår och minst två inre valideringsfall. Utan underlag
används senaste nivå per invånare. Trendfaktorn är förutbestämd till 0.5 per år.

Demografins residualer multipliceras med damping^prognossteg. Kandidaterna
0, 0.5 och 1 väljs i tidigare lokala år; utan inre validering används 1.
Kalibreringen använder tillgängliga sammanhängande årspar bland de tre senaste
åren. Äldre luckor i åldersdata stänger inte av en användbar nyare kohortserie.
Saknas användbara årspar används befolkningspersistens även i det inre
valideringssteget, så att metodvalet prövar samma beteende som prognosen.
Deltesterna no_demographic_damping och no_panel visar effekten av mekanismerna.
M0:s demografi jämförs också direkt. Historisk ekonomisk M0 körs inte när
bruttobokslut saknas; framtida basdata får inte fylla luckorna bakåt i tiden.

Rapporten redovisar resultat och komponenter var för sig. Även förluster visas.
Kandidaten ersätter inte automatiskt M0. Arbetsmålet är minst 10 procent lägre
resultat-MAE än bästa enkla alternativ, men detta är inget löfte om precision.
Första rapportens historiska resultat är utvecklingsevidens, inte ett blindtest.

Faktiska data och begränsningar
------------------------------
Default är Motala 2018-2025: fem redan befintliga år från årsredovisning 2025,
samt 2018-2020 ur årsredovisning 2022, lästa via webbverktyget. För 2018 används
enbart bokslut och totalt invånarantal; saknade åldersuppgifter fylls inte i.
Tillägget med
källor och konflikter finns i data/history-supplement.json. Original-PDF:en
är inte nedladdad. Åldersgrupperna är fortsatt 0-6, 7-15, 16-18, 19-64, 65+.

Historiska skatter + bidrag rekonstrueras som resultat + nettokostnad - finansnetto.
Det är inte en separat verifierad skatte- och bidragsserie och kan innehålla
avrundningsrester. I basåret blir summan 3318 mnkr, jämfört med 3317 i M0:s
separata avrundade intäktsposter. Skillnaden sparas i resultatfilen.

Rapporterna är publicerade i efterhand och är inte bevarade dataversioner för
historiska prognosdatum. Okända ursprungliga publiceringsdatum lämnas tomma.
Retrospektiva horisonter räknas från senast observerade år. En aktuell körning
med basår 2025 och prognosdatum 2026-10-13 börjar med 2026, alltså innevarande år.

Nya nätanrop till SCB misslyckas i arbetsmiljön 2026-10-23 vid DNS-uppslagning.
Det innebär inte att tidigare hämtade data saknas: SCB-arkivet ovan används
offline. Hämtningar och fel loggas i data/raw/receipts-*.json eller respektive
underkatalog. Ett misslyckat nytt försök ersätter inte ett lyckat äldre arkiv.

Hämta mer data
--------------
python3 -m motala_lab fetch

Insamlingen hämtar metadata och Motalas öppna kommunår samt SKR:s offentliga
prognosunderlag. Den kan köras i en nätverksansluten miljö. Rådata sparas med
SHA256. Definitioner och paginering måste granskas före normalisering; nuvarande
API-data får inte märkas som historiskt tillgängliga dataversioner.

För en större kommunpanel kan samma insamlingsfunktion acquire(directory,
sources) användas med explicita granskade URL:er. Skicka inte SKR-prognoser
som observationsdata. Varken makron eller kod från nedladdade arbetsböcker körs.

Normaliserade observationer har schemaVersion=1, scope=kommunen, moneyUnit=mnkr,
definitions, evidenceClass och rows. Visa ett fullständigt exempel:

python3 -m motala_lab observations

Varje rad har municipality (fyra siffror), year, population, taxAndGrants,
netCost (inklusive avskrivningar), financeNet, result, source, vintage,
retrievedAt och sourceRelease. Fem cohorts samt births/deaths är valfria,
men obligatoriska för kohortprojektion. Utan dessa används befolkningspersistens.
För explicit avrundningsavstämning kan accountingAdjustment anges.

CSV med granskad kolumnmappning kan importeras utan tredjepartsbibliotek:
python3 -m motala_lab.import_csv kommuner.csv mappning.json observationer.json
python3 -m motala_lab run --data observationer.json --forecast-date 2026-10-13

Mappningens format beskrivs i import_csv.py. Saknade värden, felaktig enhet,
dubbletter eller en obalanserad resultaträkning stoppar importen före skrivning.
Olika revisionsversioner väljs uttryckligen, aldrig genom att tyst skriva över.

För evidenceClass=archived_as_of krävs sourceRelease för alla rader och
explicit evaluationOrigins med municipality, forecastDate, informationCutoff.
Exempel: {municipality:0583, forecastDate:2023-10-01, informationCutoff:2023-09-30}.
Datum och kommunkod ska vara JSON-strängar. Endast uppgifter publicerade före
cutoff används. Ettårsprognosen avser då 2024, även om senast kända bokslut är 2022.

SKR och kommunprognoser som jämförelser
--------------------------------------
python3 benchmark/compare.py benchmark/observations.json --output benchmark/report.json

Tomt underlag ger ingen precision eller vinst. Jämföraren visar separata par mot
persistence, trend, reference, skr och municipal, samt en gemensam tabell för
candidate/skr/persistence/trend. Datum, informationsgräns, definition och enhet
måste stämma. Budget och uppdaterad helårsprognos får inte blandas i samma serie.
En intäktsjämförelse säger inte att hela budgetmodellen slagit SKR.

Testa och återköra
------------------
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m unittest discover -s benchmark -p 'test_*.py' -v
python3 validate.py

Tester av panelskattning använder SYNTETISKA data och är inte precisionsevidens.
Native-testet prövar också varierande investering, pensionskassabrygga och full
amortering. Körningarna fryser tillstånd efter horisonten och kontrollerar balanser.

Varje M1-run innehåller observationsdata, modellparametrar, prognosfel, Modelica,
kompilatorlogg och källkodssnapshot. Samma kommando återanvänder endast ett arkiv
vars filhashar verifieras. Ändrade arkiv eller ofullständiga körningar skrivs
inte över. För en oberoende återkörning från den frysta koden, använd:

PYTHONPATH=runs/<id>/source python3 -m motala_lab run \
  --data runs/<id>/observations.json --forecast-date 2026-10-13 \
  --output /tmp/motala-reproduction

Kör detta från en annan arbetskatalog med absoluta sökvägar för att välja den
frysta modulen i stället för den aktiva. Rapporten visar inget prognosintervall:
underlaget räcker ännu inte för att kalibrera trovärdig sannolikhetstäckning.

Nästa datadrivna steg
--------------------
1. Utred återstående käll- och redovisningsskillnader mellan den nu importerade
   SCB-serien och årsredovisningarna. Budgetreaktionsförsöket är kört enligt låst
   protokoll; matchad jämförelse med frysta M2 behövs före eventuell promotion.
2. Observerade verksamhetskostnader och volymer, först i en avgränsad verksamhet
   som skolan, för att pröva kostnadsanpassning mot faktiska utfall.
3. Finare åldrar, lokalt skatteunderlag, pensionsbetalningar, investeringstider
   och låneportfölj, med tydliga definitioner och källor.
4. En kommunpanel som kompletterande kontroll av överförbarhet. Den ersätter
   inte Motala-prövningen och är inget villkor för den egna budgetreaktionen.

M2 implementerar flera av mekanismerna som explicita scenarioantaganden.
Empirisk skattning och historisk prognosutvärdering återstår; fler parametrar
innebär inte i sig bättre precision.
