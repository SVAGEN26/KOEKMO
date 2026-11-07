"""National tax-base paths as a diagnostic, not a municipal revenue forecast."""
from copy import deepcopy
from datetime import date
import math

from .macro import factors


def select_vintage(data, origin, years, cost_vintage):
    if data.get('definition') != 'national_actual_nominal_tax_base_growth' or data.get('unit') != 'annual percent change':
        raise ValueError('Actual nominal national tax-base growth in annual percent is required')
    matches = [v for v in data['vintages'] if v['originYear'] == origin]
    if len(matches) != 1:
        raise ValueError('Exactly one tax vintage required per origin')
    vintage = deepcopy(matches[0])
    published = date.fromisoformat(vintage['publicationDate'])
    if published.year != origin or published.month != 12:
        raise ValueError('Tax input must be a December vintage from the origin year')
    if any(vintage[k] != cost_vintage[k] for k in ('originYear', 'publicationDate', 'circular')):
        raise ValueError('Tax and cost inputs must use the same declared circular')
    rows = {r['year']: r for r in vintage['rows']}
    if len(rows) != len(vintage['rows']) or type(years) is not int or years < 1:
        raise ValueError('Duplicate tax year or invalid horizon')
    try:
        vintage['rows'] = [rows[origin+h] for h in range(1, years+1)]
    except KeyError as e:
        raise ValueError('Missing tax horizon; no silent extrapolation') from e
    if [r['year'] for r in vintage['rows']] != [r['year'] for r in cost_vintage['rows']]:
        raise ValueError('Tax and cost horizons must match')
    for row in vintage['rows']:
        value = row['taxBasePercent']
        if type(value) not in (int, float) or not math.isfinite(value) or value <= -100:
            raise ValueError('Invalid nominal tax-base growth')
    vintage['mapping'] = data['mapping']
    vintage['role'] = 'diagnostic_sensitivity_not_local_forecast'
    return vintage


def accounting_projection(original, tax0, vintage):
    """Change only tax and its linear ledger consequences in a comparator."""
    if len(original) != len(vintage['rows']):
        raise ValueError('Accounting and tax horizons must match')
    result = deepcopy(original)
    for row, source, factor in zip(result, vintage['rows'], factors(vintage, 'taxBasePercent')):
        if row['year'] != source['year']:
            raise ValueError('Accounting and tax years must match')
        tax = tax0*factor
        delta = tax-row['tax']
        row['tax'] = tax
        row['taxAndGrants'] += delta
        row['result'] += delta
    return result
