#!/usr/bin/env python3
"""Annual and Continuous side by side: error per account line in the vintage hindcast.

    python3 scripts/compare_hindcasts.py [code] [assumptions]

Reads data/vintage-hindcast.json and data/vintage-hindcast-continuous.json (Motala) or the
municipality's files under data/municipalities/<code>/, written by
scripts/hindcast_vintages.py with and without HINDCAST_MODEL=Continuous. Prints mean error
(model minus outcome) and mean absolute error per line and horizon, and the mean paired
difference Continuous minus Annual over the same runs. Assumptions default to skr.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINES = ('result', 'tax', 'grants', 'netCost', 'payroll', 'pension', 'otherCosts', 'operatingRevenue',
         'depreciation', 'interest', 'debt', 'cash', 'population')


def load(code, suffix):
    path = ROOT / (f'data/vintage-hindcast{suffix}.json' if code == '0583' else f'data/municipalities/{code}/vintage-hindcast{suffix}.json')
    return json.loads(path.read_text())


def main():
    code = sys.argv[1] if len(sys.argv) > 1 else '0583'
    assumptions = sys.argv[2] if len(sys.argv) > 2 else 'skr'
    annual, continuous = load(code, ''), load(code, '-continuous')
    key = lambda r: (r['origin'], r['year'], r['assumptions'])
    paired = {key(r): r for r in continuous['runs']}
    print(f'{code}, assumptions {assumptions}. Mean error / mean absolute error, mnkr; paired = Continuous - Annual.')
    print(f'{"line":17s} {"h":>2s} {"n":>2s} {"Annual ME":>10s} {"MAE":>7s} {"Contin. ME":>11s} {"MAE":>7s} {"paired":>7s}')
    for line in LINES:
        for horizon in (1, 2, 3):
            pairs = [(a, paired[key(a)]) for a in annual['runs']
                     if a['assumptions'] == assumptions and a['horizon'] == horizon and key(a) in paired
                     and a['outcome'].get(line) is not None and line in a['model']]
            if not pairs:
                continue
            n = len(pairs)
            err = lambda r: r['model'][line] - r['outcome'][line]
            me_a, mae_a = sum(err(a) for a, _ in pairs) / n, sum(abs(err(a)) for a, _ in pairs) / n
            me_c, mae_c = sum(err(c) for _, c in pairs) / n, sum(abs(err(c)) for _, c in pairs) / n
            diff = sum(c['model'][line] - a['model'][line] for a, c in pairs) / n
            print(f'{line:17s} {horizon:2d} {n:2d} {me_a:10.1f} {mae_a:7.1f} {me_c:11.1f} {mae_c:7.1f} {diff:7.1f}')


if __name__ == '__main__':
    main()
