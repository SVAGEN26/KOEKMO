#!/usr/bin/env python3
"""Test the economy against what happened: one run per SKR December circular, 2020-2024.

    OMC=/path/to/omc python3 scripts/hindcast_vintages.py [code Package]

Without arguments: Motala, outcomes from its annual reports, written to data/vintage-hindcast.json.
With a municipality code and its Modelica package (scripts/prepare_municipality.py), for example
`0586 Mjolby`: outcomes from SCB's account summary (data/municipalities/<code>/base-years.json),
no budget comparison, written to data/municipalities/<code>/vintage-hindcast.json.

Each run starts in the closing accounts of a base year (Motala.Data.motala<year>) and
simulates Motala.Annual up to three years ahead, but not past 2025. Two sets of
assumptions are run from every base year:

  skr       what SKR's December circular of the base year said: national tax-base
            growth, the labour-cost index (payroll and pensions) and the price index
            for other costs, and Sweden's population. Grants still grow 2 % a year,
            because the circulars give no figure for Motala's grants.
  components  as skr, but the grants are computed per component (grantsByComponent). Year one's
            income, cost, regulation and LSS equalisation per inhabitant are SCB's, published in
            December of the base year; later income equalisation grows with the circular's mean
            tax capacity and follows the law's formula for the relative tax capacity; the
            regulation grant follows the circular; cost and LSS equalisation stay at year one's
            level; the property fee grows 3.5 % a year; other general grants stay as in the base year.
  hold      as components, but the regulation grant stays at year one's amount per inhabitant:
            the rule for years the state has not decided.
  prices    a diagnostic, not a forecast: as skr, but wages, pensions and other prices follow
            the PKV outcomes (SKR, October 2026). It shows how much of the cost error is the
            price forecast and how much is the model.
  hindsight a diagnostic, not a forecast: as prices, and the national tax base follows its
            outcome (SCB SkatteKraft; 2025 is SKR's estimate of October 2026, no outcome yet).
  standard  the model's standard growth rates (tax base 3.5 %, wages 3 %, prices 2 %,
            pensions 2 %, grants 2 %), with the same population as above.

Sweden's population after the base year comes from the circular, not from SCB's later
outcome. Motala's own population is the model's projection from the base year. Nothing
after the base year is used as input.

The outcome is the municipality's annual report (research/data/annual-ledgers.json).
The budget result is from research/benchmark/municipal-budget-history.json. SKR's own
forecast for Motala at the time is not available: the old municipal workbooks
(Prognosunderlag) are no longer on SKR's site. Writes data/vintage-hindcast.json.
"""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OMC = os.environ.get('OMC') or shutil.which('omc') or '/home/johti17/OpenModelicaWork/om-install/bin/omc'
LAST = 2025
CODE, PACKAGE = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ('0583', 'Motala')
PREFIX = PACKAGE.lower()
ORIGINS = range(2020, 2025)
OUTPUTS = ('tax', 'grants', 'grantParts[1]', 'grantParts[2]', 'grantParts[3]', 'grantParts[4]', 'grantParts[5]', 'grantParts[6]', 'cost', 'depreciation', 'interest', 'result', 'payroll', 'pensionExpense', 'population', 'debt')


def load(path):
    return json.loads((ROOT / path).read_text())


def pkv_outcomes():
    """PKV outcomes as extracted by scripts/cost_residual.py (SKR's workbook itself is not in git)."""
    return {int(y): v for y, v in load('data/cost-residual.json')['pkv'].items()}


def tax_base_outcomes():
    """Growth of Sweden's tax base by income year. SCB's year t is income year t-2."""
    t = load('data/downloads/20261109T162833Z/skatteunderlag-riket.json')
    level = {int(r['key'][1]) - 2: float(r['values'][0]) for r in t['data']}
    growth = {y: level[y] / level[y - 1] - 1 for y in level if y - 1 in level}
    growth.setdefault(2025, 0.03565)  # no outcome yet: SKR's estimate, prognosunderlag 2026-10-06, Blad 2 row 9
    return growth


def vintage(origin):
    tax = next(v for v in load('research/data/skr-tax-vintages.json')['vintages'] if v['originYear'] == origin)
    pkv = next(v for v in load('research/data/skr-pkv-vintages.json')['vintages'] if v['originYear'] == origin)
    rev = next(v for v in load('research/data/skr-revenue-vintages.json')['vintages'] if v['originYear'] == origin)
    assert tax['circular'] == pkv['circular'] == rev['circular']
    return {'circular': tax['circular'], 'published': tax['publicationDate'],
            'taxBase': {r['year']: r['taxBasePercent'] / 100 for r in tax['rows']},
            'labour': {r['year']: r['laborPercent'] / 100 for r in pkv['rows']},
            'other': {r['year']: r['otherPercent'] / 100 for r in pkv['rows']},
            'nationalNovember': {r['year']: r['nationalNovemberPopulation'] for r in rev['rows']},
            'capacity': {r['year']: r['skrMeanTaxCapacity'] for r in rev['rows']},
            'regulation': {r['year']: r['municipalRegulationPerCapita'] for r in rev['rows']},
            'sources': {'tax': tax['source'], 'taxLocator': tax['locator'], 'pkvLocator': pkv['locator'],
                        'populationLocator': rev['locators']['populationAndCapacity']}}


def national_path(origin, horizon, v):
    """Sweden at 31 December before each forecast year: SCB at the base year, then SKR's growth."""
    scb = load('data/national-population.json')
    observed = {int(y): p for y, p in scb['population'].items() if int(y) <= scb['lastOutcome']}
    n0, nb = observed[origin - 1], observed[origin]
    path = [nb * v['nationalNovember'][origin + i] / v['nationalNovember'][origin] for i in range(horizon)]
    return n0, path


def modelica_array(values):
    return '{' + ', '.join(f'{x:.10g}' for x in values) + '}'


def model_source(origin, horizon, v, assumptions):
    n0, path = national_path(origin, horizon, v)
    years = [origin + i for i in range(1, horizon + 1)]
    lines = [f'base = {PACKAGE}.Data.{PREFIX}{origin}', f'horizon = {horizon}',
             f'nationalPopulation0 = {n0:.10g}', f'nationalPopulationPath = {modelica_array(path)}']
    if assumptions in ('prices', 'hindsight'):
        outcome = pkv_outcomes()
        v = {**v, 'labour': {y: outcome[y]['labour'] for y in years}, 'other': {y: outcome[y]['other'] for y in years}}
    if assumptions == 'hindsight':
        v = {**v, 'taxBase': tax_base_outcomes()}
    if assumptions in ('skr', 'components', 'hold', 'prices', 'hindsight'):
        cum_tax, cum_labour, tax, pension = 1.0, 1.0, [], []
        for y in years:
            cum_tax *= 1 + v['taxBase'][y]
            cum_labour *= 1 + v['labour'][y]
            tax.append(cum_tax)
            pension.append(cum_labour)
        lines += [f'referenceTax = {modelica_array(tax)}*recurringTax0',
                  f'wageGrowthPath = {modelica_array([v["labour"][y] for y in years])}',
                  f'priceGrowthPath = {modelica_array([v["other"][y] for y in years])}',
                  f'pensionExpensePath = {modelica_array(pension)}*pension0']
    if assumptions in ('components', 'hold'):
        regulation = [v['regulation'][y] for y in years]
        capacity = [v['capacity'][y] / v['capacity'][origin] for y in years]
        # Year one's equalisation is known from SCB in December of the base year (BaseYear.equalisationNextYear);
        # later years grow with the circular's mean tax capacity.
        lines += ['grantsByComponent = true',
                  f'incomeEqualisationPerCapitaPath = {modelica_array([c / capacity[0] for c in capacity])}*base.equalisationNextYear[1]']
        if assumptions == 'components':
            lines += [f'regulationPerCapitaPath = {modelica_array(regulation)}']
    return f'model Run\n  extends {PACKAGE}.Annual(\n    ' + ',\n    '.join(lines) + ');\nend Run;\n'


def simulate(origin, horizon, source, directory):
    (directory / 'Run.mo').write_text(source)
    (directory / 'run.mos').write_text(
        f'loadFile({json.dumps(str(ROOT / "modelica/Kommunekonomi.mo"))}); getErrorString();\n'
        f'loadFile({json.dumps(str(ROOT / ("modelica/Motala.mo" if PACKAGE == "Motala" else f"modelica/municipalities/{PACKAGE}.mo")))}); getErrorString();\n'
        'loadFile("Run.mo"); getErrorString();\n'
        f'simulate(Run, startTime = {origin}, stopTime = {origin + horizon}, numberOfIntervals = {horizon},'
        ' outputFormat = "csv"); getErrorString();\n')
    process = subprocess.run([OMC, 'run.mos'], cwd=directory, capture_output=True, text=True, timeout=600)
    result = directory / 'Run_res.csv'
    if not result.exists():
        raise SystemExit(f'Simulation failed for {origin}:\n{source}\n{process.stdout[-3000:]}')
    rows = {}
    for row in csv.DictReader(result.open()):
        rows[round(float(row['time']))] = row  # the last row at each whole year is the post-event state
    return {year: {k: float(row[k]) for k in OUTPUTS} for year, row in rows.items() if year > origin}


def main():
    if CODE == '0583':
        ledgers = {r['year']: r for r in load('research/data/annual-ledgers.json')['rows']}
        ledger_sources = {k: v['url'] for k, v in load('research/data/annual-ledgers.json')['sources'].items()}
        budgets = {b['targetYear']: b for b in load('research/benchmark/municipal-budget-history.json')['budgets']
                   if b['stage'] == 'budget'}
    else:  # SCB's account summary, with the same definitions as the base years
        scb = load(f'data/municipalities/{CODE}/base-years.json')
        ledgers, ledger_sources, budgets = {}, {'scb': f"SCB räkenskapssammandrag ({scb['archive']})"}, {}
        for y, r in scb['years'].items():
            net = r['payroll'] + r['pension'] + r['otherOperatingExpense'] - r['operatingRevenue'] + r['depreciation']
            ledgers[int(y)] = {'tax': r['tax'], 'grants': r['grants'], 'netCost': net, 'payroll': r['payroll'],
                               'pension': r['pension'], 'population': r['reportedPopulation'][-1], 'sourceId': 'scb',
                               'result': r['tax'] + r['grants'] - net + r['financialIncome'] - r['interestExpense'] - r['otherFinancialExpense']}
    runs = []
    with tempfile.TemporaryDirectory(prefix='motala-vintage-') as tmp:
        for origin in ORIGINS:
            v = vintage(origin)
            horizon = min(3, LAST - origin)
            for assumptions in ('skr', 'components', 'hold', 'prices', 'hindsight', 'standard'):
                directory = Path(tmp) / f'{origin}-{assumptions}'
                directory.mkdir()
                for year, m in simulate(origin, horizon, model_source(origin, horizon, v, assumptions), directory).items():
                    o = ledgers[year]
                    runs.append({
                        'origin': origin, 'circular': v['circular'], 'published': v['published'],
                        'assumptions': assumptions, 'year': year, 'horizon': year - origin,
                        'model': {'tax': m['tax'], 'grants': m['grants'], 'netCost': m['cost'] + m['depreciation'],
                                  'personnel': m['payroll'] + m['pensionExpense'], 'result': m['result'],
                                  'population': m['population'],
                                  **({'grantParts': [m[f'grantParts[{j}]'] for j in range(1, 7)]} if assumptions in ('components', 'hold') else {})},
                        'outcome': {'tax': o['tax'], 'grants': o['grants'], 'netCost': o['netCost'],
                                    'personnel': o['payroll'] + o['pension'], 'result': o['result'],
                                    'population': o['population'], 'source': ledger_sources[o['sourceId']]},
                        'budgetResult': budgets[year]['value'] if year in budgets and year - origin == 1 else None,
                        'persistenceResult': ledgers[origin]['result'],
                    })
    keys = ('tax', 'grants', 'netCost', 'result')
    summary = {}
    for assumptions in ('skr', 'components', 'hold', 'prices', 'hindsight', 'standard'):
        for horizon in (1, 2, 3):
            cases = [r for r in runs if r['assumptions'] == assumptions and r['horizon'] == horizon]
            if cases:
                summary.setdefault(assumptions, {})[horizon] = {
                    'cases': len(cases),
                    **{f'{k}MeanError': sum(r['model'][k] - r['outcome'][k] for r in cases) / len(cases) for k in keys},
                    **{f'{k}MeanAbsError': sum(abs(r['model'][k] - r['outcome'][k]) for r in cases) / len(cases) for k in keys}}
    one = [r for r in runs if r['horizon'] == 1 and r['assumptions'] == 'skr']  # budget and persistence: once per origin
    if budgets:
        summary['budget'] = {1: {'cases': len(one), 'resultMeanAbsError': sum(abs(r['budgetResult'] - r['outcome']['result']) for r in one) / len(one),
                                 'resultMeanError': sum(r['budgetResult'] - r['outcome']['result'] for r in one) / len(one)}}
    summary['persistence'] = {1: {'cases': len(one), 'resultMeanAbsError': sum(abs(r['persistenceResult'] - r['outcome']['result']) for r in one) / len(one)}}
    out = {'municipality': CODE, 'source': f'Model {PACKAGE}.Annual; outcomes from ' + ('Motala kommun annual reports (kommunen); ' if CODE == '0583' else 'SCB:s räkenskapssammandrag (kommunen); ') + \
                     
                     'SKR December circulars 20:57, 21:49, 22:54, 23:56 and 24:56',
           'method': __doc__.strip(),
           'units': 'mnkr; population in persons; netCost includes depreciation as in the annual report',
           'limitations': [
               'The base-year accounts were published in spring after the circular. The test uses the closing accounts '
               'and the December circular as the information set, as a budget revision in spring would.',
               'In the skr and standard sets grants grow 2 % a year; the circulars have no Motala figure for grants. '
               'The components set uses the circular\'s national figures per inhabitant; cost and LSS equalisation '
               'for Motala are not in the circular and stay at the base year\'s level.',
               'One-off items in the base year (for example an impairment of 12.1 mnkr in 2022) carry into the forecast. '
               'The correction of the previous year\'s tax settlement is taken out of the base before growth is applied.',
               'The 2023 annual report moved payroll tax on pensions from pension to payroll; personnel is compared as a total.',
               'Fixed assets for 2020 and 2021 include work in progress, which those reports do not show separately.',
               'The budget result is the adopted budget for the following year, set in November before the circular.',
               'SKR forecast for Motala at the time is not available; only the national assumptions are.'],
           'summaryByHorizon': summary, 'runs': runs}
    (ROOT / ('data/vintage-hindcast.json' if CODE == '0583' else f'data/municipalities/{CODE}/vintage-hindcast.json')).write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    print(f'{"origin":>6s} {"year":>4s} {"set":8s} {"tax":>13s} {"grants":>13s} {"net cost":>13s} {"result":>13s} {"budget":>6s}')
    for r in runs:
        cell = lambda k: f'{r["model"][k]:6.0f}/{r["outcome"][k]:6.0f}'
        b = '' if r['budgetResult'] is None else f'{r["budgetResult"]:6.0f}'
        print(f'{r["origin"]:6d} {r["year"]:4d} {r["assumptions"]:8s} {cell("tax")} {cell("grants")} {cell("netCost")} {cell("result")} {b}')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
