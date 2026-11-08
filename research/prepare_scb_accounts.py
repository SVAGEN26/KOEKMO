#!/usr/bin/env python3
"""Prepare the reviewed TAB6777 vintage for the locked budget-response experiment.

Works offline from the preserved source packet. Does not splice annual-report
observations into SCB, fill missing observations, or change the forecast protocol.
"""
import argparse
import hashlib
import json
from pathlib import Path

from fetch_scb_accounts import observations, selection
from motala_lab.budget_response import validate_rows

ROOT = Path(__file__).resolve().parent
TABLE = 'TAB6777'
SOURCE_ID = 'scb-TAB6777-20261016'


def load_packet(directory):
    directory = Path(directory)
    receipts = json.loads((directory/'receipts.json').read_text())
    names = [TABLE+'-metadata.json', TABLE+'-data.json']
    files = {}
    hashes = {}
    for name in names:
        matches = [r for r in receipts['requests'] if r['file'] == name and r['status'] == 'downloaded']
        if len(matches) != 1:
            raise ValueError('Exactly one successful source receipt required: '+name)
        entry = matches[0]
        raw = (directory/name).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != entry['sha256'] or len(raw) != entry['bytes']:
            raise ValueError('Source hash or size mismatch: '+name)
        files[name] = json.loads(raw)
        hashes[name] = actual
    data_receipt = next(r for r in receipts['requests'] if r['file'] == names[1] and r['status'] == 'downloaded')
    query_path = directory/(TABLE+'-data.request.json')
    query_bytes = query_path.read_bytes()
    if hashlib.sha256(query_bytes).hexdigest() != data_receipt['requestSha256']:
        raise ValueError('Source query hash mismatch')
    hashes[query_path.name] = data_receipt['requestSha256']
    hashes['receipts.json'] = hashlib.sha256((directory/'receipts.json').read_bytes()).hexdigest()
    return files[names[0]], files[names[1]], json.loads(query_bytes), data_receipt, hashes


def normalize(metadata, data, query, mapping):
    if (mapping['tableId'] != TABLE or mapping['municipality'] != '0583'
            or mapping['scope'] != 'kommunen' or mapping['inputUnit'] != 'tkr'
            or mapping['outputUnit'] != 'mnkr_current_prices' or mapping['scale'] != 0.001):
        raise ValueError('Expected reviewed Motala TAB6777 mapping in tkr')
    if data.get('extension', {}).get('px', {}).get('tableid') != TABLE:
        raise ValueError('Unexpected source table')
    if query != selection(metadata, {'years': mapping['years']}):
        raise ValueError('Source query differs from reviewed municipality/year/item selection')
    item_axis = mapping['itemDimension']
    for code, label in mapping['expectedLabels'].items():
        if data['dimension'][item_axis]['category']['label'].get(code) != label:
            raise ValueError('Source definition differs from reviewed mapping: '+code)
    indexed = {}
    for cell in observations(data, query, TABLE):
        coordinate = json.loads(cell['item_codes'])
        units = json.loads(cell['unit_metadata'])
        if coordinate['ContentsCode'] != mapping['contentsCode'] or units['ContentsCode']['base'] != 'tkr':
            raise ValueError('Unexpected contents code or source unit')
        indexed.setdefault(int(cell['year']), {})[coordinate[item_axis]] = cell['value']
    if sorted(indexed) != list(range(mapping['years'][0], mapping['years'][1]+1)):
        raise ValueError('Missing observed year')
    rows = []
    for year, cells in sorted(indexed.items()):
        def number(code):
            value = cells[code]
            if type(value) is not int:
                raise ValueError(f'Missing or non-integer-tkr source cell: {year}/{code}')
            return value

        revenue = number('040')+number('050')
        cost = -number('030')
        finance = number('060')+number('072')
        if year <= 2010:
            finance += number('071')
        elif cells['071'] != '':
            raise ValueError('Unexpected pension-interest presentation after 2010')
        if year <= 2018:
            extra = number('100')+number('110')
            if cells['085'] != '':
                raise ValueError('Unexpected extraordinary-item presentation before 2019')
        else:
            extra = number('085')
            if cells['100'] != '' or cells['110'] != '':
                raise ValueError('Unexpected extraordinary-item presentation after 2018')
        if revenue-cost+finance != number('080'):
            raise ValueError(f'Unexplained result-after-finance residual: {year}')
        if number('120')-number('080') != extra:
            raise ValueError(f'Unexplained reported-result residual: {year}')
        rows.append({'year': year, 'taxAndGrants': revenue/1000, 'netCost': cost/1000,
                     'financeNet': finance/1000, 'result': number('120')/1000,
                     'resultAccountingResidual': extra/1000,
                     'sourceId': SOURCE_ID,
                     'locator': f'TAB6777; Region=0583; ContentsCode=000008H2; Tid={year}; Resultatraknposter per definitionMapping',
                     'sourceCellsTkr': {key: cells[key] if cells[key] != '' else None
                                        for key in mapping['expectedLabels']}})
    validate_rows(rows)
    return rows


def reconcile(rows, reference):
    lookup = {r['year']: r for r in reference['rows']}
    comparison = []
    for row in rows:
        if row['year'] not in lookup:
            continue
        old = lookup[row['year']]
        actual = {'taxAndGrants': old['tax']+old['grants'], 'netCost': old['netCost'],
                  'financeNet': old['financialIncome']-old['financialExpense'], 'result': old['result']}
        comparison.append({'year': row['year'], 'annualReportSourceId': old['sourceId'],
                           'annualReportValues': actual,
                           'scbMinusAnnualReport': {key: round(row[key]-value, 3) for key, value in actual.items()}})
    return {'definition': 'SCB minus the unchanged selected annual-report observation, mnkr',
            'observationsSpliced': False, 'rows': comparison,
            'note': 'Preserve source/version differences. In particular the 2021 grant and cost differences exceed rounding. Reasons are not inferred from arithmetic alone.'}


def prepare(packet, mapping_path, reference_path):
    metadata, data, query, receipt, hashes = load_packet(packet)
    mapping = json.loads(Path(mapping_path).read_text())
    rows = normalize(metadata, data, query, mapping)
    return {'schemaVersion': 1, 'municipality': '0583', 'scope': 'kommunen',
            'moneyUnit': 'mnkr_current_prices', 'seriesTreatment': 'reported_unadjusted',
            'evidenceClass': 'retrospective_development_not_real_time',
            'sources': {SOURCE_ID: {
                'url': 'https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__OE__OE0107__OE0107A/ResultKnN/',
                'apiUrl': receipt['url'], 'retrievedAt': receipt['finishedAt'],
                'sourceUpdatedAt': data['updated'], 'originalHistoricalReleaseDates': None,
                'sourceFileHashes': hashes}},
            'definitionMapping': mapping,
            'annualReportReconciliation': reconcile(rows, json.loads(Path(reference_path).read_text())),
            'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, default=ROOT/'reference/scb-accounts-20261016')
    parser.add_argument('--mapping', type=Path, default=ROOT/'data/scb-budget-response-mapping.json')
    parser.add_argument('--annual-ledgers', type=Path, default=ROOT/'data/annual-ledgers.json')
    parser.add_argument('--out', type=Path, required=True, help='New aggregate JSON file')
    args = parser.parse_args()
    document = prepare(args.packet, args.mapping, args.annual_ledgers)
    with args.out.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(f'Prepared {len(document["rows"])} observed years: {args.out}')


if __name__ == '__main__':
    main()
