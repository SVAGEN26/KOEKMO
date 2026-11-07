"""Period-ordered native M2 replay. Explicitly retrospective development evidence.

No optimizer, target-dependent parameter selection or future ledger access in
the forecasting function. Unknown WIP requires an explicit scenario policy.
"""
import argparse
from copy import deepcopy
import hashlib
import html
import json
import math
from pathlib import Path
import shutil
import subprocess
from statistics import mean

from . import dynamics, macro, noted_events, tax_forecasts, revenue_bridge, normalized_revenue, settlement_forecasts, regulation_forecasts
from .data import local_observations, validate
from .fiscal import baseline
from .model import forecast

ROOT = dynamics.ROOT
METRICS = ('result', 'taxAndGrants', 'netCost', 'financeNet', 'population')
COMPONENTS = ('tax', 'grants', 'payroll', 'pensionExpense', 'otherOperatingExpense',
              'operatingRevenue', 'depreciation', 'interest', 'personnel')


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def load_ledgers(path=None):
    data = json.loads(Path(path or ROOT/'data/annual-ledgers.json').read_text())
    if data['evidenceClass'] != 'retrospective_development':
        raise ValueError('This runner only supports explicitly retrospective development evidence')
    seen = set()
    for r in data['rows']:
        if r['year'] in seen or r['scope'] != 'kommunen' or r['moneyUnit'] != 'mnkr':
            raise ValueError('Duplicate year or incorrect scope/unit')
        seen.add(r['year'])
        required = ('population', 'births', 'deaths', 'tax', 'grants', 'payroll', 'pension',
                    'otherExpense', 'grossExpense', 'operatingRevenue', 'depreciation', 'interest',
                    'financialIncome', 'financialExpense', 'tangibleIncludingWIP', 'cash', 'debt', 'investment')
        if any(type(r.get(k)) not in (int, float) or not math.isfinite(r[k]) or r[k] < 0 for k in required):
            raise ValueError('Missing or invalid observed opening ledger at ' + str(r['year']))
        if len(r['cohortsReported']) != 5 or min(r['cohortsReported']) <= 0:
            raise ValueError('Five positive cohorts required')
        if r['sourceId'] not in data['sources'] or r['stockSourceId'] not in data['sources']:
            raise ValueError('Missing source/version')
        if r['workInProgress'] is not None and not 0 <= r['workInProgress'] < r['tangibleIncludingWIP']:
            raise ValueError('Invalid WIP split')
        residuals = [r['grossExpense']-r['payroll']-r['pension']-r['otherExpense'],
            r['netCost']-r['grossExpense']+r['operatingRevenue']-r['depreciation']-r['costRounding'],
            r['result']-r['tax']-r['grants']+r['netCost']-r['financialIncome']+r['financialExpense']-r['resultRounding']]
        if max(map(abs, residuals)) > 1e-6:
            raise ValueError('Unexplained ledger residual at ' + str(r['year']))
    return data


def opening_inputs(data, origin, protocol, *, missing_wip_fraction=None, event_data=None, event_policy=None):
    """Select and return only origin-period inputs; outcomes never enter here."""
    matches = [r for r in data['rows'] if r['year'] == origin]
    if len(matches) != 1:
        raise ValueError('Exactly one opening ledger required')
    r = deepcopy(matches[0])
    reported = deepcopy(r)
    note_audit = None
    if event_data is not None:
        r, note_audit = noted_events.prepare(r, event_data, event_policy)
    elif event_policy is not None:
        raise ValueError('Note policy requires reviewed note data')
    wip = r['workInProgress']
    assumed_wip = wip is None
    if assumed_wip:
        if missing_wip_fraction is None:
            raise ValueError('Missing WIP requires an explicit scenario assumption')
        if not 0 <= missing_wip_fraction < 1:
            raise ValueError('Invalid WIP scenario fraction')
        wip = missing_wip_fraction*r['tangibleIncludingWIP']
    p = [x*r['population']/sum(r['cohortsReported']) for x in r['cohortsReported']]
    deaths = [.0004, .0001, .0002, .0018]
    senior_rate = (r['deaths']-sum(a*b for a, b in zip(deaths, p)))/p[4]
    if senior_rate < 0 or r['debt'] <= 0:
        raise ValueError('Demographic or interest calibration not supported for this opening row')
    params = deepcopy(protocol['parameters'])
    params.update(p0=p, births0=r['births'], deathRates=deaths+[senior_rate],
        migration0=[r['netMigration']*x for x in [.15, .12, .03, .65, .05]],
        tax0=r['tax'], grants0=r['grants'], payroll0=r['payroll'], pension0=r['pension'],
        otherExpense0=r['otherExpense'], operatingRevenue0=r['operatingRevenue'],
        costRounding=r['costRounding'], assets0=r['tangibleIncludingWIP']-wip,
        workInProgress0=wip, depreciation0=r['depreciation'], debt0=r['debt'], cash0=r['cash'],
        financialIncome=r['financialIncome'], otherFinancialExpense=r['financialExpense']-r['interest'],
        investment0=r['investment'], interestRate0=r['interest']/r['debt'], taxRate0=.217)
    audit = {'originYear': origin, 'openingLedger': reported, 'parameters': params,
        'assumedWIP': assumed_wip, 'assumedWIPFraction': missing_wip_fraction if assumed_wip else None,
        'sourceRevisions': any(int(value) > origin for key, value in r.items()
                               if key == 'sourceId' or key.endswith('SourceId')),
        'informationCutoff': None, 'forecastDate': None,
        'warning': 'Period-ordered revised data; historical publication availability is not established.'}
    if note_audit is not None:
        audit['noteSeparation'] = note_audit
        audit['sourceRevisions'] |= note_audit['sourceRevisions']
    return params, audit


def aggregate_observations(data, *, older=None):
    """Same observed totals for M1/baselines/M2 scoring, with earlier M1 history."""
    old = local_observations()
    first = min(r['year'] for r in data['rows'])
    rows = [r for r in old['rows'] if r['year'] < first]
    if older:
        for r in older['rows']:
            if any(existing['year'] == r['year'] for existing in rows):
                raise ValueError('Older source must not replace an existing selected version')
            rows.append({'municipality': '0583', 'year': r['year'], 'population': r['reportedTotal'],
                'taxAndGrants': r['result']+r['netCost']-r['financeNet'], 'result': r['result'],
                'netCost': r['netCost'], 'financeNet': r['financeNet'], 'source': older['source'],
                'sourceRelease': older['sourceRelease'], 'vintage': older['vintage'],
                'retrievedAt': older['retrievedAt']})
    for r in sorted(data['rows'], key=lambda r: r['year']):
        rows.append({'municipality': '0583', 'year': r['year'], 'population': r['population'],
            'cohorts': [x*r['population']/sum(r['cohortsReported']) for x in r['cohortsReported']],
            'births': r['births'], 'deaths': r['deaths'], 'netMigration': r['netMigration'],
            'taxAndGrants': r['tax']+r['grants'], 'netCost': r['netCost'],
            'financeNet': r['financialIncome']-r['financialExpense'], 'result': r['result'],
            'accountingAdjustment': r['resultRounding'], 'source': data['sources'][r['sourceId']]['url'],
            'sourceRelease': None, 'retrievedAt': data['retrievedAt'],
            'vintage': 'annual-ledgers-source-'+r['sourceId']})
    return validate({**old, 'rows': sorted(rows, key=lambda r: r['year'])})


def predict_origin(data, origin, years, protocol, directory, *, legacy=False, missing_wip_fraction=None, source_root=None, macro_data=None, event_data=None, event_policy=None, tax_data=None, normalized_inputs=None, settlement_forecast=False, regulation_forecast=False):
    if event_data is not None and (legacy or macro_data is None):
        raise ValueError('Note experiment requires the current PKV candidate')
    if tax_data is not None and (legacy or macro_data is None or event_data is None):
        raise ValueError('Tax diagnostic requires current PKV and the fixed note experiment')
    if normalized_inputs is not None and (legacy or macro_data is None or event_data is None or tax_data is not None):
        raise ValueError('Normalized revenue requires the PKV note experiment without tax-only inputs')
    if type(settlement_forecast) is not bool or (settlement_forecast and normalized_inputs is None):
        raise ValueError('Settlement forecast requires normalized revenue inputs')
    if type(regulation_forecast) is not bool or (regulation_forecast and not settlement_forecast):
        raise ValueError('Regulation forecast requires the v7 settlement forecast')
    params, audit = opening_inputs(data, origin, protocol, missing_wip_fraction=missing_wip_fraction,
        event_data=event_data, event_policy=event_policy)
    if not legacy:
        params['annualFlowAnchoring'] = True
    package = Path(source_root or ROOT)/('reference/dynamics-v2/MotalaDynamics/package.mo' if legacy else 'MotalaDynamics/package.mo')
    if macro_data is not None:
        if legacy:
            raise ValueError('Frozen legacy model does not support external cost indices')
        vintage = macro.select_vintage(macro_data, origin, years)
        params.update(wageGrowth=0, priceGrowth=0, pensionGrowth=0)
        audit['macroForecast'] = vintage
        audit['personnelAllocation'] = 'Both partitions share PKV labor index; only combined personnel is a forecast target.'
        tax_vintage = None
        if tax_data is not None:
            tax_vintage = tax_forecasts.select_vintage(tax_data, origin, years, vintage)
            params.update(useExternalTax=True, useExternalRevenue=False)
            audit['taxDiagnostic'] = tax_vintage
        normalized_path = None
        if normalized_inputs is not None:
            components, national = normalized_inputs
            national_vintage = revenue_bridge.select_vintage(national, origin, years, vintage)
            normalized_path = normalized_revenue.prepare(components, audit['openingLedger'], params, national_vintage)
            if settlement_forecast:
                normalized_path = settlement_forecasts.prepare(normalized_path, audit['openingLedger'])
            if regulation_forecast:
                normalized_path = regulation_forecasts.prepare(normalized_path, audit['openingLedger'], components)
            params.update(useExternalRevenue=True, useExternalTax=False)
            audit['normalizedRevenue'] = normalized_path
        source = macro.scenario_source(params, vintage, tax_vintage=tax_vintage, normalized_path=normalized_path)
    else:
        source = dynamics.scenario_source(parameters=params)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    audit['inputHash'] = digest(audit)
    audit['legacy'] = legacy
    dump(directory/'inputs.json', audit)
    rows = dynamics.simulate(source, years, directory/'native', package=package)
    annual = dynamics.annual_rows(rows, years, base_year=origin)
    if normalized_inputs is not None:
        for index, row in enumerate(annual):
            before, now = dynamics.at_year(rows, index), dynamics.at_year(rows, index+1)
            for name, key in (('preliminaryTax', 'cumulativeNormalizedPreliminaryTax'),
                              ('incomeEqualisation', 'cumulativeNormalizedIncomeEqualisation'),
                              ('inheritedTax', 'cumulativeInheritedTax'),
                              ('inheritedGrants', 'cumulativeInheritedGrants')):
                row[name] = now[key]-before[key]
            row['preliminaryTaxAndEqualisation'] = row['preliminaryTax']+row['incomeEqualisation']
            if settlement_forecast:
                row.update(currentYearSettlement=row['taxSettlement'], priorYearSettlementRevision=0.,
                           settlementAndRevision=row['taxSettlement'])
            if regulation_forecast:
                for name in ('regulationGrant', 'allocatedParentRegulationGrant', 'allocatedParentRefugeeWelfareGrant'):
                    key = 'cumulative'+name[0].upper()+name[1:]
                    row[name] = now[key]-before[key]
                row.update(refugeeWelfareGrant=0., regulationAndTransferredGrant=row['regulationGrant'],
                           remainingGrants=row['inheritedGrants'])
            if max(abs(row['tax']-row['preliminaryTax']-row['inheritedTax']-row['taxSettlement']),
                   abs(row['grants']-row['incomeEqualisation']-row['inheritedGrants']-row.get('regulationGrant', 0))) > 1e-4:
                raise RuntimeError('Normalized revenue component identity failed')
    for row in annual:
        row['taxAndGrants'] = row['tax']+row['grants']
        row['netCost'] = (row['payroll']+row['pensionExpense']+row['otherOperatingExpense']
            -row['operatingRevenue']+row['depreciation']+row['disposalLoss']+row['transitionExpense']
            +row.get('extraExpense', 0)+params['costRounding'])
        row['financeNet'] = params['financialIncome']-params['otherFinancialExpense']-row['interest']
        row['personnel'] = row['payroll']+row['pensionExpense']
        if abs(row['result']-row['taxAndGrants']+row['netCost']-row['financeNet']) > 1e-4:
            raise RuntimeError('Integrated result identity failed')
    dump(directory/'annual.json', annual)
    # Check that native initialized values really reflect the chosen historical ledger.
    resolved = json.loads((directory/'native/resolved-parameters.json').read_text())
    for key in ('tax0', 'grants0', 'payroll0', 'pension0', 'otherExpense0', 'operatingRevenue0',
                'assets0', 'workInProgress0', 'debt0', 'cash0', 'depreciation0', 'investment0'):
        if abs(resolved[key]['value']-params[key]) > 1e-7:
            raise RuntimeError('Native opening differs from historical inputs: '+key)
    return annual, audit


def scores(cases, *, candidate_name='M2'):
    result = []
    for h in sorted({r['horizon'] for r in cases}):
        selected = [r for r in cases if r['horizon'] == h]
        for metric in METRICS:
            names = sorted(set.intersection(*(set(r['predictions']) for r in selected)))
            record = {'horizon': h, 'metric': metric, 'n': len(selected),
                'targetYears': sorted({r['targetYear'] for r in selected}), 'models': {}}
            for name in names:
                errors = [r['predictions'][name][metric]-r['actual'][metric] for r in selected]
                record['models'][name] = {'mae': mean(map(abs, errors)), 'bias': mean(errors),
                    'rmse': math.sqrt(mean(e*e for e in errors))}
            candidate_errors = [abs(r['predictions'][candidate_name][metric]-r['actual'][metric]) for r in selected]
            record['paired'] = {}
            for name in names:
                differences = [c-abs(r['predictions'][name][metric]-r['actual'][metric]) for c, r in zip(candidate_errors, selected)]
                leave_one_out = [mean(d for j, d in enumerate(differences) if j != i)
                                 for i in range(len(selected))] if len(selected) > 1 else []
                record['paired'][name] = {'meanAbsoluteErrorDifference': mean(differences),
                    'leaveOneTargetOutRange': [min(leave_one_out), max(leave_one_out)] if leave_one_out else None,
                    'note': 'Descriptive stability check, not a confidence interval; no refitting.'}
            result.append(record)
    return result


def aggregate_predictions(training, years, *, include_mean=False):
    """Fixed standard baselines, with no choice of window, weights or target year."""
    predictions = {'M1': forecast(training, horizon=years)['rows']}
    for name in ('persistence', 'trend'):
        predictions[name] = [{k: baseline(training, k, h, name)[-1] for k in METRICS}
                             for h in range(1, years+1)]
    if include_mean:
        predictions['historical_mean'] = [{**{k: mean(r[k] for r in training) for k in METRICS},
            'accountingAdjustment': mean(r.get('accountingAdjustment', 0) for r in training)}
                                           for _ in range(years)]
    return predictions


def aggregate_replay(observations, origins, horizons):
    """The larger aggregate-only set is separate from the five native targets."""
    rows = observations['rows']
    actual = {r['year']: r for r in rows}
    cases = []
    for origin in origins:
        if origin not in actual:
            # Otherwise training silently ends at an earlier year and an h-step case is really longer.
            raise ValueError(f'Origin year {origin} is missing from the observations')
        training = [r for r in rows if r['year'] <= origin]
        preds = aggregate_predictions(training, max(horizons), include_mean=True)
        for h in horizons:
            if origin+h in actual:
                cases.append({'originYear': origin, 'targetYear': origin+h, 'horizon': h,
                    'actual': {k: actual[origin+h][k] for k in METRICS},
                    'predictions': {name: p[h-1] for name, p in preds.items()}})
    return {'cases': cases, 'scores': scores(cases, candidate_name='historical_mean'),
        'warning': 'Additional aggregate targets; not additional native M2 validation. Mean is an explicit simple comparator, not a fitted mechanism or independently validated winner.'}


def descriptive_budgets(cases, benchmark):
    """Context only: never a model input or a matched-date superiority score."""
    actuals = {r['targetYear']: r['actual']['result'] for r in cases if r['horizon'] == 1}
    rows = []
    for b in benchmark['budgets']:
        if b['targetYear'] in actuals:
            rows.append({**b, 'actual': actuals[b['targetYear']], 'error': b['value']-actuals[b['targetYear']]})
    return {'role': 'descriptive_benchmark_only', 'matchedInformationDates': False,
        'warning': 'Municipal budgets are plans, partly reproduced retrospectively. Original publication dates and common information cutoffs are not established. These are not independent SKR outputs.',
        'rows': rows, 'mae': mean(abs(r['error']) for r in rows) if rows else None,
        'sources': benchmark['sources']}


def component_scores(cases):
    """Score available ledger components on identical targets per horizon."""
    result = []
    for horizon in sorted({r['horizon'] for r in cases}):
        selected = [r for r in cases if r['horizon'] == horizon]
        for metric in COMPONENTS:
            models = {}
            for name in sorted(set.intersection(*(set(r['predictions']) for r in selected))):
                if not all(metric in r['predictions'][name] for r in selected):
                    continue
                # PKV forecasts only the combined personnel expense.
                if ('PKV' in name or name.startswith('PKV-')) and metric in ('payroll', 'pensionExpense'):
                    continue
                errors = [r['predictions'][name][metric]-r['actualComponents'][metric] for r in selected]
                models[name] = {'mae': mean(map(abs, errors)), 'bias': mean(errors),
                    'rmse': math.sqrt(mean(e*e for e in errors))}
            result.append({'horizon': horizon, 'metric': metric, 'n': len(selected), 'models': models})
    return result


def evaluate(data, protocol, directory, *, source_root=None, observations=None, macro_data=None, event_data=None, tax_data=None):
    directory = Path(directory)
    observed = {r['year']: r for r in data['rows']}
    aggregate = (observations or aggregate_observations(data))['rows']
    actuals = {r['year']: r for r in aggregate}
    cases, sensitivity = [], []
    note_audits = []
    if event_data is not None and (macro_data is None or protocol.get('eventScenarios') != list(noted_events.POLICIES)):
        raise ValueError('Both fixed note scenarios and PKV inputs are required')
    if tax_data is not None and event_data is None:
        raise ValueError('Tax diagnostic requires both fixed note scenarios')
    for origin in protocol['originYears']:
        years = min(max(protocol['horizons']), max(observed)-origin)
        if years < 1:
            continue
        training = [r for r in aggregate if r['year'] <= origin]
        comparators = aggregate_predictions(training, years,
            include_mean='historical_mean' in protocol.get('additionalBaselines', []))
        native, audit = predict_origin(data, origin, years, protocol, directory/str(origin)/'M2',
            missing_wip_fraction=protocol['missingWIP']['nominal'], source_root=source_root)
        legacy, _ = predict_origin(data, origin, years, protocol, directory/str(origin)/'M2-v2', legacy=True,
            missing_wip_fraction=protocol['missingWIP']['nominal'], source_root=source_root)
        native_names = ['M2', 'M2-v2']
        if macro_data is not None:
            pkv, _ = predict_origin(data, origin, years, protocol, directory/str(origin)/'M2-PKV',
                missing_wip_fraction=protocol['missingWIP']['nominal'], source_root=source_root, macro_data=macro_data)
            comparators['M2-PKV'] = pkv
            comparators['PKV-accounting'] = macro.accounting_projection(observed[origin],
                macro.select_vintage(macro_data, origin, years), protocol['parameters'])
            native_names.append('M2-PKV')
        if event_data is not None:
            for policy in protocol['eventScenarios']:
                name = 'M2-PKV-'+policy
                adjusted, adjusted_audit = predict_origin(data, origin, years, protocol,
                    directory/str(origin)/name, missing_wip_fraction=protocol['missingWIP']['nominal'],
                    source_root=source_root, macro_data=macro_data, event_data=event_data, event_policy=policy)
                comparators[name] = adjusted
                native_names.append(name)
                note_audits.append(adjusted_audit['noteSeparation'])
                recurring, _ = noted_events.prepare(observed[origin], event_data, policy)
                comparators['PKV-accounting-'+policy] = macro.accounting_projection(recurring,
                    macro.select_vintage(macro_data, origin, years), protocol['parameters'])
                if tax_data is not None:
                    tax_name = name+'-tax-only'
                    tax_projection, _ = predict_origin(data, origin, years, protocol,
                        directory/str(origin)/tax_name, missing_wip_fraction=protocol['missingWIP']['nominal'],
                        source_root=source_root, macro_data=macro_data, event_data=event_data,
                        event_policy=policy, tax_data=tax_data)
                    # Tax diagnostic must not change costs, grants or local demography.
                    for before, after in zip(adjusted, tax_projection):
                        for field in ('grants', 'netCost', 'population', 'personnel'):
                            if abs(after[field]-before[field]) > 1e-3:
                                raise RuntimeError('Tax-only diagnostic changed '+field)
                    comparators[tax_name] = tax_projection
                    native_names.append(tax_name)
                    comparators['PKV-accounting-'+policy+'-tax-only'] = tax_forecasts.accounting_projection(
                        comparators['PKV-accounting-'+policy], recurring['tax'],
                        tax_forecasts.select_vintage(tax_data, origin, years,
                            macro.select_vintage(macro_data, origin, years)))
        for h in protocol['horizons']:
            target = origin+h
            if h > years or target not in observed:
                continue
            predictions = {'M2': native[h-1], 'M2-v2': legacy[h-1],
                           **{name: p[h-1] for name, p in comparators.items()}}
            raw = observed[target]
            component_actuals = {k: raw[{'pensionExpense': 'pension', 'otherOperatingExpense': 'otherExpense'}.get(k, k)]
                                 for k in COMPONENTS if k != 'personnel'}
            component_actuals['personnel'] = raw['payroll']+raw['pension']
            cases.append({'originYear': origin, 'targetYear': target, 'horizon': h,
                'assumedOpeningWIP': audit['assumedWIP'], 'revisedOpeningData': audit['sourceRevisions'],
                'actual': {k: actuals[target][k] for k in METRICS}, 'actualComponents': component_actuals,
                'predictions': predictions,
                'componentErrors': {name: {k: predictions[name][k]-component_actuals[k] for k in COMPONENTS}
                                    for name in native_names}})
        if audit['assumedWIP']:
            for fraction in protocol['missingWIP']['sensitivityFractionsOfTotalTangibleAssets']:
                alternative, _ = predict_origin(data, origin, years, protocol,
                    directory/str(origin)/f'WIP-{fraction}', missing_wip_fraction=fraction, source_root=source_root)
                sensitivity.extend({'originYear': origin, 'targetYear': r['year'], 'fraction': fraction,
                    'model': 'M2', 'result': r['result'], 'differenceFromNominal': r['result']-native[i]['result']}
                    for i, r in enumerate(alternative))
                if macro_data is not None:
                    alternative, _ = predict_origin(data, origin, years, protocol,
                        directory/str(origin)/f'PKV-WIP-{fraction}', missing_wip_fraction=fraction,
                        source_root=source_root, macro_data=macro_data)
                    sensitivity.extend({'originYear': origin, 'targetYear': r['year'], 'fraction': fraction,
                        'model': 'M2-PKV', 'result': r['result'], 'differenceFromNominal': r['result']-pkv[i]['result']}
                        for i, r in enumerate(alternative))
                if event_data is not None:
                    for policy in protocol['eventScenarios']:
                        name = 'M2-PKV-'+policy
                        alternative, _ = predict_origin(data, origin, years, protocol,
                            directory/str(origin)/f'{name}-WIP-{fraction}', missing_wip_fraction=fraction,
                            source_root=source_root, macro_data=macro_data, event_data=event_data, event_policy=policy)
                        sensitivity.extend({'originYear': origin, 'targetYear': r['year'], 'fraction': fraction,
                            'model': name, 'result': r['result'],
                            'differenceFromNominal': r['result']-comparators[name][i]['result']}
                            for i, r in enumerate(alternative))
                        if tax_data is not None:
                            tax_name = name+'-tax-only'
                            tax_alternative, _ = predict_origin(data, origin, years, protocol,
                                directory/str(origin)/f'{tax_name}-WIP-{fraction}', missing_wip_fraction=fraction,
                                source_root=source_root, macro_data=macro_data, event_data=event_data,
                                event_policy=policy, tax_data=tax_data)
                            sensitivity.extend({'originYear': origin, 'targetYear': r['year'], 'fraction': fraction,
                                'model': tax_name, 'result': r['result'],
                                'differenceFromNominal': r['result']-comparators[tax_name][i]['result']}
                                for i, r in enumerate(tax_alternative))
    known = [r for r in cases if not r['assumedOpeningWIP']]
    original = [r for r in known if not r['revisedOpeningData']]
    candidate = 'M2-PKV-costbase' if event_data is not None else ('M2-PKV' if macro_data is not None else 'M2')
    return {'evidenceClass': data['evidenceClass'], 'protocolHash': digest(protocol), 'candidate': candidate,
        'forecastSuperiorityProven': False, 'cases': cases, 'scores': scores(cases, candidate_name=candidate),
        'componentScores': component_scores(cases),
        'noteSeparation': note_audits,
        'knownWIPScores': scores(known, candidate_name=candidate) if known else [],
        'sameReportYearKnownWIPScores': scores(original, candidate_name=candidate) if original else [],
        'wipSensitivity': sensitivity,
        'limitations': [
            'Only five one-year development outcomes; no blind final test or verified publication vintages.',
            '2020/2021 WIP missing: nominal zero and 10/20 percent alternatives are scenarios, not data.',
            '2023 capital split uses a later revised report; not historically available at origin.',
            'Gross payroll/pension classification changes; combined personnel is the more comparable component.',
            'Fixed price/wage/tax assumptions omit historical macro shocks, policy decisions and pension forecasts.',
            'Opening physical capacity and staffing are inferred; sector shares are equal illustrative shares.',
            'Cash/debt accounting omits working capital, asset sales and some non-cash adjustments; no validated cash forecast.',
            'Native model does not fit any parameter to these outcomes. M1 selection remains inside each chronological fold.',
            'Several origins predicting the same year are not additional independent outcomes.'
        ]}


def write_report(directory, result):
    esc = html.escape
    def table(headers, rows):
        return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+\
            '</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(f'{v:.2f}' if isinstance(v, float) else str(v))+'</td>'
            for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
    metric_names = {'result': 'Resultat', 'taxAndGrants': 'Skatt och bidrag', 'netCost': 'Nettokostnad',
                    'financeNet': 'Finansnetto', 'population': 'Befolkning'}
    summaries = []
    for s in result['scores']:
        for name, values in s['models'].items():
            summaries.append([s['horizon'], metric_names[s['metric']], s['n'], name,
                              values['mae'], values['bias'], values['rmse']])
    annual = [r for r in result['cases'] if r['horizon'] == 1]
    model_names = list(annual[0]['predictions'])
    predictions = [[r['targetYear'], r['actual']['result']]+[r['predictions'][n]['result'] for n in model_names] for r in annual]
    components = [[r['targetYear'], name, k, r['actualComponents'][k], r['predictions'][name][k],
                   r['componentErrors'][name][k]] for r in annual
                  for name in r['componentErrors'] if name != 'M2-v2' for k in COMPONENTS
                  if not name.startswith('M2-PKV') or k not in ('payroll', 'pensionExpense')]
    subsets = []
    for label, key in [('Alla scenariostarter', 'scores'), ('Känd WIP', 'knownWIPScores'),
                       ('Känd WIP, samma rapportår', 'sameReportYearKnownWIPScores')]:
        for s in result[key]:
            if s['horizon'] == 1 and s['metric'] == 'result':
                subsets.append([label, str(s['targetYears']), s['n']]+[s['models'][n]['mae'] for n in model_names])
    content = '''<!doctype html><html lang="sv"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Historisk prövning av Motala Dynamics</title><style>body{font:16px system-ui;max-width:1150px;margin:35px auto;padding:0 20px;color:#142630;background:#fafbfc}h1,h2{line-height:1.2}.note{background:#fff0cf;padding:18px;border-left:4px solid #a06500}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;margin:15px 0 30px}th,td{padding:9px;border-bottom:1px solid #cbd4db;text-align:right}th{background:#e5edf2}td:first-child,th:first-child{text-align:left}a{color:#164f86}li{margin:8px 0}</style>
<h1>Historisk prövning av Motala Dynamics</h1>
<p class="note"><b>Utvecklingsevidens, inte en blind prognosvalidering.</b> Prognoserna använder endast observationer för perioder fram till respektive startår. Senare redovisningsversioner, okända publiceringsdatum och antagna byggprojekt gör att detta inte är en rekonstruktion av dåtidens informationsläge. Ingen överlägsen prognosförmåga är fastställd.</p>
<p>Belopp i mnkr, befolkning i personer. Positivt fel betyder överskattning. M2-v2 är den frysta modellen före rättningen av årsflöden. M2 använder samma historiska startvärden och fasta antaganden med analytiskt rättad årsankring. M1 och baslinjerna får samma föregående bokslut. Alla resultat, även ogynnsamma, redovisas.</p>
<p><a href="evaluation.json">Resultat och alla prognoser</a> · <a href="protocol.json">Låst protokoll</a> · <a href="annual-ledgers.json">Bokslut, källor och konflikter</a> · <a href="manifest.json">Filhashar</a></p>'''
    content += '<h2>Ett års prognos för resultatet</h2>'+table(['Målår', 'Utfall']+model_names, predictions)
    if result.get('noteSeparation'):
        content += '<h2>Not 10-kostnadsbas och separat intäktskänslighet</h2><p class="note">Primären M2-PKV-costbase skiljer redan bokförda PFAS-/deponikostnader och försäljningsförlust från den återkommande kostnadsbasen. Inkomstantagandena är oförändrade. Varianten no-repeat antar dessutom ingen upprepning eller ersättande finansiering för notens tillfälliga intäkter. Det är en mekanisk känslighet, inte ett sannolikhetsintervall. Båda reglerna låstes före omräkningen.</p><p>Detta gäller endast uttryckliga poster i not 10, inte fullständig engångsrensning. Exempelvis ligger nedskrivningen 12,1 mnkr år 2022 i not 5 och är kvar i underlaget. Framtida nya engångskostnader antas vara noll i just dessa historiska körningar. Framtida betalningar, omvärderingar och nya beslut är inte därmed noll. Observerade slutstockar och hela bokslutsutfallet lämnas oförändrade.</p>'
        content += table(['Startår', 'Regel', 'Borttagen kostnad', 'Borttagen verksamhetsintäkt', 'Borttaget generellt bidrag', 'Observerat resultat', 'Resultat utan valda poster'],
            [[a['originYear'], a['policy']]+[a['excludedFromRecurringBase'][k] for k in noted_events.FIELDS]
             +[a['reported']['result'], a['recurringBase']['result']] for a in result['noteSeparation']])
        content += '<p>Den sista kolumnen är en bokföringsbrygga för startåret, inte ett justerat utfall i poängsättningen. <a href="motala-noted-events.json">Samtliga poster, källor och motstridiga summetiketter</a>.</p>'
    if 'macroInputs' in result:
        content += '<h2>Daterade kostnadsprognoser från SKR</h2><p class="note">M2-PKV använder decemberprognosen före respektive målår. Hela personalkostnaden, inklusive pension, följer arbetskraftsindex en gång. Löne- och pensionsdelarna är beräkningsposter; endast summan bedöms. PKV-accounting använder samma kostnadsprognoser utan modellens befolknings-, kapital- och finansieringsdynamik. Detta är ingen jämförelse mot SKR:s kommunvisa modell Skatter och bidrag.</p><p>Årsfaktorerna hålls konstanta inom varje år. Boksluten är fortfarande retrospektivt sammanställda; cirkulärens datum gör inte hela övningen till ett test av dåtidens informationsläge.</p>'
        content += table(['Startår', 'Cirkulär', 'Publicerat', 'Målår', 'Arbetskraft %', 'Övriga priser %'],
            [[v['originYear'], v['circular'], v['publicationDate'], r['year'], r['laborPercent'], r['otherPercent']]
             for v in result['macroInputs']['vintages'] for r in v['rows']])
        content += '<p><a href="skr-pkv-vintages.json">Alla källor och definitioner för SKR-underlaget</a></p>'
    if 'taxInputs' in result:
        content += '<h2>Separat känslighet för skatteunderlag</h2><p class="note">Varianterna tax-only är diagnostik, inte en godkänd kommunvis skatteprognos. Skatten följer det faktiskt nominella nationella skatteunderlaget i samma decembercirkulär som kostnaderna. Det antar oförändrad lokal andel och skattesats. Lokal befolkningsutveckling multipliceras inte in igen. Bidragsbanan behåller exakt samma antaganden som före ändringen; även dess förenklade utjämning ligger kvar. Räntekostnader kan däremot förändras genom kassaflöde och skuld.</p><p>Öppningsskatten innehåller slutavräkningar och skatteregler kan kompenseras med statsbidrag. Dessa delar är inte modellerade av denna känslighet. Alla fem starter, båda notvarianterna och samtliga horisonter behålls. M2-PKV-costbase är fortfarande den tidigare kandidaten.</p>'
        content += table(['Startår', 'Cirkulär', 'Publicerat', 'Målår', 'Skatteunderlag %'],
            [[v['originYear'], v['circular'], v['publicationDate'], r['year'], r['taxBasePercent']]
             for v in result['taxInputs']['vintages'] for r in v['rows']])
        content += '<p><a href="skr-tax-vintages.json">Källor och antaganden för skatteexperimentet</a></p>'
        content += '<h2>Skatt och bidrag bedöms var för sig</h2>'+table(['År framåt', 'Komponent', 'n', 'Modell', 'MAE', 'Bias', 'RMSE'],
            [[s['horizon'], s['metric'], s['n'], name, m['mae'], m['bias'], m['rmse']]
             for s in result['componentScores'] if s['metric'] in ('tax', 'grants')
             for name, m in s['models'].items() if 'costbase' in name or 'no-repeat' in name])
    content += '<h2>Hur urvalet påverkar resultatfelet</h2><p>MAE på samma målår inom varje rad. Urvalen är små och överlappar.</p>'+table(['Urval', 'Målår', 'n']+model_names, subsets)
    if 'aggregateReplay' in result:
        content += '<h2>Utökad prövning av enkla alternativ</h2><p class="note">Tillägg efter den första granskningen. 2017 års sammanställning har lagts till. historical_mean betyder det oviktade medelvärdet av alla tidigare observerade år, utan vald fönsterlängd. Detta är fortfarande utvecklingsevidens. Den längre serien kan inte användas för full M2 eftersom bruttobokslut och stockar saknas för de första åren.</p>'
        extra = result['aggregateReplay']
        content += table(['Målår', 'Utfall', 'Historiskt medel', 'M1', 'Oförändrat', 'Trend'],
            [[r['targetYear'], r['actual']['result']]+[r['predictions'][n]['result'] for n in ('historical_mean', 'M1', 'persistence', 'trend')]
             for r in extra['cases'] if r['horizon'] == 1])
        content += table(['År framåt', 'n', 'Modell', 'MAE', 'Bias', 'RMSE'],
            [[s['horizon'], s['n'], n, m['mae'], m['bias'], m['rmse']] for s in extra['scores']
             if s['metric'] == 'result' for n, m in s['models'].items()])
    budget = result.get('municipalBudgetBenchmark')
    if budget:
        content += '<h2>Kommunens budget som jämförelseunderlag</h2><p class="note">Separat beskrivande jämförelse. Budget är en styrande plan och informationsdatumen är inte matchade. Detta är inte en validerad jämförelse med SKR:s modell. Beloppen används inte som indata till M1 eller M2.</p>'
        content += table(['Målår', 'Budget', 'Utfall', 'Fel'], [[r['targetYear'], r['value'], r['actual'], r['error']] for r in budget['rows']])
        content += f'<p>Beskrivande MAE: {budget["mae"]:.2f} mnkr. Källor och osäkra datum finns i evaluation.json.</p>'
    content += '<h2>Fel per komponent, ett år</h2><p>Personalkostnad och pension har omklassificerats. Summan personnel är därför mer jämförbar än de enskilda delarna. Avskrivning 2022 inkluderar nedskrivning 12,1. Alla ursprungsdefinitioner sparas i underlaget.</p>'+table(['Målår', 'Modell', 'Komponent', 'Utfall', 'Prognos', 'Fel'], components)
    content += '<h2>Alla tidshorisonter och mätetal</h2>'+table(['År framåt', 'Mätetal', 'n', 'Modell', 'MAE', 'Bias', 'RMSE'], summaries)
    content += '<h2>Byggprojekt som saknar observation</h2><p>Alternativen antar att 10 eller 20 procent av materiella tillgångar är pågående byggprojekt vid starten. De är varken skattningar eller konfidensintervall. Nominellt antas noll.</p>'+table(['Modell', 'Startår', 'Målår', 'Andel', 'Resultat', 'Skillnad mot noll'], [[r.get('model', 'M2')]+[r[k] for k in ('originYear', 'targetYear', 'fraction', 'result', 'differenceFromNominal')] for r in result['wipSensitivity']])
    content += '<h2>Begränsningar</h2><ul>'+''.join('<li>'+esc(x)+'</li>' for x in result['limitations'])+'</ul></html>'
    (Path(directory)/'report.html').write_text(content)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--protocol', type=Path, default=ROOT/'data/historical-protocol.json')
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=False)
    data = load_ledgers()
    protocol = json.loads(args.protocol.read_text())
    macro_data = json.loads((ROOT/'data'/protocol['macroFile']).read_text()) if protocol.get('macroFile') else None
    if macro_data is not None:
        # Same rule as taxFile: a protocol that loads cost inputs must pin their hash.
        if not protocol.get('macroSha256'):
            raise ValueError('Protocol names macroFile without macroSha256')
        if hashlib.sha256((ROOT/'data'/protocol['macroFile']).read_bytes()).hexdigest() != protocol['macroSha256']:
            raise ValueError('Macro inputs differ from the locked protocol')
    tax_data = None
    if protocol.get('taxFile'):
        tax_file = ROOT/'data'/protocol['taxFile']
        if hashlib.sha256(tax_file.read_bytes()).hexdigest() != protocol['taxSha256']:
            raise ValueError('Tax inputs differ from the locked protocol')
        tax_data = json.loads(tax_file.read_text())
    event_data = None
    if protocol.get('eventsFile'):
        event_file = ROOT/'data'/protocol['eventsFile']
        if hashlib.sha256(event_file.read_bytes()).hexdigest() != protocol['eventsSha256']:
            raise ValueError('Note inputs differ from the locked protocol')
        event_data = json.loads(event_file.read_text())
    frozen = ROOT/'reference/dynamics-v2'
    for name, expected in json.loads((frozen/'manifest.json').read_text())['files'].items():
        if hashlib.sha256((frozen/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen M2-v2 changed: '+name)
    dump(args.out/'annual-ledgers.json', data)
    dump(args.out/'protocol.json', protocol)
    shutil.copytree(ROOT/'MotalaDynamics', args.out/'sources/MotalaDynamics')
    shutil.copytree(frozen, args.out/'sources/reference/dynamics-v2')
    shutil.copytree(ROOT/'reference/m0', args.out/'sources/reference/m0')
    shutil.copytree(ROOT/'motala_lab', args.out/'sources/motala_lab', ignore=shutil.ignore_patterns('__pycache__'))
    (args.out/'sources/data').mkdir()
    for name in ('annual-ledgers.json', 'historical-protocol.json', 'history-supplement.json'):
        shutil.copy2(ROOT/'data'/name, args.out/'sources/data'/name)
    dump(args.out/'sources/data/historical-protocol.json', protocol)
    shutil.copy2(ROOT/'run_historical.py', args.out/'sources/run_historical.py')
    (args.out/'sources/benchmark').mkdir()
    shutil.copy2(ROOT/'benchmark/municipal-budget-history.json', args.out/'sources/benchmark/municipal-budget-history.json')
    older = json.loads((ROOT/'data/history-2017.json').read_text()) if protocol.get('include2017') else None
    if older:
        dump(args.out/'sources/data/history-2017.json', older)
    if macro_data:
        shutil.copy2(ROOT/'data'/protocol['macroFile'], args.out/'sources/data'/protocol['macroFile'])
        shutil.copy2(ROOT/'data'/protocol['macroFile'], args.out/'skr-pkv-vintages.json')
    if tax_data is not None:
        shutil.copy2(tax_file, args.out/'sources/data'/protocol['taxFile'])
        shutil.copy2(tax_file, args.out/'skr-tax-vintages.json')
    if event_data is not None:
        # Copy exact bytes: the protocol pins the original file hash.
        shutil.copy2(event_file, args.out/'sources/data'/protocol['eventsFile'])
        shutil.copy2(event_file, args.out/'motala-noted-events.json')
        (args.out/'sources/tests').mkdir()
        test_names = ['test_noted_events.py', 'test_historical_dynamics.py', 'test_macro.py']
        if tax_data is not None:
            test_names.append('test_tax_forecasts.py')
        for name in test_names:
            shutil.copy2(ROOT/'tests'/name, args.out/'sources/tests'/name)
    observations = aggregate_observations(data, older=older)
    dump(args.out/'aggregate-observations.json', observations)
    compiler_version = subprocess.run([dynamics.compiler(), '--version'], capture_output=True, text=True, check=True).stdout.strip()
    dump(args.out/'environment.json', {'compiler': dynamics.compiler(), 'version': compiler_version,
        'annualFlowAnchoring': '(1+g)*log(1+g)/g, analytic limit 1 at zero',
        'modelicaSourceRoot': str((args.out/'sources').resolve())})
    result = evaluate(data, protocol, args.out/'origins', source_root=args.out/'sources', observations=observations,
        macro_data=macro_data, event_data=event_data, tax_data=tax_data)
    if tax_data is not None:
        result['taxInputs'] = tax_data
        result['limitations'].extend(tax_data['limitations'])
        result['taxDiagnostic'] = {'role': 'diagnostic_sensitivity_not_local_forecast',
            'candidateUnchanged': True, 'comparison': 'Each tax-only variant versus its same-note-policy parent',
            'diagnosticScores': {policy: scores(result['cases'], candidate_name='M2-PKV-'+policy+'-tax-only')
                for policy in protocol['eventScenarios']}}
    if event_data is not None:
        result['limitations'].append('Only note10 entries are separated. No-repeat assumes no replacement income and is a sensitivity scenario, not a calibrated forecast. Original total outcomes and all closing stocks are unchanged. Future provision payments and remeasurement remain unestimated.')
    if macro_data:
        result['macroInputs'] = macro_data
        result['limitations'].append('M2-PKV replaces constant personnel/other prices with dated national SKR PKV forecasts. Local applicability, quality adjustments and within-year timing are approximations; the payroll/pension split is not predicted separately.')
    benchmark = json.loads((args.out/'sources/benchmark/municipal-budget-history.json').read_text())
    result['municipalBudgetBenchmark'] = descriptive_budgets(result['cases'], benchmark)
    if protocol.get('aggregateOriginYears'):
        result['aggregateReplay'] = aggregate_replay(observations, protocol['aggregateOriginYears'], protocol['horizons'])
    dump(args.out/'evaluation.json', result)
    write_report(args.out, result)
    dump(args.out/'manifest.json', {str(p.relative_to(args.out)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(args.out.rglob('*')) if p.is_file() and p.name != 'manifest.json'})
    for s in result['scores']:
        if s['horizon'] == 1 and s['metric'] == 'result':
            print(json.dumps(s, indent=2))
    print(args.out/'report.html')
    return 0
