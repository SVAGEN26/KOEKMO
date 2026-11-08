"""Source-defined separation of Motala note 10 items, never outcome cleaning.

Closing stocks remain observed stocks. This is a forecast-base adapter, not a
provision valuation model. Future exceptional flows require their own assumptions.
"""
from copy import deepcopy
import math


POLICIES = ('costbase', 'no-repeat')
FIELDS = ('otherExpense', 'operatingRevenue', 'grants')


def prepare(row, data, policy):
    if policy not in POLICIES:
        raise ValueError('Unknown note separation policy')
    if (data.get('schemaVersion') != 1 or data.get('municipality') != '0583'
            or data.get('scope') != 'kommunen' or data.get('moneyUnit') != 'mnkr'):
        raise ValueError('Incorrect note schema, municipality, scope or unit')
    if row.get('scope') != 'kommunen' or row.get('moneyUnit') != 'mnkr':
        raise ValueError('Incorrect opening ledger scope or unit')
    selected = [r for r in data['rows'] if r['originYear'] == row['year']]
    if len(selected) != 1 or selected[0].get('reviewComplete') is not True:
        raise ValueError('Exactly one reviewed note record required per origin')
    record = deepcopy(selected[0])
    source = deepcopy(data['sources'][record['sourceId']])
    if type(source.get('reportYear')) is not int or not source.get('url') or not source.get('locator'):
        raise ValueError('Missing note source or report year')
    amounts = {k: 0. for k in FIELDS}
    note_net, seen, included = 0., set(), []
    for item in record['items']:
        key, amount, kind = item['field'], item['amount'], item['kind']
        if (not item.get('id') or item['id'] in seen or not item.get('label')
                or type(amount) not in (int, float) or not math.isfinite(amount) or amount <= 0):
            raise ValueError('Invalid or duplicate note item')
        seen.add(item['id'])
        cost = kind == 'recognised_exceptional_cost'
        receipt = kind == 'temporary_receipt'
        if not ((cost and key == 'otherExpense') or
                (receipt and key in ('operatingRevenue', 'grants'))):
            raise ValueError('Incorrect economic sign or ledger mapping for note item')
        note_net += -amount if cost else amount
        if cost or policy == 'no-repeat':
            amounts[key] += amount
            included.append(item['id'])
    stated = record.get('sourceNoteNet')
    if stated is not None and (type(stated) not in (int, float)
            or not math.isfinite(stated) or abs(stated-note_net) > 1e-8):
        raise ValueError('Itemised economic signs disagree with the source net')
    result = deepcopy(row)
    for key, amount in amounts.items():
        value = row[key]
        if type(value) not in (int, float) or not math.isfinite(value) or amount > value:
            raise ValueError('Note adjustment exceeds the reported ledger component')
        result[key] = value-amount
    cost, receipts, grants = (amounts[k] for k in FIELDS)
    result['grossExpense'] -= cost
    result['netCost'] += receipts-cost
    result['result'] += cost-receipts-grants
    # These are algebraic bridges, not changes to actual results used for scoring.
    residuals = (
        result['grossExpense']-result['payroll']-result['pension']-result['otherExpense'],
        result['netCost']-result['grossExpense']+result['operatingRevenue']
            -result['depreciation']-result['costRounding'],
        result['result']-result['tax']-result['grants']+result['netCost']
            -result['financialIncome']+result['financialExpense']-result['resultRounding'])
    if max(map(abs, residuals)) > 1e-6:
        raise ValueError('Unexplained ledger residual in note separation')
    audit = {
        'policy': policy, 'originYear': row['year'], 'source': source, 'note': record,
        'sourceRevisions': source['reportYear'] > row['year'],
        'reportedNoteNet': stated, 'itemisedNoteNet': note_net, 'excludedItemIds': included,
        'excludedFromRecurringBase': amounts,
        'reported': {k: row[k] for k in FIELDS+('grossExpense', 'netCost', 'result')},
        'recurringBase': {k: result[k] for k in FIELDS+('grossExpense', 'netCost', 'result')},
        'reportedResultEffectOfExcludedItems': receipts+grants-cost,
        'futureNewExceptionalCosts': 'Assumed zero in this experiment, not observed or actuarially forecast.',
        'temporaryReceipts': ('Original income assumption retained to isolate costs.' if policy == 'costbase'
            else 'No repeat and no replacement financing; mechanical sensitivity, not a probability interval.'),
        'stockTreatment': 'All observed closing stocks remain unchanged. No repeated disposal or liability removal.',
        'scopeLimit': 'Note10 only. Payments, remeasurement, other impairments and working capital are not estimated.'}
    return result, audit
