"""The band around tax and grants on the page: SKR's forecast errors by years ahead (data/revenue-uncertainty.json)."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RevenueUncertainty(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/revenue-uncertainty.json').read_text())
        cls.summary = json.loads((ROOT / 'data/outcome-explanation-summary.json').read_text())

    def test_it_is_the_summary_of_skrs_forecasts_by_years_ahead(self):
        by = {}
        for f in self.summary['taxAndGrantsForecasts']:
            if f['forecast'].startswith('SKR '):
                for r in f['rows']:
                    by.setdefault(r['year'] - int(f['published'][:4]), []).append(r['meanAbsErrorPercent'])
        self.assertEqual([r['yearsAhead'] for r in self.data['byYearsAhead']], sorted(by))
        for r in self.data['byYearsAhead']:
            self.assertEqual(r['forecasts'], len(by[r['yearsAhead']]))
            self.assertAlmostEqual(r['meanAbsErrorPercent'], sum(by[r['yearsAhead']]) / len(by[r['yearsAhead']]), delta=0.006)

    def test_only_skrs_own_forecasts_are_counted_and_the_error_grows_with_the_horizon(self):
        self.assertEqual(len(self.data['forecasts']), 4)
        self.assertTrue(all(f['forecast'].startswith('SKR ') for f in self.data['forecasts']))
        errors = [r['meanAbsErrorPercent'] for r in self.data['byYearsAhead']]
        self.assertEqual(errors, sorted(errors))
        self.assertLess(errors[0], 1.5)   # the current year
        self.assertGreater(errors[-1], 3)  # four years ahead, from the 2021 forecast


if __name__ == '__main__':
    unittest.main()
