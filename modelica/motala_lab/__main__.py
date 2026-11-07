"""Run: python3 -m motala_lab run; fetch; evaluate --data observations.json.

All generated files stay below modelica unless an explicit output is supplied.
The default run is retrospective research on the existing public annual-report
series. It is not a historical SKR comparison or a validated operating budget.
"""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
from .data import ROOT,FROZEN,available,by_municipality,digest,load,verify_reference
from .evaluate import evaluate
from .model import forecast
from .modelica import validate_native
from .report import write_report


def save(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def code_files():
    return sorted([*ROOT.glob('motala_lab/*.py'),*ROOT.glob('motala_lab/*.mjs'),
                   *ROOT.glob('MotalaResearch/**/*.mo'),*ROOT.glob('MotalaResearch/**/package.order')])


def decision(evaluation,municipality):
    scores=[s for s in evaluation['scores'] if s['municipality']==municipality and s['metric']=='result' and s['horizonYears']==1]
    if not scores:
        return {'promoted':False,'summary':'För få jämförbara fall för att bedöma resultatprognosen.',
                'nextExperiment':'Utöka jämförbar bokslutshistorik och dokumentera ursprungliga publiceringsdatum.'}
    s=scores[0];own=s['models']['candidate']['mae'];best=min(s['models'][m]['mae'] for m in ('persistence','trend'))
    gain=(best-own)/best if best else None
    enough=s['distinctTargetYears']>=5
    return {'promoted':False,
            'passesDevelopmentTarget':bool(enough and gain is not None and gain>=.1),
            'relativeMAEImprovement':gain,'distinctTargetYears':s['distinctTargetYears'],
            'summary':f"M1 har MAE {own:.2f} mnkr för resultat mot {best:.2f} för bästa enkla baslinjen, på {s['n']} retrospektiva fall. "
                      +('Underlaget är för litet för att ersätta referensen.' if not enough else 'Resultatet är utvecklingsevidens och kräver oberoende slutprövning.'),
            'nextExperiment':'Samla en längre kommunpanel och separata kostnads- och intäktsserier; pröva skattad sektorsvis kostnadsanpassning före fler fria parametrar.'}


def run(args):
    reference=verify_reference();data=load(args.data)
    date.fromisoformat(args.forecast_date)
    # A current forecast may use observations retrieved by its declared date.
    rows=[r for r in data['rows'] if r['year']<date.fromisoformat(args.forecast_date).year
          and (r.get('sourceRelease') or r.get('retrievedAt') or '9999-12-31')<=args.forecast_date]
    own=by_municipality(rows).get(args.municipality,[])
    if not own:raise ValueError('No observations available by the requested forecast date')
    base_year=own[-1]['year'];rows=[r for r in rows if r['year']<=base_year]
    candidate=forecast(rows,args.municipality,args.horizon)
    evaluation=evaluate(data,args.horizon)
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in code_files()}
    if not 1<=args.horizon<=10:
        raise ValueError('Run horizon must be 1 to 10 years')
    config={'municipality':args.municipality,'forecastDate':args.forecast_date,'horizon':args.horizon,
            'evidenceClass':data['evidenceClass'],'native':not args.skip_native}
    run_id=digest({'data':data,'config':config,'code':hashes,'reference':reference['files'],
                   'python':sys.version,'numpy':np.__version__})[:16]
    output=Path(args.output) if args.output else ROOT/'runs'/run_id
    if output.exists() and any(output.iterdir()):
        manifest_path=output/'manifest.json'
        if manifest_path.exists():
            previous=json.loads(manifest_path.read_text())
            if previous.get('runId')==run_id and previous.get('artifacts'):
                for name,expected in previous['artifacts'].items():
                    artifact=output/name
                    if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest()!=expected:
                        raise ValueError('Archived run artifact changed: '+name)
                print(json.dumps({'runId':run_id,'directory':str(output),'status':'reused_verified_run'},indent=2))
                return
        raise ValueError(f'Output already exists or is incomplete; preserve it and choose another --output: {output}')
    output.mkdir(parents=True,exist_ok=True)
    save(output/'observations.json',data)
    # Snapshot executable sources, frozen data and package files for reproducibility.
    for p in code_files():
        destination=output/'source'/p.relative_to(ROOT);destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,destination)
    shutil.copytree(FROZEN,output/'source/reference/m0')
    save(output/'candidate.json',candidate)
    native={'status':'unverified','reason':'Native check explicitly skipped'}
    if not args.skip_native:
        b=json.loads((FROZEN/'baseline.json').read_text())
        if args.municipality=='0583' and base_year==b['baseYear'] and candidate['demographicCalibration'] and all('cohorts' in r for r in candidate['rows']):
            financing={'assets0':b['assets'],'depreciation0':b['depreciation'],
                       'debt0':b['debt'],'cash0':b['cash'],'investmentPath':[b['investment']]*args.horizon,
                       'pensionAccrualMinusCashPath':[0]*args.horizon}
            native=validate_native(candidate,own[-1],financing,output/'native')
            save(output/'financing-assumptions.json',{'status':'scenario_not_accuracy_validated',**financing})
        else:native={'status':'unverified','reason':'Matching opening asset/cash/debt ledger or valid cohort calibration unavailable'}
    baseline=None
    opening_reference=json.loads((FROZEN/'baseline.json').read_text())
    if args.municipality=='0583' and base_year==opening_reference['baseYear']:
        baseline=json.loads(subprocess.check_output(['node',str(ROOT/'motala_lab/run_reference.mjs')],text=True))
    save(output/'reference-current-forecast.json',baseline)
    bundle={'runId':run_id,'forecastDate':args.forecast_date,'candidate':candidate,'evaluation':evaluation,
            'native':native,'decision':decision(evaluation,args.municipality),
            'benchmarkStatus':'Saknar verifierade historiska SKR-prognoser; ingen jämförelse gjord',
            'baselineReconciliation':{'note':'The candidate uses reconstructed combined revenue from rounded historical accounts; the frozen current M0 uses reported tax and grant components.',
                                      'candidateOpeningRevenue':own[-1]['taxAndGrants'],
                                      'referenceOpeningRevenue':opening_reference['tax']+opening_reference['grants'] if baseline else None}}
    save(output/'results.json',bundle)
    write_report(bundle,output)
    artifacts={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(output.rglob('*')) if p.is_file()}
    save(output/'manifest.json',{'runId':run_id,'config':config,'dataSHA256':digest(data),'code':hashes,
                                'reference':reference,'python':sys.version,'numpy':np.__version__,
                                'native':native,'candidateUsesBenchmarkForecasts':False,'artifacts':artifacts})
    print(json.dumps({'runId':run_id,'directory':str(output),'native':native['status'],
                      'decision':bundle['decision']},ensure_ascii=False,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    subs=parser.add_subparsers(dest='command',required=True)
    run_parser=subs.add_parser('run',help='Freeze, fit, backtest, validate and report')
    run_parser.add_argument('--data',type=Path)
    run_parser.add_argument('--municipality',default='0583')
    run_parser.add_argument('--horizon',type=int,default=3)
    run_parser.add_argument('--forecast-date',default=date.today().isoformat())
    run_parser.add_argument('--output',type=Path)
    run_parser.add_argument('--skip-native',action='store_true')
    ev=subs.add_parser('evaluate',help='Retrospective evaluation of normalized observations')
    ev.add_argument('--data',type=Path);ev.add_argument('--horizon',type=int,default=3)
    fetch=subs.add_parser('fetch',help='Acquire raw public sources with receipts')
    fetch.add_argument('--output',type=Path,default=ROOT/'data/raw')
    obs=subs.add_parser('observations',help='Print documented observation schema and current local records')
    obs.add_argument('--data',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='run':run(args)
        elif args.command=='evaluate':print(json.dumps(evaluate(load(args.data),args.horizon),indent=2,ensure_ascii=False))
        elif args.command=='observations':print(json.dumps(load(args.data),indent=2,ensure_ascii=False))
        elif args.command=='fetch':
            from .public_data import acquire
            receipts=acquire(args.output)
            print(json.dumps(receipts,indent=2,ensure_ascii=False))
            if not any(r['status']=='downloaded' for r in receipts):raise SystemExit(1)
    except (ValueError,KeyError,ArithmeticError,RuntimeError) as exc:
        raise SystemExit(str(exc))


if __name__=='__main__':main()
