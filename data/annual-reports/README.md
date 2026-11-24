# Årsredovisningarnas resultaträkning mot SCB

Skapad 2026-11-23 med `python3 scripts/extract_annual_reports.py /sökväg/till/ekonomilabb-kallor`.
PDF:erna ligger i ett privat repo (SVAGEN26/ekonomilabb-kallor): de är offentliga handlingar,
men bilderna i dem kan ha andra rättighetsinnehavare. Varje rad här har kommunens egen URL.

- `resultatrakning.csv`: kommunens resultaträkning, rad för rad, för årsredovisningarna
  2021–2025 (rapportåret och jämförelseåret). `arsredovisning` är beloppet i rapporten i mnkr
  (omräknat från tkr där `enhet` = tkr), `scb` SCB TAB6777, `sida` PDF-sidan (1 = filens första
  sida; den tryckta sidnumreringen kan skilja).
- `jamforelsestorande.csv`: rader som nämner jämförelsestörande poster, med sida, för läsning
  för hand.

Status per rad:
- `stämmer`: rapporten har ett belopp inom 1,5 mnkr från SCB för året. Det är en kontroll av
  SCB mot rapporten, inte en oberoende avläsning av kolumnen.
- `ingen träff`: inget belopp i rapporten ligger nära SCB. Antingen skiljer sig rapporten från
  SCB, eller så läser skriptet inte layouten. Läs sidan för hand.
- `resultaträkning ej hittad`: ingen sida med resultaträkningen i textform.

Läget 2026-11-23: 881 av 1 232 rader stämmer, 219 utan träff, 132 utan hittad resultaträkning.

Kända skillnader och luckor:
- Linköping: årsredovisningen följer god redovisningssed "med undantag av pensionsredovisningen"
  (2025, s. 61). Kommunens resultat 594 mnkr 2025 och 233 mnkr 2024 enligt rapporten, 418 och
  161 enligt SCB. Skillnaden i resultat är inte utredd.
- Norrköping: jämförelsestörande poster för Ostlänken; se `docs/project-memory.md`.
- Boxholm 2021–2025 och Åtvidaberg 2023: resultaträkningen är en bild i PDF:en. Behöver OCR
  eller avläsning för hand.
- Motala ingår inte: dess bokslut är avläst för hand i `research/data/annual-ledgers.json`.
- Saknas helt: Kinda 2021–2022 och Mjölby 2021 och 2024 (se `kallor-saknas.md` i källrepot).
