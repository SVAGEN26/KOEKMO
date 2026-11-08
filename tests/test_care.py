"""Care weights in the base-year records must match data/care-weights.json (Kolada)."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = (ROOT / 'modelica/Motala.mo').read_text()
WEIGHTS = json.loads((ROOT / 'data/care-weights.json').read_text())


class Care(unittest.TestCase):
    def test_base_records_use_the_kolada_weights(self):
        for year in ('2024', '2025'):
            record = re.search(rf'constant BaseYear motala{year} = BaseYear\((.*?)\)\s*"', MODEL, re.S).group(1)
            found = [float(x) for x in re.search(r'careCostPerInhabitant = \{([^}]*)\}', record).group(1).split(',')]
            expected = WEIGHTS['baseYears'][year]['costPerInhabitant']
            self.assertEqual(found, [round(expected['65-79']), round(expected['80+'])], year)

    def test_each_base_year_uses_three_years_ending_in_it(self):
        for base, b in WEIGHTS['baseYears'].items():
            self.assertEqual(b['years'], [int(base) - 2, int(base) - 1, int(base)])
            self.assertGreater(b['ratio80to6579'], 1)


if __name__ == '__main__':
    unittest.main()
