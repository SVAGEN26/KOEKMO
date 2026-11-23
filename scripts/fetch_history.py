#!/usr/bin/env python3
"""Archive SCB's older series for the 13 municipalities in Östergötland, 2009-2016.

    python3 scripts/fetch_history.py

The per-municipality archives (scripts/fetch_municipality.py) start in 2017. This adds the years
before, for two uses:

- scripts/cost_residual.py: net cost growth beyond prices and demographic need from 2010.
- scripts/prepare_municipality.py: base years 2017-2019, so the hindcast can run eight years
  ahead to 2025 (scripts/hindcast_long.py). A base year needs the population two years back.

Tables (SCB, Statistikdatabasen, CC BY 4.0):
- TAB6777 income statement and TAB6779 balance sheet, 2009-2016 (tkr). The balance sheet gives the
  opening debt of base year 2017.
- BefolkningNy: population by single year of age and sex, 31 December, 2009-2016.
- BefforandrKvRLK: births and deaths in the year, 2009-2016.

Writes data/downloads/<timestamp>-history/ with the raw responses and a manifest (URL, query,
bytes, SHA-256). The folder is named in data/municipalities/ostergotland-sources.json.
"""
import hashlib
import json
import time
from datetime import datetime, timezone

from fetch_municipality import AGES, V1, V2, ROOT, request, v1_query

CODES = ['0509', '0512', '0513', '0560', '0561', '0562', '0563', '0580', '0581', '0582', '0583', '0584', '0586']
YEARS = [str(y) for y in range(2009, 2017)]


def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT / 'data/downloads' / f'{stamp}-history'
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'municipalities': CODES,
                'source': 'Statistics Sweden (SCB), Statistikdatabasen, CC BY 4.0', 'files': []}

    def save(name, data, url, query=None):
        (out / name).write_bytes(data)
        manifest['files'].append({'file': name, 'url': url, 'query': query, 'bytes': len(data),
                                  'sha256': hashlib.sha256(data).hexdigest()})

    for table, items in (('TAB6777', 'Resultatraknposter'), ('TAB6779', 'Balansraknposter')):
        url = (V2.format(table) + ''.join(f'&valueCodes[Region]={c}' for c in CODES)
               + f'&valueCodes[{items}]=*&valueCodes[ContentsCode]=*' + ''.join(f'&valueCodes[Tid]={y}' for y in YEARS))
        save(f'{table}.json', request(url), url)
        time.sleep(1)
    for name, path, selection in [
        ('population', 'BE/BE0101/BE0101A/BefolkningNy', [
            ('Region', CODES), ('Civilstand', ['OG', 'G', 'SK', 'ÄNKL']), ('Alder', AGES), ('Kon', ['1', '2']),
            ('ContentsCode', ['BE0101N1']), ('Tid', YEARS)]),
        ('changes', 'BE/BE0101/BE0101G/BefforandrKvRLK', [
            ('Region', CODES), ('Forandringar', ['115', '130']), ('Period', ['hel']), ('Kon', ['1+2']),
            ('ContentsCode', ['000002Z9']), ('Tid', YEARS)]),
    ]:
        time.sleep(1)
        query = v1_query(selection)
        save(f'{name}.json', request(V1 + path, query), V1 + path, query)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    (out / 'README.md').write_text(
        '# Östergötlands kommuner 2009-2016: räkenskaper och befolkning från SCB\n\n'
        'Källa: SCB, Statistikdatabasen (CC BY 4.0). Hämtat med `scripts/fetch_history.py`. '
        'Se manifest.json för tabeller, frågor och SHA-256.\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
