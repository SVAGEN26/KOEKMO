#!/usr/bin/env python3
"""Run the locked aggregate budget-response diagnostic; never fill missing data."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from motala_lab.budget_response import evaluate, validate_rows

ROOT = Path(__file__).resolve().parent


def load_rows(document, format_name):
    if format_name == 'annual-ledgers':
        rows = []
        for row in document['rows']:
            if row['scope'] != 'kommunen' or row['moneyUnit'] != 'mnkr':
                raise ValueError('Expected municipal accounts in mnkr')
            if row['sourceId'] not in document['sources']:
                raise ValueError('Missing source record')
            rows.append({'year': row['year'], 'taxAndGrants': row['tax']+row['grants'],
                         'financeNet': row['financialIncome']-row['financialExpense'],
                         'netCost': row['netCost'], 'result': row['result']})
    else:
        expected = {'municipality': '0583', 'scope': 'kommunen', 'moneyUnit': 'mnkr_current_prices',
                    'seriesTreatment': 'reported_unadjusted'}
        if any(document.get(key) != value for key, value in expected.items()):
            raise ValueError('Aggregate file must identify Motala, scope, nominal units and reported treatment')
        rows = document['rows']
        for row in rows:
            source = document['sources'][row['sourceId']]
            if not source.get('url') or not row.get('locator'):
                raise ValueError('Each aggregate row requires a source and locator')
    validate_rows(rows)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accounts', type=Path, default=ROOT/'data/annual-ledgers.json')
    parser.add_argument('--format', choices=['annual-ledgers', 'aggregate'], default='annual-ledgers')
    parser.add_argument('--out', type=Path, required=True, help='New output directory')
    args = parser.parse_args(argv)
    protocol_path = ROOT/'data/budget-response-protocol.json'
    protocol_bytes = protocol_path.read_bytes()
    input_bytes = args.accounts.read_bytes()
    rows = load_rows(json.loads(input_bytes), args.format)
    report = evaluate(rows, json.loads(protocol_bytes))
    report.update(createdAt=datetime.now(timezone.utc).isoformat(), inputFormat=args.format,
                  evidenceClass='retrospective_development_not_real_time',
                  observedYears=[row['year'] for row in rows],
                  limits=['No automatic SCB mapping or mixing with annual-report definitions.',
                          'No frozen M2 comparison attached yet; required before any candidate promotion.',
                          'No causal policy interpretation or whole-goal approval.'])
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out/'accounts.json').write_bytes(input_bytes)
    (args.out/'protocol.json').write_bytes(protocol_bytes)
    # Preserve imports and the fixed protocol path so the saved code also runs
    # outside the repository, with only Python's standard library installed.
    for relative in ('run_budget_response.py', 'motala_lab/budget_response.py',
                     'motala_lab/__init__.py', 'data/budget-response-protocol.json'):
        destination = args.out/'source'/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/relative, destination)
    report['reproduceArgumentsFromPacketDirectory'] = [
        'python3', 'source/run_budget_response.py', '--accounts', 'accounts.json',
        '--format', args.format, '--out', 'NEW_OUTPUT_DIRECTORY']
    report['sourceHashes'] = {path.relative_to(args.out).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in sorted(args.out.rglob('*')) if path.is_file()}
    (args.out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(report['status'] + ': ' + str((args.out/'report.json').resolve()))
    print('Observed years:', ', '.join(map(str, report['observedYears'])))
    print('Scored predictions:', len(report['cases']))
    return 0 if report['cases'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
