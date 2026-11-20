"""Prepare dated inputs for the optional wage and migration models."""
import hashlib
import json
import sys
from pathlib import Path

from prepare_municipality import jsonstat

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://api.scb.se/OV0104/v1/doris/sv/ssd/BE/BE0101/BE0101J/Flyttningar97'
ACCOUNTS = {'0583': '20261109T162149Z', '0586': '20261109T162208Z'}


def migration_cells(raw):
    table = json.loads(raw)
    assert [col['code'] for col in table['columns']] == [
        'Region', 'Alder', 'Kon', 'Tid', 'BE0101AU', 'BE0101AV']
    cells = {}
    for record in table['data']:
        code, age, sex, year = record['key']
        key = (code, int(year), int(sex), int(age.removesuffix('+')))
        assert key not in cells
        cells[key] = tuple(map(int, record['values']))
    return cells


def migration_inputs(cells, code, years):
    histories = [[
        [cells[code, year, sex, age] for year in years] for age in range(101)
    ] for sex in (1, 2)]
    migration = [[sum(i - o for i, o in counts) / len(years) for counts in ages]
                 for ages in histories]
    arrivals = [[sum(i for i, _ in counts) for counts in ages] for ages in histories]
    total = sum(map(sum, arrivals))
    return {'years': years, 'netMigration': migration,
            'arrivalWeights': [[n / total for n in ages] for ages in arrivals]}


def prepare(archive):
    raw = (archive / 'migration-raw.json').read_bytes()
    query = json.loads((archive / 'migration-query.json').read_text())
    cells = migration_cells(raw)
    result = {}
    for code, accounts in ACCOUNTS.items():
        salaries = jsonstat(ROOT / 'data/downloads' / accounts / 'TAB4202.json')
        result[code] = {}
        for base in range(2020, 2026):
            # The archived pre-CKM series ends in 2024. Each origin uses at most three completed years.
            end = min(base, 2024)
            years = list(range(end - 2, end + 1))
            result[code][base] = {
                **migration_inputs(cells, code, years),
                'wages': salaries['100'][base], 'employerContributions': salaries['110'][base],
            }
    return {'municipalities': result, 'sources': {
        'migration': {'url': SOURCE, 'table': 'TAB1212', 'query': query,
                      'archive': str(archive.relative_to(ROOT)), 'sha256': hashlib.sha256(raw).hexdigest()},
        'employment': {'table': 'TAB4202', 'archives': ACCOUNTS, 'rows': ['100', '110']},
    }}


if __name__ == '__main__':
    data = prepare(Path(sys.argv[1]).resolve())
    (ROOT / 'data/model-experiments.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n')
