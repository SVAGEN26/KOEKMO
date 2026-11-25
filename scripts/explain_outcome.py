#!/usr/bin/env python3
"""Explain what happened: run the model from a base year as things were believed, then set one cause at a time
to what happened, and see how far each takes the result towards the accounts.

    OMC=/path/to/omc python3 scripts/explain_outcome.py [code Package] [--origin 2021]
    python3 scripts/explain_outcome.py --summary     # after all 13: data/outcome-explanation-summary.json

The closing accounts are the facts. The first run is a forecast with what was known in the spring after the
base year (the `skr` set of scripts/hindcast_vintages.py: SKR's December circular for the national tax base,
wages and prices; grants 2 % a year). Each later run keeps the earlier changes and sets one more input to its
outcome. Only inputs are changed, through the model's ordinary parameters; no equation is.

  believed    SKR's December circular of the base year. Years beyond the circular's three keep its last rates.
  wages       wageGrowthPath: SKR's labour-cost index as it turned out (PKV, October 2026).
  prices      priceGrowthPath: SKR's price index for other costs as it turned out.
  pensions    pensionExpensePath: the pension cost in the accounts.
  taxBase     referenceTax: the national tax base as it turned out (SCB; 2025 is SKR's estimate).
  grants      the state's general grants as booked, per component (as the hindsight set).
  interest    interestRatePath: the year's interest expense over the mean of the debt at the start and the end of
              the year, accounts.
  investment  investmentPath: the year's investments in the accounts.

What is left after the last outcome step is what these causes do not explain: the municipality's own decisions on
volume and savings, one-off items, financial items other than interest (constant in the model), the
municipality's population (the model's projection throughout) and model error. The steps are cumulative in
this order; with another order a step's share can differ where causes interact (wages and volume, debt and rate).

Two more runs test the model's inflation scenario: the believed run with inflationShockPath set to the price
surprise and nothing else, once with the default shares and once with the state compensating the grants. They
show whether the mechanism a user gets from the scenario button gives what the accounts show.

Beside the runs: SKR's own forecast of the municipality's tax and grants at the time, from the recovered
workbooks (data/skr-historical/forecasts.json), where one was read out.

HINDCAST_MODEL=Annual runs the annual model; the default here is Continuous, the model the site runs.
Writes data/outcome-explanation.json (Motala) or data/municipalities/<code>/outcome-explanation.json.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ORIGIN = 2021
if '--origin' in sys.argv:
    i = sys.argv.index('--origin')
    ORIGIN = int(sys.argv[i + 1])
    del sys.argv[i:i + 2]
import hindcast_vintages as hv  # noqa: E402  (reads the municipality from sys.argv)

MODEL = os.environ.get('HINDCAST_MODEL', 'Continuous')

ROOT = hv.ROOT
STANDARD = {'taxBase': 0.035, 'wages': 0.03, 'prices': 0.02}  # Kommunekonomi.Assumptions: taxGrowth, wageGrowth, priceGrowth
STEPS = ('believed', 'wages', 'prices', 'pensions', 'taxBase', 'grants', 'interest', 'investment')
LABELS = {
    'believed': 'Som man trodde då (SKR:s decembercirkulär)',
    'wages': 'Lönerna som de blev',
    'prices': 'Priserna som de blev',
    'pensions': 'Pensionskostnaden som den blev',
    'taxBase': 'Rikets skatteunderlag som det blev',
    'grants': 'Statens bidrag som de blev',
    'interest': 'Räntan som den blev',
    'investment': 'Investeringarna som de blev',
}
LINES = ('tax', 'grants', 'payroll', 'pension', 'otherCosts', 'operatingRevenue', 'depreciation', 'interest', 'result', 'debt', 'population')


def extended(v, years):
    """The circular's paths, with its last rate kept for years it does not cover."""
    out = {**v}
    for key in ('taxBase', 'labour', 'other'):
        out[key] = {y: v[key].get(y, v[key][max(v[key])]) for y in years}
    november = dict(v['nationalNovember'])
    for y in range(max(november) + 1, years[-1]):
        november[y] = november[y - 1] * november[y - 1] / november[y - 2]
    out['nationalNovember'] = november
    return out


def interest_rate(ledgers, year):
    """The rate paid: the year's interest expense over the mean of the debt at the start and the end of the year."""
    debt = (ledgers[year - 1]['debt'] + ledgers[year]['debt']) / 2
    return ledgers[year]['interest'] / debt if debt > 0 else 0


def model_source(origin, horizon, v, done, ledgers, older_shares=None, extra=()):
    """The model with every input in `done` set to its outcome."""
    n0, path = hv.national_path(origin, horizon, v)
    years = [origin + i for i in range(1, horizon + 1)]
    pkv, record = hv.pkv_outcomes(), lambda y: f'{hv.PACKAGE}.Data.{hv.PREFIX}{y}'
    labour = {y: pkv[y]['labour'] if 'wages' in done else v['labour'][y] for y in years}
    other = {y: pkv[y]['other'] if 'prices' in done else v['other'][y] for y in years}
    tax_base = hv.tax_base_outcomes() if 'taxBase' in done else v['taxBase']
    cum_tax, cum_labour, tax, pension = 1.0, 1.0, [], []
    for y in years:
        cum_tax *= 1 + tax_base[y]
        cum_labour *= 1 + v['labour'][y]  # the believed pension path follows the believed labour index
        tax.append(cum_tax)
        pension.append(cum_labour)
    lines = [f'base = {record(origin)}', f'horizon = {horizon}', f'nationalPopulation0 = {n0:.10g}',
             f'nationalPopulationPath = {hv.modelica_array(path)}',
             f'referenceTax = {hv.modelica_array(tax)}*recurringTax0',
             f'wageGrowthPath = {hv.modelica_array([labour[y] for y in years])}',
             f'priceGrowthPath = {hv.modelica_array([other[y] for y in years])}',
             'pensionExpensePath = ' + (hv.modelica_array([ledgers[y]['pension'] for y in years]) if 'pensions' in done
                                        else f'{hv.modelica_array(pension)}*pension0')]
    if older_shares:
        lines.append(f'olderShares = {hv.modelica_array(older_shares)}')
    if 'grants' in done:  # as the hindsight set: each component as booked, per inhabitant at the end of the year before
        per_capita = lambda k: '{' + ', '.join(f'{record(y)}.grantComponents[{k}]*1e6/{record(y)}.reportedPopulation[2]' for y in years) + '}'
        lines += ['grantsByComponent = true', f'incomeEqualisationPerCapitaPath = {per_capita(1)}',
                  f'relativeTaxCapacityPath = fill(base.relativeTaxCapacity[2], {horizon})',
                  f'costEqualisationPerCapitaPath = {per_capita(2)}', f'regulationPerCapitaPath = {per_capita(3)}',
                  f'lssEqualisationPerCapitaPath = {per_capita(4)}',
                  'propertyFeePath = {' + ', '.join(f'{record(y)}.grantComponents[5]' for y in years) + '}',
                  'otherGeneralGrantsPath = {' + ', '.join(f'{record(y)}.grants - sum({record(y)}.grantComponents)' for y in years) + '}']
    rate = lambda y: interest_rate(ledgers, y)
    if ledgers[origin - 1]['debt'] <= 0:  # no debt at the start of the base year, so the model cannot derive a rate
        lines.append(f'interestRate = {rate(origin + 1):.10g}')
    if 'interest' in done:
        lines.append('interestRatePath = ' + hv.modelica_array([rate(y) for y in years]))
    if 'investment' in done:
        lines.append('investmentPath = ' + hv.modelica_array([ledgers[y]['investment'] for y in years]))
    lines += extra
    return f'model Run\n  extends {hv.PACKAGE}.{MODEL}(\n    ' + ',\n    '.join(lines) + ');\nend Run;\n'


def skr_forecasts(years):
    """SKR's own forecast of the municipality's tax and grants in each recovered workbook, for the years asked."""
    path = ROOT / 'data/skr-historical/forecasts.json'
    if not path.exists():
        return []
    out = []
    for v in json.loads(path.read_text())['vintages']:
        rows = {r['year']: r for r in v['municipalities'].get(hv.CODE, {}).get('rows', [])}
        if any(y in rows for y in years):
            out.append({'circular': v['circular'], 'published': v['published'],
                        'rows': [{'year': y, 'tax': rows[y]['tax'], 'grants': rows[y]['grants']} for y in years if y in rows]})
    return out


def main():
    ledgers, sources, _, regional = hv.outcomes()
    horizon = hv.LAST - ORIGIN
    years = [ORIGIN + i for i in range(1, horizon + 1)]
    v = extended(hv.vintage(ORIGIN), years)
    older = regional.get(ORIGIN, {}).get('olderShares')
    runs = {}
    with tempfile.TemporaryDirectory(prefix='explain-') as tmp:
        def run(name, done, extra=(), source=None):
            directory = Path(tmp) / name
            directory.mkdir()
            hv.MODEL = MODEL  # simulate() takes twelve steps a year for the continuous model
            result = hv.simulate(ORIGIN, horizon, source or model_source(ORIGIN, horizon, v, done, ledgers, older, extra), directory)
            return {y: {'tax': m['tax'], 'grants': m['grants'], 'payroll': m['payroll'], 'pension': m['pensionExpense'],
                        'otherCosts': m['otherOperatingExpense'], 'operatingRevenue': m['operatingRevenue'],
                        'depreciation': m['depreciation'], 'interest': m['interest'], 'result': m['result'],
                        'debt': m['debt'], 'population': m['population']} for y, m in result.items()}
        for k, step in enumerate(STEPS):
            runs[step] = run(step, STEPS[:k + 1])
        # The model's inflation scenario, fed only the price surprise: does its mechanism give what happened?
        pkv = hv.pkv_outcomes()
        shock = [pkv[y]['other'] - v['other'][y] for y in years]
        path = 'inflationShockPath = ' + hv.modelica_array(shock)
        scenario = {'mechanism': run('mechanism', STEPS[:1], [path]),
                    'compensated': run('compensated', STEPS[:1], [path, 'inflationGrantCompensation = 1'])}
        # The model on its own: its standard rates instead of SKR's circular (tax base 3.5 %, wages 3 %, prices 2 %;
        # grants 2 % as in every run). Sweden's population stays the circular's, which was known then.
        own = {**v, 'taxBase': {y: STANDARD['taxBase'] for y in years}, 'labour': {y: STANDARD['wages'] for y in years},
               'other': {y: STANDARD['prices'] for y in years}}
        runs['standard'] = run('standard', (), source=model_source(ORIGIN, horizon, own, (), ledgers, older))
    outcome = {y: {'tax': o['tax'], 'grants': o['grants'], 'payroll': o.get('payroll'), 'pension': o.get('pension'),
                   'otherCosts': o.get('otherExpense'), 'operatingRevenue': o.get('operatingRevenue'),
                   'depreciation': o.get('depreciation'), 'interest': o.get('interest'), 'result': o['result'],
                   'debt': o.get('debt'), 'population': o['population'],
                   'otherFinancialNet': o['financialIncome'] - (o['financialExpense'] - o['interest']),
                   'source': sources[o['sourceId']]} for y, o in ((y, ledgers[y]) for y in years)}
    ladder = []
    for y in years:
        before = None
        for step in STEPS:
            result = runs[step][y]['result']
            ladder.append({'year': y, 'step': step, 'label': LABELS[step], 'result': result,
                           'change': None if before is None else result - before, 'gap': result - outcome[y]['result']})
            before = result
    last = STEPS[-1]
    o0 = ledgers[ORIGIN]
    other_net = lambda o: o['financialIncome'] - (o['financialExpense'] - o['interest'])
    remaining = [{'year': y, **{k: runs[last][y][k] - outcome[y][k] for k in LINES if outcome[y][k] is not None},
                  # the model keeps the base year's financial income and other financial expense
                  'otherFinancialNet': other_net(o0) - other_net(ledgers[y])} for y in years]
    out = {'municipality': hv.CODE, 'model': f'{hv.PACKAGE}.{MODEL}', 'origin': ORIGIN, 'years': years,
           'circular': v['circular'], 'method': __doc__.strip(), 'units': 'mnkr; population in persons',
           'steps': [{'step': s, 'label': LABELS[s]} for s in STEPS],
           'inputs': {'believed': {str(y): {'taxBase': v['taxBase'][y], 'wages': v['labour'][y], 'prices': v['other'][y]} for y in years},
                      'outcome': {str(y): {'taxBase': hv.tax_base_outcomes()[y], 'wages': hv.pkv_outcomes()[y]['labour'],
                                           'prices': hv.pkv_outcomes()[y]['other'], 'pension': ledgers[y]['pension'],
                                           'interestRate': interest_rate(ledgers, y),
                                           'investment': ledgers[y]['investment']} for y in years},
                      'beyondCircular': [y for y in years if y not in hv.vintage(ORIGIN)['taxBase']]},
           'baseYear': {'result': o0['result'], 'otherFinancialNet': other_net(o0)},
           'ladder': ladder, 'remainingByLine': remaining, 'outcome': {str(y): o for y, o in outcome.items()},
           'runs': {s: {str(y): r for y, r in rows.items()} for s, rows in runs.items()},
           'inflationScenario': {
               'description': 'The believed run with the model\'s inflation scenario and nothing else: inflationShockPath is the '
                              'price surprise (SKR\'s price index for other costs, outcome minus the circular). mechanism has '
                              'the model\'s default shares; compensated also has inflationGrantCompensation = 1 (the state '
                              'raises the grants by the year before\'s extra inflation).',
               'shock': shock, 'delayed': [((shock[i - 1] if i > 0 else 0) + (shock[i - 2] if i > 1 else 0)) / 2 for i in range(len(years))],
               'evidence': {str(y): {'labourIndexAboveBelieved': pkv[y]['labour'] - v['labour'][y],
                                     'taxBaseAboveBelieved': hv.tax_base_outcomes()[y] - v['taxBase'][y],
                                     'pensionOverBelievedPath': ledgers[y]['pension'] / runs['believed'][y]['pension'] - 1,
                                     'paidRateAboveBaseYear': interest_rate(ledgers, y) - interest_rate(ledgers, ORIGIN)}
                            for y in years},
               'runs': {name: {str(y): r for y, r in rows.items()} for name, rows in scenario.items()}},
           'skrForecasts': skr_forecasts(years)}
    suffix = '' if MODEL == 'Continuous' else '-annual'
    target = ROOT / (f'data/outcome-explanation{suffix}.json' if hv.CODE == '0583' else f'data/municipalities/{hv.CODE}/outcome-explanation{suffix}.json')
    target.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    print(f'{hv.PACKAGE} from {ORIGIN}: result, mnkr')
    print(f'{"":46s}' + ''.join(f'{y:>8d}' for y in years))
    for step in STEPS:
        print(f'{LABELS[step]:46s}' + ''.join(f'{runs[step][y]["result"]:8.0f}' for y in years))
    print(f'{"Bokslut":46s}' + ''.join(f'{outcome[y]["result"]:8.0f}' for y in years))
    for name, label in (('mechanism', 'Inflationsscenariot, bara prischocken'), ('compensated', 'Inflationsscenariot med statlig kompensation')):
        print(f'{label:46s}' + ''.join(f'{scenario[name][y]["result"]:8.0f}' for y in years))
    print(f'{"Kvar att förklara":46s}' + ''.join(f'{runs[last][y]["result"] - outcome[y]["result"]:8.0f}' for y in years))
    for k in (*LINES, 'otherFinancialNet'):
        if all(k in r for r in remaining):
            print(f'  kvar, {k:39s}' + ''.join(f'{r[k]:8.0f}' for r in remaining))


def summary():
    """All municipalities' runs side by side, and SKR's old forecasts of tax and grants against the outcomes."""
    import statistics
    files = {f.parent.name: f for f in sorted((ROOT / 'data/municipalities').glob('[0-9]*/outcome-explanation.json'))}
    files['0583'] = ROOT / 'data/outcome-explanation.json'
    runs = {code: json.loads(f.read_text()) for code, f in sorted(files.items())}
    years = next(iter(runs.values()))['years']
    last = STEPS[-1]
    share = lambda value, base: 100 * value / base
    median = lambda values: statistics.median(values)
    rows, gaps = [], {}
    for code, d in runs.items():
        outcome = {y: d['outcome'][str(y)] for y in years}
        revenue = {y: outcome[y]['tax'] + outcome[y]['grants'] for y in years}
        result = lambda step: [d['runs'][step][str(y)]['result'] for y in years]
        actual = [outcome[y]['result'] for y in years]
        change = lambda series: [series[0] - d['baseYear']['result']] + [b - a for a, b in zip(series, series[1:])]
        rows.append({'municipality': code, 'name': json.loads((ROOT / f'data/municipalities/{code}/base-years.json').read_text())['name'],
                     'believed': result('believed'), 'explained': result(last), 'outcome': actual,
                     'remainingByLine': d['remainingByLine']})
        for name, step in (('believed', 'believed'), ('explained', last)):
            for i, y in enumerate(years):
                g = gaps.setdefault(name, {}).setdefault(y, {'result': [], 'resultChange': [], 'payroll': [], 'otherCosts': []})
                g['result'].append(share(abs(result(step)[i] - actual[i]), revenue[y]))
                g['resultChange'].append(share(abs(change(result(step))[i] - change(actual)[i]), revenue[y]))
                for line in ('payroll', 'otherCosts'):
                    g[line].append(share(d['runs'][step][str(y)][line] - outcome[y][line], outcome[y][line]))
    # How much of the price surprise reached other costs: 0 = they rose as believed, 1 = as SKR's index turned out.
    reached = {y: median([(d['outcome'][str(y)]['otherCosts'] - d['runs']['wages'][str(y)]['otherCosts'])
                          / (d['runs']['prices'][str(y)]['otherCosts'] - d['runs']['wages'][str(y)]['otherCosts'])
                          for d in runs.values()]) for y in years}
    # The inflation scenario against the accounts: each line, and the result's change from the believed run.
    scenario = {'lines': {}, 'resultAgainstBelieved': {}}
    for line in ('tax', 'grants', 'payroll', 'pension', 'otherCosts', 'interest'):
        scenario['lines'][line] = {str(y): median([share(d['inflationScenario']['runs']['mechanism'][str(y)][line] - d['outcome'][str(y)][line],
                                                         d['outcome'][str(y)][line]) for d in runs.values() if d['outcome'][str(y)][line]])
                                   for y in years}
    usual = [d for code, d in runs.items() if code != '0581']  # Norrköping's 2022 holds the Ostlänken provision
    for name, source in (('mechanism', lambda d, y: d['inflationScenario']['runs']['mechanism'][y]['result']),
                         ('compensated', lambda d, y: d['inflationScenario']['runs']['compensated'][y]['result']),
                         ('accounts', lambda d, y: d['outcome'][y]['result'])):
        scenario['resultAgainstBelieved'][name] = {
            str(y): median([share(source(d, str(y)) - d['runs']['believed'][str(y)]['result'],
                                  d['outcome'][str(y)]['tax'] + d['outcome'][str(y)]['grants']) for d in usual]) for y in years}
    first = next(iter(runs.values()))['inflationScenario']
    evidence = {str(y): {'priceSurprise': first['shock'][i], 'delayed': first['delayed'][i],
                         'labourIndexAboveBelieved': first['evidence'][str(y)]['labourIndexAboveBelieved'],
                         'taxBaseAboveBelieved': first['evidence'][str(y)]['taxBaseAboveBelieved'],
                         'pensionOverBelievedPath': median([d['inflationScenario']['evidence'][str(y)]['pensionOverBelievedPath'] for d in runs.values()]),
                         'paidRateAboveBaseYear': median([d['inflationScenario']['evidence'][str(y)]['paidRateAboveBaseYear'] for d in runs.values()])}
                for i, y in enumerate(years)}
    forecasts = []
    path = ROOT / 'data/skr-historical/forecasts.json'
    for v in json.loads(path.read_text())['vintages'] if path.exists() else []:
        errors = {}
        for code, d in runs.items():
            base = json.loads((ROOT / f'data/municipalities/{code}/base-years.json').read_text())['years']
            for r in v['municipalities'].get(code, {}).get('rows', []):
                if str(r['year']) in base and r['year'] <= hv.LAST:
                    o = base[str(r['year'])]['tax'] + base[str(r['year'])]['grants']
                    errors.setdefault(r['year'], []).append(share(r['tax'] + r['grants'] - o, o))
        forecasts.append({'forecast': f"SKR {v['circular']}", 'published': v['published'],
                          'rows': [{'year': y, 'municipalities': len(e), 'meanErrorPercent': statistics.mean(e),
                                    'meanAbsErrorPercent': statistics.mean(map(abs, e))} for y, e in sorted(errors.items())]})
    own = {}
    for d in runs.values():
        for y in years:
            o, m = d['outcome'][str(y)], d['runs']['believed'][str(y)]
            own.setdefault(y, []).append(share(m['tax'] + m['grants'] - o['tax'] - o['grants'], o['tax'] + o['grants']))
    forecasts.append({'forecast': f'The model from the {ORIGIN} accounts (believed)', 'published': 'accounts in spring; circular of December',
                      'rows': [{'year': y, 'municipalities': len(e), 'meanErrorPercent': statistics.mean(e),
                                'meanAbsErrorPercent': statistics.mean(map(abs, e))} for y, e in sorted(own.items())]})
    alone = {}
    for d in runs.values():
        if 'standard' not in d['runs']:
            continue
        for y in years:
            o, m = d['outcome'][str(y)], d['runs']['standard'][str(y)]
            alone.setdefault(y, []).append(share(m['tax'] + m['grants'] - o['tax'] - o['grants'], o['tax'] + o['grants']))
    if alone:
        forecasts.append({'forecast': f'The model from the {ORIGIN} accounts with its own standard rates (no SKR tax base)',
                          'published': 'accounts in spring', 'rows': [
                              {'year': y, 'municipalities': len(e), 'meanErrorPercent': statistics.mean(e),
                               'meanAbsErrorPercent': statistics.mean(map(abs, e))} for y, e in sorted(alone.items())]})
    out = {'origin': ORIGIN, 'years': years, 'municipalities': rows,
           'units': 'mnkr; gaps in per cent',
           'medianGap': {name: {str(y): {'resultPercentOfTaxAndGrants': median(g['result']),
                                        'resultChangePercentOfTaxAndGrants': median(g['resultChange']),
                                        'payrollPercent': median(g['payroll']), 'otherCostsPercent': median(g['otherCosts'])}
                               for y, g in by_year.items()} for name, by_year in gaps.items()},
           'priceSurpriseReachingOtherCosts': {str(y): v for y, v in reached.items()},
           'inflationScenario': {'description': 'The model\'s inflation scenario from the base year, fed the price surprise only. lines: '
                                                'median of the model minus the accounts, per cent of the line. resultAgainstBelieved: '
                                                'median change of the result from the believed run, per cent of tax and grants '
                                                '(12 municipalities, without Norrköping). evidence: what the shares are set after.',
                                 **scenario, 'evidence': evidence},
           'taxAndGrantsForecasts': forecasts,
           'notes': ['believed: the model with what was known in the spring after the base year. explained: the same model '
                     'with wages, prices, pensions, tax base, grants, interest rate and investments set to their outcomes.',
                     'result gaps are absolute, as a share of the year\'s tax and grants; resultChange compares the change from '
                     'the year before. payroll and otherCosts are the model minus the outcome, as a share of the outcome.',
                     'Outcomes in the forecast comparison are SCB\'s account summary for all 13, so that the municipalities are '
                     'measured alike. SKR\'s forecasts are dated; the model\'s run uses the closing accounts and the December '
                     'circular, which came later than SKR 21:35.']}
    (ROOT / 'data/outcome-explanation-summary.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    for name, by_year in out['medianGap'].items():
        for y, g in by_year.items():
            print(name, y, {k: round(v, 1) for k, v in g.items()})
    print('price surprise reaching other costs', {y: round(v, 2) for y, v in reached.items()})
    for line, by_year in scenario['lines'].items():
        print('scenario', line, {y: round(v, 1) for y, v in by_year.items()})
    for name, by_year in scenario['resultAgainstBelieved'].items():
        print('result against believed', name, {y: round(v, 1) for y, v in by_year.items()})
    for y, e in evidence.items():
        print('evidence', y, {k: round(100 * v, 1) for k, v in e.items()})
    for f in forecasts:
        print(f['forecast'], [(r['year'], round(r['meanErrorPercent'], 1)) for r in f['rows']])


if __name__ == '__main__':
    if '--summary' in sys.argv:
        summary()
    else:
        main()
