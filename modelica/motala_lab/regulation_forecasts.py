"""Dated regulation rates with a fixed local fiscal-population proxy.

Opening note categories are replaced once; no target-year outcomes enter prepare.
"""
from copy import deepcopy

from .revenue_bridge import finite


COMPONENTS = ('regulationAndTransferredGrant', 'regulationGrant',
              'incomeEqualisation', 'remainingGrants', 'grants')


def prepare(parent_path, ledger, component_data):
    path = deepcopy(parent_path)
    origin = path['originYear']
    if ledger['year'] != origin or 'settlementForecast' not in path:
        raise ValueError('Regulation requires the origin ledger and v7 settlement path')
    population = finite(ledger.get('population'), 'opening year-end population', minimum=1)
    opening = path['openingComponents']['grantComponents']
    r0 = finite(opening['regulationGrant'], 'opening regulation')
    f0 = finite(opening['refugeeWelfareGrant'], 'opening transferred grant', minimum=0)
    denominator = finite(path['grantAnchor0']-path['incomeEqualisation0'],
                         'parent inherited grant anchor')
    if denominator <= 0:
        raise ValueError('Parent inherited grant anchor must be positive')
    transfer = None
    if f0:
        matches = [r for r in component_data.get('categoryTransitions', [])
                   if r['openingYear'] == origin and r['effectiveYear'] == origin+1
                   and r['fromComponent'] == 'refugeeWelfareGrant'
                   and r['toComponent'] == 'regulationGrant']
        if (len(matches) != 1 or matches[0]['openingAmount'] != f0
                or matches[0]['unit'] != 'mnkr' or not matches[0].get('source')
                or not matches[0].get('locator')):
            raise ValueError('A sourced category transition is required for the opening refugee grant')
        transfer = deepcopy(matches[0])
    source_rows = path['vintage']['rows']
    years = list(range(origin, origin+len(path['rows'])+1))
    if [r['year'] for r in source_rows] != years:
        raise ValueError('Regulation fiscal years differ from the normalized path')
    rows = []
    for source in source_rows[1:]:
        rate = finite(source['municipalRegulationPerCapita'], 'dated regulation rate')
        rows.append({'year': source['year'], 'ratePerPerson': rate,
                     'fiscalPopulationReferenceDate': f"{source['year']-1}-11-01",
                     'regulationGrant': rate*population/1e6,
                     'refugeeWelfareGrant': 0.,
                     'role': 'dated_SKR_estimate_with_constant_population_proxy'})
    path['regulationForecast'] = {
        'populationProxy': {'value': population, 'unit': 'persons',
            'referenceDate': f'{origin}-12-31',
            'status': 'constant_year_end_proxy_for_each_target_previous_November',
            'sourceId': ledger.get('demographySourceId', ledger.get('sourceId')),
            'historicalPublicationAvailabilityEstablished': False},
        'regulationGrant0': r0, 'transferredRefugeeGrant0': f0,
        'parentInheritedGrantAnchor': denominator,
        'categoryTransition': transfer, 'rows': rows}
    return path


def allocation(parent, path, index):
    """Split the old proportional remainder; never allocate from new total grants."""
    forecast = path['regulationForecast']
    source = forecast['rows'][index]
    if parent['year'] != source['year']:
        raise ValueError('Regulation and parent years differ')
    scale = parent['inheritedGrants']/forecast['parentInheritedGrantAnchor']
    old_r = forecast['regulationGrant0']*scale
    old_f = forecast['transferredRefugeeGrant0']*scale
    remaining = parent['inheritedGrants']-old_r-old_f
    return {'regulationGrant': source['regulationGrant'],
            'refugeeWelfareGrant': source['refugeeWelfareGrant'],
            'regulationAndTransferredGrant': source['regulationGrant'],
            'allocatedParentRegulationGrant': old_r,
            'allocatedParentRefugeeWelfareGrant': old_f,
            'remainingGrants': remaining, 'inheritedGrants': remaining}


def accounting_projection(parent, path):
    if len(parent) != len(path['regulationForecast']['rows']):
        raise ValueError('Regulation and accounting horizons differ')
    result = deepcopy(parent)
    for index, row in enumerate(result):
        parts = allocation(row, path, index)
        grants = row['incomeEqualisation']+parts['regulationGrant']+parts['remainingGrants']
        row['result'] += grants-row['grants']
        row.update(parts, grants=grants, taxAndGrants=row['tax']+grants)
    return result


def population_sensitivity(path, differences):
    return [{'year': row['year'], 'populationDifference': finite(delta, 'population difference'),
             'regulationGrantDifference': row['ratePerPerson']*delta/1e6,
             'role': 'hypothetical_direct_revenue_effect_not_error_bound_or_full_result_interval'}
            for row in path['regulationForecast']['rows'] for delta in differences]
