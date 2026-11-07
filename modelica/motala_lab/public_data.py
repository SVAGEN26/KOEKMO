"""Archive public source responses and honest receipts; never infer missing data.

Raw API responses require a reviewed variable map before being converted to the
observation schema. Current/revised API data are not historical as-of vintages.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen
import zipfile
import io

SOURCES=[
 {'id':'kolada-municipalities','url':'https://api.kolada.se/v3/municipality','format':'json'},
 {'id':'kolada-kpi-definitions','url':'https://api.kolada.se/v3/kpi','format':'json'},
 {'id':'scb-table-index','url':'https://statistikdatabasen.scb.se/api/v2/tables','format':'json'},
 {'id':'skr-26-28','url':'https://skr.se/download/18.22a5529f1a0fb7804e67d572/1791283712510/Prognosunderlag-K-2026-2033-26028.xlsm',
  'format':'xlsm','role':'benchmark_only'},
]+[{'id':f'kolada-motala-{year}','url':f'https://api.kolada.se/v3/data/municipality/0583/year/{year}','format':'json'} for year in range(2010,2026)]


def acquire(directory, sources=None):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    receipts=[];failed_hosts=set()
    for source in SOURCES if sources is None else sources:
        host=urlparse(source['url']).hostname
        receipt={**source,'attemptedAt':datetime.now(timezone.utc).isoformat()}
        if host in failed_hosts:
            receipt.update(status='not_attempted',reason='Earlier request to this host failed in this acquisition')
            receipts.append(receipt);continue
        try:
            with urlopen(source['url'],timeout=15) as response:
                payload=response.read(20_000_001)
                receipt['resolvedUrl']=response.url
            if len(payload)>20_000_000:raise ValueError('Response exceeds 20 MB; narrow the request')
            if source['format']=='json':
                obj=json.loads(payload)
                if not isinstance(obj,(dict,list)):raise ValueError('Unexpected JSON document')
                # Preserve pagination links as well as payload; incomplete pages are not a complete dataset.
                receipt['requiresPaginationReview']=True
            elif source['format']=='xlsm':
                with zipfile.ZipFile(io.BytesIO(payload)) as z:
                    if 'xl/workbook.xml' not in z.namelist():raise ValueError('Not an Excel workbook')
                    if z.testzip():raise ValueError('Corrupt workbook')
            else:raise ValueError('Unsupported source format')
            sha=hashlib.sha256(payload).hexdigest()
            name=sha+'.'+source['format'];(directory/name).write_bytes(payload)
            receipt.update(status='downloaded',sha256=sha,bytes=len(payload),path=name,
                           normalizationStatus='pending_definition_review')
        except (OSError,ValueError,zipfile.BadZipFile) as exc:
            receipt.update(status='failed',error=str(exc))
            if isinstance(exc, URLError) and not isinstance(exc, HTTPError):
                failed_hosts.add(host)
        receipts.append(receipt)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    (directory/f'receipts-{stamp}.json').write_text(json.dumps(receipts,indent=2)+'\n')
    return receipts
