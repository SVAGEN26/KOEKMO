"""The base-year records in Motala.mo must agree with the project's source data files."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = (ROOT / 'modelica/Motala.mo').read_text()
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
        self.assertGreaterEqual(years[-1], 2055, 'the browser needs 30 years after 2025')


if __name__ == '__main__':
    unittest.main()
