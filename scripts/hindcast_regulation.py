#!/usr/bin/env python3
"""Which rule for the state's frame fits the regulation grant's history?

    python3 scripts/hindcast_regulation.py

The regulation grant (or fee) is what is left of the state's frame for the equalisation when the income
equalisation is paid, the same amount per inhabitant in every municipality (lag 2004:773). The frame is the
state's decision, so a forecast needs a rule for years not yet decided. Three are tried against SCB's
outcomes (data/equalisation.json, TAB1981, kr per inhabitant 2005-2026), from every start year 2011-2025
and up to ten years ahead, each using only the start year's own figures:

  fixed     the frame stays fixed in kronor, SKR's assumption: the income equalisation grows with the tax
            base and takes more of the frame every year, so the regulation grant shrinks.
  hold      the regulation grant per inhabitant stays at the start year's amount in kronor.
  taxbase   the frame follows the nation's tax base. The income equalisation's cost is a share of the tax
            base, so the rest is too: the regulation grant per inhabitant grows with the tax base per
            inhabitant. The model's rule (Assumptions.stateFrameFollowsTaxBase, Data.sourcedRevenue).

The nation's tax base per inhabitant is taken from the equalisation itself: the median growth of the income
equalisation per inhabitant among the municipalities that receive it, since that grant is a rate times the
gap between 115 % of the nation's mean tax capacity and the municipality's own. The state's net cost of the
income equalisation, needed only for `fixed`, is 15 % of the mean tax capacity times the county rate; it is
set from Motala's grant and relative tax capacity 2026 (14 734 kr at 87.6 %: 8 066 kr per inhabitant).
Sweden's population is the model's table (Kommunekonomi.Data.SCB), from 2010.

Writes data/regulation-hindcast.json. The state added more than any rule says in 2019-2021 and 2024, so all
three are too low; the question is which is least wrong.
"""
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YEARS = range(2005, 2027)
STARTS = range(2011, 2026)
HORIZONS = (1, 2, 3, 4, 6, 8, 10)
MOTALA = '0583'
MOTALA_CAPACITY_2026, GUARANTEE = 0.876, 1.15


def main():
    data = json.loads((ROOT / 'data/equalisation.json').read_text())
    municipalities = data['municipalities']

    def value(code, year, field):
        row = municipalities[code]['years'].get(str(year))
        return None if row is None else row.get(field)

    index = {YEARS[0]: 1.0}
    for y in YEARS[1:]:
        growth = [value(c, y, 'income') / value(c, y - 1, 'income') for c in municipalities
                  if (value(c, y, 'income') or 0) > 2000 and (value(c, y - 1, 'income') or 0) > 2000]
        index[y] = index[y - 1] * statistics.median(growth)
    regulation = {y: value(MOTALA, y, 'regulation') for y in YEARS}
    assert all(value(c, y, 'regulation') == regulation[y] for c in municipalities for y in YEARS), 'the regulation grant differs between municipalities'
    source = (ROOT / 'modelica/Kommunekonomi.mo').read_text()
    table = re.search(r'constant Real nationalPopulation\[\d+\] = \{([^}]*)\}', source).group(1)
    first = int(re.search(r'constant Integer nationalFirstYear = (\d+)', source).group(1))
    national = {first + i: float(x) for i, x in enumerate(table.replace('\n', ' ').split(','))}
    cost_2026 = (GUARANTEE - 1) * value(MOTALA, 2026, 'income') / (GUARANTEE - MOTALA_CAPACITY_2026)
    cost = {y: cost_2026 * index[y] / index[2026] for y in YEARS}
    # The equalisation of year y uses the population on 1 November of y - 1: the end of y - 1 in the table.
    rules = {
        'fixed': lambda s, t: (cost[s] + regulation[s]) * national[s - 1] / national[t - 1] - cost[t],
        'hold': lambda s, t: regulation[s],
        'taxbase': lambda s, t: regulation[s] * index[t] / index[s],
    }
    summary = {}
    for name, rule in rules.items():
        for h in HORIZONS:
            errors = [rule(s, s + h) - regulation[s + h] for s in STARTS if s + h <= YEARS[-1]]
            summary.setdefault(name, {})[str(h)] = {'cases': len(errors), 'meanError': round(statistics.mean(errors)),
                                                   'meanAbsError': round(statistics.mean(map(abs, errors)))}
    out = {'source': 'scripts/hindcast_regulation.py from data/equalisation.json (SCB TAB1981)',
           'unit': 'kr per inhabitant; error = rule minus outcome',
           'startYears': [STARTS[0], STARTS[-1]], 'outcomes': [YEARS[0], YEARS[-1]],
           'regulationPerInhabitant': regulation,
           'taxCapacityGrowthPercent': {y: round(100 * (index[y] / index[y - 1] - 1), 2) for y in YEARS[1:]},
           'stateCostOfIncomeEqualisation2026': round(cost_2026),
           'rules': {'fixed': "The state's frame fixed in kronor (SKR's assumption)",
                     'hold': 'The regulation grant per inhabitant held in kronor',
                     'taxbase': "The state's frame follows the nation's tax base (the model's rule)"},
           'summary': summary,
           'note': 'One series for the whole country, start years that overlap, and a period in which the state raised the frame '
                   'several times: every rule is too low. hold and taxbase cannot be told apart on the absolute error.'}
    (ROOT / 'data/regulation-hindcast.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    for name in rules:
        print(f'{name:<8}', '  '.join(f"{h}: {summary[name][str(h)]['meanError']:+6d}/{summary[name][str(h)]['meanAbsError']:5d}" for h in HORIZONS))


if __name__ == '__main__':
    main()
