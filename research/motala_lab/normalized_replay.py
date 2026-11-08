"""Append a preregistered normalized P/I diagnostic to the frozen v5 comparison."""
import argparse
from copy import deepcopy
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import shutil
from statistics import mean
import subprocess

from . import dynamics, historical_dynamics as hist, normalized_revenue as normalized
from . import revenue_bridge

ROOT = dynamics.ROOT
SUFFIX = '-normalized-PI'


def verify_archive(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    for relative, expected in manifest.items():
        path = directory/relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Parent archive changed: '+relative)
    return manifest


def summarize(cases, metrics, *, suffix=SUFFIX):
    result = []
    for horizon in sorted({c['horizon'] for c in cases}):
        group = [c for c in cases if c['horizon'] == horizon]
        names = sorted(set.intersection(*(set(c['predictions']) for c in group)))
        for metric in metrics:
            models = {}
            for name in names:
                errors = [c['predictions'][name][metric]-c['actual'][metric] for c in group]
                models[name] = {'mae': mean(map(abs, errors)), 'bias': mean(errors),
                                'rmse': math.sqrt(mean(e*e for e in errors))}
            paired = {}
            for name in names:
                if not name.endswith(suffix):
                    continue
                parent = name.removesuffix(suffix)
                differences = [abs(c['predictions'][name][metric]-c['actual'][metric])
                               -abs(c['predictions'][parent][metric]-c['actual'][metric]) for c in group]
                leave = [mean(v for j, v in enumerate(differences) if i != j)
                         for i in range(len(group))] if len(group) > 1 else []
                paired[name] = {'parent': parent, 'meanAbsoluteErrorDifference': mean(differences),
                    'leaveOneTargetOutRange': [min(leave), max(leave)] if leave else None,
                    'note': 'Descriptive only, no refitting or confidence claim.'}
            result.append({'horizon': horizon, 'metric': metric, 'n': len(group),
                           'targetYears': [c['targetYear'] for c in group], 'models': models, 'paired': paired})
    return result


def check_native(directory, annual, parent, path):
    checks = {'maximumBalanceResidual': 0., 'maximumUnchangedQuantityDifference': 0.,
              'maximumResidualAllocationDifference': 0., 'maximumPIIntegrationDifference': 0.}
    with (directory/'native/native.csv').open() as handle:
        for row in csv.DictReader(handle):
            for name in ('balanceResidual', 'demography.populationResidual', 'finance.cashResidual', 'finance.debtResidual'):
                checks['maximumBalanceResidual'] = max(checks['maximumBalanceResidual'], abs(float(row['plant.'+name])))
    for index, (before, after) in enumerate(zip(parent, annual)):
        expected = normalized.allocation(before, path, index)
        for key in ('netCost', 'personnel', 'population', 'operatingRevenue', 'depreciation'):
            checks['maximumUnchangedQuantityDifference'] = max(checks['maximumUnchangedQuantityDifference'], abs(before[key]-after[key]))
        for key in ('inheritedTax', 'inheritedGrants'):
            checks['maximumResidualAllocationDifference'] = max(checks['maximumResidualAllocationDifference'], abs(after[key]-expected[key]))
        for key in ('preliminaryTax', 'incomeEqualisation'):
            checks['maximumPIIntegrationDifference'] = max(checks['maximumPIIntegrationDifference'], abs(after[key]-expected[key]))
    if max(checks.values()) > 1e-3:
        raise ArithmeticError('Normalized experiment invariant failed: '+str(checks))
    return checks


def write_report(directory, result):
    def table(headers, rows):
        def cell(value):
            return html.escape(f'{value:.2f}' if type(value) is float else str(value))
        return '<div class="scroll"><table><tr>'+''.join('<th>'+cell(h)+'</th>' for h in headers)+'</tr>'+''.join(
            '<tr>'+''.join('<td>'+cell(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</table></div>'
    summaries = [[s['horizon'], s['metric'], s['n'], name, values['mae'], values['bias'], values['rmse']]
                 for s in result['scores'] if s['metric'] in ('result', 'taxAndGrants', 'netCost', 'financeNet')
                 for name, values in s['models'].items()]
    pi = [[s['horizon'], s['metric'], s['n'], name, values['mae'], values['bias'], values['rmse']]
          for s in result['normalizedComponentScores'] for name, values in s['models'].items()]
    other_components = [[s['horizon'], s['metric'], s['n'], name, values['mae'], values['bias'], values['rmse']]
                        for s in result['componentScores'] if s['metric'] in ('tax', 'grants', 'personnel')
                        for name, values in s['models'].items()
                        if name.endswith(SUFFIX) or name in ('M2-PKV-costbase', 'M2-PKV-no-repeat',
                                                             'PKV-accounting-costbase', 'PKV-accounting-no-repeat')]
    finance = [[c['originYear'], c['targetYear'], c['model'], c['taxAndGrantsChange'],
                c['financeNetChange'], c['netCostChange'], c['resultChange']] for c in result['financingEffects']]
    pairs = [[s['horizon'], s['metric'], name, values['meanAbsoluteErrorDifference'], str(values['leaveOneTargetOutRange'])]
             for s in result['normalizedPairedScores']+result['normalizedComponentScores']
             for name, values in s['paired'].items()]
    text = '''<!doctype html><html lang="sv"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Motala: prövning av preliminär skatt och inkomstutjämning</title>
<style>body{font:16px system-ui;max-width:1200px;margin:32px auto;padding:0 20px;color:#142630}table{border-collapse:collapse;font-variant-numeric:tabular-nums;margin:16px 0}td,th{padding:8px;border-bottom:1px solid #ccd4db;text-align:right}th{background:#e5edf2}.scroll{overflow-x:auto}.note{background:#fff0cf;padding:18px}li{margin:10px 0}</style>
<h1>Preliminär skatt och inkomstutjämning för Motala</h1>
<p class="note">Retrospektiv utvecklingsprövning. Samma tolv fall och tidigare jämförelser behålls. Inga parametrar har anpassats till målutfallen. Årsutfallen har dock redan påverkat modellutvecklingen; detta är inget oberoende slutprov. Den tidigare kandidaten M2-PKV-costbase är oförändrad.</p>
<p>Preliminär skatt (P) och inkomstutjämning (I) följer samma förändring i nationell skattekraft, med oförändrad relativ lokal skattekraft och konstant referensbefolkning. För första året används regeringens värde i det daterade SKR-cirkuläret; därefter används SKR:s prognostiserade nivå direkt som approximation. Absolut novemberbefolkning härleds inte.</p>
<p>Den proportionellt allokerade återstoden av skatter och bidrag behåller tidigare antaganden. Den är en ärvd rest från jämförelsen och ingen ny korrekt prognos för avräkning, reglering eller övriga bidrag. Dessa delar och personalkostnaderna återstår att förbättra.</p>
<p>Native-varianterna kör hela Modelica-modellen, inklusive finansiering. PKV-accounting-varianterna behåller sina fasta kvantiteter och sitt finansnetto. Kostnader och demografi är oförändrade mot respektive jämförelse inom numerisk tolerans. Den nya årsvisa intäktsprofilen kan påverka ränta och skuld inom året; kassaprognosen är inte empiriskt validerad.</p>
<p><a href="protocol.json">Låst protokoll</a> · <a href="evaluation.json">Alla prognoser, fel och kontroller</a> · <a href="manifest.json">Hashar</a> · <a href="reference/evaluation.json">Oförändrad tidigare prövning</a></p>
<h2>De prövade intäktskomponenterna</h2><p>Belopp i mnkr. Parent-radernas P/I är en proportionell allokering av tidigare totalprognoser, inte tidigare separat skattade komponenter. Positivt fel betyder överskattning.</p>'''
    text += table(['År framåt', 'Komponent', 'n', 'Modell', 'MAE', 'Bias', 'RMSE'], pi)
    text += '<h2>Hela skatten, bidragen och personalkostnaden</h2>'+table(['År framåt', 'Komponent', 'n', 'Modell', 'MAE', 'Bias', 'RMSE'], other_components)
    text += '<h2>Hela resultatet och övriga huvudmått</h2>'+table(['År framåt', 'Mått', 'n', 'Modell', 'MAE', 'Bias', 'RMSE'], summaries)
    text += '<h2>Finansieringens bidrag till skillnaden</h2>'+table(['Startår', 'Målår', 'Modell', 'Δ skatt och bidrag', 'Δ finansnetto', 'Δ nettokostnad', 'Δ resultat'], finance)
    text += '<h2>Stabilitet när ett målår utelämnas</h2><p>Negativ MAE-skillnad är en förbättring. Intervallen är beskrivande känslighet, inte konfidensintervall. Ingen modell omkalibreras.</p>'+table(['År framåt', 'Mått', 'Modell', 'MAE-skillnad', 'Utelämningsintervall'], pairs)
    text += '<h2>Begränsningar</h2><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in result['limitations'])+'</ul></html>'
    (directory/'report.html').write_text(text, encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--protocol', type=Path, default=ROOT/'data/historical-protocol-normalized-revenue.json')
    parser.add_argument('--parent-run', type=Path, help='Same hash-verified parent archive, optionally relocated')
    args = parser.parse_args(argv)
    protocol = json.loads(args.protocol.read_text())
    parent_root = args.parent_run or ROOT/protocol['parentRun']
    if args.out.resolve().is_relative_to(parent_root.resolve()):
        raise ValueError('New output must be outside the preserved parent archive')
    if hashlib.sha256((parent_root/'manifest.json').read_bytes()).hexdigest() != protocol['parentManifestSha256']:
        raise ValueError('Parent manifest differs from registration')
    parent_manifest = verify_archive(parent_root)
    inputs = {}
    for name, expected in protocol['sources'].items():
        file = ROOT/'data'/name
        if hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise ValueError('Registered source changed: '+name)
        inputs[name] = json.loads(file.read_text())
    parent = json.loads((parent_root/'evaluation.json').read_text())
    old_protocol = json.loads((parent_root/'protocol.json').read_text())
    for key in ('originYears', 'horizons', 'eventScenarios'):
        if protocol[key] != old_protocol[key]:
            raise ValueError('Experiment changed the registered target set: '+key)
    data = hist.load_ledgers(parent_root/'annual-ledgers.json')
    costs = json.loads((parent_root/'skr-pkv-vintages.json').read_text())
    events = json.loads((parent_root/'motala-noted-events.json').read_text())
    components = inputs['motala-revenue-components.json']
    national = inputs['skr-revenue-vintages.json']
    args.out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(ROOT/'MotalaDynamics', args.out/'sources/MotalaDynamics')
    shutil.copytree(ROOT/'motala_lab', args.out/'sources/motala_lab', ignore=shutil.ignore_patterns('__pycache__'))
    (args.out/'sources/tests').mkdir()
    for name in ('test_normalized_revenue.py', 'test_revenue_bridge.py'):
        shutil.copy2(ROOT/'tests'/name, args.out/'sources/tests'/name)
    shutil.copytree(parent_root, args.out/'reference')
    (args.out/'sources/data').mkdir()
    for name in protocol['sources']:
        shutil.copy2(ROOT/'data'/name, args.out/'sources/data'/name)
    for name in ('annual-ledgers.json', 'skr-pkv-vintages.json', 'motala-noted-events.json'):
        shutil.copy2(parent_root/name, args.out/'sources/data'/name)
    shutil.copy2(parent_root/'protocol.json', args.out/'sources/data/historical-protocol-tax.json')
    shutil.copy2(args.protocol, args.out/'sources/data/historical-protocol-normalized-revenue.json')
    shutil.copy2(args.protocol, args.out/'protocol.json')
    shutil.copy2(ROOT/'run_normalized_revenue.py', args.out/'sources/run_normalized_revenue.py')
    shutil.copy2(ROOT/'README.txt', args.out/'sources/README.txt')
    equations = ROOT.parent/'docs/dynamics-equations.md'
    if not equations.is_file():
        equations = ROOT.parent/'equations.md'  # Reproduction from a saved source snapshot.
    shutil.copy2(equations, args.out/'equations.md')
    result = deepcopy(parent)
    result.update(protocolHash=hist.digest(protocol), normalizedProtocol=protocol,
                  normalizedChecks=[], normalizedComponents=[], financingEffects=[])
    paths = {}
    for origin in protocol['originYears']:
        cases = [c for c in parent['cases'] if c['originYear'] == origin]
        years = max(c['horizon'] for c in cases)
        for policy in protocol['eventScenarios']:
            base_name = 'M2-PKV-'+policy
            name = base_name+SUFFIX
            destination = args.out/'origins'/str(origin)/name
            annual, audit = hist.predict_origin(data, origin, years, old_protocol, destination,
                source_root=args.out/'sources', missing_wip_fraction=old_protocol['missingWIP']['nominal'],
                macro_data=costs, event_data=events, event_policy=policy, normalized_inputs=(components, national))
            path = audit['normalizedRevenue']
            paths[origin, policy] = path
            original = json.loads((parent_root/'origins'/str(origin)/base_name/'annual.json').read_text())
            checks = check_native(destination, annual, original, path)
            result['normalizedChecks'].append({'originYear': origin, 'policy': policy, 'WIP': 'nominal', **checks})
            accounting_name = 'PKV-accounting-'+policy
            accounting_parent = [c['predictions'][accounting_name] for c in sorted(cases, key=lambda c: c['horizon'])]
            accounting = normalized.accounting_projection(accounting_parent, path)
            for case in result['cases']:
                if case['originYear'] != origin:
                    continue
                index = case['horizon']-1
                case['predictions'][name] = annual[index]
                case['predictions'][accounting_name+SUFFIX] = accounting[index]
                case['componentErrors'][name] = {k: annual[index][k]-case['actualComponents'][k] for k in hist.COMPONENTS}
                before, after = case['predictions'][base_name], annual[index]
                result['financingEffects'].append({'originYear': origin, 'targetYear': case['targetYear'], 'model': name,
                    **{key+'Change': after[key]-before[key] for key in ('taxAndGrants', 'financeNet', 'netCost', 'result')}})
            if audit['assumedWIP']:
                for fraction in old_protocol['missingWIP']['sensitivityFractionsOfTotalTangibleAssets']:
                    destination = args.out/'origins'/str(origin)/f'{name}-WIP-{fraction}'
                    alternative, alternative_audit = hist.predict_origin(data, origin, years, old_protocol, destination,
                        source_root=args.out/'sources', missing_wip_fraction=fraction, macro_data=costs,
                        event_data=events, event_policy=policy, normalized_inputs=(components, national))
                    original = json.loads((parent_root/'origins'/str(origin)/f'{base_name}-WIP-{fraction}'/'annual.json').read_text())
                    checks = check_native(destination, alternative, original, alternative_audit['normalizedRevenue'])
                    result['normalizedChecks'].append({'originYear': origin, 'policy': policy, 'WIP': fraction, **checks})
                    result['wipSensitivity'].extend({'originYear': origin, 'targetYear': row['year'], 'fraction': fraction,
                        'model': name, 'result': row['result'], 'differenceFromNominal': row['result']-annual[i]['result']}
                        for i, row in enumerate(alternative))
    # Outcomes are consulted only after all prospective runs have completed.
    for case in result['cases']:
        ledger = next(r for r in data['rows'] if r['year'] == case['targetYear'])
        target_data = inputs['revenue-component-targets-2025.json'] if ledger['year'] == 2025 else components
        target = revenue_bridge.opening_components(target_data, ledger)
        actual_p = target['taxComponents']['preliminaryTax']
        actual_i = target['grantComponents']['incomeEqualisation']
        component_case = {k: case[k] for k in ('originYear', 'targetYear', 'horizon')}
        component_case.update(actual={'preliminaryTax': actual_p, 'incomeEqualisation': actual_i,
                                     'preliminaryTaxAndEqualisation': actual_p+actual_i}, predictions={})
        for policy in protocol['eventScenarios']:
            path = paths[case['originYear'], policy]
            for prefix in ('M2-PKV-', 'PKV-accounting-'):
                name = prefix+policy
                allocated = normalized.allocation(case['predictions'][name], path, case['horizon']-1)
                p, i = allocated['allocatedParentPreliminaryTax'], allocated['allocatedParentIncomeEqualisation']
                component_case['predictions'][name] = dict(preliminaryTax=p, incomeEqualisation=i, preliminaryTaxAndEqualisation=p+i)
                component_case['predictions'][name+SUFFIX] = {key: case['predictions'][name+SUFFIX][key] for key in normalized.COMPONENTS}
        result['normalizedComponents'].append(component_case)
    result['scores'] = hist.scores(result['cases'], candidate_name=result['candidate'])
    result['componentScores'] = hist.component_scores(result['cases'])
    for key, selected in [('knownWIPScores', [c for c in result['cases'] if not c['assumedOpeningWIP']]),
                          ('sameReportYearKnownWIPScores', [c for c in result['cases'] if not c['assumedOpeningWIP'] and not c['revisedOpeningData']])]:
        result[key] = hist.scores(selected, candidate_name=result['candidate']) if selected else []
    result['normalizedComponentScores'] = summarize(result['normalizedComponents'], normalized.COMPONENTS)
    selected = [dict(c, predictions={name: p for name, p in c['predictions'].items()
                    if name.endswith(SUFFIX) or name in ('M2-PKV-costbase', 'M2-PKV-no-repeat', 'PKV-accounting-costbase', 'PKV-accounting-no-repeat')}) for c in result['cases']]
    result['normalizedPairedScores'] = summarize(selected, hist.METRICS)
    for before, after in zip(parent['cases'], result['cases']):
        if before['actual'] != after['actual'] or before['actualComponents'] != after['actualComponents']:
            raise RuntimeError('Target outcomes changed')
        if any(after['predictions'][name] != prediction for name, prediction in before['predictions'].items()):
            raise RuntimeError('A previous prediction was overwritten')
    result['limitations'].extend([
        'Normalized P/I is a constant fiscal-reference population scenario. Demographic changes remain in costs and inherited revenue residuals; this is a partial experiment, not a complete municipal forecast.',
        'Remaining tax settlements and grant categories keep the parent assumptions, including known shortcomings. No missing November observations have been fabricated.',
        'Government-to-SKR capacity transition after horizon 1 is an explicit approximation, not a statutory identity or a fitted level adjustment.',
        'Parent P/I are proportional allocations of total forecasts. New P/I are direct component forecasts; remaining residuals are not separately validated.',
        'Annual constant P/I changes within-year income and cash timing. Native financing changes include this numerical timing assumption; actual settlement cash dates remain unknown.',
        '2025 component targets were read from notes 6/7 solely for scoring. The source grant rounding difference -1 mnkr is preserved.'
    ])
    result['parentArchive'] = {'relativePath': protocol['parentRun'], 'manifestSha256': protocol['parentManifestSha256'],
                              'verifiedArtifactCount': len(parent_manifest), 'oldPredictionsPreservedExactly': True}
    hist.dump(args.out/'evaluation.json', result)
    write_report(args.out, result)
    hist.dump(args.out/'environment.json', {'compiler': subprocess.check_output([dynamics.compiler(), '--version'], text=True).strip()})
    hist.dump(args.out/'manifest.json', {str(p.relative_to(args.out)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(args.out.rglob('*')) if p.is_file()})
    print(args.out/'report.html')
    return 0
