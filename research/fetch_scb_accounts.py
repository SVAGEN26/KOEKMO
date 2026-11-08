#!/usr/bin/env python3
"""Fetch four SCB accounts tables for Motala, preserving sources before modelling.

Uses only Python's standard library and the documented PxWebApi v2 endpoints.
Exports the current data vintage, not historically available forecast inputs.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
API = 'https://statistikdatabasen.scb.se/api/v2/tables/'
REGION = '0583'
MAX_BYTES = 32 * 1024 * 1024


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def codes(dataset, variable):
    """Use the explicit JSON-stat axis order, never label/dict insertion order."""
    category = dataset['dimension'][variable]['category']
    index = category.get('index')
    size = dataset['size'][dataset['id'].index(variable)]
    if isinstance(index, list):
        result = index
    elif isinstance(index, dict):
        if any(type(n) is not int for n in index.values()) or sorted(index.values()) != list(range(size)):
            raise ValueError('Invalid category positions: ' + variable)
        result = sorted(index, key=index.get)
    elif size == 1 and len(category.get('label', {})) == 1:
        result = list(category['label'])
    else:
        raise ValueError('Missing category order: ' + variable)
    if len(result) != size or len(set(result)) != size:
        raise ValueError('Category size mismatch: ' + variable)
    return result


def selection(metadata, source):
    ids = metadata['id']
    if len(ids) != len(set(ids)) or len(ids) != len(metadata['size']):
        raise ValueError('Invalid dimensions')
    if 'Region' not in ids or 'Tid' not in ids:
        raise ValueError('Expected SCB Region and Tid dimensions')
    selected = {}
    for variable in ids:
        available = codes(metadata, variable)
        if variable == 'Region':
            chosen = [REGION]
        elif variable == 'Tid':
            first, last = source['years']
            chosen = [str(year) for year in range(first, last + 1)]
        else:
            chosen = available
        if not chosen or not set(chosen).issubset(available):
            raise ValueError('Missing requested categories: ' + variable)
        selected[variable] = chosen
    if math.prod(map(len, selected.values())) > 150000:
        raise ValueError('Selection exceeds SCB cell limit')
    return {'selection': [{'variableCode': key, 'valueCodes': value} for key, value in selected.items()]}


def observations(dataset, request, table_id):
    """Validate the returned selection, then preserve values, missingness and units."""
    expected = {item['variableCode']: item['valueCodes'] for item in request['selection']}
    ids = dataset['id']
    if dataset.get('class') != 'dataset' or len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError('Unexpected response dimensions')
    if len(dataset['size']) != len(ids):
        raise ValueError('Unexpected response shape')
    axes = [codes(dataset, variable) for variable in ids]
    if any(set(axis) != set(expected[variable]) for variable, axis in zip(ids, axes)):
        raise ValueError('Response does not match requested municipality/years/items')
    if expected.get('Region') != [REGION]:
        raise ValueError('Only Motala is supported')
    count = math.prod(dataset['size'])
    values = dataset['value']
    status = dataset.get('status')
    for field in (values, status):
        if isinstance(field, list) and len(field) != count:
            raise ValueError('Array length differs from dimensions')
        if isinstance(field, dict) and any(not str(k).isdigit() or str(int(k)) != k or not 0 <= int(k) < count for k in field):
            raise ValueError('Invalid sparse index')
    if not isinstance(values, (list, dict)):
        raise ValueError('Expected numeric values array or sparse object')
    if status is not None and not isinstance(status, (str, list, dict)):
        raise ValueError('Invalid status field')
    for index, coordinate in enumerate(itertools.product(*axes)):
        value = values[index] if isinstance(values, list) else values.get(str(index))
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
            raise ValueError('Invalid observation value')
        cell_status = (status[index] if isinstance(status, list) else
                       status.get(str(index), '') if isinstance(status, dict) else status or '')
        coordinate = dict(zip(ids, coordinate))
        labels, units = {}, {}
        for variable, code in coordinate.items():
            category = dataset['dimension'][variable]['category']
            labels[variable] = category.get('label', {}).get(code, code)
            if code in (category.get('unit') or {}):
                units[variable] = category['unit'][code]
        # No unit conversion, sign changes, total reconstruction or model import.
        yield {'table': table_id, 'year': coordinate['Tid'], 'region_code': coordinate['Region'],
               'region': labels['Region'], 'item_codes': json.dumps(coordinate, ensure_ascii=False),
               'item_labels': json.dumps(labels, ensure_ascii=False), 'value': '' if value is None else value,
               'unit_metadata': json.dumps(units, ensure_ascii=False), 'status': cell_status}


def fetch_json(url, path, receipts, body=None):
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8')
    entry = {'url': url, 'method': 'GET' if body is None else 'POST', 'file': path.name,
             'requestedAt': datetime.now(timezone.utc).isoformat(), 'status': 'failed'}
    if payload is not None:
        entry['requestSha256'] = hashlib.sha256(payload).hexdigest()
        path.with_suffix('.request.json').write_bytes(payload)
    receipts.append(entry)
    request = Request(url, data=payload, headers={'Accept': 'application/json',
                      'Content-Type': 'application/json', 'User-Agent': 'Motala-SCB-accounts/1.0'})
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError('Response exceeds 32 MiB')
            entry.update(finalUrl=response.geturl(), contentType=response.headers.get('Content-Type'),
                         lastModified=response.headers.get('Last-Modified'))
        path.write_bytes(raw)
        entry.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        obj = json.loads(raw)
        entry['status'] = 'downloaded'
        return obj
    except Exception as error:
        entry['error'] = str(error)
        raise
    finally:
        entry['finishedAt'] = datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--table', action='append', choices=['TAB6777', 'TAB4202', 'TAB6782', 'TAB4199'],
                        help='Fetch only this table; repeat to select several. Default: all four.')
    parser.add_argument('--out', type=Path, help='New output directory; existing directories are never overwritten.')
    args = parser.parse_args()
    catalogue_path = ROOT / 'data/municipal-economics-research.json'
    catalogue_bytes = catalogue_path.read_bytes()
    catalogue = json.loads(catalogue_bytes)
    sources = [row for row in catalogue['observedDataRoutes'] if not args.table or row['tableId'] in args.table]
    destination = args.out or ROOT / 'data/raw/scb-accounts' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'source-catalogue.json').write_bytes(catalogue_bytes)
    packet = {'municipality': REGION, 'catalogueSha256': hashlib.sha256(catalogue_bytes).hexdigest(),
              'note': 'Current observed data vintage. Retrieval date is not historical availability. No automatic model import.',
              'requests': [], 'tables': []}
    for source in sources:
        table_id = source['tableId']
        table = {'id': table_id, 'status': 'failed'}
        packet['tables'].append(table)
        try:
            metadata = fetch_json(API + table_id + '/metadata?lang=sv&defaultSelection=false',
                                  destination / (table_id + '-metadata.json'), packet['requests'])
            body = selection(metadata, source)
            data = fetch_json(API + table_id + '/data?' + urlencode({'lang': 'sv', 'outputFormat': 'json-stat2'}),
                              destination / (table_id + '-data.json'), packet['requests'], body)
            rows = list(observations(data, body, table_id))
            if not rows:
                raise ValueError('Empty table')
            csv_path = destination / (table_id + '-motala.csv')
            with csv_path.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            table.update(status='validated_selection', cells=len(rows), missing=sum(row['value'] == '' for row in rows),
                         csvFile=csv_path.name, csvSha256=hashlib.sha256(csv_path.read_bytes()).hexdigest())
            print(table_id, ':', len(rows), 'cells saved for Motala', flush=True)
        except Exception as error:
            table['error'] = str(error)
            print(table_id, ':', error, file=sys.stderr, flush=True)
        finally:
            dump(destination / 'receipts.json', packet)
    print('Sources and receipts:', destination, flush=True)
    return 0 if all(table['status'] == 'validated_selection' for table in packet['tables']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
