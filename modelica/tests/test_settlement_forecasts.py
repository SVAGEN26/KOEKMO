"""Information boundaries and signed accounting for the dated settlement experiment."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from motala_lab import dynamics, historical_dynamics as hist, macro, revenue_bridge
from motala_lab import normalized_revenue as normalized, settlement_forecasts as settlements


class SettlementTests(unittest.TestCase):
    def setUp(self):
        def read(name):
            return json.loads((dynamics.ROOT/'data'/name).read_text())
        self.ledgers = hist.load_ledgers()
        self.components = read('motala-revenue-components.json')
        self.national = read('skr-revenue-vintages.json')
        self.costs = read('skr-pkv-vintages.json')
        self.events = read('motala-noted-events.json')
        self.protocol = read('historical-protocol-tax.json')
        self.params, self.audit = hist.opening_inputs(self.ledgers, 2022, self.protocol,
            missing_wip_fraction=0, event_data=self.events, event_policy='costbase')
        cost = macro.select_vintage(self.costs, 2022, 3)
        vintage = revenue_bridge.select_vintage(self.national, 2022, 3, cost)
        self.normalized = normalized.prepare(self.components, self.audit['openingLedger'], self.params, vintage)
        self.path = settlements.prepare(self.normalized, self.audit['openingLedger'])

    def test_year_reference_signed_value_and_separate_nulls(self):
        original = deepcopy(self.normalized)
        forecast = self.path['settlementForecast']
        self.assertEqual(forecast['populationProxy']['referenceDate'], '2022-12-31')
        self.assertEqual(forecast['populationProxy']['proxyForReferenceDate'], '2022-11-01')
        self.assertFalse(forecast['populationProxy']['historicalPublicationAvailabilityEstablished'])
        self.assertEqual([r['year'] for r in forecast['rows']], [2023, 2024, 2025])
        self.assertEqual([r['sourceCurrentPerCapita'] for r in forecast['rows']], [-317, None, None])
        self.assertEqual([r['currentYearSettlement'] for r in forecast['rows']], [-317*43728/1e6, 0, 0])
        self.assertEqual([r['priorYearSettlementRevision'] for r in forecast['rows']], [0, 0, 0])
        self.assertEqual(self.normalized, original)
        self.assertEqual(self.path['vintage'], original['vintage'])
        changed = deepcopy(self.normalized)
        changed['vintage']['priorYearSettlementRevisionPerCapita'] = 99999
        changed['vintage']['rows'][1]['nationalNovemberPopulation'] = 999999999
        self.assertEqual(settlements.prepare(changed, self.audit['openingLedger'])['settlementForecast'], forecast)

    def test_positive_controls_and_population_sensitivity(self):
        changed = deepcopy(self.normalized)
        changed['vintage']['rows'][1]['currentYearSettlementPerCapita'] += 100
        positive = settlements.prepare(changed, self.audit['openingLedger'])
        self.assertAlmostEqual(positive['settlementForecast']['rows'][0]['settlementAndRevision']
            -self.path['settlementForecast']['rows'][0]['settlementAndRevision'], 100*43728/1e6)
        for delta in (-1000, -100, 0, 100, 1000):
            ledger = self.audit['openingLedger'] | {'population': 43728+delta}
            changed = settlements.prepare(self.normalized, ledger)
            direct = settlements.population_sensitivity(self.path, [delta])[0]
            self.assertAlmostEqual(direct['firstYearSettlementDifference'], -317*delta/1e6)
            self.assertAlmostEqual(changed['settlementForecast']['rows'][0]['settlementAndRevision']
                -self.path['settlementForecast']['rows'][0]['settlementAndRevision'], direct['firstYearSettlementDifference'])
        with self.assertRaisesRegex(ValueError, 'forecast origin'):
            settlements.prepare(self.normalized, self.audit['openingLedger'] | {'year': 2021})
        changed = deepcopy(self.normalized)
        changed['vintage']['rows'][2]['currentYearSettlementPerCapita'] = 0
        with self.assertRaisesRegex(ValueError, 'remain null'):
            settlements.prepare(changed, self.audit['openingLedger'])

    def test_accounting_removes_entire_residual_preserving_finance(self):
        parent = [{'year': 2023+i, 'tax': 100, 'grants': 80, 'taxAndGrants': 180,
                   'result': 15, 'netCost': 160, 'financeNet': -5, 'preliminaryTax': 80,
                   'incomeEqualisation': 60, 'inheritedTax': 20, 'inheritedGrants': 20}
                  for i in range(3)]
        original = deepcopy(parent)
        actual = settlements.accounting_projection(parent, self.path)
        for before, after, source in zip(parent, actual, self.path['settlementForecast']['rows']):
            self.assertEqual(after['inheritedTax'], 0)
            self.assertEqual(after['tax'], 80+source['settlementAndRevision'])
            self.assertAlmostEqual(after['result']-before['result'], after['tax']-before['tax'])
            for key in ('grants', 'netCost', 'financeNet', 'preliminaryTax', 'incomeEqualisation', 'inheritedGrants'):
                self.assertEqual(after[key], before[key])
        self.assertEqual(parent, original)

    def test_native_signed_integral_unchanged_components_and_future_mutation(self):
        from motala_lab.settlement_replay import check_native
        with tempfile.TemporaryDirectory(prefix='motala-settlement-test-') as temp:
            directory = Path(temp)
            def run(name, ledgers, components, national, enabled=True):
                return hist.predict_origin(ledgers, 2022, 3, self.protocol, directory/name,
                    missing_wip_fraction=0, macro_data=self.costs, event_data=self.events,
                    event_policy='costbase', normalized_inputs=(components, national), settlement_forecast=enabled)
            parent, _ = run('parent', self.ledgers, self.components, self.national, False)
            actual, audit = run('actual', self.ledgers, self.components, self.national)
            checks = check_native(directory/'actual', actual, parent, audit['normalizedRevenue'])
            self.assertLess(max(checks.values()), 1e-3)
            self.assertLess(actual[0]['taxSettlement'], 0)
            ledgers, components, national = map(deepcopy, (self.ledgers, self.components, self.national))
            for row in ledgers['rows']:
                if row['year'] != 2022:
                    row.update(tax=999999, population=123456789, result=888888)
            for row in components['rows']:
                if row['year'] != 2022:
                    row['taxComponents']['preliminaryTax'] = 123456789
            for vintage in national['vintages']:
                if vintage['originYear'] != 2022:
                    vintage['rows'][1]['currentYearSettlementPerCapita'] = 123456789
            repeated, _ = run('future-mutation', ledgers, components, national)
            self.assertEqual(actual, repeated)
            national = deepcopy(self.national)
            vintage = next(v for v in national['vintages'] if v['originYear'] == 2022)
            vintage['rows'][1]['currentYearSettlementPerCapita'] += 100
            positive, _ = run('selected-settlement-mutation', self.ledgers, self.components, national)
            self.assertAlmostEqual(positive[0]['tax']-actual[0]['tax'], 100*43728/1e6, delta=1e-6)
            for before, after in zip(actual, positive):
                for key in ('preliminaryTax', 'incomeEqualisation', 'grants', 'personnel', 'netCost'):
                    self.assertAlmostEqual(before[key], after[key], delta=1e-3)


if __name__ == '__main__':
    unittest.main()
