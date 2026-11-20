#!/usr/bin/env python3
"""Compare the three production Modelica demographic variants with observed age counts.

Run with python3 scripts/hindcast_county_ages.py. Set OMC if OpenModelica is not on PATH.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
from statistics import mean
import subprocess
import tempfile

from prepare_county_cohorts import county_cohorts
from prepare_demography import ROOT, by_age, load
from prepare_model_experiments import migration_cells, migration_inputs
from write_demography_modelica import cohort_records

BASES = (2022, 2023, 2024)
LAST = 2025
MODES = ('groups', 'cohort', 'observed')
METRICS = ('population', 'age7to15', 'age80to89', 'age90Plus')


def read(path):
    return json.loads((ROOT / path).read_text())


def archived_bytes(archive, filename):
    manifest = read(archive / 'manifest.json')
    entry = next(item for item in manifest['files'] if item['file'] == filename)
    raw = (ROOT / archive / filename).read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry['sha256']:
        raise ValueError(f'{archive / filename} does not match its manifest')
    return raw


def actual_2025(archive):
    table = load(ROOT / archive, 'population-2025', read(archive / 'manifest.json'))[0]
    cells = {(row['Region'], row['Alder']): int(row['value']) for row in table}
    return {
        code: {
            'population': cells[code, 'TotSA'],
            'age7to15': sum(cells[code, str(a)] for a in range(7, 16)),
            'age80to89': cells[code, '80-89'],
            'age90Plus': cells[code, '90-99'] + cells[code, '100+10'],
        }
        for code, age in cells if age == 'TotSA'
    }


def actual_before_2025(archive):
    populations = by_age(load(ROOT / archive, 'population-2017-2024', read(archive / 'manifest.json'))[0])
    outcomes = {}
    for year in range(BASES[0] + 1, LAST):
        counts = [x + y for x, y in zip(populations[year]['1'], populations[year]['2'], strict=True)]
        outcomes[year] = dict(zip(METRICS, (
            sum(counts), sum(counts[7:16]), sum(counts[80:90]), sum(counts[90:])
        ), strict=True))
    return outcomes


def literal(value):
    if isinstance(value, list):
        return '{' + ','.join(map(literal, value)) + '}'
    return repr(value)


def case_source(package, cohort_package, base, observed):
    book = f'{package}.Data.{package.lower()}{base}'
    demography = f'{cohort_package}.{package.lower()}{base}'
    cohort_args = f"""data = {demography}, reportedTotal = sum(p0),
      migrationWeights = weights,
      redeclare Kommunekonomi.Components.Fertility.Constant fertility(
        totalFertility = {demography}.totalFertilityMean5,
        profile = Kommunekonomi.Data.SCB.historicalFertilityProfile[{base - 2020}, :])"""
    metrics = ',\n      '.join(
        f'{{{mode}.population, {mode}.cohorts.p[2], {mode}.cohorts.older[2], {mode}.cohorts.older[3]}}'
        for mode in MODES
    )
    # Match the web's historical calibration and scenario defaults, using standalone demography components.
    return f"""
  model Case{base}
    import Data = Kommunekonomi.Data;
    import Components = Kommunekonomi.Components;
    inner Components.Calendar calendar(baseYear = {base}, horizon = {LAST - base});
    parameter Data.BaseYear book = {book};
    parameter Real p0[5] = Data.reconcile(book.cohorts[3, :], book.reportedPopulation[3]);
    parameter Real deaths[5] = Data.mortality(p0, book.deaths);
    parameter Real weights[5] = {{0.15,0.12,0.03,0.65,0.05}};
    Components.Demography groups(p0 = p0, births0 = book.births[2], deathRates = deaths,
      migrationWeights = weights, olderShares = Data.SCB.olderShares({demography}.population));
    Components.CohortDemography cohort({cohort_args});
    Components.CohortDemography observed({cohort_args},
      residualMigration = {literal(observed['netMigration'])});
    output Real metrics[3,4] = {{{metrics}}};
  equation
    groups.drivers.residualMigration = Data.calibratedMigration(
      book.cohorts, book.reportedPopulation, book.births, deaths);
    cohort.drivers.residualMigration = zeros(5);
    observed.drivers.residualMigration = zeros(5);
    groups.drivers.birthChange = 0;
    cohort.drivers.birthChange = 0;
    observed.drivers.birthChange = 0;
    groups.drivers.migrationDelta = 0;
    cohort.drivers.migrationDelta = 0;
    observed.drivers.migrationDelta = 0;
  end Case{base};
"""


def simulate(book_path, migration, outcomes, directory, omc):
    records = read(book_path)
    code, name, package = (records[key] for key in ('municipality', 'name', 'packageName'))
    archive = Path(records['archive'])
    actuals = {**actual_before_2025(archive), 2025: outcomes[code]}
    is_motala = code == '0583'
    package_path = ROOT / 'modelica' / (f'{package}.mo' if is_motala else f'municipalities/{package}.mo')
    county_package = ''
    if not is_motala:
        years = {int(y): row for y, row in records['years'].items()}
        calibrated = county_cohorts(code, ROOT / archive, years, BASES)
        constants = '\n'.join(cohort_records(name, package.lower(), calibrated))
        county_package = f'''
  package Inputs
    import Kommunekonomi.Data.SCB.DemographyYear;
{constants}
  end Inputs;
'''
    cohort_package = f'{package}.Data.SCB' if is_motala else 'Run.Inputs'
    cases = '\n'.join(case_source(package, cohort_package, base,
                                 migration_inputs(migration, code, list(range(base - 2, base + 1))))
                      for base in BASES)
    instances = '\n'.join(f'  Case{base} base{base};' for base in BASES)
    (directory / 'Run.mo').write_text(f'model Run\n{county_package}{cases}{instances}\nend Run;\n')
    (directory / 'run.mos').write_text(
        f'loadFile({json.dumps(str(ROOT / "modelica/Kommunekonomi.mo"))}); getErrorString();\n'
        f'loadFile({json.dumps(str(package_path))}); getErrorString();\n'
        'loadFile("Run.mo"); getErrorString();\n'
        f'simulate(Run, startTime = {BASES[0]}, stopTime = {LAST}, numberOfIntervals = {LAST - BASES[0]},'
        ' method = "euler", outputFormat = "csv", variableFilter = "base.*metrics.*"); getErrorString();\n'
    )
    result = subprocess.run([omc, 'run.mos'], cwd=directory, capture_output=True, text=True, timeout=600)
    output = directory / 'Run_res.csv'
    if result.returncode or not output.exists() or 'simulation finished successfully' not in result.stdout:
        raise RuntimeError(f'{code} simulation failed:\n{result.stdout[-4000:]}\n{result.stderr[-2000:]}')
    with output.open() as source:
        rows = {round(float(row['time'])): row for row in csv.DictReader(source)
                if abs(float(row['time']) - round(float(row['time']))) < 1e-8}
    return [
        {'municipality': code, 'name': name, 'base': base, 'year': year, 'actual': actuals[year],
         'model': {mode: {metric: float(rows[year][f'base{base}.metrics[{i},{j}]'])
                          for j, metric in enumerate(METRICS, 1)}
                   for i, mode in enumerate(MODES, 1)}}
        for base in BASES for year in range(base + 1, LAST + 1)
    ]


def scores(rows):
    return {mode: {metric: {
        'mae': mean(abs(row['model'][mode][metric] - row['actual'][metric]) for row in rows),
        'bias': mean(row['model'][mode][metric] - row['actual'][metric] for row in rows),
    } for metric in METRICS} for mode in MODES}


def cross_check(runs, archive):
    raw = json.loads(archived_bytes(archive, 'kolada-comparison.json'))
    published = {(r['municipality'], r['period'], r['kpi']):
                 next(v['value'] for v in r['values'] if v['gender'] == 'T') for r in raw['values']}
    results = []
    for code, year in sorted({(r['municipality'], r['year']) for r in runs}):
        actual = next(r['actual'] for r in runs if r['municipality'] == code and r['year'] == year)
        total = published[code, year, 'N01951']
        older = published[code, year, 'N01957']
        results.append({'municipality': code, 'year': year, 'koladaPopulation': total, 'kolada80Plus': older,
                        'populationScbMinusKolada': actual['population'] - total,
                        'age80PlusScbMinusKolada': actual['age80to89'] + actual['age90Plus'] - older})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--municipality', help='Run only this municipality for diagnostics')
    args = parser.parse_args()
    omc = os.environ.get('OMC') or shutil.which('omc')
    if not omc:
        parser.error('OpenModelica missing. Set OMC to the executable.')
    sources = read(Path('data/municipalities/ostergotland-sources.json'))
    archive = Path(sources['ageBacktestArchive'])
    recent = Path(sources['migrationArchive'])
    migration = {
        **migration_cells(archived_bytes(archive, 'migration-2020-2021.json')),
        **migration_cells(archived_bytes(recent, 'migration.json')),
    }
    outcomes = actual_2025(archive)
    books = sorted((ROOT / 'data/municipalities').glob('0*/base-years.json'))
    if args.municipality:
        books = [p for p in books if p.parent.name == args.municipality]
        if not books:
            parser.error('Unknown municipality')
    with tempfile.TemporaryDirectory(prefix='county-ages-') as tmp:
        def one(book):
            directory = Path(tmp) / book.parent.name
            directory.mkdir()
            result = simulate(book, migration, outcomes, directory, omc)
            print(f'{book.parent.name} complete', flush=True)
            return result

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            rows = [row for cases in pool.map(one, books) for row in cases]
    summary = {h: scores([row for row in rows if row['year'] - row['base'] == h]) for h in range(1, 4)}
    print(json.dumps(summary, indent=2))
    if not args.municipality:
        output = {
            'baseYears': BASES, 'lastOutcome': LAST, 'metrics': METRICS,
            'sources': {'scb2025': str(archive), 'scbEarlier': 'SCB BefolkningNy, municipality archives',
                        'migration': [str(archive), str(recent)], 'kolada': str(archive)},
            'summaryByHorizon': summary, 'summaryAll': scores(rows),
            'crossCheck': cross_check(rows, archive), 'runs': rows,
        }
        (ROOT / 'research/data/age-group-hindcast.json').write_text(
            json.dumps(output, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
