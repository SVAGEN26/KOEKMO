#!/usr/bin/env python3
"""Fixed interest-rate paths for stress tests, from episodes in Riksbank's yearly rates.

    python3 scripts/prepare_rate_stress.py [data/downloads/<timestamp>-riksbank-rates]

Each path is how the 3-month treasury bill rate moved, year by year, from the year before an episode:
the change in percentage points, added to the municipality's own rate in the scenario. So the path starts
where the scenario's rate is and moves the way the market rate once did. The page keeps the rate at or
above 0 and lets the fixed-rate period carry the change into the average rate. Where an episode is shorter
than the horizon, its last change stays. Not forecasts: paths that have happened, to see what they would
do to the result and the debt.

Writes data/rate-stress.json. Without an argument it reads the latest archive.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YEARS = 8
EPISODES = (
    ('rise2022', 2022, 'Som 2022–2025', 'Inflationen: räntan steg nästan 4 procentenheter på två år.'),
    ('crisis1990', 1989, 'Som 1989–1996', '90-talskrisen: räntan steg 3–4 procentenheter och föll sedan kraftigt.'),
    ('finance2006', 2006, 'Som 2006–2013', 'Före och efter finanskrisen: en uppgång på 2 procentenheter, sedan fall.'),
    ('low2013', 2013, 'Som 2013–2020', 'Allt lägre ränta, ned mot noll.'),
)


def main():
    archive = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted((ROOT / 'data/downloads').glob('*-riksbank-rates'))[-1]
    archive = archive if archive.is_absolute() else ROOT / archive
    rows = json.loads((archive / 'SETB3MBENCH.json').read_text())
    rate = {r['year']: round(r['average'], 2) for r in rows}
    episodes = []
    for key, first, label, description in EPISODES:
        start = rate[first - 1]
        years = [y for y in range(first, first + YEARS) if y in rate]
        changes = [round(rate[y] - start, 2) for y in years]
        episodes.append({'id': key, 'label': label, 'description': description, 'years': [first, years[-1]],
                         'startRate': start, 'rates': [rate[y] for y in years], 'changes': changes})
    out = {
        'source': 'Sveriges riksbank, statsskuldväxel 3 månader (SETB3MBENCH), årsmedelvärde',
        'sourceUrl': 'https://www.riksbank.se/sv/statistik/rantor-och-valutakurser/',
        'archive': str(archive.relative_to(ROOT)),
        'unit': 'procent; changes i procentenheter från året före episoden',
        'method': __doc__.split('\n\n', 2)[1].strip().replace('\n', ' '),
        'yearlyRates': {str(y): r for y, r in sorted(rate.items())},
        'episodes': episodes,
    }
    (ROOT / 'data/rate-stress.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    for e in episodes:
        print(e['id'], e['years'], 'from', e['startRate'], 'changes', e['changes'])


if __name__ == '__main__':
    main()
