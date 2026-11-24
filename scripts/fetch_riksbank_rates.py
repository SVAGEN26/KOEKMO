#!/usr/bin/env python3
"""Archive Riksbank's yearly average interest rates, 1983 onwards, for the rate stress paths.

    python3 scripts/fetch_riksbank_rates.py

Series (Sveriges riksbank, SWEA API, https://api.riksbank.se/swea/v1):
- SETB3MBENCH  Swedish treasury bill, 3 months (statsskuldväxel), from 1983. The rate closest to what a
               municipality pays on new and refixed loans with the shortest fixing.
- SEGVB5YC     Swedish government bond, 5 years, from 1985. For comparison.
- SECBREPOEFF  The policy rate, from June 1994. For comparison.

ObservationAggregates with frequency Y gives the average, minimum, maximum and the last value of each
calendar year; the current year is left out until it is complete. Writes
data/downloads/<timestamp>-riksbank-rates/ with the raw responses and a manifest (URL, bytes, SHA-256).
scripts/prepare_rate_stress.py turns it into data/rate-stress.json.
"""
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = 'https://api.riksbank.se/swea/v1/ObservationAggregates/{}/Y/{}/{}'
SERIES = (('SETB3MBENCH', '1983-01-01'), ('SEGVB5YC', '1985-01-01'), ('SECBREPOEFF', '1994-06-01'))


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
    now = datetime.now(timezone.utc)
    out = ROOT / 'data/downloads' / f"{now.strftime('%Y%m%dT%H%M%SZ')}-riksbank-rates"
    out.mkdir(parents=True, exist_ok=False)
    manifest = {'retrieved_at': now.isoformat(), 'source': 'Sveriges riksbank, räntor och valutakurser (SWEA API)',
                'licence': 'Öppna data från Riksbanken; ange källa', 'files': []}
    for series, start in SERIES:
        url = API.format(series, start, now.strftime('%Y-%m-%d'))
        data = request(url)
        rows = json.loads(data)
        if not rows or 'average' not in rows[0]:
            raise SystemExit(f'{series}: unexpected answer {data[:200]!r}')
        (out / f'{series}.json').write_bytes(data)
        manifest['files'].append({'file': f'{series}.json', 'url': url, 'bytes': len(data),
                                  'sha256': hashlib.sha256(data).hexdigest(),
                                  'years': [rows[0]['year'], rows[-1]['year']]})
        time.sleep(1)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + '\n')
    (out / 'README.md').write_text(
        '# Riksbankens årsräntor\n\nÅrsmedelvärden från Riksbankens API (SWEA), hämtade '
        f"{now.strftime('%Y-%m-%d')}: statsskuldväxel 3 månader (SETB3MBENCH), statsobligation 5 år (SEGVB5YC) "
        'och styrräntan (SECBREPOEFF). Källa: Sveriges riksbank. Se manifest.json för adresser och SHA-256.\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
