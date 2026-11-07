#!/usr/bin/env python3
"""Explain frozen Motala cost errors; never fit or generate a new forecast.

The constant-quantity PKV residual is not an identified price/pension error.
The saved input packet permits an independent replay with standard Python.
"""
import argparse
from copy import deepcopy
import hashlib
import html
import json
import math
from pathlib import Path
import shutil
from statistics import mean

ROOT = Path(__file__).resolve().parent
SUFFIX = '-normalized-PI-settlement'
TERMS = ('personnel', 'otherOperatingExpense', 'negativeOperatingRevenue',
         'depreciation', 'modelSpecificExpenseAndRounding')


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(directory, definitions_path):
    manifest = json.loads((directory/'manifest.json').read_text())
    for relative, expected in manifest.items():
        if file_hash(directory/relative) != expected:
            raise ValueError('Changed source artifact: '+relative)
    used = {}
    def read(relative):
        if relative not in manifest:
            raise ValueError('Input is not covered by parent manifest: '+relative)
        used[relative] = manifest[relative]
        return json.loads((directory/relative).read_text())
    evaluation = read('evaluation.json')
    protocol = evaluation['settlementProtocol']
    audits = []
    for origin in protocol['originYears']:
        for policy in protocol['eventScenarios']:
            relative = f'origins/{origin}/M2-PKV-{policy}{SUFFIX}/inputs.json'
            audits.append({'originYear': origin, 'policy': policy, 'audit': read(relative)})
    ledgers = read('reference/reference/annual-ledgers.json')
    return {'schemaVersion': 1, 'role': 'posthoc_cost_diagnostic_no_new_predictions',
        'originYears': protocol['originYears'], 'policies': protocol['eventScenarios'],
        'cases': evaluation['cases'], 'ledgers': ledgers, 'openingAudits': audits,
        'definitions': json.loads(definitions_path.read_text()),
        'provenance': {'sourceRun': directory.name, 'verifiedArtifactCount': len(manifest),
            'sourceManifestSha256': file_hash(directory/'manifest.json'), 'sourceFiles': used,
            'definitionCatalogSha256': file_hash(definitions_path),
            'packetRole': 'Exact parsed copies of the selected verified JSON inputs, plus the separately identified definition catalog.'}}


def analyze(packet):
    if packet['role'] != 'posthoc_cost_diagnostic_no_new_predictions':
        raise ValueError('Cost audit requires frozen retrospective predictions')
    ledger = {r['year']: r for r in packet['ledgers']['rows']}
    audits = {(r['originYear'], r['policy']): r['audit'] for r in packet['openingAudits']}
    rows = []
    checks = {'maximumCostErrorIdentityResidual': 0., 'maximumDynamicCostIdentityResidual': 0.,
              'maximumPersonnelErrorIdentityResidual': 0., 'maximumAccountingFormulaResidual': 0.,
              'maximumPensionPartitionFormulaResidual': 0.}
    for case in packet['cases']:
        actual = ledger[case['targetYear']]
        if abs(actual['payroll']+actual['pension']-case['actualComponents']['personnel']) > 1e-8:
            raise ArithmeticError('Observed personnel differs between frozen sources')
        if actual['netCost'] != case['actual']['netCost']:
            raise ArithmeticError('Observed net cost differs between frozen sources')
        for policy in packet['policies']:
            audit = audits[case['originYear'], policy]
            parameters = audit['parameters']
            native = case['predictions']['M2-PKV-'+policy+SUFFIX]
            accounting = case['predictions']['PKV-accounting-'+policy+SUFFIX]
            horizon = case['horizon']
            vintage = audit['macroForecast']['rows'][:horizon]
            if [r['year'] for r in vintage] != list(range(case['originYear']+1, case['targetYear']+1)):
                raise ValueError('Frozen price horizon mismatch')
            labor_factor = math.prod(1+r['laborPercent']/100 for r in vintage)
            other_factor = math.prod(1+r['otherPercent']/100 for r in vintage)
            expected = {'personnel': (parameters['payroll0']+parameters['pension0'])*labor_factor,
                        'otherOperatingExpense': parameters['otherExpense0']*other_factor,
                        'operatingRevenue': parameters['operatingRevenue0']*(1+parameters['feeGrowth'])**horizon,
                        'depreciation': parameters['depreciation0']}
            for key, value in expected.items():
                checks['maximumAccountingFormulaResidual'] = max(checks['maximumAccountingFormulaResidual'], abs(accounting[key]-value))
            checks['maximumPensionPartitionFormulaResidual'] = max(checks['maximumPensionPartitionFormulaResidual'],
                abs(native['pensionExpense']-parameters['pension0']*labor_factor))
            model_flows = sum(native[k] for k in ('disposalLoss', 'transitionExpense', 'extraExpense'))
            terms = {'personnel': native['personnel']-(actual['payroll']+actual['pension']),
                     'otherOperatingExpense': native['otherOperatingExpense']-actual['otherExpense'],
                     'negativeOperatingRevenue': -(native['operatingRevenue']-actual['operatingRevenue']),
                     'depreciation': native['depreciation']-actual['depreciation'],
                     'modelSpecificExpenseAndRounding': model_flows+parameters['costRounding']-actual['costRounding']}
            dynamic = {key: native[key]-accounting[key] for key in ('personnel', 'otherOperatingExpense', 'depreciation')}
            dynamic['negativeOperatingRevenue'] = -(native['operatingRevenue']-accounting['operatingRevenue'])
            dynamic['modelSpecificExpenseAndRounding'] = model_flows
            cost_error = native['netCost']-actual['netCost']
            constant_error = accounting['personnel']-(actual['payroll']+actual['pension'])
            checks['maximumCostErrorIdentityResidual'] = max(checks['maximumCostErrorIdentityResidual'], abs(sum(terms.values())-cost_error))
            checks['maximumDynamicCostIdentityResidual'] = max(checks['maximumDynamicCostIdentityResidual'],
                abs(sum(dynamic.values())-(native['netCost']-accounting['netCost'])))
            checks['maximumPersonnelErrorIdentityResidual'] = max(checks['maximumPersonnelErrorIdentityResidual'],
                abs(constant_error+dynamic['personnel']-terms['personnel']))
            rows.append({**{k: case[k] for k in ('originYear', 'targetYear', 'horizon')}, 'policy': policy,
                'nativeModel': 'M2-PKV-'+policy+SUFFIX, 'accountingModel': 'PKV-accounting-'+policy+SUFFIX,
                'netCostError': cost_error, 'netCostErrorTerms': terms,
                'dynamicCostDifference': native['netCost']-accounting['netCost'], 'dynamicCostTerms': dynamic,
                'personnel': {'openingTotal': parameters['payroll0']+parameters['pension0'],
                    'laborIndexFactor': labor_factor, 'constantQuantityProjection': accounting['personnel'],
                    'observedTotal': actual['payroll']+actual['pension'], 'nativeProjection': native['personnel'],
                    'constantQuantityResidual': constant_error, 'modelQuantityContribution': dynamic['personnel'],
                    'totalError': terms['personnel']},
                'reportedCostRounding': actual['costRounding'], 'openingCostRounding': parameters['costRounding'],
                'additionalModelFlows': {k: native[k] for k in ('disposalLoss', 'transitionExpense', 'extraExpense')},
                'revisedOpeningData': case['revisedOpeningData'], 'assumedOpeningWIP': case['assumedOpeningWIP']})
    if max(checks.values()) > 1e-6:
        raise ArithmeticError('Cost diagnostic reconciliation failed: '+str(checks))
    def stats(values):
        return {'mae': mean(abs(x) for x in values), 'bias': mean(values), 'rmse': math.sqrt(mean(x*x for x in values))}
    summaries = []
    for policy in packet['policies']:
        for horizon in sorted({r['horizon'] for r in rows}):
            selected = [r for r in rows if r['policy'] == policy and r['horizon'] == horizon]
            quantity = [r['personnel']['modelQuantityContribution'] for r in selected]
            summaries.append({'policy': policy, 'horizon': horizon, 'n': len(selected),
                'targetYears': [r['targetYear'] for r in selected],
                'netCost': stats([r['netCostError'] for r in selected]),
                'personnel': stats([r['personnel']['totalError'] for r in selected]),
                'constantQuantityPersonnel': stats([r['personnel']['constantQuantityResidual'] for r in selected]),
                'modelPersonnelQuantityContribution': {'mean': mean(quantity), 'minimum': min(quantity), 'maximum': max(quantity)},
                'costTerms': {key: stats([r['netCostErrorTerms'][key] for r in selected]) for key in TERMS}})
    return {'role': packet['role'], 'provenance': packet['provenance'], 'cases': rows,
        'summaries': summaries, 'checks': checks,
        'limitations': [
            'Post-hoc diagnosis of the same already examined historical targets. No new forecast, fitting, selection, counterfactual outcome or validation sample.',
            'The accounting residual combines national-price forecast mismatch, local pensions, wage mix, observed staffing changes and source/version effects. These causes are not separately identified.',
            'The model quantity contribution is the difference between two existing projections with the same opening totals and price path. It is not an observed staffing change or a causal estimate.',
            'The reported payroll/pension split is not harmonized across years. Only the combined operating personnel amount is diagnosed; pension finance is excluded.',
            'Component biases add to net-cost bias. Component MAEs do not add to net-cost MAE because signed errors can cancel.',
            'This diagnostic covers the twelve nominal cases under both policies. WIP alternatives remain in the unchanged parent experiment, not new observations or independent replications here.'
        ]}


def report(directory, result, definitions):
    def table(headers, rows):
        def cell(v):
            return html.escape(f'{v:.2f}' if type(v) is float else str(v))
        return '<div class="scroll"><table><tr>'+''.join('<th>'+cell(h)+'</th>' for h in headers)+'</tr>'+''.join(
            '<tr>'+''.join('<td>'+cell(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</table></div>'
    text = '''<!doctype html><html lang="sv"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Motala: uppdelning av de historiska kostnadsfelen</title>
<style>body{font:16px system-ui;max-width:1200px;margin:32px auto;padding:0 20px;color:#142630}table{border-collapse:collapse;font-variant-numeric:tabular-nums;margin:16px 0}td,th{padding:8px;border-bottom:1px solid #ccd4db;text-align:right}th{background:#e5edf2}.scroll{overflow-x:auto}.note{background:#fff0cf;padding:18px}</style>
<h1>Vad består Motalamodellens kostnadsfel av?</h1>
<p class="note">En diagnos av frysta v7-prognoser, inte en ny prognosmodell. Samma tolv fall och båda notpolicys ingår. Inga parametrar, prognoser eller målutfall ändras.</p>
<p>Personalfelet delas exakt i två termer: felet i den sparade bokföringsprognosen med oförändrade kvantiteter och den extra kostnad som modellens kvantitetsförändringar ger. Första termen är inte ett identifierat pris- eller pensionsfel: faktiska bemanningsförändringar, sammansättning och källskillnader ingår också.</p>
<p>Nästan hela personalfelet finns också i jämförelsen med oförändrade kvantiteter och samma nationella prisbana. Detta är ett skäl att först granska lokala kostnads- och personalunderlag, inte att passa anpassningstider mot ett sammanlagt resultatfel. Uppdelningen visar inte vilken del av det faktiska utfallet som beror på priser, pensioner respektive bemanning.</p>
<p>Alla belopp i mnkr. Positivt kostnadsfel betyder överskattad kostnad. Driftintäktens fel får negativt tecken i nettokostnaden. Biasbidrag kan summeras; komponenternas MAE kan inte summeras.</p>
<p><a href="evaluation.json">Alla fel och identitetskontroller</a> · <a href="input-packet.json">Verifierade indata och källdefinitioner</a> · <a href="manifest.json">Artefakthashar</a></p>
<h2>Personalkostnad: samma prisbana, olika kvantiteter</h2>'''
    text += table(['Policy', 'År framåt', 'n', 'Personal-MAE', 'Oförändrad kvantitet, MAE', 'Medelbidrag från modellens kvantiteter', 'Min', 'Max'],
        [[s['policy'], s['horizon'], s['n'], s['personnel']['mae'], s['constantQuantityPersonnel']['mae'],
          s['modelPersonnelQuantityContribution']['mean'], s['modelPersonnelQuantityContribution']['minimum'],
          s['modelPersonnelQuantityContribution']['maximum']] for s in result['summaries']])
    text += '<h2>Personalfelet i varje fall</h2>'+table(
        ['Policy', 'Startår', 'Målår', 'Utfall', 'PKV med fast kvantitet', 'PKV-restfel', 'Modellens kvantitetsbidrag', 'Hela personalfelet'],
        [[r['policy'], r['originYear'], r['targetYear'], r['personnel']['observedTotal'],
          r['personnel']['constantQuantityProjection'], r['personnel']['constantQuantityResidual'],
          r['personnel']['modelQuantityContribution'], r['personnel']['totalError']] for r in result['cases']])
    text += '<h2>Hela nettokostnadsfelet</h2><p>Sista bidraget innehåller endast angivna modellflöden för utrangering, omställning och extra kostnader samt skillnaden i redovisad avrundning. Det är ingen anpassad restpost.</p>'+table(
        ['Policy', 'Startår', 'Målår', 'Personal', 'Övrig drift', 'Minus driftintäkt', 'Avskrivning', 'Modellflöden och avrundning', 'Nettokostnadsfel'],
        [[r['policy'], r['originYear'], r['targetYear'], *[r['netCostErrorTerms'][k] for k in TERMS], r['netCostError']] for r in result['cases']])
    text += '<h2>Kontroll av kostnadsdefinitionerna</h2><p>2022 års ursprungliga personalsumma 2 187,1 jämförs med 2 186 i 2023 års omklassificerade jämförelsekolumn. Skillnaden −1,1 bevaras som versions-/avrundningsavvikelse. Den används inte för att korrigera prognoser eller lösa ut exakt löneskatt. 2023 anger pension exklusive löneskatt; rubriken i 2025 års not anger inte uttryckligen skatteplaceringen.</p>'
    text += table(['Källrapport', 'Utfallsår', 'Kolumn', 'Personal exkl. redovisad pension', 'Redovisad pension', 'Summa', 'Skattebas'],
        [[r['sourceId'], r['year'], r['columnRole'], r['personnelExcludingReportedPension'], r['reportedPension'],
          r['combinedPersonnel'], r['pensionTaxBasis']] for r in definitions['observedVersions']])
    text += '<p>Årsredovisning 2022 beskriver en väntad pensionskostnadsökning över 100 mnkr inför 2023. Det är ingen daterad punktprognos. Beloppet förs inte in som en exakt prognos eller läggs ovanpå PKV som redan innehåller pensionseffekter. Originalrapporten för 2021 gick inte att läsa på nytt; 2024 års PDF överskred hämtningens storleksgräns. Luckorna bevaras.</p>'
    text += '<p>Före en lokal pensionsbana behövs förenliga definitioner av lön, övriga arbetsgivaravgifter, driftspension, särskild löneskatt, pensionsfinans och betalningar. Ändring av en pensionsavsättning är inte hela pensionskostnaden. Inga fullständiga daterade lokala prognosbanor har återfunnits i denna källkontroll.</p>'
    text += '<ul>'+''.join('<li><a href="'+html.escape(s['url'], quote=True)+'">'+html.escape(k)+'</a>: '+html.escape(s['locator'])+'</li>' for k,s in definitions['sources'].items())+'</ul>'
    text += '<h2>Begränsningar</h2><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in result['limitations'])+'</ul></html>'
    (directory/'report.html').write_text(text, encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--run', type=Path, help='Verified frozen v7 run')
    mode.add_argument('--input-packet', type=Path, help='Saved packet for exact standalone reproduction')
    parser.add_argument('--definitions', type=Path, default=ROOT/'data/motala-personnel-sources.json')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    protected = args.run if args.run else args.input_packet.parent
    if args.out.resolve().is_relative_to(protected.resolve()):
        raise ValueError('Output must be outside preserved input directory')
    packet = collect(args.run, args.definitions) if args.run else json.loads(args.input_packet.read_text())
    original = deepcopy(packet)
    result = analyze(packet)
    if packet != original:
        raise RuntimeError('Diagnostic mutated input data')
    args.out.mkdir(parents=True, exist_ok=False)
    dump(args.out/'input-packet.json', packet)
    dump(args.out/'evaluation.json', result)
    report(args.out, result, packet['definitions'])
    shutil.copy2(Path(__file__), args.out/'run_cost_audit.py')
    dump(args.out/'manifest.json', {str(p.relative_to(args.out)): file_hash(p) for p in sorted(args.out.rglob('*')) if p.is_file()})
    print(json.dumps({'report': str(args.out/'report.html'), 'cases': len(result['cases']), 'checks': result['checks']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
