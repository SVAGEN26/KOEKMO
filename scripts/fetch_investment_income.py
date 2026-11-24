#!/usr/bin/env python3
"""Archive what the 13 municipalities in Östergötland received for their investments, 2011-2025.

    python3 scripts/fetch_investment_income.py

A municipality does not pay all its investments itself. Connection fees (water and sewerage) and
public investment grants come in when the investment is made and are then spread over the asset's
life in the income statement. The model needs to know how large a part of the investments they pay.

Tables (SCB, Statistikdatabasen, CC BY 4.0):
- TAB4201 operating revenue by account: 210 connection and facility fees (investments), 560 public
  grants (investments), 580 investment grants spread over the useful life (the part taken to income
  in the year) and 892 gains from sales of fixed assets, 2011-2025.
- TAB5179 investment expenditure, total (950), 2015-2025.

Writes data/downloads/<timestamp>-investment-income/ with the raw responses and a manifest (URL,
bytes, SHA-256), and names the folder in data/municipalities/ostergotland-sources.json.
scripts/prepare_investment_income.py turns it into data/investment-income.json.
"""
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = 'https://statistikdatabasen.scb.se/api/v2/tables/{}/data?lang=sv&outputFormat=json-stat2'
CODES = ['0509', '0512', '0513', '0560', '0561', '0562', '0563', '0580', '0581', '0582', '0583', '0584', '0586']
TABLES = (('TAB4201', 'Kontopost', ['210', '560', '580', '892'], range(2011, 2026)),
          ('TAB5179', 'Verksomrkom', ['950'], range(2015, 2026)))


def request(url, attempts=4):
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'research-data/1.0'}), timeout=120) as response:
                return response.read()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(5 * (attempt + 1))


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT / 'data/downloads' / f'{stamp}-investment-income'
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'municipalities': CODES,
                'source': 'Statistics Sweden (SCB), Statistikdatabasen, CC BY 4.0', 'files': []}
    for table, dimension, items, years in TABLES:
        url = (V2.format(table) + ''.join(f'&valueCodes[Region]={c}' for c in CODES)
               + ''.join(f'&valueCodes[{dimension}]={i}' for i in items)
               + ('&valueCodes[ContentsCode]=000002ZW' if table == 'TAB5179' else '&valueCodes[ContentsCode]=*')
               + ''.join(f'&valueCodes[Tid]={y}' for y in years))
        data = request(url)
        (out / f'{table}.json').write_bytes(data)
        manifest['files'].append({'file': f'{table}.json', 'url': url, 'query': None, 'bytes': len(data),
                                  'sha256': hashlib.sha256(data).hexdigest()})
        time.sleep(1)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    (out / 'README.md').write_text(
        '# Östergötlands kommuner: investeringsinkomster och investeringsutgifter från SCB\n\n'
        'Källa: SCB, Statistikdatabasen (CC BY 4.0), tabellerna TAB4201 (2011-2025) och TAB5179 (2015-2025). '
        'Hämtat med `scripts/fetch_investment_income.py`. Se manifest.json för frågor och SHA-256.\n')
    sources = ROOT / 'data/municipalities/ostergotland-sources.json'
    index = json.loads(sources.read_text())
    index['investmentIncomeArchive'] = str(out.relative_to(ROOT))
    sources.write_text(json.dumps(index, indent=2, ensure_ascii=False) + '\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
