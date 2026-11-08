# Kolada: äldreomsorg i Motala efter åldersgrupp

Hämtat 2026-11-08 med `python3 scripts/fetch_care_data.py`. Källa: Kolada (RKA), öppna data; statistiken
kommer från Socialstyrelsen och SCB. Anrop och SHA-256 finns i manifest.json, nyckeltalens definitioner i
kolada-care-kpi-metadata.json.

Nyckeltal 2015–2025, Motala (0583), totalt och per kön: hemtjänsttagare 65+, 65–79, 80+ (N21702, N21703,
N21705); brukare i särskilt boende 65+, 65–79, 80+ (N23805, N23807, N23806); kostnad hemtjänst och särskilt
boende per invånare 65+ och 80+ (N21009, N21024, N23007, N23001); särskilt boende kr/brukare (N23009);
äldreomsorg kr/invånare 65+ och 80+ (N20007, N20048); invånare 65–79 och 80+ (N01956, N01957).

Kolada delar inte upp 80+. `python3 scripts/prepare_care.py data/downloads/20261108T131731Z` beräknar
omsorgskostnad per invånare 65–79 och 80+ till data/care-weights.json.
