"""The rule for the state's frame against the regulation grant's history (data/regulation-hindcast.json)."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RegulationHindcast(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/regulation-hindcast.json').read_text())
        cls.equalisation = json.loads((ROOT / 'data/equalisation.json').read_text())['municipalities']

    def test_the_series_is_scbs_and_the_same_in_every_municipality(self):
        for year, amount in self.data['regulationPerInhabitant'].items():
            for code in ('0583', '0580', '0180', '2584'):
                self.assertEqual(self.equalisation[code]['years'][year]['regulation'], amount)

    def test_the_hold_rule_is_the_start_years_amount(self):
        regulation = {int(y): v for y, v in self.data['regulationPerInhabitant'].items()}
        first, last = self.data['startYears']
        for horizon, summary in self.data['summary']['hold'].items():
            errors = [regulation[s] - regulation[s + int(horizon)] for s in range(first, last + 1) if s + int(horizon) <= 2026]
            self.assertEqual(summary['cases'], len(errors))
            self.assertEqual(summary['meanError'], round(sum(errors) / len(errors)))
            self.assertEqual(summary['meanAbsError'], round(sum(map(abs, errors)) / len(errors)))

    def test_the_tax_base_per_inhabitant_grew_three_to_four_per_cent_a_year(self):
        growth = list(self.data['taxCapacityGrowthPercent'].values())
        self.assertEqual(len(growth), 21)
        self.assertGreater(sum(growth) / len(growth), 3)
        self.assertLess(sum(growth) / len(growth), 4)

    def test_a_frame_fixed_in_kronor_is_the_worst_rule_at_every_horizon(self):
        summary = self.data['summary']
        for horizon in summary['fixed']:
            self.assertGreater(summary['fixed'][horizon]['meanAbsError'], summary['hold'][horizon]['meanAbsError'])
            self.assertGreater(summary['fixed'][horizon]['meanAbsError'], summary['taxbase'][horizon]['meanAbsError'])
            self.assertLess(summary['fixed'][horizon]['meanError'], summary['taxbase'][horizon]['meanError'])

    def test_every_rule_is_too_low_and_following_the_tax_base_is_the_least_biased(self):
        summary = self.data['summary']
        for horizon in summary['hold']:
            self.assertLess(summary['taxbase'][horizon]['meanError'], 0)
            self.assertLess(summary['hold'][horizon]['meanError'], summary['taxbase'][horizon]['meanError'])
        # The absolute errors of the two are within 10 % of each other: the history does not separate them.
        for horizon in summary['hold']:
            ratio = summary['taxbase'][horizon]['meanAbsError'] / summary['hold'][horizon]['meanAbsError']
            self.assertGreater(ratio, 0.9)
            self.assertLess(ratio, 1.1)


if __name__ == '__main__':
    unittest.main()
