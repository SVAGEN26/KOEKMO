"""Panel integrity, temporal isolation, and equal-municipality scoring."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from motala_lab import external_pkv as panel


class PanelTests(unittest.TestCase):
    def setUp(self):
        self.candidate, self.protocol, self.macros = panel.load_frozen()
        self.data = panel.read(panel.ROOT/'data/external-pkv-ledgers.json')

    def run_panel(self, data=None):
        return panel.evaluate(data or self.data, self.protocol, self.macros, self.candidate)

    def test_all_declared_cases_retained_including_missing(self):
        result = self.run_panel()
        self.assertEqual(len(result['cases']), 18)
        self.assertEqual([s['expected'] for s in result['scores']], [9, 6, 3])
        for c in result['cases']:
            if c['actual'] is None:
                self.assertFalse(c['comparable'])
                self.assertTrue(c['missingReasons'])
                self.assertEqual(c['errors'], {})

    def test_future_outcomes_cannot_change_origin_forecasts(self):
        before = [c['predictions'] for c in self.run_panel()['cases'] if c['origin'] == 2022]
        changed = deepcopy(self.data)
        for city in changed['municipalities']:
            for row in city['rows']:
                if row['year'] > 2022:
                    row['result'] = (row['result'] or 0)+100
                    if 'tax' in row:
                        row['tax'] += 100  # Preserve the future ledger identity.
        after = [c['predictions'] for c in self.run_panel(changed)['cases'] if c['origin'] == 2022]
        self.assertEqual(before, after)

    def test_reject_changed_frozen_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'frozen'
            shutil.copytree(panel.ROOT/'reference/pkv-accounting-v1', path)
            with (path/'macro.py').open('a') as stream:
                stream.write('\n# alteration\n')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                panel.load_frozen(path)

    def test_ledger_adapter_does_not_double_count_pensions_or_remove_oneoffs(self):
        row = next(m for m in self.data['municipalities'] if m['id'] == '0581')['rows'][2]
        adapted = panel.opening(row)
        self.assertEqual(adapted['payroll']+adapted['pension'], 5560+487)
        self.assertEqual(adapted['otherExpense'], 13564-6047)
        self.assertEqual(adapted['resultRounding'], 0)
        vintage = self.candidate.select_vintage(self.macros, 2022, 1)
        prediction = self.candidate.accounting_projection(adapted, vintage, self.protocol['parameters'])[0]
        independent = 7344*1.035+2303*1.02+2032*1.02-6047*1.072-7517*1.045-610+640-1028
        self.assertAlmostEqual(prediction['result'], independent)

    def test_scoring_equal_city_weight_not_currency_size_or_number_of_cases(self):
        def case(mid, error):
            return dict(municipalityId=mid, comparable=True,
                errors={m: dict(errorMnkr=error*10, errorPercentagePoints=error) for m in panel.MODELS})
        cells = [case('A', 1), case('A', 1), case('B', 3)]
        self.assertEqual(panel.equal_municipality(cells, ['A', 'B']), {m: 2 for m in panel.MODELS})
        self.assertIsNone(panel.equal_municipality(cells, ['A', 'B', 'C']))

    def test_reject_panel_selection_and_unit_errors(self):
        changed = deepcopy(self.data)
        changed['municipalities'].pop()
        with self.assertRaisesRegex(ValueError, 'predeclared'):
            self.run_panel(changed)
        changed = deepcopy(self.data)
        changed['moneyUnit'] = 'tkr'
        with self.assertRaisesRegex(ValueError, 'mnkr'):
            self.run_panel(changed)

    def test_reject_unexplained_ledger_difference(self):
        row = deepcopy(self.data['municipalities'][0]['rows'][2])
        row['grossExpense'] += 10
        with self.assertRaisesRegex(ValueError, 'accounting residual'):
            panel.opening(row)
        row = deepcopy(self.data['municipalities'][0]['rows'][2])
        row['result'] += 10
        with self.assertRaisesRegex(ValueError, 'accounting residual'):
            panel.opening(row)
        row = deepcopy(self.data['municipalities'][0]['rows'][2])
        del row['roundingUnitMnkr']
        with self.assertRaisesRegex(ValueError, 'precision'):
            panel.opening(row)

    def test_archive_reruns_without_repository_or_environment_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp)/'first', Path(tmp)/'second'
            panel.main(['--out', str(first)])
            environment = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
            run = subprocess.run([sys.executable, '-E', str(first/'sources/run_external_pkv.py'),
                                  '--out', str(second)], cwd=tmp, env=environment,
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads((first/'evaluation.json').read_text())['cases'],
                             json.loads((second/'evaluation.json').read_text())['cases'])


if __name__ == '__main__':
    unittest.main()
