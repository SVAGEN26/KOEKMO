"""Append a locked dated-settlement experiment to the preserved v6 comparison."""
import argparse
from copy import deepcopy
import csv
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess

from . import dynamics, historical_dynamics as hist, revenue_bridge
from . import settlement_forecasts as settlements
from .normalized_replay import summarize, verify_archive

ROOT = dynamics.ROOT
SUFFIX = '-settlement'
PARENT_SUFFIX = '-normalized-PI'
UNCHANGED = ('preliminaryTax', 'incomeEqualisation', 'preliminaryTaxAndEqualisation',
             'grants', 'inheritedGrants', 'netCost', 'personnel', 'population',
             'operatingRevenue', 'depreciation')


def check_native(directory, annual, parent, path):
    expected = path['settlementForecast']['rows']
    if len(annual) != len(parent) or len(annual) != len(expected):
        raise ArithmeticError('Settlement comparison horizons differ')
    checks = {'maximumBalanceResidual': 0., 'maximumUnchangedQuantityDifference': 0.,
              'maximumSettlementIntegrationDifference': 0., 'maximumTaxIdentityResidual': 0.,
              'maximumResultChangeIdentityResidual': 0.}
    with (directory/'native/native.csv').open() as handle:
        for row in csv.DictReader(handle):
            for name in ('balanceResidual', 'demography.populationResidual', 'finance.cashResidual', 'finance.debtResidual'):
                checks['maximumBalanceResidual'] = max(checks['maximumBalanceResidual'], abs(float(row['plant.'+name])))
    for before, after, source in zip(parent, annual, expected):
        if before['year'] != after['year'] or after['year'] != source['year']:
            raise ArithmeticError('Settlement comparison years differ')
        for key in UNCHANGED:
            checks['maximumUnchangedQuantityDifference'] = max(checks['maximumUnchangedQuantityDifference'], abs(before[key]-after[key]))
        checks['maximumSettlementIntegrationDifference'] = max(checks['maximumSettlementIntegrationDifference'],
            abs(after['taxSettlement']-source['settlementAndRevision']),
            abs(after['currentYearSettlement']-source['currentYearSettlement']),
            abs(after['priorYearSettlementRevision']))
        checks['maximumTaxIdentityResidual'] = max(checks['maximumTaxIdentityResidual'], abs(after['inheritedTax']),
            abs(after['tax']-after['preliminaryTax']-after['taxSettlement']),
            abs(after['settlementAndRevision']-after['taxSettlement']))
        checks['maximumResultChangeIdentityResidual'] = max(checks['maximumResultChangeIdentityResidual'],
            abs(after['result']-before['result']-(after['taxAndGrants']-before['taxAndGrants'])
                -(after['financeNet']-before['financeNet'])+(after['netCost']-before['netCost'])))
    if max(checks.values()) > 1e-3:
        raise ArithmeticError('Settlement experiment invariant failed: '+str(checks))
    return checks


def write_report(directory, result):
    def table(headers, rows):
        def cell(value):
            return html.escape(f'{value:.3f}' if type(value) is float else str(value))
        return '<div class="scroll"><table><tr>'+''.join('<th>'+cell(h)+'</th>' for h in headers)+'</tr>'+''.join(
            '<tr>'+''.join('<td>'+cell(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</table></div>'
    def score_rows(scores):
        return [[s['horizon'], s['metric'], s['n'], name, values['mae'], values['bias'], values['rmse']]
                for s in scores for name, values in s['models'].items()]
    text = '''<!doctype html><html lang="sv"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Motala: daterade skatteavräkningar</title>
<style>body{font:16px system-ui;max-width:1200px;margin:32px auto;padding:0 20px;color:#142630}table{border-collapse:collapse;font-variant-numeric:tabular-nums;margin:16px 0}td,th{padding:8px;border-bottom:1px solid #ccd4db;text-align:right}th{background:#e5edf2}.scroll{overflow-x:auto}.note{background:#fff0cf;padding:18px}li{margin:10px 0}</style>
<h1>Daterade skatteavräkningar för Motala</h1>
<p class="note">Retrospektiv utvecklingsprövning på samma tolv fall. Alla tidigare prognoser och målutfall bevaras. Inga parametrar anpassas till dessa utfall, men åren har redan påverkat modellutvecklingen. Detta är inget oberoende slutprov. Tidigare kandidat M2-PKV-costbase är oförändrad.</p>
<p>Den ärvda skatteresten i v6 ersätts helt. Första årets aktuella avräkning beräknas som det daterade decembercirkulärets kronor per invånare gånger Motalas befolkning vid startårets slut, delat med en miljon. Befolkningen är en uttrycklig proxy för 1 november samma år. Senare aktuella avräkningar och alla framtida revisionsdifferenser antas noll. Källornas okända värden ligger kvar som null.</p>
<p>Preliminär skatt, inkomstutjämning, bidrag och kostnader följer v6. Avräkningen är en separat signerad intäkt utan skalning med kommunens skattesats. Native-varianterna omfattar ränta och skuld; accounting-varianterna behåller sitt finansnetto. Betalning samma år och noll öppningsfordran är kvarvarande antaganden, inte empirisk validering av likviditet.</p>
<p><a href="protocol.json">Låst protokoll</a> · <a href="evaluation.json">Alla prognoser, fel och kontroller</a> · <a href="manifest.json">Hashar</a> · <a href="reference/report.html">Oförändrad v6-prövning</a></p>
<h2>Avräkning, preliminär skatt och hela skatten</h2>
<p>Belopp i mnkr. Avräkningsmåttet omfattar aktuell avräkning plus revision av föregående år. Parent-värdet är v6:s ärvda skatterest, inte en tidigare separat administrativ prognos. Båda delarnas observerade utfall sparas separat i evaluation.json. Positiv bias betyder överskattning.</p>'''
    headers = ['År framåt', 'Mått', 'n', 'Modell', 'MAE', 'Bias', 'RMSE']
    text += table(headers, score_rows(result['settlementComponentScores']))
    text += '<h2>Bidrag och personal</h2>'+table(headers, score_rows(result['settlementOtherComponentScores']))
    text += '<h2>Hela resultatet och tidigare jämförelser</h2>'+table(headers, score_rows(result['scores']))
    finance = [[c['originYear'], c['targetYear'], c['model'], c['taxAndGrantsChange'],
                c['financeNetChange'], c['netCostChange'], c['resultChange']] for c in result['settlementFinancingEffects']]
    text += '<h2>Finansieringens bidrag till skillnaden</h2>'+table(
        ['Startår', 'Målår', 'Modell', 'Δ skatt och bidrag', 'Δ finansnetto', 'Δ nettokostnad', 'Δ resultat'], finance)
    pairs = [[s['horizon'], s['metric'], name, values['meanAbsoluteErrorDifference'], str(values['leaveOneTargetOutRange'])]
             for s in result['settlementPairedScores']+result['settlementComponentScores']+result['settlementOtherComponentScores']
             for name, values in s['paired'].items()]
    text += '<h2>Stabilitet när ett målår utelämnas</h2><p>Negativ MAE-skillnad betyder förbättring mot motsvarande v6-variant. Intervallen är beskrivande känslighet, inte konfidensintervall. Ingen omkalibrering sker.</p>'+table(
        ['År framåt', 'Mått', 'Modell', 'MAE-skillnad', 'Utelämningsintervall'], pairs)
    sensitivity = [[r['originYear'], r['ratePerPerson'], r['populationProxy']['value'],
                    s['populationDifference'], s['firstYearSettlementDifference']]
                   for r in result['settlementPopulationSensitivity'] for s in r['differences']]
    text += '<h2>Befolkningsproxyns direkta effekt</h2><p>s × ΔN / 1 000 000. Skillnaderna är hypotetiska, inte observerade proxyfel, felgränser eller fullständiga resultatintervall. Senare ränteeffekter ingår inte.</p>'+table(
        ['Startår', 'kr/person', 'Årsslutsbefolkning', 'Δ personer', 'Δ avräkning, mnkr'], sensitivity)
    text += '<h2>Kvarstående begränsningar</h2><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in result['settlementLimitations'])+'</ul></html>'
    (directory/'report.html').write_text(text, encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--protocol', type=Path, default=ROOT/'data/historical-protocol-settlements.json')
    parser.add_argument('--parent-run', type=Path, help='Same hash-verified v6 archive, optionally relocated')
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
    previous_protocol = json.loads((parent_root/'protocol.json').read_text())
    for key in ('originYears', 'horizons', 'eventScenarios'):
        if protocol[key] != previous_protocol[key]:
            raise ValueError('Experiment changed the registered target set: '+key)
    old_root = parent_root/'reference'
    old_protocol = json.loads((old_root/'protocol.json').read_text())
    data = hist.load_ledgers(old_root/'annual-ledgers.json')
    costs = json.loads((old_root/'skr-pkv-vintages.json').read_text())
    events = json.loads((old_root/'motala-noted-events.json').read_text())
    components = inputs['motala-revenue-components.json']
    national = inputs['skr-revenue-vintages.json']
    args.out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(ROOT/'MotalaDynamics', args.out/'sources/MotalaDynamics')
    shutil.copytree(ROOT/'motala_lab', args.out/'sources/motala_lab', ignore=shutil.ignore_patterns('__pycache__'))
    (args.out/'sources/tests').mkdir()
    for name in ('test_settlement_forecasts.py', 'test_normalized_revenue.py', 'test_revenue_bridge.py'):
        shutil.copy2(ROOT/'tests'/name, args.out/'sources/tests'/name)
    shutil.copytree(parent_root, args.out/'reference')
    (args.out/'sources/data').mkdir()
    for name in protocol['sources']:
        shutil.copy2(ROOT/'data'/name, args.out/'sources/data'/name)
    for name in ('annual-ledgers.json', 'skr-pkv-vintages.json', 'motala-noted-events.json'):
        shutil.copy2(old_root/name, args.out/'sources/data'/name)
    shutil.copy2(old_root/'protocol.json', args.out/'sources/data/historical-protocol-tax.json')
    shutil.copy2(args.protocol, args.out/'sources/data/historical-protocol-settlements.json')
    shutil.copy2(args.protocol, args.out/'protocol.json')
    shutil.copy2(ROOT/'run_settlements.py', args.out/'sources/run_settlements.py')
    shutil.copy2(ROOT/'README.txt', args.out/'sources/README.txt')
    equations = ROOT/'dynamics-equations.md'
    if not equations.is_file():
        equations = ROOT.parent/'equations.md'
    shutil.copy2(equations, args.out/'equations.md')
    result = deepcopy(parent)
    result.update(protocolHash=hist.digest(protocol), settlementProtocol=protocol,
                  settlementChecks=[], settlementComponents=[], settlementFinancingEffects=[],
                  settlementPopulationSensitivity=[])
    for origin in protocol['originYears']:
        cases = sorted((c for c in parent['cases'] if c['originYear'] == origin), key=lambda c: c['horizon'])
        years = max(c['horizon'] for c in cases)
        for policy_index, policy in enumerate(protocol['eventScenarios']):
            base_name = 'M2-PKV-'+policy+PARENT_SUFFIX
            name = base_name+SUFFIX
            destination = args.out/'origins'/str(origin)/name
            annual, audit = hist.predict_origin(data, origin, years, old_protocol, destination,
                source_root=args.out/'sources', missing_wip_fraction=old_protocol['missingWIP']['nominal'],
                macro_data=costs, event_data=events, event_policy=policy,
                normalized_inputs=(components, national), settlement_forecast=True)
            path = audit['normalizedRevenue']
            original = json.loads((parent_root/'origins'/str(origin)/base_name/'annual.json').read_text())
            checks = check_native(destination, annual, original, path)
            result['settlementChecks'].append({'originYear': origin, 'policy': policy, 'WIP': 'nominal', **checks})
            if policy_index == 0:
                forecast = path['settlementForecast']
                result['settlementPopulationSensitivity'].append({'originYear': origin,
                    'ratePerPerson': forecast['rows'][0]['assumedCurrentPerCapita'],
                    'populationProxy': forecast['populationProxy'],
                    'differences': settlements.population_sensitivity(path, protocol['populationSensitivityPersons'])})
            accounting_name = 'PKV-accounting-'+policy+PARENT_SUFFIX
            accounting_parent = [c['predictions'][accounting_name] for c in cases]
            accounting = settlements.accounting_projection(accounting_parent, path)
            for before, after in zip(accounting_parent, accounting):
                if any(before[k] != after[k] for k in (*UNCHANGED, 'financeNet')):
                    raise ArithmeticError('Settlement accounting changed unrelated quantities')
            for case in result['cases']:
                if case['originYear'] != origin:
                    continue
                index = case['horizon']-1
                case['predictions'][name] = annual[index]
                case['predictions'][accounting_name+SUFFIX] = accounting[index]
                case['componentErrors'][name] = {k: annual[index][k]-case['actualComponents'][k] for k in hist.COMPONENTS}
                before, after = case['predictions'][base_name], annual[index]
                result['settlementFinancingEffects'].append({'originYear': origin, 'targetYear': case['targetYear'], 'model': name,
                    **{key+'Change': after[key]-before[key] for key in ('taxAndGrants', 'financeNet', 'netCost', 'result')}})
            if audit['assumedWIP']:
                for fraction in old_protocol['missingWIP']['sensitivityFractionsOfTotalTangibleAssets']:
                    destination = args.out/'origins'/str(origin)/f'{name}-WIP-{fraction}'
                    alternative, alternative_audit = hist.predict_origin(data, origin, years, old_protocol, destination,
                        source_root=args.out/'sources', missing_wip_fraction=fraction, macro_data=costs,
                        event_data=events, event_policy=policy, normalized_inputs=(components, national), settlement_forecast=True)
                    original = json.loads((parent_root/'origins'/str(origin)/f'{base_name}-WIP-{fraction}'/'annual.json').read_text())
                    checks = check_native(destination, alternative, original, alternative_audit['normalizedRevenue'])
                    result['settlementChecks'].append({'originYear': origin, 'policy': policy, 'WIP': fraction, **checks})
                    result['wipSensitivity'].extend({'originYear': origin, 'targetYear': row['year'], 'fraction': fraction,
                        'model': name, 'result': row['result'], 'differenceFromNominal': row['result']-annual[i]['result']}
                        for i, row in enumerate(alternative))
    # Component targets enter only scoring, after every prospective run is finished.
    compared_names = [prefix+policy+PARENT_SUFFIX+suffix for policy in protocol['eventScenarios']
                      for prefix in ('M2-PKV-', 'PKV-accounting-') for suffix in ('', SUFFIX)]
    other_cases = []
    for case in result['cases']:
        ledger = next(r for r in data['rows'] if r['year'] == case['targetYear'])
        target_data = inputs['revenue-component-targets-2025.json'] if ledger['year'] == 2025 else components
        target = revenue_bridge.opening_components(target_data, ledger)
        parts = target['taxComponents']
        actual_p = parts['preliminaryTax']
        component_case = {k: case[k] for k in ('originYear', 'targetYear', 'horizon')}
        component_case.update(actual={'preliminaryTax': actual_p,
            'currentYearSettlement': parts['estimatedCurrentYearSettlement'],
            'priorYearSettlementRevision': parts['priorYearSettlementDifference'],
            'settlementAndRevision': parts['estimatedCurrentYearSettlement']+parts['priorYearSettlementDifference'],
            'tax': ledger['tax']}, sourceTaxComponents=parts,
            sourceTaxRoundingResidual=target['taxRoundingResidual'], sourceId=target['sourceId'], predictions={})
        for name in compared_names:
            prediction = case['predictions'][name]
            component_case['predictions'][name] = {'preliminaryTax': prediction['preliminaryTax'],
                'settlementAndRevision': (prediction['settlementAndRevision'] if name.endswith(SUFFIX)
                    else prediction['tax']-prediction['preliminaryTax']), 'tax': prediction['tax']}
        result['settlementComponents'].append(component_case)
        other_cases.append(dict(case, actual=case['actualComponents'],
            predictions={name: case['predictions'][name] for name in compared_names}))
    result['scores'] = hist.scores(result['cases'], candidate_name=result['candidate'])
    result['componentScores'] = hist.component_scores(result['cases'])
    for key, selected in [('knownWIPScores', [c for c in result['cases'] if not c['assumedOpeningWIP']]),
                          ('sameReportYearKnownWIPScores', [c for c in result['cases'] if not c['assumedOpeningWIP'] and not c['revisedOpeningData']])]:
        result[key] = hist.scores(selected, candidate_name=result['candidate']) if selected else []
    result['settlementComponentScores'] = summarize(result['settlementComponents'], settlements.COMPONENTS, suffix=SUFFIX)
    result['settlementOtherComponentScores'] = summarize(other_cases, ('grants', 'personnel'), suffix=SUFFIX)
    selected = [dict(c, predictions={name: c['predictions'][name] for name in compared_names}) for c in result['cases']]
    result['settlementPairedScores'] = summarize(selected, hist.METRICS, suffix=SUFFIX)
    for before, after in zip(parent['cases'], result['cases']):
        if before['actual'] != after['actual'] or before['actualComponents'] != after['actualComponents']:
            raise RuntimeError('Target outcomes changed')
        if any(after['predictions'][name] != prediction for name, prediction in before['predictions'].items()):
            raise RuntimeError('A previous prediction was overwritten')
    result['settlementLimitations'] = [
        'Same five target years already used in development; the overlapping twelve cases are not twelve independent years. Historical availability of opening reports is not established.',
        'Population at year-end is a labeled proxy for November 1. The sensitivity examples are not measured proxy errors or statistical intervals.',
        'Future revisions and h2/h3 current settlements have assumed expectation zero. Source nulls are retained, not converted into observed zeros.',
        'Preliminary tax and equalisation retain the fixed fiscal-population v6 assumption and explicit government-to-SKR level transition.',
        'Remaining grant categories and personnel/pension costs are unchanged and not thereby validated.',
        'Same-year payment and zero opening tax receivable remain scenario assumptions. These result scores do not validate liquidity forecasts.',
        'The inherited v6 metadata and limitations describe the frozen parent experiment. settlement-prefixed fields describe this new variant.'
    ]
    result['settlementParentArchive'] = {'relativePath': protocol['parentRun'], 'manifestSha256': protocol['parentManifestSha256'],
        'verifiedArtifactCount': len(parent_manifest), 'oldPredictionsPreservedExactly': True}
    hist.dump(args.out/'evaluation.json', result)
    write_report(args.out, result)
    hist.dump(args.out/'environment.json', {'compiler': subprocess.check_output([dynamics.compiler(), '--version'], text=True).strip()})
    hist.dump(args.out/'manifest.json', {str(p.relative_to(args.out)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(args.out.rglob('*')) if p.is_file()})
    print(args.out/'report.html')
    return 0
