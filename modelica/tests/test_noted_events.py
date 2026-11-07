"""Reported-to-recurring bridges, future-information isolation, fixed rules."""
from copy import deepcopy
import json
import unittest

from motala_lab import historical_dynamics as hist, noted_events, macro


class NotedEventsTests(unittest.TestCase):
    def setUp(self):
        self.ledgers = hist.load_ledgers()
        self.data = json.loads((hist.ROOT/'data/motala-noted-events.json').read_text())
        self.protocol = json.loads((hist.ROOT/'data/historical-protocol.json').read_text())
        self.macro = json.loads((hist.ROOT/'data/skr-pkv-vintages.json').read_text())

    def row(self, year):
        return next(r for r in self.ledgers['rows'] if r['year'] == year)

    def test_itemised_signs_and_unchanged_closing_stocks(self):
        original = deepcopy(self.row(2021))
        recurring, audit = noted_events.prepare(original, self.data, 'costbase')
        self.assertEqual(original, self.row(2021))
        self.assertAlmostEqual(recurring['otherExpense'], 1179.4-30-28.6)
        self.assertAlmostEqual(recurring['result'], 61.7+58.6)
        self.assertAlmostEqual(audit['itemisedNoteNet'], -38.6)
        for key in ('operatingRevenue', 'grants', 'tangibleIncludingWIP', 'workInProgress',
                    'debt', 'cash', 'payroll', 'pension', 'investment', 'depreciation'):
            self.assertEqual(recurring[key], original[key])
        all_items, _ = noted_events.prepare(original, self.data, 'no-repeat')
        self.assertAlmostEqual(all_items['result'], 61.7+30+28.6-20)
        self.assertEqual(all_items['operatingRevenue'], original['operatingRevenue']-20)

    def test_landfill_charge_is_not_a_stock_addition_or_payment(self):
        recurring, audit = noted_events.prepare(self.row(2023), self.data, 'costbase')
        self.assertEqual(audit['excludedFromRecurringBase']['otherExpense'], 26)
        self.assertEqual(recurring['otherExpense'], 1221)
        self.assertEqual(recurring['result'], 49)
        self.assertEqual(recurring['cash'], 115)
        self.assertEqual(recurring['tangibleIncludingWIP'], 2627)

    def test_temporary_general_grants_and_operating_receipts_keep_their_fields(self):
        row, audit = noted_events.prepare(self.row(2020), self.data, 'no-repeat')
        self.assertAlmostEqual(row['grants'], 760.5-82.1)
        self.assertAlmostEqual(row['operatingRevenue'], 680.8-31.6-15.7)
        self.assertAlmostEqual(row['result']+audit['reportedResultEffectOfExcludedItems'], 64.8)
        self.assertTrue(audit['sourceRevisions'])

    def test_all_origins_keep_a_reversible_full_result_identity(self):
        for year in range(2020, 2025):
            for policy in noted_events.POLICIES:
                raw = self.row(year)
                row, a = noted_events.prepare(raw, self.data, policy)
                self.assertAlmostEqual(row['result']+a['reportedResultEffectOfExcludedItems'], raw['result'])
                self.assertAlmostEqual(row['tax']+row['grants']-row['netCost']
                    +row['financialIncome']-row['financialExpense']+row['resultRounding'], row['result'])
        row, audit = noted_events.prepare(self.row(2024), self.data, 'costbase')
        self.assertEqual(row, self.row(2024))
        self.assertEqual(audit['excludedItemIds'], [])

    def test_absent_notes_bad_signs_duplicate_items_and_overadjustment_fail(self):
        for change in ('missing', 'unreviewed', 'duplicate', 'mapping', 'too-large', 'net'):
            data = deepcopy(self.data)
            row = data['rows'][1]
            if change == 'missing':
                data['rows'].pop(1)
            elif change == 'unreviewed':
                row['reviewComplete'] = False
            elif change == 'duplicate':
                row['items'].append(deepcopy(row['items'][0]))
            elif change == 'mapping':
                row['items'][0]['field'] = 'otherExpense'
            elif change == 'too-large':
                row['items'][1]['amount'] = 100000
            else:
                row['sourceNoteNet'] = 78.6
            with self.assertRaises(ValueError, msg=change):
                noted_events.prepare(self.row(2021), data, 'costbase')

    def test_future_outcomes_and_future_note_items_do_not_change_forecasts(self):
        changed = deepcopy(self.data)
        for row in changed['rows']:
            if row['originYear'] > 2021:
                row['items'] = [{'unusable': True}]
                row['reviewComplete'] = False
        later = deepcopy(self.ledgers)
        for row in later['rows']:
            if row['year'] > 2021:
                row['result'] = 100000
                row['otherExpense'] = 1
        for policy in noted_events.POLICIES:
            before = hist.opening_inputs(self.ledgers, 2021, self.protocol, missing_wip_fraction=0,
                event_data=self.data, event_policy=policy)
            after = hist.opening_inputs(later, 2021, self.protocol, missing_wip_fraction=0,
                event_data=changed, event_policy=policy)
            self.assertEqual(before, after)
            self.assertEqual(before[1]['openingLedger'], self.row(2021))

    def test_accounting_delta_matches_independent_cost_and_receipt_indices(self):
        raw = self.row(2021)
        vintage = macro.select_vintage(self.macro, 2021, 3)
        base = macro.accounting_projection(raw, vintage, self.protocol['parameters'])
        adjusted, _ = noted_events.prepare(raw, self.data, 'no-repeat')
        pred = macro.accounting_projection(adjusted, vintage, self.protocol['parameters'])
        price = 1.
        for h, (a, b, v) in enumerate(zip(base, pred, vintage['rows']), 1):
            price *= 1+v['otherPercent']/100
            self.assertAlmostEqual(b['result']-a['result'], 58.6*price-20*1.02**h)
            self.assertEqual(b['personnel'], a['personnel'])


if __name__ == '__main__':
    unittest.main()
