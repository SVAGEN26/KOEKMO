#!/usr/bin/env python3
"""Archive tax capacity (skattekraft) for every municipality and Sweden: SCB OE0101 SkatteKraft.

    python3 scripts/fetch_tax_capacity.py

Writes a new timestamped folder under data/downloads/ with the raw SCB response and a manifest,
then data/tax-capacity.json: per municipality and year, skattekraft in kronor per inhabitant and
as a share of Sweden's mean. Källa: SCB, Statistikdatabasen (CC BY 4.0).

SCB's year t is the equalisation year (utjämningsår) t: the tax base is the taxable income of
year t-2 from Skatteverket's assessment in year t-1 (lag 2004:773, 3 §). The 2026 value for
Sweden, 2 868 946 mnkr, equals SKR's prognosunderlag for income year 2024. The value for year t is
known in December of year t-1, before the equalisation year starts.
"""
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://api.scb.se/OV0104/v1/doris/sv/ssd/OE/OE0101/SkatteKraft'
YEARS = [str(y) for y in range(2010, 2027)]


def request(url, query, attempts=4):
    body = json.dumps(query).encode()
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


def main():
    out = ROOT / 'data/downloads' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True, exist_ok=False)
    query = {'query': [{'code': 'Region', 'selection': {'filter': 'all', 'values': ['*']}},
                       {'code': 'ContentsCode', 'selection': {'filter': 'item', 'values': ['OE0101A5', 'OE0101A0']}},
                       {'code': 'Tid', 'selection': {'filter': 'item', 'values': YEARS}}],
             'response': {'format': 'json'}}
    data = request(URL, query)
    (out / 'skattekraft.json').write_bytes(data)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'source': 'Statistics Sweden (SCB), Statistikdatabasen, CC BY 4.0',
                'files': [{'file': 'skattekraft.json', 'url': URL, 'query': query, 'bytes': len(data),
                           'sha256': hashlib.sha256(data).hexdigest()}]}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    (out / 'README.md').write_text('# Skatteunderlag och skattekraft per kommun\n\nKälla: SCB, Statistikdatabasen (CC BY 4.0), '
                                   'OE0101 SkatteKraft, 2010-2026. År t är utjämningsåret: inkomster år t-2. Hämtat med '
                                   '`scripts/fetch_tax_capacity.py`; bearbetat till `data/tax-capacity.json`.\n')
    table = json.loads(data)
    values = {}
    for row in table['data']:
        region, year = row['key']
        if row['values'][1] in ('..', ''):
            continue
        values.setdefault(region, {})[year] = {'taxBase': float(row['values'][0]), 'perInhabitant': float(row['values'][1])}
    sweden = values['00']
    result = {'source': 'Källa: SCB, Statistikdatabasen (CC BY 4.0), OE0101 SkatteKraft', 'archive': str(out.relative_to(ROOT)),
              'note': 'Year = equalisation year; income of year t-2. relative = skattekraft / Sweden\'s mean.',
              'sweden': sweden,
              'municipalities': {r: {y: {**v, 'relative': v['perInhabitant'] / sweden[y]['perInhabitant']} for y, v in years.items()}
                                 for r, years in sorted(values.items()) if len(r) == 4}}
    (ROOT / 'data/tax-capacity.json').write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n')
    for code in ('0583', '0586'):
        print(code, ' '.join(f"{y}:{100 * v['relative']:.1f}" for y, v in result['municipalities'][code].items()))
    print(out.relative_to(ROOT), len(result['municipalities']), 'municipalities')


if __name__ == '__main__':
    main()
