"""Versioned observations, accounting definitions and as-of selection."""
from collections import defaultdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / 'reference/m0'
METRICS = ('taxAndGrants', 'netCost', 'financeNet', 'result', 'population')
DEFINITIONS = {
    'taxAndGrants': 'reconstructed_tax_and_grants_from_rounded_accounts',
    'netCost': 'net_operating_cost_including_depreciation',
    'financeNet': 'financial_income_minus_financial_expenses',
    'result': 'annual_result_kommunen',
    'population': 'population_december_31',
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def verify_reference():
    manifest = json.loads((FROZEN / 'manifest.json').read_text())
    for name, info in manifest['files'].items():
        if hashlib.sha256((FROZEN / name).read_bytes()).hexdigest() != info['sha256']:
            raise ValueError('Frozen M0 reference changed: ' + name)
    return manifest


def local_observations():
    """Reconstruct combined revenue without inventing tax/grant splits or dates."""
    verify_reference()
    history = json.loads((FROZEN / 'history.json').read_text())
    supplement_path = ROOT / 'data/history-supplement.json'
    supplement = json.loads(supplement_path.read_text()) if supplement_path.exists() else None
    sources = ([supplement] if supplement else []) + [history]
    rows = []
    for record_source in sources:
        for r in record_source['rows']:
            total = r['reportedTotal']
            row = dict(
                municipality='0583', year=r['year'], population=total,
                taxAndGrants=r['result']+r['netCost']-r['financeNet'],
                netCost=r['netCost'], financeNet=r['financeNet'], result=r['result'],
                source=record_source['source'], sourceRelease=None, retrievedAt=record_source.get('retrievedAt', record_source.get('retrieved')),
                vintage=record_source.get('vintage', 'retrospective_2025_annual_report'),
                derivations={'taxAndGrants': 'result + netCost - financeNet; includes rounded-ledger residuals'},
            )
            if 'population' in r:
                row['cohorts'] = [v * total / sum(r['population']) for v in r['population']]
                row['derivations']['cohorts'] = 'proportional reconciliation to reported population total'
            for name in ('births', 'deaths', 'netMigration'):
                if name in r:
                    row[name] = r[name]
            rows.append(row)
    return {'schemaVersion': 1, 'scope': 'kommunen', 'moneyUnit': 'mnkr',
            'definitions': DEFINITIONS, 'evidenceClass': 'retrospective',
            'sourceNotes': supplement.get('notes', []) if supplement else [], 'rows': rows}


def validate(data):
    if data.get('role') == 'benchmark_only' or data.get('usesBenchmarkOutputs'):
        raise ValueError('Benchmark forecasts cannot be candidate observations')
    if data.get('schemaVersion') != 1 or data.get('scope') != 'kommunen' or data.get('moneyUnit') != 'mnkr':
        raise ValueError('Expected observation schema 1, scope kommunen, moneyUnit mnkr')
    if data.get('evidenceClass') not in ('retrospective', 'archived_as_of'):
        raise ValueError('Explicit evidenceClass required')
    if set(data.get('definitions', {})) != set(METRICS):
        raise ValueError('Every metric requires a reviewed definition')
    if any(not isinstance(d, str) or not d for d in data['definitions'].values()):
        raise ValueError('Definitions must be nonempty identifiers')
    seen = set()
    for r in data['rows']:
        if not isinstance(r.get('municipality'), str) or len(r['municipality']) != 4 or not r['municipality'].isdigit():
            raise ValueError('Municipality must be a four-digit string')
        if type(r.get('year')) is not int:
            raise ValueError('Integer observation year required')
        key = (r['municipality'], r['year'])
        if key in seen:
            raise ValueError('Duplicate municipality/year; explicitly select one vintage')
        seen.add(key)
        for name in METRICS:
            if type(r.get(name)) not in (float, int) or not math.isfinite(r[name]):
                raise ValueError(f'Missing/nonfinite {name} at {key}')
        if r['population'] <= 0 or r['netCost'] < 0:
            raise ValueError('Population must be positive; net costs nonnegative')
        adjustment = r.get('accountingAdjustment', 0)
        if not math.isfinite(adjustment) or abs(r['result'] - (r['taxAndGrants']-r['netCost']+r['financeNet']+adjustment)) > 1e-6:
            raise ValueError('Ledger does not reconcile; declare accountingAdjustment explicitly')
        if not r.get('source') or not r.get('vintage'):
            raise ValueError('Source and vintage required')
        for name in ('sourceRelease', 'retrievedAt'):
            if r.get(name) is not None:
                date.fromisoformat(r[name])
        if data['evidenceClass'] == 'archived_as_of' and not r.get('sourceRelease'):
            raise ValueError('Archived evaluation requires original release dates')
        if 'cohorts' in r:
            c = r['cohorts']
            if len(c) != 5 or any(not math.isfinite(v) or v < 0 for v in c) or abs(sum(c)-r['population']) > 1e-6:
                raise ValueError('Five reconciled, nonnegative cohorts required')
            for name in ('births', 'deaths'):
                if not isinstance(r.get(name), (int, float)) or not math.isfinite(r[name]) or r[name] < 0:
                    raise ValueError(f'Observed {name} required for cohort forecasting')
    return data


def load(path=None):
    return validate(json.loads(Path(path).read_text()) if path else local_observations())


def by_municipality(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['municipality']].append(row)
    return {m: sorted(rs, key=lambda x: x['year']) for m, rs in groups.items()}


def available(data, year, cutoff=None):
    """No future-period data; real-time mode additionally enforces release dates."""
    if data['evidenceClass'] == 'archived_as_of' and cutoff is None:
        raise ValueError('Archived mode requires an explicit information cutoff')
    rows = [r for r in data['rows'] if r['year'] <= year]
    if cutoff:
        date.fromisoformat(cutoff)
        rows = [r for r in rows if r.get('sourceRelease') and r['sourceRelease'] <= cutoff]
    return rows
