"""Independent identities and information boundaries for the normalized diagnostic."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from motala_lab import dynamics, historical_dynamics as hist, macro, revenue_bridge
from motala_lab import normalized_revenue as normalized


class NormalizedRevenueTests(unittest.TestCase):
    def setUp(self):
        def read(name):
            return json.loads((dynamics.ROOT/'data'/name).read_text())
        self.ledgers = hist.load_ledgers()
        self.components = read('motala-revenue-components.json')
        self.national = read('skr-revenue-vintages.json')
        self.costs = read('skr-pkv-vintages.json')
        self.events = read('motala-noted-events.json')
        self.protocol = read('historical-protocol-tax.json')
        self.params, self.audit = hist.opening_inputs(self.ledgers, 2020, self.protocol,
            missing_wip_fraction=0, event_data=self.events, event_policy='no-repeat')
        self.cost = macro.select_vintage(self.costs, 2020, 3)
        self.vintage = revenue_bridge.select_vintage(self.national, 2020, 3, self.cost)
        self.path = normalized.prepare(self.components, self.audit['openingLedger'], self.params, self.vintage)

    def test_capacity_transition_and_note_adjusted_anchor(self):
        self.assertAlmostEqual(self.path['grantAnchor0'], 760.5-82.1)
        self.assertEqual([r['populationRatio'] for r in self.path['rows']], [1, 1, 1])
        for row, expected in zip(self.path['rows'], [233600/232529, 241182/232529, 249222/232529]):
            self.assertAlmostEqual(row['factor'], expected)
        changed = deepcopy(self.vintage)
        changed['rows'][1]['skrMeanTaxCapacity'] = 999999
        changed['rows'][0]['nationalNovemberPopulation'] = 123456789
        alternate = normalized.prepare(self.components, self.audit['openingLedger'], self.params, changed)
        self.assertEqual(alternate['rows'], self.path['rows'])
        changed['rows'][1]['governmentMeanTaxCapacity'] *= 1.01
        positive = normalized.prepare(self.components, self.audit['openingLedger'], self.params, changed)
        self.assertAlmostEqual(positive['rows'][0]['factor'], self.path['rows'][0]['factor']*1.01)
        with self.assertRaisesRegex(ValueError, 'reference tax rate'):
            normalized.prepare(self.components, self.audit['openingLedger'], self.params|{'taxRate': .22}, self.vintage)

    def test_accounting_preserves_named_residuals_and_finance(self):
        parent = [{'year': 2021, 'tax': 100, 'grants': 80, 'result': 15, 'taxAndGrants': 180,
                   'netCost': 160, 'financeNet': -5}]
        path = {'preliminaryTax0': 80, 'incomeEqualisation0': 60, 'taxAnchor0': 100,
                'grantAnchor0': 80, 'rows': [{'year': 2021, 'factor': 1.1}]}
        before = deepcopy(parent)
        row = normalized.accounting_projection(parent, path)[0]
        self.assertAlmostEqual(row['tax'], 108)
        self.assertAlmostEqual(row['grants'], 86)
        self.assertAlmostEqual(row['result'], 29)
        self.assertEqual(row['inheritedTax'], 20)
        self.assertEqual(row['inheritedGrants'], 20)
        self.assertEqual(row['financeNet'], -5)
        self.assertEqual(parent, before)

    def test_2025_targets_reconcile_without_becoming_opening_data(self):
        targets = json.loads((dynamics.ROOT/'data/revenue-component-targets-2025.json').read_text())
        ledger = next(r for r in self.ledgers['rows'] if r['year'] == 2025)
        row = revenue_bridge.opening_components(targets, ledger)
        self.assertEqual(row['taxComponents']['preliminaryTax'], 2344)
        self.assertEqual(row['grantComponents']['incomeEqualisation'], 631)
        self.assertEqual(row['grantRoundingResidual'], -1)

    def test_native_components_residuals_financing_and_no_future_leakage(self):
        with tempfile.TemporaryDirectory(prefix='motala-normalized-test-') as temp:
            directory = Path(temp)
            def run(name, ledgers, components, national):
                return hist.predict_origin(ledgers, 2020, 3, self.protocol, directory/name,
                    missing_wip_fraction=0, macro_data=self.costs, event_data=self.events,
                    event_policy='no-repeat', normalized_inputs=(components, national))[0]
            parent, _ = hist.predict_origin(self.ledgers, 2020, 3, self.protocol, directory/'parent',
                missing_wip_fraction=0, macro_data=self.costs, event_data=self.events, event_policy='no-repeat')
            actual = run('actual', self.ledgers, self.components, self.national)
            changed_data, changed_parts, changed_national = map(deepcopy, (self.ledgers, self.components, self.national))
            for row in changed_data['rows']:
                if row['year'] > 2020:
                    row.update(tax=999999, grants=888888, result=777777)
            for row in changed_parts['rows']:
                if row['year'] != 2020:
                    row['taxComponents']['preliminaryTax'] = 123456789
                    row['grantComponents']['incomeEqualisation'] = 999999
            for vintage in changed_national['vintages']:
                if vintage['originYear'] != 2020:
                    vintage['rows'][0]['governmentMeanTaxCapacity'] = 123456789
            repeated = run('future-mutation', changed_data, changed_parts, changed_national)
            self.assertEqual(actual, repeated)
            changed_parts = deepcopy(self.components)
            opening = next(r for r in changed_parts['rows'] if r['year'] == 2020)
            opening['taxComponents']['preliminaryTax'] += 10
            opening['taxComponents']['estimatedCurrentYearSettlement'] -= 10
            positive = run('opening-mutation', self.ledgers, changed_parts, self.national)
            self.assertGreater(abs(positive[0]['tax']-actual[0]['tax']), .05)
            for index, (before, after) in enumerate(zip(parent, actual)):
                expected = normalized.allocation(before, self.path, index)
                for key in ('preliminaryTax', 'incomeEqualisation', 'inheritedTax', 'inheritedGrants'):
                    self.assertAlmostEqual(after[key], expected[key], delta=1e-3)
                for key in ('netCost', 'population', 'personnel', 'operatingRevenue', 'depreciation'):
                    self.assertAlmostEqual(after[key], before[key], delta=1e-3)
                self.assertAlmostEqual(after['result']-before['result'],
                    after['taxAndGrants']-before['taxAndGrants']+after['financeNet']-before['financeNet'], delta=1e-4)
                self.assertLess(abs(after['balanceResidual']), 1e-4)


if __name__ == '__main__':
    unittest.main()
