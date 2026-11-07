"""Published forecast vintages, no double-counting, exact annual integration."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from motala_lab import dynamics, macro, historical_dynamics as hist


class MacroTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((dynamics.ROOT/'data/skr-pkv-vintages.json').read_text())

    def test_only_declared_origin_vintage_can_affect_forecast(self):
        before = macro.select_vintage(self.data, 2022, 3)
        changed = deepcopy(self.data)
        for v in changed['vintages']:
            if v['originYear'] != 2022:
                for row in v['rows']:
                    row['laborPercent'] = 999
        self.assertEqual(before, macro.select_vintage(changed, 2022, 3))
        self.assertEqual(before['publicationDate'], '2022-12-15')
        self.assertEqual([r['year'] for r in before['rows']], [2023, 2024, 2025])
        self.assertFalse(before['openingAccountsAvailableAtMacroCutoff'])

    def test_reject_future_publication_and_missing_horizon(self):
        changed = deepcopy(self.data)
        changed['vintages'][2]['publicationDate'] = '2023-02-16'
        with self.assertRaisesRegex(ValueError, 'December vintage'):
            macro.select_vintage(changed, 2022, 1)
        changed = deepcopy(self.data)
        changed['vintages'][2]['rows'][1]['year'] = 2027
        with self.assertRaisesRegex(ValueError, 'Missing forecast horizon'):
            macro.select_vintage(changed, 2022, 3)

    def test_reject_double_indexation(self):
        vintage = macro.select_vintage(self.data, 2022, 1)
        for key in ('wageGrowth', 'priceGrowth', 'pensionGrowth'):
            params = dict(wageGrowth=0, priceGrowth=0, pensionGrowth=0)
            params[key] = .02
            with self.assertRaisesRegex(ValueError, 'zero internal'):
                macro.scenario_source(params, vintage)

    def test_native_varying_cost_path_matches_independent_annual_totals(self):
        vintage = {'rows': [
            {'laborPercent': 7.2, 'otherPercent': 4.5},
            {'laborPercent': 4.2, 'otherPercent': 0.},
            {'laborPercent': -.4, 'otherPercent': -2.}]}
        params = dict(demographyEnabled=False, allowClosure=False, physicalLifeYears=[1e12]*3,
            investment0=0, workInProgress0=0, purchaseCoverage=[0]*3,
            wageGrowth=0, priceGrowth=0, pensionGrowth=0, payroll0=2000, pension0=200,
            otherExpense0=1000)
        with tempfile.TemporaryDirectory(prefix='motala-pkv-integrals-') as tmp:
            rows = dynamics.simulate(macro.scenario_source(params, vintage), 3, Path(tmp))
        expected_personnel = [2200*1.072, 2200*1.072*1.042, 2200*1.072*1.042*.996]
        expected_other = [1045, 1045, 1045*.98]
        for i, annual in enumerate(dynamics.annual_rows(rows, 3)):
            self.assertAlmostEqual(annual['payroll']+annual['pensionExpense'], expected_personnel[i], delta=1e-4)
            self.assertAlmostEqual(annual['otherOperatingExpense'], expected_other[i], delta=1e-4)
        for row in rows:
            self.assertLess(abs(row['balanceResidual']), 1e-4)

    def test_accounting_comparator_preserves_money_identity(self):
        r = next(r for r in hist.load_ledgers()['rows'] if r['year'] == 2022)
        params = json.loads((dynamics.ROOT/'data/historical-protocol.json').read_text())['parameters']
        pred = macro.accounting_projection(r, macro.select_vintage(self.data, 2022, 3), params)
        self.assertAlmostEqual(pred[0]['personnel'], (2009+178.1)*1.072)
        for row in pred:
            self.assertAlmostEqual(row['result'], row['taxAndGrants']-row['netCost']+row['financeNet'])


if __name__ == '__main__':
    unittest.main()
