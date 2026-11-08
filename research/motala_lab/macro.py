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


def scenario_source(parameters, vintage, *, tax_vintage=None, normalized_path=None):
    # Reuse the public data-only validator before constructing any Modelica code.
    dynamics.scenario_source(parameters=parameters)
    if any(parameters.get(k) != 0 for k in ('wageGrowth', 'priceGrowth', 'pensionGrowth')):
        raise ValueError('Full PKV path requires zero internal wage, price and pension growth')
    modifiers = ','.join(k+'='+dynamics.literal(v) for k, v in parameters.items())
    labor = dynamics.literal(factors(vintage, 'laborPercent'))
    other = dynamics.literal(factors(vintage, 'otherPercent'))
    tax_declaration = tax_binding = extra_equations = ''
    if tax_vintage is not None and normalized_path is not None:
        raise ValueError('Tax-only and normalized revenue are separate experiments')
    if tax_vintage is not None:
        if parameters.get('useExternalTax') is not True or parameters.get('useExternalRevenue', False):
            raise ValueError('Tax-only diagnostic requires independent external tax and internal grants')
        if [r['year'] for r in vintage['rows']] != [r['year'] for r in tax_vintage['rows']]:
            raise ValueError('Tax and cost horizons must match')
        tax_factors = dynamics.literal(factors(tax_vintage, 'taxBasePercent'))
        tax_declaration = f'  parameter Real taxFactors[{len(vintage["rows"])}]={tax_factors};\n'
        tax_binding = ',externalTax=plant.tax0*taxFactors[costYear]'
    if normalized_path is not None:
        if (parameters.get('useExternalRevenue') is not True or parameters.get('useExternalTax', False)
                or parameters.get('taxRate', parameters['taxRate0']) != parameters['taxRate0']):
            raise ValueError('Normalized revenue requires external revenue at the reference tax rate')
        if any(normalized_path[key] != parameters[param] for key, param in
               (('taxAnchor0', 'tax0'), ('grantAnchor0', 'grants0'))):
            raise ValueError('Normalized revenue anchors differ from the actual note policy')
        if [r['year'] for r in normalized_path['rows']] != [r['year'] for r in vintage['rows']]:
            raise ValueError('Normalized revenue and cost horizons must match')
        pi = dynamics.literal([r['factor'] for r in normalized_path['rows']])
        p0 = dynamics.literal(normalized_path['preliminaryTax0'])
        i0 = dynamics.literal(normalized_path['incomeEqualisation0'])
        settlement = normalized_path.get('settlementForecast')
        regulation = normalized_path.get('regulationForecast')
        grant_removed = i0
        if regulation is not None:
            if settlement is None or [r['year'] for r in regulation['rows']] != [r['year'] for r in vintage['rows']]:
                raise ValueError('Regulation requires matching v7 settlement and cost horizons')
            grant_removed = dynamics.literal(normalized_path['incomeEqualisation0']
                +regulation['regulationGrant0']+regulation['transferredRefugeeGrant0'])
        inherited_tax = '0' if settlement is not None else f'(1-{p0}/plant.tax0)*plant.revenue.referenceTax'
        tax_declaration = f'''  parameter Real piFactors[{len(vintage['rows'])}]={pi};
  Real normalizedPreliminaryTax={p0}*piFactors[costYear];
  Real normalizedIncomeEqualisation={i0}*piFactors[costYear];
  Real inheritedTax={inherited_tax};
  Real inheritedGrants=(1-{grant_removed}/plant.grants0)*plant.revenue.referenceGrants;
  Real cumulativeNormalizedPreliminaryTax(start=0,fixed=true);
  Real cumulativeNormalizedIncomeEqualisation(start=0,fixed=true);
  Real cumulativeInheritedTax(start=0,fixed=true);
  Real cumulativeInheritedGrants(start=0,fixed=true);
'''
        tax_binding = (',externalTax=inheritedTax+normalizedPreliminaryTax'
                       ',externalGrants=inheritedGrants+normalizedIncomeEqualisation')
        if settlement is not None:
            if [r['year'] for r in settlement['rows']] != [r['year'] for r in vintage['rows']]:
                raise ValueError('Settlement and cost horizons must match')
            values = dynamics.literal([r['settlementAndRevision'] for r in settlement['rows']])
            tax_declaration += f'  parameter Real settlementAmounts[{len(vintage["rows"])}]={values};\n'
            tax_binding += ',externalTaxSettlement=settlementAmounts[costYear]'
        extra_equations = '''equation
  der(cumulativeNormalizedPreliminaryTax)=normalizedPreliminaryTax/MotalaDynamics.yearSeconds;
  der(cumulativeNormalizedIncomeEqualisation)=normalizedIncomeEqualisation/MotalaDynamics.yearSeconds;
  der(cumulativeInheritedTax)=inheritedTax/MotalaDynamics.yearSeconds;
  der(cumulativeInheritedGrants)=inheritedGrants/MotalaDynamics.yearSeconds;
'''
        if regulation is not None:
            values = dynamics.literal([r['regulationGrant'] for r in regulation['rows']])
            r0 = dynamics.literal(regulation['regulationGrant0'])
            f0 = dynamics.literal(regulation['transferredRefugeeGrant0'])
            tax_declaration += f'''  parameter Real regulationAmounts[{len(vintage['rows'])}]={values};
  Real regulationGrant=regulationAmounts[costYear];
  Real allocatedParentRegulationGrant={r0}/plant.grants0*plant.revenue.referenceGrants;
  Real allocatedParentRefugeeWelfareGrant={f0}/plant.grants0*plant.revenue.referenceGrants;
  Real cumulativeRegulationGrant(start=0,fixed=true);
  Real cumulativeAllocatedParentRegulationGrant(start=0,fixed=true);
  Real cumulativeAllocatedParentRefugeeWelfareGrant(start=0,fixed=true);
'''
            tax_binding = tax_binding.replace('externalGrants=inheritedGrants+normalizedIncomeEqualisation',
                'externalGrants=inheritedGrants+normalizedIncomeEqualisation+regulationGrant')
            extra_equations += '''  der(cumulativeRegulationGrant)=regulationGrant/MotalaDynamics.yearSeconds;
  der(cumulativeAllocatedParentRegulationGrant)=allocatedParentRegulationGrant/MotalaDynamics.yearSeconds;
  der(cumulativeAllocatedParentRefugeeWelfareGrant)=allocatedParentRefugeeWelfareGrant/MotalaDynamics.yearSeconds;
'''
    return f'''within ;
model Scenario
  parameter Real laborFactors[{len(vintage['rows'])}]={labor};
  parameter Real otherFactors[{len(vintage['rows'])}]={other};
{tax_declaration}\
  Integer costYear=min(size(laborFactors,1),integer(floor(time/MotalaDynamics.yearSeconds))+1);
  MotalaDynamics.Continuous plant({modifiers},
    laborPriceMultiplier=laborFactors[costYear],otherPriceMultiplier=otherFactors[costYear],
    pensionExpense=plant.pension0*laborFactors[costYear]{tax_binding});
{extra_equations}\
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
