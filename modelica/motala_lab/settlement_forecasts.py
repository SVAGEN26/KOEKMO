"""Dated h1 settlement and explicit later zero expectations, with a population proxy."""
from copy import deepcopy

from .revenue_bridge import finite


COMPONENTS = ('preliminaryTax', 'settlementAndRevision', 'tax')


def prepare(normalized_path, ledger):
    """Uses only the selected opening ledger and its selected December vintage."""
    path = deepcopy(normalized_path)
    origin = path['originYear']
    if ledger['year'] != origin:
        raise ValueError('Population proxy must come from the forecast origin')
    population = finite(ledger.get('population'), 'opening year-end population', minimum=1)
    source_rows = path['vintage']['rows']
    if [r['year'] for r in source_rows] != list(range(origin, origin+len(path['rows'])+1)):
        raise ValueError('Settlement fiscal-year sequence differs from normalized revenue')
    rows = []
    for horizon, source in enumerate(source_rows[1:], 1):
        observed_source = source['currentYearSettlementPerCapita']
        rate = finite(observed_source, 'dated first-year settlement') if horizon == 1 else 0.
        if horizon > 1 and observed_source is not None:
            raise ValueError('Later settlement source must remain null under this protocol')
        current = rate*population/1e6
        rows.append({'year': origin+horizon, 'sourceCurrentPerCapita': observed_source,
                     'assumedCurrentPerCapita': rate,
                     'currentYearSettlement': current, 'priorYearSettlementRevision': 0.,
                     'settlementAndRevision': current,
                     'role': 'dated_SKR_estimate_with_population_proxy' if horizon == 1 else 'declared_zero_expectation'})
    path['settlementForecast'] = {
        'populationProxy': {'value': population, 'unit': 'persons', 'referenceDate': f'{origin}-12-31',
            'proxyForReferenceDate': f'{origin}-11-01', 'status': 'observed_year_end_used_as_November_proxy',
            'sourceId': ledger.get('demographySourceId', ledger.get('sourceId')),
            'historicalPublicationAvailabilityEstablished': False},
        'priorRevisionPolicy': 'All future revisions have declared expectation zero, not known outcomes.',
        'rows': rows}
    return path


def population_sensitivity(path, differences):
    rate = path['settlementForecast']['rows'][0]['assumedCurrentPerCapita']
    return [{'populationDifference': finite(n, 'population difference'),
             'firstYearSettlementDifference': rate*n/1e6,
             'role': 'hypothetical_direct_revenue_effect_not_error_bound_or_full_result_interval'} for n in differences]


def accounting_projection(parent, path):
    rows = path['settlementForecast']['rows']
    if len(parent) != len(rows):
        raise ValueError('Settlement and accounting horizons differ')
    result = deepcopy(parent)
    for row, source in zip(result, rows):
        if row['year'] != source['year']:
            raise ValueError('Settlement and accounting years differ')
        tax = row['preliminaryTax']+source['settlementAndRevision']
        row['result'] += tax-row['tax']
        row.update(tax=tax, taxAndGrants=tax+row['grants'], inheritedTax=0.,
                   taxSettlement=source['settlementAndRevision'],
                   currentYearSettlement=source['currentYearSettlement'],
                   priorYearSettlementRevision=source['priorYearSettlementRevision'],
                   settlementAndRevision=source['settlementAndRevision'])
    return result
