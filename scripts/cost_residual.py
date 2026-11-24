#!/usr/bin/env python3
"""How much faster did costs grow than prices and the model's service volume? The 13 municipalities in Östergötland.

    python3 scripts/cost_residual.py

The residual is measured on the basis the model applies costDrift to. The model multiplies payroll and
other operating expenses (gross, before operating revenue) by the cost standard; their volume follows the
service volume: per sector, capacity closes half the gap to 0.25 + 0.75 x demand each year (the model's
defaults adjustment 0.5 and fixedShare 0.25), and demand in year y is the need from the population at the
end of year y, as in Kommunekonomi.Annual. Operating revenue follows prices and the same population, not
the standard. The residual of a year is the costDrift that makes the model's net cost grow as the outcome did:

  net_y / (1 + PKV_y) = gross_{y-1} x volume growth x (1 + residual) - revenue_{y-1} x population growth

  gross cost   SCB TAB6777 item 022 (verksamhetens kostnader, without depreciation); revenue item 010; net
               cost their difference. One-offs the annual report marks as jämförelsestörande are added back
               (annual-report-inputs.json, nonRecurring). Pension costs are in 022; the model does not
               scale them (about 5-8 % of the item).
  PKV          SKR's price index for municipal activities (outcomes 2009-2025, table of October 2026).
  volume       the model's service volume from the population: education by ages 0-18, elderly care by
               65-79 and 80+ with the Kolada cost weights, the rest by the whole population, weighted with the
               sector shares.

`knownBy` gives the mean up to each base year, computed with the care weights and sector shares known
in that base year (the earliest there are when none are: `weightsFrom` says which). `costDrift` and the
summaries use the 2025 weights. The earlier measure on net cost with the full need (`netResidual`) is kept
for comparison. The model's default is 0: scripts/hindcast_long.py tests `knownBy` as a forecast (set drift).

Years 2009-2016 come from data/downloads/*-history (scripts/fetch_history.py), 2017-2025 from each
municipality's archive (data/municipalities/<code>/base-years.json); Motala's accounts from the PKV
archive (1998-2025) and its population 2015-2025 from data/demography-inputs.json. The capacity starts
at the need of 2009 and the residual is reported from 2011.

Until 2026-11-24 this script took the need and the population of the year before (end of y-1 for year y),
a year behind the model. scripts/response_test.py showed that the model's timing fits the accounts
better, and the script now follows the model.

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


FIXED_SHARE, ADJUSTMENT = 0.25, 0.5  # the model's defaults (Assumptions.fixedShare, adjustment)


def accounts(code):
    old = jsonstat(HISTORY / 'TAB6777.json', code)
    recent = jsonstat(ARCHIVE / 'TAB6777-0583.json') if code == '0583' else \
        jsonstat(ROOT / json.loads((ROOT / f'data/municipalities/{code}/base-years.json').read_text())['archive'] / 'TAB6777.json')
    table = {item: {**old.get(item, {}), **years} for item, years in recent.items()}
    net = {y: -table['030'][y] + table['025'][y] for y in table['030']}  # both negative in SCB's signs
    gross = {y: -table['022'][y] for y in table['022']}
    # One-offs the annual report marks as jämförelsestörande (positive = lowered the cost) go back in.
    for y, item in supplement(code).get('nonRecurring', {}).items():
        net[int(y)] += item.get('operating', 0.0)
        gross[int(y)] += item.get('operating', 0.0)
    return net, gross


def supplement(code):
    path = ROOT / f'data/municipalities/{code}/annual-report-inputs.json'
    return json.loads(path.read_text()) if path.exists() else {}


def weights(folder, year):
    """Care weights and sector shares known in a base year, or the earliest there are."""
    care = json.loads((folder / 'care-weights.json').read_text())['baseYears']
    sectors = json.loads((folder / 'sector-costs.json').read_text())['years']
    pick = lambda table: str(max((int(k) for k in table if int(k) <= year), default=min(int(k) for k in table)))
    c, s = pick(care), pick(sectors)
    return care[c]['costPerInhabitant'], sectors[s]['shares'], {'care': int(c), 'sectors': int(s)}


def series(pop, net, gross, prices, care, shares):
    def need(y):
        p = pop[y]
        return (sum(p[0:19]), sum(p[65:80]) * care['65-79'] + sum(p[80:]) * care['80+'], sum(p))
    share = (shares['education'], shares['elderly'], shares['other'])
    first = need(FIRST - 1)
    capacity = [FIXED_SHARE + (1 - FIXED_SHARE) * 1.0] * 3  # steady state with the population at the end of FIRST - 1
    volume = {}
    for y in range(FIRST, 2026):
        demand = [n / f for n, f in zip(need(y), first)]  # the need at the end of the year, as in Kommunekonomi.Annual
        capacity = [c + ADJUSTMENT * (FIXED_SHARE + (1 - FIXED_SHARE) * d - c) for c, d in zip(capacity, demand)]
        volume[y] = sum(s * c for s, c in zip(share, capacity))
    rows = {}
    for y in range(FIRST + 1, 2026):
        v, q = volume[y] / volume[y - 1], sum(pop[y]) / sum(pop[y - 1])
        revenue = gross[y - 1] - net[y - 1]
        # The model: net cost = gross x prices x volume x (1 + costDrift) - revenue x prices x population growth.
        # The drift that gives this year's net cost in real terms:
        drift = (net[y] / (1 + prices[y]['pkv']) + revenue * q) / (gross[y - 1] * v) - 1
        net_real = net[y] / net[y - 1] / (1 + prices[y]['pkv']) - 1
        a, b = need(y - 1), need(y)
        need_growth = sum(s * (b[i] / a[i] - 1) for i, s in enumerate(share))
        rows[y] = {'grossCost': gross[y], 'netCost': net[y], 'pkv': prices[y]['pkv'], 'volumeGrowth': v - 1,
                   'populationGrowth': q - 1, 'residual': drift,
                   'netRealGrowth': net_real, 'needGrowth': need_growth, 'netResidual': net_real - need_growth}
    return rows


def main():
    prices = pkv()
    result = {'source': 'SKR PKV (oktober 2026) and SCB TAB6777 and BefolkningNy, CC BY 4.0; '
                        f'{ARCHIVE.relative_to(ROOT)}, {HISTORY.relative_to(ROOT)} and the municipal archives',
              'method': __doc__.split('\n\n', 1)[1].strip(), 'pkv': prices, 'municipalities': {}}
    for code, name in NAMES.items():
        folder = ROOT / ('data' if code == '0583' else f'data/municipalities/{code}')
        net, gross = accounts(code)
        pop = population(code)
        # Years whose growth contains a one-off that is not split out (annual-report-inputs.json, trendExclude).
        excluded = set(supplement(code).get('trendExclude', []))
        rows = series(pop, net, gross, prices, *weights(folder, 2025)[:2])
        residuals = {y: r['residual'] for y, r in rows.items() if y not in excluded}
        summary = {}
        for a, b in ((FIRST + 1, 2019), (FIRST + 1, 2025), (2016, 2025), (2020, 2025)):
            values = [r for y, r in residuals.items() if a <= y <= b]
            net_values = [rows[y]['netResidual'] for y in residuals if a <= y <= b]
            summary[f'{a}-{b}'] = {'mean': statistics.mean(values), 'median': statistics.median(values),
                                   'stdev': statistics.stdev(values), 'years': len(values),
                                   'netResidualMean': statistics.mean(net_values)}
        known, weights_from = {}, {}
        for origin in range(2015, 2026):
            care, shares, used = weights(folder, origin)
            r = series(pop, net, gross, prices, care, shares)
            known[origin] = statistics.mean(r[y]['residual'] for y in r if y <= origin and y not in excluded)
            weights_from[origin] = used
        period = f'{FIRST + 1}-2025'
        result['municipalities'][code] = {'name': name, 'excludedYears': sorted(excluded), 'costDrift': summary[period]['mean'],
                                          'knownBy': known, 'weightsFrom': weights_from, 'years': rows, 'summary': summary}
        print(f"{name:13s} residual {period}: mean {100 * summary[period]['mean']:5.2f} %, "
              f"median {100 * summary[period]['median']:5.2f} %, sd {100 * summary[period]['stdev']:4.2f}; "
              f"on net cost {100 * summary[period]['netResidualMean']:5.2f} %; known by 2017/2019 "
              f"{100 * known[2017]:5.2f}/{100 * known[2019]:5.2f} %")
    (ROOT / 'data/cost-residual.json').write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
