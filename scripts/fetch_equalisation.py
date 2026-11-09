#!/usr/bin/env python3
"""Archive the equalisation system per municipality: SCB TAB1981 (2005-) and TAB4011 (LSS, 2004-).

    python3 scripts/fetch_equalisation.py

Writes a new timestamped folder under data/downloads/ with the raw SCB responses (json-stat2)
and a manifest (URL, cells, bytes, SHA-256), then data/equalisation.json with kr per inhabitant
per municipality and year: income and cost equalisation, structural and introduction grants,
the regulation grant or fee, and the LSS equalisation. All municipalities are kept, so the
library can be used for any of them. Källa: SCB (CC BY 4.0).

The amounts are SCB's final calculation for each year (utfall), per inhabitant on 1 November
of the year before. The last year is the preliminary calculation for the coming year.
"""
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = 'https://statistikdatabasen.scb.se/api/v2/tables/{}/data?lang=sv&outputFormat=json-stat2'
TABLES = {
    'equalisation': ('TAB1981', {'OE0115B1': 'income', 'OE0115B2': 'cost', 'OE0115B3': 'structure',
                                 'OE0115B4': 'introduction', 'OE0115B6': 'regulation', 'OE0115B7': 'total'}),
    'lss-equalisation': ('TAB4011', {'OE0115G6': 'lss'}),
}


def request(url, attempts=4):
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Motala-research-data/1.0'})
            with urllib.request.urlopen(req, timeout=120) as response:
                return response.read()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(5 * (attempt + 1))


def cells(stat):
    """Yield (region, contents, year, value) from a json-stat2 dataset."""
    ids, sizes = stat['id'], stat['size']
    labels = [list(stat['dimension'][d]['category']['index']) if isinstance(stat['dimension'][d]['category']['index'], dict)
              else stat['dimension'][d]['category']['index'] for d in ids]
    for flat, value in enumerate(stat['value']):
        index, rest = [], flat
        for size in reversed(sizes):
            index.append(rest % size)
            rest //= size
        key = dict(zip(ids, (labels[k][i] for k, i in enumerate(reversed(index)))))
        yield key['Region'], key['ContentsCode'], int(key['Tid']), value


def main():
    out = ROOT / 'data/downloads' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'region': 'all municipalities',
                'source': 'Statistics Sweden (SCB), Statistikdatabasen, CC BY 4.0', 'files': []}
    municipalities, names, years = {}, {}, set()
    for name, (table, contents) in TABLES.items():
        url = API.format(table) + ''.join(f'&valueCodes[ContentsCode]={c}' for c in contents) \
            + '&valueCodes[Region]=*&valueCodes[Tid]=*'
        data = request(url)
        stat = json.loads(data)
        (out / f'{name}.json').write_bytes(data)
        manifest['files'].append({'file': f'{name}.json', 'table': table, 'url': url, 'cells': len(stat['value']),
                                  'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                                  'updated': stat.get('updated')})
        names.update(stat['dimension']['Region']['category']['label'])
        for region, code, year, value in cells(stat):
            if len(region) != 4 or value is None:  # four digits: a municipality, not a region (two digits)
                continue
            municipalities.setdefault(region, {}).setdefault(str(year), {})[contents[code]] = value
            years.add(year)
        time.sleep(1)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    (out / 'README.md').write_text(
        '# Kommunalekonomisk utjämning och LSS-utjämning per kommun\n\n'
        'Källa: SCB, Statistikdatabasen (CC BY 4.0). TAB1981 (kommunalekonomisk utjämning, kr/invånare, 2005-) och\n'
        'TAB4011 (utjämning av LSS-kostnader, beräknat bidrag/avgift kr per invånare, 2004-). Hämtat med\n'
        '`scripts/fetch_equalisation.py`; bearbetat till `data/equalisation.json`. Se manifest.json för URL och SHA-256.\n')
    result = {'source': 'Källa: SCB, Statistikdatabasen (CC BY 4.0), TAB1981 och TAB4011', 'archive': str(out.relative_to(ROOT)),
              'unit': 'kr per inhabitant (population 1 November of the previous year)',
              'note': 'Final calculation (utfall) per year; the last year is SCB\'s preliminary calculation.',
              'fields': {'income': 'inkomstutjämning', 'cost': 'kostnadsutjämning', 'structure': 'strukturbidrag',
                         'introduction': 'införandebidrag', 'regulation': 'regleringsbidrag (+) eller -avgift (-)',
                         'total': 'kommunalekonomisk utjämning totalt', 'lss': 'LSS-utjämning, bidrag (+) eller avgift (-)'},
              'years': [min(years), max(years)],
              'municipalities': {code: {'name': names.get(code, code), 'years': values}
                                 for code, values in sorted(municipalities.items())}}
    (ROOT / 'data/equalisation.json').write_text(json.dumps(result, indent=1, ensure_ascii=False) + '\n')
    m = result['municipalities']['0583']['years']
    print(f'{out.relative_to(ROOT)}: {len(municipalities)} municipalities, {min(years)}-{max(years)}')
    for y in sorted(m):
        print(y, {k: round(v) for k, v in m[y].items()})


if __name__ == '__main__':
    main()
