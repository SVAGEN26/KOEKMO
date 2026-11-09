#!/usr/bin/env python3
"""Archive Kolada elderly-care data for a municipality (default Motala, 0583): users and costs by age group.

    python3 scripts/fetch_care_data.py [municipality code]

Writes a new timestamped folder under data/downloads/ with the raw Kolada responses,
KPI metadata and a manifest (URL, bytes, SHA-256). Källa: Kolada (RKA), open data;
the underlying statistics are Socialstyrelsen's and SCB's.
"""
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = 'https://api.kolada.se/v3/'
MOTALA = sys.argv[1] if len(sys.argv) > 1 else '0583'
NAME = 'motala' if MOTALA == '0583' else MOTALA
YEARS = ','.join(str(y) for y in range(2015, 2026))
KPIS = {
    'N21702': 'Hemtjänsttagare 65+ i ordinärt boende, antal',
    'N21703': 'Hemtjänsttagare 65-79 i ordinärt boende, antal',
    'N21705': 'Hemtjänsttagare 80+ i ordinärt boende, antal',
    'N23805': 'Brukare 65+ i särskilt boende äldre, antal',
    'N23807': 'Brukare 65-79 år i särskilt boende äldre, antal',
    'N23806': 'Brukare 80+ i särskilt boende äldre, antal',
    'N21009': 'Kostnad hemtjänst äldreomsorg, kr/inv 65+',
    'N21024': 'Kostnad hemtjänst äldreomsorg, kr/inv 80+',
    'N23007': 'Kostnad särskilt boende äldreomsorg, kr/inv 65+',
    'N23001': 'Kostnad särskilt boende äldreomsorg, kr/inv 80+',
    'N23009': 'Kostnad särskilt boende äldreomsorg, kr/brukare',
    'N20007': 'Kostnad äldreomsorg, kr/inv 65+',
    'N20048': 'Kostnad äldreomsorg, kr/inv 80+',
    'N01956': 'Invånare 65-79 år, antal',
    'N01957': 'Invånare 80+, antal',
}


def request(url, attempts=4):
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Motala-research-data/1.0'})
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(5 * (attempt + 1))


def main():
    out = ROOT / 'data/downloads' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'municipality': MOTALA,
                'source': 'Kolada (RKA), open data; statistics from Socialstyrelsen and SCB', 'files': []}

    def save(name, data, url):
        (out / name).write_bytes(data)
        manifest['files'].append({'file': name, 'url': url, 'bytes': len(data),
                                  'sha256': hashlib.sha256(data).hexdigest()})

    ids = ','.join(KPIS)
    url = f'{API}kpi/{ids}'
    meta = request(url)
    titles = {k['id']: k['title'] for k in json.loads(meta)['values']}
    if set(titles) != set(KPIS):
        raise SystemExit(f'Kolada returned metadata for {sorted(titles)}, expected {sorted(KPIS)}')
    for kpi, title in KPIS.items():
        if titles[kpi] != title:
            raise SystemExit(f'{kpi} is now titled {titles[kpi]!r}, expected {title!r}; check its definition')
    save('kolada-care-kpi-metadata.json', meta, url)
    url = f'{API}data/kpi/{ids}/municipality/{MOTALA}/year/{YEARS}'
    data = request(url)
    body = json.loads(data)
    if body.get('next_url'):
        raise SystemExit('Kolada paged the response; fetch the remaining pages')
    save(f'kolada-care-{NAME}.json', data, url)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(f'{len(body["values"])} KPI-years -> {out}')


if __name__ == '__main__':
    main()
