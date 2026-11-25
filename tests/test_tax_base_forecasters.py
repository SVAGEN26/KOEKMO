"""SKR's tax-base forecasts beside the government's and ESV's (data/tax-base-forecasters.json)."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from hindcast_vintages import tax_base_outcomes  # noqa: E402


class TaxBaseForecasters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((ROOT / 'research/data/tax-base-forecasters.json').read_text())
        cls.data = json.loads((ROOT / 'data/tax-base-forecasters.json').read_text())
        cls.vintages = json.loads((ROOT / 'research/data/skr-tax-vintages.json').read_text())['vintages']

    def test_skrs_row_is_the_forecast_the_hindcasts_use(self):
        for c in self.source['circulars']:
            vintage = next(v for v in self.vintages if v['circular'] == c['circular'])
            skr = next(r for r in c['rows'] if r['forecaster'] == 'SKR')['growthPercent']
            self.assertEqual(vintage['publicationDate'], c['published'])
            for row in vintage['rows']:
                self.assertEqual(skr[str(row['year'])], row['taxBasePercent'])

    def test_every_circular_has_the_four_forecasters_and_a_source(self):
        self.assertEqual([c['circular'] for c in self.source['circulars']], ['20:57', '21:49', '22:54', '23:56', '24:56'])
        for c in self.source['circulars']:
            self.assertEqual(sorted(r['forecaster'] for r in c['rows']), ['ESV', 'Government', 'SKR', 'SKR previous'])
            self.assertTrue(c['source'].startswith('https://'))
            self.assertIn('Tabell', c['locator'])

    def test_errors_are_forecast_minus_outcome_and_only_for_years_with_an_outcome(self):
        outcome = tax_base_outcomes()
        self.assertTrue(self.data['errors'])
        for e in self.data['errors']:
            self.assertLessEqual(e['year'], 2024)
            self.assertAlmostEqual(e['errorPoints'], e['forecastPercent'] - 100 * outcome[e['year']], delta=0.006)
            self.assertEqual(e['yearsAhead'], e['year'] - int('20' + e['circular'][:2]))

    def test_the_summary_is_the_mean_of_the_errors(self):
        for s in self.data['summary']:
            e = [r['errorPoints'] for r in self.data['errors'] if r['forecaster'] == s['forecaster'] and r['yearsAhead'] == s['yearsAhead']]
            self.assertEqual(s['forecasts'], len(e))
            self.assertAlmostEqual(s['meanErrorPoints'], sum(e) / len(e), delta=0.006)
            self.assertAlmostEqual(s['meanAbsErrorPoints'], sum(abs(v) for v in e) / len(e), delta=0.006)

    def test_nobody_saw_the_years_after_the_pandemic_coming(self):
        # One year ahead every forecaster was too low in all four cases, by about the same amount.
        ahead = {s['forecaster']: s for s in self.data['summary'] if s['yearsAhead'] == 1}
        for who in ('SKR', 'ESV', 'Government'):
            self.assertEqual(ahead[who]['forecasts'], 4)
            self.assertAlmostEqual(ahead[who]['meanErrorPoints'], -ahead[who]['meanAbsErrorPoints'], delta=0.006)
            self.assertLess(abs(ahead[who]['meanAbsErrorPoints'] - ahead['SKR']['meanAbsErrorPoints']), 0.5)


if __name__ == '__main__':
    unittest.main()
