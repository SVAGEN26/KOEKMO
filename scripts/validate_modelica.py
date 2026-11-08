"""Compile native Modelica and compare every annual forecast row with reference."""
from pathlib import Path
import subprocess
import os
import shutil
import json
import csv
import math
import tempfile

ROOT = Path(__file__).resolve().parents[1]
omc = os.environ.get('OMC') or shutil.which('omc')
if not omc:
    candidate = Path('/home/johti17/OpenModelicaWork/om-install/bin/omc')
    if candidate.exists(): omc = str(candidate)
if not omc: raise SystemExit('OpenModelica unavailable. Set OMC=/absolute/path/to/omc')
(ROOT / 'build').mkdir(exist_ok=True)
scenarios = [{}, {'taxGrowth':2.5,'wageGrowth':4,'interestRate':4,'migrationDelta':-100}, {'migrationDelta':300,'investment':250,'productivity':0.5,'taxRate':22.2}, {'pensionExpensePath':[275,250,220,190,190,190,190,190], 'pensionCashPaymentsPath':[190,195,200,200,200,200,200,200]}]
output_names = ['population','tax','grants','cost','depreciation','interest','result','debt','cash','assets','educationIndex','careIndex','payroll','pensionExpense','pensionCashPayments','otherOperatingExpense','operatingRevenue','operatingCash']
for n, assumptions in enumerate(scenarios):
    ref = json.loads(subprocess.check_output(['node',str(ROOT/'scripts/export_reference.mjs'),json.dumps(assumptions)],text=True))
    directory = Path(tempfile.mkdtemp(prefix=f'modelica-{n}-',dir=ROOT/'build'))
    (directory/'Scenario.mo').write_text(ref['source'])
    quote = lambda p: json.dumps(str(p))
    (directory/'run.mos').write_text(f'loadFile({quote(ROOT/"modelica/Motala.mo")});\nloadFile("Scenario.mo");\ncheckModel(Scenario);\ngetErrorString();\nsimulate(Scenario,startTime=2025,stopTime=2033,numberOfIntervals=8,outputFormat="csv");\ngetErrorString();\n')
    process = subprocess.run([omc,'run.mos'],cwd=directory,text=True,capture_output=True,timeout=120)
    (directory/'omc.log').write_text(process.stdout+process.stderr)
    result = directory/'Scenario_res.csv'
    if process.returncode or not result.exists():
        raise SystemExit(f'Modelica validation failed in {directory}\n{process.stdout}\n{process.stderr}')
    with result.open() as f: rows=list(csv.DictReader(f))
    for year,row in enumerate(ref['run']['rows'][1:],1):
        matching=[r for r in rows if math.isclose(float(r['time']),2025+year,abs_tol=1e-7)]  # time is the calendar year
        if not matching: raise AssertionError(f'Missing simulation year {year}')
        actual=matching[-1] # last row at a discrete event is the post-event state
        for name in output_names:
            if not math.isclose(float(actual[name]),row[name],rel_tol=1e-10,abs_tol=1e-5):
                raise AssertionError(f'Scenario {n}, year {year}, {name}: Modelica {actual[name]} vs JS {row[name]}')
        for j,value in enumerate(row['cohorts'],1):
            if not math.isclose(float(actual[f'p[{j}]']),value,rel_tol=1e-10,abs_tol=1e-5): raise AssertionError('Cohort parity failed')
    print(f'Scenario {n+1}: 8 annual rows and {len(output_names)+5} outputs match native Modelica; log {directory/"omc.log"}')
print('Native Modelica parity passed. Browser wasm-jit remains unverified without assets.')
