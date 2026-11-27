"""The base-year records in Motala.mo must agree with the project's source data files."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = (ROOT / 'modelica/Kommunekonomi/Municipalities/Motala.mo').read_text()
HISTORY = {r['year']: r for r in json.loads((ROOT / 'data/history.json').read_text())['rows']}
ACCOUNTS = {r['year']: r for r in json.loads((ROOT / 'data/operating-accounts-history.json').read_text())['rows']}
BASELINE = json.loads((ROOT / 'data/baseline.json').read_text())


def record(name):
    """Fields of `constant BaseYear <name> = BaseYear(...)` as numbers or nested lists."""
    body = re.search(rf'constant BaseYear {name} = BaseYear\((.*?)\)\s*"', MODEL, re.S).group(1)
    fields = {}
    for key, value in re.findall(r'(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|-?[\d.]+)', body):
        fields[key] = json.loads(value.replace('{', '[').replace('}', ']'))
    return fields


class BaseYears(unittest.TestCase):
    def check(self, name, year):
        r = record(name)
        self.assertEqual(r['year'], year)
        for k, y in enumerate((year - 2, year - 1, year)):
            self.assertEqual(r['cohorts'][k], HISTORY[y]['population'], f'{name} cohorts {y}')
            self.assertEqual(r['reportedPopulation'][k], HISTORY[y]['reportedTotal'], f'{name} total {y}')
        self.assertEqual(r['births'], [HISTORY[year - 1]['births'], HISTORY[year]['births']])
        self.assertEqual(r['deaths'], HISTORY[year]['deaths'])
        self.assertEqual(r['debt'], HISTORY[year]['debt'])
        self.assertEqual(r['openingDebt'], HISTORY[year - 1]['debt'], f'{name}: opening debt is last year\'s closing debt')
        self.assertEqual(r['investment'], HISTORY[year]['investment'])
        a = ACCOUNTS[year]
        for model_key, data_key in [('payroll', 'payrollExcludingPensions'), ('pension', 'pensionExpense'),
                                    ('otherOperatingExpense', 'otherOperatingExpense'),
                                    ('operatingRevenue', 'operatingRevenue'),
                                    ('netCostRoundingAdjustment', 'netCostRoundingAdjustment')]:
            self.assertEqual(r[model_key], a[data_key], f'{name} {model_key}')
        net = r['payroll'] + r['pension'] + r['otherOperatingExpense'] - r['operatingRevenue'] + r['netCostRoundingAdjustment']
        self.assertEqual(net, a['netOperatingCost'])
        self.assertEqual(net + r['depreciation'], HISTORY[year]['netCost'], f'{name}: net cost incl. depreciation')
        finance_net = r['financialIncome'] - r['interestExpense'] - r['otherFinancialExpense']
        self.assertEqual(finance_net, HISTORY[year]['financeNet'], f'{name}: financial net')
        result = r['tax'] + r['grants'] - HISTORY[year]['netCost'] + finance_net
        self.assertLessEqual(abs(result - HISTORY[year]['result']), 1, f'{name}: result reconciles within rounding')

    def test_2025_matches_sources(self):
        self.check('motala2025', 2025)
        r = record('motala2025')
        for model_key, base_key in [('tax', 'tax'), ('grants', 'grants'), ('cash', 'cash'), ('assets', 'assets'),
                                    ('depreciation', 'depreciation'), ('financialIncome', 'financialIncome'),
                                    ('interestExpense', 'interestExpense'),
                                    ('otherFinancialExpense', 'otherFinancialExpense'), ('taxRate', 'taxRate')]:
            self.assertEqual(r[model_key], BASELINE[base_key], model_key)

    def test_2024_matches_sources(self):
        self.check('motala2024', 2024)

    def test_2020_to_2023_match_ledgers_and_scb(self):
        """Base years for the hindcasts: money from the annual-report ledgers, people from SCB."""
        ledgers = {r['year']: r for r in json.loads((ROOT / 'research/data/annual-ledgers.json').read_text())['rows']}
        scb = json.loads((ROOT / 'data/downloads/20261108T124756Z/motala-population-2015-2024.json').read_text())
        groups = {}
        for row in scb['data']:
            age, year = row['key'][2], int(row['key'][4])
            a = min(int(age.rstrip('+')), 100)
            g = 0 if a <= 6 else 1 if a <= 15 else 2 if a <= 18 else 3 if a <= 64 else 4
            groups.setdefault(year, [0] * 5)[g] += int(row['values'][0])
        # Loans including the short-term part, Årsredovisning 2022 p. 6 and 32; 2023 from report 2023.
        debt = {2019: 801.3, 2020: 788.0, 2021: 830.2, 2022: 664.5, 2023: 663}
        for year in range(2020, 2024):
            r, o = record(f'motala{year}'), ledgers[year]
            self.assertEqual(r['year'], year)
            for k, y in enumerate((year - 2, year - 1, year)):
                self.assertEqual(r['cohorts'][k], groups[y], f'{year} cohorts {y}')
                self.assertEqual(r['reportedPopulation'][k], sum(groups[y]))
            self.assertEqual(r['births'][1], o['births'])
            self.assertEqual(r['deaths'], o['deaths'])
            self.assertEqual((r['debt'], r['openingDebt']), (debt[year], debt[year - 1]))
            for key in ('tax', 'grants', 'payroll', 'pension', 'operatingRevenue', 'depreciation', 'financialIncome',
                        'investment', 'cash'):
                self.assertEqual(r[key], o[key], f'{year} {key}')
            self.assertEqual(r['otherOperatingExpense'], o['otherExpense'])
            self.assertEqual(r['interestExpense'], o['interest'])
            self.assertAlmostEqual(r['interestExpense'] + r['otherFinancialExpense'], o['financialExpense'], places=6)
            net = (r['payroll'] + r['pension'] + r['otherOperatingExpense'] - r['operatingRevenue']
                   + r['netCostRoundingAdjustment'] + r['depreciation'])
            self.assertAlmostEqual(net, o['netCost'], places=6, msg=f'{year} net cost')
            result = r['tax'] + r['grants'] - net + r['financialIncome'] - r['interestExpense'] - r['otherFinancialExpense']
            self.assertAlmostEqual(result, o['result'], places=6, msg=f'{year} result')


    def test_grant_components_match_the_notes(self):
        """Note 7 of each annual report (research/data); SCB's amounts per inhabitant agree (data/equalisation.json)."""
        notes = {r['year']: r['grantComponents'] for r in json.loads((ROOT / 'research/data/motala-revenue-components.json').read_text())['rows']}
        notes[2025] = json.loads((ROOT / 'research/data/revenue-component-targets-2025.json').read_text())['rows'][0]['grantComponents']
        scb = json.loads((ROOT / 'data/equalisation.json').read_text())['municipalities']['0583']['years']
        for year in range(2020, 2026):
            r, n = record(f'motala{year}'), notes[year]
            self.assertEqual(r['grantComponents'], [n['incomeEqualisation'], n['costEqualisation'], n['regulationGrant'],
                                                    n['lssEqualisation'], n['propertyFee']], year)
            self.assertGreaterEqual(r['grants'] - sum(r['grantComponents']), 0, f'{year}: other general grants')
            settlements = {r['year']: r['taxComponents'] for r in json.loads((ROOT / 'research/data/motala-revenue-components.json').read_text())['rows']}
            settlements[2025] = json.loads((ROOT / 'research/data/revenue-component-targets-2025.json').read_text())['rows'][0]['taxComponents']
            self.assertEqual(r['priorYearSettlement'], settlements[year]['priorYearSettlementDifference'], f'{year}: prior-year settlement')
            # SCB per inhabitant times the population a year earlier (31 December; SCB uses 1 November).
            population = r['reportedPopulation'][1]
            for k, key in [(0, 'income'), (2, 'regulation')]:
                self.assertAlmostEqual(scb[str(year)][key] * population / 1e6, r['grantComponents'][k], delta=2, msg=f'{year} {key}')


    def test_relative_tax_capacity_is_scbs(self):
        """Skattekraft i förhållande till riket för basåret och året efter (data/tax-capacity.json, SCB SkatteKraft)."""
        capacity = json.loads((ROOT / 'data/tax-capacity.json').read_text())['municipalities']['0583']
        for year in range(2020, 2026):
            self.assertEqual(record(f'motala{year}')['relativeTaxCapacity'],
                             [round(capacity[str(year)]['relative'], 4), round(capacity[str(year + 1)]['relative'], 4)], year)

    def test_next_years_equalisation_is_scbs(self):
        """Utjämningen per invånare året efter basåret, som SCB publicerar i december under basåret (data/equalisation.json)."""
        eq = json.loads((ROOT / 'data/equalisation.json').read_text())['municipalities']['0583']['years']
        for year in range(2020, 2026):
            e = eq[str(year + 1)]
            self.assertEqual(record(f'motala{year}')['equalisationNextYear'], [round(e[k]) for k in ('income', 'cost', 'regulation', 'lss')], year)

    def test_sector_weights_come_from_kolada(self):
        """The base year's sector shares are Kolada's (data/sector-costs.json); the site's baseline uses the same for 2025."""
        sectors = json.loads((ROOT / 'data/sector-costs.json').read_text())['years']
        for year in range(2020, 2026):
            r, k = record(f'motala{year}'), sectors[str(year)]
            self.assertEqual(r['sectorShares'], [round(k['shares'][x], 4) for x in ('education', 'elderly', 'other')], year)
            self.assertEqual(r['educationShares'], [round(x, 4) for x in k['educationSplit']], year)
        r, a = record('motala2025'), BASELINE['assumptions']
        net = r['payroll'] + r['pension'] + r['otherOperatingExpense'] - r['operatingRevenue'] + r['netCostRoundingAdjustment']
        for model, site in zip([x / sum(r['sectorShares']) * net for x in r['sectorShares']], a['sectorCosts']):
            self.assertAlmostEqual(model, site, places=9)
        for model, site in zip([x / sum(r['educationShares']) for x in r['educationShares']], a['educationWeights']):
            self.assertAlmostEqual(model, site, places=12)


class Budgets(unittest.TestCase):
    def test_budget_2026_matches_the_data_file(self):
        budget = json.loads((ROOT / 'data/municipal-budgets.json').read_text())['budgets'][0]
        body = re.search(r'constant Budget budget2026 = Budget\((.*?)\)\s*"', MODEL, re.S).group(1)
        fields = {k: json.loads(v.replace('{', '[').replace('}', ']'))
                  for k, v in re.findall(r'(\w+)\s*=\s*(\{[^}]*\}|\d+)', body)}
        self.assertEqual(fields['year'], budget['budget'])
        for key in ('tax', 'grants', 'netCost', 'depreciation', 'financialIncome', 'financialCost', 'result',
                    'investment', 'operatingCash', 'newLoans'):
            self.assertEqual(fields[key], budget[key], key)
        for i in range(3):  # the budget's own statements add up
            parts = (budget['tax'][i] + budget['grants'][i] - budget['netCost'][i] - budget['depreciation'][i]
                     + budget['financialIncome'][i] - budget['financialCost'][i])
            self.assertEqual(parts, budget['result'][i])
            self.assertEqual(budget['result'][i] + budget['depreciation'][i], budget['operatingCash'][i])


class NationalPopulation(unittest.TestCase):
    def test_baseline_carries_the_same_series_as_the_data_file(self):
        national = json.loads((ROOT / 'data/national-population.json').read_text())
        self.assertEqual(BASELINE['nationalPopulation']['population'], national['population'])
        years = sorted(int(y) for y in national['population'])
        self.assertEqual(years, list(range(years[0], years[-1] + 1)), 'one value per year, no gaps')
        self.assertLessEqual(years[0], 2019)
        self.assertGreaterEqual(years[-1], 2055, 'SCB projects to 2070; the browser extends the last growth after that')


if __name__ == '__main__':
    unittest.main()
