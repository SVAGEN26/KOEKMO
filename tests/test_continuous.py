"""Continuous.Economy against Annual: same rules where time within the year does not matter.

Needs OpenModelica (OMC or omc on PATH); skipped otherwise.
"""
import csv
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OMC = os.environ.get('OMC') or shutil.which('omc')


def year_rows(path):
    rows = {}
    with path.open() as handle:
        for row in csv.DictReader(handle):
            t = float(row['time'])
            if abs(t - round(t)) < 1e-9:
                rows[round(t)] = {k: float(v) for k, v in row.items()}  # last row at a year is after the event
    return rows


@unittest.skipUnless(OMC, 'OpenModelica not available')
class ContinuousEconomy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = Path(tempfile.mkdtemp(prefix='continuous-'))
        script = '\n'.join([
            f'loadFile("{ROOT / "modelica/Kommunekonomi.mo"}"); getErrorString();',
            f'loadFile("{ROOT / "modelica/Motala.mo"}"); getErrorString();',
            'simulate(Motala.Annual, startTime=2025, stopTime=2033, numberOfIntervals=8, outputFormat="csv"); getErrorString();',
            'simulate(Motala.Continuous, startTime=2025, stopTime=2033, numberOfIntervals=96, outputFormat="csv"); getErrorString();',
            'simulate(Motala.Continuous, startTime=2025, stopTime=2033, numberOfIntervals=96, outputFormat="csv",'
            ' simflags="-override=workingCapitalEnabled=true,collectionDays=30,paymentDays=30,liquidityPolicy=true,cashReserve=150,constructionYears=2",'
            ' fileNamePrefix="Stress"); getErrorString();'])
        (cls.dir / 'run.mos').write_text(script)
        subprocess.run([OMC, 'run.mos'], cwd=cls.dir, capture_output=True, text=True, timeout=900)
        cls.annual = year_rows(cls.dir / 'Motala.Annual_res.csv')
        cls.continuous = year_rows(cls.dir / 'Motala.Continuous_res.csv')
        cls.stress = year_rows(cls.dir / 'Stress_res.csv')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_same_years(self):
        self.assertEqual(sorted(self.annual), list(range(2025, 2034)))
        self.assertEqual(sorted(self.continuous), sorted(self.annual))

    def test_rules_set_at_the_start_of_the_year_match(self):
        # Demography and revenue run the annual components one step early; the result must not move.
        for year, a in self.annual.items():
            c = self.continuous[year]
            for key in ('population', 'p[1]', 'p[5]', 'births', 'deaths', 'tax', 'grants', 'wageIndex', 'priceIndex'):
                self.assertAlmostEqual(c[key], a[key], places=6, msg=f'{key} {year}')

    def test_base_year_row_is_the_accounts(self):
        a, c = self.annual[2025], self.continuous[2025]
        for key in ('result', 'cost', 'depreciation', 'interest', 'debt', 'cash', 'assets', 'operatingCash'):
            self.assertAlmostEqual(c[key], a[key], places=6, msg=key)

    def test_depreciation_matches_without_construction_time(self):
        for year, a in self.annual.items():
            self.assertAlmostEqual(self.continuous[year]['depreciation'], a['depreciation'], delta=0.5, msg=year)

    def test_stocks_and_flows_balance(self):
        for rows in (self.continuous, self.stress):
            for year, c in rows.items():
                for key in ('equityBalance', 'assetBalance', 'cashBalance', 'debtBalance', 'populationBalance'):
                    self.assertLess(abs(c[key]), 1e-6, f'{key} {year}')

    def test_result_is_its_parts(self):
        for year, c in self.stress.items():
            if year == 2025:
                continue
            parts = c['tax'] + c['grants'] - c['cost'] - c['depreciation'] + c['finance.financial.annual'] - c['interest'] - c['finance.otherFinancial.annual']
            self.assertAlmostEqual(c['result'], parts, places=6)

    def test_liquidity_policy_holds_the_reserve(self):
        for year, c in self.stress.items():
            if year > 2025:
                self.assertGreater(c['cash'], 150 - 1, year)


if __name__ == '__main__':
    unittest.main()
