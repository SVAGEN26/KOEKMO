#!/usr/bin/env python3
"""One-off fetch of the seven SCB tables listed in data/revenue-source-downloads.json."""
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib.request import Request, urlopen
from zipfile import ZipFile


def main():
    root = Path(__file__).resolve().parent
    catalog_path = root / 'data/revenue-source-downloads.json'
    catalog_bytes = catalog_path.read_bytes()
    catalog = json.loads(catalog_bytes)
    started = datetime.now(timezone.utc)
    destination = root / 'data/raw/revenue' / started.strftime('%Y%m%dT%H%M%S%fZ')
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'source-catalog.json').write_bytes(catalog_bytes)
    receipts = []
    for source in catalog['sources']:
        receipt = {'id': source['id'], 'requestedUrl': source['url'],
                   'filename': source['filename']}
        try:
            request = Request(source['url'], headers={'User-Agent': 'Motala-research-source-fetch/1.0'})
            with urlopen(request, timeout=60) as response:
                payload = response.read(64 * 1024 * 1024 + 1)
                if len(payload) > 64 * 1024 * 1024:
                    raise ValueError('Source exceeds 64 MiB limit')
                receipt.update(finalUrl=response.geturl(),
                               contentType=response.headers.get('Content-Type'),
                               lastModified=response.headers.get('Last-Modified'))
            with ZipFile(io.BytesIO(payload)) as archive:
                names = archive.namelist()
                if source['kind'] == 'xlsx' and 'xl/workbook.xml' not in names:
                    raise ValueError('Response is not an XLSX workbook')
                if source['kind'] == 'csv_zip' and not any(n.lower().endswith('.csv') for n in names):
                    raise ValueError('Response contains no CSV table')
            (destination / source['filename']).write_bytes(payload)
            receipt.update(status='downloaded', bytes=len(payload),
                           sha256=hashlib.sha256(payload).hexdigest())
            print('Saved', source['filename'], flush=True)
        except Exception as error:
            receipt.update(status='failed', error=str(error))
            print('Failed', source['filename'], ':', error, file=sys.stderr, flush=True)
        receipt['retrievedAt'] = datetime.now(timezone.utc).isoformat()
        receipts.append(receipt)
        (destination / 'receipts.json').write_text(json.dumps({
            'startedAt': started.isoformat(),
            'catalogSha256': hashlib.sha256(catalog_bytes).hexdigest(),
            'note': 'Retrieval timestamp is not the original publication date. No automatic forecast import.',
            'sources': receipts}, ensure_ascii=False, indent=2) + '\n')
    print('Sources and receipts:', destination, flush=True)
    return 0 if all(r['status'] == 'downloaded' for r in receipts) else 1


if __name__ == '__main__':
    raise SystemExit(main())
