#!/usr/bin/env python3
"""Test the cohort-component demography against what happened, 2021-2025.

    OMC=/path/to/omc python3 scripts/hindcast_demography.py

For each base year 2020-2024, simulates Motala.Examples.DemographyOnly up to 2025 with
each birth model and compares births, deaths and population with SCB's outcome. The
calibration for a base year uses data up to that year only (Data.SCB.motala<year>), and
no scenario changes are applied. Writes data/demography-hindcast.json.

SCB's own regional projection (base year 2024) is listed for 2025 as a benchmark.
"""
import csv
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OMC = os.environ.get('OMC') or shutil.which('omc') or '/home/johti17/OpenModelicaWork/om-install/bin/omc'
LAST = 2025
BIRTH_MODELS = {
    'fertility 1.41': 'Kommunekonomi.Components.Fertility.Constant fertility(totalFertility = 1.41)',
    'Motala base year': 'Kommunekonomi.Components.Fertility.Constant fertility(totalFertility = Motala.Data.SCB.motala{base}.totalFertility)',
    'Motala 5-year mean': 'Kommunekonomi.Components.Fertility.Constant fertility(totalFertility = Motala.Data.SCB.motala{base}.totalFertilityMean5)',
    'old rule (19-64)': 'Kommunekonomi.Components.Fertility.Legacy fertility',
    # Sweden's level in the base year times the municipality's relation to Sweden over five years: known at the base year.
    'national level, local relation': 'Kommunekonomi.Components.Fertility.Constant fertility(totalFertility = Kommunekonomi.Data.SCB.totalFertilityAt({base})*Motala.Data.SCB.motala{base}.totalFertilityMean5/Kommunekonomi.Data.SCB.totalFertilityMean5({base}))',
}


def simulate(base, birth_model, directory):
    horizon = LAST - base
    source = f'''model Run
  extends Motala.Examples.DemographyOnly(horizon = {horizon},
    redeclare Kommunekonomi.Components.CohortDemography demography(data = Motala.Data.SCB.motala{base},
      redeclare {birth_model.format(base=base)}));
end Run;
'''
    (directory / 'Run.mo').write_text(source)
    (directory / 'run.mos').write_text(
        f'loadFile({json.dumps(str(ROOT / "modelica/Kommunekonomi.mo"))}); getErrorString();\n'
        f'loadFile({json.dumps(str(ROOT / "modelica/Motala.mo"))}); getErrorString();\n'
        'loadFile("Run.mo"); getErrorString();\n'
        f'simulate(Run, startTime = {base}, stopTime = {LAST}, numberOfIntervals = {horizon}, outputFormat = "csv",'
        ' variableFilter = "demography\\\\.(population|births|deaths|migration|older.*)"); getErrorString();\n')
    process = subprocess.run([OMC, 'run.mos'], cwd=directory, capture_output=True, text=True, timeout=600)
    result = directory / 'Run_res.csv'
    if not result.exists():
        raise SystemExit(f'Simulation failed for {base}, {birth_model}:\n{process.stdout[-2000:]}')
    rows = {}
    for row in csv.DictReader(result.open()):
        rows[round(float(row['time']))] = row  # the last row at each whole year is the post-event state
    # Time is the calendar year: the base year's accounts at the start, then one row per year.
    return {year: {k.split('.', 1)[1]: float(v) for k, v in row.items() if k.startswith('demography.')}
            for year, row in rows.items() if year > base}


def main():
    d = json.loads((ROOT / 'data/demography-inputs.json').read_text())
    observed = {int(y): {'population': sum(p['1']) + sum(p['2'])} for y, p in d['observed']['population'].items()}
    for y, b in d['observed']['births'].items():
        observed[int(y)]['births'] = b['1'] + b['2']
    for y, x in d['observed']['deaths'].items():
        observed[int(y)]['deaths'] = sum(x['1']) + sum(x['2'])
    runs = []
    with tempfile.TemporaryDirectory(prefix='motala-demography-') as tmp:
        for name, model in BIRTH_MODELS.items():
            for base in range(2020, LAST):
                directory = Path(tmp) / f'{base}-{len(runs)}'
                directory.mkdir()
                for year, values in simulate(base, model, directory).items():
                    runs.append({'birthModel': name, 'base': base, 'year': year, 'horizon': year - base,
                                 **{k: values[k] for k in ('population', 'births', 'deaths', 'migration')},
                                 'observed': observed[year]})
    summary = {}
    for name in BIRTH_MODELS:
        for horizon in range(1, LAST - 2020 + 1):
            cases = [r for r in runs if r['birthModel'] == name and r['horizon'] == horizon]
            if not cases:
                continue
            summary.setdefault(name, {})[horizon] = {
                'cases': len(cases),
                **{f'{k}MeanAbsError': sum(abs(r[k] - r['observed'][k]) for r in cases) / len(cases)
                   for k in ('births', 'deaths', 'population')},
                **{f'{k}MeanError': sum(r[k] - r['observed'][k] for r in cases) / len(cases)
                   for k in ('births', 'deaths', 'population')}}
    scb = d['scbProjectionMotala']['2025']
    benchmark = {'source': 'SCB regional projection for Motala, base year 2024 (BefProgOsiktRegN)',
                 'year': 2025, 'births': scb['Födda'], 'deaths': scb['Döda'], 'population': scb['Folkmängd'],
                 'observed': observed[2025]}
    out = {'source': 'Källa: SCB (CC BY 4.0); model Motala.Examples.DemographyOnly',
           'note': 'Calibration per base year uses data up to that year only. No scenario changes. '
                   'Births, deaths and population are compared with SCB outcomes.',
           'summaryByHorizon': summary, 'scbProjection2025': benchmark, 'runs': runs}
    (ROOT / 'data/demography-hindcast.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    print(f'{"birth model":20s} {"h":>2s} {"n":>2s} {"births MAE":>10s} {"bias":>6s} {"deaths MAE":>10s} {"bias":>6s} {"pop MAE":>8s} {"bias":>7s}')
    for name, rows in summary.items():
        for h, s in rows.items():
            print(f'{name:20s} {h:2d} {s["cases"]:2d} {s["birthsMeanAbsError"]:10.1f} {s["birthsMeanError"]:6.1f} '
                  f'{s["deathsMeanAbsError"]:10.1f} {s["deathsMeanError"]:6.1f} {s["populationMeanAbsError"]:8.1f} {s["populationMeanError"]:7.1f}')
    one = [r for r in runs if r['birthModel'] == 'fertility 1.41' and r['base'] == 2024][0]
    print(f'\n2025 from base 2024: model births {one["births"]:.0f}, deaths {one["deaths"]:.0f}, population {one["population"]:.0f}; '
          f'SCB projection {benchmark["births"]:.0f}, {benchmark["deaths"]:.0f}, {benchmark["population"]:.0f}; '
          f'outcome {observed[2025]["births"]:.0f}, {observed[2025]["deaths"]:.0f}, {observed[2025]["population"]:.0f}')


if __name__ == '__main__':
    main()
