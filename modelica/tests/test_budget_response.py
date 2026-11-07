"""Budget-response checks use synthetic accounts, never forecast evidence."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('budget_response', ROOT/'motala_lab/budget_response.py')
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)
PROTOCOL = json.loads((ROOT/'data/budget-response-protocol.json').read_text())


def synthetic_accounts(adjustment=0.25):
    # Independent recurrence: manually compute the four differences and one-step
    # base, without calling the implementation under test.
    rows = []
    for year in range(1998, 2026):
        revenue = 100.0 + 2.0*(year-1998)
        if len(rows) < 5:
            cost = 80.0 + year-1998
        else:
            recent = rows[-5:]
            mean_change = sum(recent[i+1]['netCost']-recent[i]['netCost'] for i in range(4))/4
            last = rows[-1]
            gap = last['taxAndGrants']-last['netCost']+last['financeNet']
            cost = last['netCost']+0.5*mean_change+adjustment*gap
        rows.append({'year': year, 'taxAndGrants': revenue, 'netCost': cost,
                     'financeNet': -1.0, 'result': revenue-cost-1.0})
    return rows


class BudgetResponseTests(unittest.TestCase):
    def test_constant_resource_gap_decays_analytically(self):
        rows = [{'year': year, 'taxAndGrants': 110.0, 'netCost': 100.0,
                 'financeNet': 0.0, 'result': 10.0} for year in range(2000, 2005)]
        path = MODEL.forecast(rows, 3, 0.5, PROTOCOL)
        self.assertEqual([r['result'] for r in path], [5.0, 2.5, 1.25])
        self.assertEqual([r['netCost'] for r in path], [105.0, 107.5, 108.75])

    def test_zero_feedback_is_exact_base(self):
        rows = synthetic_accounts()[:5]
        path = MODEL.forecast(rows, 3, 0, PROTOCOL)
        self.assertEqual([r['netCost'] for r in path], [84.5, 84.75, 84.875])
        self.assertEqual([r['taxAndGrants'] for r in path], [109.0, 109.5, 109.75])
        self.assertEqual([r['financeNet'] for r in path], [-1.0]*3)

    def test_known_parameter_recovered_and_bounds_reported(self):
        for adjustment in (0.25, -0.05, 1.2):
            with self.subTest(adjustment=adjustment):
                fitted = MODEL.fit(synthetic_accounts(adjustment), 2019, PROTOCOL)
                self.assertEqual(fitted['status'], 'fitted')
                self.assertAlmostEqual(fitted['unconstrainedLambda'], adjustment)
                self.assertAlmostEqual(fitted['lambda'], max(0, min(1, adjustment)))

    def test_future_outcomes_cannot_change_earlier_predictions(self):
        original = synthetic_accounts()
        changed = deepcopy(original)
        for row in changed:
            if row['year'] > 2012:
                row['netCost'] *= 1.8
                row['taxAndGrants'] *= 2
                row['financeNet'] -= 100
                row['result'] += 200
        first, second = [MODEL.evaluate(rows, PROTOCOL) for rows in (original, changed)]
        for a, b in zip(first['cases'], second['cases']):
            if a['origin'] <= 2012:
                self.assertEqual(a['forecast'], b['forecast'])
        for origin in range(2010, 2013):
            self.assertEqual(first['fits'][str(origin)], second['fits'][str(origin)])

    def test_parameter_is_frozen_before_existing_targets(self):
        rows = synthetic_accounts()
        original = MODEL.fit(rows, 2024, PROTOCOL)
        for row in rows:
            if row['year'] >= 2020:
                row['netCost'] *= 2
        for origin in range(2020, 2025):
            self.assertEqual(MODEL.fit(rows, origin, PROTOCOL), original)
        self.assertTrue(all(p['target'] <= 2019 for p in original['trainingPairs']))

    def test_short_history_fails_gate_without_scores(self):
        rows = [r for r in synthetic_accounts() if r['year'] >= 2017]
        result = MODEL.evaluate(rows, PROTOCOL)
        self.assertEqual(result['status'], 'no_evaluable_cases')
        self.assertEqual(result['cases'], [])
        self.assertEqual(len(result['skipped']), len(PROTOCOL['originYears']))
        self.assertEqual(result['fits']['2024']['status'], 'insufficient_training')

    def test_zero_signal_is_unidentified_not_fitted_zero(self):
        rows = synthetic_accounts()
        for row in rows:
            row['netCost'] = row['taxAndGrants']-1
            row['result'] = 0
        fitted = MODEL.fit(rows, 2019, PROTOCOL)
        self.assertEqual(fitted['status'], 'unidentified_budget_signal')
        self.assertIsNone(fitted['lambda'])

    def test_gaps_never_form_training_transitions_or_base_windows(self):
        rows = [r for r in synthetic_accounts() if r['year'] != 2005]
        fitted = MODEL.fit(rows, 2019, PROTOCOL)
        origins = [pair['origin'] for pair in fitted['trainingPairs']]
        self.assertFalse(set(range(2004, 2010)) & set(origins))

    def test_bookkeeping_residual_not_fitted_and_error_identity_holds(self):
        rows = synthetic_accounts()
        fit_before = MODEL.fit(rows, 2019, PROTOCOL)
        for row in rows:
            row['result'] += 1
        self.assertEqual(MODEL.fit(rows, 2019, PROTOCOL), fit_before)
        result = MODEL.evaluate(rows, PROTOCOL)
        for case in result['cases']:
            e = case['errors']
            if 'netCost' in e:
                self.assertAlmostEqual(e['result'], e['taxAndGrants']-e['netCost']+e['financeNet']
                                       -case['actualAccountingResidual'])

    def test_pairs_components_and_target_coverage_match(self):
        report = MODEL.evaluate(synthetic_accounts(), PROTOCOL)
        main = [c for c in report['cases'] if c['model'] == 'budget_response']
        control = [c for c in report['cases'] if c['model'] == 'identical_base_lambda_zero']
        self.assertEqual([(c['origin'], c['target']) for c in main],
                         [(c['origin'], c['target']) for c in control])
        self.assertEqual(len([c for c in main if c['origin'] >= 2020]), 12)
        for a, b in zip(main, control):
            for key in ('taxAndGrants', 'financeNet'):
                self.assertEqual(a['forecast'][key], b['forecast'][key])

    def test_valid_last_target_not_discarded_for_invalid_later_extrapolation(self):
        rows = synthetic_accounts()
        row = next(r for r in rows if r['year'] == 2024)
        row['netCost'] = 20.0
        row['result'] = row['taxAndGrants']-20.0+row['financeNet']
        protocol = dict(PROTOCOL, originYears=[2024])
        # The zero-feedback trend is still positive in 2025, but becomes
        # negative beyond the experiment's final target. Those later years
        # must not invalidate the valid one-year paired comparison.
        history = [r for r in rows if r['year'] <= 2024]
        with self.assertRaises(ValueError):
            MODEL.forecast(history, 3, 0.0, protocol)
        report = MODEL.evaluate(rows, protocol)
        self.assertEqual(len(report['cases']), 4)
        self.assertTrue(all(c['target'] == 2025 and c['horizon'] == 1 for c in report['cases']))

    def test_failed_long_horizon_does_not_remove_valid_shorter_cases(self):
        rows = synthetic_accounts()
        base_cost = next(r['netCost'] for r in rows if r['year'] == 2018)
        row = next(r for r in rows if r['year'] == 2022)
        row['netCost'] = base_cost/6
        row['result'] = row['taxAndGrants']-row['netCost']+row['financeNet']
        report = MODEL.evaluate(rows, dict(PROTOCOL, originYears=[2022]))
        self.assertEqual(len(report['cases']), 8)
        self.assertEqual({c['horizon'] for c in report['cases']}, {1, 2})
        self.assertEqual(report['skipped'][0]['horizon'], 3)
        self.assertEqual(report['skipped'][0]['reason'], 'invalid_forecast')
        self.assertIn('identical_base_lambda_zero', report['skipped'][0]['failures'])

    def test_invalid_or_duplicate_accounts_rejected(self):
        for bad in (None, float('nan'), float('inf'), True):
            rows = synthetic_accounts()
            rows[0]['netCost'] = bad
            with self.subTest(value=bad), self.assertRaises(ValueError):
                MODEL.evaluate(rows, PROTOCOL)
        rows = synthetic_accounts()
        rows[1]['year'] = rows[0]['year']
        with self.assertRaises(ValueError):
            MODEL.evaluate(rows, PROTOCOL)


if __name__ == '__main__':
    unittest.main()
