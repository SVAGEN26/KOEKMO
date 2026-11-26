#!/usr/bin/env python3
"""Test the economy against what happened: one run per SKR December circular, 2020-2024.

    OMC=/path/to/omc python3 scripts/hindcast_vintages.py [code Package]

Without arguments: Motala, outcomes from its annual reports, written to data/vintage-hindcast-continuous.json.
With a municipality code and its Modelica package (scripts/prepare_municipality.py), for example
`0586 Mjolby`: outcomes from SCB's account summary (data/municipalities/<code>/base-years.json),
the municipality's adopted budget when recorded with a source, and older age shares from
the corresponding base year. Written to data/municipalities/<code>/vintage-hindcast-continuous.json.

Each run starts in the closing accounts of a base year (Motala.Data.motala<year>) and
simulates Motala.Continuous up to three years ahead, but not past 2025. Two sets of
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
  hold      as components, but the regulation grant stays at year one's amount per inhabitant.
  frame     as components, but the state's frame follows the nation's tax base, so the regulation
            grant per inhabitant grows from year one's with the circular's tax base per inhabitant:
            the model's rule for years the state has not decided (stateFrameFollowsTaxBase).
  prices    a diagnostic, not a forecast: as skr, but wages, pensions and other prices follow
            the PKV outcomes (SKR, October 2026). It shows how much of the cost error is the
            price forecast and how much is the model.
  hindsight a diagnostic, not a forecast: as prices, and the national tax base follows its
            outcome (SCB SkatteKraft; 2025 is SKR's estimate of October 2026, no outcome yet).
            The grants follow the state's decisions as they turned out: per component as booked
            (income, cost, regulation and LSS equalisation per inhabitant of the year before, the
            property fee and other general grants in mnkr). Only the municipality's population is
            the model's.
  standard  the model's standard growth rates (tax base 3.5 %, wages 3 %, prices 2 %,
            pensions following the payroll, grants 2 %), with the same population as above.

No set has cost growth beyond demography and prices (costDrift 0, the model's default);
scripts/hindcast_long.py shows that the historical mean of that residual made eight-year
forecasts worse.

Sweden's population after the base year comes from the circular, not from SCB's later
outcome. Motala's own population is the model's projection from the base year. In the skr,
components, hold and standard sets the inputs are what a budget revision in the spring after the
base year would have: the December circular, SCB's equalisation table of that December, and the
base year's closing accounts and Kolada figures. The prices and hindsight sets are diagnostics
that use outcomes on purpose.

Benchmark: persistence, the base year's result kept, scored at every horizon.

The outcome is the municipality's annual report (research/data/annual-ledgers.json).
The budget result is from research/benchmark/municipal-budget-history.json. SKR's own
forecasts of tax and grants for the municipality at the time are not part of this test: four
old workbooks (Prognosunderlag) were recovered from the Internet Archive and are read by
scripts/read_skr_vintages.py; scripts/explain_outcome.py shows them beside the model.
Writes data/vintage-hindcast-continuous.json.
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
CODE, PACKAGE = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1].isdigit() else ('0583', 'Motala')
# The package's Continuous model (Kommunekonomi.Continuous.Economy), the only model.
MODEL = 'Continuous'
SUFFIX = '-continuous'
PREFIX = PACKAGE.lower()
ORIGINS = range(2020, 2025)
OUTPUTS = ('annualFinancialIncome', 'tax', 'grants', 'grantParts[1]', 'grantParts[2]', 'grantParts[3]', 'grantParts[4]', 'grantParts[5]', 'grantParts[6]', 'cost', 'depreciation', 'interest', 'result', 'payroll', 'pensionExpense', 'otherOperatingExpense', 'operatingRevenue', 'population', 'debt', 'cash')
# Lines scored besides the result. Debt and cash depend on the financing rule as much as on the forecast.
LINES = ('payroll', 'pension', 'otherCosts', 'operatingRevenue', 'depreciation', 'interest', 'debt', 'cash')


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


def model_source(origin, horizon, v, assumptions, older_shares=None):
    n0, path = national_path(origin, horizon, v)
    years = [origin + i for i in range(1, horizon + 1)]
    lines = [f'base = {PACKAGE}.Data.{PREFIX}{origin}', f'horizon = {horizon}',
             f'nationalPopulation0 = {n0:.10g}', f'nationalPopulationPath = {modelica_array(path)}']
    if older_shares:
        lines.append(f'olderShares = {modelica_array(older_shares)}')
    if assumptions in ('prices', 'hindsight'):
        outcome = pkv_outcomes()
        v = {**v, 'labour': {y: outcome[y]['labour'] for y in years}, 'other': {y: outcome[y]['other'] for y in years}}
    if assumptions == 'hindsight':
        v = {**v, 'taxBase': tax_base_outcomes()}
    if assumptions in ('skr', 'components', 'hold', 'frame', 'prices', 'hindsight'):
        cum_tax, cum_labour, tax, pension = 1.0, 1.0, [], []
        for y in years:
            cum_tax *= 1 + v['taxBase'][y]
            cum_labour *= 1 + v['labour'][y]
            tax.append(cum_tax)
            pension.append(cum_labour)
        lines += [f'referenceTax = {modelica_array(tax)}*recurringTax0',
                  f'wageGrowthPath = {modelica_array([v["labour"][y] for y in years])}',
                  f'priceGrowthPath = {modelica_array([v["other"][y] for y in years])}',
                  # The pension cost follows the labour-cost index, as SKR's PKV does; the model's own rule (the payroll,
                  # with volume and productivity) is tested in the standard set.
                  f'pensionExpensePath = {modelica_array(pension)}*pension0', 'pensionFollowsPayroll = false']
    if assumptions in ('components', 'hold', 'frame'):
        regulation = [v['regulation'][y] for y in years]
        capacity = [v['capacity'][y] / v['capacity'][origin] for y in years]
        # Year one's equalisation is known from SCB in December of the base year (BaseYear.equalisationNextYear);
        # later years grow with the circular's mean tax capacity.
        lines += ['grantsByComponent = true',
                  f'incomeEqualisationPerCapitaPath = {modelica_array([c / capacity[0] for c in capacity])}*base.equalisationNextYear[1]']
        if assumptions == 'components':
            lines += [f'regulationPerCapitaPath = {modelica_array(regulation)}']
        if assumptions == 'hold':
            lines += ['stateFrameFollowsTaxBase = false']
    if assumptions == 'hindsight':
        # The state's grants as they turned out: each component as booked in year y, per inhabitant at the end of
        # y - 1 (the population the model multiplies by), so a mid-year decision is included.
        record = lambda y: f'{PACKAGE}.Data.{PREFIX}{y}'
        per_capita = lambda k: '{' + ', '.join(f'{record(y)}.grantComponents[{k}]*1e6/{record(y)}.reportedPopulation[2]' for y in years) + '}'
        lines += ['grantsByComponent = true',
                  f'incomeEqualisationPerCapitaPath = {per_capita(1)}',
                  f'relativeTaxCapacityPath = fill(base.relativeTaxCapacity[2], {horizon})',
                  f'costEqualisationPerCapitaPath = {per_capita(2)}',
                  f'regulationPerCapitaPath = {per_capita(3)}',
                  f'lssEqualisationPerCapitaPath = {per_capita(4)}',
                  'propertyFeePath = {' + ', '.join(f'{record(y)}.grantComponents[5]' for y in years) + '}',
                  'otherGeneralGrantsPath = {' + ', '.join(f'{record(y)}.grants - sum({record(y)}.grantComponents)' for y in years) + '}']
    return f'model Run\n  extends {PACKAGE}.{MODEL}(\n    ' + ',\n    '.join(lines) + ');\nend Run;\n'


def simulate(origin, horizon, source, directory):
    (directory / 'Run.mo').write_text(source)
    (directory / 'run.mos').write_text(
        f'loadFile({json.dumps(str(ROOT / "modelica/Kommunekonomi.mo"))}); getErrorString();\n'
        f'loadFile({json.dumps(str(ROOT / ("modelica/Motala.mo" if PACKAGE == "Motala" else f"modelica/municipalities/{PACKAGE}.mo")))}); getErrorString();\n'
        'loadFile("Run.mo"); getErrorString();\n'
        f'simulate(Run, startTime = {origin}, stopTime = {origin + horizon}, numberOfIntervals = {horizon * 12},'
        ' outputFormat = "csv"); getErrorString();\n')
    process = subprocess.run([OMC, 'run.mos'], cwd=directory, capture_output=True, text=True, timeout=600)
    result = directory / 'Run_res.csv'
    if not result.exists():
        raise SystemExit(f'Simulation failed for {origin}:\n{source}\n{process.stdout[-3000:]}')
    rows = {}
    for row in csv.DictReader(result.open()):
        t = float(row['time'])
        if abs(t - round(t)) < 1e-6:  # whole years only: in Continuous a row between year ends is mid-year
            rows[round(t)] = row  # the last row at each whole year is the post-event state
    return {year: {k: float(row[k]) for k in OUTPUTS} for year, row in rows.items() if year > origin}


def outcomes():
    """What happened, per year: the annual reports for Motala, SCB's account summary for the others."""
    regional_years = {}
    if CODE == '0583':
        ledgers = {r['year']: r for r in load('research/data/annual-ledgers.json')['rows']}
        ledger_sources = {k: v['url'] for k, v in load('research/data/annual-ledgers.json')['sources'].items()}
        budgets = {b['targetYear']: b for b in load('research/benchmark/municipal-budget-history.json')['budgets']
                   if b['stage'] == 'budget'}
    else:  # SCB's account summary, with the same definitions as the base years
        scb = load(f'data/municipalities/{CODE}/base-years.json')
        ledgers, ledger_sources, budgets = {}, {'scb': f"SCB räkenskapssammandrag ({scb['archive']})"}, {}
        supplemental = ROOT / f'data/municipalities/{CODE}/annual-report-inputs.json'
        if supplemental.exists():
            evidence = json.loads(supplemental.read_text())
            budgets = {int(year): {'value': amount, 'source': evidence['sources'].get(f'annual{year}')}
                       for year, amount in evidence.get('budgetResult', {}).items()}
        regional_years = {int(y): r for y, r in scb['years'].items()}
        for y, r in regional_years.items():
            net = r['payroll'] + r['pension'] + r['otherOperatingExpense'] - r['operatingRevenue'] + r['depreciation']
            ledgers[int(y)] = {'tax': r['tax'], 'grants': r['grants'], 'netCost': net, 'payroll': r['payroll'],
                               'pension': r['pension'], 'population': r['reportedPopulation'][-1], 'sourceId': 'scb',
                               'otherExpense': r['otherOperatingExpense'], 'operatingRevenue': r['operatingRevenue'],
                               'depreciation': r['depreciation'], 'interest': r['interestExpense'], 'debt': r['debt'], 'cash': r['cash'],
                               'investment': r['investment'], 'financialIncome': r['financialIncome'],
                               'financialExpense': r['interestExpense'] + r['otherFinancialExpense'],
                               'result': r['tax'] + r['grants'] - net + r['financialIncome'] - r['interestExpense'] - r['otherFinancialExpense']}
    return ledgers, ledger_sources, budgets, regional_years


def main():
    ledgers, ledger_sources, budgets, regional_years = outcomes()
    runs = []
    with tempfile.TemporaryDirectory(prefix='motala-vintage-') as tmp:
        for origin in ORIGINS:
            v = vintage(origin)
            horizon = min(3, LAST - origin)
            for assumptions in ('skr', 'components', 'hold', 'frame', 'prices', 'hindsight', 'standard'):
                directory = Path(tmp) / f'{origin}-{assumptions}'
                directory.mkdir()
                for year, m in simulate(origin, horizon, model_source(origin, horizon, v, assumptions, regional_years.get(origin, {}).get('olderShares')), directory).items():
                    o = ledgers[year]
                    runs.append({
                        'origin': origin, 'circular': v['circular'], 'published': v['published'],
                        'assumptions': assumptions, 'year': year, 'horizon': year - origin,
                        'model': {'tax': m['tax'], 'grants': m['grants'], 'netCost': m['cost'] + m['depreciation'],
                                  'personnel': m['payroll'] + m['pensionExpense'], 'result': m['result'],
                                  'population': m['population'], 'payroll': m['payroll'], 'pension': m['pensionExpense'],
                                  'otherCosts': m['otherOperatingExpense'], 'operatingRevenue': m['operatingRevenue'],
                                  'depreciation': m['depreciation'], 'interest': m['interest'], 'debt': m['debt'], 'cash': m['cash'],
                                  **({'grantParts': [m[f'grantParts[{j}]'] for j in range(1, 7)]} if assumptions in ('components', 'hold', 'frame', 'hindsight') else {})},
                        'outcome': {'tax': o['tax'], 'grants': o['grants'], 'netCost': o['netCost'],
                                    'personnel': o['payroll'] + o['pension'], 'result': o['result'],
                                    'population': o['population'], 'payroll': o.get('payroll'), 'pension': o.get('pension'),
                                    'otherCosts': o.get('otherExpense'), 'operatingRevenue': o.get('operatingRevenue'),
                                    'depreciation': o.get('depreciation'), 'interest': o.get('interest'), 'debt': o.get('debt'),
                                    'cash': o.get('cash'), 'source': ledger_sources[o['sourceId']]},
                        'budgetResult': budgets[year]['value'] if year in budgets and year - origin == 1 else None,
                        'budgetSource': budgets[year].get('source') if year in budgets and year - origin == 1 else None,
                        'persistenceResult': ledgers[origin]['result'],
                    })
    keys = ('tax', 'grants', 'netCost', 'result')
    summary = {}
    for assumptions in ('skr', 'components', 'hold', 'frame', 'prices', 'hindsight', 'standard'):
        for horizon in (1, 2, 3):
            cases = [r for r in runs if r['assumptions'] == assumptions and r['horizon'] == horizon]
            if cases:
                summary.setdefault(assumptions, {})[horizon] = {
                    'cases': len(cases),
                    **{f'{k}MeanError': sum(r['model'][k] - r['outcome'][k] for r in cases) / len(cases) for k in keys},
                    **{f'{k}MeanAbsError': sum(abs(r['model'][k] - r['outcome'][k]) for r in cases) / len(cases) for k in keys}}
                for k in LINES:
                    scored = [r for r in cases if r['outcome'].get(k) is not None]
                    if scored:
                        summary[assumptions][horizon][f'{k}MeanError'] = sum(r['model'][k] - r['outcome'][k] for r in scored) / len(scored)
                        summary[assumptions][horizon][f'{k}MeanAbsError'] = sum(abs(r['model'][k] - r['outcome'][k]) for r in scored) / len(scored)
    one = [r for r in runs if r['horizon'] == 1 and r['assumptions'] == 'skr']  # budget and persistence: once per origin
    with_budget = [r for r in one if r['budgetResult'] is not None]
    if with_budget:
        errors = [r['budgetResult'] - r['outcome']['result'] for r in with_budget]
        summary['budget'] = {1: {'cases': len(errors), 'resultMeanAbsError': sum(map(abs, errors)) / len(errors),
                                 'resultMeanError': sum(errors) / len(errors)}}
    # Persistence: the base year's result kept, scored at every horizon like the model.
    summary['persistence'] = {}
    for horizon in (1, 2, 3):
        cases = [r for r in runs if r['horizon'] == horizon and r['assumptions'] == 'skr']
        if cases:
            errors = [r['persistenceResult'] - r['outcome']['result'] for r in cases]
            summary['persistence'][horizon] = {'cases': len(cases), 'resultMeanAbsError': sum(map(abs, errors)) / len(errors),
                                               'resultMeanError': sum(errors) / len(errors)}
    out = {'municipality': CODE, 'source': f'Model {PACKAGE}.{MODEL}; outcomes from ' + ('Motala kommun annual reports (kommunen); ' if CODE == '0583' else 'SCB:s räkenskapssammandrag (kommunen); ') + \
                     
                     'SKR December circulars 20:57, 21:49, 22:54, 23:56 and 24:56',
           'method': __doc__.strip(),
           'units': 'mnkr; population in persons; netCost includes depreciation as in the annual report',
           'limitations': [
               'The base-year accounts were published in spring after the circular. The test uses the closing accounts '
               'and the December circular as the information set, as a budget revision in spring would.',
               'In the skr, prices and standard sets grants grow 2 % a year; hindsight has the grants as they turned out. '
               'The components set uses the circular\'s national figures per inhabitant; cost and LSS equalisation '
               'beyond the first year stay at the first forecast year\'s level.',
               *(['One-off items in the base year (for example an impairment of 12.1 mnkr in 2022) carry into the forecast. '
                  'The correction of the previous year\'s tax settlement is taken out of the base before growth is applied.',
                  'The 2023 annual report moved payroll tax on pensions from pension to payroll; personnel is compared as a total.',
                  'Fixed assets for 2020 and 2021 include work in progress, which those reports do not show separately.',
                  'The budget result is the adopted budget for the following year, set in November before the circular.',
                  'SKR\'s own forecast for Motala is not used here, only the national assumptions (see scripts/explain_outcome.py).']
                 if CODE == '0583' else
                 ['One-off items in the base year may carry into the forecast. '
                  'The correction of the previous year\'s tax settlement is taken out of the base before growth is applied.',
                  'Personnel is compared as a total. Fixed assets from SCB include work in progress.',
                  'The budget result is the adopted budget for the following year, set in November before the circular.',
                  'The test uses the published national SKR assumptions. Historical local SKR revenue paths are outside this test.'])],
           'summaryByHorizon': summary, 'runs': runs}
    (ROOT / (f'data/vintage-hindcast{SUFFIX}.json' if CODE == '0583' else f'data/municipalities/{CODE}/vintage-hindcast{SUFFIX}.json')).write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    print(f'{"origin":>6s} {"year":>4s} {"set":8s} {"tax":>13s} {"grants":>13s} {"net cost":>13s} {"result":>13s} {"budget":>6s}')
    for r in runs:
        cell = lambda k: f'{r["model"][k]:6.0f}/{r["outcome"][k]:6.0f}'
        b = '' if r['budgetResult'] is None else f'{r["budgetResult"]:6.0f}'
        print(f'{r["origin"]:6d} {r["year"]:4d} {r["assumptions"]:8s} {cell("tax")} {cell("grants")} {cell("netCost")} {cell("result")} {b}')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
