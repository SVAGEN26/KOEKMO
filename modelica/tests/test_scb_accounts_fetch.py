"""Offline contract checks; synthetic values are never historical evidence."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('scb_fetch', Path(__file__).resolve().parents[1] / 'fetch_scb_accounts.py')
FETCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FETCH)


def dataset():
    return {'version': '2.0', 'class': 'dataset', 'id': ['Region', 'Item', 'Tid'], 'size': [1, 2, 2],
            'dimension': {
                'Region': {'category': {'index': {'0583': 0}, 'label': {'0583': 'Motala'}}},
                'Item': {'category': {'index': {'cost': 1, 'tax': 0}, 'label': {'tax': 'Tax', 'cost': 'Cost'},
                                     'unit': {'tax': {'base': 'tkr'}, 'cost': {'base': 'tkr'}}}},
                'Tid': {'category': {'index': {'2021': 1, '2020': 0}, 'label': {'2020': '2020', '2021': '2021'}}}},
            'value': [100, 0, -30, None], 'status': {'3': '..'}}


class SCBFetchTests(unittest.TestCase):
    def test_explicit_order_sign_zero_missing_and_units(self):
        data = dataset()
        request = FETCH.selection(data, {'years': [2020, 2021]})
        rows = list(FETCH.observations(data, request, 'TEST'))
        self.assertEqual([row['value'] for row in rows], [100, 0, -30, ''])
        self.assertEqual([row['year'] for row in rows], ['2020', '2021', '2020', '2021'])
        self.assertIn('"Item": "tax"', rows[0]['item_codes'])
        self.assertEqual(rows[3]['status'], '..')
        self.assertIn('tkr', rows[0]['unit_metadata'])

    def test_selection_requires_motala_and_all_requested_years(self):
        data = dataset()
        data['dimension']['Region']['category']['index'] = {'0581': 0, '0583': 1}
        data['size'][0] = 2
        request = FETCH.selection(data, {'years': [2020, 2021]})
        self.assertEqual(request['selection'][0]['valueCodes'], ['0583'])
        with self.assertRaises(ValueError):
            FETCH.selection(data, {'years': [2019, 2021]})

    def test_wrong_municipality_response_is_rejected(self):
        data = dataset()
        request = FETCH.selection(data, {'years': [2020, 2021]})
        data['dimension']['Region']['category']['index'] = {'0581': 0}
        with self.assertRaises(ValueError):
            list(FETCH.observations(data, request, 'TEST'))

    def test_sparse_missing_values_are_not_zero(self):
        data = dataset()
        data['value'] = {'0': 100, '1': 0, '2': -30}
        rows = list(FETCH.observations(data, FETCH.selection(data, {'years': [2020, 2021]}), 'TEST'))
        self.assertEqual([r['value'] for r in rows], [100, 0, -30, ''])

    def test_changed_dimension_order_preserves_coordinates(self):
        original = dataset()
        request = FETCH.selection(original, {'years': [2020, 2021]})
        data = deepcopy(original)
        data['id'] = ['Tid', 'Item', 'Region']
        data['size'] = [2, 2, 1]
        data['value'] = [100, -30, 0, None]
        rows = list(FETCH.observations(data, request, 'TEST'))
        self.assertEqual([(r['year'], r['value']) for r in rows], [('2020', 100), ('2020', -30), ('2021', 0), ('2021', '')])

    def test_invalid_numeric_or_sparse_data_rejected(self):
        for value in ([100, 0, float('nan'), None], {'4': 5}, [100, 0, True, None], [100]):
            with self.subTest(value=value):
                data = dataset()
                request = FETCH.selection(data, {'years': [2020, 2021]})
                data['value'] = value
                with self.assertRaises(ValueError):
                    list(FETCH.observations(data, request, 'TEST'))


if __name__ == '__main__':
    unittest.main()
