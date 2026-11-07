"""One-parameter reported-budget feedback, with strictly earlier training data.

This is an annual diagnostic for the proposed M2 mechanism, not an estimated
causal spending rule. All monetary inputs use the same nominal mnkr basis.
"""
import math

COMPONENTS = ('taxAndGrants', 'netCost', 'financeNet')
METRICS = COMPONENTS + ('result',)


def validate_rows(rows):
    if not rows:
        raise ValueError('No observed accounts')
    years = [row['year'] for row in rows]
    if any(type(year) is not int for year in years) or years != sorted(set(years)):
        raise ValueError('Years must be unique integers in chronological order')
    for row in rows:
        for key in METRICS:
            value = row[key]
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('Missing or non-finite account: ' + key)
        if row['taxAndGrants'] <= 0 or row['netCost'] < 0:
            raise ValueError('Positive revenue and nonnegative net cost required')


def signal(row):
    return row['taxAndGrants'] - row['netCost'] + row['financeNet']


def window(rows, year, size):
    result = [row for row in rows if year - size < row['year'] <= year]
    return result if [row['year'] for row in result] == list(range(year-size+1, year+1)) else []


def base_path(history, horizon, protocol):
    """Same damped trend as fiscal.baseline; require a complete five-year base."""
    recent = window(history, history[-1]['year'], protocol['baseHistoryYears'])
    if not recent:
        raise ValueError('Incomplete base history')
    slopes = {key: sum(b[key]-a[key] for a, b in zip(recent, recent[1:])) / (len(recent)-1)
              for key in COMPONENTS}
    origin = recent[-1]
    path = [{key: origin[key] for key in COMPONENTS}]
    damping_sum = 0.0
    for h in range(1, horizon+1):
        damping_sum += protocol['trendDamping'] ** h
        path.append({key: origin[key] + slopes[key]*damping_sum for key in COMPONENTS})
    return path


def coefficient(pairs, protocol):
    denominator = sum(p['x']**2 for p in pairs)
    if denominator <= protocol['minimumNormalizedSignalSumSquares']:
        return None, None, denominator
    raw = sum(p['x']*p['z'] for p in pairs) / denominator
    lower, upper = protocol['lambdaBounds']
    return raw, max(lower, min(upper, raw)), denominator


def fit(rows, origin, protocol):
    cutoff = min(origin, protocol['lastTrainingTargetYear'])
    history = [r for r in rows if r['year'] <= cutoff]
    lookup = {r['year']: r for r in history}
    pairs, omitted = [], []
    for row in history:
        year = row['year']
        if year+1 > cutoff:
            continue
        recent = window(history, year, protocol['baseHistoryYears'])
        if not recent or year+1 not in lookup:
            omitted.append({'origin': year, 'reason': 'missing_base_history_or_next_observation'})
            continue
        predicted = base_path(recent, 1, protocol)[1]['netCost']
        revenue = row['taxAndGrants']
        pairs.append({'origin': year, 'target': year+1,
                      'x': signal(row)/revenue,
                      'z': (lookup[year+1]['netCost']-predicted)/revenue,
                      'budgetSignal': signal(row), 'baseNetCost': predicted,
                      'observedNetCost': lookup[year+1]['netCost']})
    result = {'cutoff': cutoff, 'trainingPairs': pairs, 'omittedTrainingOrigins': omitted,
              'pairCount': len(pairs), 'lambda': None, 'unconstrainedLambda': None}
    denominator = sum(p['x']**2 for p in pairs)
    result.update(normalizedSignalSumSquares=denominator,
                  signalCounts={'positive': sum(p['x'] > 0 for p in pairs),
                                'negative': sum(p['x'] < 0 for p in pairs),
                                'zero': sum(p['x'] == 0 for p in pairs)},
                  largestSignalSquareShare=max((p['x']**2/denominator for p in pairs), default=0.0)
                  if denominator else None)
    if len(pairs) < protocol['minimumTrainingPairs']:
        return dict(result, status='insufficient_training')
    raw, bounded, denominator = coefficient(pairs, protocol)
    result.update(unconstrainedLambda=raw, **{'lambda': bounded})
    if bounded is None:
        return dict(result, status='unidentified_budget_signal')
    stability = []
    for index, pair in enumerate(pairs):
        leave_raw, leave_bounded, _ = coefficient(pairs[:index]+pairs[index+1:], protocol)
        stability.append({'omittedTarget': pair['target'], 'unconstrainedLambda': leave_raw,
                          'lambda': leave_bounded})
    for pair in pairs:
        pair['normalizedTrainingResidual'] = pair['z']-bounded*pair['x']
    return dict(result, status='fitted', leaveOnePairOut=stability,
                stabilityInterpretation='sensitivity_only_not_confidence_interval')


def forecast(history, horizon, adjustment, protocol):
    if not math.isfinite(adjustment) or not 0 <= adjustment <= 1:
        raise ValueError('Lambda must be finite and in [0,1]')
    base = base_path(history, horizon, protocol)
    previous = base[0]
    result = []
    for h in range(1, horizon+1):
        row = dict(base[h])
        reaction = adjustment*signal(previous)
        row['netCost'] = (base[h]['netCost'] if adjustment == 0 else
                          previous['netCost'] + (base[h]['netCost'] - base[h-1]['netCost']) + reaction)
        if row['taxAndGrants'] <= 0 or row['netCost'] < 0:
            raise ValueError('Forecast outside admissible account domain')
        row.update(year=history[-1]['year']+h, result=signal(row), budgetReaction=reaction)
        if not all(math.isfinite(row[key]) for key in METRICS):
            raise ValueError('Non-finite forecast')
        result.append(row)
        previous = row
    return result


def evaluate(rows, protocol):
    validate_rows(rows)
    if protocol['resultTargetShare'] != 0 or protocol['lambdaBounds'] != [0.0, 1.0]:
        raise ValueError('This experiment implements only s=0 and lambda in [0,1]')
    lookup = {row['year']: row for row in rows}
    fits, cases, skipped = {}, [], []
    for origin in protocol['originYears']:
        fit_result = fit(rows, origin, protocol)
        fits[str(origin)] = fit_result
        history = [r for r in rows if r['year'] <= origin]
        reason = ('missing_origin' if origin not in lookup else
                  'incomplete_base_history' if not window(history, origin, protocol['baseHistoryYears']) else
                  fit_result['status'] if fit_result['status'] != 'fitted' else None)
        if reason:
            skipped.append({'origin': origin, 'reason': reason, 'trainingStatus': fit_result['status']})
            continue
        for h in protocol['horizons']:
            target = origin+h
            if target > protocol['lastTargetYear']:
                continue
            if target not in lookup:
                skipped.append({'origin': origin, 'horizon': h, 'reason': 'missing_target'})
                continue
            actual = lookup[target]
            predictions, failures = {}, {}
            for name, adjustment in (('budget_response', fit_result['lambda']),
                                     ('identical_base_lambda_zero', 0.0)):
                try:
                    predictions[name] = forecast(history, h, adjustment, protocol)[-1]
                except ValueError as exc:
                    failures[name] = str(exc)
            if failures:
                skipped.append({'origin': origin, 'horizon': h, 'reason': 'invalid_forecast',
                                'failures': failures})
                continue
            predictions['last_reported_result'] = {'result': history[-1]['result']}
            predictions['expanding_mean_reported_result'] = {
                'result': sum(row['result'] for row in history)/len(history)}
            for name, prediction in predictions.items():
                metrics = {key: prediction[key]-actual[key] for key in METRICS if key in prediction}
                cases.append({'origin': origin, 'target': target, 'horizon': h, 'model': name,
                              'originBlock': 'earlier_origins' if origin <= 2019 else 'existing_origins',
                              'period': 'earlier_targets' if target <= 2019 else 'previously_examined_targets',
                              'forecast': prediction,
                              'actual': {key: actual[key] for key in METRICS},
                              'actualAccountingResidual': actual['result']-signal(actual),
                              'errors': metrics})
    summaries = []
    for period in ('all', 'earlier_targets', 'previously_examined_targets', 'earlier_origins', 'existing_origins'):
        subset = [c for c in cases if period == 'all' or c['period'] == period or c['originBlock'] == period]
        for name in sorted({c['model'] for c in subset}):
            for h in protocol['horizons']:
                selected = [c for c in subset if c['model'] == name and c['horizon'] == h]
                for metric in METRICS:
                    errors = [c['errors'][metric] for c in selected if metric in c['errors']]
                    if errors:
                        summaries.append({'period': period, 'model': name, 'horizon': h, 'metric': metric,
                                          'count': len(errors), 'MAE': sum(abs(e) for e in errors)/len(errors),
                                          'RMSE': math.sqrt(sum(e*e for e in errors)/len(errors)),
                                          'bias': sum(errors)/len(errors)})
    return {'status': 'evaluated_retrospective' if cases else 'no_evaluable_cases',
            'fits': fits, 'cases': cases, 'skipped': skipped, 'summary': summaries,
            'forecastPrecisionApproved': False}
