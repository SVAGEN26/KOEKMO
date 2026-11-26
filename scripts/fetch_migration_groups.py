#!/usr/bin/env python3
"""Archive migration by age for all municipalities and SKR's municipality groups, and write data/migration-groups.json.

    python3 scripts/fetch_migration_groups.py              # download to a new folder under data/downloads/
    python3 scripts/fetch_migration_groups.py ARCHIVE      # read an archive already downloaded

The model calibrates a municipality's migration on its own last two years. That is noisy, so the model can
instead take the migration, or half of it, from the municipality's group in SKR's classification
(Kommungruppsindelning 2023: nine groups such as "Större stad" and "Lågpendlingskommun nära större stad").
This script fetches what that needs:

  SKR   Kommungruppsindelning 2023 (Excel): municipality code -> group
  SCB   population 31 December by single year of age (BefolkningNy 1999-2024, BefolkningCKM 2025)
  SCB   domestic moves in and out, immigration and emigration by single year of age
        (Flyttningar97 2000-2024, Flyttningar97CKM 2025)

SCB perturbs every cell from 2025 (Cell Key Method), so for 2025 the published age aggregates are used where
they fit the model's five age groups, to add as few perturbed cells as possible.

data/migration-groups.json holds, per year 2000-2025 and for the age groups 0-6, 7-15, 16-18, 19-64 and 65+,
net migration (domestic and foreign) per inhabitant of the age group at the start of the year: pooled for each
of SKR's nine groups, and for each of Östergötland's 13 municipalities. Age is the age at the end of the year,
as in SCB's migration tables. All 290 municipalities are in the archive, not in the repository.
Källa: SCB, Statistikdatabasen (CC BY 4.0); SKR, Kommungruppsindelning 2023.
"""
import hashlib
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCB = 'https://api.scb.se/OV0104/v1/doris/sv/ssd/BE/BE0101/'
SKR = 'https://skr.se/download/18.7c5af3d619913bebe3cc3074/1757509057199/Kommungruppsindelning-2023-SKR.xlsx'
AGENT = 'municipal-research-data/1.0'
AGES = [str(a) for a in range(100)]
GROUPS = (('0-6', 0, 6), ('7-15', 7, 15), ('16-18', 16, 18), ('19-64', 19, 64), ('65+', 65, 100))
# 2025: published aggregates and the single years that complete each of the model's groups.
PARTS_2025 = {'0-6': (['-4'], [5, 6]), '7-15': (['10-14'], [7, 8, 9, 15]), '16-18': ([], [16, 17, 18]),
              '19-64': (['20-29', '30-39', '40-49', '50-59', '60-64'], [19]),
              '65+': (['65-69', '70-79', '80-89', '90-99', '100+1'], [])}
FLOWS = {'BE0101A2': 'in', 'BE0101A3': 'out', 'BE0101AX': 'immigration', 'BE0101AY': 'emigration',
         '0000086D': 'in', '0000086E': 'out', '00000869': 'immigration', '00000867': 'emigration'}
COUNTY = ('0509', '0512', '0513', '0560', '0561', '0562', '0563', '0580', '0581', '0582', '0583', '0584', '0586')
FIRST, LAST = 2000, 2025


def request(url, body=None, attempts=6):
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode(),
                                         headers={'User-Agent': AGENT, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=300) as response:
                return response.read()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(10 * (attempt + 1))


def xlsx_rows(path, sheet):
    """Rows of one sheet of an Excel file, without a spreadsheet library."""
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
          'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
    z = zipfile.ZipFile(path)
    strings = [''.join(t.text or '' for t in si.iter('{%s}t' % ns['m']))
               for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', ns)]
    targets = {r.get('Id'): r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    for s in ET.fromstring(z.read('xl/workbook.xml')).find('m:sheets', ns):
        if s.get('name') != sheet:
            continue
        target = targets[s.get('{%s}id' % ns['r'])].lstrip('/')
        rows = []
        for row in ET.fromstring(z.read(target if target.startswith('xl/') else 'xl/' + target)).iter('{%s}row' % ns['m']):
            cells = {}
            for c in row.findall('m:c', ns):
                column = 0
                for ch in re.match(r'[A-Z]+', c.get('r')).group(0):
                    column = column * 26 + ord(ch) - 64
                v = c.find('m:v', ns)
                if v is not None:
                    cells[column - 1] = strings[int(v.text)] if c.get('t') == 's' else v.text
            if cells:
                rows.append([cells.get(i, '') for i in range(max(cells) + 1)])
        return rows
    raise SystemExit(f'{path.name} has no sheet {sheet!r}')


def download(out):
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'files': [],
                'source': 'SCB, Statistikdatabasen (CC BY 4.0); SKR, Kommungruppsindelning 2023'}

    def save(name, data, url, query=None):
        (out / name).write_bytes(data)
        manifest['files'].append({'file': name, 'url': url, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                                  **({'query': query} if query else {})})

    save('kommungruppsindelning-2023.xlsx', request(SKR), SKR)
    codes = sorted(groups_of(out))

    def post(table, name, selection):
        body = {'query': [{'code': c, 'selection': {'filter': 'item', 'values': v}} for c, v in selection.items()],
                'response': {'format': 'json'}}
        save(f'{name}.json', request(SCB + table, body), SCB + table,
             {c: v if len(v) < 30 else f'{len(v)} values {v[0]}..{v[-1]}' for c, v in selection.items()})
        print('fetched', name, flush=True)
        time.sleep(1.5)

    for first in range(FIRST - 1, 2025, 4):
        years = [str(y) for y in range(first, min(first + 4, 2025))]
        post('BE0101A/BefolkningNy', f'pop_age_{years[0]}_{years[-1]}', {'Region': codes, 'Alder': AGES + ['100+'], 'ContentsCode': ['BE0101N1'], 'Tid': years})
    post('BE0101A/BefolkningCKM', 'pop_age_2025', {'Region': codes, 'Civilstand': ['SC'], 'Alder': AGES + ['100+1'], 'Kon': ['TotSa'], 'ContentsCode': ['000007ME'], 'Tid': ['2025']})
    for year in range(FIRST, 2025):
        post('BE0101J/Flyttningar97', f'mig_age_{year}', {'Region': codes, 'Alder': AGES + ['100+'], 'ContentsCode': ['BE0101A2', 'BE0101A3', 'BE0101AX', 'BE0101AY'], 'Tid': [str(year)]})
    post('BE0101J/Flyttningar97CKM', 'mig_age_2025', {'Region': codes, 'Alder': AGES + ['100+1'], 'Kon': ['TotSa'], 'ContentsCode': ['0000086D', '0000086E', '00000869', '00000867'], 'Tid': ['2025']})
    post('BE0101A/FolkmangdDecCKM', 'pop_groups_2025', {'Region': codes, 'Alder': ['TotSA', '0-6', '7-15', '16-18', '19-64', '65+'], 'Kon': ['TotSa'], 'ContentsCode': ['000008HY'], 'Tid': ['2025']})
    post('BE0101J/Flyttningar97CKM', 'mig_groups_2025', {'Region': codes, 'Alder': ['-4', '10-14', '20-29', '30-39', '40-49', '50-59', '60-64', '65-69', '70-79', '80-89', '90-99', '100+1', 'tot'],
                                                         'Kon': ['TotSa'], 'ContentsCode': ['0000086D', '0000086E', '00000869', '00000867'], 'Tid': ['2025']})
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    (out / 'README.md').write_text(
        '# Flyttningar per ålder och SKR:s kommungrupper\n\nKälla: SCB, Statistikdatabasen (CC BY 4.0), och SKR, Kommungruppsindelning 2023. '
        'Alla 290 kommuner, 1999-2025. Hämtat med `scripts/fetch_migration_groups.py`; bearbetat till `data/migration-groups.json`. '
        'Se manifest.json för URL, fråga och SHA-256.\n')


def groups_of(archive):
    path = next(p for p in (archive / 'kommungruppsindelning-2023.xlsx', archive / 'skr/Kommungruppsindelning-2023-SKR.xlsx') if p.exists())
    rows = xlsx_rows(path, 'Bilaga1 Lista alla kommuner')
    start = next(i for i, r in enumerate(rows) if r and r[0] == 'Gruppkod')
    return {r[1].zfill(4): {'group': r[0], 'groupName': r[4].strip(), 'name': r[2].strip()} for r in rows[start + 1:] if len(r) >= 5 and r[1]}


def load(archive, name):
    path = next(p for p in (archive / f'{name}.json', archive / 'raw' / f'{name}.json') if p.exists())
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    columns = [c['code'] for c in data['columns']]
    keys = len(data['data'][0]['key'])
    return columns[:keys], columns[keys:], data['data']


def number(value):
    return 0.0 if value in ('..', '.', '-', '') else float(value)


def prepare(archive):
    municipalities = groups_of(archive)
    age = lambda a: 100 if a.startswith('100') else int(a)
    index = {g: i for i, (g, _, _) in enumerate(GROUPS)}
    group_of = [next(i for i, (_, lo, hi) in enumerate(GROUPS) if lo <= a <= hi) for a in range(101)]
    population, net = {}, {}   # (code, year) -> five numbers
    names = sorted({p.stem for folder in (archive, archive / 'raw') if folder.exists() for p in folder.glob('pop_age_*.json')})
    for name in names:
        keys, _, rows = load(archive, name)
        for r in rows:
            k = dict(zip(keys, r['key']))
            if int(k['Tid']) == 2025:
                continue
            population.setdefault((k['Region'], int(k['Tid'])), [0.0] * 5)[group_of[age(k['Alder'])]] += number(r['values'][0])
    single = {}
    for year in range(FIRST, LAST + 1):
        keys, values, rows = load(archive, f'mig_age_{year}')
        for r in rows:
            k = dict(zip(keys, r['key']))
            f = {FLOWS[c]: number(x) for c, x in zip(values, r['values'])}
            flow = f['in'] - f['out'] + f['immigration'] - f['emigration']
            if year == 2025:
                single[(k['Region'], age(k['Alder']))] = flow
            else:
                net.setdefault((k['Region'], year), [0.0] * 5)[group_of[age(k['Alder'])]] += flow
    keys, _, rows = load(archive, 'pop_groups_2025')
    for r in rows:
        if r['key'][1] in index:
            population.setdefault((r['key'][0], 2025), [0.0] * 5)[index[r['key'][1]]] = number(r['values'][0])
    keys, values, rows = load(archive, 'mig_groups_2025')
    aggregate = {}
    for r in rows:
        f = {FLOWS[c]: number(x) for c, x in zip(values, r['values'])}
        aggregate[(r['key'][0], r['key'][1])] = f['in'] - f['out'] + f['immigration'] - f['emigration']
    for code in municipalities:
        net[(code, 2025)] = [sum(aggregate[(code, a)] for a in PARTS_2025[g][0]) + sum(single[(code, a)] for a in PARTS_2025[g][1]) for g, _, _ in GROUPS]
    missing = [(c, y) for c in municipalities for y in range(FIRST, LAST + 1) if (c, y) not in net and (c, y - 1) in population]
    if missing:
        raise SystemExit(f'migration missing for {missing[:5]}')

    def rate(codes, year):
        # Knivsta has no population before its start in 2003: only municipalities with both figures count.
        codes = [c for c in codes if (c, year) in net and (c, year - 1) in population]
        return [round(sum(net[(c, year)][i] for c in codes) / sum(population[(c, year - 1)][i] for c in codes), 6) for i in range(5)]

    members = {}
    for code, m in municipalities.items():
        members.setdefault(m['group'], []).append(code)
    out = {'source': 'Källa: SCB, Statistikdatabasen (CC BY 4.0): folkmängd och flyttningar per ålder; SKR, Kommungruppsindelning 2023',
           'archive': str(archive.relative_to(ROOT)) if archive.is_relative_to(ROOT) else str(archive),
           'method': 'python3 scripts/fetch_migration_groups.py',
           'unit': 'net migration (domestic and foreign) per inhabitant of the age group at the start of the year; age at the end of the year',
           'ageGroups': [g for g, _, _ in GROUPS], 'years': [FIRST, LAST],
           'note': 'Group rates are pooled: the sum of the flows over the sum of the population in the group\'s municipalities, with the 2023 '
                   'classification for all years. 2025 is perturbed by SCB (Cell Key Method).',
           'groups': {g: {'name': municipalities[codes[0]]['groupName'], 'municipalities': len(codes),
                          'rates': {str(y): rate(codes, y) for y in range(FIRST, LAST + 1)}} for g, codes in sorted(members.items())},
           'municipalities': {c: {'name': municipalities[c]['name'], 'group': municipalities[c]['group'],
                                  'rates': {str(y): rate([c], y) for y in range(FIRST, LAST + 1)}} for c in COUNTY}}
    (ROOT / 'data/migration-groups.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    for g, v in out['groups'].items():
        print(g, v['name'], v['municipalities'], [round(1000 * x, 1) for x in v['rates'][str(LAST)]])


def main():
    if len(sys.argv) > 1:
        archive = Path(sys.argv[1]).resolve()
    else:
        archive = ROOT / 'data/downloads' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        archive.mkdir(parents=True, exist_ok=False)
        download(archive)
    prepare(archive)


if __name__ == '__main__':
    main()
