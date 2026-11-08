"""Unit, calendar, information-boundary and independent algebra checks."""
from copy import deepcopy
import json
import unittest

from motala_lab import dynamics, historical_dynamics, macro, revenue_bridge as bridge


def november(year, value):
    return {'municipality': '0583', 'referenceDate': f'{year}-11-01',
            'unit': 'persons', 'value': value}


class RevenueBridgeTests(unittest.TestCase):
    def setUp(self):
        root = dynamics.ROOT / 'data'
        self.local = json.loads((root/'motala-revenue-components.json').read_text())
        self.national = json.loads((root/'skr-revenue-vintages.json').read_text())
        self.costs = json.loads((root/'skr-pkv-vintages.json').read_text())
        self.ledgers = historical_dynamics.load_ledgers()

    def test_all_openings_reconcile_and_do_not_read_future_accounts(self):
        for origin in range(2020, 2025):
            ledger = next(r for r in self.ledgers['rows'] if r['year'] == origin)
            before = bridge.opening_components(self.local, ledger)
            changed = deepcopy(self.local)
            for row in changed['rows']:
                if row['year'] > origin:
                    row['taxComponents'] = {'future': 999999}
                    row['grantComponents'] = {'future': -999999}
            self.assertEqual(before, bridge.opening_components(changed, ledger))
        self.assertEqual(self.local['rows'][1]['grantRoundingResidual'], .1)
        self.assertEqual(self.local['rows'][3]['grantComponents']['otherGeneralGrants'], 8)

    def test_reconciliation_rejects_mismatched_totals_missing_parts_and_bad_units(self):
        ledger = self.ledgers['rows'][0]
        for mutation in ('rounding', 'balancing_plug', 'precision', 'missing',
                         'unexpected', 'duplicate', 'scope', 'unit', 'nan'):
            with self.subTest(mutation=mutation):
                changed = deepcopy(self.local)
                row = changed['rows'][0]
                if mutation == 'rounding':
                    row['grantRoundingResidual'] += .1
                elif mutation == 'balancing_plug':
                    row['grantComponents']['incomeEqualisation'] += 1000
                    row['grantRoundingResidual'] -= 1000
                elif mutation == 'precision':
                    row['reportingPrecisionMnkr'] = 1000
                elif mutation == 'missing':
                    del row['taxComponents']['priorYearSettlementDifference']
                elif mutation == 'unexpected':
                    row['grantComponents']['undisclosedGrant'] = 0
                elif mutation == 'duplicate':
                    changed['rows'].append(deepcopy(row))
                elif mutation == 'scope':
                    row['scope'] = 'koncernen'
                elif mutation == 'unit':
                    changed['unit'] = 'tkr'
                else:
                    row['taxComponents']['preliminaryTax'] = float('nan')
                with self.assertRaises(ValueError):
                    bridge.opening_components(changed, ledger)

    def test_vintage_selection_preserves_calendar_and_nulls(self):
        for origin in range(2020, 2025):
            cost = macro.select_vintage(self.costs, origin, 3)
            vintage = bridge.select_vintage(self.national, origin, 3, cost)
            self.assertEqual(vintage['rows'][1]['fiscalPopulationReferenceDate'], f'{origin}-11-01')
            self.assertEqual(vintage['rows'][1]['novemberReferenceDate'], f'{origin+1}-11-01')
            self.assertIsNone(vintage['rows'][2]['currentYearSettlementPerCapita'])
            self.assertIsNone(vintage['rows'][2]['governmentMeanTaxCapacity'])
            changed = deepcopy(self.national)
            for other in changed['vintages']:
                if other['originYear'] != origin:
                    other['rows'] = []
            self.assertEqual(vintage, bridge.select_vintage(changed, origin, 3, cost))

    def test_vintage_rejects_future_releases_and_false_later_observations(self):
        cost = macro.select_vintage(self.costs, 2020, 3)
        for mutation in ('publication', 'circular', 'missing', 'duplicate', 'units',
                         'source', 'locator', 'future_settlement'):
            with self.subTest(mutation=mutation):
                changed = deepcopy(self.national)
                vintage = changed['vintages'][0]
                if mutation == 'publication':
                    vintage['publicationDate'] = '2021-01-01'
                elif mutation == 'circular':
                    vintage['circular'] = '20:39'
                elif mutation == 'missing':
                    vintage['rows'].pop()
                elif mutation == 'duplicate':
                    vintage['rows'][1]['year'] = 2020
                elif mutation == 'units':
                    changed['unitCodes']['regulation'] = 'mnkr'
                elif mutation == 'source':
                    del vintage['source']
                elif mutation == 'locator':
                    del vintage['locators']['settlements']
                else:
                    vintage['rows'][2]['currentYearSettlementPerCapita'] = 0
                with self.assertRaises(ValueError):
                    bridge.select_vintage(changed, 2020, 3, cost)

    def test_settlements_have_separate_populations_and_do_not_scale_with_local_rate(self):
        # 5,000 mnkr taxable income, 21% rate; +20 mnkr settlement and -3 mnkr revision.
        args = (2024, 5000, .21, 400, -100, november(2023, 50000), november(2022, 30000))
        before = bridge.recognised_tax(*args)
        after = bridge.recognised_tax(*args[:2], .22, *args[3:])
        self.assertAlmostEqual(before['tax'], 1067)
        self.assertAlmostEqual(after['tax']-before['tax'], 50)
        for key in bridge.TAX_PARTS[1:]:
            self.assertEqual(before[key], after[key])
        wrong_date = november(2023, 50000) | {'referenceDate': '2023-12-31'}
        with self.assertRaisesRegex(ValueError, 'November'):
            bridge.recognised_tax(*args[:5], wrong_date, args[-1])

    def test_equalisation_recipient_payer_and_marginal_net_revenue(self):
        pop = november(2023, 10000)
        settings = dict(recipient_rate=.19, payer_rate=.17)
        # Guaranteed taxable base 1.15*200,000*10,000 = 2,300 mnkr.
        self.assertAlmostEqual(bridge.income_equalisation(2024, 2000, 200000, pop, **settings), 57)
        self.assertAlmostEqual(bridge.income_equalisation(2024, 2400, 200000, pop, **settings), -17)
        self.assertAlmostEqual(bridge.income_equalisation(2024, 2300, 200000, pop, **settings), 0)
        before = bridge.preliminary_tax(2000, .21)+bridge.income_equalisation(2024, 2000, 200000, pop, **settings)
        after = bridge.preliminary_tax(2100, .21)+bridge.income_equalisation(2024, 2100, 200000, pop, **settings)
        # 100 mnkr more taxable income: 21 more own tax, 19 less equalisation.
        self.assertAlmostEqual(after-before, 2)
        self.assertAlmostEqual(bridge.regulation_grant(2024, -200, pop), -2)

    def test_constant_relative_capacity_identity_is_consistent_for_tax_and_equalisation(self):
        original = bridge.income_equalisation(2024, 2000, 200000, november(2023, 10000),
                                              recipient_rate=.19, payer_rate=.17)
        factor = (220000/200000)*(9000/10000)
        changed = bridge.income_equalisation(2025, 2000*factor, 220000, november(2024, 9000),
                                             recipient_rate=.19, payer_rate=.17)
        self.assertAlmostEqual(changed, original*factor)
        self.assertAlmostEqual(bridge.preliminary_tax(2000*factor, .21), 420*factor)

    def test_reject_nonfinite_rates_boolean_populations_and_percentage_points(self):
        for bad in (True, float('nan'), float('inf'), None, 21.7, -.01):
            with self.assertRaises(ValueError):
                bridge.preliminary_tax(1000, bad)
        with self.assertRaises(ValueError):
            bridge.regulation_grant(2024, 200, november(2023, True))
        with self.assertRaises(ValueError):
            bridge.regulation_grant(2024, 200, november(2022, 10000))


if __name__ == '__main__':
    unittest.main()
