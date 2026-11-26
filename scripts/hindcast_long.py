#!/usr/bin/env python3
"""Eight years ahead: the model from the accounts of 2017, 2018 and 2019 against SCB's outcomes to 2025.

    OMC=/path/to/omc python3 scripts/hindcast_long.py

The site shows eight years; scripts/hindcast_vintages.py reaches three, because SKR's
circulars are only collected from December 2020. This test runs the 13 municipalities in
Östergötland from base years 2017-2019 to 2025 (8, 7 and 6 years) and compares each year
with SCB's account summary (TAB6777, kommunen), with the definitions of
scripts/prepare_municipality.py. Motala too is compared with SCB here, built from SCB like the
others (package MotalaScb, written to a temporary folder), not from its annual reports.

There are no forecasts from those years in the project, so the assumption sets are:

  hindsight  a diagnostic of the model's structure, not a forecast. What happened to everything
             the model takes as given: national tax base (SCB SkatteKraft; 2025 SKR's estimate),
             wages, pensions and other prices (SKR's PKV outcomes), the state's grants per component
             as booked (as in hindcast_vintages.py), Sweden's population (SCB). No cost growth beyond
             demography and prices (costDrift 0, the model's default). The municipality's
             population, its costs, debt and result are the model's.
  drift      as hindsight, with costDrift the municipality's mean residual from 2011 to the base
             year, measured on the model's basis with the weights known then (data/cost-residual.json,
             knownBy): does the history of that residual help?
  standard   the model's standard rates (tax base 3.5 %, wages 3 %, prices 2 %, pensions following the payroll,
             grants 2 %), costDrift 0. Sweden's population is SCB's outcome, not a forecast of the
             time: no forecast from 2017-2019 is in the project.

No set is a forecast with only what was known in the base year. Besides the outcomes named above,
Boxholm's care weights for base years 2017 and 2018 are Kolada's 2019 ones (the earliest there are).

Benchmark: the base year's result as a share of tax and grants, kept. Its error in percent of tax and
grants is the base year's share minus the outcome's. A model that does not beat it after a few years
says little about the result that the base year did not.

Outcomes are scored without the years a municipality's annual report shows a one-off that is not split
out (annual-report-inputs.json, trendExclude): Norrköping 2022 and 2023, the provision for Ostlänken
(-3 281 and -80 mnkr). They stay in the runs with "excluded": true.

Investment stays at the base year's amount: the model has no investment forecast. Where the base
year gives no plausible interest rate (no debt at the start of the year: Linköping and
Vadstena 2017-2019), the run uses 2 %. The packages' Continuous model (Kommunekonomi.Continuous.Economy),
twelve output points a year. Writes data/long-hindcast-continuous.json.
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
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_municipality as pm  # noqa: E402
from hindcast_vintages import modelica_array, pkv_outcomes, tax_base_outcomes  # noqa: E402

OMC = os.environ.get('OMC') or shutil.which('omc') or '/home/johti17/OpenModelicaWork/om-install/bin/omc'
MODEL = 'Continuous'
STEPS = 12
OUTPUT = 'data/long-hindcast-continuous.json'
LAST = 2025
ORIGINS = (2017, 2018, 2019)
SETS = ('hindsight', 'drift', 'standard')
CODES = ['0509', '0512', '0513', '0560', '0561', '0562', '0563', '0580', '0581', '0582', '0583', '0584', '0586']
OUTPUTS = ('tax', 'grants', 'cost', 'depreciation', 'interest', 'result', 'population', 'debt')
LINES = ('result', 'tax', 'grants', 'netCost', 'population', 'interest', 'debt')
FALLBACK_RATE = 0.02


def load(path):
    return json.loads((ROOT / path).read_text())


def municipality(code, tmp):
    """Package name, Modelica file and SCB base years (with outcomes) for one municipality."""
    if code == '0583':
        archive = ROOT / load('data/municipalities/0583/base-years.json')['archive']
        years, older = pm.build(code, archive)
        for y in ORIGINS:
            if 'interestRate' not in years[y] and not plausible_rate(years[y]):
                years[y]['interestRate'] = FALLBACK_RATE
        path = tmp / 'MotalaScb.mo'
        path.write_text(pm.modelica('MotalaScb', 'Motala', code, archive.relative_to(ROOT), years, older))
        return 'MotalaScb', path, {int(y): r for y, r in years.items()}
    records = load(f'data/municipalities/{code}/base-years.json')
    package = records['packageName']
    years = {int(y): r for y, r in records['years'].items()}
    missing = [y for y in ORIGINS if 'interestRate' not in years[y] and not plausible_rate(years[y])]
    if not missing:
        return package, ROOT / f'modelica/municipalities/{package}/package.mo', years
    # The library asserts that the base year gives a rate; write the package again with the fallback in those years.
    for y in missing:
        years[y]['interestRate'] = FALLBACK_RATE
    path = tmp / f'{package}.mo'
    path.write_text(pm.modelica(package, records['name'], code, Path(records['archive']), years, records['olderShares']))
    print(f'{code}: interest rate {FALLBACK_RATE} in base years {missing}', flush=True)
    return package, path, years


def plausible_rate(r):
    return r['openingDebt'] > 0 and 0 <= r['interestExpense'] / r['openingDebt'] <= 0.1


def outcome(r):
    net = r['payroll'] + r['pension'] + r['otherOperatingExpense'] - r['operatingRevenue'] + r['depreciation']
    # The recurring result: one-offs the base year takes out (nonRecurring) are in otherOperatingExpense and
    # otherFinancialExpense already; extraordinary items are left out, as in the model.
    return {'tax': r['tax'], 'grants': r['grants'], 'netCost': net, 'population': r['reportedPopulation'][-1],
            'interest': r['interestExpense'], 'debt': r['debt'],
            'result': r['tax'] + r['grants'] - net + r['financialIncome'] - r['interestExpense'] - r['otherFinancialExpense']}


def model_source(package, code, origin, records, assumptions):
    horizon = LAST - origin
    years = list(range(origin + 1, LAST + 1))
    national = {int(y): p for y, p in load('data/national-population.json')['population'].items()}
    base = records[origin]
    record = lambda y: f'{package}.Data.{package.lower()}{y}'
    lines = [f'base = {record(origin)}', f'olderShares = {package}.Data.olderShares{origin}', f'horizon = {horizon}',
             f'nationalPopulation0 = {national[origin - 1]:.10g}',
             f'nationalPopulationPath = {modelica_array([national[y - 1] for y in years])}']
    if assumptions in ('hindsight', 'drift'):
        pkv, tax_base = pkv_outcomes(), tax_base_outcomes()
        cum_tax, cum_labour, tax, pension = 1.0, 1.0, [], []
        for y in years:
            cum_tax *= 1 + tax_base[y]
            cum_labour *= 1 + pkv[y]['labour']
            tax.append(cum_tax)
            pension.append(cum_labour)
        per_capita = lambda k: '{' + ', '.join(f'{record(y)}.grantComponents[{k}]*1e6/{record(y)}.reportedPopulation[2]' for y in years) + '}'
        drift = load('data/cost-residual.json')['municipalities'][code]['knownBy'][str(origin)] if assumptions == 'drift' else 0
        lines += [f'referenceTax = {modelica_array(tax)}*recurringTax0',
                  f'wageGrowthPath = {modelica_array([pkv[y]["labour"] for y in years])}',
                  f'priceGrowthPath = {modelica_array([pkv[y]["other"] for y in years])}',
                  f'pensionExpensePath = {modelica_array(pension)}*pension0', 'pensionFollowsPayroll = false',
                  f'costDrift = {drift:.6g}',
                  'grantsByComponent = true',
                  f'incomeEqualisationPerCapitaPath = {per_capita(1)}',
                  f'relativeTaxCapacityPath = fill(base.relativeTaxCapacity[2], {horizon})',
                  f'costEqualisationPerCapitaPath = {per_capita(2)}',
                  f'regulationPerCapitaPath = {per_capita(3)}',
                  f'lssEqualisationPerCapitaPath = {per_capita(4)}',
                  'propertyFeePath = {' + ', '.join(f'{record(y)}.grantComponents[5]' for y in years) + '}',
                  'otherGeneralGrantsPath = {' + ', '.join(f'{record(y)}.grants - sum({record(y)}.grantComponents)' for y in years) + '}']
    return f'model Run\n  extends {package}.{MODEL}(\n    ' + ',\n    '.join(lines) + ');\nend Run;\n'


def simulate(package_file, origin, source, directory):
    (directory / 'Run.mo').write_text(source)
    (directory / 'run.mos').write_text(
        f'loadFile({json.dumps(str(ROOT / "modelica/Kommunekonomi.mo"))}); getErrorString();\n'
        f'loadFile({json.dumps(str(package_file))}); getErrorString();\n'
        'loadFile("Run.mo"); getErrorString();\n'
        f'simulate(Run, startTime = {origin}, stopTime = {LAST}, numberOfIntervals = {(LAST - origin)*STEPS}, outputFormat = "csv"); getErrorString();\n')
    process = subprocess.run([OMC, 'run.mos'], cwd=directory, capture_output=True, text=True, timeout=600)
    result = directory / 'Run_res.csv'
    if not result.exists():
        raise SystemExit(f'Simulation failed for {origin}:\n{source}\n{process.stdout[-3000:]}')
    # Whole years only; the last row at a year end is the one after the year's events.
    rows = {round(float(row['time'])): row for row in csv.DictReader(result.open()) if abs(float(row['time']) - round(float(row['time']))) < 1e-6}
    if max(rows) < LAST:
        raise SystemExit(f'Simulation stopped before {LAST} for {origin}:\n{source}\n{process.stdout[-3000:]}')
    return {year: {k: float(row[k]) for k in OUTPUTS} for year, row in rows.items() if year > origin}


def excluded_years(code):
    path = ROOT / f'data/municipalities/{code}/annual-report-inputs.json'
    return set(json.loads(path.read_text()).get('trendExclude', [])) if path.exists() else set()


def simulate_all():
    runs = []
    with tempfile.TemporaryDirectory(prefix='long-hindcast-') as tmp:
        tmp = Path(tmp)
        for code in CODES:
            package, package_file, records = municipality(code, tmp)
            for origin in ORIGINS:
                for assumptions in SETS:
                    directory = tmp / f'{code}-{origin}-{assumptions}'
                    directory.mkdir()
                    for year, m in simulate(package_file, origin, model_source(package, code, origin, records, assumptions), directory).items():
                        runs.append({'municipality': code, 'origin': origin, 'assumptions': assumptions, 'year': year,
                                     'horizon': year - origin,
                                     'model': {'tax': m['tax'], 'grants': m['grants'], 'netCost': m['cost'] + m['depreciation'],
                                               'result': m['result'], 'population': m['population'], 'interest': m['interest'],
                                               'debt': m['debt']},
                                     'outcome': outcome(records[year]), 'baseYear': outcome(records[origin])})
            print(code, package, 'done', flush=True)
    return runs


def share(o):
    return o['result'] / (o['tax'] + o['grants'])


def main():
    if '--rescore' in sys.argv:
        runs = load(OUTPUT)['runs']  # score again without simulating
    else:
        runs = simulate_all()
    for r in runs:
        r['excluded'] = r['year'] in excluded_years(r['municipality'])
    summary = {}
    for assumptions in SETS:
        for horizon in range(1, LAST - min(ORIGINS) + 1):
            cases = [r for r in runs if r['assumptions'] == assumptions and r['horizon'] == horizon and not r['excluded']]
            row = {'cases': len(cases)}
            for k in LINES:
                errors = [r['model'][k] - r['outcome'][k] for r in cases]
                # Relative to the outcome's tax and grants, so small and large municipalities weigh alike.
                relative = [100 * (r['model'][k] - r['outcome'][k]) / (r['outcome']['tax'] + r['outcome']['grants'])
                            for r in cases] if k != 'population' else \
                    [100 * (r['model'][k] - r['outcome'][k]) / r['outcome'][k] for r in cases]
                row[k] = {'meanError': sum(errors) / len(errors), 'meanAbsError': sum(map(abs, errors)) / len(errors),
                          'meanErrorPercent': sum(relative) / len(relative),
                          'meanAbsErrorPercent': sum(map(abs, relative)) / len(relative)}
            summary.setdefault(assumptions, {})[horizon] = row
    for horizon in range(1, LAST - min(ORIGINS) + 1):
        cases = [r for r in runs if r['assumptions'] == SETS[0] and r['horizon'] == horizon and not r['excluded']]
        errors = [100 * (share(r['baseYear']) - share(r['outcome'])) for r in cases]
        summary.setdefault('persistence', {})[horizon] = {'cases': len(cases), 'result': {
            'meanErrorPercent': sum(errors) / len(errors), 'meanAbsErrorPercent': sum(map(abs, errors)) / len(errors)}}
    out = {'source': f'Model Kommunekonomi.Continuous.Economy with SCB base years; outcomes SCB räkenskapssammandrag (kommunen), '
                     'data/municipalities/<code>/base-years.json; Motala from data/downloads/20261109T162149Z',
           'method': __doc__.strip(),
           'units': 'mnkr; population in persons. Percent: error / outcome of tax and grants (population: / outcome)',
           'summaryByHorizon': summary, 'runs': runs}
    (ROOT / OUTPUT).write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    print('\npersistence (base year\'s result share kept): result, mean error / mean absolute error, percent')
    for horizon, row in summary['persistence'].items():
        print(f'{horizon:2d} {row["cases"]:3d} {row["result"]["meanErrorPercent"]:7.2f} /{row["result"]["meanAbsErrorPercent"]:6.2f}')
    for assumptions in SETS:
        print(f'\n{assumptions}: mean error / mean absolute error, percent of tax and grants (population: percent)')
        print(f'{"h":>2s} {"n":>3s} ' + ' '.join(f'{k:>16s}' for k in LINES))
        for horizon, row in summary[assumptions].items():
            print(f'{horizon:2d} {row["cases"]:3d} ' + ' '.join(
                f'{row[k]["meanErrorPercent"]:7.2f} /{row[k]["meanAbsErrorPercent"]:6.2f}' for k in LINES))


if __name__ == '__main__':
    main()
