#!/usr/bin/env python3
"""How far SKR's forecasts of tax and grants have been from the outcome, by years ahead.

    python3 scripts/prepare_revenue_uncertainty.py

Reads data/outcome-explanation-summary.json (scripts/explain_outcome.py --summary): for each of SKR's
recovered workbooks (Prognosunderlag 21:35, 22:28, 23:56 and 24:56) the error of the forecast tax and
general grants against SCB's outcome, per year, as a mean over the 13 municipalities. Years ahead is the
forecast year minus the year the workbook was published: 0 is the current year.

Writes data/revenue-uncertainty.json: per years ahead the number of workbooks, the mean error and the
mean absolute error in per cent. The page draws the mean absolute error as a band around tax and grants.
Four workbooks from one period, 2021-2025, with the inflation of 2022-2023: the band shows the size of
the errors then, not a probability.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    summary = json.loads((ROOT / 'data/outcome-explanation-summary.json').read_text())
    by = {}
    used = []
    for f in summary['taxAndGrantsForecasts']:
        if not f['forecast'].startswith('SKR '):
            continue
        published = int(f['published'][:4])
        used.append({'forecast': f['forecast'], 'published': f['published']})
        for r in f['rows']:
            by.setdefault(r['year'] - published, []).append(r)
    rows = [{'yearsAhead': h, 'forecasts': len(rs),
             'meanErrorPercent': round(sum(r['meanErrorPercent'] for r in rs) / len(rs), 2),
             'meanAbsErrorPercent': round(sum(r['meanAbsErrorPercent'] for r in rs) / len(rs), 2)}
            for h, rs in sorted(by.items())]
    out = {'source': 'scripts/prepare_revenue_uncertainty.py from data/outcome-explanation-summary.json',
           'description': "SKR's forecast of tax and general grants against SCB's outcome, 13 municipalities of Östergötland: "
                          'mean error (forecast minus outcome) and mean absolute error in per cent, by years ahead '
                          '(0 = the year the forecast was published).',
           'forecasts': used, 'outcomes': '2021-2025', 'byYearsAhead': rows,
           'note': 'Four forecasts from one period with high inflation; the errors are mostly negative (the forecast too low). '
                   'The longest horizon rests on one forecast. Not a probability.'}
    (ROOT / 'data/revenue-uncertainty.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    for r in rows:
        print(r)


if __name__ == '__main__':
    main()
