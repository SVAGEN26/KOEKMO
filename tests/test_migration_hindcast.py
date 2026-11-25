"""The migration-window test (scripts/hindcast_migration.py): its copy of the demography is the model's."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hindcast_migration as hm  # noqa: E402

ARCHIVES = (ROOT / json.loads((ROOT / 'data/municipalities/ostergotland-sources.json').read_text())['historyArchive'] / 'population.json').exists()


class Stored(unittest.TestCase):
    def test_the_result_covers_every_window_and_says_what_it_shows(self):
        out = json.loads((ROOT / 'data/migration-hindcast.json').read_text())
        self.assertEqual(out['windows'], [1, 2, 3, 5, 8])
        recent = out['summary']['bases2020to2024']['modelBirths']
        for w in ('2', '3'):
            self.assertEqual(recent[w]['1']['cases'], 13 * 5)
        # From the refugee years the two-year window gives about 6 % too many people after eight years.
        self.assertGreater(out['summary']['bases2017to2024']['modelBirths']['2']['8']['meanError'], 5)
        self.assertEqual(len(out['residualFlowFrom2025']), 13)


@unittest.skipUnless(ARCHIVES, 'SCB archives under data/downloads/ are not in this checkout')
class AgainstTheModel(unittest.TestCase):
    def test_two_years_give_the_models_population(self):
        """The model's own population in the eight-year hindcast (hindsight set, two-year calibration)."""
        runs = [r for r in json.loads((ROOT / 'data/long-hindcast.json').read_text())['runs'] if r['assumptions'] == 'hindsight']
        cache = {}
        for r in runs:
            code = r['municipality']
            cache.setdefault(code, hm.series(code))
            projected, _ = hm.project(*cache[code], r['origin'], 2)
            self.assertAlmostEqual(sum(projected[r['year']]), r['model']['population'], delta=0.5, msg=f"{code} {r['origin']} {r['year']}")


if __name__ == '__main__':
    unittest.main()
