"""Historical information boundaries and native reproducibility, not curve fitting."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from statistics import mean

from motala_lab import historical_dynamics as hist


class HistoricalInputsTests(unittest.TestCase):
    def setUp(self):
        self.data = hist.load_ledgers()
        self.protocol = json.loads((hist.ROOT/'data/historical-protocol.json').read_text())

    def test_unknown_wip_is_not_silently_zero(self):
        with self.assertRaisesRegex(ValueError, 'explicit scenario'):
            hist.opening_inputs(self.data, 2020, self.protocol)
        p, audit = hist.opening_inputs(self.data, 2020, self.protocol, missing_wip_fraction=.1)
        self.assertTrue(audit['assumedWIP'])
        self.assertAlmostEqual(p['assets0']+p['workInProgress0'], 2224.7)
        self.assertEqual(p['workInProgress0'], .1*2224.7)

    def test_historical_initials_use_their_own_ledger_and_reconcile_demography(self):
        p, audit = hist.opening_inputs(self.data, 2022, self.protocol)
        self.assertFalse(audit['assumedWIP'])
        self.assertAlmostEqual(p['assets0'], 2305.3)
        self.assertEqual(p['workInProgress0'], 114.7)
        self.assertEqual(p['payroll0'], 2009)
        self.assertEqual(p['cash0'], 85.8)
        self.assertAlmostEqual(sum(p['p0']), 43728)
        self.assertAlmostEqual(sum(a*b for a, b in zip(p['p0'], p['deathRates'])), 420)
        self.assertAlmostEqual(sum(p['migration0']), 98)
        self.assertEqual(p['sectorShares'], [1/3]*3)

    def test_no_future_period_can_change_an_earlier_model_source(self):
        for origin in (2020, 2021, 2022, 2023, 2024):
            changed = deepcopy(self.data)
            for row in changed['rows']:
                if row['year'] > origin:
                    for key, value in list(row.items()):
                        if isinstance(value, (int, float)) and key != 'year':
                            row[key] = value*7+999
                    row['cohortsReported'] = [999]*5
            before = hist.opening_inputs(self.data, origin, self.protocol, missing_wip_fraction=0)
            after = hist.opening_inputs(changed, origin, self.protocol, missing_wip_fraction=0)
            self.assertEqual(before, after)
            self.assertEqual(hist.dynamics.scenario_source(parameters=before[0]),
                             hist.dynamics.scenario_source(parameters=after[0]))

    def test_aggregate_comparisons_keep_original_precision_and_rounding_visible(self):
        rows = {r['year']: r for r in hist.aggregate_observations(self.data)['rows']}
        self.assertEqual(rows[2021]['result'], 61.7)
        self.assertEqual(rows[2025]['taxAndGrants'], 3317)
        self.assertEqual(rows[2025]['accountingAdjustment'], 1)
        self.assertEqual(rows[2023]['financeNet'], -6)

    def test_older_aggregate_source_does_not_replace_selected_versions(self):
        older = json.loads((hist.ROOT/'data/history-2017.json').read_text())
        rows = hist.aggregate_observations(self.data, older=older)['rows']
        self.assertEqual(rows[0]['year'], 2017)
        self.assertAlmostEqual(rows[0]['taxAndGrants'], 2427.)
        self.assertNotIn('cohorts', rows[0])
        self.assertEqual([r for r in rows if r['year'] >= 2018],
                         hist.aggregate_observations(self.data)['rows'])
        older['rows'][0]['year'] = 2018
        with self.assertRaisesRegex(ValueError, 'replace an existing'):
            hist.aggregate_observations(self.data, older=older)

    def test_mean_replay_has_no_future_leakage_and_keeps_ledger_rounding(self):
        observations = hist.aggregate_observations(self.data,
            older=json.loads((hist.ROOT/'data/history-2017.json').read_text()))
        before = hist.aggregate_replay(observations, [2022], [1, 2, 3])
        changed = deepcopy(observations)
        for row in changed['rows']:
            if row['year'] > 2022:
                for key in hist.METRICS:
                    row[key] += 1000
        after = hist.aggregate_replay(changed, [2022], [1, 2, 3])
        for a, b in zip(before['cases'], after['cases']):
            self.assertEqual(a['predictions'], b['predictions'])
            self.assertNotEqual(a['actual'], b['actual'])
        training = [r for r in observations['rows'] if r['year'] <= 2022]
        predicted = before['cases'][0]['predictions']['historical_mean']
        self.assertAlmostEqual(predicted['result'], mean(r['result'] for r in training))
        # Averaging a linear ledger preserves any explicitly recorded rounding residual.
        full = hist.aggregate_predictions(observations['rows'], 1, include_mean=True)['historical_mean'][0]
        self.assertAlmostEqual(full['result']-full['taxAndGrants']+full['netCost']-full['financeNet'],
            mean(r.get('accountingAdjustment', 0) for r in observations['rows']))

    def test_demographic_source_revision_is_not_hidden(self):
        changed = deepcopy(self.data)
        row = next(r for r in changed['rows'] if r['year'] == 2022)
        for key in tuple(row):
            if key == 'sourceId' or key.endswith('SourceId'):
                row[key] = '2022'
        self.assertFalse(hist.opening_inputs(changed, 2022, self.protocol)[1]['sourceRevisions'])
        row['demographicSourceId'] = '2025'
        self.assertTrue(hist.opening_inputs(changed, 2022, self.protocol)[1]['sourceRevisions'])

    def test_unexplained_accounting_error_is_rejected(self):
        changed = deepcopy(self.data)
        changed['rows'][0]['tax'] += 100
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'bad.json'
            hist.dump(path, changed)
            with self.assertRaisesRegex(ValueError, 'ledger residual'):
                hist.load_ledgers(path)

    def test_native_future_outcome_mutation_does_not_change_earlier_prediction(self):
        changed = deepcopy(self.data)
        for row in changed['rows']:
            if row['year'] > 2022:
                for key in ('result', 'payroll', 'tax', 'grants', 'netCost', 'debt', 'cash', 'workInProgress'):
                    row[key] += 1000
        with tempfile.TemporaryDirectory(prefix='motala-history-leakage-') as temp:
            a, _ = hist.predict_origin(self.data, 2022, 1, self.protocol, Path(temp)/'a')
            b, _ = hist.predict_origin(changed, 2022, 1, self.protocol, Path(temp)/'b')
            for key in hist.METRICS+hist.COMPONENTS:
                self.assertAlmostEqual(a[0][key], b[0][key], places=8, msg=key)
            # A genuine opening change must affect the run, so this is not a cached result.
            changed['rows'][2]['tax'] += 10
            c, _ = hist.predict_origin(changed, 2022, 1, self.protocol, Path(temp)/'c')
            self.assertGreater(c[0]['result']-a[0]['result'], 9)


if __name__ == '__main__':
    unittest.main()
