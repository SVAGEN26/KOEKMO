# Modellen som sajten kör

- `Motala.mo`: årsmodellen `Motala.Annual` med sex delar (demografi, verksamhet, drift, intäkter, kapital, finans).
- `MotalaBrowser.mo`: omslaget som webbläsaren kompilerar med OpenModelica (wasm-jit).
- `validate.py`: kompilerar modellen med lokal omc och jämför med den oberoende JavaScript-referensen.

Tiden är kalenderår: starttid 2025 (bokslutet 31 december 2025) och stopptid 2030 räknar fram 2026–2030. Med ett annat basår är starttiden det året.
Beskrivningar och dokumentation är på svenska; namnen i koden är ASCII, eftersom Modelica-standarden inte tillåter å, ä eller ö i namn.
Standardvärdena är illustrativa. Hämta `Scenario.mo` från sajten för att återskapa ett scenario med planeringsunderlagen.

Forskningsmodellerna M1 och M2 ligger i `../research/` och används inte av sajten.
