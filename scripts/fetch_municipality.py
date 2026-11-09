#!/usr/bin/env python3
"""Archive what SCB publishes about one municipality's accounts and population, 2017-2025.

    python3 scripts/fetch_municipality.py 0586

Writes a new timestamped folder under data/downloads/ with the raw responses and a manifest
(URL, query, bytes, SHA-256). scripts/prepare_municipality.py turns it into base years.
Källa: SCB, Statistikdatabasen (CC BY 4.0).

Tables:
- TAB6777 income statement, TAB6779 balance sheet, TAB6782 tax, equalisation and financial
  items, TAB4202 operating costs by account, TAB5179 investment expenditure (all tkr).
- BefolkningNy (2017-2024) and BefolkningCKM (2025): population by single year of age, 31 December.
- BefforandrKvRLK (2017-2024) and BefforandrKvRLKCKM (2025): births and deaths in the year.
- Kommunalskatter2000: the municipal tax rate.
"""
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1 = 'https://api.scb.se/OV0104/v1/doris/sv/ssd/'
V2 = 'https://statistikdatabasen.scb.se/api/v2/tables/{}/data?lang=sv&outputFormat=json-stat2'
YEARS = [str(y) for y in range(2017, 2026)]
AGES = [str(a) for a in range(100)] + ['100+']


def request(url, query=None, attempts=4):
    body = None if query is None else json.dumps(query).encode()
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, data=body, headers={'User-Agent': 'Motala-research-data/1.0',
                                                                  'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=120) as response:
                return response.read()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(5 * (attempt + 1))


def v1_query(selection):
    return {'query': [{'code': c, 'selection': {'filter': 'item', 'values': v}} for c, v in selection],
            'response': {'format': 'json'}}


def main():
    code = sys.argv[1]
    out = ROOT / 'data/downloads' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'municipality': code,
                'source': 'Statistics Sweden (SCB), Statistikdatabasen, CC BY 4.0', 'files': []}

    def save(name, data, url, query=None):
        (out / name).write_bytes(data)
        manifest['files'].append({'file': name, 'url': url, 'query': query, 'bytes': len(data),
                                  'sha256': hashlib.sha256(data).hexdigest()})

    years = ''.join(f'&valueCodes[Tid]={y}' for y in YEARS)
    for table, extra in [('TAB6777', '&valueCodes[Resultatraknposter]=*&valueCodes[ContentsCode]=*'),
                         ('TAB6779', '&valueCodes[Balansraknposter]=*&valueCodes[ContentsCode]=*'),
                         ('TAB6782', '&valueCodes[Kontopost]=*&valueCodes[ContentsCode]=*'),
                         ('TAB4202', '&valueCodes[Kontopost]=*&valueCodes[ContentsCode]=*'),
                         ('TAB5179', '&valueCodes[Verksomrkom]=950&valueCodes[ContentsCode]=000002ZW')]:
        tyears = years if table not in ('TAB6782', 'TAB4202') else ''.join(f'&valueCodes[Tid]={y}' for y in YEARS if y >= '2017')
        url = V2.format(table) + f'&valueCodes[Region]={code}' + extra + tyears
        save(f'{table}.json', request(url), url)
        time.sleep(1)
    v1 = [
        ('population-2017-2024', 'BE/BE0101/BE0101A/BefolkningNy', [
            ('Region', [code]), ('Civilstand', ['OG', 'G', 'SK', 'ÄNKL']), ('Alder', AGES), ('Kon', ['1', '2']),
            ('ContentsCode', ['BE0101N1']), ('Tid', YEARS[:-1])]),
        ('population-2025', 'BE/BE0101/BE0101A/BefolkningCKM', [
            ('Region', [code]), ('Civilstand', ['SC']), ('Alder', AGES[:-1] + ['100+1']), ('Kon', ['1', '2']),
            ('ContentsCode', ['000007ME']), ('Tid', ['2025'])]),
        ('changes-2017-2024', 'BE/BE0101/BE0101G/BefforandrKvRLK', [
            ('Region', [code]), ('Forandringar', ['115', '130']), ('Period', ['hel']), ('Kon', ['1+2']),
            ('ContentsCode', ['000002Z9']), ('Tid', YEARS[:-1])]),
        ('changes-2025', 'BE/BE0101/BE0101G/BefforandrKvRLKCKM', [
            ('Region', [code]), ('Forandringar', ['115', '130']), ('Period', ['hel']), ('Kon', ['TotSa']),
            ('ContentsCode', ['000007TB']), ('Tid', ['2025'])]),
        ('tax-rate', 'OE/OE0101/Kommunalskatter2000', [
            ('Region', [code]), ('ContentsCode', ['OE0101D2']), ('Tid', YEARS)]),
    ]
    for name, path, selection in v1:
        query = v1_query(selection)
        save(f'{name}.json', request(V1 + path, query), V1 + path, query)
        time.sleep(1)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    (out / 'README.md').write_text(
        f'# Kommun {code}: räkenskapssammandrag och befolkning från SCB\n\nKälla: SCB, Statistikdatabasen (CC BY 4.0). '
        'Hämtat med `scripts/fetch_municipality.py`; bearbetat med `scripts/prepare_municipality.py`. '
        'Se manifest.json för tabeller, frågor och SHA-256.\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
