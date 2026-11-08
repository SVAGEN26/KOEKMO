"""Paired comparisons must preserve matching assumptions and expose failed cases."""
import copy
import unittest

from motala_lab import experiments


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.config = {'schemaVersion': 1, 'years': 2,
            'reference': {'scenario': 'base', 'parameters': {'priceGrowth': 0.02}},
            'alternatives': [{'id': 'policy', 'label': 'Policy', 'parameters': {'reductionYears': [0.5, 3, 3]}}],
            'sensitivities': [{'id': 'wage', 'label': 'Wages', 'low': {'wageGrowth': 0.01}, 'high': {'wageGrowth': 0.05}}]}

    def test_shared_assumptions_apply_identically_to_both_policies(self):
        cases = experiments.design(self.config)
        self.assertEqual(len(cases), 6)
        for ref, alt in zip(cases[::2], cases[1::2]):
            self.assertEqual(ref['background'], alt['background'])
            for key, value in ref['parameters'].items():
                self.assertEqual(alt['parameters'][key], value)
            self.assertEqual(alt['parameters']['reductionYears'], [0.5, 3, 3])

    def test_overlapping_assumptions_and_duplicate_ids_are_rejected(self):
        config = copy.deepcopy(self.config)
        config['alternatives'][0]['parameters']['wageGrowth'] = 0.03
        with self.assertRaises(ValueError):
            experiments.design(config)
        self.config['alternatives'][0]['id'] = 'reference'
        with self.assertRaises(ValueError):
            experiments.design(self.config)

    def test_pairing_uses_own_reference_and_keeps_failed_pairs_missing(self):
        cases = experiments.design(self.config)
        for index, case in enumerate(cases):
            case.update(status='success', summary={'endingDebt': 100 + index * 10})
        cases[2]['status'] = 'failed'
        cases = experiments.paired_results(cases)
        self.assertEqual(cases[1]['delta']['endingDebt'], 10)
        self.assertIsNone(cases[3]['delta'])
        self.assertEqual(cases[5]['delta']['endingDebt'], 10)


if __name__ == '__main__':
    unittest.main()
