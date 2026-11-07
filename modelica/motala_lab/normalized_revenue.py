"""A fixed-population P/I diagnostic, not a complete administrative forecast.

Absolute November population cancels from the normalized statutory identities.
The inherited residuals deliberately retain the parent's remaining assumptions.
No target outcomes or fitted parameters are used by prepare().
"""
from copy import deepcopy

from . import revenue_bridge


COMPONENTS = ('preliminaryTax', 'incomeEqualisation', 'preliminaryTaxAndEqualisation')


def prepare(component_data, ledger, parameters, vintage):
    opening = revenue_bridge.opening_components(component_data, ledger)
    rows = vintage['rows']
    origin = ledger['year']
    if not 2 <= len(rows) <= 4 or [r['year'] for r in rows] != list(range(origin, origin+len(rows))):
        raise ValueError('Normalized revenue requires origin and consecutive forecast years')
    if parameters.get('taxRate', parameters['taxRate0']) != parameters['taxRate0']:
        raise ValueError('Historical normalized revenue requires the reference tax rate')
    tax = revenue_bridge.finite(parameters['tax0'], 'tax anchor', minimum=1)
    grants = revenue_bridge.finite(parameters['grants0'], 'note-adjusted grant anchor', minimum=1)
    if abs(tax-ledger['tax']) > 1e-6:
        raise ValueError('Preliminary tax anchor must use the reported opening tax total')
    capacity = revenue_bridge.finite(rows[0]['governmentMeanTaxCapacity'], 'opening capacity', minimum=1)
    path = []
    for h, row in enumerate(rows[1:], 1):
        kind = 'governmentMeanTaxCapacity' if h == 1 else 'skrMeanTaxCapacity'
        value = revenue_bridge.finite(row[kind], kind, minimum=1)
        path.append({'year': row['year'], 'capacity': value, 'capacityKind': kind,
                     'populationRatio': 1, 'factor': value/capacity})
    return {'originYear': origin, 'role': 'normalized_PI_diagnostic_not_complete_forecast',
            'preliminaryTax0': opening['taxComponents']['preliminaryTax'],
            'incomeEqualisation0': opening['grantComponents']['incomeEqualisation'],
            'taxAnchor0': tax, 'grantAnchor0': grants, 'openingComponents': opening,
            'vintage': deepcopy(vintage), 'rows': path}


def allocation(parent, path, index):
    """Exact annual replacement, with unchanged remaining revenue components."""
    source = path['rows'][index]
    if parent['year'] != source['year']:
        raise ValueError('Parent and normalized revenue years differ')
    p0, i0 = path['preliminaryTax0'], path['incomeEqualisation0']
    old_p = p0*parent['tax']/path['taxAnchor0']
    old_i = i0*parent['grants']/path['grantAnchor0']
    p, i = p0*source['factor'], i0*source['factor']
    return {'preliminaryTax': p, 'incomeEqualisation': i,
            'preliminaryTaxAndEqualisation': p+i,
            'allocatedParentPreliminaryTax': old_p,
            'allocatedParentIncomeEqualisation': old_i,
            'inheritedTax': parent['tax']-old_p,
            'inheritedGrants': parent['grants']-old_i}


def accounting_projection(parent, path):
    if len(parent) != len(path['rows']):
        raise ValueError('Parent and normalized revenue horizons differ')
    result = deepcopy(parent)
    for index, row in enumerate(result):
        parts = allocation(row, path, index)
        tax = parts['preliminaryTax']+parts['inheritedTax']
        grants = parts['incomeEqualisation']+parts['inheritedGrants']
        row['result'] += tax+grants-row['tax']-row['grants']
        row.update(parts, tax=tax, grants=grants, taxAndGrants=tax+grants)
    return result
