#!/usr/bin/env python3
"""Does history move the way the model says it should? The model's responses against the accounts of 13 municipalities.

    python3 scripts/response_test.py

The hindcasts (hindcast_vintages.py, hindcast_long.py) score levels: was the result right. The site is used
for something else: to see how much the result moves when the population, the investments or the prices move.
This script tests those responses. For each one it computes the change the model's own rule gives from the
observed driver, and compares it with the observed change in the accounts:

  costs        real growth of gross operating cost (SCB TAB6777 item 022, deflated with SKR's PKV) against the
               growth of the model's service volume from the observed population, 2012-2025.
  revenue      growth of tax and general grants (items 040 and 050) against the growth of the population the
               year before, 2011-2025. The model scales both with the population (elasticity 1).
  financing    where a financing need (investment less the result and depreciation) shows up in the balance
               sheet (SCB TAB6779), 2018-2025, over one to eight years. The model borrows exactly what the cash
               flow does not cover.
  depreciation depreciation against the model's rule (assets in use over a fixed life) with the observed
               investments, 2017-2025.
  prices       nominal cost growth beyond the service volume against PKV, year by year (13 municipalities' mean).

A response is right when the slope is 1: the observed change is, on average, the change the model gives.
A slope of 0.5 means history moved half as much as the model says. The slope is a regression of the observed
change on the model's, with a common effect per year removed (what happened to all 13 municipalities that
year: the pandemic, a national wage round, a reform of the grants). It is therefore identified from
differences between municipalities, not from the national trend. The 95 % interval resamples municipalities
(cluster bootstrap), since one municipality's years are not independent.

Everything here uses outcomes for the drivers, on purpose: the question is what follows from a given
population or investment, not whether the population was foreseen. Nothing here is a forecast.

Limits. Thirteen municipalities in one county are few; the intervals are wide and say so. PKV is national,
so a municipality's own wage drift is in the cost growth. The service volume uses each municipality's sector
shares and care weights of 2025 for the whole period. Costs include pensions (5-8 % of the item), which the
model does not scale with volume. The capacity starts at the need of 2009, so 2010-2011 are run-in and not
scored. Years with a one-off that the annual report does not split out are left out (trendExclude). Not
tested: the interest rate's pass-through, the tax rate and pension costs. The inflation scenario is compared with
2022-2025 in scripts/explain_outcome.py.

Writes data/response-test.json.
"""
import json
import math
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import cost_residual as cr  # noqa: E402
from prepare_municipality import jsonstat  # noqa: E402

FIRST, LAST = 2009, 2025
RUN_IN = 2  # years after FIRST that are not scored: the capacity starts at the need of FIRST
ADJUSTMENT, FIXED_SHARE = 0.5, 0.25  # the model's defaults (Assumptions.adjustment, fixedShare)
HORIZONS = (1, 3, 5, 10)


# --- The model's service volume, from a population by single years of age -------------------------------------

def groups(ages):
    """The age groups the model's services use: 0-6, 7-15, 16-18; 65-79, 80-89, 90+; everyone."""
    return {'education': [sum(ages[0:7]), sum(ages[7:16]), sum(ages[16:19])],
            'older': [sum(ages[65:80]), sum(ages[80:90]), sum(ages[90:])], 'total': sum(ages)}


def need(now, base, education_weights, care_weights):
    """Kommunekonomi.Components.Services: education, elderly care and other need, index (base = 1)."""
    care = lambda g: sum(w * x for w, x in zip(care_weights, g['older']))
    return [sum(w * x / x0 for w, x, x0 in zip(education_weights, now['education'], base['education'])),
            care(now) / care(base), now['total'] / base['total']]


def annual_volume(needs, shares, adjustment=ADJUSTMENT, fixed_share=FIXED_SHARE, lag=0):
    """Service volume per year with a yearly step (the rule of the former Kommunekonomi.Annual): capacity closes `adjustment` of the gap to
    fixed + (1 - fixed) x need once a year, and the year's cost uses the capacity after that step.
    needs[k] is the need at the end of year k (needs[0] = 1, the start). lag = 1 uses the need a year earlier."""
    capacity, out = [1.0] * 3, [1.0]
    for k in range(1, len(needs)):
        demand = needs[max(0, k - lag)]
        capacity = [c + adjustment * (fixed_share + (1 - fixed_share) * d - c) for c, d in zip(capacity, demand)]
        out.append(sum(s * c for s, c in zip(shares, capacity)))
    return out


def continuous_capacity(needs, adjustment=ADJUSTMENT, fixed_share=FIXED_SHARE):
    """Capacity per sector as Kommunekonomi.Continuous.Services has it: der(capacity) = rate x (target - capacity),
    rate = -ln(1 - adjustment), target = fixed + (1 - fixed) x need. The need moves linearly between year ends.
    Returns per year the capacity at the year's end and its mean over the year (first entry: the start, 1)."""
    rate = -math.log(max(1e-6, 1 - adjustment))
    capacity, ends, means = [1.0] * 3, [[1.0] * 3], [[1.0] * 3]
    for k in range(1, len(needs)):
        mean = []
        for i in range(3):
            t0, t1 = (fixed_share + (1 - fixed_share) * needs[j][i] for j in (k - 1, k))
            slope, gap = t1 - t0, capacity[i] - t0 + (t1 - t0) / rate
            # capacity(u) = target(u) - slope/rate + gap x exp(-rate x u), u in [0, 1]
            mean.append(t0 + slope / 2 - slope / rate + gap * (1 - math.exp(-rate)) / rate)
            capacity[i] = t1 - slope / rate + gap * math.exp(-rate)
        ends.append(list(capacity))
        means.append(mean)
    return ends, means


def continuous_volume(needs, shares, adjustment=ADJUSTMENT, fixed_share=FIXED_SHARE):
    """Service volume per year as Kommunekonomi.Continuous.Economy counts it: the year's cost follows the year's
    mean capacity, weighted with the sector shares."""
    return [sum(s * m for s, m in zip(shares, mean)) for mean in continuous_capacity(needs, adjustment, fixed_share)[1]]


VARIANTS = {
    'annual': ('A yearly step (the former Kommunekonomi.Annual): adjustment 0.5, fixed share 0.25, need at the end of the year',
               lambda needs, shares: annual_volume(needs, shares)),
    'continuous': ('Kommunekonomi.Continuous.Economy (the model): the same parameters, capacity adjusts '
                   'continuously and the cost is the year\'s mean', lambda needs, shares: continuous_volume(needs, shares)),
    'annualLagged': ('as annual with the need at the end of the year before (the timing data/cost-residual.json used)',
                     lambda needs, shares: annual_volume(needs, shares, lag=1)),
    'need': ('the need itself at the end of the year: no fixed share, no delay',
             lambda needs, shares: annual_volume(needs, shares, adjustment=1.0, fixed_share=0.0)),
    'population': ('the total population at the end of the year', lambda needs, shares: [n[2] for n in needs]),
}


# --- Regression of the observed change on the model's ---------------------------------------------------------

def demean(cases, keys):
    """Remove group means (fixed effects) from x and y; alternating projections for more than one key."""
    x, y = [c['x'] for c in cases], [c['y'] for c in cases]
    for _ in range(1 if len(keys) < 2 else 60):
        for key in keys:
            for values in (x, y):
                sums = {}
                for c, v in zip(cases, values):
                    s = sums.setdefault(c[key], [0.0, 0])
                    s[0] += v
                    s[1] += 1
                for i, c in enumerate(cases):
                    values[i] -= sums[c[key]][0] / sums[c[key]][1]
    return x, y


def slope(cases, keys=('year',)):
    x, y = demean(cases, keys)
    sxx, sxy, syy = sum(a * a for a in x), sum(a * b for a, b in zip(x, y)), sum(b * b for b in y)
    return (sxy / sxx, sxy * sxy / (sxx * syy) if syy else float('nan')) if sxx else (float('nan'), float('nan'))


def interval(cases, keys=('year',), reps=2000, seed=20261124):
    """95 % interval of the slope from resampling municipalities with their years (cluster bootstrap)."""
    rng = random.Random(seed)
    by = {}
    for c in cases:
        by.setdefault(c['municipality'], []).append(c)
    names, draws = sorted(by), []
    for _ in range(reps):
        sample = []
        for n, name in enumerate(rng.choices(names, k=len(names))):
            sample += [{**c, 'municipality': n} for c in by[name]]  # a municipality drawn twice is two units
        b = slope(sample, keys)[0]
        if not math.isnan(b):
            draws.append(b)
    draws.sort()
    return draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]


def report(cases, keys=('year',), expected=1.0):
    b, r2 = slope(cases, keys)
    low, high = interval(cases, keys)
    return {'slope': b, 'low': low, 'high': high, 'r2': r2, 'cases': len(cases),
            'municipalities': len({c['municipality'] for c in cases}), 'modelSays': expected,
            'spreadOfModelChange': statistics.pstdev(demean(cases, keys)[0]),
            'spreadOfObservedChange': statistics.pstdev(demean(cases, keys)[1])}


def windows(series_x, series_y, municipality, horizon, first, excluded=()):
    """Log changes over `horizon` years of two level series, for every end year; overlapping windows."""
    out = []
    for year in sorted(series_y):
        start = year - horizon
        if start < first or start not in series_x or start not in series_y or year not in series_x:
            continue
        if any(start < e <= year for e in excluded):
            continue
        out.append({'municipality': municipality, 'year': year, 'x': math.log(series_x[year] / series_x[start]),
                    'y': math.log(series_y[year] / series_y[start])})
    return out


# --- Data -------------------------------------------------------------------------------------------------------

def load(code):
    folder = ROOT / ('data' if code == '0583' else f'data/municipalities/{code}')
    records = json.loads((ROOT / f'data/municipalities/{code}/base-years.json').read_text())
    old = jsonstat(cr.HISTORY / 'TAB6777.json', code)
    # Tax (040) and general grants (050): the history archive to 2016, the base-year records from 2017.
    revenue = {y: old['040'][y] + old['050'][y] for y in old['040']}
    revenue.update({int(y): r['tax'] + r['grants'] for y, r in records['years'].items()})
    net, gross = cr.accounts(code)
    care, sectors, _ = cr.weights(folder, LAST)
    split = json.loads((folder / 'sector-costs.json').read_text())['years']
    education = split[max(split)]['educationSplit']
    return {'population': cr.population(code), 'gross': gross, 'net': net,
            'revenue': revenue,
            'excluded': set(cr.supplement(code).get('trendExclude', [])),
            'shares': [sectors['education'], sectors['elderly'], sectors['other']],
            'educationWeights': [w / sum(education) for w in education],
            'careWeights': [care['65-79'], care['80+'], care['80+']],
            'records': {int(y): r for y, r in records['years'].items()},
            'balance': jsonstat(ROOT / records['archive'] / 'TAB6779.json')}


def result_of(r):
    net = r['payroll'] + r['pension'] + r['otherOperatingExpense'] - r['operatingRevenue'] + r['netCostRoundingAdjustment']
    return r['tax'] + r['grants'] - net - r['depreciation'] + r['financialIncome'] - r['interestExpense'] - r['otherFinancialExpense']


# --- The tests ----------------------------------------------------------------------------------------------------

def cost_cases(data, prices):
    """Per variant and horizon: model volume growth (x) against real gross cost growth (y)."""
    cases = {v: {h: [] for h in HORIZONS} for v in VARIANTS}
    yearly = {}
    for code, d in data.items():
        years = list(range(FIRST, LAST + 1))
        base = groups(d['population'][FIRST])
        needs = [need(groups(d['population'][y]), base, d['educationWeights'], d['careWeights']) for y in years]
        real, level = {FIRST: 1.0}, 1.0
        for y in years[1:]:
            level *= d['gross'][y] / d['gross'][y - 1] / (1 + prices[str(y)]['pkv'])
            real[y] = level
        for name, (_, rule) in VARIANTS.items():
            volume = dict(zip(years, rule(needs, d['shares'])))
            for h in HORIZONS:
                cases[name][h] += windows(volume, real, code, h, FIRST + RUN_IN, d['excluded'])
            if name == 'annual':
                yearly[code] = {y: {'nominal': d['gross'][y] / d['gross'][y - 1] - 1, 'volume': volume[y] / volume[y - 1] - 1}
                                for y in years[RUN_IN + 1:] if y not in d['excluded']}
    return cases, yearly, {code: [need(groups(d['population'][y]), groups(d['population'][FIRST]), d['educationWeights'],
                                       d['careWeights']) for y in range(FIRST, LAST + 1)] for code, d in data.items()}


def best_parameters(data, needs, prices, horizon=5):
    """Which adjustment and fixed share would have fitted the cost growth best, with the slope held at 1?"""
    real = {}
    for code, d in data.items():
        level, real[code] = 1.0, {FIRST: 1.0}
        for y in range(FIRST + 1, LAST + 1):
            level *= d['gross'][y] / d['gross'][y - 1] / (1 + prices[str(y)]['pkv'])
            real[code][y] = level
    years = list(range(FIRST, LAST + 1))
    grid = [(a / 10, f / 20) for a in range(1, 11) for f in range(0, 19)]

    def errors(codes):
        out = {}
        for a, f in grid:
            cases = []
            for n, code in enumerate(codes):
                volume = dict(zip(years, continuous_volume(needs[code], data[code]['shares'], a, f)))
                cases += windows(volume, real[code], n, horizon, FIRST + RUN_IN, data[code]['excluded'])
            x, y = demean(cases, ('year',))
            out[(a, f)] = sum((b - c) ** 2 for b, c in zip(y, x))
        return out

    sse = errors(sorted(data))
    best = min(sse, key=sse.get)
    flat = []
    for n, code in enumerate(sorted(data)):
        flat += windows({y: 1.0 for y in years}, real[code], n, horizon, FIRST + RUN_IN, data[code]['excluded'])
    without = sum(b * b for b in demean(flat, ('year',))[1])
    rng, picks = random.Random(20261124), []
    for _ in range(300):
        draw = errors(rng.choices(sorted(data), k=len(data)))
        picks.append(min(draw, key=draw.get))
    quantile = lambda values, q: sorted(values)[min(len(values) - 1, int(q * len(values)))]
    return {'horizon': horizon, 'model': 'continuous', 'adjustment': best[0], 'fixedShare': best[1],
            'adjustmentInterval': [quantile([p[0] for p in picks], 0.025), quantile([p[0] for p in picks], 0.975)],
            'fixedShareInterval': [quantile([p[1] for p in picks], 0.025), quantile([p[1] for p in picks], 0.975)],
            'squaredErrorAtBest': sse[best], 'squaredErrorAtDefault': sse[(ADJUSTMENT, FIXED_SHARE)],
            'squaredErrorWithoutVolume': without,
            'note': 'Least squares over a grid (adjustment 0.1-1.0, fixed share 0-0.9), slope held at 1, year effects removed; '
                    'intervals from 300 resamples of municipalities. A diagnostic, not an estimate to rely on.'}


def component_share(data):
    """The share of tax and general grants that the site's default (adjustment per component) scales with the
    population: tax before the settlement, income equalisation and the regulation grant. Mean 2017-2025."""
    shares = []
    for d in data.values():
        for r in d['records'].values():
            scaled = r['tax'] - r['priorYearSettlement'] + r['grantComponents'][0] + r['grantComponents'][2]
            shares.append(scaled / (r['tax'] + r['grants']))
    return statistics.mean(shares)


def revenue_cases(data):
    """Population growth the year before, and the same year (x), against the growth of tax and general grants (y)."""
    out = {'lagged': {h: [] for h in HORIZONS}, 'sameYear': {h: [] for h in HORIZONS}}
    for code, d in data.items():
        total = {y: sum(p) for y, p in d['population'].items()}
        before = {y: total[y - 1] for y in total if y - 1 in total}
        for h in HORIZONS:
            out['lagged'][h] += windows(before, d['revenue'], code, h, FIRST + 1, d['excluded'])
            out['sameYear'][h] += windows(total, d['revenue'], code, h, FIRST, d['excluded'])
    return out


# Where a financing need shows up in the balance sheet (SCB TAB6779). Each entry is a source of money: a liability
# that grows or an asset that shrinks. By the balance sheet identity they sum to the financing need, apart from
# disposals, revaluations and adjustments of equity, which are the remainder.
SOURCES = {
    'bankDebt': ('bank loans and bonds, with the short-term part (081, 082, 136, 134): the model\'s debt',
                 lambda b: b('081') + b('082') + b('136') + b('134')),
    'lending': ('less long-term lending, mostly to the municipality\'s own companies (033)', lambda b: -b('033')),
    'cash': ('less cash and bank (065): the model\'s cash', lambda b: -b('065')),
    'placements': ('less short-term investments and long-term securities (060, 036, 037, 032)',
                   lambda b: -(b('060') + b('035') - b('033'))),
    'otherLongTerm': ('other long-term liabilities: investment grants and connection fees, group loans, leasing (089 less loans)',
                      lambda b: b('089') - b('081') - b('082') - b('136')),
    'provisions': ('provisions, mostly pensions (079)', lambda b: b('079')),
    'shortTerm': ('short-term liabilities without the short-term part of loans (098 less 134)', lambda b: b('098') - b('134')),
    'receivables': ('less receivables and stock (069 less 065 and 060)', lambda b: -(b('069') - b('065') - b('060'))),
}


def debt_cases(data):
    """Per municipality and year: the financing need from the accounts, and each source's change, in shares of tax and grants."""
    cases = []
    for code, d in data.items():
        r, bs = d['records'], d['balance']
        for y in sorted(r):
            if y - 1 not in r or y in d['excluded'] or any(y not in bs.get(i, {}) or y - 1 not in bs.get(i, {}) for i in ('089', '098', '069')):
                continue
            scale = r[y]['tax'] + r[y]['grants']
            change = lambda rule: (rule(lambda item: bs.get(item, {}).get(y, 0.0)) - rule(lambda item: bs.get(item, {}).get(y - 1, 0.0))) / scale
            fixed = lambda b: b('010') if y in bs.get('010', {}) else b('015') + b('025')
            case = {'municipality': code, 'year': y, 'need': (r[y]['investment'] - result_of(r[y]) - r[y]['depreciation']) / scale,
                    # The same need with the investment the balance sheet shows: the change of fixed assets plus depreciation.
                    'needFromBalanceSheet': change(fixed) + (r[y]['depreciation'] - result_of(r[y]) - r[y]['depreciation']) / scale,
                    'investment': r[y]['investment'] / scale, 'selfFinancing': (result_of(r[y]) + r[y]['depreciation']) / scale}
            case.update({name: change(rule) for name, (_, rule) in SOURCES.items()})
            case['remainder'] = case['need'] - sum(case[name] for name in SOURCES)
            case['netBankDebt'] = case['bankDebt'] + case['lending'] + case['cash']
            cases.append(case)
    return cases


def financing(cases):
    """How much of a krona of financing need each source provided: slopes on the need, year effects removed."""
    pick = lambda key: [{'municipality': c['municipality'], 'year': c['year'], 'x': c['need'], 'y': c[key]} for c in cases]
    out = {'sources': {name: {'what': what, **report(pick(name), expected=1.0 if name == 'bankDebt' else 0.0)} for name, (what, _) in SOURCES.items()}}
    out['sources']['remainder'] = {'what': 'disposals, revaluations, adjustments of equity and differences of definition',
                                   **report(pick('remainder'), expected=0.0)}
    out['netBankDebt'] = {'what': 'bank debt less lending and cash: what the model\'s debt stands for when the companies\' loans are set aside',
                          **report(pick('netBankDebt'))}
    out['netBankDebtOnBalanceSheetNeed'] = {
        'what': 'as netBankDebt, with the need computed from the balance sheet\'s own change of fixed assets instead of SCB\'s investment survey',
        **report([{'municipality': c['municipality'], 'year': c['year'], 'x': c['needFromBalanceSheet'], 'y': c['netBankDebt']} for c in cases])}
    both = [{**c, 'y': c['netBankDebt']} for c in cases]
    a, b = two_slopes(both, 'investment', 'selfFinancing')
    rng, by, draws = random.Random(20261124), {}, []
    for c in both:
        by.setdefault(c['municipality'], []).append(c)
    for _ in range(2000):
        sample = [c for name in rng.choices(sorted(by), k=len(by)) for c in by[name]]
        draws.append(two_slopes(sample, 'investment', 'selfFinancing'))
    bounds = lambda i: [sorted(d[i] for d in draws)[int(q * len(draws))] for q in (0.025, 0.975)]
    out['netBankDebtOnInvestment'] = {'slope': a, 'low': bounds(0)[0], 'high': bounds(0)[1], 'modelSays': 1.0}
    out['netBankDebtOnSelfFinancing'] = {'slope': b, 'low': bounds(1)[0], 'high': bounds(1)[1], 'modelSays': -1.0}
    # The same over several years: the sums of the need and of the change of net bank debt, overlapping windows.
    by = {}
    for c in cases:
        by.setdefault(c['municipality'], {})[c['year']] = c
    out['netBankDebtByHorizon'] = {}
    for horizon in (1, 2, 3, 5, 8):
        row = {}
        for key in ('need', 'needFromBalanceSheet'):
            summed = []
            for municipality, years in by.items():
                for year in years:
                    span = [year - k for k in range(horizon)]
                    if all(s in years for s in span):
                        summed.append({'municipality': municipality, 'year': year, 'x': sum(years[s][key] for s in span),
                                       'y': sum(years[s]['netBankDebt'] for s in span)})
            row[key] = report(summed)
        out['netBankDebtByHorizon'][horizon] = row
    out['meanNeed'] = statistics.mean(c['need'] for c in cases)
    out['meanBySource'] = {name: statistics.mean(c[name] for c in cases) for name in list(SOURCES) + ['remainder']}
    return out


def investment_income(data):
    """Connection fees and public investment grants as a share of investment expenditure, 2018-2025 (SCB TAB4201
    items 210 and 560 over TAB5179 item 950). None when the archive of scripts/fetch_investment_income.py is not there."""
    index = json.loads((ROOT / 'data/municipalities/ostergotland-sources.json').read_text())
    archive = ROOT / index.get('investmentIncomeArchive', 'missing')
    if not (archive / 'TAB4201.json').exists():
        return None
    shares = {}
    for code in data:
        income, spending = jsonstat(archive / 'TAB4201.json', code), jsonstat(archive / 'TAB5179.json', code)['950']
        years = range(2018, LAST + 1)
        shares[cr.NAMES[code]] = sum(income['210'].get(y, 0.0) + income['560'].get(y, 0.0) for y in years) / sum(spending[y] for y in years)
    return {'source': 'SCB TAB4201 items 210 and 560, TAB5179 item 950; ' + str(archive.relative_to(ROOT)),
            'period': '2018-2025', 'byMunicipality': shares, 'lowest': min(shares.values()), 'highest': max(shares.values()),
            'median': statistics.median(shares.values())}


def two_slopes(cases, a, b):
    """Coefficients of y on two regressors with year effects removed (ordinary least squares)."""
    def centred(key):
        means = {}
        for c in cases:
            means.setdefault(c['year'], []).append(c[key])
        return [c[key] - statistics.mean(means[c['year']]) for c in cases]
    x1, x2, y = centred(a), centred(b), centred('y')
    s11, s22, s12 = sum(v * v for v in x1), sum(v * v for v in x2), sum(v * w for v, w in zip(x1, x2))
    s1y, s2y = sum(v * w for v, w in zip(x1, y)), sum(v * w for v, w in zip(x2, y))
    det = s11 * s22 - s12 * s12
    return (s1y * s22 - s2y * s12) / det, (s2y * s11 - s1y * s12) / det


def depreciation_cases(data):
    """The model's depreciation from the observed investments (x) against the observed (y), per horizon."""
    out = {h: [] for h in (1, 3, 5)}
    for code, d in data.items():
        r = d['records']
        for base in sorted(r):
            if r[base]['depreciation'] <= 0 or r[base]['assets'] <= 0:
                continue
            life, assets = r[base]['assets'] / r[base]['depreciation'], r[base]['assets']
            for y in range(base + 1, LAST + 1):
                if y not in r:
                    break
                # Kommunekonomi.Components.Capital without construction time: half the year's investment in use.
                depreciation = (assets + 0.5 * r[y]['investment']) / life
                assets += r[y]['investment'] - depreciation
                if y - base in out:
                    out[y - base].append({'municipality': code, 'year': y, 'x': math.log(depreciation / r[base]['depreciation']),
                                          'y': math.log(r[y]['depreciation'] / r[base]['depreciation'])})
    return out


def price_test(yearly, prices):
    """Year by year: the 13 municipalities' mean nominal cost growth beyond the model's volume, against PKV."""
    rows = []
    for y in range(FIRST + RUN_IN + 1, LAST + 1):
        values = [m[y]['nominal'] - m[y]['volume'] for m in yearly.values() if y in m]
        rows.append({'year': y, 'pkv': prices[str(y)]['pkv'], 'costBeyondVolume': statistics.mean(values), 'municipalities': len(values)})
    x, y = [r['pkv'] for r in rows], [r['costBeyondVolume'] for r in rows]
    mx, my = statistics.mean(x), statistics.mean(y)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    rng, draws = random.Random(20261124), []
    for _ in range(2000):
        sample = rng.choices(rows, k=len(rows))
        sx, sy = [r['pkv'] for r in sample], [r['costBeyondVolume'] for r in sample]
        ax, ay = statistics.mean(sx), statistics.mean(sy)
        denominator = sum((a - ax) ** 2 for a in sx)
        if denominator:
            draws.append(sum((a - ax) * (c - ay) for a, c in zip(sx, sy)) / denominator)
    draws.sort()
    return {'slope': b, 'low': draws[int(0.025 * len(draws))], 'high': draws[int(0.975 * len(draws)) - 1], 'modelSays': 1.0,
            'years': len(rows), 'meanDifference': my - mx, 'rows': rows,
            'note': 'One point per year, the mean of the municipalities; the interval resamples years. '
                    'meanDifference is the mean cost growth beyond volume and PKV, per year.'}


def main():
    prices = json.loads((ROOT / 'data/cost-residual.json').read_text())['pkv']
    data = {code: load(code) for code in cr.NAMES}
    cost, yearly, needs = cost_cases(data, prices)
    costs = {name: {'rule': VARIANTS[name][0],
                    'byHorizon': {h: report(cases) for h, cases in by.items()},
                    'withMunicipalityEffects': {h: report(by[h], ('year', 'municipality')) for h in (1, 3)}}
             for name, by in cost.items()}
    revenue = {name: {h: report(cases) for h, cases in by.items()} for name, by in revenue_cases(data).items()}
    revenue['modelSaysPerComponent'] = component_share(data)
    debt = financing(debt_cases(data))
    debt['investmentIncomeShare'] = investment_income(data)
    depreciation = {h: report(cases) for h, cases in depreciation_cases(data).items()}
    out = {'source': 'SCB TAB6777 and BefolkningNy (CC BY 4.0), SKR PKV, Kolada sector shares and care weights; '
                     'data/municipalities/<code>/base-years.json and the history archive',
           'method': __doc__.split('\n\n', 1)[1].strip(),
           'reading': 'slope 1 = history moved as the model says; low and high are a 95 % interval from resampling municipalities',
           'costs': costs, 'costParameters': best_parameters(data, needs, prices),
           'revenue': revenue, 'netDebt': debt, 'depreciation': depreciation, 'prices': price_test(yearly, prices)}
    (ROOT / 'data/response-test.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')

    line = lambda r: f"{r['slope']:6.2f}  [{r['low']:5.2f}, {r['high']:5.2f}]  R2 {r['r2']:4.2f}  n {r['cases']:3d}"
    print('Slope of the observed change on the model\'s (1 = as the model says), 95 % interval, year effects removed\n')
    print('Costs: real gross cost growth against the service volume')
    for name, r in costs.items():
        for h in HORIZONS:
            print(f'  {name:13s} {h:2d} y  {line(r["byHorizon"][h])}')
    for name in ('annual', 'continuous'):
        for h in (1, 3):
            print(f'  {name:13s} {h:2d} y  {line(costs[name]["withMunicipalityEffects"][h])}  (and municipality effects)')
    p = out['costParameters']
    print(f"  best fit, {p['horizon']} y: adjustment {p['adjustment']} {p['adjustmentInterval']}, fixed share {p['fixedShare']} {p['fixedShareInterval']}; "
          f"squared error {p['squaredErrorAtBest']:.4f} against {p['squaredErrorAtDefault']:.4f} at the defaults and {p['squaredErrorWithoutVolume']:.4f} with no volume at all")
    print('Revenue: tax and grants against the population')
    for name in ('lagged', 'sameYear'):
        for h in HORIZONS:
            print(f'  {name:13s} {h:2d} y  {line(revenue[name][h])}')
    print(f"  the site's default (per component) scales {revenue['modelSaysPerComponent']:.2f} of tax and grants with the population")
    print('Financing: where a krona of financing need (investment less result and depreciation) came from')
    for name, r in debt['sources'].items():
        print(f'  {name:14s}     {line(r)}  mean {100 * debt["meanBySource"][name]:5.2f} % of tax and grants')
    print(f'  bank debt less lending and cash {line(debt["netBankDebt"])}')
    print(f'  the same on the need from the balance sheet {line(debt["netBankDebtOnBalanceSheetNeed"])}')
    for h, row in debt['netBankDebtByHorizon'].items():
        print(f'  over {h} y         {line(row["need"])}  | need from the balance sheet {line(row["needFromBalanceSheet"])}')
    if debt['investmentIncomeShare']:
        s = debt['investmentIncomeShare']
        print(f"  connection fees and investment grants paid {100 * s['lowest']:.1f} to {100 * s['highest']:.1f} % of the investments 2018-2025 (median {100 * s['median']:.1f} %)")
    i, s = debt['netBankDebtOnInvestment'], debt['netBankDebtOnSelfFinancing']
    print(f'  on investment alone {i["slope"]:.2f} [{i["low"]:.2f}, {i["high"]:.2f}] (model 1), on result and depreciation alone '
          f'{s["slope"]:.2f} [{s["low"]:.2f}, {s["high"]:.2f}] (model -1); mean need {100 * debt["meanNeed"]:.2f} % of tax and grants')
    print('Depreciation: observed against the model\'s rule with observed investments')
    for h, r in depreciation.items():
        print(f'  {h} y                {line(r)}')
    r = out['prices']
    print(f"Prices: cost growth beyond volume against PKV, {r['years']} years: slope {r['slope']:.2f} [{r['low']:.2f}, {r['high']:.2f}], "
          f"mean difference {100 * r['meanDifference']:.2f} % a year")


if __name__ == '__main__':
    main()
