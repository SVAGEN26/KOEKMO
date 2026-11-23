# Modellerna som sajten kör

Ladda alltid `Kommunekonomi.mo` först.

- `Kommunekonomi.mo`: biblioteket. Posttyper för bokslut och befolkning, rikets SCB-data, komponenterna
  (`Scenario`, `Demography` och `CohortDemography`, `Services`, `OperatingAccounts`, `Revenue`, `Capital`,
  `WorkingCapital`, `Finance`), de gemensamma antagandena (`Assumptions`), utdata (`Report`) och de två
  modellerna `Annual` (ett steg per år) och `Continuous.Economy` (lager och flöden, kontinuerlig tid inom året).
- `Motala.mo`: Motalas basår 2020–2025 (`Data.motala2020` till `motala2025`), handledning och ordlista,
  `Motala.Annual`, `Motala.Continuous` och exempel som `Hindcast2025`, `AnnualCohort` och `Budget2026`.
- `municipalities/`: ett paket per kommun i Östergötland, genererat av `scripts/prepare_municipality.py`
  ur SCB och Kolada, med basår 2017–2025. Redigera inte för hand.
- `MotalaBrowser.mo`: omslaget som webbläsaren kompilerar (wasm-jit). Fast kapacitet på 100 år och alla
  indata som fria parametrar med bokstavliga standardvärden, så att `-override` når dem.
- `validate.py`: kompilerar med lokal omc och jämför med JavaScript-referensen (`npm run validate:modelica`).

Tiden är kalenderår. Starttiden är basåret (bokslutet 31 december), och `horizon` år räknas fram; standard
är åtta år, 2026–2033 från bokslut 2025. Belopp i mnkr, löpande priser. Enheterna står i typerna i
`Kommunekonomi.Units`: `Money` (`MSEK`; i `Annual` årets belopp), `MoneyRate` (`MSEK/a`, flöden i `Continuous`),
`MoneyPerPerson` (`SEK`, kronor per invånare), `Persons` och `Duration` (`a`). Andelar, index och tillväxttakter
är dimensionslösa och har ingen enhet angiven, skattesatsen är i procent. OpenModelicas enhetskontroll
(`--unitChecking`) varnar inte, men den känner inte valutan, så det är ingen fullständig kontroll. Beskrivningar är på svenska;
namnen i koden är ASCII, eftersom Modelica inte tillåter å, ä eller ö i namn.

Standardvärdena är illustrativa. Hämta `Scenario.mo` från sajten för att återskapa ett scenario med
planeringsunderlagen. Ekvationerna beskrivs i [../docs/methodology.md](../docs/methodology.md).

Forskningsmodellerna M1 och M2 ligger i `../research/` och används inte av sajten.
