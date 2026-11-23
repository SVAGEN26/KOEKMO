#!/usr/bin/env python3
"""How much faster did net cost grow than prices and demographic need? The 13 municipalities in Östergötland.

    python3 scripts/cost_residual.py

Net cost excluding depreciation (SCB TAB6777: 030 minus 025) is deflated with SKR's price index
for municipal activities (PKV, outcomes 2009-2025, table of October 2026). Demographic need is
weighted like the model's sectors: education by ages 0-18, elderly care by 65-79 and 80+ with
the Kolada cost weights, the rest by the whole population, with the base year's sector shares.
The residual is real growth minus need growth: the part that is neither price nor demography
(standard, new tasks, efficiency, accounting changes). Writes data/cost-residual.json.

The residual is the history of the model's costDrift (cost growth beyond demography and prices),
whose default is 0. `knownBy` gives the mean over the years up to each base year;
scripts/hindcast_long.py tests it as a forecast (set drift) and finds it made costs too high. The weights are the 2025 ones for every year.

Years 2009-2016 come from data/downloads/*-history (scripts/fetch_history.py), 2017-2025 from each
municipality's archive (data/municipalities/<code>/base-years.json); Motala's accounts from the PKV
archive (1998-2025) and its population 2015-2025 from data/demography-inputs.json.

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
HISTORY = ROOT / json.loads((ROOT / 'data/municipalities/ostergotland-sources.json').read_text())['historyArchive']
NAMES = {'0509': 'Ödeshög', '0512': 'Ydre', '0513': 'Kinda', '0560': 'Boxholm', '0561': 'Åtvidaberg', '0562': 'Finspång',
         '0563': 'Valdemarsvik', '0580': 'Linköping', '0581': 'Norrköping', '0582': 'Söderköping', '0583': 'Motala',
         '0584': 'Vadstena', '0586': 'Mjölby'}
FIRST = 2010  # PKV starts in 2009, so real growth from 2010


def pkv():
    sheet = read_workbook(ARCHIVE / 'PKV-2610.xlsx')['PKV']
    columns = {int(c['value']): re.match(r'[A-Z]+', ref).group(0) for ref, c in sheet.items()
               if re.fullmatch(r'[A-Z]+4', ref) and isinstance(c['value'], float)}
    return {y: {'pkv': sheet[f'{c}9']['value'] / 100, 'labour': sheet[f'{c}5']['value'] / 100,
                'other': sheet[f'{c}7']['value'] / 100} for y, c in columns.items() if y <= 2025}


def ages(rows, out):
    for k, v in rows:
        a = 100 if k['Alder'].startswith('100') else int(k['Alder'])
        out.setdefault(int(k['Tid']), [0.0] * 101)[a] += v
    return out


def population(code):
    out = ages([(k, v) for k, v in px(HISTORY / 'population.json') if k['Region'] == code], {})
    if code == '0583':
        d = json.loads((ROOT / 'data/demography-inputs.json').read_text())['observed']['population']
        out.update({int(y): [a + b for a, b in zip(p['1'], p['2'])] for y, p in d.items()})
        return out
    archive = ROOT / json.loads((ROOT / f'data/municipalities/{code}/base-years.json').read_text())['archive']
    recent = {}
    for name in ('population-2017-2024', 'population-2025'):
        ages(px(archive / f'{name}.json'), recent)
    out.update(recent)
    return out


def net_cost(code):
    old = jsonstat(HISTORY / 'TAB6777.json', code)
    recent = jsonstat(ARCHIVE / 'TAB6777-0583.json') if code == '0583' else \
        jsonstat(ROOT / json.loads((ROOT / f'data/municipalities/{code}/base-years.json').read_text())['archive'] / 'TAB6777.json')
    accounts = {item: {**old.get(item, {}), **years} for item, years in recent.items()}
    net = {y: -accounts['030'][y] + accounts['025'][y] for y in accounts['030']}  # both negative in SCB's signs
    # One-offs the annual report marks as jämförelsestörande (positive = lowered the cost) go back in.
    for y, item in supplement(code).get('nonRecurring', {}).items():
        net[int(y)] += item.get('operating', 0.0)
    return net


def supplement(code):
    path = ROOT / f'data/municipalities/{code}/annual-report-inputs.json'
    return json.loads(path.read_text()) if path.exists() else {}


def main():
    prices = pkv()
    result = {'source': 'SKR PKV (oktober 2026) and SCB TAB6777 and BefolkningNy, CC BY 4.0; '
                        f'{ARCHIVE.relative_to(ROOT)}, {HISTORY.relative_to(ROOT)} and the municipal archives',
              'method': __doc__.split('\n\n', 1)[1].strip(), 'pkv': prices, 'municipalities': {}}
    for code, name in NAMES.items():
        folder = ROOT / ('data' if code == '0583' else f'data/municipalities/{code}')
        net = net_cost(code)
        pop = population(code)
        care = json.loads((folder / 'care-weights.json').read_text())['baseYears']['2025']['costPerInhabitant']
        shares = json.loads((folder / 'sector-costs.json').read_text())['years']['2025']['shares']

        def need(y):
            p = pop[y]
            return (sum(p[0:19]), sum(p[65:80]) * care['65-79'] + sum(p[80:]) * care['80+'], sum(p))
        rows = {}
        for y in range(FIRST, 2026):
            real = net[y] / net[y - 1] / (1 + prices[y]['pkv']) - 1
            a, b = need(y - 1), need(y)
            need_growth = sum(s * (b[i] / a[i] - 1) for i, s in enumerate((shares['education'], shares['elderly'], shares['other'])))
            rows[y] = {'netCost': net[y], 'nominalGrowth': net[y] / net[y - 1] - 1, 'pkv': prices[y]['pkv'],
                       'realGrowth': real, 'needGrowth': need_growth, 'residual': real - need_growth}
        # Years whose growth contains a one-off that is not split out (annual-report-inputs.json, trendExclude).
        excluded = set(supplement(code).get('trendExclude', []))
        residuals = {y: r['residual'] for y, r in rows.items() if y not in excluded}
        summary = {}
        for a, b in ((FIRST, 2019), (FIRST, 2025), (2016, 2025), (2020, 2025)):
            values = [r for y, r in residuals.items() if a <= y <= b]
            summary[f'{a}-{b}'] = {'mean': statistics.mean(values), 'median': statistics.median(values),
                                   'stdev': statistics.stdev(values), 'years': len(values)}
        known = {origin: statistics.mean(r for y, r in residuals.items() if y <= origin) for origin in range(2015, 2026)}
        result['municipalities'][code] = {'name': name, 'excludedYears': sorted(excluded), 'costDrift': summary[f'{FIRST}-2025']['mean'],
                                          'knownBy': known, 'years': rows, 'summary': summary}
        print(f"{name:13s} residual {FIRST}-2025: mean {100 * summary[f'{FIRST}-2025']['mean']:5.2f} %, "
              f"median {100 * summary[f'{FIRST}-2025']['median']:5.2f} %, sd {100 * summary[f'{FIRST}-2025']['stdev']:4.2f}; "
              f"2016-2025 mean {100 * summary['2016-2025']['mean']:5.2f} %; real growth mean "
              f"{100 * statistics.mean(r['realGrowth'] for r in rows.values()):4.2f} %")
    (ROOT / 'data/cost-residual.json').write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
