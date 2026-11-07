"""Generate and validate native Modelica scenarios; no browser engine claims."""
import csv
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from .data import ROOT


def literal(value):
    if isinstance(value, (list,tuple)):
        return '{'+','.join(literal(v) for v in value)+'}'
    if not math.isfinite(value):
        raise ValueError('Nonfinite Modelica parameter')
    return repr(value)


def source(candidate, initial, financing):
    calibration=candidate['demographicCalibration']
    if not calibration or any('cohorts' not in row for row in candidate['rows']):
        raise ValueError('Native cohort scenario requires valid demographic calibration')
    rows=candidate['rows']
    fields={'horizon':len(rows),**calibration,'damping':candidate['damping'],
            'revenue0':initial['taxAndGrants'],'netCost0':initial['netCost'],'financeNet0':initial['financeNet'],
            'revenuePerPerson':[r['taxAndGrants']/r['population'] for r in rows],
            'netCostPerPerson':[r['netCost']/r['population'] for r in rows],
            'financeNetPerPerson':[r['financeNet']/r['population'] for r in rows],
            **financing}
    return 'within ;\nmodel Scenario\n  extends MotalaResearch.Annual(\n    '+',\n    '.join(k+'='+literal(v) for k,v in fields.items())+');\nend Scenario;\n'


def validate_native(candidate, initial, financing, directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    scenario=source(candidate,initial,financing)
    (directory/'Scenario.mo').write_text(scenario)
    omc=os.environ.get('OMC') or shutil.which('omc')
    local=Path('/home/johti17/OpenModelicaWork/om-install/bin/omc')
    if not omc and local.exists():omc=str(local)
    if not omc:
        return {'status':'unverified','reason':'OpenModelica executable not available'}
    build=Path(tempfile.mkdtemp(prefix='motala-m1-'))
    (build/'Scenario.mo').write_text(scenario)
    horizon=len(candidate['rows']);stop=horizon+2
    (build/'run.mos').write_text(f'loadFile({json.dumps(str(ROOT/"MotalaResearch/package.mo"))});\n'
        'loadFile("Scenario.mo");\ncheckModel(Scenario);\ngetErrorString();\n'
        f'simulate(Scenario,stopTime={stop},numberOfIntervals={stop},outputFormat="csv");\ngetErrorString();\n')
    proc=subprocess.run([omc,'run.mos'],cwd=build,text=True,capture_output=True,timeout=120)
    log=proc.stdout+proc.stderr;(directory/'omc.log').write_text(log)
    if proc.returncode or 'The simulation finished successfully' not in log or re.search(r'LOG_ASSERT\s*\|\s*error',log):
        raise RuntimeError(f'Native candidate failed; see {directory / "omc.log"}\n{log}')
    shutil.copy2(build/'Scenario_res.csv',directory/'Scenario_res.csv')
    with (build/'Scenario_res.csv').open() as f:raw=list(csv.DictReader(f))
    rows=[]
    for t in range(stop+1):
        matches=[r for r in raw if math.isclose(float(r['time']),t,abs_tol=1e-8)]
        if not matches: raise ArithmeticError(f'Missing native time {t}')
        rows.append({k:float(v) for k,v in matches[-1].items() if k})
    def close(a,b,label):
        if not math.isfinite(a) or not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-5):
            raise ArithmeticError(f'{label}: native {a} != expected {b}')
    close(rows[0]['result'],initial['taxAndGrants']-initial['netCost']+initial['financeNet'],'initial ledger')
    for step,expected in enumerate(candidate['rows'],1):
        actual=rows[step];before=rows[step-1]
        for metric in ('population','taxAndGrants','netCost','financeNet','result'):
            close(actual[metric],expected[metric],f'{metric}, step {step}')
        for j,value in enumerate(expected['cohorts'],1):close(actual[f'p[{j}]'],value,f'cohort {j}')
        investment=financing['investmentPath'][step-1]
        bridge=financing['pensionAccrualMinusCashPath'][step-1]
        close(actual['assets']-before['assets'],investment-actual['capital.depreciation'],'asset change')
        close(actual['financing.operatingCash'],actual['result']+actual['capital.depreciation']+bridge,'cash bridge')
        close(actual['debt']-before['debt'],actual['financing.borrowing']-actual['financing.repayment'],'debt change')
        close(actual['cash']-before['cash'],actual['financing.operatingCash']-investment
              +actual['financing.borrowing']-actual['financing.repayment'],'cash change')
        if actual['debt']<0 or actual['financing.borrowing']*actual['financing.repayment']!=0:
            raise ArithmeticError('Invalid financing waterfall')
        for name in ('demography.populationBalance','ledger.ledgerResidual','capital.assetBalance',
                     'financing.debtBalance','financing.cashBalance'):close(actual[name],0,name)
    for row in rows[horizon+1:]:
        for metric in ('population','taxAndGrants','netCost','financeNet','result','debt','cash','assets','yearIndex'):
            close(row[metric],rows[horizon][metric],'horizon freeze: '+metric)
    return {'status':'passed','forecastYears':horizon,'comparedOutputsPerYear':10,
            'checks':['population conservation','fiscal ledger','asset roll-forward','cash bridge','debt roll-forward','horizon freeze'],
            'compiler':subprocess.check_output([omc,'--version'],text=True).strip(),
            'financingIsScenario':True}
