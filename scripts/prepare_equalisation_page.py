#!/usr/bin/env python3
"""The 13 municipalities' equalisation for the page that explains the system (site/src/utjamning.html).

    python3 scripts/prepare_equalisation_page.py

Reads data/equalisation.json (SCB TAB1981 and TAB4011, kr per inhabitant) and writes
data/equalisation-county.json: the latest year's income and cost equalisation, structural grant,
regulation grant, their sum and the LSS equalisation for Östergötland's municipalities.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('income', 'cost', 'structure', 'regulation', 'total', 'lss')


def main():
    data = json.loads((ROOT / 'data/equalisation.json').read_text())
    year = data['years'][1]
    rows = [{'code': code, 'name': m['name'], **{f: m['years'][str(year)][f] for f in FIELDS}}
            for code, m in sorted(data['municipalities'].items()) if code.startswith('05')]
    out = {'source': data['source'], 'archive': data['archive'], 'year': year,
           'unit': 'kr per invånare (folkmängd 1 november året före)', 'municipalities': rows}
    (ROOT / 'data/equalisation-county.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    for r in rows:
        print(r)


if __name__ == '__main__':
    main()
