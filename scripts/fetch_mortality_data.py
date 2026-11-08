#!/usr/bin/env python3
"""Archive SCB mortality, fertility and single-year population data for Motala (0583).

    python3 scripts/fetch_mortality_data.py

Writes a new timestamped folder under data/downloads/ with the raw SCB responses,
their metadata, and a manifest (URL, query, bytes, SHA-256). Nothing in the model
changes; a separate preparation step reads the archive.

Tables (SCB Statistikdatabasen, PxWeb API v1):
- LivslangdEttariga: national single-year life table by sex, death risk (per mille)
  and remaining life expectancy, 2010-2025.
- BefProgDodstalNb: death rates assumed in SCB's latest national projection, 2026-2070.
- BefolkningNy / BefolkningCKM: Motala population by single year of age and sex, 2015-2025.
- DodaHandelseK / DodaHandelseKCKM: deaths in Motala by age reached and sex, 2015-2025.
- BefProgOsiktRegN: SCB's regional projection for Motala (population, births, deaths,
  migration by age and sex), 2024-2070. An independent benchmark, not a model input.
- FruktsamhetHVD / FruktsamhetSum: fertility by mother's age (Sweden) and total fertility
  (Sweden and Motala).
- FoddaK / FoddaKCKM: births in Motala by mother's age, 2015-2025.
- BefProgFruktTotNb: fertility assumed in SCB's latest national projection, 2026-2070.
SCB's open data are CC BY 4.0: cite "Källa: SCB" and the table.
"""
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = 'https://api.scb.se/OV0104/v1/doris/sv/ssd/'
AGENT = 'Motala-research-data/1.0'
MOTALA = '0583'


def request(url, query=None, attempts=4):
    body = None if query is None else json.dumps(query).encode()
    for attempt in range(attempts):
        req = urllib.request.Request(url, data=body, headers={'User-Agent': AGENT, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(5 * (attempt + 1))


def single_ages(variable):
    """Codes for single years of age (0, 1, ..., and the open top group); no totals or ranges.
    Tables from 2025 list the top group once per grouping (100+1, 100+5, 100+10); take the single-year one."""
    return [v for v in variable['values'] if v.isdigit() or v in ('100+', '100+1', '105+')]


def years(variable, first, last):
    return [v for v in variable['values'] if first <= int(v) <= last]


def contents(variable, *prefixes):
    picked = [c for c, t in zip(variable['values'], variable['valueTexts']) if t.startswith(prefixes)]
    if len(picked) != len(prefixes):
        raise ValueError(f'Expected contents {prefixes}, found {variable["valueTexts"]}')
    return picked


# Each table: how to pick values per variable from its metadata. Unlisted variables keep all values.
TABLES = {
    'life-table': ('BE/BE0101/BE0101I/LivslangdEttariga', {
        'Alder': single_ages,
        'ContentsCode': lambda v: contents(v, 'Dödsrisker', 'Återstående medellivslängd'),
        'Tid': lambda v: years(v, 2010, 2025)}),
    'projected-death-rates': ('BE/BE0401/BE0401D/BefProgDodstalNb', {
        'Fodelseregion': lambda v: ['90'],
        'Tid': lambda v: years(v, 2026, 2070)}),
    'motala-population-2015-2024': ('BE/BE0101/BE0101A/BefolkningNy', {
        'Region': lambda v: [MOTALA],
        'Alder': single_ages,
        'ContentsCode': lambda v: contents(v, 'Folkmängd'),
        'Tid': lambda v: years(v, 2015, 2024)}),
    'motala-population-2025': ('BE/BE0101/BE0101A/BefolkningCKM', {
        'Region': lambda v: [MOTALA],
        'Civilstand': lambda v: ['SC'],
        'Alder': single_ages,
        'Kon': lambda v: ['1', '2'],
        'ContentsCode': lambda v: contents(v, 'Folkmängd')}),
    'motala-deaths-2015-2024': ('BE/BE0101/BE0101I/DodaHandelseK', {
        'Region': lambda v: [MOTALA],
        'Alder': single_ages,
        'Tid': lambda v: years(v, 2015, 2024)}),
    'motala-deaths-2025': ('BE/BE0101/BE0101I/DodaHandelseKCKM', {
        'Region': lambda v: [MOTALA],
        'Alder': single_ages,
        'Kon': lambda v: ['1', '2']}),
    'scb-projection-motala': ('BE/BE0401/BE0401A/BefProgOsiktRegN', {
        'Region': lambda v: [MOTALA]}),
    'fertility-rates-sweden': ('BE/BE0101/BE0101H/FruktsamhetHVD', {
        'Region': lambda v: ['00'],
        'Tid': lambda v: years(v, 2010, 2025)}),
    'total-fertility': ('BE/BE0101/BE0101H/FruktsamhetSum', {
        'Region': lambda v: ['00', MOTALA]}),
    'motala-births-2015-2024': ('BE/BE0101/BE0101H/FoddaK', {
        'Region': lambda v: [MOTALA],
        'Tid': lambda v: years(v, 2015, 2024)}),
    'motala-births-2025': ('BE/BE0101/BE0101H/FoddaKCKM', {
        'Region': lambda v: [MOTALA]}),
    'projected-fertility': ('BE/BE0401/BE0401D/BefProgFruktTotNb', {
        'ModerFodregion': lambda v: ['90'],
        'Tid': lambda v: years(v, 2026, 2070)}),
}


def main():
    out = ROOT / 'data/downloads' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'municipality': MOTALA,
                'source': 'Statistics Sweden (SCB), Statistikdatabasen, CC BY 4.0', 'files': [], 'errors': []}

    def save(name, data, url, query=None, cells=None):
        (out / name).write_bytes(data)
        manifest['files'].append({'file': name, 'url': url, 'query': query, 'cells': cells,
                                  'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})

    for name, (path, pick) in TABLES.items():
        url = API + path
        try:
            raw_meta = request(url)
            meta = json.loads(raw_meta)
            save(f'{name}-metadata.json', raw_meta, url)
            selection = []
            expected = 1
            for variable in meta['variables']:
                values = pick[variable['code']](variable) if variable['code'] in pick else variable['values']
                if not values:
                    raise ValueError(f'No values selected for {variable["code"]}')
                selection.append({'code': variable['code'], 'selection': {'filter': 'item', 'values': values}})
                expected *= len(values)
            query = {'query': selection, 'response': {'format': 'json'}}
            data = request(url, query)
            result = json.loads(data)
            cells = len(result['data']) * len([c for c in result['columns'] if c['type'] == 'c'])
            if cells != expected:
                raise ValueError(f'Incomplete response: {cells} of {expected} cells')
            save(f'{name}.json', data, url, query, cells)
            print(f'{name}: {cells} cells', flush=True)
        except Exception as exc:  # keep going; the manifest records what failed
            manifest['errors'].append({'table': name, 'url': url, 'error': str(exc)})
            print(f'{name}: {exc}', flush=True)
        time.sleep(1)  # SCB allows about 30 requests per 10 seconds
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print('Archive:', out)
    if manifest['errors']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
