"""Paired native Modelica policy comparisons under explicit sensitivity assumptions."""
import argparse
import contextlib
import csv
from datetime import datetime, timezone
import hashlib
import html
import io
import json
from pathlib import Path
import re
import shutil

from . import dynamics


def design(config):
    """Expand one-at-a-time and joint assumptions; every policy has the same background."""
    if not isinstance(config, dict) or config.get('schemaVersion') != 1:
        raise ValueError('Expected experiment schemaVersion 1')
    years = config.get('years', 8)
    if type(years) is not int or not 1 <= years <= 100:
        raise ValueError('years must be an integer from 1 to 100')
    reference = config['reference']
    if not isinstance(reference, dict) or reference.get('scenario') not in dynamics.SCENARIOS:
        raise ValueError('A named reference scenario is required')
    base = reference.get('parameters', {})
    dynamics.scenario_source(reference['scenario'], base)
    policies = [{'id': 'reference', 'label': reference.get('label', 'Referens'), 'parameters': {}}]
    policies += config.get('alternatives', [])
    backgrounds = [{'id': 'central', 'label': 'Grundantaganden', 'parameters': {}}]
    for axis in config.get('sensitivities', []):
        for side, label in (('low', 'lågt värde'), ('high', 'högt värde')):
            backgrounds.append({'id': axis['id'] + '-' + side,
                                'label': axis['label'] + ': ' + label, 'parameters': axis[side]})
    backgrounds += config.get('backgrounds', [])
    for group in (policies, backgrounds):
        ids = [item['id'] for item in group]
        if len(ids) != len(set(ids)) or any(not re.fullmatch(r'[a-z][a-z0-9-]*', i) for i in ids):
            raise ValueError('IDs must be unique lowercase letters/digits/hyphens')
        for item in group:
            if set(item) - {'id', 'label', 'parameters'}:
                raise ValueError('Unsupported policy/background fields: ' + str(set(item) - {'id', 'label', 'parameters'}))
            if not isinstance(item.get('label'), str):
                raise ValueError('Every policy/background requires a label')
            dynamics.scenario_source(reference['scenario'], item.get('parameters', {}))
    cases = []
    for background in backgrounds:
        for policy in policies:
            shared, decision = background.get('parameters', {}), policy.get('parameters', {})
            if set(shared) & set(decision):
                raise ValueError('Sensitivity and policy override the same parameter: ' + str(set(shared) & set(decision)))
            cases.append({'id': background['id'] + '--' + policy['id'],
                          'background': background['id'], 'backgroundLabel': background['label'],
                          'policy': policy['id'], 'policyLabel': policy['label'],
                          'scenario': reference['scenario'], 'years': years,
                          'parameters': {**base, **shared, **decision}})
    if len({case['id'] for case in cases}) != len(cases):
        raise ValueError('Case IDs collide; avoid double hyphens in IDs')
    return cases


def summarize(annual):
    services = [key.removeprefix('unmetShare') for key in annual[0] if key.startswith('unmetShare')]
    return {'cumulativeResult': sum(row['result'] for row in annual),
            'endingDebt': annual[-1]['debt'], 'maximumYearEndDebt': max(row['debt'] for row in annual),
            'minimumYearEndCash': min(row['cash'] for row in annual),
            'cumulativePayroll': sum(row['payroll'] for row in annual),
            'cumulativeInvestment': sum(row['investment'] for row in annual),
            'maximumAnnualUnmetShare': max(row['unmetShare' + i] for row in annual for i in services)}


def paired_results(cases):
    references = {case['background']: case for case in cases if case['policy'] == 'reference'}
    for case in cases:
        ref = references[case['background']]
        case['delta'] = None
        if case['status'] == ref['status'] == 'success':
            case['delta'] = {key: case['summary'][key] - ref['summary'][key] for key in case['summary']}
    return cases


def write_report(output, config, cases):
    body = []
    for case in cases:
        label = html.escape(case['backgroundLabel']) + '<br><strong>' + html.escape(case['policyLabel']) + '</strong>'
        if case['status'] != 'success':
            body.append('<tr><td>' + label + '</td><td colspan="6">Körning misslyckades: '
                        + html.escape(case['error']) + '</td></tr>')
            continue
        s, delta = case['summary'], case['delta']
        values = [s['cumulativeResult'], delta['cumulativeResult'] if delta else None,
                  s['endingDebt'], delta['endingDebt'] if delta else None, 100*s['maximumAnnualUnmetShare']]
        cells = ''.join('<td>' + ('saknas' if value is None else f'{value:,.2f}') + '</td>' for value in values)
        body.append('<tr><td>' + label + '</td>' + cells + '<td><a href="runs/'
                    + case['id'] + '/report.html">Detaljer</a></td></tr>')
    central = [case for case in cases if case['background'] == 'central' and case['status'] == 'success']
    drivers = []
    for policy in central:
        alternatives = [case for case in cases if case['policy'] == policy['policy'] and case['status'] == 'success']
        totals = [case['summary']['cumulativeResult'] for case in alternatives]
        failed = sum(case['status'] != 'success' for case in cases if case['policy'] == policy['policy'])
        drivers.append('<li>' + html.escape(policy['policyLabel']) + ': ackumulerat resultat '
                       + f'{min(totals):,.2f}–{max(totals):,.2f} mnkr över de prövade antagandena. '
                       + str(failed) + ' misslyckade körningar.</li>')
    title = html.escape(config.get('title', 'Motala: scenariojämförelse'))
    lookup = {(case['background'], case['policy']): case for case in cases if case['status'] == 'success'}
    sensitivity = []
    for axis in config.get('sensitivities', []):
        low, high = (lookup.get((axis['id'] + '-' + side, 'reference')) for side in ('low', 'high'))
        if low and high:
            change = high['summary']['cumulativeResult'] - low['summary']['cumulativeResult']
            sensitivity.append((abs(change), '<tr><td>' + html.escape(axis['label']) + '</td><td>' + f'{change:,.2f}' + '</td></tr>'))
    sensitivity_table = ('<h2>Känslighet i referensen</h2><p>Ändring i ackumulerat resultat från det lägre till det högre '
                         'parametervärdet. Rangordningen gäller just de valda intervallen.</p><table><tr><th>Antagande</th>'
                         '<th>Resultatskillnad, mnkr</th></tr>' + ''.join(row for _, row in sorted(sensitivity, reverse=True)) + '</table>')
    (output / 'report.html').write_text('''<!doctype html><html lang="sv"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font:17px/1.5 system-ui;max-width:1250px;margin:2rem auto;padding:0 1rem;color:#183042}
table{border-collapse:collapse;width:100%}td,th{padding:.6rem;border-bottom:1px solid #ccd6dc;text-align:right}
td:first-child,th:first-child{text-align:left}.scroll{overflow:auto}.notice{background:#fff2d1;padding:1rem}
pre{white-space:pre-wrap}</style><title>''' + title + '</title><h1>' + title + '</h1>'
        + '<p class="notice">Känslighetsanalys med valda antaganden. Spännvidden är inget sannolikhets- eller '
        + 'konfidensintervall. En parameter i taget varieras, samt eventuella uttryckliga kombinationsscenarier. '
        + 'Övriga samspel kan finnas. Varje alternativ jämförs med referensen under samma omvärld.</p>'
        + '<p>Grundscenario före parameterändringar: ' + html.escape(dynamics.SCENARIO_DESCRIPTIONS[config['reference']['scenario']]) + '</p>'
        + '<p>Horisont: ' + str(config.get('years', 8)) + ' år från utgången av 2025. Belopp i mnkr. '
        + 'Δ anger skillnad mot referensen inom respektive antagande. Negativ Δ skuld betyder lägre skuld. '
        + 'Servicebrist är den största årsandelen otillgodosett behov inom någon verksamhet; '
        + 'den mäter inte utbildningsresultat eller hälsa.</p><ul>' + ''.join(drivers) + '</ul>' + sensitivity_table
        + '<div class="scroll"><table><tr><th>Antagande och alternativ</th><th>Ackumulerat resultat</th>'
        + '<th>Δ resultat</th><th>Slutskuld</th><th>Δ skuld</th><th>Största servicebrist, %</th>'
        + '<th>Underlag</th></tr>' + ''.join(body) + '</table></div>'
        + '<p><a href="results.csv">CSV</a> · <a href="results.json">Alla resultat och fel</a> · '
        + '<a href="design.json">Antaganden</a> · <a href="manifest.json">Filkontroller</a></p>'
        + '<details><summary>Exakta antaganden</summary><pre>'
        + html.escape(json.dumps(config, ensure_ascii=False, indent=2)) + '</pre></details></html>', encoding='utf-8')


def run(config, output):
    cases = design(config)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Preserve existing experiments; choose a new output directory')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'design.json').write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    (output / 'source').mkdir()
    shutil.copy2(__file__, output / 'source/experiments.py')
    for index, case in enumerate(cases, 1):
        target = output / 'runs' / case['id']
        parameter_file = output / (case['id'] + '.json')
        parameter_file.write_text(json.dumps(case['parameters'], indent=2) + '\n')
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                dynamics.main(['--scenario', case['scenario'], '--years', str(case['years']),
                               '--parameters', str(parameter_file), '--output', str(target)])
            case['summary'] = summarize(json.loads((target / 'annual.json').read_text()))
            case['status'] = 'success'
        except SystemExit as exc:
            case['status'], case['error'] = 'failed', str(exc)
        print(f"{index}/{len(cases)} {case['id']}: {case['status']}", flush=True)
    paired_results(cases)
    (output / 'results.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2) + '\n')
    records = []
    for case in cases:
        record = {key: case[key] for key in ('id', 'background', 'policy', 'status')}
        record.update(case.get('summary', {}))
        record.update({'delta_' + key: value for key, value in (case['delta'] or {}).items()})
        record['error'] = case.get('error', '')
        records.append(record)
    fields = list(dict.fromkeys(key for record in records for key in record))
    with (output / 'results.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(records)
    write_report(output, config, cases)
    (output / 'manifest.json').write_text(json.dumps({'model': 'MotalaDynamics-v3',
        'status': 'complete' if all(c['status'] == 'success' for c in cases) else 'contains_failed_runs',
        'caseCount': len(cases), 'artifacts': {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                                            for p in sorted(output.rglob('*')) if p.is_file()}}, indent=2) + '\n')
    print('Report: ' + str((output / 'report.html').resolve()))
    return cases


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('design', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        config = json.loads(args.design.read_text())
        output = args.output or dynamics.ROOT / 'runs' / ('comparison-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        cases = run(config, output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(str(exc))
    if any(c['status'] != 'success' for c in cases):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
