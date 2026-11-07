#!/usr/bin/env python3
"""Allocate frozen v8 grant remainders for diagnosis, without new forecasts.

All component paths are opening-share allocations of existing predictions.
They are not separate administrative forecasts or estimates of causal effects.
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

SUFFIX = '-normalized-PI-settlement-regulation'
TERMS = ('costEqualisation', 'lssEqualisation', 'propertyFee',
         'otherGeneralGrants', 'grantRoundingResidual')
SEPARATE = ('incomeEqualisation', 'regulationGrant', 'refugeeWelfareGrant')
LABELS = {'costEqualisation': 'Kostnadsutjämning', 'lssEqualisation': 'LSS',
          'propertyFee': 'Fastighetsavgift', 'otherGeneralGrants': 'Andra generella bidrag',
          'grantRoundingResidual': 'Avrundning'}
NOTE_MAPPING = {'2020-extra-general-grants': 'otherGeneralGrants'}
ROLE = 'posthoc_grant_allocation_diagnostic_no_new_predictions'


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('A finite monetary amount is required')
    return value


def collect(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    for relative, expected in manifest.items():
        if file_hash(directory/relative) != expected:
            raise ValueError('Changed source artifact: '+relative)
    used = {}
    def read(relative):
        if relative not in manifest:
            raise ValueError('Input is not covered by source manifest: '+relative)
        used[relative] = manifest[relative]
        return json.loads((directory/relative).read_text())
    evaluation = read('evaluation.json')
    protocol = evaluation['regulationProtocol']
    audits = []
    for origin in protocol['originYears']:
        for policy in protocol['eventScenarios']:
            relative = f'origins/{origin}/M2-PKV-{policy}{SUFFIX}/inputs.json'
            audits.append({'originYear': origin, 'policy': policy, 'audit': read(relative)})
    return {'schemaVersion': 1, 'role': ROLE, 'originYears': protocol['originYears'],
        'horizons': protocol['horizons'], 'policies': protocol['eventScenarios'],
        'cases': evaluation['cases'], 'componentCases': evaluation['regulationComponents'],
        'openingAudits': audits,
        'components': read('sources/data/motala-revenue-components.json'),
        'targets2025': read('sources/data/revenue-component-targets-2025.json'),
        'provenance': {'sourceRun': directory.name, 'verifiedArtifactCount': len(manifest),
            'sourceManifestSha256': file_hash(directory/'manifest.json'), 'sourceFiles': used,
            'packetRole': 'Exact parsed copies from hash-verified frozen v8 JSON artifacts.'}}


def source_row(data, year):
    if (data.get('schemaVersion') != 1 or data.get('municipality') != '0583'
            or data.get('scope') != 'kommunen' or data.get('unit') != 'mnkr'):
        raise ValueError('Motala municipal grant sources in mnkr are required')
    matches = [r for r in data['rows'] if r['year'] == year]
    if len(matches) != 1:
        raise ValueError('Exactly one declared source version required for year '+str(year))
    row = matches[0]
    if row['scope'] != 'kommunen' or row['moneyUnit'] != 'mnkr':
        raise ValueError('Wrong source row scope or unit')
    if set(row['grantComponents']) != set(SEPARATE+TERMS[:-1]):
        raise ValueError('Missing or unexpected grant categories')
    for value in (*row['grantComponents'].values(), row['grantRoundingResidual'], row['reportedGrants']):
        finite(value)
    return row


def allocation_basis(audit, source):
    path = audit['normalizedRevenue']
    note = audit['noteSeparation']
    if audit['originYear'] != source['year'] or note['originYear'] != source['year']:
        raise ValueError('Grant opening years differ')
    opening = path['openingComponents']
    for key in ('grantComponents', 'grantRoundingResidual', 'reportedGrants', 'sourceId'):
        if opening[key] != source[key]:
            raise ValueError('Opening audit differs from its declared grant source')
    before = {k: source['grantComponents'][k] for k in TERMS[:-1]}
    before['grantRoundingResidual'] = source['grantRoundingResidual']
    adjusted = deepcopy(before)
    grant_items = []
    removed = 0.
    for item in note['note']['items']:
        if item['field'] != 'grants':
            continue
        if item['id'] not in NOTE_MAPPING or item['kind'] != 'temporary_receipt':
            raise ValueError('No declared grant-component mapping for note item')
        component = NOTE_MAPPING[item['id']]
        amount = finite(item['amount'])
        excluded = item['id'] in note['excludedItemIds']
        grant_items.append(dict(item, component=component, excludedFromOpening=excluded,
                               retainedOpeningAmount=0. if excluded else amount))
        if excluded:
            adjusted[component] -= amount
            removed += amount
    anchor = finite(path['grantAnchor0'])
    if any(abs(value-removed) > 1e-8 for value in (
            note['excludedFromRecurringBase']['grants'], source['reportedGrants']-anchor)):
        raise ArithmeticError('Note removal does not reconcile to the selected grant anchor')
    if (note['reported']['grants'] != source['reportedGrants']
            or note['recurringBase']['grants'] != anchor or audit['parameters']['grants0'] != anchor):
        raise ArithmeticError('Grant anchor differs between note, parameters and revenue path')
    separate = {k: source['grantComponents'][k] for k in SEPARATE}
    denominator = anchor-sum(separate.values())
    if denominator <= 0:
        raise ValueError('Remaining grant anchor must be strictly positive')
    if abs(sum(adjusted.values())-denominator) > 1e-8:
        raise ArithmeticError('Opening grant components do not sum to the remaining anchor')
    return {'reportedComponents': before, 'adjustedComponents': adjusted,
        'separateOpeningCategories': separate, 'reportedTotalGrants': source['reportedGrants'],
        'grantAnchor': anchor, 'remainingAnchor': denominator, 'noteItems': grant_items,
        'excludedFromOtherGeneralGrants': removed,
        'sourceId': source['sourceId'], 'source': opening['source'],
        'role': 'opening_basis_for_proportional_allocation_not_new_component_forecasts'}


def analyze(packet):
    if packet['schemaVersion'] != 1 or packet['role'] != ROLE:
        raise ValueError('Frozen v8 diagnostic packet required')
    last_year = max(r['year'] for r in packet['targets2025']['rows'])
    expected = {(origin, origin+h, h) for origin in packet['originYears']
                for h in packet['horizons'] if origin+h <= last_year}
    def key(row):
        return row['originYear'], row['targetYear'], row['horizon']
    for values in (packet['cases'], packet['componentCases']):
        if len(values) != len(expected) or {key(c) for c in values} != expected:
            raise ValueError('Diagnostic must retain every declared nominal case exactly once')
    audits = {(r['originYear'], r['policy']): r['audit'] for r in packet['openingAudits']}
    required_audits = {(o, p) for o in packet['originYears'] for p in packet['policies']}
    if len(audits) != len(packet['openingAudits']) or set(audits) != required_audits:
        raise ValueError('Missing or duplicate opening audit')
    bases = {}
    for (origin, policy), audit in audits.items():
        if audit['noteSeparation']['policy'] != policy:
            raise ValueError('Opening note policy mismatch')
        bases[origin, policy] = allocation_basis(audit, source_row(packet['components'], origin))
    component_cases = {key(c): c for c in packet['componentCases']}
    rows = []
    checks = {'maximumAllocatedPredictionIdentityResidual': 0.,
        'maximumRemainingErrorIdentityResidual': 0., 'maximumWholeGrantErrorIdentityResidual': 0.,
        'maximumSourceGrantIdentityResidual': 0., 'maximumFrozenComponentDifference': 0.,
        'maximumSummaryBiasIdentityResidual': 0.}
    for case in packet['cases']:
        data = packet['targets2025'] if case['targetYear'] == 2025 else packet['components']
        target = source_row(data, case['targetYear'])
        separate_actual = {k: target['grantComponents'][k] for k in SEPARATE}
        actual = {k: target['grantComponents'][k] for k in TERMS[:-1]}
        actual['grantRoundingResidual'] = target['grantRoundingResidual']
        remaining_actual = target['reportedGrants']-sum(separate_actual.values())
        checks['maximumSourceGrantIdentityResidual'] = max(checks['maximumSourceGrantIdentityResidual'],
            abs(sum(actual.values())-remaining_actual),
            abs(target['reportedGrants']-case['actualComponents']['grants']))
        frozen = component_cases[key(case)]
        if (target['grantComponents'] != frozen['sourceGrantComponents']
                or target['grantRoundingResidual'] != frozen['sourceGrantRoundingResidual']
                or target['sourceId'] != frozen['sourceId']):
            raise ArithmeticError('Target source differs from the frozen evaluation')
        for policy in packet['policies']:
            basis = bases[case['originYear'], policy]
            for kind, prefix in (('native', 'M2-PKV-'), ('accounting', 'PKV-accounting-')):
                name = prefix+policy+SUFFIX
                prediction = case['predictions'][name]
                remaining_prediction = finite(prediction['remainingGrants'])
                factor = remaining_prediction/basis['remainingAnchor']
                allocated = {k: value*factor for k, value in basis['adjustedComponents'].items()}
                errors = {k: allocated[k]-actual[k] for k in TERMS}
                separate_errors = {k: prediction[k]-separate_actual[k] for k in SEPARATE}
                remaining_error = remaining_prediction-remaining_actual
                total_error = prediction['grants']-target['reportedGrants']
                checks['maximumAllocatedPredictionIdentityResidual'] = max(checks['maximumAllocatedPredictionIdentityResidual'],
                    abs(sum(allocated.values())-remaining_prediction))
                checks['maximumRemainingErrorIdentityResidual'] = max(checks['maximumRemainingErrorIdentityResidual'],
                    abs(sum(errors.values())-remaining_error))
                checks['maximumWholeGrantErrorIdentityResidual'] = max(checks['maximumWholeGrantErrorIdentityResidual'],
                    abs(sum(errors.values())+sum(separate_errors.values())-total_error))
                for k in (*SEPARATE, 'remainingGrants', 'grants'):
                    checks['maximumFrozenComponentDifference'] = max(checks['maximumFrozenComponentDifference'],
                        abs(prediction[k]-frozen['predictions'][name][k]))
                rows.append({**{k: case[k] for k in ('originYear', 'targetYear', 'horizon')},
                    'policy': policy, 'kind': kind, 'model': name, 'allocationFactor': factor,
                    'allocatedComponents': allocated, 'actualComponents': actual,
                    'componentErrors': errors, 'remainingPrediction': remaining_prediction,
                    'remainingActual': remaining_actual, 'remainingError': remaining_error,
                    'separateCategoryErrors': separate_errors, 'wholeGrantError': total_error,
                    'targetSourceId': target['sourceId'], 'targetSource': data['sources'][target['sourceId']],
                    'revisedOpeningData': case['revisedOpeningData'], 'assumedOpeningWIP': case['assumedOpeningWIP']})
    def stats(values):
        return {'mae': mean(abs(x) for x in values), 'bias': mean(values),
                'rmse': math.sqrt(mean(x*x for x in values))}
    summaries = []
    for policy in packet['policies']:
        for kind in ('native', 'accounting'):
            for horizon in packet['horizons']:
                selected = [r for r in rows if (r['policy'], r['kind'], r['horizon']) == (policy, kind, horizon)]
                terms = {k: stats([r['componentErrors'][k] for r in selected]) for k in TERMS}
                total = stats([r['remainingError'] for r in selected])
                checks['maximumSummaryBiasIdentityResidual'] = max(checks['maximumSummaryBiasIdentityResidual'],
                    abs(sum(s['bias'] for s in terms.values())-total['bias']))
                summaries.append({'policy': policy, 'kind': kind, 'horizon': horizon, 'n': len(selected),
                    'targetYears': [r['targetYear'] for r in selected], 'remainingGrants': total,
                    'wholeGrants': stats([r['wholeGrantError'] for r in selected]), 'components': terms})
    if max(checks.values()) > 1e-6:
        raise ArithmeticError('Grant diagnostic reconciliation failed: '+str(checks))
    return {'role': ROLE, 'provenance': packet['provenance'], 'cases': rows,
        'openingBases': [{'originYear': o, 'policy': p, **basis} for (o,p), basis in bases.items()],
        'summaries': summaries, 'checks': checks, 'limitations': [
            'Post-hoc allocation of frozen v8 forecasts on the same already examined outcomes. No new forecasts, fitted parameters, policy selection or validation sample.',
            'Every displayed component path uses its adjusted opening amount times the same remaining-grant factor. These are proportional allocations, not independently estimated administrative component forecasts.',
            'The 82.1 opening2020 grant is retained under costbase and removed under no-repeat exactly as in the frozen note policy. It is not removed from later outcomes; new or replacement funding remains uncertain.',
            'Signed opening rounding follows the same declared allocation factor; signed target rounding is kept as reported. Neither is silently assigned to another category or fitted to make a score smaller.',
            'Component errors and biases add to the remaining-grant error and bias. Component MAEs do not add to the total MAE because errors can cancel.',
            'Twelve overlapping nominal cases are displayed under two policies and two calculation variants, giving48rows, not48independent observations. WIP alternatives remain unchanged in v8 and are not new observations here.',
            'The diagnosis locates discrepancies under a declared allocation; it does not identify causal effects or justify adjusting growth rates to these targets. Original source versions and precision remain in force.',
            'Historical publication availability of opening accounts is not established. Full forecast quality and real-time forecasting have not been validated by this diagnostic.'
        ]}


def report(directory, result):
    def table(headers, rows):
        def cell(value):
            return html.escape(f'{value:.3f}' if type(value) is float else str(value))
        return '<div class="scroll"><table><tr>'+''.join('<th>'+cell(h)+'</th>' for h in headers)+'</tr>'+''.join(
            '<tr>'+''.join('<td>'+cell(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</table></div>'
    text = '''<!doctype html><html lang="sv"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Motala: diagnos av återstående bidrag</title>
<style>body{font:16px system-ui;max-width:1200px;margin:32px auto;padding:0 20px;color:#142630}table{border-collapse:collapse;font-variant-numeric:tabular-nums;margin:16px 0}td,th{padding:8px;border-bottom:1px solid #ccd4db;text-align:right}th{background:#e5edf2}.scroll{overflow-x:auto}.note{background:#fff0cf;padding:18px}li{margin:10px 0}</style>
<h1>Vad består felet i återstående bidrag av?</h1>
<p class="note">Diagnos av frysta v8-prognoser. Alla tolv fall finns kvar med båda notpolicyerna och både dynamisk modell och bokföringsjämförelse. De 48 raderna är inte 48 oberoende observationer. Inga prognoser, parametrar eller utfall ändras.</p>
<p>Den återstående bidragsprognosen fördelas efter öppningsårets belopp för kostnadsutjämning, LSS, fastighetsavgift, andra generella bidrag och avrundning. Varje belopp multipliceras med samma faktor: sparad restprognos delad med notjusterat restbelopp vid starten. Detta är proportionella allokeringar av en befintlig prognos, inte nya administrativa delprognoser.</p>
<p>Öppningsåret 2020 har 82,1 mnkr extra generella bidrag. Costbase behåller beloppet, medan no-repeat redan har tagit bort det från andra generella bidrag. Borttagningen görs inte igen och målårets utfall ändras inte. Programövergången från flykting-/välfärdsbidrag till reglering hanterades redan i v8.</p>
<p>Alla belopp är mnkr. Positivt fel betyder överskattad intäkt. Signerade komponentfel och bias summerar till restfelet; komponenternas MAE kan inte summeras. Öppningsavrundningen följer samma faktor och målårets avrundning ligger kvar separat.</p>
<p><a href="evaluation.json">Alla allokeringar, fel och kontroller</a> · <a href="input-packet.json">Frysta indata med källhänvisningar</a> · <a href="manifest.json">Filhashar</a></p>
<h2>Öppningsbelopp efter notpolicy</h2>'''
    text += table(['Startår', 'Policy', 'Borttaget övrigt bidrag', *[LABELS[k] for k in TERMS], 'Restankare'],
        [[r['originYear'], r['policy'], r['excludedFromOtherGeneralGrants'],
          *[r['adjustedComponents'][k] for k in TERMS], r['remainingAnchor']] for r in result['openingBases']])
    text += '<h2>Genomsnittliga signerade fel</h2><p>Raderna visar hur varje del bidrar till restens bias. Native är den dynamiska modellen; accounting är den bevarade bokföringsjämförelsen.</p>'+table(
        ['Policy', 'Variant', 'År framåt', 'n', *[LABELS[k] for k in TERMS], 'Restbias', 'Rest-MAE'],
        [[s['policy'], s['kind'], s['horizon'], s['n'], *[s['components'][k]['bias'] for k in TERMS],
          s['remainingGrants']['bias'], s['remainingGrants']['mae']] for s in result['summaries']])
    text += '<h2>Komponenternas felstorlek</h2>'+table(
        ['Policy', 'Variant', 'År framåt', 'n', 'Komponent', 'MAE', 'Bias', 'RMSE'],
        [[s['policy'], s['kind'], s['horizon'], s['n'], LABELS[k], v['mae'], v['bias'], v['rmse']]
         for s in result['summaries'] for k,v in s['components'].items()])
    text += '<h2>Signerade fel i varje fall</h2>'+table(
        ['Policy', 'Variant', 'Startår', 'Målår', *[LABELS[k] for k in TERMS], 'Restfel', 'Hela bidragsfelet'],
        [[r['policy'], r['kind'], r['originYear'], r['targetYear'], *[r['componentErrors'][k] for k in TERMS],
          r['remainingError'], r['wholeGrantError']] for r in result['cases']])
    text += '<h2>Begränsningar</h2><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in result['limitations'])+'</ul></html>'
    (directory/'report.html').write_text(text, encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--run', type=Path, help='Verified frozen v8 run')
    mode.add_argument('--input-packet', type=Path, help='Saved packet for exact standalone reproduction')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    protected = args.run if args.run else args.input_packet.parent
    if args.out.resolve().is_relative_to(protected.resolve()):
        raise ValueError('Output must be outside preserved input directory')
    packet = collect(args.run) if args.run else json.loads(args.input_packet.read_text())
    original = deepcopy(packet)
    result = analyze(packet)
    if packet != original:
        raise RuntimeError('Diagnostic mutated frozen inputs')
    args.out.mkdir(parents=True, exist_ok=False)
    dump(args.out/'input-packet.json', packet)
    dump(args.out/'evaluation.json', result)
    report(args.out, result)
    shutil.copy2(Path(__file__), args.out/'run_grant_audit.py')
    dump(args.out/'manifest.json', {str(p.relative_to(args.out)): file_hash(p) for p in sorted(args.out.rglob('*')) if p.is_file()})
    print(json.dumps({'report': str(args.out/'report.html'), 'cases': len(result['cases']), 'checks': result['checks']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
