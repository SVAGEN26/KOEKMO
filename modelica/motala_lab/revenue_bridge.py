"""Reconciled revenue sources and statutory algebra.

The normalized P/I replay uses the opening-component and vintage selectors.
The statutory amount functions still require explicit administrative bases
and population references; they never infer those inputs from future accounts
or replace missing November counts with year-end counts.
All monetary outputs are mnkr. Tax bases are mnkr of taxable income, capacities
and settlements SEK/person, and tax rates fractions (not percentage points).
"""
from copy import deepcopy
from datetime import date
import math


TAX_PARTS = ('preliminaryTax', 'estimatedCurrentYearSettlement',
             'priorYearSettlementDifference')
GRANT_PARTS = ('incomeEqualisation', 'costEqualisation', 'regulationGrant',
               'lssEqualisation', 'propertyFee', 'refugeeWelfareGrant',
               'otherGeneralGrants')
NATIONAL_UNITS = {'population': 'persons', 'capacity': 'SEK taxable income/person',
                  'regulation': 'SEK/person', 'settlement': 'SEK/person'}


def finite(value, name, *, minimum=None, maximum=None):
    if (type(value) not in (int, float) or not math.isfinite(value)
            or (minimum is not None and value < minimum)
            or (maximum is not None and value > maximum)):
        raise ValueError('Invalid ' + name)
    return value


def opening_components(data, ledger):
    """Select only the requested origin and reconcile both published totals."""
    if (data.get('schemaVersion') != 1 or data.get('municipality') != '0583'
            or data.get('scope') != 'kommunen' or data.get('unit') != 'mnkr'):
        raise ValueError('Incorrect revenue schema, municipality, scope or unit')
    if ledger.get('scope') != 'kommunen' or ledger.get('moneyUnit') != 'mnkr':
        raise ValueError('Incorrect opening ledger scope or unit')
    matches = [r for r in data['rows'] if r['year'] == ledger['year']]
    if len(matches) != 1:
        raise ValueError('Exactly one component record required per opening year')
    row = deepcopy(matches[0])
    if row.get('scope') != 'kommunen' or row.get('moneyUnit') != 'mnkr':
        raise ValueError('Incorrect component scope or unit')
    source = deepcopy(data['sources'][row['sourceId']])
    if not source.get('url') or not source.get('locator'):
        raise ValueError('Missing component source or locator')
    precision = finite(row['reportingPrecisionMnkr'], 'source reporting precision')
    if precision not in (0.1, 1):
        raise ValueError('Unsupported source reporting precision')
    for prefix, fields, target in [('tax', TAX_PARTS, 'tax'), ('grant', GRANT_PARTS, 'grants')]:
        parts = row[prefix+'Components']
        if set(parts) != set(fields):
            raise ValueError('Unexpected or missing ' + prefix + ' component')
        total = sum(finite(parts[k], k) for k in fields)
        residual = finite(row[prefix+'RoundingResidual'], prefix+' rounding')
        # Each printed component and the printed total can be rounded by
        # at most half a reporting unit. A balancing plug is not rounding.
        if abs(residual) > (len(fields)+1)*precision/2 + 1e-6:
            raise ValueError('Rounding residual exceeds source precision')
        reported = finite(row['reported'+target.title()], target+' total')
        observed = finite(ledger[target], target+' ledger total')
        if abs(total+residual-reported) > 1e-6 or abs(reported-observed) > 1e-6:
            raise ValueError('Unexplained ' + prefix + ' reconciliation difference')
    row['source'] = source
    row['historicalAvailabilityEstablished'] = False
    return row


def select_vintage(data, origin, years, cost_vintage):
    """Keep fiscal-year and November-year columns separate in the selected data."""
    if (data.get('schemaVersion') != 1
            or data.get('scope') != 'Swedish municipalities, not regions'
            or data.get('unitCodes') != NATIONAL_UNITS):
        raise ValueError('Municipal national revenue sources required')
    if type(years) is not int or not 1 <= years <= 3:
        raise ValueError('One to three prospective years required')
    matches = [v for v in data['vintages'] if v['originYear'] == origin]
    if len(matches) != 1:
        raise ValueError('Exactly one revenue vintage required per origin')
    vintage = deepcopy(matches[0])
    if (not isinstance(vintage.get('source'), str) or not vintage['source'].strip()
            or not isinstance(vintage.get('locators'), dict)
            or any(not isinstance(vintage['locators'].get(k), str)
                   or not vintage['locators'][k].strip()
                   for k in ('populationAndCapacity', 'municipalRegulation', 'settlements'))):
        raise ValueError('Missing national revenue source or locator')
    published = date.fromisoformat(vintage['publicationDate'])
    if published.year != origin or published.month != 12:
        raise ValueError('December vintage from the origin year required')
    if any(vintage[k] != cost_vintage[k] for k in ('originYear', 'publicationDate', 'circular')):
        raise ValueError('Revenue and cost vintage must use the same circular')
    rows = {r['year']: r for r in vintage['rows']}
    if len(rows) != len(vintage['rows']):
        raise ValueError('Duplicate revenue year')
    try:
        vintage['rows'] = [rows[origin+h] for h in range(years+1)]
    except KeyError as error:
        raise ValueError('Missing revenue year; no extrapolation') from error
    if [r['year'] for r in vintage['rows'][1:]] != [r['year'] for r in cost_vintage['rows']]:
        raise ValueError('Revenue and cost horizons must match')
    for h, row in enumerate(vintage['rows']):
        for key in ('nationalNovemberPopulation', 'skrMeanTaxCapacity'):
            finite(row[key], key, minimum=1)
        finite(row['municipalRegulationPerCapita'], 'regulation per capita')
        if row['populationStatus'] != ('observed' if h == 0 else 'forecast'):
            raise ValueError('Incorrect national population status')
        for key in ('governmentMeanTaxCapacity', 'currentYearSettlementPerCapita'):
            if h > 1 and row[key] is not None:
                raise ValueError('Later administrative inputs are absent in the declared circulars')
            if row[key] is None:
                if h <= 1:
                    raise ValueError('Missing first-year administrative input')
            else:
                finite(row[key], key, minimum=1 if key == 'governmentMeanTaxCapacity' else None)
        row['novemberReferenceDate'] = f'{row["year"]}-11-01'
        row['fiscalPopulationReferenceDate'] = f'{row["year"]-1}-11-01'
    finite(vintage['priorYearSettlementRevisionPerCapita'], 'prior settlement revision')
    vintage['role'] = 'reconciled_sources_not_complete_forecast'
    return vintage


def november_count(record, year):
    if (record.get('municipality') != '0583'
            or record.get('referenceDate') != f'{year}-11-01'
            or record.get('unit') != 'persons'):
        raise ValueError('Explicit Motala November population reference required')
    return finite(record['value'], 'November population', minimum=1)


def preliminary_tax(upscaled_tax_base, tax_rate):
    return (finite(upscaled_tax_base, 'upscaled tax base', minimum=0)
            * finite(tax_rate, 'municipal tax rate fraction', minimum=0, maximum=1))


def recognised_tax(year, upscaled_tax_base, tax_rate, settlement_per_capita,
                   prior_revision_per_capita, previous_november, earlier_november):
    """Separate bases for current settlement and prior-year revision."""
    preliminary = preliminary_tax(upscaled_tax_base, tax_rate)
    settlement = (finite(settlement_per_capita, 'settlement')
                  * november_count(previous_november, year-1) / 1e6)
    revision = (finite(prior_revision_per_capita, 'prior revision')
                * november_count(earlier_november, year-2) / 1e6)
    return {'preliminaryTax': preliminary, 'estimatedCurrentYearSettlement': settlement,
            'priorYearSettlementDifference': revision, 'tax': preliminary+settlement+revision}


def income_equalisation(year, upscaled_tax_base, mean_tax_capacity, previous_november,
                        *, recipient_rate, payer_rate, guarantee=1.15):
    """Administrative income equalisation; own municipal tax rate is not an input."""
    population = november_count(previous_november, year-1)
    base = finite(upscaled_tax_base, 'upscaled tax base', minimum=0)
    capacity = finite(mean_tax_capacity, 'mean tax capacity', minimum=1)
    level = finite(guarantee, 'guarantee', minimum=0)
    positive = finite(recipient_rate, 'recipient rate fraction', minimum=0, maximum=1)
    negative = finite(payer_rate, 'payer rate fraction', minimum=0, maximum=1)
    gap = level*capacity*population/1e6-base
    return gap*(positive if gap >= 0 else negative)


def regulation_grant(year, per_capita, previous_november):
    return (finite(per_capita, 'municipal regulation per capita')
            * november_count(previous_november, year-1) / 1e6)
