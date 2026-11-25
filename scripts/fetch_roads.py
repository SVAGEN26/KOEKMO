#!/usr/bin/env python3
"""Archive the municipalities' road network and its net cost from Kolada.

    python3 scripts/fetch_roads.py

For the 13 municipalities of Östergötland, 2015-2025:

  N07024  net cost of roads, railways and parking, kr per inhabitant (SCB's account summary)
  N07810  municipal roads and cycle paths, metres

Writes a new timestamped folder under data/downloads/ with the raw responses and a manifest, then
data/roads.json. The model uses the net cost as the part of the sector "other" that follows the road
network and not the population (BaseYear.infrastructureShare, scripts/prepare_municipality.py).
The cost includes parking and the municipality's share of railways; Kolada has no narrower series
for all municipalities. Källa: Kolada (RKA), open data.
"""
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = 'https://api.kolada.se/v3/'
YEARS = ','.join(str(y) for y in range(2015, 2026))
MUNICIPALITIES = ['0509', '0512', '0513', '0560', '0561', '0562', '0563', '0580', '0581', '0582', '0583', '0584', '0586']
KPIS = {
    'N07024': 'Nettokostnad väg- och järnvägsnät, parkering, kr/inv',
    'N07810': 'Bil- och cykelväg i kommunen, kommunal, meter',
}
FIELDS = {'N07024': 'netCostPerInhabitant', 'N07810': 'metres'}


def request(url, attempts=4):
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'municipal-research-data/1.0'})
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(5 * (attempt + 1))


def main():
    out = ROOT / 'data/downloads' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'municipalities': MUNICIPALITIES,
                'source': 'Kolada (RKA), open data', 'files': []}

    def save(name, data, url):
        (out / name).write_bytes(data)
        manifest['files'].append({'file': name, 'url': url, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})

    ids = ','.join(KPIS)
    url = f'{API}kpi/{ids}'
    meta = request(url)
    titles = {k['id']: k['title'] for k in json.loads(meta)['values']}
    for kpi, title in KPIS.items():
        if titles.get(kpi) != title:
            raise SystemExit(f'{kpi} is titled {titles.get(kpi)!r}, expected {title!r}; check its definition')
    save('kolada-roads-kpi-metadata.json', meta, url)
    result = {}
    for kpi in KPIS:
        url = f'{API}data/kpi/{kpi}/municipality/{",".join(MUNICIPALITIES)}/year/{YEARS}'
        data = request(url)
        body = json.loads(data)
        if body.get('next_url'):
            raise SystemExit('Kolada paged the response; fetch the remaining pages')
        save(f'kolada-{kpi}.json', data, url)
        for v in body['values']:
            total = next((x['value'] for x in v['values'] if x['gender'] == 'T'), None)
            if total is not None:
                result.setdefault(v['municipality'], {}).setdefault(str(v['period']), {})[FIELDS[kpi]] = total
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    (out / 'README.md').write_text(
        '# Vägnät och nettokostnad för vägar\n\nKälla: Kolada (RKA), öppna data. Östergötlands 13 kommuner, 2015-2025. '
        'Hämtat med `scripts/fetch_roads.py`; bearbetat till `data/roads.json`. Se manifest.json för URL och SHA-256.\n')
    (ROOT / 'data/roads.json').write_text(json.dumps(
        {'source': 'Källa: Kolada (RKA)', 'archive': str(out.relative_to(ROOT)), 'kpis': KPIS,
         'note': 'netCostPerInhabitant: nettokostnad för väg- och järnvägsnät samt parkering, kr per invånare. '
                 'metres: kommunal bil- och cykelväg, meter.',
         'municipalities': {m: dict(sorted(result.get(m, {}).items())) for m in MUNICIPALITIES}},
        indent=1, ensure_ascii=False) + '\n')
    for m in MUNICIPALITIES:
        latest = result.get(m, {}).get('2025', {})
        print(m, latest)


if __name__ == '__main__':
    main()
