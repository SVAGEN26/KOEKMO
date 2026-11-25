# Modellerna som sajten kör

Ladda alltid `Kommunekonomi.mo` först.

- `Kommunekonomi.mo`: biblioteket. Posttyper för bokslut och befolkning, rikets SCB-data, de gemensamma delarna
  (`Components.Scenario`, `Revenue`, `Calendar`, `Fertility`), de gemensamma antagandena (`Assumptions`), utdata
  (`Report`) och modellen `Continuous.Economy`: lager och flöden i kontinuerlig tid, med komponenterna
  `Demography`, `CohortDemography`, `Services`, `OperatingAccounts`, `Payments`, `Capital` och `Finance`.
  Årsmodellen (`Annual`) togs bort i november 2026. `Components.Demography` och `CohortDemography` finns kvar
  med årssteg för demografitesterna (`Motala.Examples.DemographyOnly`).
- `Motala.mo`: Motalas basår 2020–2025 (`Data.motala2020` till `motala2025`), handledning och ordlista,
  `Motala.Continuous` och exempel som `Hindcast2025`, `ContinuousCohort` och `Budget2026`.
- `municipalities/`: ett paket per kommun i Östergötland, genererat av `scripts/prepare_municipality.py`
  ur SCB och Kolada, med basår 2017–2025. Redigera inte för hand.
- `MotalaBrowser.mo`: omslaget som webbläsaren kompilerar (wasm-jit), `MotalaBrowserContinuous` kring
  `Motala.Continuous`. Fast kapacitet på 100 år och alla indata som fria parametrar med bokstavliga
  standardvärden, så att `-override` når dem.

Tiden är kalenderår. Starttiden är basåret (bokslutet 31 december), och `horizon` år räknas fram; standard
är åtta år, 2026–2033 från bokslut 2025. Belopp i mnkr, löpande priser. Enheterna står i typerna i
`Kommunekonomi.Units`: `Money` (`MSEK`, lager och årsbelopp), `MoneyRate` (`MSEK/a`, flöden),
`MoneyPerPerson` (`SEK`, kronor per invånare), `Persons`, `PersonsPerYear` (`1/a`), `Rate` (`1/a`: takt i
kontinuerlig tid, som dödstal och tillväxt) och `Duration` (`a`). Andelar, index och årliga tillväxttal
är dimensionslösa och har ingen enhet angiven, skattesatsen är i procent. Ett årsbelopp blir ett flöde genom
division med `Units.year`. Modelicas `time` räknas här i år, inte i sekunder som standarden antar.

OpenModelicas enhetskontroll (`--unitChecking`) känner bara SI-enheter och säger inget om `MSEK` eller `a`.
`npm run check:units` (`scripts/check_units.py`) skriver därför om enheterna till SI-enheter som kontrollen känner
(`MSEK` och `SEK` som `mol`, `a` som `s`) och kontrollerar `Motala.Continuous`,
`Motala.Examples.ContinuousCohort` och `Kommunekonomi.Continuous.Economy`. Den hittade 13 motsägelser, mest årsbelopp som kopplades direkt till flöden i
`Continuous`; de är rättade och siffrorna oförändrade. Kontrollen täcker ekvationer och kopplingar mellan variabler
med angiven enhet, men inte algoritmavsnitt: årsstegen (`when calendar.tick` med `:=`) kontrolleras inte. Där är enheterna deklarerade men bara granskade för hand. Vektorekvationer
(`x = y .* z` på hela fält) kontrolleras inte heller; den kontinuerliga demografin är därför skriven med for-slingor. Variabler utan enhet får en
enhet härledd i stället för kontrollerad, och kronor och miljoner kronor är samma enhet för den. Beskrivningar är på svenska;
namnen i koden är ASCII, eftersom Modelica inte tillåter å, ä eller ö i namn.

Åldrandet mellan befolkningslagren följer basårets ettårsåldrar (`Data.ageProfile`, `BaseYear.ages`), pensionskostnaden
följer lönesumman, kassan ger ränta och gator och vägar följer vägnätet (`infrastructureShare`).

I `Continuous.Economy` är pengar och befolkning lager med flöden:
födda, döda, åldrande och flyttningar (`Continuous.Demography`, fem grupper; `Continuous.CohortDemography`,
ettårsåldrar), kostnader och löne-, pris- och kostnadsnivåer som växer under året. Löne- och prisnivåns takt inom
året är vald så att årsmedlet ökar som banan anger (`Data.meanPreservingRates`). Händelser finns bara för det som
är årligt: bokslutet 31 december, beslut som gäller från 1 januari (skattesats, årets skatt och bidrag, som betalas
jämnt), folkbokföringen 1 november och inläsningen av årsbanorna. Med ettårsåldrar byter födelseårsgrupperna
etikett vid årsskiftet. Varför och hur stort det blir: [../docs/methodology.md](../docs/methodology.md#continuous-time).
Modellen behöver en riktig lösare. Sajten kör den implicita lösaren `ida`, som också klarar flöden med tidskonstanter på dagar till veckor: betalningstider i dagar
(rörelsekapital), kassareserven och ett projekt som tas i bruk. I OMEdit räcker standardlösaren `dassl`.

Standardvärdena är illustrativa. Hämta `Scenario.mo` från sajten för att återskapa ett scenario med
planeringsunderlagen. Ekvationerna beskrivs i [../docs/methodology.md](../docs/methodology.md).

Forskningsmodellerna M1 och M2 ligger i `../research/` och används inte av sajten.
