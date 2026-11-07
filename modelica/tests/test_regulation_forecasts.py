"""Information boundaries, category transfer and signed native grant accounting."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from motala_lab import dynamics, historical_dynamics as hist, macro, revenue_bridge
from motala_lab import normalized_revenue, settlement_forecasts, regulation_forecasts as regulation


class RegulationTests(unittest.TestCase):
    def setUp(self):
        def read(name):
            return json.loads((dynamics.ROOT/'data'/name).read_text())
        self.ledgers = hist.load_ledgers()
        self.components = read('motala-revenue-components.json')
        self.national = read('skr-revenue-vintages.json')
        self.costs = read('skr-pkv-vintages.json')
        self.events = read('motala-noted-events.json')
        self.protocol = read('historical-protocol-tax.json')

    def path(self, origin=2020, policy='costbase'):
        params, audit = hist.opening_inputs(self.ledgers, origin, self.protocol,
            missing_wip_fraction=0, event_data=self.events, event_policy=policy)
        cost = macro.select_vintage(self.costs, origin, 3)
        vintage = revenue_bridge.select_vintage(self.national, origin, 3, cost)
        path = normalized_revenue.prepare(self.components, audit['openingLedger'], params, vintage)
        path = settlement_forecasts.prepare(path, audit['openingLedger'])
        return path, audit['openingLedger']

    def test_constant_local_population_and_category_transfer_under_both_policies(self):
        for policy, anchor in [('costbase', 760.5), ('no-repeat', 678.4)]:
            parent, ledger = self.path(policy=policy)
            before = deepcopy(parent)
            path = regulation.prepare(parent, ledger, self.components)
            forecast = path['regulationForecast']
            self.assertAlmostEqual(path['grantAnchor0'], anchor)
            self.assertAlmostEqual(forecast['parentInheritedGrantAnchor'], anchor-491)
            self.assertEqual(forecast['transferredRefugeeGrant0'], 11.2)
            self.assertEqual(forecast['regulationGrant0'], 44.7)
            self.assertEqual(forecast['populationProxy']['referenceDate'], '2020-12-31')
            self.assertEqual([r['fiscalPopulationReferenceDate'] for r in forecast['rows']],
                             ['2020-11-01', '2021-11-01', '2022-11-01'])
            self.assertEqual([r['regulationGrant'] for r in forecast['rows']],
                             [r*43640/1e6 for r in (2974, 2417, 1632)])
            self.assertEqual(parent, before)
            self.assertEqual(path['vintage'], parent['vintage'])
            changed = deepcopy(parent)
            for row in changed['vintage']['rows']:
                row['nationalNovemberPopulation'] = 123456789
            self.assertEqual(regulation.prepare(changed, ledger, self.components)['regulationForecast'], forecast)
        parent, ledger = self.path(2022)
        forecast = regulation.prepare(parent, ledger, self.components)['regulationForecast']
        self.assertEqual(forecast['transferredRefugeeGrant0'], 0)
        self.assertIsNone(forecast['categoryTransition'])

    def test_signed_rate_population_controls_and_every_horizon_sensitivity(self):
        parent, ledger = self.path()
        path = regulation.prepare(parent, ledger, self.components)
        changed = deepcopy(parent)
        changed['vintage']['rows'][1]['municipalRegulationPerCapita'] = -100
        self.assertEqual(regulation.prepare(changed, ledger, self.components)['regulationForecast']['rows'][0]['regulationGrant'], -4.364)
        for delta in (-1000, -100, 0, 100, 1000):
            actual = regulation.prepare(parent, ledger | {'population': ledger['population']+delta}, self.components)
            direct = regulation.population_sensitivity(path, [delta])
            for before, after, sensitivity in zip(path['regulationForecast']['rows'], actual['regulationForecast']['rows'], direct):
                self.assertAlmostEqual(after['regulationGrant']-before['regulationGrant'], sensitivity['regulationGrantDifference'])
                self.assertEqual(sensitivity['regulationGrantDifference'], before['ratePerPerson']*delta/1e6)

    def test_accounting_removes_only_two_categories_and_keeps_finance(self):
        for policy in ('costbase', 'no-repeat'):
            parent_path, ledger = self.path(policy=policy)
            path = regulation.prepare(parent_path, ledger, self.components)
            anchor = path['grantAnchor0']
            parent = [{'year': 2021+i, 'tax': 2000, 'incomeEqualisation': 500,
                'grants': 500+(anchor-491)*1.1, 'inheritedGrants': (anchor-491)*1.1,
                'result': 100, 'netCost': 2500, 'financeNet': -20} for i in range(3)]
            saved = deepcopy(parent)
            actual = regulation.accounting_projection(parent, path)
            for before, after, rate in zip(parent, actual, (2974, 2417, 1632)):
                self.assertAlmostEqual(after['allocatedParentRegulationGrant'], 44.7*1.1)
                self.assertAlmostEqual(after['allocatedParentRefugeeWelfareGrant'], 11.2*1.1)
                self.assertAlmostEqual(after['remainingGrants'], (anchor-491-44.7-11.2)*1.1)
                self.assertAlmostEqual(after['grants']-before['grants'], rate*43640/1e6-(44.7+11.2)*1.1)
                self.assertAlmostEqual(after['result']-before['result'], after['grants']-before['grants'])
                for key in ('tax', 'incomeEqualisation', 'netCost', 'financeNet'):
                    self.assertEqual(after[key], before[key])
            self.assertEqual(parent, saved)

    def test_requires_sourced_transfer_matching_origin_and_finite_inputs(self):
        parent, ledger = self.path()
        with self.assertRaisesRegex(ValueError, 'sourced category'):
            regulation.prepare(parent, ledger, self.components | {'categoryTransitions': []})
        with self.assertRaisesRegex(ValueError, 'origin ledger'):
            regulation.prepare(parent, ledger | {'year': 2021}, self.components)
        with self.assertRaisesRegex(ValueError, 'must be positive'):
            regulation.prepare(parent | {'grantAnchor0': parent['incomeEqualisation0']}, ledger, self.components)
        for invalid in (None, True, float('nan'), float('inf')):
            changed = deepcopy(parent)
            changed['vintage']['rows'][1]['municipalRegulationPerCapita'] = invalid
            with self.assertRaises(ValueError):
                regulation.prepare(changed, ledger, self.components)

    def test_native_both_policies_future_mutation_and_selected_rate_control(self):
        from motala_lab.regulation_replay import check_native, UNCHANGED
        with tempfile.TemporaryDirectory(prefix='motala-regulation-test-') as temp:
            directory = Path(temp)
            def run(name, policy, ledgers, components, national, enabled=True):
                return hist.predict_origin(ledgers, 2020, 3, self.protocol, directory/name,
                    missing_wip_fraction=0, macro_data=self.costs, event_data=self.events,
                    event_policy=policy, normalized_inputs=(components, national),
                    settlement_forecast=True, regulation_forecast=enabled)
            for policy in ('costbase', 'no-repeat'):
                parent, _ = run('parent-'+policy, policy, self.ledgers, self.components, self.national, False)
                actual, audit = run('actual-'+policy, policy, self.ledgers, self.components, self.national)
                self.assertLess(max(check_native(directory/('actual-'+policy), actual, parent, audit['normalizedRevenue']).values()), 1e-3)
                self.assertAlmostEqual(actual[0]['regulationGrant'], 2974*43640/1e6, delta=1e-6)
                for before, after in zip(parent, actual):
                    self.assertAlmostEqual(after['allocatedParentRefugeeWelfareGrant']/after['allocatedParentRegulationGrant'], 11.2/44.7)
                    self.assertAlmostEqual(after['grants']-before['grants'], after['regulationGrant']
                        -after['allocatedParentRegulationGrant']-after['allocatedParentRefugeeWelfareGrant'], delta=1e-5)
            # All non-origin accounts and unselected vintages are unavailable to this forecast.
            ledgers, components, national = map(deepcopy, (self.ledgers, self.components, self.national))
            for row in ledgers['rows']:
                if row['year'] != 2020:
                    row.update(grants=999999, population=123456789, result=888888)
            for row in components['rows']:
                if row['year'] != 2020:
                    row['grantComponents']['regulationGrant'] = 123456789
            for vintage in national['vintages']:
                if vintage['originYear'] != 2020:
                    for row in vintage['rows']:
                        row['municipalRegulationPerCapita'] = 123456789
            repeated, _ = run('future-mutation', 'no-repeat', ledgers, components, national)
            self.assertEqual(actual, repeated)
            national = deepcopy(self.national)
            vintage = next(v for v in national['vintages'] if v['originYear'] == 2020)
            vintage['rows'][1]['municipalRegulationPerCapita'] = -100
            positive, _ = run('selected-signed-rate', 'no-repeat', self.ledgers, self.components, national)
            self.assertAlmostEqual(positive[0]['regulationGrant'], -100*43640/1e6, delta=1e-6)
            self.assertAlmostEqual(positive[0]['grants']-actual[0]['grants'], (-100-2974)*43640/1e6, delta=1e-5)
            for before, after in zip(actual, positive):
                for key in (*UNCHANGED, 'remainingGrants'):
                    self.assertAlmostEqual(before[key], after[key], delta=1e-3)


if __name__ == '__main__':
    unittest.main()
