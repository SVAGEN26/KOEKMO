"""Dated annual cost forecasts. No fitted weights or outcome-dependent selection."""
from copy import deepcopy
from datetime import date
import math

from . import dynamics


def select_vintage(data, origin, years):
    matches = [v for v in data['vintages'] if v['originYear'] == origin]
    if len(matches) != 1:
        raise ValueError('Exactly one declared December vintage required per origin')
    v = deepcopy(matches[0])
    published = date.fromisoformat(v['publicationDate'])
    if published.year != origin or published.month != 12:
        raise ValueError('Macro forecast must be a December vintage from the origin year')
    rows = {r['year']: r for r in v['rows']}
    if len(rows) != len(v['rows']) or not 1 <= years <= len(rows):
        raise ValueError('Duplicate or insufficient forecast years')
    try:
        v['rows'] = [rows[origin+h] for h in range(1, years+1)]
    except KeyError as e:
        raise ValueError('Missing forecast horizon; no silent extrapolation') from e
    for row in v['rows']:
        for key in ('laborPercent', 'otherPercent'):
            value = row[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value <= -100:
                raise ValueError('Invalid annual cost growth')
    v['macroCutoff'] = f'{origin}-12-31'
    v['openingAccountsAvailableAtMacroCutoff'] = False
    return v


def factors(vintage, key):
    level, result = 1., []
    for row in vintage['rows']:
        level *= 1+row[key]/100
        result.append(level)
    return result


def scenario_source(parameters, vintage):
    # Reuse the public data-only validator before constructing any Modelica code.
    dynamics.scenario_source(parameters=parameters)
    if any(parameters.get(k) != 0 for k in ('wageGrowth', 'priceGrowth', 'pensionGrowth')):
        raise ValueError('Full PKV path requires zero internal wage, price and pension growth')
    modifiers = ','.join(k+'='+dynamics.literal(v) for k, v in parameters.items())
    labor = dynamics.literal(factors(vintage, 'laborPercent'))
    other = dynamics.literal(factors(vintage, 'otherPercent'))
    return f'''within ;
model Scenario
  parameter Real laborFactors[{len(vintage['rows'])}]={labor};
  parameter Real otherFactors[{len(vintage['rows'])}]={other};
  Integer costYear=min(size(laborFactors,1),integer(floor(time/MotalaDynamics.yearSeconds))+1);
  MotalaDynamics.Continuous plant({modifiers},
    laborPriceMultiplier=laborFactors[costYear],otherPriceMultiplier=otherFactors[costYear],
    pensionExpense=plant.pension0*laborFactors[costYear]);
end Scenario;
'''


def accounting_projection(row, vintage, parameters):
    """Same macro paths without M2 quantities, capital or financing dynamics."""
    result = []
    for h, (labor, other) in enumerate(zip(factors(vintage, 'laborPercent'), factors(vintage, 'otherPercent')), 1):
        revenue = row['operatingRevenue']*(1+parameters['feeGrowth'])**h
        tax = row['tax']*(1+parameters['taxBaseGrowth'])**h
        grants = row['grants']*(1+parameters['grantGrowth'])**h
        personnel = (row['payroll']+row['pension'])*labor
        cost = personnel+row['otherExpense']*other-revenue+row['depreciation']+row['costRounding']
        finance = row['financialIncome']-row['financialExpense']
        result.append({'year': row['year']+h, 'result': tax+grants-cost+finance,
            'taxAndGrants': tax+grants, 'netCost': cost, 'financeNet': finance,
            'population': row['population'], 'personnel': personnel,
            'otherOperatingExpense': row['otherExpense']*other, 'operatingRevenue': revenue,
            'depreciation': row['depreciation'], 'tax': tax, 'grants': grants,
            'interest': row['interest']})
    return result
