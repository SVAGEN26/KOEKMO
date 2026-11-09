#!/usr/bin/env python3
"""How much faster did net cost grow than prices and demographic need? Motala and Mjölby.

    python3 scripts/cost_residual.py

Net cost excluding depreciation (SCB TAB6777: 030 minus 025) is deflated with SKR's price index
for municipal activities (PKV, outcomes 2009-2025, table of October 2026). Demographic need is
weighted like the model's sectors: education by ages 0-18, elderly care by 65-79 and 80+ with
the Kolada cost weights, the rest by the whole population, with the base year's sector shares.
The residual is real growth minus need growth: the part that is neither price nor demography
(standard, new tasks, efficiency, accounting changes). Writes data/cost-residual.json.

SKR's workbook is not redistributed (.gitignore). Download PKV-2610.xlsx into the archive folder from
the URL in its manifest.json and check its SHA-256; data/cost-residual.json keeps the index values.
"""
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from import_skr import read_workbook  # noqa: E402
from prepare_municipality import jsonstat, px  # noqa: E402

ARCHIVE = ROOT / 'data/downloads/20261109T162833Z'
MUNICIPALITIES = {
    '0583': {'name': 'Motala', 'population': 'motala', 'care': ROOT / 'data/care-weights.json',
             'sectors': ROOT / 'data/sector-costs.json'},
    '0586': {'name': 'Mjölby', 'population': 'data/downloads/20261109T162208Z',
             'care': ROOT / 'data/municipalities/0586/care-weights.json', 'sectors': ROOT / 'data/municipalities/0586/sector-costs.json'},
}


def pkv():
    sheet = read_workbook(ARCHIVE / 'PKV-2610.xlsx')['PKV']
    columns = {int(c['value']): re.match(r'[A-Z]+', ref).group(0) for ref, c in sheet.items()
               if re.fullmatch(r'[A-Z]+4', ref) and isinstance(c['value'], float)}
    return {y: {'pkv': sheet[f'{c}9']['value'] / 100, 'labour': sheet[f'{c}5']['value'] / 100,
                'other': sheet[f'{c}7']['value'] / 100} for y, c in columns.items() if y <= 2025}


def population(source):
    if source == 'motala':
        d = json.loads((ROOT / 'data/demography-inputs.json').read_text())['observed']['population']
        return {int(y): [a + b for a, b in zip(p['1'], p['2'])] for y, p in d.items()}
    out = {}
    for name in ('population-2017-2024', 'population-2025'):
        for k, v in px(ROOT / source / f'{name}.json'):
            a = 100 if k['Alder'].startswith('100') else int(k['Alder'])
            out.setdefault(int(k['Tid']), [0.0] * 101)[a] += v
    return out


def main():
    prices = pkv()
    result = {'source': 'SKR PKV (oktober 2026) and SCB TAB6777, CC BY 4.0; ' + str(ARCHIVE.relative_to(ROOT)),
              'method': __doc__.split('\n\n', 1)[1].strip(), 'pkv': prices, 'municipalities': {}}
    for code, m in MUNICIPALITIES.items():
        accounts = jsonstat(ARCHIVE / f'TAB6777-{code}.json')
        net = {y: -accounts['030'][y] + accounts['025'][y] for y in accounts['030']}  # both negative in SCB's signs
        pop = population(m['population'])
        care = json.loads(m['care'].read_text())['baseYears']['2025']['costPerInhabitant']
        shares = json.loads(m['sectors'].read_text())['years']['2025']['shares']

        def need(y):
            p = pop[y]
            return (sum(p[0:19]), sum(p[65:80]) * care['65-79'] + sum(p[80:]) * care['80+'], sum(p))
        rows = {}
        for y in range(2010, 2026):
            real = net[y] / net[y - 1] / (1 + prices[y]['pkv']) - 1
            row = {'netCost': net[y], 'nominalGrowth': net[y] / net[y - 1] - 1, 'pkv': prices[y]['pkv'], 'realGrowth': real}
            if y - 1 in pop and y in pop:
                a, b = need(y - 1), need(y)
                row['needGrowth'] = sum(s * (b[i] / a[i] - 1) for i, s in enumerate((shares['education'], shares['elderly'], shares['other'])))
                row['residual'] = real - row['needGrowth']
            rows[y] = row
        residuals = {y: r['residual'] for y, r in rows.items() if 'residual' in r}
        periods = {}
        for a, b in ((min(residuals), 2019), (min(residuals), 2025), (2020, 2025)):
            values = [r for y, r in residuals.items() if a <= y <= b]
            periods[f'{a}-{b}'] = {'mean': statistics.mean(values), 'median': statistics.median(values), 'years': len(values)}
        real_all = [rows[y]['realGrowth'] for y in range(2011, 2026)]
        periods['realGrowth 2011-2025'] = {'mean': statistics.mean(real_all), 'median': statistics.median(real_all), 'years': 15}
        result['municipalities'][code] = {'name': m['name'], 'years': rows, 'summary': periods}
        print(m['name'])
        for y, r in rows.items():
            print(f"  {y} net {r['netCost']:7.0f} nominal {100 * r['nominalGrowth']:5.1f} PKV {100 * r['pkv']:4.1f} real {100 * r['realGrowth']:5.1f}"
                  + (f" need {100 * r['needGrowth']:5.2f} residual {100 * r['residual']:5.2f}" if 'residual' in r else ''))
        for k, v in periods.items():
            print(f"  {k}: mean {100 * v['mean']:.2f} %, median {100 * v['median']:.2f} % ({v['years']} years)")
    (ROOT / 'data/cost-residual.json').write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
