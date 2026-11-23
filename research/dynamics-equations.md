# Motala Dynamics: ekvationer och parameterkontrakt

Version 3, 15 oktober 2026. Detta är en mekanismbaserad scenariomodell för
kommunens egna verksamheter. Den kompletterar den äldre årliga scenariomodellen
och M1:s statistiska prognosförsök. Ekvationerna nedan implementeras i
`research/MotalaDynamics`; de utländska studierna bestämmer inga Motala-parametrar.

## Forskningsgrund och val av samband

| Underlag och granskning | Vad vi använder | Avgränsning |
| --- | --- | --- |
| [Calgary, kommunal systemdynamik](https://www.calgary.ca/content/dam/www/cfod/finance/documents/corporate-economics/other-reports/regional-economic-growth-and-municipal-financial-planning.pdf), särskilt tryckta s. 16–18 | Bestånd, kapacitetsmål, investeringar och fördröjd anpassning; skuld och ränta återkopplas. | Calgarys fastighetsskatt och automatiskt balanserande skattesats överförs inte. |
| [Starke (2021)](https://doi.org/10.1007/s41358-021-00269-0), sammanfattning och modell-/resultatbeskrivning | Befolkningsminskning behöver inte ge proportionell kostnadsminskning. | Tyska kommuner och observationssamband; ingen skattad svensk anpassningstid. |
| [Lais och Penker (2012)](https://lex-localis.org/index.php/LexLocalis/article/view/204), förlagets sammanfattning | Österrikisk evidens för kvarstående infrastrukturkostnader vid krympning. | Fulltext kräver prenumeration; endast sammanfattningen granskad. |
| [Cohen, Karatzimas och Naoum (2017)](https://doi.org/10.1108/JAAR-03-2015-0019), indexerad förlagssammanfattning | Grekiska kommuners administrativa kostnader kan anpassas snabbare nedåt än uppåt. | Motiverar fria, separata tidskonstanter; stöder ingen universell regel om långsam neddragning. |
| [Bradbury och Scott (2018)](https://doi.org/10.1177/0312896218773136), förlagets sammanfattning | Kommunal kostnadsasymmetri kan behöva beaktas även i planeringen. | Nya Zeeland; ingen koefficient överförs. |
| [Fabre och Borgert (2022)](https://www.scielo.br/j/rbgn/a/GNhYJMvBknmsn3Fk4Ltvrgq/?lang=en), avsnitt 1–3 och slutsatser | Olika kostnadsslag kan ha olika anpassningsmönster. | Brasiliansk redovisning skiljer sig; samband mellan intäkter och utgifter bevisar inte kausal efterfrågeanpassning. |
| [KI, mars 2024](https://www.konj.se/media/3eojy3lo/konjunkturlaget-mars-2024.pdf), s. 44/78 | Separera åldersrelaterade volymer, bemanning och priser. | De tre verksamhetsaggregaten nedan kräver lokala nyttjandevikter. |
| [Eurostats befolkningsmetod](https://ec.europa.eu/eurostat/en/web/population-demography/population-projections/methodology) | Kohortbalans med födslar, dödsfall och migration. | Vår kontinuerliga femgruppsapproximation är inte Eurostats detaljerade kohortmodell. |
| [RKR R4](https://www.rkr.se/wp-content/uploads/2023/06/RKR-R4-Materiella-anlaggningstillgangar.pdf), avskrivningsavsnittet | Skilj investering under byggnad från tillgång i bruk. | Den aggregerade avskrivningsfunktionen här ersätter inte kommunens komponentregister. |

Ekvationernas specifika funktioner är våra modelleringsval. Källorna motiverar
mekanismer och prövbara hypoteser, inte att just dessa ekvationer är empiriskt
identifierade för Motala. Migration som följd av servicekvalitet, produktivitet
som följd av nedskärningar och skattebas som följd av lokal investering saknar
ännu identifierade samband och ingår inte som automatiska återkopplingar.

## Tid, enheter och variabelroller

I grundscenariot är t antal år efter 31 december 2025; historiska körningar
anger sitt eget startår. Pengar anges i nominella
mnkr; resultat, kostnader och investeringsutgifter är flöden i mnkr/år.
Modelica använder sekunder internt: `yearSeconds=31557600` och
`der(x)=årsflöde/yearSeconds`. Årsrapporten anger kalenderår och förflutna
modellår; den råa native-filens `time` är fortfarande i sekunder.

| Roll | Exempel | Modelica |
| --- | --- | --- |
| Konstant antagande eller kalibrering | Anpassningstid, livslängd, kostnadsandel, initialt bestånd | `parameter` |
| Beslut/omvärldsbana under körning | Bemanningsmål, investeringsram, marknadsränta, pensionsbetalning | `input` med en förvald bindning |
| Tillstånd | Befolkning, personal, byggprojekt, kapacitet, bokvärde, skuld, kassa | Kontinuerlig variabel med `der(...)` |
| Härledd storhet | Levererad service, kostnad, resultat, underskott | Algebraisk ekvation |

`input` kan bindas till en konstant parameter eller ett tidsberoende uttryck i
en Scenario-modell. En ändring av ett bemanningsmål ändrar det önskade beståndet;
den hoppar inte omedelbart över till faktisk bemanning. Ingen parameter behöver
vara skattad för att simulering ska vara möjlig; dess antagandestatus måste vara
synlig. Alla räntor och tillväxttal anges som andelar, exempelvis 0,03 för 3 %.

Simulera `Examples.Base` eller ett annat scenario som innehåller `Continuous`.
Då blir de förvalda input-bindningarna ekvationer inne i komponenten. Att
simulera `Continuous` direkt kan lämna toppnivåindata åt simulatorns externa
indatahantering. Testet av basbokslutet kontrollerar därför även dessa bindningar.

Exempel på parameterändring i Modelica:

```modelica
model MittScenario
  extends MotalaDynamics.Examples.SchoolDecline(
    plant(reductionYears={0.5,3,3}, closureYears={8,8,8}));
end MittScenario;
```

Samma konstanta ändring kan anges i körskriptets JSON-fil. `reductionYears` är
en parameter; den faktiska personalstyrkan är fortfarande ett dynamiskt tillstånd.

## 1. Befolkning: bevarandelag

För fem åldersgrupper N_a med åldrandehastighet gamma_a och dödlighet mu_a:

\[
\dot N_1=B-(\gamma_1+\mu_1)N_1+M_1,\qquad
\dot N_a=\gamma_{a-1}N_{a-1}-(\gamma_a+\mu_a)N_a+M_a.
\]

Gamma är `{1/7,1/9,1/3,1/46,0}`. Födslar är
`B=births0*(N_4/N_4,0)*fertilityMultiplier`. Därmed gäller exakt
`d(sum(N))/dt = B - sum(mu_a*N_a) + sum(M_a)`.
Åldrande lämnar inte den öppna gruppen 65+. Födelsernas exponering genom hela
19–64-gruppen är en approximation; kön och ettårsåldrar behövs för en full modell.
Första ordningens åldrande ger spridda uppehållstider inom breda grupper och
ska inte tolkas som exakt övergång vid födelsedagar.

Initial befolkning och födslar hämtas från projektets bokslutsunderlag. Standard-
migrationen fördelar 2025 års observerade totala nettomigration över antagna
åldersvikter. Den återanvänder inte M0:s diskreta residualer som kontinuerliga
flöden. Negativa kohorter avbryter ett scenario; de klipps inte tyst till noll.

## 2. Efterfrågan och personal

För verksamhet i: `Q_i=m_i*sum_a(w_ia*N_a)`. Standardvikterna summerar barn
0–18 för utbildning, 65+ för omsorg och alla invånare för övrigt. Enheterna är
demografiska serviceekvivalenter per år, **inte observerade elever eller brukare**.
Vikterna och efterfrågefaktorn m kan ersättas med deltagandegrad och vårdintensitet.

Med produktivitetsindex z, personalbehov h per serviceenhet och bemanningsmål u:

\[
H_i^*=\max(H_i^{min},h_i u_iQ_i/z),\quad
\dot H_i=\frac{[H_i^*-H_i]_+}{\tau_i^+}
             -\frac{[H_i-H_i^*]_+}{\tau_i^-}.
\]

Detta är nettoutökning respektive nettominskning av årsarbetare, inte brutto-
rekrytering inklusive ersättning av avgångar. Båda tidskonstanterna är fria.
Vid konstant mål fås `H(t)=H*+(H(0)-H*)exp(-t/tau)` på respektive sida om målet.
Det härleder den gradvisa anpassningen och ger ett oberoende analytiskt test.

När `limitStaffChanges=true` begränsas respektive flöde dessutom av
`maxStaffIncrease_i` och `maxStaffDecrease_i`, mätt i årsarbetare/år:
`dot H = min(högstaÖkning,[H*-H]+/tau+) - min(högstaMinskning,[H-H*]+/tau-)`.
Ett bindande tak ger först linjär förändring och sedan exponentiell anpassning.
Taken gäller nettoförändring, inte bruttoanställningar inklusive ersättning av
avgångar. Standardtaken när funktionen aktiveras är antagna till 10 procent av
initial bemanning per år. [SKR:s personalprognos](https://skr.se/personalochkompetensforsorjning/skrspersonalprognos.8994.html)
motiverar att hålla behov och personaltillgång isär; den skattar inte dessa tak.

Personalkapaciteten är `Q_H=H*z/h`. Lägre u sänker önskad bemanning men höjer
inte produktiviteten. Fördubblad produktivitet är ett uttryckligt scenarioantagande.

## 3. Fysisk kapacitet och byggfördröjning

K är färdig servicekapacitet, U kapacitet under byggnad, W betalda byggutgifter
under uppförande, I investeringsutgift och c pris per ny kapacitetsenhet:

\[
\dot U=I/c-U/\tau_b,\quad \dot W=I-W/\tau_b,\quad
J_U=U/\tau_b,\quad J_W=W/\tau_b.
\]

U och W hålls separat så att en senare prisändring inte skriver om hur mycket
fysisk kapacitet redan beställda projekt ska ge. Fysisk förslitning är
`V=K/L_physical`. Önskad kapacitet `K*=capacityTarget*Q`. Om avveckling tillåts
är `X=[K-K*]_+/tauClose`, annars X=0. Då är `dot K=J_U-V-X`.
Ett större kapacitetsmål innebär ett uttryckligt beslut om reservkapacitet.

Med automatisk investeringsplanering:

\[
I^{önskad}=c\,[V+(K^*-K-U)/\tau_{plan}]_+,\qquad
I=\min(I^{ram},I^{önskad}).
\]

Byggprojekt räknas av innan nya beställs. Utan automatisk planering är I den
angivna investeringsbanan. Ramen är ett beslut, inte ett påstått kreditutrymme.
Första ordningens byggfördröjning sprider färdigställandet över tiden; ett exakt
driftsättningsdatum skulle kräva en projekt-/vintagemodell.

V2 använder ett observerat ingående W på **99 mnkr**, från kommunens bokslut
2025, s. 48 och not 12 på s. 53. Tillgångar i bruk på 2 997 mnkr omfattar inte
denna post. Verksamhetsfördelningen är fortfarande antagen, och initialt U
beräknas som W/c. Detta är en kapacitetsapproximation, inte en projektinventering.

## 4. Leverans, köpt service och otillgodosett behov

\[
Q^{egen}=\min(Q,Q_H,K),\quad
Q^{köpt}=v\,[Q-Q^{egen}]_+,\quad
Q^{saknas}=Q-Q^{egen}-Q^{köpt},\quad 0\le v\le1.
\]

Outsourcingandelen v är ett scenario. Köpt service antas tillgänglig till angivet
pris. När `limitExternalService=true` gäller i stället
`Q_köpt=min(externalServiceCapacity,v*[Q-Q_egen]+)`; kapaciteten är ett indataflöde
som kan ges en tidsbana. Standardvärdet när taket aktiveras är antagna 5 procent
av initial efterfrågan. Modellen visar bristens storlek
och beskriver inte automatiskt effekter på kvalitet, utbildningsresultat eller hälsa.

## 5. Kostnader: personal, lokaler, fasta och rörliga delar

Låt p vara prisindex, l löneindex, s_i andel av övrig drift och O_0 övrig driftkostnad:

\[
C_H=\sum_i l\,w_i^H H_i,
\]
\[
C_O=\sum_i p\,O_0s_i\left(f_i+k_i K_i/K_{i0}
 +(1-f_i-k_i)Q_i^{egen}/Q_{i0}\right)
 +\sum_i p\,c_i^{köpt}Q_i^{köpt}.
\]

`f_i+k_i<=1`. f är en kvarstående administrativ kostnadsandel; k knyter drift
till fysisk kapacitet. Ingen av dem multipliceras dessutom med en extra
"tröghetsfaktor". Personalkostnaden följer H, även vid underutnyttjande.
`payrollShares`, `otherExpenseShares`, `operatingRevenueShares`, `assetShares`
och `investmentShares` är separata fördelningar och summerar var och en till ett.
Äldre `sectorShares` är deras gemensamma förval tills separata uppgifter anges.
Driftintäkter har egen prisbana och skalar med levererad service per sektor.
Deras basfördelning är antagen eftersom avgifter, försäljning och bidrag ännu
inte har separerats. Pensionskostnad och pensionsbetalning är oberoende indata.
Prisindex följer `dot p=log(1+g_p)*p`, vilket ger exakt faktor 1+g_p efter ett år.

### Årsbelopp och öppningsflöde

Ett bokslutsbelopp är en integral över det föregående året. Det är inte samma
sak som det momentana flödet vid årets slut. För `k=log(1+g)` och ett föregående
årsbelopp `B` antar vi en exponentiell pris-/värdebana och härleder

```text
F(t) = F(0)*exp(k*t)
B = integral från -1 till 0 av F(t) dt = F(0)*(1-exp(-k))/k
F(0) = B * (1+g)*log(1+g)/g
integral från 0 till 1 av F(t) dt = B*(1+g)
```

Det gäller exakt när kvantiteten hålls konstant. Förändrade personalbestånd,
servicevolymer och skatteexponering påverkar sedan respektive flöde separat.
Gränsvärdet vid `g=0` är 1; nära noll används en Taylorutveckling.
`annualFlowAnchoring=true` är förvalet och gäller löner, övriga priser,
skattebas, bidrag, driftintäkter och pensionskostnader. Produktiviteten börjar
på 1 eftersom den anger en kapacitetsnivå. Investering och externa
intäktsbindningar anges direkt som annualiserade momentana flöden. Avskrivning
och ränta beräknas fortfarande från bestånd; deras öppningskalibrering till
föregående års belopp är en separat approximation.

`annualFlowAnchoring=false` behåller v2:s äldre konvention där öppningsflödet
likställdes med föregående årsbelopp. Den frysta v2-källan finns i
`research/reference/dynamics-v2`. Ett analytiskt native-test kontrollerar
integrerade årstotaler för positiv, negativ, noll och nästan noll tillväxt.

Omställning kan ha en engångskostnad per minskad årsarbetare eller avvecklad
kapacitetsenhet: `C_omst = l*sum(staffReductionCost*staffDecrease)
+ p*sum(capacityClosureCost*closure)`. Kostnaden belastar både resultat och
kassaflöde när omställningen sker; bokförd avvecklingsförlust hanteras separat.
Noll är ett uttryckligt antagande om kostnadsfri omställning, inte ett observerat
värde. Personalparametern är en effektiv genomsnittskostnad för nettominskningen
och ska ta hänsyn till hur stor del som sker genom naturliga avgångar.

## 6. Tillgångar, avskrivning och avvecklingsförlust

För varje sektor är A bokvärdet för tillgångar i bruk:

\[
D_A=A/L_{accounting},\quad
F_X=\begin{cases}A X/K&K>0\\0&K=0\end{cases},\quad
\dot A=J_W-D_A-F_X.
\]

Under byggnad sker ingen avskrivning. Avveckling utan försäljningsintäkt tar bort
ett proportionellt bokvärde, vilket belastar resultatet men inte kassaflödet.
Normal fysisk förslitning antas avse uttjänta, fullt avskrivna enheter; den ger
ingen ytterligare avvecklingsförlust. Blandad ålder och återstående bokvärde
gör detta till en aggregerad proxy. Exponentiell avskrivning och genomsnittligt
bokvärde ska senare ersättas med komponenter/vintager där data medger det.
Fysisk livslängd och bokföringsmässig livslängd är skilda parametrar.

## 7. Skatteintäkter och bidrag

Exponering `Z=sum(incomeWeights_a*N_a)` och folkmängd N får varsin
fördröjd storhet: `dot Z_lag=(Z-Z_lag)/tauTax`, motsvarande för N.
Med skattebasindex b och bidragsindex g:

\[
T_{std}=T_0 b Z_{lag}/Z_0,\quad
T=T_{std}(taxRate/taxRate_0),
\]
\[
G=G_0 g N_{lag}/N_0
 -e\,(T_{std}-T_0bN_{lag}/N_0).
\]

Äldres skattepliktiga inkomster representeras av en separat inkomstvikt.
Utjämningskänsligheten e är en schablon. Den kompenserar inte en egen
skattesatsändring. Fördröjningen är inte den lagstadgade novemberavstämningen.
Detta ersätter **inte** SKR:s regelverk för skatter, utjämning och avräkningar.
Alternativt kan explicit externa skatte-/bidragsbanor användas; en sådan körning
ska märkas som beroende av externt underlag och kan inte jämföras med samma
SKR-bana som en oberoende intäktsprognos.

`useExternalRevenue=true` ersätter både T och G. Med enbart
`useExternalTax=true` ersätts T med
`externalTax*(taxRate/taxRate0)+externalTaxSettlement`, medan
G fortfarande beräknas med samma interna `T_std`, b och g som ovan.
Det gör en isolerad skatteanalys möjlig utan att samtidigt ändra bidragen.
Den interna utjämningen är då ett oförändrat jämförelseantagande, inte en
regelriktig reaktion på den externa skattebanan.

`externalTaxSettlement` är en separat, signerad avräkning i mnkr/år och
är noll som förval. När den anges ska `externalTax` bara innehålla den
skatt som ska multipliceras med egen skattesats; avräkningen får inte
också ingå där. Tidigare körningar har avräkningen inbakad i sin
schablon och behåller noll för den nya separata indatan.

I den låsta historiska känsligheten `historical-protocol-tax.json` anges
`externalTax_h=T_0*produkt(1+SKR_skatt_i/100)` årsvis. Detta antar konstant
lokal andel av rikets nominella skatteunderlag. Rikets tillväxt innehåller redan
dess demografi, så någon ytterligare lokal befolkningsfaktor används inte i
denna skattebana. Öppningsskattens slutavräkningar och regeländringars
kompensation genom statsbidrag är kvarvarande begränsningar. Kostnader och
bidrag behåller sina tidigare antaganden; kassaflöde och ränta kan påverkas.

SKR tillhandahåller både [skatteunderlagsprognoser och modellverktyg](https://skr.se/ekonomiochbudgetplanering/skatteunderlagsprognoserochmodellverktyg.8271.html)
och [stöd för resursfördelning och demografiska budgetberäkningar](https://skr.se/ekonomiochbudgetplanering/resursfordelningochanalysstod.8273.html).
Det går därför inte att beskriva SKR:s hela erbjudande som enbart en skatteprognos.
M2:s bidrag här är att personal-, kapacitets- och finansieringsförlopp redovisas
som explicita tillstånd och fördröjningar. En jämförelse av prognosprecision
kräver samma utfallsdefinition, informationsdatum och prognoshorisont; någon
sådan ny historisk jämförelse har inte gjorts för M2.

### 7.1 Härledd intäktsbrygga inför nästa historiska prövning

Detta avsnitt är specifikationen för nästa intäktsmodell. Den fullständiga
regelbryggan är ännu inte inkopplad i `Continuous.mo` och har inte fått
någon prognospoäng. Separat avräkning och skattefordran är implementerade
som indata respektive tillstånd; de väljer inga prognosantaganden. De tidigare
frysta prövningarna behåller schablonen ovan. Underlaget finns i
`research/data/motala-revenue-components.json` och
`research/data/skr-revenue-vintages.json`. Ingen koefficient nedan har valts
för att minska de observerade prognosfelen.

Låt y beteckna räkenskapsår och v prognosens informationsdatum. N_{i,y-1}
är Motalas folkmängd **1 november föregående år**. B^G_{i,y} är det lokala
skatteunderlaget, i miljoner kronor beskattningsbar inkomst, uppräknat med
regeringens fastställda faktorer. Det är inte bokförd skatteintäkt dividerad
med skattesatsen: bokförd intäkt innehåller också kollektiv avräkning.
K^G_y är motsvarande fastställda medelskattekraft i riket, i kronor per
invånare. De olika enheterna kräver faktorn 10^-6 nedan.

Med kommunens egen skattesats tau_i, aktuell avräkningsprognos s_{y|v}
i kronor per invånare och revision d_{y-1|v} av föregående års avräkning:

\[
T^{prel}_{i,y}=\tau_{i,y}B^G_{i,y},\qquad
T^{bok}_{i,y|v}=T^{prel}_{i,y}
 +10^{-6}s_{y|v}N_{i,y-1}
 +10^{-6}d_{y-1|v}N_{i,y-2}.
\]

Avräkningen är kollektiv och fördelas med ett gemensamt belopp per
invånare. En ändrad lokal skattesats multiplicerar därför den preliminära
skatten, inte automatiskt avräkningarna. Den historiska revisionsposten
är inte en återkommande tillväxtkomponent. Framtida revisioner kräver ett
eget prognosantagande; att sätta deras förväntade värde till noll är ett
antagande, inte observerade nollor. SKR:s fem decembercirkulär anger
avräkning för öppningsåret och året därefter. Senare år lämnas `null` i
källsamlingen. De explicit angivna avräkningsbeloppen ska användas, inte
rekonstrueras som skillnaden mellan tabellens två medelskattekraftsserier.
[SKR 21:49, s. 10](https://insynsverige.se/documentHandler.ashx?did=2017024),
[SKR 23:56, s. 23](https://extra.skr.se/download/18.40b25ebf18c6245376516b5b/1702628339915/Cirkul%C3%A4r%2023056.pdf).

Inkomstutjämningens underlag och belopp är:

\[
U_{i,y}=10^{-6}\gamma K^G_yN_{i,y-1}-B^G_{i,y},\qquad
I_{i,y}=\begin{cases}
\tau^+_{l,y}U_{i,y},&U_{i,y}\ge0,\\
\tau^-_{l,y}U_{i,y},&U_{i,y}<0.
\end{cases}
\]

Garantinivån gamma är 1,15. De länsvisa bidrags- och avgiftssatserna
tau_l är separata administrativa parametrar. De ska inte ersättas med
95 procent av Motalas egen skattesats. Detta skiljer en lokal skattesatsändring
från en ändring av själva skatteunderlaget. Formeln avser utjämningssystemets
inkomstkomponent, inte kostnadsutjämning, LSS eller fastighetsavgift.
[SCB:s beskrivning för utjämningsåret 2023, s. 3–5](https://www.scb.se/contentassets/d93ddb5be2504691ba3912701fc1e32a/beskrivning-av-kommunalekonomisk-utjamning-2023_utfall.pdf).

För kommunernas regleringspost r_{y|v}, i kronor per invånare:

\[
G^{reg}_{i,y|v}=10^{-6}r_{y|v}N_{i,y-1},\qquad
G_{i,y}=I_{i,y}+G^{kost}_{i,y}+G^{reg}_{i,y}
 +G^{struktur}_{i,y}+G^{inforande}_{i,y}
 +G^{LSS}_{i,y}+G^{fastighet}_{i,y}+G^{ovrigt}_{i,y}.
\]

Varje post ska finnas separat i avstämningen. Fastighetsavgift och övriga
bidrag har inte automatiskt samma befolknings- eller prisuppräkning.
SKR:s tabeller för kommuner ska hållas skilda från regionernas tabeller
och från rikets totaler i mnkr. Tabellens novemberbefolkning i kolumn y
avser november år y; den kan därför inte direkt multipliceras med
regleringsbeloppet för räkenskapsår y i samma kolumn.
[SKR 24:56, tabell 9 och 16](https://extra.skr.se/download/18.72fac55919386070c95830a7/1733995400288/Cirkul%C3%A4r%2024056.pdf).

En möjlig, uttrycklig prognosrestriktion är konstant relativ lokal
skattekraft q_{i,y} = 10^6 B^G_{i,y}/(K^G_y N_{i,y-1}). För oförändrad garantinivå,
länsskattesats och q_i kan inkomstutjämningen från öppningsår o skrivas:

\[
\widehat I_{i,y|v}=I_{i,o}
 \frac{\widehat K_{y|v}}{K^G_o}
 \frac{\widehat N_{i,y-1|v}}{N_{i,o-1}},\qquad
\widehat B_{i,y|v}=B^G_{i,o}
 \frac{\widehat K_{y|v}}{K^G_o}
 \frac{\widehat N_{i,y-1|v}}{N_{i,o-1}}.
\]

Det är en algebraisk följd av restriktionen, inte en skattad elasticitet.
Den förutsätter att samma skattebasantagande används i både preliminär
skatt och inkomstutjämning. Konstant lokal andel av rikets totala skattebas
är ett annat antagande när den relativa befolkningen ändras och ska inte
blandas in i samma brygga. Fastställda värden används där de finns;
för senare år måste valet av prognostiserad medelskattekraft och dess
övergång till framtida administrativa underlag låsas före prövningen.
Kostnadsutjämning och LSS kräver fortfarande separata underlag eller
tydligt redovisade scenarier. Den här restriktionen är ännu inte vald som
en godkänd fullständig prognosregel.

2020 års tillfälliga generella bidrag 82,1 mnkr finns i både not 7 och
not 10. När bidrag byggs upp komponentvis ska notjusteringen tillämpas
på den identifierade posten en gång. Ett generellt avdrag från en redan
rensad totalsumma skulle dubbelräkna bortfallet. Samma princip gäller
omklassificeringar mellan verksamhetsintäkter och generella bidrag:
bevara rapporterade utfall och redovisa jämförbarhet separat.

Motalas separat redovisade flyktingbaserade välfärdsbidrag var 11,2 mnkr
2020. Den återstående äldre välfärdssatsningen ingår från 2021 i
regleringsposten. En framtida komponentprognos får därför inte fortsätta
2020 års separata bidrag ovanpå den nya regleringsposten. Detta är en
kategoriövergång, inte ett antagande om att samma lokala belopp tillkommer
i regleringen. Nollorna i den normaliserade flyktingkolumnen efter 2020
betyder att posten inte redovisas separat; de är inte avlästa nollceller
i varje årsredovisning.
[SKR 20:57, s. 10](https://meetingsplus.gavle.se/welcome-sv/namnder-styrelser/kommunstyrelsen/mote-2021-02-09/agenda/cirkular-2057-fran-skr-budgetforutsattningar-for-aren-2020-2023pdf?downloadMode=open).

Beräkningsreglerna är årsvisa algebraiska samband. Befolkning och lokalt
skatteunderlag kan komma från dynamiska delmodeller, men en glidande
fördröjning ersätter inte referensdatumet 1 november. Stegvisa årsbelopp
kan bindas som annualiserade flöden till Modelica och integreras som
övriga intäkter. Kassaflödet behöver en ytterligare periodisering:

\[
\dot Q_T=T^{bok}-T^{betald},\qquad
OCF=R+D_A+F_X+E_p-P_p+E_x-P_x-\dot Q_T.
\]

Q_T är en nettoskattefordran, alltså en tillgång med positivt tecken i
balansidentiteten. Dess öppningsvärde och betalningsplan måste vara
avstämda. En avräkning kan påverka resultatet före betalningen; den
uppgiften får inte användas för att samtidigt förbättra historisk
likviditet utan ett motsvarande fordringssaldo. Modelica-tillståndet
`taxReceivable` och indatan `taxPayments` implementerar nu denna brygga,
inklusive `+Q_T` i balansidentiteten och dess native-kontroll. Förvalen
`taxReceivable0=0` och `taxPayments=tax` är uttryckliga antaganden, inte
avlästa historiska saldon eller betalningsplaner. Resultatvalideringen
validerar därför inte kassaflödet för skatteavräkningar. Ett negativt
saldo betecknar en nettoskatteskuld.

SCB:s novemberbefolkning och administrativa Excel-underlag behövs för
nästa lokala avstämning. Filernas publicering och korrigeringar listas i
`research/data/revenue-source-downloads.json`; en engångshämtning finns i
`research/fetch_revenue_sources.py`. En senare korrigerad tabell kan
användas som tydligt märkt kontrollunderlag men blir inte därmed en
historiskt tillgänglig prognosversion.

### Normaliserad delprövning av preliminär skatt och inkomstutjämning

Protokollet `historical-protocol-normalized-revenue.json` prövar den gemensamma
skalningen av P och I utan att härleda saknad novemberbefolkning. Vid konstant
relativ skattekraft q, referensbefolkning N, egen skattesats tau, länssats lambda
och garanti gamma gäller `P=tau*q*K*N` och `I=lambda*(gamma-q)*K*N`. Därför:

```text
P_h = P_0 * k_h, I_h = I_0 * k_h
k_1 = K_government,1 / K_government,0
k_h = K_SKR,h / K_government,0, h=2,3
```

Övergången till SKR:s prognostiserade nivå är ett explicit antagande om framtida
administrativ skattekraft. Befolkningskvoten är satt till ett, inte observerad.
Ingen nivåjustering eller målkalibrering görs. Absolut N och faktisk q identifieras
inte av denna normalisering.

I varje jämförelse allokeras de tidigare totalprognoserna proportionellt:
`P_old=P_0*T_parent/T_0`, `I_old=I_0*G_parent/G_anchor`. G_anchor är öppningsbidraget
efter respektive notpolicy. Native-modellen byter dessa delar mot konstanta
årsflöden P_h och I_h. Resterande skatt och bidrag behåller exakt sina tidigare
funktioner; `referenceGrants` beräknas med den ursprungliga `referenceTax`.
Det finns ingen återkoppling från nya skatten till en andra utjämningsberäkning.
Egen skattesats hålls på referensnivån under denna historiska prövning.

Den ärvda återstoden är ingen korrekt separat prognos för avräkning, reglering
eller övriga bidrag. Modellen har också kvar sin demografi i kostnader och
återstående intäktsdelar. Detta är en avgränsad mekanismprövning, inte hela
regelmodellen ovan. Båda notpolicys, samtliga tidigare fall och WIP-alternativ
behålls. P, I, P+I och hela årsresultatet bedöms var för sig. Finansnettot får
reagera i native-modellen; dess förändring redovisas separat och påverkas även
av den ändrade fördelningen av intäkter inom året. Bokföringsjämförelsen håller
sitt finansnetto fast. Årsutfallen är redan använda utvecklingsdata.

### Separat prövning av daterad skatteavräkning

Protokollet `historical-protocol-settlements.json` behåller P/I från den
normaliserade prövningen och ersätter hela dess ärvda skatterest:

```text
S_1 = s_(o+1|v) * N_yearend,o / 1e6
S_2 = S_3 = 0
revision_h = 0
tax_h = P_h + S_h + revision_h
```

Här är o startåret, v samma daterade decembercirkulär som för kostnaderna och
s cirkulärets prognos för aktuell avräkning i kronor per invånare för o+1.
Motalas observerade årsslutsbefolkning används uttryckligen som proxy för
1 november samma startår. Den utges inte för att vara observerad novemberdata.
Nollorna är deklarerade förväntningar, inte utfall eller säkerhet; källornas
okända senare avräkningsvärden ligger kvar som null i den sparade vintagen.
Tidigare års revisionsbelopp i cirkuläret avser startårets redovisning och
flyttas inte till ett framtida år.

Avräkningen binds separat till `externalTaxSettlement`, med sitt tecken och
utan skalning med egen skattesats. Den gamla `inheritedTax` sätts till noll.
Bidrag, kostnader, demografi och parametrar för kapital och finansiering
behålls. Finansnettot får reagera på de ändrade intäkterna; motsvarande
bokföringskontroll håller det fast. Samma års betalning och noll öppningsfordran
är kvarvarande antaganden och ger ingen empirisk likviditetsvalidering.

Proxyns direkta känslighet är `deltaS_1=s*deltaN/1e6`. De låsta exemplen
±100 och ±1000 personer är hypotetiska avvikelser, inte uppmätta felgränser
eller konfidensintervall. De omfattar inte senare ränteeffekter.
Samma tolv fall, båda notpolicys och alla WIP-varianter behålls. Avräkning
inklusive revision, preliminär skatt, hela skatten och resultatet bedöms
separat, med bias, MAE, RMSE och utelämning av ett målår i taget. Detta är
fortsatt utveckling på redan granskade utfall, inte ett oberoende slutprov.

### Separat prövning av daterat regleringsbidrag

Protokollet `historical-protocol-regulation.json` bygger vidare på avräknings-
prövningen. Med samma decembervintage v och konstant lokal referensbefolkning:

```text
R_h = r_(o+h|v) * N_yearend,o / 1e6
F_h = 0
G_remaining(t) = (1 - (I_0 + R_0 + F_0)/G_anchor) * referenceGrants(t)
G(t) = I_h + R_h + G_remaining(t)
```

r är SKR:s signerade kommunala regleringsbelopp i kronor per invånare.
N_yearend,o är öppningsårets lokala årsslutsbefolkning och hålls konstant
för alla horisonter som proxy för 1 november året före respektive målår.
Detta är ett antagande, inte observerade framtida folkmängder.
G_anchor är bidraget efter respektive notpolicy. F_0 är 11,2 mnkr vid start2020
och noll vid övriga starter; den separata flykting-/välfärdskategorin övergår
till regleringen2021. Övergången innebär inte att samma lokala belopp läggs
till R_h. No-repeat-policyens borttagning av82,1 mnkr görs inte igen.

För bokföringskontrollen härleds de borttagna allokeringarna från v7:s
ärvda rest, aldrig från det nya totalbidraget:

```text
scale_h = inheritedGrants_v7,h / (G_anchor - I_0)
R_old,h = R_0 * scale_h
F_old,h = F_0 * scale_h
G_remaining,h = inheritedGrants_v7,h - R_old,h - F_old,h
```

Den positiva nämnaren kontrolleras. Native-modellen integrerar samma
allokeringar och den nya årsvisa regleringsbanan. Skatt, avräkning, I_h,
kostnader och demografi behålls; finansieringen får reagera på nytt bidrag.
Det jämförbara kategorimåttet är R+F. Återstående bidragsutfall är publicerat
totalbidrag minus I, R och F, inklusive den separat redovisade avrundningsresten.
Costbase:s kvarhållna82,1 mnkr kan inte säkert avgränsas mot framtida nationella
tillskott. De två notpolicyerna redovisas som scenarier, inte observationer.
Direkt befolkningskänslighet är `deltaR_h=r_h*deltaN/1e6`, utan efterföljande
ränteeffekt och utan anspråk på empiriska felgränser. Alla tolv fall behålls;
förbättring i ett delmått godkänner inte hela prognosen.

## 8. Resultat, periodisering, skuld och kassa

Med pensionskostnad E_p, betalning P_p, extra driftkostnad E_x, övrigt finansnetto F och ränta r:

\[
R=T+G+O_{rev}-C_H-C_O-C_{omst}-E_p-E_x-adjustment-D_A-F_X+F-rD.
\]

En räntebindningsproxy ger `dot r=(r_market-r)/tauRate`.
Driftens kassaflöde är `OCF=R+D_A+F_X+E_p-P_p+E_x-P_x-dot Q_T`, där P_x är betalning för extrakostnaden.
L är ackumulerad skillnad mellan pensionskostnad och betalning: `dot L=E_p-P_p`.
Det är en kassabrygga, inte en aktuariellt värderad pensionsskuld.

Extra kostnader styrs av `extraCostPath` och `extraCostPaymentPath`, vanliga
Modelica-parametrar med nominella årsbelopp i mnkr. Första posten avser det
första simulerade året; utanför listan är tillägget noll. Varje årsbelopp hålls
konstant som ett annualiserat flöde inom året, så årsintegralen blir exakt det
angivna beloppet. Inget ytterligare prisindex appliceras. Betalningsbanan följer
kostnadsbanan som förval och kan anges separat. Vid behov av förlopp inom året
kan båda indata `extraExpense` och `extraPayments` bindas explicit i scenariot.

Med tillståndet X definieras `dot X=E_x-P_x`, `X(0)=0`. Positivt X är ackumulerad
obetald extrakostnad; negativt X är förskottsbetalning. Kostnaden minskar resultatet
en gång. Den icke betalda delen återläggs i kassabryggan; senare betalning minskar
kassan utan att samma kostnad bokförs igen. X är inte en värdering av kommunens
totala avsättningar. Detta stöd avser extra drift, inte aktivering av investeringar
eller pensionskostnader som redan ligger i andra komponenter. Ett ofullständigt
betalningsschema kan lämna ett positivt saldo efter prognoshorisonten.

Sätt `F_cash=OCF-sum(I)` och `S=F_cash+(C-C_target)/tauLiquidity`:

\[
Borrow=[-S]_+,\quad Repay=\min([D]_+/\tauRepay,[S]_+),
\]
\[
\dot D=Borrow-Repay,\quad \dot C=F_{cash}+Borrow-Repay.
\]

Detta är en explicit finansieringspolicy som håller en kassabuffert och
amorterar överskott. Upplåning antas tillgänglig; likviditetsbegränsningar och
lånevillkor är ännu inte modellerade. Vid D=0 kan amortering inte göra D negativ.
Vid C=0 och ett icke-negativt kassamål kan flödet inte föra C under noll.

## 9. Härledda kontroller och årsrapportering

Modellens nettoställning är `E=sum(A+W)+C+Q_T-D-L-X`. Substitution av ekvationerna ger
**dot E=R**: investering flyttar pengar till byggprojekt, färdigställande flyttar
projekt till tillgångar, upplåning ändrar kassa och skuld lika mycket och
periodiseringsbryggorna motverkar de icke kassamässiga kostnaderna och intäkterna. Inget av dessa flöden
får bli intäkt eller dubbel kostnad. E är inte kommunens publicerade egna kapital,
eftersom övriga balansposter saknas.

Resultat och andra årsflöden rapporteras som integraler över [y-1,y], inte som
flödesvärdet vid årets sista dag. Befolkning, kassa och skuld är slutbestånd.
Ett extra tillstånd `cumulativeResult` gör kontrollen
`E(t)-E(0)-cumulativeResult(t)=0` oberoende av tidssteg.

Kontrollfallen omfattar analytisk personalanpassning, populationens bevarande,
fördröjt färdigställande, oförändrat kassaflöde vid en icke betald pensionskostnad,
räntechock, skattesatsändring, skuld som amorteras mot noll och årliga integraler.
Modellen måste också visa att långsammare personalminskning ger högre kvarstående
personalkostnad efter en efterfrågeminskning. Om lägre bemanning ger lägre kostnad
ska eventuell servicebrist samtidigt visas.

## Parameterunderlag och kvarvarande skattning

`data/baseline.json` ger initial befolkning samt de sammanlagda bokslutsposterna.
De avrundade bokslutsposterna summerar till 104 mnkr mot redovisade 105;
skillnaden på 1 mnkr läggs inte in som en återkommande intäkt. Sektorandelar,
årsarbetskostnad, personalantal, servicevikter, anpassningstider, kapacitetspris,
byggprojektens kapacitet/fördelning vid start och inkomstvikter är **scenarioantaganden eller härledningar
från sådana**. De är exponerade parametrar, inte uppmätta Motala-värden.

Den första empiriska skattningen bör använda personalårsarbetskrafter, elev-/
brukarvolymer, lokalkapacitet, sektorredovisning och projektens betalnings-/
driftsättningsdatum. Prova symmetrisk och asymmetrisk anpassning på samma tidigare
data. Fler parametrar är motiverade först när de tillför identifierbara mekanismer
eller tydligt avgränsade beslutsalternativ. Teknisk validering är skild från
prognosprecision; ingen ny SKR-överlägsenhet följer av denna implementation.

### Egen prognos utan historiska KPA-/SKR-prognosbanor

Sådana prognosbanor är inte ett generellt krav för att bygga en egen modell.
Observerade årsredovisningar och SCB:s räkenskapssammandrag kan användas för
skattning och periodordnade tester. Historiska prognosversioner behövs när
modellen uttryckligen använder dem som indata eller jämförs med vad den
prognosmakaren faktiskt förutsåg. Reviderade utfallsdata ger däremot inte
automatiskt ett test med exakt den information som fanns tillgänglig då.

En hypotes är att kostnaderna reagerar på budgetutrymme. En separat årlig
prognosregel är nu implementerad och tekniskt testad; dess prognoseffekt för
Motala är ännu **inte utvärderad**. Nuvarande `Services` får ingen sådan
signal; `Finance` finansierar kassabrist med lån. Kommunal budgetanpassning
studeras av [Büttner och Wildasin](https://www.ifo.de/DocDL/cesifo_wp649.pdf).
[Dahlberg och Lindström](https://doi.org/10.1006/juec.1997.2069) ger svensk
evidens för betydelsen av varaktiga resurser, och
[Dahlberg m.fl.](https://www.ifo.de/DocDL/cesifo1_wp1857.pdf) för utgiftsreaktioner
på statsbidrag. Källorna ger ingen direkt överförbar Motala-koefficient.

Ett avgränsat årligt test kan skrivas

\[
B_t=T_t+G_t^{rec}+F_t-C_t^{rec}-s(T_t+G_t^{rec}),
\qquad
\widehat C_{t+1}=C_t^{rec}+\Delta\widehat C_{t+1}^{bas}+\lambda B_t.
\]

Här är C nettokostnad, T skatt, G generella bidrag/utjämning och F finansnetto,
samtliga i samma prisbas och redovisningsavgränsning. `rec` avser en i förväg
bestämd behandling av tillfälliga poster. Basförändringen representerar den
oförändrade jämförelsemodellens pris-/behovsprognos. s är ett uttryckligt fast
resultatmål eller scenario, inte en ytterligare parameter vald efter utfallet.
Endast lambda är den nya reaktionsparametern; lambda=0 tar bort mekanismen.
Ett negativt B ger en nedåtriktad kostnadsjustering, ett positivt B en uppåtriktad.
Vid flera prognossteg används föregående stegs prognostiserade belopp, inte
målårets utfall. B är ett redovisat resultatutrymme relativt målet, inte en
identifierad permanent inkomst eller ett kassaflöde. En skattad positiv lambda
är ett prediktivt samband; eftersom C ingår både i basen och i B kan återgång
efter tillfälliga kostnadsstörningar ge samma mönster. Sambandet identifierar
inte ensamt en kausal politisk reaktion.

Med konstanta resurser, oförändrat mål och noll basförändring blir
`B_(t+1)=(1-lambda)*B_t`. Intervallet 0<=lambda<=1 ger då successiv anpassning
utan växlande tecken. Detta är en härledd egenskap under dessa antaganden,
inte ett påstående om faktisk kommunal politik eller ett lagkrav. Prövningen
ska inte samtidigt skatta ett permanentinkomstfilter och flera nya
bemannings-/anpassningstider. En senare koppling till Modelica måste gå genom
faktiska kostnads- och beslutsflöden så att bokföringsbalanserna bevaras.

[Forsknings- och datakatalogen](data/municipal-economics-research.json)
anger SCB:s resultaträkningar 1998–2025 och kostnads-/intäktsserier 2011–2025.
Tabellernas metadata är verifierade; Motala-raderna är ännu inte hämtade.
Källavstämning återstår. Träningsregeln och testprotokollet för det första
försöket är nu låsta enligt nedan.
Det befintliga upplägget med tolv redan undersökta fall är inte ett nytt
oberoende sluttest. Ingen ny prognospoäng eller kandidatbefordran följer av
denna hypotes.
Den [oberoende omprövningen](reviews/full-goal-reconsideration-20261015.txt)
stöder detta som nästa avgränsade försök, men godkänner inte prognosprecision
i förväg.

### Låst försök med rapporterad budgetsignal

`research/run_budget_response.py` prövar den reducerade årsmodellen separat
från Modelica. [Protokollet](data/budget-response-protocol.json)
registrerades före någon skattning mot nya Motala-data. Huvudförsöket använder
orensade rapporterade poster konsekvent över hela serien: R=T+G, C är positiv
nettokostnad inklusive avskrivning, F finansnetto och B=R-C+F. Här används
alltså inget `rec`-superskript. Saknade äldre engångspostnoter hindrar inte
detta försök; signalen får däremot inte kallas varaktiga resurser. s=0 är ett
deklarerat scenarioantagande.

Basen för varje komponent är samma fasta trendregel som i `fiscal.py`:
medelvärdet av fyra årsdifferenser från fem sammanhängande bokslutsår,
med framtida tillskott dämpade med 0,5 per prognossteg. Hela basbanan beräknas
före återkopplingen. Framtida R och F följer den banan; C får dessutom
lambda gånger föregående prognosstegs B. Kontrollen med lambda=0 återger
basbanan exakt. Framtida utfallspriser och utfallsvolymer används inte.

För varje träningsövergång normaliseras signalen och kostnadsfelet med R_t:

\[
x_t=(R_t-C_t+F_t)/R_t,\qquad
z_t=(C_{t+1}-\widehat C^{bas}_{t+1|t})/R_t,\qquad
\widehat\lambda=\operatorname{clip}_{[0,1]}
\left(\frac{\sum_t x_tz_t}{\sum_t x_t^2}\right).
\]

Inget intercept skattas. Minst åtta giltiga övergångar krävs, vardera med
fem års sammanhängande bashistorik. Målåren i träningen får högst vara
`min(prognosstart, 2019)`: parametern fryses alltså för starter 2020–2024.
Äldre starter 2010–2019 skattas endast på tidigare observationer. Både rå
och begränsad koefficient, signalernas tecken, enskilda års inflytande och
känslighet när en träningsövergång utelämnas redovisas. Dessa känsligheter
är inte konfidensintervall. Noll signal ger ingen identifierad parameter.

Rapporten behåller samtliga planerade starter och orsaker till uteblivna
prognoser. Resultatfel och komponentfel redovisas på samma fall, separat
för äldre och tidigare undersökta perioder. Bokslutsresten
`rho=resultat-(R-C+F)` sparas separat och används inte för att ändra B.
Prognosens framtida rest antas vara noll, vilket ger felidentiteten
`e_resultat=e_R-e_C+e_F-rho_utfall`.

Körningen mot befintliga fullständiga bokslut 2020–2025 ger inga skattningar
eller prognospoäng, eftersom äldre träning saknas. Den längre SCB-serien
måste först hämtas och stämmas av. Det nya försöket har inte ändrat några
tidigare prognoser. Jämförelse med frysta M2-resultat på gemensamma fall och
oberoende granskning av faktisk prognosförmåga återstår före en eventuell
integration i Modelicas driftbeslut.

## Historisk prövning

`research/run_historical.py` kör M2 och fryst v2 från historiska bokslut och
jämför på samma målår med M1, oförändrat värde och en fast dämpad trend.
`research/data/historical-protocol.json` låser antagandena; inga parametrar
optimeras mot utfallen. Bruttobokslut och källversioner finns i
`research/data/annual-ledgers.json`. Ursprungliga avrundningsskillnader bevaras.

Fem ettårsmål, 2021–2025, ger utvecklingsevidens. Publiceringsdatum är inte
verifierade och vissa poster är senare reviderade. Byggprojekt saknas för
2020/2021; noll, tio och tjugo procent av materiella tillgångar är uttryckliga
scenarier. Rapporten visar även urval med känd byggprojektsvolym. Testet med
ändrade framtida utfall kontrollerar periodgränsen; det bevisar inte att en
senare rapportversion var tillgänglig historiskt.

Den första körningen gav ettårs-MAE 61,93 mnkr för M2 mot 58,92 för oförändrat
resultat. Den analytiska rättningen är motiverad även om den inte räcker för
att slå baslinjen.

### Årsvisa kostnadsbanor från SKR

`historical-protocol-pkv.json` låser en efterföljande utvecklingsprövning med
decembercirkuläret från varje startår. `skr-pkv-vintages.json` innehåller de
daterade källorna. Inga cirkulär eller tillväxttal väljs efter prognosfelet.
PKV:s arbetskraftsindex inkluderar pensionseffekten, så det appliceras på den
sammanlagda personalkostnaden exakt en gång.

Med årlig tillväxt `gL[j]` respektive `gO[j]` definieras

\[
L_y=\prod_{j=1}^{y}(1+g^L_j),\qquad
O_y=\prod_{j=1}^{y}(1+g^O_j).
\]

Faktorerna hålls konstanta för `y-1 <= t < y`. Det motsvarar årsgenomsnitt,
inte en skattad månadsprofil. Modellens egna löne-, pris- och pensionstillväxt
sätts till noll. `laborPriceMultiplier=L_y` driver lönekostnaden och
`pensionExpense=pension0*L_y` den bokföringsmässiga pensionsdelen.
Vid oförändrad personalvolym blir den integrerade personalkostnaden exakt
`(payroll0+pension0)*L_y`. Den lokala fördelningen mellan lön och pension
prognostiseras inte separat. `otherPriceMultiplier=O_y` driver övriga kostnader
och kapacitetspris. Befolkning, bemanning, kapacitet och finansiering behåller
sina differentialekvationer. Integralerna och balansidentiteten är kontinuerliga
även när kostnadsfaktorerna byts vid ett årsskifte.

Ett oberoende native-test jämför tre års integrerade belopp med direkt
uppräkning, inklusive positiv, noll och negativ tillväxt. `macro.py` avvisar
saknade prognosår, framtida publiceringsdatum och samtidig intern indexering.

Detta är en nationell kostnadsapproximation. SKR:s äldre arbetskraftsindex drar
av antagen kvalitetsökning, vilket inte är exakt samma volymbegrepp som
oförändrade årsarbetskrafter. SKR tog bort justeringen i april 2022
([cirkulär 22:15, s. 14](https://extra.skr.se/download/18.542a096a18019210a48a9383/1651143815523/22015.pdf)).
De ursprungliga prognoserna bevaras utan efterhandskorrigering. Lokala
pensionskostnader kan avvika på grund av personalstruktur.

På de fem gemensamma ettårsmålen faller resultat-MAE till 25,21 mnkr och
personal-MAE från 82,19 till 37,20 mnkr. Den enkla jämförelsen PKV-accounting,
som använder samma kostnadsbanor men konstanta volymer, avskrivningar och
finansnetto, når resultat-MAE 24,25. M2:s dynamik har därmed inget visat
tillskott till punktprognosprecisionen. Treårs-MAE försämras från 56,05 till
83,02 mnkr. Dessa utfall behålls i rapporten. Korrekt makrodatum gör inte
retrospektivt sammanställda bokslut till historiskt tillgängliga data;
prövningen är utvecklingsevidens och ingen överlägsenhet över SKR:s
kommunvisa intäktsmodell har visats.

## Parade experiment och känslighetsanalys

`research/run_experiments.py` läser en namngiven referens, beslutsalternativ och
ändrade antaganden. Varje omvärldsvariant körs med både referens och alternativ;
resultatskillnader beräknas inom samma variant. Motstridiga ändringar av samma
parameter i beslut och känslighetsantagande avvisas. Misslyckade körningar finns
kvar i rapporten och får inga jämförelsetal.

Exempeldesignen varierar löner, byggfördröjning, lokalkostnadsandel och
omställningskostnad en i taget, samt en uttrycklig kombination av högre kostnader,
högre ränta och svagare skattebas. Intervallen är valda stresstest, inte skattade
sannolikhetsintervall. Rangordning av påverkan gäller de valda intervallen;
en parameter i taget fångar inte alla samspel.

Varje delkörning sparar kompilatorns faktiskt beräknade parametrar, årsflöden,
tillstånd, källor och filhashar. Utöver ekonomi visas köpt service, kostnader
per verksamhet och årets otillgodosedda behov. Andelen servicebrist divideras
med integrerad efterfrågan under samma år, inte med behovet vid årets sista dag.
Serviceandelar jämförs per verksamhet; de adderas inte över olika volymmått.
