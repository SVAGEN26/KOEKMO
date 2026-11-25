#!/usr/bin/env python3
"""SKR's forecasts of Sweden's tax base against the government's and ESV's, and all against the outcome.

    python3 scripts/compare_tax_base_forecasters.py

Reads research/data/tax-base-forecasters.json (the comparison table of SKR's December circulars 2020-2024) and
the outcome of the tax base (scripts/hindcast_vintages.py: SCB, growth by income year). Years ahead is the
forecast year minus the circular's year; 0 is the year under way. Years without an outcome (2025 on) are left
out. Writes data/tax-base-forecasters.json: every error, and per forecaster and years ahead the number of
forecasts, the mean error and the mean absolute error in percentage points of growth, and the error of the
level after two and three years.

The forecasts are not from the same day, the cases are few and they share one period: this shows whether
SKR stood out, not who forecasts best.
"""
import json
from pathlib import Path

from hindcast_vintages import tax_base_outcomes

ROOT = Path(__file__).resolve().parents[1]
FORECASTERS = ('SKR', 'ESV', 'Government', 'SKR previous')
LAST_OUTCOME = 2024


def main():
    source = json.loads((ROOT / 'research/data/tax-base-forecasters.json').read_text())
    outcome = {y: 100 * g for y, g in tax_base_outcomes().items() if y <= LAST_OUTCOME}
    errors, levels = [], []
    for c in source['circulars']:
        origin = int(c['published'][:4])
        for row in c['rows']:
            growth = {int(y): v for y, v in row['growthPercent'].items()}
            for year in sorted(growth):
                if year >= origin and year in outcome:
                    errors.append({'circular': c['circular'], 'forecaster': row['forecaster'], 'made': row['made'], 'year': year,
                                   'yearsAhead': year - origin, 'forecastPercent': growth[year],
                                   'outcomePercent': round(outcome[year], 2), 'errorPoints': round(growth[year] - outcome[year], 2)})
            # The level after n years, from the year before the first forecast year: the errors of single years add up.
            for n in (2, 3):
                years = range(origin + 1, origin + n + 1)
                if all(y in growth and y in outcome for y in years):
                    f = o = 1.0
                    for y in years:
                        f *= 1 + growth[y] / 100
                        o *= 1 + outcome[y] / 100
                    levels.append({'circular': c['circular'], 'forecaster': row['forecaster'], 'years': n,
                                   'levelErrorPercent': round(100 * (f / o - 1), 2)})
    summary = []
    for who in FORECASTERS:
        for h in range(4):
            e = [r['errorPoints'] for r in errors if r['forecaster'] == who and r['yearsAhead'] == h]
            if e:
                summary.append({'forecaster': who, 'yearsAhead': h, 'forecasts': len(e),
                                'meanErrorPoints': round(sum(e) / len(e), 2),
                                'meanAbsErrorPoints': round(sum(abs(v) for v in e) / len(e), 2)})
    out = {'source': 'scripts/compare_tax_base_forecasters.py from research/data/tax-base-forecasters.json',
           'description': "Forecasts of Sweden's municipal tax base in SKR's December circulars 2020-2024 against the outcome "
                          f'(growth by income year, through {LAST_OUTCOME}). Error = forecast minus outcome, percentage points of growth.',
           'notes': source['notes'], 'summary': summary, 'levels': levels, 'errors': errors}
    (ROOT / 'data/tax-base-forecasters.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    print('years ahead     ' + ''.join(f'{h:>16}' for h in range(4)))
    for who in FORECASTERS:
        cells = [next((s for s in summary if s['forecaster'] == who and s['yearsAhead'] == h), None) for h in range(4)]
        print(f'{who:<16}' + ''.join(f"{'':>16}" if s is None else f"{s['meanErrorPoints']:+6.2f}/{s['meanAbsErrorPoints']:.2f} n={s['forecasts']}" .rjust(16) for s in cells))
    for n in (2, 3):
        print(f'level after {n} years:', {(r['circular'], r['forecaster']): r['levelErrorPercent'] for r in levels if r['years'] == n})


if __name__ == '__main__':
    main()
