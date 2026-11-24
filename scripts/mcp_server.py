#!/usr/bin/env python3
"""Local MCP server: let an AI assistant run a municipality's economy year by year.

    python3 scripts/mcp_server.py                 # stdio (Claude Code, Claude Desktop, LM Studio, Ollama MCP clients)
    python3 scripts/mcp_server.py --http 3001     # Streamable HTTP on http://127.0.0.1:3001/mcp, like OMEdit's server

The model is the project's own Modelica library, simulated with native OpenModelica
(set OMC to the omc executable if it is not on PATH). Nothing leaves the machine: the
HTTP transport binds to 127.0.0.1 and refuses browser requests from other origins.

An assistant starts a session for a municipality and base year, sets decisions for
the coming year (tax rate, investments, interest, wages, migration ...), advances one
year at a time and reads the accounts. Decisions for a year that has been simulated
are fixed. The session log keeps every decision with its stated reason, and
save_session writes it to build/mcp/sessions/ together with a Modelica model that
reproduces the run in OMEdit.

Only parameters of Kommunekonomi.Assumptions can be set, and only with numbers or
booleans of the declared size; no Modelica text from the client reaches the compiler.
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'build' / 'mcp'
LIBRARY = ROOT / 'modelica' / 'Kommunekonomi.mo'
OMC = os.environ.get('OMC') or shutil.which('omc')
PROTOCOLS = ('2025-06-18', '2025-03-26', '2024-11-05')
SERVER_INFO = {'name': 'koekmo', 'title': 'KOEKMO', 'version': '0.1.0'}
MODELS = ('Annual', 'Continuous')
MAX_HORIZON = 15
REPORTED = ('population', 'tax', 'grants', 'cost', 'payroll', 'otherOperatingExpense', 'operatingRevenue',
            'depreciation', 'interest', 'result', 'resultShare', 'annualInvestment', 'operatingCash',
            'borrowing', 'repayment', 'debt', 'cash', 'assets', 'serviceVolume', 'wageIndex', 'annualInterestRate')
CHECKS = ('populationBalance', 'assetBalance', 'cashBalance', 'debtBalance', 'equityBalance')
CORE_DECISIONS = ('taxRatePath', 'investmentPath', 'interestRatePath', 'wageGrowthPath', 'priceGrowthPath',
                  'productivityGrowth', 'migrationDeltaPath', 'serviceAdjustment', 'liquidityPolicy', 'cashReserve',
                  'constructionYears', 'constructionShare', 'workingCapitalEnabled', 'collectionDays', 'paymentDays',
                  'rateShock', 'rateShockTime', 'rateFixingYears', 'inflationShock', 'inflationPersistence',
                  'inflationWagePassThrough', 'inflationPensionPassThrough', 'inflationRateResponse', 'inflationGrantCompensation')
RATE_FIXING = json.loads((ROOT / 'data' / 'rate-fixing.json').read_text())
SCENARIOS = {
    'base': 'The model\'s default assumptions.',
    'higherInterest': 'The market rate for new and refixed loans 3 percentage points higher from 1 January of the first forecast year. '
                      'It reaches the average rate at the pace of the average fixed-rate period (from the annual report where known, else 3 years).',
    'higherInflation': 'Inflation 3 percentage points above the price path in the first forecast year, half of it left each year after. '
                       'Prices of other costs follow at once. Wages and the tax base (0.4 of it), pension cost (8 times it, above '
                       'its path, and back when inflation is over) and the market rate (0.5 per point) follow the mean extra '
                       'inflation of the two years before. General grants stay fixed in kronor unless '
                       'inflationGrantCompensation is set. The shares are set after 2022-2025 in the county\'s municipalities.',
}


def rate_fixing(code, year):
    return RATE_FIXING['municipalities'].get(code, {}).get(str(year), RATE_FIXING['default'])


def scenario_values(name, m, base_year):
    if name not in SCENARIOS:
        raise ValueError(f'scenario is one of {list(SCENARIOS)}')
    if name == 'higherInterest':
        return {'rateShock': 0.03, 'rateShockTime': float(base_year + 1), 'rateFixingYears': float(rate_fixing(m['code'], base_year)['years'])}
    if name == 'higherInflation':
        return {'inflationShock': 0.03, 'inflationPersistence': 0.5, 'rateFixingYears': float(rate_fixing(m['code'], base_year)['years'])}
    return {}


def log(*args):
    print(*args, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- municipalities and parameters

def municipalities():
    out = {}
    for path in sorted((ROOT / 'data' / 'municipalities').glob('*/base-years.json')):
        data = json.loads(path.read_text())
        code = path.parent.name
        package = data['packageName']
        file = ROOT / 'modelica' / ('Motala.mo' if package == 'Motala' else f'municipalities/{package}.mo')
        if not file.exists():
            continue
        skr = ROOT / ('data/skr-revenue-path.json' if code == '0583' else f'data/municipalities/{code}/skr-revenue-path.json')
        out[code] = {'code': code, 'name': data['name'], 'package': package, 'file': file,
                     'baseYears': sorted(int(y) for y in data['years']), 'skr': skr if skr.exists() else None,
                     'accounts': data['years']}
    return out


def _skip_balanced(text, i, open_char, close_char):
    depth = 0
    while i < len(text):
        c = text[i]
        if c == '"':
            i = text.index('"', i + 1)
        elif c == open_char:
            depth += 1
        elif c == close_char:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError('unbalanced')


def parameter_catalogue():
    """Parameters of Kommunekonomi.Assumptions: name, type, size and description, read from the library."""
    text = LIBRARY.read_text()
    start = text.index('partial model Assumptions "')
    block = text[start:text.index('initial equation', start)]
    catalogue = {}
    for m in re.finditer(r'(?m)^\s*(final\s+)?parameter\s+(Real|Integer|Boolean|Units\.\w+)\s+(\w+)', block):
        final, kind, name = m.group(1), m.group(2), m.group(3)
        i = m.end()
        dims = None
        if block[i] == '[':
            j = block.index(']', i)
            dims = block[i + 1:j].replace(' ', '')
            i = j + 1
        while block[i] == ' ':
            i += 1
        if block[i] == '(':
            i = _skip_balanced(block, i, '(', ')')
        description = ''
        depth = 0
        while i < len(block):  # skip the default expression up to its description or the end of the statement
            c = block[i]
            if c in '({':
                depth += 1
            elif c in ')}':
                depth -= 1
            elif c == '"' and depth == 0:
                j = block.index('"', i + 1)
                description = block[i + 1:j]
                i = j + 1
                continue
            elif c == ';' and depth == 0:
                break
            i += 1
        if final:
            continue
        if dims is None:
            shape = 'scalar'
        elif dims == 'horizon':
            shape = 'perYear'
        elif dims.startswith('horizon,'):
            shape = 'perYearGroups'
        else:
            shape = 'vector'
        size = None
        if shape == 'vector':
            size = int(dims) if dims.isdigit() else None
        elif shape == 'perYearGroups':
            size = int(dims.split(',')[1]) if dims.split(',')[1].isdigit() else None
        if shape != 'scalar' and size is None and shape != 'perYear':
            continue
        if name in ('horizon',):
            continue
        # Units.Money and the other unit types are Real with a unit (Kommunekonomi.Units).
        unit = {'type': 'Real', 'unitType': kind.split('.', 1)[1]} if kind.startswith('Units.') else {'type': kind}
        catalogue[name] = {'name': name, **unit, 'shape': shape, 'size': size, 'description': ' '.join(description.split())}
    return catalogue


# ---------------------------------------------------------------- OpenModelica results (.mat v4)

def read_mat(path):
    """Read an OpenModelica result file (MATLAB v4, binTrans): {name: [values per output point]} and descriptions."""
    data = path.read_bytes()
    pos = 0
    matrices = {}
    while pos < len(data):
        mopt, rows, cols, imag, namelen = struct.unpack_from('<5i', data, pos)
        pos += 20
        name = data[pos:pos + namelen - 1].decode('latin-1')
        pos += namelen
        precision = (mopt % 100) // 10
        fmt, size = {0: ('d', 8), 1: ('f', 4), 2: ('i', 4), 3: ('h', 2), 4: ('H', 2), 5: ('B', 1)}[precision]
        count = rows * cols
        values = struct.unpack_from(f'<{count}{fmt}', data, pos)
        pos += count * size
        matrices[name] = (rows, cols, values, mopt % 10 == 1)
    def strings(key):
        rows, cols, values, _ = matrices[key]
        # binTrans: one string per column, rows characters long
        return [bytes(int(values[c * rows + r]) for r in range(rows)).decode('utf-8', 'replace').rstrip('\x00 ') for c in range(cols)]
    names, descriptions = strings('name'), strings('description')
    info_rows, _, info, _ = matrices['dataInfo']
    sets = {}
    for key in ('data_1', 'data_2'):
        rows, cols, values, _ = matrices[key]
        sets[key] = [values[c * rows:(c + 1) * rows] for c in range(cols)]  # one column per time point
    series = {}
    for k, name in enumerate(names):
        which, index = int(info[k * info_rows]), int(info[k * info_rows + 1])
        source = sets['data_1' if which == 1 else 'data_2'] if which in (1, 2) else sets['data_2']
        column = abs(index) - 1 if which in (1, 2) else 0
        sign = -1 if index < 0 else 1
        series[name] = [sign * point[column] for point in source]
    return series, dict(zip(names, descriptions))


# ---------------------------------------------------------------- simulation

_locks = {}
_locks_guard = threading.Lock()


def literal(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return f'{value:.12g}'
    return '{' + ', '.join(literal(v) for v in value) + '}'


def run_source(m, model, base_year, horizon, overrides):
    package = m['package']
    if f'olderShares{base_year}' in m['file'].read_text():
        older = f'{package}.Data.olderShares{base_year}'
    else:
        older = f'{package}.Data.SCB.olderShares({package}.Data.SCB.{package.lower()}{base_year}.population)'
    mods = [f'base = {package}.Data.{package.lower()}{base_year}', f'olderShares = {older}', f'horizon = {horizon}']
    mods += [f'{name} = {literal(value)}' for name, value in sorted(overrides.items())]
    return f'model Run\n  extends {package}.{model}(\n    ' + ',\n    '.join(mods) + ');\nend Run;\n'


def simulate(m, model, base_year, horizon, years, overrides):
    if not OMC:
        raise RuntimeError('OpenModelica (omc) not found; set OMC to the omc executable')
    source = run_source(m, model, base_year, horizon, overrides)
    intervals = years * (12 if model == 'Continuous' else 1)
    digest = hashlib.sha256((source + str(years) + LIBRARY.read_text() + m['file'].read_text()).encode()).hexdigest()[:20]
    directory = WORK / 'runs' / digest
    result = directory / 'Run_res.mat'
    with _locks_guard:
        lock = _locks.setdefault(digest, threading.Lock())
    with lock:
        if not result.exists():
            directory.mkdir(parents=True, exist_ok=True)
            (directory / 'Run.mo').write_text(source)
            (directory / 'run.mos').write_text(
                f'loadFile({json.dumps(str(LIBRARY))}); getErrorString();\n'
                f'loadFile({json.dumps(str(m["file"]))}); getErrorString();\n'
                'loadFile("Run.mo"); getErrorString();\n'
                f'simulate(Run, startTime = {base_year}, stopTime = {base_year + years}, numberOfIntervals = {intervals}); getErrorString();\n')
            process = subprocess.run([OMC, 'run.mos'], cwd=directory, capture_output=True, text=True, timeout=600)
            if not result.exists():
                (directory / 'omc.log').write_text(process.stdout + process.stderr)
                messages = re.findall(r'(?:Error|assert)[^\n]*', process.stdout)
                raise RuntimeError('Simulation failed: ' + ('; '.join(messages[:5]) or process.stdout[-1500:]))
            (directory / 'omc.log').write_text(process.stdout + process.stderr)
            log_text = process.stdout
            failed = re.search(r'simulation terminated by an assertion[^\n]*|LOG_ASSERT[^\n]*', log_text)
            if failed:
                result.unlink()
                raise RuntimeError('Simulation stopped: ' + failed.group(0))
    series, descriptions = read_mat(result)
    return series, descriptions, source


def year_rows(series, base_year, years, names):
    times = series['time']
    rows = []
    for year in range(base_year, base_year + years + 1):
        indices = [i for i, t in enumerate(times) if abs(t - year) < 1e-9]
        if not indices:
            continue
        i = indices[-1]  # the last point at a year is after the year-end event
        rows.append({'year': year, **{n: round(series[n][i], 6) for n in names if n in series}})
    return rows


# ---------------------------------------------------------------- sessions

SESSIONS = {}


class Session:
    def __init__(self, municipality, base_year, model, horizon):
        self.id = uuid.uuid4().hex[:12]
        self.m, self.base_year, self.model, self.horizon = municipality, base_year, model, horizon
        self.current = 0  # simulated years
        self.decisions = {}  # name -> full value (scalar/vector) or {year: value} for per-year parameters
        self.defaults = {}
        self.log = []
        self.rows = []

    def overrides(self):
        out = {}
        for name, value in self.decisions.items():
            spec = CATALOGUE[name]
            if spec['shape'] in ('perYear', 'perYearGroups') and isinstance(value, dict):
                full = list(self.defaults[name])
                for year, v in value.items():
                    full[int(year) - self.base_year - 1] = v
                out[name] = full
            else:
                out[name] = value
        return out

    def describe(self):
        return {'session': self.id, 'municipality': self.m['code'], 'name': self.m['name'], 'model': self.model,
                'baseYear': self.base_year, 'horizon': self.horizon, 'simulatedThrough': self.base_year + self.current,
                'nextYear': self.base_year + self.current + 1 if self.current < self.horizon else None}


def default_values(series, horizon):
    out = {}
    for name, spec in CATALOGUE.items():
        if spec['shape'] == 'scalar' and name in series:
            out[name] = series[name][0]
        elif spec['shape'] == 'perYear':
            values = [series.get(f'{name}[{i}]') for i in range(1, horizon + 1)]
            if all(v is not None for v in values):
                out[name] = [v[0] for v in values]
        elif spec['shape'] == 'perYearGroups':
            values = [[series.get(f'{name}[{i},{j}]') for j in range(1, spec['size'] + 1)] for i in range(1, horizon + 1)]
            if all(v is not None for row in values for v in row):
                out[name] = [[v[0] for v in row] for row in values]
        elif spec['shape'] == 'vector':
            values = [series.get(f'{name}[{i}]') for i in range(1, spec['size'] + 1)]
            if all(v is not None for v in values):
                out[name] = [v[0] for v in values]
    return out


def check_value(name, value, horizon, per_year):
    if name not in CATALOGUE:
        raise ValueError(f'Unknown parameter {name}; see list_parameters')
    spec = CATALOGUE[name]

    def number(v):
        if spec['type'] == 'Boolean':
            if not isinstance(v, bool):
                raise ValueError(f'{name} takes true or false')
            return v
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError(f'{name} takes finite numbers')
        if spec['type'] == 'Integer':
            if int(v) != v:
                raise ValueError(f'{name} takes whole numbers')
            return int(v)
        return float(v)

    def vector(v, size):
        if not isinstance(v, list) or len(v) != size:
            raise ValueError(f'{name} takes a list of {size} numbers')
        return [number(x) for x in v]

    shape = spec['shape']
    if shape == 'scalar':
        return number(value)
    if shape == 'vector':
        return vector(value, spec['size'])
    if shape == 'perYear':
        return number(value) if per_year else vector(value, horizon)
    if per_year:
        return vector(value, spec['size'])
    if not isinstance(value, list) or len(value) != horizon:
        raise ValueError(f'{name} takes {horizon} rows of {spec["size"]} numbers')
    return [vector(row, spec['size']) for row in value]


# ---------------------------------------------------------------- tools

def tool_list_municipalities(_):
    return {'municipalities': [{'code': m['code'], 'name': m['name'], 'package': m['package'], 'baseYears': m['baseYears'],
                                'skrReference': m['skr'] is not None} for m in MUNICIPALITIES.values()],
            'models': {'Annual': 'One step per year, as the site runs it.',
                       'Continuous': 'Stocks and flows with continuous time within the year (Kommunekonomi.Continuous).'}}


def tool_list_parameters(args):
    names = CATALOGUE if args.get('all') else [n for n in CORE_DECISIONS if n in CATALOGUE]
    return {'parameters': [CATALOGUE[n] for n in names], 'scenarios': SCENARIOS,
            'note': 'perYear parameters take one value per forecast year; set them year by year with set_decisions(year=...). '
                    'Growth rates are shares (0.03 = 3 %), taxRate is in percent, amounts in mnkr. '
                    'Pass all=true for every parameter of Kommunekonomi.Assumptions.'}


def municipality(code):
    if code not in MUNICIPALITIES:
        raise ValueError(f'Unknown municipality {code}; see list_municipalities')
    return MUNICIPALITIES[code]


def tool_start_session(args):
    m = municipality(str(args.get('municipality', '0583')))
    base_year = int(args.get('baseYear', max(m['baseYears'])))
    if base_year not in m['baseYears']:
        raise ValueError(f'{m["name"]} has base years {m["baseYears"]}')
    model = args.get('model', 'Annual')
    if model not in MODELS:
        raise ValueError(f'model is one of {MODELS}')
    horizon = int(args.get('horizon', 8))
    if not 1 <= horizon <= MAX_HORIZON:
        raise ValueError(f'horizon is 1-{MAX_HORIZON} years')
    session = Session(m, base_year, model, horizon)
    series, _, _ = simulate(m, model, base_year, horizon, horizon, {})
    session.defaults = default_values(series, horizon)
    scenario = args.get('scenario', 'base')
    preset = scenario_values(scenario, m, base_year)
    if preset:
        session.decisions.update(preset)
        session.log.append({'year': None, 'values': preset, 'reason': f'scenario {scenario}: {SCENARIOS[scenario]}'})
    SESSIONS[session.id] = session
    base_row = year_rows(series, base_year, 0, REPORTED)[0]
    return {**session.describe(), 'scenario': scenario, 'scenarioValues': preset,
            'rateFixing': rate_fixing(m['code'], base_year), 'accounts': base_row,
            'defaults': {n: session.defaults[n] for n in CORE_DECISIONS if n in session.defaults},
            'information': f'The base year is the accounts of {base_year}. Decide for {base_year + 1}, then call advance. '
                           'Defaults are the model\'s illustrative assumptions, not a forecast.'}


def get_session(args):
    sid = args.get('session')
    if sid not in SESSIONS:
        raise ValueError('Unknown session; call start_session')
    return SESSIONS[sid]


def tool_set_decisions(args):
    s = get_session(args)
    values = args.get('values') or {}
    if not isinstance(values, dict) or not values:
        raise ValueError('values is an object of parameter names and values')
    year = args.get('year')
    first_open = s.base_year + s.current + 1
    if year is not None:
        year = int(year)
        if not s.base_year < year <= s.base_year + s.horizon:
            raise ValueError(f'year is {s.base_year + 1}-{s.base_year + s.horizon}')
        if year < first_open:
            raise ValueError(f'{year} has been simulated; decisions from {first_open} can change')
    changed = {}
    for name, value in values.items():
        spec = CATALOGUE.get(name)
        per_year = year is not None and spec is not None and spec['shape'] in ('perYear', 'perYearGroups')
        checked = check_value(name, value, s.horizon, per_year)
        if per_year:
            years = range(year, s.base_year + s.horizon + 1) if args.get('carryForward', True) else [year]
            current = s.decisions.get(name)
            current = dict(current) if isinstance(current, dict) else {}
            for y in years:
                current[str(y)] = checked
            s.decisions[name] = current
        else:
            if s.current > 0:
                raise ValueError(f'{name} applies to every year; it can only be set before the first advance')
            s.decisions[name] = checked
        changed[name] = checked
    s.log.append({'year': year, 'values': changed, 'reason': args.get('reason', '')})
    return {**s.describe(), 'set': changed, 'decisions': s.decisions}


def tool_advance(args):
    s = get_session(args)
    years = int(args.get('years', 1))
    if years < 1 or s.current + years > s.horizon:
        raise ValueError(f'{s.horizon - s.current} years remain')
    stop = s.current + years
    series, _, source = simulate(s.m, s.model, s.base_year, s.horizon, stop, s.overrides())
    rows = year_rows(series, s.base_year, stop, REPORTED + CHECKS)
    new = [r for r in rows if r['year'] > s.base_year + s.current]
    s.rows = rows
    s.current = stop
    for row in new:
        checks = {k: row.pop(k) for k in CHECKS if k in row}
        row['checksOk'] = all(abs(v) < 1e-6 for v in checks.values())
    reference = skr_reference(s.m)
    for row in new:
        ref = reference.get(row['year'])
        if ref:
            row['skr'] = ref
    out = {**s.describe(), 'years': new}
    if s.model == 'Continuous' and args.get('monthly'):
        times = series['time']
        out['monthly'] = [{'time': round(t, 4), 'cash': round(series['finance.cash.level'][i], 3),
                           'debt': round(-series['finance.debt.level'][i], 3)}
                          for i, t in enumerate(times) if t > s.base_year + stop - years]
    return out


def tool_get_results(args):
    s = get_session(args)
    names = args.get('variables') or list(REPORTED)
    if s.current == 0:
        return {**s.describe(), 'years': []}
    series, descriptions, _ = simulate(s.m, s.model, s.base_year, s.horizon, s.current, s.overrides())
    unknown = [n for n in names if n not in series]
    if unknown:
        raise ValueError(f'Unknown variables {unknown}')
    return {**s.describe(), 'years': year_rows(series, s.base_year, s.current, names),
            'descriptions': {n: descriptions.get(n, '') for n in names}}


def tool_run_scenario(args):
    m = municipality(str(args.get('municipality', '0583')))
    base_year = int(args.get('baseYear', max(m['baseYears'])))
    if base_year not in m['baseYears']:
        raise ValueError(f'{m["name"]} has base years {m["baseYears"]}')
    model = args.get('model', 'Annual')
    if model not in MODELS:
        raise ValueError(f'model is one of {MODELS}')
    horizon = int(args.get('horizon', 8))
    if not 1 <= horizon <= MAX_HORIZON:
        raise ValueError(f'horizon is 1-{MAX_HORIZON} years')
    overrides = scenario_values(args.get('scenario', 'base'), m, base_year)
    overrides.update({name: check_value(name, value, horizon, False) for name, value in (args.get('values') or {}).items()})
    series, _, _ = simulate(m, model, base_year, horizon, horizon, overrides)
    rows = year_rows(series, base_year, horizon, REPORTED + CHECKS)
    return {'municipality': m['code'], 'name': m['name'], 'model': model, 'baseYear': base_year, 'years': rows}


def skr_reference(m):
    if not m['skr']:
        return {}
    data = json.loads(m['skr'].read_text())
    return {row['year']: {'tax': row['tax'], 'grants': row['grants'], 'circular': data.get('source', {}).get('circular', '26:28')}
            for row in data['rows']}


def tool_reference(args):
    m = municipality(str(args.get('municipality', '0583')))
    out = {'municipality': m['code'], 'name': m['name']}
    if m['skr']:
        data = json.loads(m['skr'].read_text())
        out['skr'] = {'rows': [{k: row[k] for k in ('year', 'tax', 'grants', 'population')} for row in data['rows']],
                      'source': data.get('source')}
    keys = ('tax', 'grants', 'payroll', 'pension', 'otherOperatingExpense', 'operatingRevenue', 'depreciation',
            'financialIncome', 'interestExpense', 'otherFinancialExpense', 'debt', 'cash', 'assets', 'investment', 'taxRate')
    out['accounts'] = {year: {k: record[k] for k in keys if k in record} for year, record in sorted(m['accounts'].items())}
    out['note'] = ('Accounts are outcomes from SCB\'s account summary (kommunen), mnkr. In a test from an earlier base year '
                   'they are the answer, not input: decide only with what was known at the base year. '
                   'SKR figures are quoted with reference; the workbook is not redistributed.')
    return out


def tool_save_session(args):
    s = get_session(args)
    directory = WORK / 'sessions'
    directory.mkdir(parents=True, exist_ok=True)
    source = run_source(s.m, s.model, s.base_year, s.horizon, s.overrides()).replace('model Run', f'model Session_{s.id}', 1).replace('end Run;', f'end Session_{s.id};')
    (directory / f'{s.id}.mo').write_text(source)
    record = {**s.describe(), 'decisions': s.decisions, 'log': s.log, 'years': s.rows,
              'modelica': str((directory / f'{s.id}.mo').relative_to(ROOT))}
    (directory / f'{s.id}.json').write_text(json.dumps(record, ensure_ascii=False, indent=1) + '\n')
    return {'saved': str((directory / f'{s.id}.json').relative_to(ROOT)), 'modelica': record['modelica'],
            'open': f'Load modelica/Kommunekonomi.mo and {s.m["file"].relative_to(ROOT)} in OMEdit, then the .mo file, and simulate Session_{s.id} '
                    f'from {s.base_year} to {s.base_year + s.horizon}.'}


TOOLS = {
    'list_municipalities': (tool_list_municipalities, 'List the municipalities and base years the model can start from, and the two model variants.', {}),
    'list_parameters': (tool_list_parameters, 'List the decisions and assumptions that can be set, with type, size and description (Swedish). By default the core decisions; all=true lists every parameter.',
                        {'all': {'type': 'boolean'}}),
    'start_session': (tool_start_session, 'Start a run for a municipality from the closing accounts of a base year. Returns the base-year accounts and the default decisions.',
                      {'municipality': {'type': 'string', 'description': 'Municipality code, for example 0583 (Motala)'},
                       'baseYear': {'type': 'integer', 'description': 'Base year with closing accounts (2020-2025); default the latest'},
                       'model': {'type': 'string', 'enum': list(MODELS), 'description': 'Annual (default) or Continuous'},
                       'horizon': {'type': 'integer', 'description': f'Years to plan, 1-{MAX_HORIZON}; default 8'},
                       'scenario': {'type': 'string', 'enum': list(SCENARIOS), 'description': 'Starting scenario; higherInterest raises the market rate 3 percentage points'}}),
    'set_decisions': (tool_set_decisions, 'Set decisions before advancing. With year, per-year parameters (investmentPath, interestRatePath, wageGrowthPath ...) change from that year on (carryForward=false for that year only). Without year, set a whole parameter before the first advance. Give a reason; it is kept in the session log.',
                      {'session': {'type': 'string'}, 'year': {'type': 'integer'}, 'values': {'type': 'object'},
                       'carryForward': {'type': 'boolean'}, 'reason': {'type': 'string'}}),
    'advance': (tool_advance, 'Simulate the next year(s) with the decisions so far and return the accounts, balance checks and the SKR reference for tax and grants where there is one. monthly=true adds cash and debt month by month (Continuous model).',
                {'session': {'type': 'string'}, 'years': {'type': 'integer'}, 'monthly': {'type': 'boolean'}}),
    'get_results': (tool_get_results, 'Return chosen output variables for the simulated years, with descriptions.',
                    {'session': {'type': 'string'}, 'variables': {'type': 'array', 'items': {'type': 'string'}}}),
    'run_scenario': (tool_run_scenario, 'Run a whole scenario at once without a session.',
                     {'municipality': {'type': 'string'}, 'baseYear': {'type': 'integer'}, 'model': {'type': 'string', 'enum': list(MODELS)},
                      'horizon': {'type': 'integer'}, 'scenario': {'type': 'string', 'enum': list(SCENARIOS)}, 'values': {'type': 'object'}}),
    'reference': (tool_reference, 'SKR 26:28 tax and grants for the municipality (with citation) and its closing accounts 2020-2025 from SCB.',
                  {'municipality': {'type': 'string'}}),
    'save_session': (tool_save_session, 'Save the session (decisions, reasons, results) as JSON and as a Modelica model that reproduces it in OMEdit.',
                     {'session': {'type': 'string'}}),
}
REQUIRED = {'set_decisions': ['session', 'values'], 'advance': ['session'], 'get_results': ['session'], 'save_session': ['session']}

PROMPTS = {
    'budget_round': {
        'description': 'Run a municipality\'s budget year by year as its finance committee.',
        'arguments': [{'name': 'municipality', 'description': 'Code, for example 0583', 'required': False},
                      {'name': 'goal', 'description': 'What the committee is aiming for', 'required': False}],
        'text': ('You are the finance committee of municipality {municipality}. Goal: {goal}.\n'
                 'Call start_session, read the accounts and list_parameters. For each year: decide the tax rate, investments '
                 'and anything else you choose with set_decisions (give a short reason), call advance for one year, and read the '
                 'result, debt and cash. A common financial target is a result of at least 2 % of tax and grants. '
                 'Do not use outcomes after the base year as inputs. When done, call save_session and summarise the decisions '
                 'and their effect.')},
}


def call_tool(name, args):
    if name not in TOOLS:
        raise ValueError(f'Unknown tool {name}')
    for key in REQUIRED.get(name, []):
        if key not in args:
            raise ValueError(f'{key} is required')
    return TOOLS[name][0](args)


# ---------------------------------------------------------------- JSON-RPC

def handle(message):
    """Handle one JSON-RPC message; return the response, or None for a notification."""
    method, mid = message.get('method'), message.get('id')
    params = message.get('params') or {}
    if mid is None:
        return None
    try:
        if method == 'initialize':
            requested = params.get('protocolVersion')
            result = {'protocolVersion': requested if requested in PROTOCOLS else PROTOCOLS[0],
                      'capabilities': {'tools': {'listChanged': False}, 'prompts': {'listChanged': False}},
                      'serverInfo': SERVER_INFO,
                      'instructions': 'Municipal economy model for Swedish municipalities (Motala and Östergötland). '
                                      'Start with list_municipalities, then start_session, set_decisions and advance year by year.'}
        elif method == 'ping':
            result = {}
        elif method == 'tools/list':
            result = {'tools': [{'name': n, 'description': d, 'inputSchema': {'type': 'object', 'properties': p, 'required': REQUIRED.get(n, [])}}
                                for n, (_, d, p) in TOOLS.items()]}
        elif method == 'tools/call':
            try:
                data = call_tool(params.get('name'), params.get('arguments') or {})
                result = {'content': [{'type': 'text', 'text': json.dumps(data, ensure_ascii=False)}], 'structuredContent': data, 'isError': False}
            except (ValueError, RuntimeError, KeyError) as e:
                result = {'content': [{'type': 'text', 'text': str(e)}], 'isError': True}
        elif method == 'prompts/list':
            result = {'prompts': [{'name': n, 'description': p['description'], 'arguments': p['arguments']} for n, p in PROMPTS.items()]}
        elif method == 'prompts/get':
            p = PROMPTS.get(params.get('name'))
            if not p:
                raise ValueError('Unknown prompt')
            a = params.get('arguments') or {}
            text = p['text'].format(municipality=a.get('municipality', '0583'), goal=a.get('goal', 'a sound economy within the financial targets'))
            result = {'description': p['description'], 'messages': [{'role': 'user', 'content': {'type': 'text', 'text': text}}]}
        else:
            return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32601, 'message': f'Method not found: {method}'}}
        return {'jsonrpc': '2.0', 'id': mid, 'result': result}
    except Exception as e:  # noqa: BLE001 - report every failure to the client
        return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32603, 'message': str(e)}}


def serve_stdio():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Parse error'}}), flush=True)
            continue
        response = handle(message)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)


class Handler(BaseHTTPRequestHandler):
    def _origin_ok(self):
        origin = self.headers.get('Origin')
        return origin is None or re.match(r'^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$', origin) is not None

    def do_POST(self):
        if self.path.split('?')[0] != '/mcp':
            self.send_error(404)
            return
        if not self._origin_ok():
            self.send_error(403, 'Origin not allowed')
            return
        length = int(self.headers.get('Content-Length', 0))
        try:
            message = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON')
            return
        response = handle(message)
        if response is None:
            self.send_response(202)
            self.end_headers()
            return
        body = json.dumps(response, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        if message.get('method') == 'initialize':
            self.send_header('Mcp-Session-Id', uuid.uuid4().hex)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.send_response(405)
        self.send_header('Allow', 'POST')
        self.end_headers()

    def log_message(self, fmt, *args):
        log('http', fmt % args)


CATALOGUE = parameter_catalogue()
MUNICIPALITIES = municipalities()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--http', type=int, metavar='PORT', help='serve Streamable HTTP on 127.0.0.1:PORT/mcp instead of stdio')
    args = parser.parse_args()
    if not OMC:
        log('Warning: omc not found; set OMC. Listing tools works, simulations will fail.')
    if args.http:
        server = ThreadingHTTPServer(('127.0.0.1', args.http), Handler)
        log(f'MCP server on http://127.0.0.1:{args.http}/mcp')
        server.serve_forever()
    else:
        serve_stdio()


if __name__ == '__main__':
    main()
