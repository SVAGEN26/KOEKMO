# Nedladdade planeringsunderlag för Motala

Hämtat 2026-11-06. Kommunkod 0583. Originalfiler, anrop, metadata och SHA-256 finns i manifest.json.

- budget-2026-plan-2027-2028.pdf: kommunens publicerade budget.
- budget-2025-plan-2026-2027.pdf: föregående budget; kommunens aktuella länk heter Budget_260323.pdf.
- arsredovisning-2022.pdf till arsredovisning-2025.pdf: fyra årsredovisningar.
- bep6001-motala.csv och .json: 651 värden, 2005–2035, femårsåldrar till 90–94 samt 95+ och totalt. Ålderskoderna 1–21 är kategorikoder, inte åldrar; etiketter finns i bep6001-metadata.json.
- bep6006-motala.csv och .json: 124 värden, 2005–2035, grupperna 0–19, 20–64, 65+ och totalt.
- kolada-motala-2010-2025.csv: 384 rader för 20 nyckeltal om kostnader, barn/elever, bemanning och hemtjänst. Årstäckningen varierar; manifestets kolada_coverage visar varje serie.
- kolada-kpi-metadata.json: definitioner, källor och avgränsningar. Rådata finns i kolada-data-page-1.json.

Befolkningsdatabasens fotnot anger observationer 2005–2025 och prognos 2026–2035, med kommunens egen prognos som källa för Motala. Detaljtabellen har femårsåldrar, inte ettårsåldrar. Uppgifterna är aktuell dataversion och ska inte användas som historiskt tillgängliga prognoser utan versionskontroll.

CSV-filer är UTF-8 med BOM. Råa saknadmarkeringar, status, kön och rader markerade som borttagna har bevarats. Kolada-definitionerna skiljer bland annat på hemkommun, lägeskommun och egen regi. Kostnader i kr/inv eller kr/elev är inte totalbelopp i mnkr. Data måste definieras och enheter granskas före modellimport.

Delårsrapport/tertialrapport 2026 är ännu inte hämtad. En sökning i offentliga diariet gav noll träffar, vilket inte visar att dokumenten saknas. Separata lokal-, låne- och pensionsunderlag återstår vid behov efter granskning av PDF:erna.

Detta är ett källarkiv. Modellens kalibrerade indata har inte ändrats.

Återskapa i ett nytt tidsstämplat arkiv med `python3 scripts/fetch_planning_data.py`.
