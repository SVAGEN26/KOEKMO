"""Check source integrity, sign conventions and reporting changes before scoring."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import prepare_scb_accounts as prep

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT/'reference/scb-accounts-20261016'
MAPPING = ROOT/'data/scb-budget-response-mapping.json'


class SCBPreparationTests(unittest.TestCase):
    def setUp(self):
        self.metadata, self.data, self.query, _, _ = prep.load_packet(PACKET)
        self.mapping = json.loads(MAPPING.read_text())

    def normalize(self):
        return prep.normalize(self.metadata, self.data, self.query, self.mapping)

    def set_cell(self, item, year, value):
        categories = self.data['dimension']
        item_index = categories['Resultatraknposter']['category']['index'][item]
        year_index = categories['Tid']['category']['index'][str(year)]
        self.data['value'][item_index*28+year_index] = value

    def test_all_observed_years_and_explicit_source_locations(self):
        rows = self.normalize()
        self.assertEqual([r['year'] for r in rows], list(range(1998, 2026)))
        last = rows[-1]
        self.assertEqual([last[k] for k in ['taxAndGrants', 'netCost', 'financeNet', 'result']],
                         [3317.451, 3202.904, -9.964, 104.583])
        self.assertIn('Region=0583', last['locator'])

    def test_pension_interest_is_counted_in_earlier_finance(self):
        rows = {r['year']: r for r in self.normalize()}
        # The separate pension interest must enter finance exactly once.
        self.assertEqual(rows[1998]['financeNet'], -5.279)
        self.assertEqual(rows[2010]['financeNet'], -3.085)
        self.assertEqual(rows[2011]['financeNet'], -8.691)
        self.assertIsNone(rows[2011]['sourceCellsTkr']['071'])
        self.set_cell('071', 2010, None)
        with self.assertRaisesRegex(ValueError, 'source cell'):
            self.normalize()

    def test_reported_extraordinary_result_remains_separate(self):
        rows = {r['year']: r for r in self.normalize()}
        self.assertEqual(rows[2017]['result'], 62.444)
        self.assertEqual(rows[2017]['resultAccountingResidual'], 32.224)
        self.assertEqual(rows[1998]['resultAccountingResidual'], 65.338)
        self.assertEqual(rows[2005]['resultAccountingResidual'], -14.392)
        self.assertEqual(rows[2019]['resultAccountingResidual'], 0)
        self.assertIsNone(rows[2019]['sourceCellsTkr']['100'])

    def test_unexplained_ledger_residual_is_rejected(self):
        self.set_cell('080', 2025, 104584)
        with self.assertRaisesRegex(ValueError, 'result-after-finance'):
            self.normalize()

    def test_missing_core_observation_is_never_zero(self):
        self.set_cell('040', 2007, None)
        with self.assertRaisesRegex(ValueError, 'source cell'):
            self.normalize()

    def test_changed_units_and_definitions_require_review(self):
        self.data['dimension']['ContentsCode']['category']['unit']['000008H2']['base'] = 'mnkr'
        with self.assertRaisesRegex(ValueError, 'source unit'):
            self.normalize()
        self.data = json.loads((PACKET/'TAB6777-data.json').read_text())
        self.data['dimension']['Resultatraknposter']['category']['label']['030'] = 'different scope'
        with self.assertRaisesRegex(ValueError, 'definition'):
            self.normalize()

    def test_wrong_municipality_cannot_be_selected(self):
        self.query['selection'][0]['valueCodes'] = ['0180']
        with self.assertRaises(ValueError):
            self.normalize()

    def test_tampered_source_or_request_is_rejected(self):
        for name in ['TAB6777-data.json', 'TAB6777-data.request.json']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                folder = Path(temp)/'packet'
                shutil.copytree(PACKET, folder)
                with (folder/name).open('ab') as handle:
                    handle.write(b'\n')
                with self.assertRaisesRegex(ValueError, 'hash'):
                    prep.load_packet(folder)

    def test_annual_report_differences_are_retained_without_splicing(self):
        rows = self.normalize()
        original = deepcopy(rows)
        reference = json.loads((ROOT/'data/annual-ledgers.json').read_text())
        review = prep.reconcile(rows, reference)
        self.assertEqual(rows, original)
        self.assertFalse(review['observationsSpliced'])
        year = next(r for r in review['rows'] if r['year'] == 2021)
        self.assertEqual(year['scbMinusAnnualReport']['netCost'], 19.507)
        self.assertEqual(year['scbMinusAnnualReport']['taxAndGrants'], 19.448)


if __name__ == '__main__':
    unittest.main()
