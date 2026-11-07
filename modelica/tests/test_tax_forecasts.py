"""Tax-only information boundaries and a native independent ledger check."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from motala_lab import dynamics, historical_dynamics as hist, macro, tax_forecasts


class TaxForecastTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((dynamics.ROOT/'data/skr-tax-vintages.json').read_text())
        self.costs = json.loads((dynamics.ROOT/'data/skr-pkv-vintages.json').read_text())
        self.cost = macro.select_vintage(self.costs, 2022, 3)

    def test_declared_vintages_and_future_information_boundary(self):
        for origin in range(2020, 2025):
            cost = macro.select_vintage(self.costs, origin, 3)
            before = tax_forecasts.select_vintage(self.data, origin, 3, cost)
            changed = deepcopy(self.data)
            for vintage in changed['vintages']:
                if vintage['originYear'] != origin:
                    vintage['rows'][0]['taxBasePercent'] = 999
            self.assertEqual(before, tax_forecasts.select_vintage(changed, origin, 3, cost))
            self.assertEqual([r['year'] for r in before['rows']], list(range(origin+1, origin+4)))
        self.assertEqual([r['taxBasePercent'] for r in self.data['vintages'][2]['rows']], [3.6, 4.4, 4.3])

    def test_reject_wrong_definition_future_date_and_mismatched_circular(self):
        for field, value in [('definition', 'real_tax_base'), ('unit', 'fraction')]:
            changed = deepcopy(self.data)
            changed[field] = value
            with self.assertRaises(ValueError):
                tax_forecasts.select_vintage(changed, 2022, 3, self.cost)
        for field, value in [('publicationDate', '2023-01-01'), ('circular', '22:37')]:
            changed = deepcopy(self.data)
            changed['vintages'][2][field] = value
            with self.assertRaises(ValueError):
                tax_forecasts.select_vintage(changed, 2022, 3, self.cost)

    def test_reject_missing_duplicate_and_invalid_rates(self):
        for value in [float('nan'), float('inf'), -100, True, '3.6']:
            changed = deepcopy(self.data)
            changed['vintages'][2]['rows'][0]['taxBasePercent'] = value
            with self.assertRaises(ValueError):
                tax_forecasts.select_vintage(changed, 2022, 3, self.cost)
        for operation in ('missing', 'duplicate_year', 'duplicate_origin'):
            changed = deepcopy(self.data)
            if operation == 'missing':
                changed['vintages'][2]['rows'].pop()
            elif operation == 'duplicate_year':
                changed['vintages'][2]['rows'][1]['year'] = 2023
            else:
                changed['vintages'].append(deepcopy(changed['vintages'][2]))
            with self.assertRaises(ValueError):
                tax_forecasts.select_vintage(changed, 2022, 3, self.cost)

    def test_accounting_changes_only_tax_and_preserves_original(self):
        opening = next(r for r in hist.load_ledgers()['rows'] if r['year'] == 2022)
        params = json.loads((dynamics.ROOT/'data/historical-protocol.json').read_text())['parameters']
        original = macro.accounting_projection(opening, self.cost, params)
        saved = deepcopy(original)
        vintage = tax_forecasts.select_vintage(self.data, 2022, 3, self.cost)
        changed = tax_forecasts.accounting_projection(original, opening['tax'], vintage)
        expected = [2137.6*1.036, 2137.6*1.036*1.044, 2137.6*1.036*1.044*1.043]
        for i, (before, after) in enumerate(zip(original, changed)):
            self.assertAlmostEqual(after['tax'], expected[i])
            for key in before.keys()-{'tax', 'taxAndGrants', 'result'}:
                self.assertEqual(before[key], after[key])
            self.assertAlmostEqual(after['result']-before['result'], after['tax']-before['tax'])
            self.assertAlmostEqual(after['result'], after['taxAndGrants']-after['netCost']+after['financeNet'])
        self.assertEqual(original, saved)

    def test_reject_binding_that_would_replace_grants(self):
        vintage = tax_forecasts.select_vintage(self.data, 2022, 3, self.cost)
        params = dict(wageGrowth=0, priceGrowth=0, pensionGrowth=0)
        for flags in ({}, {'useExternalTax': True, 'useExternalRevenue': True}):
            with self.assertRaisesRegex(ValueError, 'internal grants'):
                macro.scenario_source(params|flags, self.cost, tax_vintage=vintage)

    def test_native_tax_integrals_with_unchanged_demographic_grant_path(self):
        vintage = tax_forecasts.select_vintage(self.data, 2022, 3, self.cost)
        for row, rate in zip(vintage['rows'], [10, -5, 0]):
            row['taxBasePercent'] = rate
        params = dict(tax0=100, grants0=50, payroll0=20, pension0=2, otherExpense0=10,
            operatingRevenue0=2, assets0=30, depreciation0=3, workInProgress0=0,
            investment0=0, interestRate0=0, debt0=0, cash0=0,
            financialIncome=0, otherFinancialExpense=0, taxBaseGrowth=.035, grantGrowth=.02,
            wageGrowth=0, priceGrowth=0, pensionGrowth=0,
            migration0=[0, 0, 0, 100, 0], allowClosure=False)
        with tempfile.TemporaryDirectory(prefix='motala-tax-only-') as tmp:
            original = dynamics.simulate(macro.scenario_source(params, self.cost), 3, Path(tmp)/'original')
            changed = dynamics.simulate(macro.scenario_source(params|{'useExternalTax': True},
                self.cost, tax_vintage=vintage), 3, Path(tmp)/'changed')
        original = dynamics.annual_rows(original, 3)
        annual = dynamics.annual_rows(changed, 3)
        for before, after, expected in zip(original, annual, [110, 104.5, 104.5]):
            self.assertAlmostEqual(after['tax'], expected, delta=1e-4)
            for key in ('grants', 'population', 'payroll', 'pensionExpense', 'otherOperatingExpense',
                        'operatingRevenue', 'depreciation'):
                self.assertAlmostEqual(before[key], after[key], delta=1e-4)
            self.assertAlmostEqual(after['result']-before['result'], after['tax']-before['tax'], delta=1e-4)
        self.assertNotAlmostEqual(original[0]['grants'], original[1]['grants'], places=2)
        self.assertNotAlmostEqual(original[0]['population'], original[1]['population'], places=2)
        for row in changed:
            self.assertLess(abs(row['balanceResidual']), 1e-4)


if __name__ == '__main__':
    unittest.main()
