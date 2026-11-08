#!/usr/bin/env python3
"""Archive Sweden's population: outcome 2010-2025 and SCB's latest projection 2026-2070.

    python3 scripts/fetch_national_population.py

Writes a new timestamped folder under data/downloads/ with the raw SCB responses and a
manifest (URL, query, cells, bytes, SHA-256), then data/national-population.json with
the population on 31 December per year. Källa: SCB (CC BY 4.0).

Tables: BE0101A/BefolkningNy (1968-2024) and BefolkningCKM (2025), region 00 (riket),
summed over civil status, age and sex; BE0401A/BefPrognosOversiktN, Folkmängd.
"""
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = 'https://api.scb.se/OV0104/v1/doris/sv/ssd/'
QUERIES = {
    'national-population-2010-2024': ('BE/BE0101/BE0101A/BefolkningNy', [
        ('Region', ['00']), ('Civilstand', ['OG', 'G', 'SK', 'ÄNKL']), ('Alder', ['tot']), ('Kon', ['1', '2']),
        ('ContentsCode', ['BE0101N1']), ('Tid', [str(y) for y in range(2010, 2025)])]),
    'national-population-2025': ('BE/BE0101/BE0101A/BefolkningCKM', [
        ('Region', ['00']), ('Civilstand', ['SC']), ('Alder', ['TotSA']), ('Kon', ['TotSa']),
        ('ContentsCode', ['000007ME']), ('Tid', ['2025'])]),
    'national-population-projection': ('BE/BE0401/BE0401A/BefPrognosOversiktN', [
        ('ContentsCode', ['0000028T']), ('Tid', [str(y) for y in range(2026, 2071)])]),
}


def request(url, query=None, attempts=4):
    body = None if query is None else json.dumps(query).encode()
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, data=body, headers={'User-Agent': 'Motala-research-data/1.0',
                                                                  'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(5 * (attempt + 1))


def main():
    out = ROOT / 'data/downloads' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'region': '00 (riket)',
                'source': 'Statistics Sweden (SCB), Statistikdatabasen, CC BY 4.0', 'files': []}
    population = {}
    for name, (path, selection) in QUERIES.items():
        url = API + path
        query = {'query': [{'code': c, 'selection': {'filter': 'item', 'values': v}} for c, v in selection],
                 'response': {'format': 'json'}}
        data = request(url, query)
        expected = 1
        for _, values in selection:
            expected *= len(values)
        table = json.loads(data)
        if len(table['data']) != expected:
            raise SystemExit(f'{name}: {len(table["data"])} of {expected} cells')
        (out / f'{name}.json').write_bytes(data)
        manifest['files'].append({'file': f'{name}.json', 'url': url, 'query': query, 'cells': expected,
                                  'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        keys = [c['code'] for c in table['columns'] if c['type'] != 'c']
        for row in table['data']:
            year = int(dict(zip(keys, row['key']))['Tid'])
            population[year] = population.get(year, 0) + float(row['values'][0])
        time.sleep(1)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    result = {'source': 'Källa: SCB, Statistikdatabasen (CC BY 4.0)', 'archive': str(out.relative_to(ROOT)),
              'note': 'Sweden, population on 31 December. Outcome to 2025, then SCB\'s latest projection.',
              'lastOutcome': 2025, 'population': {str(y): population[y] for y in sorted(population)}}
    (ROOT / 'data/national-population.json').write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n')
    print(f'{out.relative_to(ROOT)}: ' + ', '.join(f'{y} {population[y]:.0f}' for y in (2020, 2024, 2025, 2026, 2033)))


if __name__ == '__main__':
    main()
