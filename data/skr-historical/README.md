# Återfunna historiska SKR-underlag

Hämtat 2026-11-17, kommunförekomst kontrollerad 2026-11-18. Källa: SKR:s ursprungliga arbetsböcker,
bevarade av Internet Archive. Detta kompletterar tidigare anteckningar om att
historiska kommunvisa prognosunderlag saknades i projektet.

| Publicering | Cirkulär | Arbetsbokens år | Kontrollerat |
| --- | --- | --- | --- |
| 2021-09-30 | 21:35 | 2021–2028 | Cirkulär, årsrubrik, Motala i grunddata, SHA-1 |
| 2022-08-25 | 22:28 | 2022–2029 | Cirkulär, årsrubrik, Motala i grunddata, SHA-1 |
| 2023-12-14 | 23:56 | 2023–2030 | Cirkulär, årsrubrik, Motala i grunddata, SHA-1 |
| 2024-12-12 | 24:56 | 2024–2031 | Cirkulär, årsrubrik, Motala i grunddata, SHA-1 |

Originalen ligger lokalt i `originals/`. De distribueras inte i git eller sajten.
`manifest.json` innehåller original- och arkivadresser, arkivdatum, hämtningsdatum,
SHA-256, arkivets SHA-1 och status. Återhämta med:

```sh
python3 scripts/fetch_historical_skr.py
```

Skriptet hämtar endast filer och verifierar dem; det kör inga makron och ändrar
inte modellens indata. Befintliga filer med rätt kontrollsumma lämnas orörda.

## Publicering och rättigheter

Användarens inriktning 2026-11-18: dela begränsade sifferutdrag och egna analyser,
behåll de fullständiga arbetsböckerna lokalt. Publicera källadresser,
cirkulär/publiceringsdatum, kommun, enheter och cellhänvisningar med utdragen.
Skilj SKR:s publicerade belopp från våra omräkningar och scenariojusteringar.
Original och omräknade arbetsböcker ingår varken i git eller webbbygget.

SKR publicerar prognosunderlagen öppet på sin
[prognossida](https://skr.se/ekonomiochbudgetplanering/skatteunderlagsprognoser.8271.html).
Vid granskning 2026-11-18 hittades ingen uttrycklig återpubliceringslicens för
just dessa arbetsböcker på prognossidan eller i den sökbara celltexten i de
granskade xlsm-filerna. SKR har även en
[sida för öppna data](https://skr.se/resurserochhjalpmedel/skrsoppnadata.8439.html),
men kopplingen mellan dess generella beskrivning och dessa arbetsböcker är
inte fastställd. Offentlig publicering är inte i sig ett licensbesked.

[PRV anger att fakta inte skyddas av upphovsrätten](https://www.prv.se/sv/upphovsratt/for-myndigheter/).
Sammanställningar kan dock omfattas av katalog-/databasskydd enligt
[49 § upphovsrättslagen](https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/lag-1960729-om-upphovsratt-till-litterara-och_sfs-1960-729/).
Att exportera till CSV/JSON eller ange källa innebär därför inte automatiskt
att varje omfattning av återpublicering är tillåten. Begränsade Motala-utdrag
och egna jämförelser är projektets valda inriktning; någon uttrycklig licens
eller bekräftelse från SKR har inte inhämtats. Tredjepartsmaterialet omfattas
inte av projektets MIT-licens.

Kontroll 2026-11-18: inga Excel-filer spåras i den aktuella git-versionen och
inga finns i `site/dist/`. Äldre Excel-original och arbetskopior finns dock
kvar i git-historiken (bland annat commit `95f2df9`). `.gitignore` tar inte bort
dem ur historiken. Historiken har inte skrivits om vid denna kontroll.

## Vad fynden möjliggör

Arbetsböckerna innehåller SKR:s kommunvisa beräkning av **skatt och generella
bidrag/utjämning**, inte en prognos för kommunens hela resultaträkning.
Motala finns i **alla fyra**: `Data!A56 = 583`, `Data!B56 = Motala`, samt
`kommunkoder!G27 = Motala`, `H27 = 583`. Raden innehåller numeriska lokala
grunduppgifter. Förekomsten är alltså kontrollerad i själva arbetsböckerna.

De är generella filer med kommunval. I alla fyra är
`Prognosunderlag!B1` tom och kommunintäkternas cachade värden noll. Motala (583)
måste väljas i en kopia, makron tas bort och formlerna räknas om innan beloppen
kan användas. Kontrollera även beräknat kommunnamn och summorna av delposterna.

2021 års äldre XLS-fil har Excels inbyggda kryptering med standardlösenordet
`VelvetSweatshop`. Den lästes 2026-11-18 i minnet med msoffcrypto-tool 6.1.0
och xlrd 2.0.2. Biblioteken installerades bara till `/tmp/motala-xls-reader`.
Inga makron eller formler kördes och originalets kontrollsumma är oförändrad.

December 2023 och 2024 motsvarar två av tillfällena i
`scripts/hindcast_vintages.py`. De återfunna versionerna 2021 och 2022 har andra
datum än decemberversionerna. Septemberversionen 21:35 används i webbens historiska
körning från bokslutet 2021. Alla fyra är omräknade för länets kommuner, se nedan.

Den lokala makrofria kopian ligger i
`recalculated/Prognosunderlag-Motala-0583-21035.xlsx`. Den togs fram genom
XLS-läsning och konvertering med makron spärrade, kommunval 583 på bladet
Prognosunderlag, tömning av cachade formelvärden och omräkning i LibreOffice.
Återskapa sifferutdraget med
`python3 scripts/prepare_replay_2022.py data/skr-historical/recalculated/Prognosunderlag-Motala-0583-21035.xlsx`.
Skriptet kontrollerar kommunnamn, prognosversion, år och intäktssummorna.

Publiceringsdatum kommer från cirkulären. Arkivdatum är separata observationer;
de bevisar inte att filen var oförändrad sedan publiceringsdagen. Interna
cirkulärnummer och årsrubriker har kontrollerats där ovanstående tabell anger det.

## Utläsning för länets 13 kommuner (2026-11-24)

`scripts/read_skr_vintages.py` väljer varje kommun i en makrofri kopia av alla fyra
arbetsböckerna, tömmer cachade formelvärden, räknar om i lokal LibreOffice med makron
spärrade och läser skatt (Blad 1 rad 38) och generella bidrag (rad 40) för bokens åtta år.
Kommunnamn, cirkulär, år och delsummor kontrolleras. 2021 års XLS öppnas direkt av
LibreOffice (standardlösenordet hanteras där). Resultatet ligger i `forecasts.json`:
två belopp per kommun och år, med cellhänvisning. De omräknade kopiorna ligger lokalt i
`recalculated/<cirkulär>/` och originalen även i det privata repot
https://github.com/SVAGEN26/ekonomilabb-kallor (`skr-prognosunderlag/`).

Motalas värden ur 21:35 är desamma som i den tidigare handgjorda omräkningen
(`data/replay-2022.json`), och prognosen för innevarande år ligger inom 3 % av utfallet
för alla kommuner och årgångar (`tests/test_explain_outcome.py`). Jämförelsen med utfall
och med modellen: `scripts/explain_outcome.py` och README, avsnittet Accuracy.

## Återstående luckor och sökningar

- Decemberversionerna 20:57, 21:49 och 22:54 är ännu inte hämtade.
- Länken till filen för 20:57 finns i SKR-sidan arkiverad 2021-01-19. Den ger
  404 hos SKR; webbarkivets exakta filindex gav ingen träff vid kontrollen.
- SKR:s nuvarande prognossida listar 2026 års kommunfiler. De kontrollerade
  direktlänkarna till originalfilerna 23:56 och 24:56 ger 404 både hos skr.se
  och extra.skr.se. Arkivkopiorna kunde däremot hämtas och verifieras.
- SKR-sidorna arkiverade 2022-09-26 och 2025-01-19 samt webbarkivets filindex
  gav de återfunna filadresserna. Adresser och sökstatus finns i manifestet.
- Motalas diarium gick att läsa. Dess offentliga konfiguration anger
  ”Sökfunktionen är i nuläget inte aktiv.” Inga nya Motala-bilagor återfanns där
  i denna sökning; frånvaro i kommunens arkiv är inte fastställd.

En fortsatt riktad förfrågan till kommunen/SKR bör ange just originalfilerna
20:57, 21:49 och 22:54, gärna med sparad version och administrationsblad.
Ingen förfrågan har skickats.
