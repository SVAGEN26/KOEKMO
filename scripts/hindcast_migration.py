#!/usr/bin/env python3
"""How many years should the migration calibration look back? A test against SCB's population, 13 municipalities.

    python3 scripts/hindcast_migration.py

The five-group demography (Kommunekonomi.Components.Demography, the page's yearly model) moves people by
births, deaths, ageing and a residual flow per age group: migration and statistical adjustments. The residual
is calibrated as the mean of the last years' residuals before the base year; the library and the page use
two years. Base years 2015-2017 (the large refugee immigration) gave a population 6 % too high after eight
years in scripts/hindcast_long.py.

This script repeats the demography in Python, from every base year 2012-2024 to 2025, with windows of 1, 2,
3, 5 and 8 years, and compares the total population and the five groups with SCB. Only data up to the base
year are used. The rule is the model's: death rates from the base year (four fixed, 65+ from the year's
deaths), births in proportion to the 19-64 group, ageing by the groups' widths. Its two-year window is
checked against the model's own population in data/long-hindcast.json.

The births are the model's (births per adult kept from the base year); a second set uses SCB's births, to
separate the error from falling fertility. data/migration-hindcast.json has the mean error and mean absolute
error per window and horizon for base years 2017-2024 and 2020-2024, the error in 2025 per base year, and
the yearly residual flow each window gives from the 2025 accounts.
"""
import json
import statistics as st
from pathlib import Path

from prepare_municipality import groups, px

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = (1, 2, 3, 5, 8)
FIRST_BASE, LAST = 2012, 2025
WIDTH = (7, 9, 3, 46)
YOUNG = (0.0004, 0.0001, 0.0002, 0.0018)


def series(code):
    """Five groups at each year's end, births and deaths per year, 2009-2025."""
    sources = json.loads((ROOT / 'data/municipalities/ostergotland-sources.json').read_text())
    history = ROOT / sources['historyArchive']
    folder = 'data' if code == '0583' else f'data/municipalities/{code}'
    archive = ROOT / json.loads((ROOT / f'data/municipalities/{code}/base-years.json').read_text())['archive']
    ages, changes = {}, {}
    files = [history / 'population.json', archive / 'population-2017-2024.json', archive / 'population-2025.json']
    for path in files:
        for k, v in px(path):
            if k['Region'] != code:
                continue
            a = 100 if k['Alder'].startswith('100') else int(k['Alder'])
            ages.setdefault(int(k['Tid']), [0.0] * 101)[a] += v
    for path in (history / 'changes.json', archive / 'changes-2017-2024.json', archive / 'changes-2025.json'):
        for k, v in px(path):
            if k['Region'] == code and k['Forandringar'] in ('115', '130'):
                changes.setdefault(int(k['Tid']), {})[{'115': 'births', '130': 'deaths'}[k['Forandringar']]] = v
    return {y: groups(a) for y, a in ages.items()}, changes


def death_rates(p, deaths):
    return [*YOUNG, (deaths - sum(x * d for x, d in zip(p[:4], YOUNG))) / p[4]]


def step(p, births, rates, residual):
    survivors = [x * (1 - d) for x, d in zip(p, rates)]
    out = [s / w for s, w in zip(survivors[:4], WIDTH)] + [0.0]
    return [survivors[i] - out[i] + (births if i == 0 else out[i - 1]) + residual[i] for i in range(5)]


def residual(pop, changes, base, window, rates):
    years = range(base - window + 1, base + 1)
    flows = [[a - b for a, b in zip(pop[y], step(pop[y - 1], changes[y]['births'], rates, [0] * 5))] for y in years]
    return [sum(f[i] for f in flows) / window for i in range(5)]


def project(pop, changes, base, window, observed_births=False):
    """Population at each year end from the base year to 2025. observed_births: a diagnostic with SCB's births."""
    rates = death_rates(pop[base], changes[base]['deaths'])
    flow = residual(pop, changes, base, window, rates)
    p, births0, adults0, out = pop[base], changes[base]['births'], pop[base][3], {}
    for y in range(base + 1, LAST + 1):
        births = changes[y]['births'] if observed_births else births0 * p[3] / adults0
        p = step(p, births, rates, flow)
        out[y] = p
    return out, flow


def errors(data, window, bases, observed_births=False):
    rows = []
    for code, (pop, changes) in data.items():
        for base in bases:
            projected, _ = project(pop, changes, base, window, observed_births)
            for y, p in projected.items():
                rows.append({'municipality': code, 'base': base, 'horizon': y - base,
                             'total': 100 * (sum(p) - sum(pop[y])) / sum(pop[y]),
                             'groups': [100 * (a - b) / b for a, b in zip(p, pop[y])]})
    out = {}
    for h in sorted({r['horizon'] for r in rows}):
        sel = [r for r in rows if r['horizon'] == h]
        out[str(h)] = {'cases': len(sel), 'meanError': round(st.mean(r['total'] for r in sel), 3),
                       'meanAbsError': round(st.mean(abs(r['total']) for r in sel), 3),
                       'groupsMeanError': [round(st.mean(r['groups'][i] for r in sel), 2) for i in range(5)]}
    return out


def main():
    codes = sorted(p.parent.name for p in (ROOT / 'data/municipalities').glob('*/base-years.json'))
    data = {code: series(code) for code in codes}
    periods = {'bases2017to2024': range(2017, LAST), 'bases2020to2024': range(2020, LAST)}
    summary = {name: {mode: {str(w): errors(data, w, bases, mode == 'observedBirths') for w in WINDOWS}
                      for mode in ('modelBirths', 'observedBirths')} for name, bases in periods.items()}
    by_base = {str(base): {str(w): round(st.mean(100 * (sum(project(pop, ch, base, w)[0][LAST]) - sum(pop[LAST])) / sum(pop[LAST])
                                                for pop, ch in data.values()), 3)
                           for w in WINDOWS if base - w >= min(min(pop) for pop, _ in data.values())}
               for base in range(FIRST_BASE, LAST)}
    flows = {}
    for code, (pop, changes) in data.items():
        rates = death_rates(pop[LAST], changes[LAST]['deaths'])
        flows[code] = {'population': round(sum(pop[LAST])), **{str(w): round(sum(residual(pop, changes, LAST, w, rates)), 1) for w in WINDOWS}}
    out = {'source': 'SCB, Statistikdatabasen (CC BY 4.0): folkmängd per ålder, födda och döda, 2009-2025',
           'method': __doc__.split('\n\n', 2)[2].strip(),
           'unit': 'procent av utfallet; grupper 0-6, 7-15, 16-18, 19-64, 65+; flöden i personer per år',
           'windows': list(WINDOWS), 'summary': summary,
           'errorIn2025ByBaseYear': by_base, 'residualFlowFrom2025': flows}
    (ROOT / 'data/migration-hindcast.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    for name in periods:
        print(name, '(model births): mean error / mean absolute error, % of the population')
        for w in WINDOWS:
            s = summary[name]['modelBirths'][str(w)]
            print(f'  window {w}: ' + '  '.join(f"{h}: {v['meanError']:+.1f}/{v['meanAbsError']:.1f}" for h, v in s.items()))


if __name__ == '__main__':
    main()
