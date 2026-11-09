#!/usr/bin/env python3
"""Archive net costs per sector from Kolada and derive the model's sector weights.

    python3 scripts/fetch_sector_costs.py [municipality code, default 0583]

Kolada publishes SCB's account summary (Räkenskapssammandraget) as net cost per inhabitant for
each activity. Writes a new timestamped folder under data/downloads/ with the raw responses and a
manifest, then data/sector-costs.json with, per base year:

  education   preschool, school-age childcare, preschool class, compulsory school and upper
              secondary school, including the adapted forms (needs driven by ages 0-18)
  elderly     elderly care (needs driven by ages 65+)
  other       the rest of the net cost of the operations

as shares of the total, and the split of education into ages 0-6, 7-15 and 16-18. Only the base
year's own values are used, so a hindcast from an earlier base year uses data known then.
Källa: Kolada (RKA), open data; the statistics are SCB's.
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
YEARS = ','.join(str(y) for y in range(2015, 2026))
KPIS = {
    'N03067': 'Nettokostnad kommunens driftverksamhet totalt, kr/inv',
    'N11004': 'Nettokostnad förskola, kr/inv',
    'N13004': 'Nettokostnad fritidshem, kr/inv',
    'N15015': 'Nettokostnad förskoleklass, kr/inv',
    'N15028': 'Nettokostnad grundskola F-9, kr/inv',
    'N18002': 'Nettokostnad anpassad grundskola, kr/inv',
    'N17014': 'Nettokostnad gymnasieskola, kr/inv',
    'N18003': 'Nettokostnad anpassad gymnasieskola, kr/inv',
    'N20014': 'Nettokostnad äldreomsorg, kr/inv',
}
# Which ages each education activity serves: 0-6, 7-15 or 16-18 (the model's groups).
EDUCATION = {'N11004': 0, 'N15015': 0, 'N13004': 1, 'N15028': 1, 'N18002': 1, 'N17014': 2, 'N18003': 2}


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
    municipality = sys.argv[1] if len(sys.argv) > 1 else '0583'
    out = ROOT / 'data/downloads' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'municipality': municipality,
                'source': 'Kolada (RKA), open data; statistics from SCB (Räkenskapssammandraget)', 'files': []}

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
    save('kolada-sector-kpi-metadata.json', meta, url)
    url = f'{API}data/kpi/{ids}/municipality/{municipality}/year/{YEARS}'
    data = request(url)
    body = json.loads(data)
    if body.get('next_url'):
        raise SystemExit('Kolada paged the response; fetch the remaining pages')
    save(f'kolada-sector-costs-{municipality}.json', data, url)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    (out / 'README.md').write_text(
        '# Nettokostnad per verksamhet\n\nKälla: Kolada (RKA), öppna data; statistiken är SCB:s räkenskapssammandrag. '
        f'Kommun {municipality}, kr per invånare, 2015-2025. Hämtat med `scripts/fetch_sector_costs.py`; bearbetat till '
        '`data/sector-costs.json`. Se manifest.json för URL och SHA-256.\n')

    values = {}
    for v in body['values']:
        total = next((x['value'] for x in v['values'] if x['gender'] == 'T'), None)
        if total is not None:
            values.setdefault(str(v['period']), {})[v['kpi']] = total
    years = {}
    for year, k in sorted(values.items()):
        if any(kpi not in k for kpi in KPIS):
            continue  # a year without every series cannot be split
        groups = [0.0, 0.0, 0.0]
        for kpi, group in EDUCATION.items():
            groups[group] += k[kpi]
        education, elderly, total = sum(groups), k['N20014'], k['N03067']
        years[year] = {'krPerInhabitant': k,
                       'shares': {'education': education / total, 'elderly': elderly / total,
                                  'other': (total - education - elderly) / total},
                       'educationSplit': [g / education for g in groups]}
    result = {'source': 'Källa: Kolada (RKA), SCB:s räkenskapssammandrag', 'archive': str(out.relative_to(ROOT)),
              'municipality': municipality, 'kpis': KPIS,
              'method': 'Shares of the net cost of the operations (N03067). Education: preschool and preschool class '
                        '(ages 0-6), school-age childcare and compulsory school including adapted (7-15), upper '
                        'secondary including adapted (16-18). Each base year uses its own year only.',
              'years': years}
    target = ROOT / ('data/sector-costs.json' if municipality == '0583' else f'data/municipalities/{municipality}/sector-costs.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n')
    for year, y in years.items():
        print(year, {k: round(v, 3) for k, v in y['shares'].items()}, [round(x, 3) for x in y['educationSplit']])


if __name__ == '__main__':
    main()
