# SCB: dödlighet, fruktsamhet och befolkning per ettårsålder

Hämtat 2026-11-08 med `python3 scripts/fetch_mortality_data.py`. Källa: SCB, Statistikdatabasen (CC BY 4.0).
Anrop, svarsstorlek och SHA-256 för varje fil finns i manifest.json; metadata per tabell i *-metadata.json.

| Fil | SCB-tabell | Innehåll |
|---|---|---|
| life-table | BE0101I/LivslangdEttariga | Riket, dödsrisk (promille) och återstående medellivslängd per ettårsålder och kön, 2010–2025 |
| projected-death-rates | BE0401D/BefProgDodstalNb | Dödstal i SCB:s senaste riksframskrivning, 2026–2070 |
| projected-fertility | BE0401D/BefProgFruktTotNb | Fruktsamhetstal per ålder i samma framskrivning, 2026–2070 |
| motala-population-2015-2024, -2025 | BE0101A/BefolkningNy, BefolkningCKM | Motala, folkmängd 31/12 per ettårsålder och kön |
| motala-deaths-2015-2024, -2025 | BE0101I/DodaHandelseK, DodaHandelseKCKM | Motala, döda per uppnådd ålder och kön |
| motala-births-2015-2024, -2025 | BE0101H/FoddaK, FoddaKCKM | Motala, födda per moderns ålder och barnets kön |
| total-fertility | BE0101H/FruktsamhetSum | Summerad fruktsamhet, riket och Motala, 2000–2025 |
| fertility-rates-sweden | BE0101H/FruktsamhetHVD | Fruktsamhetstal per femårsålder, riket, 2010–2025 |
| scb-projection-motala | BE0401A/BefProgOsiktRegN | SCB:s regionala framskrivning för Motala (basår 2024), 2024–2070 |

SCB:s folkmängd 2025 (43 113) och döda (459) skiljer sig från årsredovisningen (43 131, 468). Modellen skalar
ettårsåldrarna till årsredovisningens total. Den regionala framskrivningen är ett jämförelsetal, inte modellindata.

Bearbetning: `python3 scripts/prepare_demography.py data/downloads/20261108T124756Z` skriver
data/demography-inputs.json; `python3 scripts/write_demography_modelica.py` skriver Motala.Data.SCB.
