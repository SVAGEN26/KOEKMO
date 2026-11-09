"""SCB demography inputs: consistency between the prepared JSON and the Modelica data package."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = json.loads((ROOT / 'data/demography-inputs.json').read_text())


class Demography(unittest.TestCase):
    def test_modelica_data_matches_the_json(self):
        """Regenerating the SCB packages from the JSON must leave Kommunekonomi.mo and Motala.mo unchanged."""
        spec = importlib.util.spec_from_file_location('writer', ROOT / 'scripts/write_demography_modelica.py')
        writer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(writer)
        with tempfile.TemporaryDirectory() as tmp:
            copies = {}
            for name in ('Kommunekonomi.mo', 'Motala.mo'):
                copies[name] = Path(tmp) / name
                shutil.copy(ROOT / 'modelica' / name, copies[name])
            writer.LIBRARY, writer.MUNICIPALITY = copies['Kommunekonomi.mo'], copies['Motala.mo']
            writer.main()
            # Compare without whitespace: OMEdit reformats the file when it saves.
            squeeze = lambda text: ''.join(text.split())
            for name, copy in copies.items():
                self.assertEqual(squeeze(copy.read_text()), squeeze((ROOT / 'modelica' / name).read_text()),
                                 f'{name}: run scripts/write_demography_modelica.py after prepare_demography.py')

    def test_each_base_year_uses_its_own_observations(self):
        observed = INPUTS['observed']['population']
        for base, c in INPUTS['baseYears'].items():
            self.assertEqual(c['population'], observed[base], base)
            self.assertEqual(c['mortalityWindow'][1], int(base), base)
            self.assertEqual(c['migrationTransitions'][1], int(base), base)
            for ratio in c['mortalityRatio']:
                self.assertTrue(0.7 < ratio < 1.4, f'{base}: implausible mortality ratio {ratio}')
            for sex in ('1', '2'):
                self.assertEqual(len(c['deathRisk'][sex]), 101)
                self.assertTrue(all(0 < q <= 1 for q in c['deathRisk'][sex]), f'{base}: death risk outside (0, 1]')

    def test_fertility_profile_is_a_distribution(self):
        shares = INPUTS['fertilityProfile']['shares']
        self.assertAlmostEqual(sum(shares), 1, places=12)
        self.assertTrue(all(x >= 0 for x in shares))
        self.assertTrue(all(x == 0 for a, x in enumerate(shares) if a < 15 or a > 49))

    def test_hindcast_is_recorded(self):
        hindcast = json.loads((ROOT / 'data/demography-hindcast.json').read_text())
        self.assertIn('fertility 1.41', hindcast['summaryByHorizon'])
        self.assertTrue(all(r['observed'] for r in hindcast['runs']))


if __name__ == '__main__':
    unittest.main()
