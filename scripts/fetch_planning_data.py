#!/usr/bin/env python3
"""Archive public Motala planning inputs, without changing calibrated model inputs."""
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/downloads' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
KPI = ['N11004','N11006','N11008','N11010','N11807','N15025','N15027','N15028','N15034','N15829','N15832','N20007','N20014','N20043','N20048','N20050','N21702','N21703','N21705','N21826']

def main():
    OUT.mkdir(parents=True, exist_ok=False)
    receipt = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'municipality': '0583', 'files': [], 'errors': [], 'notes': ['Archived source data only; not imported into the model. Current source vintage is not historical real-time data.']}
    def save(name, data, url, query=None):
        (OUT / name).write_bytes(data)
        receipt['files'].append({'file': name, 'url': url, 'query': query, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    def fetch(name, url, query=None, pdf=False):
        req = urllib.request.Request(url, data=None if query is None else json.dumps(query).encode(), headers={'User-Agent': 'Motala-research-data/1.0', 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=35) as response:
            data = response.read()
        if pdf and not data.startswith(b'%PDF-'):
            raise ValueError('Response is not a PDF')
        save(name, data, url, query)
        return data
    def task(label, fn):
        try:
            fn()
            print(label + ': OK', flush=True)
        except Exception as exc:
            receipt['errors'].append({'task': label, 'error': str(exc)})
            print(label + ': ' + str(exc), flush=True)
    pdfs = {
        'budget-2026-plan-2027-2028.pdf': 'Budget-Mal-och-resursplan-for-2026-med-plan-for-2027-2028.pdf',
        'budget-2025-plan-2026-2027.pdf': 'Budget_260323.pdf',
        'arsredovisning-2025.pdf': 'Arsredovisning-2025.pdf',
        'arsredovisning-2024.pdf': 'Arsredovisning-2024.pdf',
        'arsredovisning-2023.pdf': 'MK-arsredovisning-2023-laguppl.pdf',
        'arsredovisning-2022.pdf': 'arsredovisning-2022.pdf'}
    for name, remote in pdfs.items():
        task(name, lambda name=name, remote=remote: fetch(name, 'https://www.motala.se/media/uploads/' + remote, pdf=True))
    for table in ['bep6001', 'bep6006']:
        def population(table=table):
            url = 'https://statistik.linkoping.se/PXWeb/api/v1/sv/Samlad_planering/LevaBo/' + table + '.px'
            meta = json.loads(fetch(table + '-metadata.json', url))
            query = {'query': [{'code': v['code'], 'selection': {'filter': 'item', 'values': ['0583'] if v['code'] == 'område' else v['values']}} for v in meta['variables']], 'response': {'format': 'json'}}
            result = json.loads(fetch(table + '-motala.json', url, query))
            expected = 1
            for item in query['query']:
                expected *= len(item['selection']['values'])
            if len(result['data']) != expected:
                raise ValueError('Incomplete population response')
            area_index = [c['code'] for c in result['columns'] if c['type'] != 'c'].index('område')
            if any(row['key'][area_index] != '0583' for row in result['data']):
                raise ValueError('Wrong municipality')
            stream = io.StringIO()
            writer = csv.writer(stream)
            writer.writerow([c['code'] for c in result['columns']])
            for row in result['data']:
                writer.writerow(row['key'] + row['values'])
            save(table + '-motala.csv', stream.getvalue().encode('utf-8-sig'), url, query)
        task(table, population)
    def kolada():
        base = 'https://api.kolada.se/v3/'
        metadata = json.loads(fetch('kolada-kpi-metadata.json', base + 'kpi/' + ','.join(KPI)))
        titles = {x['id']: x['title'] for x in metadata['values']}
        if set(titles) != set(KPI):
            raise ValueError('Missing KPI metadata')
        url = base + 'data/kpi/' + ','.join(KPI) + '/municipality/0583/year/' + ','.join(map(str, range(2010, 2026))) + '?per_page=5000'
        rows, seen = [], set()
        while url:
            if url in seen or not url.startswith(base):
                raise ValueError('Unexpected pagination URL')
            seen.add(url)
            result = json.loads(fetch('kolada-data-page-' + str(len(seen)) + '.json', url))
            rows.extend(result['values'])
            url = result.get('next_url')
        if not rows or any(r['municipality'] != '0583' or not 2010 <= int(r['period']) <= 2025 or r['kpi'] not in titles for r in rows):
            raise ValueError('Wrong or empty Kolada selection')
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(['municipality','year','kpi','title','gender','value','status','count','isdeleted'])
        coverage = {}
        for row in rows:
            for value in row['values']:
                writer.writerow([row['municipality'], row['period'], row['kpi'], titles[row['kpi']], value.get('gender'), value.get('value'), value.get('status'), value.get('count'), value.get('isdeleted')])
                if value.get('value') is not None and not value.get('isdeleted'):
                    coverage.setdefault(row['kpi'], set()).add(row['period'])
        save('kolada-motala-2010-2025.csv', stream.getvalue().encode('utf-8-sig'), base)
        receipt['kolada_coverage'] = {k: {'title': titles[k], 'years_with_values': sorted(coverage.get(k, set()))} for k in KPI}
    task('Kolada', kolada)
    (OUT / 'manifest.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print('Archive:', OUT)
    print('Files:', len(receipt['files']), 'Errors:', len(receipt['errors']))
    return 1 if receipt['errors'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
