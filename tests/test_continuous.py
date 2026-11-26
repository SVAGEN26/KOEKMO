"""Continuous.Economy, natively compiled: its decisions, indices and own bookkeeping.

Tax and grants are decided for a year and paid evenly, so a reference path gives the same yearly amounts. Wage and
price indices grow within the year so that the yearly mean follows the stated growth. Every stock and the
population reconcile at each year end.

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
TAX = [2400, 2480, 2550, 2640, 2700, 2790, 2850, 2950]
GRANTS = [1000, 1010, 1030, 1060, 1070, 1100, 1120, 1150]
TAX_RATE = [21.7, 21.7, 22.2, 22.2, 22.2, 21.95, 21.95, 21.95]
WAGES = [0.03, 0.035, 0.06, 0.03, 0.03, 0.03, 0.03, 0.03]
REFERENCE = f'''model Reference "Skatt och bidrag enligt en given bana; skattesatsen och lönerna ändras"
  extends Motala.Continuous(revenueFromReference = true, referenceTax = {{{", ".join(map(str, TAX))}}},
    referenceGrants = {{{", ".join(map(str, GRANTS))}}}, taxRatePath = {{{", ".join(map(str, TAX_RATE))}}},
    wageGrowthPath = {{{", ".join(map(str, WAGES))}}});
end Reference;
'''


def year_rows(path):
    rows = {}
    with path.open() as handle:
        for row in csv.DictReader(handle):
            t = float(row['time'])
            if abs(t - round(t)) < 1e-9:
                rows[round(t)] = {k: float(v) for k, v in row.items()}  # last row at a year is after the event
    return rows


def all_rows(path):
    with path.open() as handle:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(handle)]


@unittest.skipUnless(OMC, 'OpenModelica not available')
class ContinuousEconomy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = Path(tempfile.mkdtemp(prefix='continuous-'))
        (cls.dir / 'Reference.mo').write_text(REFERENCE)
        script = '\n'.join([
            f'loadFile("{ROOT / "modelica/Kommunekonomi.mo"}"); getErrorString();',
            f'loadFile("{ROOT / "modelica/municipalities/Motala.mo"}"); getErrorString();',
            'loadFile("Reference.mo"); getErrorString();',
            'simulate(Motala.Continuous, startTime=2025, stopTime=2033, numberOfIntervals=96, outputFormat="csv"); getErrorString();',
            'simulate(Motala.Continuous, startTime=2025, stopTime=2033, numberOfIntervals=96, outputFormat="csv",'
            ' simflags="-override=workingCapitalEnabled=true,collectionDays=30,paymentDays=30,liquidityPolicy=true,reserveDays=15,creditLine=0,reserveAdjustmentTime=0,constructionYears=2",'
            ' fileNamePrefix="Stress"); getErrorString();',
            'simulate(Reference, startTime=2025, stopTime=2033, numberOfIntervals=96, outputFormat="csv"); getErrorString();',
            'simulate(Motala.Examples.ContinuousCohort, startTime=2025, stopTime=2030, numberOfIntervals=60, outputFormat="csv"); getErrorString();'])
        (cls.dir / 'run.mos').write_text(script)
        subprocess.run([OMC, 'run.mos'], cwd=cls.dir, capture_output=True, text=True, timeout=900)
        cls.continuous = year_rows(cls.dir / 'Motala.Continuous_res.csv')
        cls.stress = year_rows(cls.dir / 'Stress_res.csv')
        cls.reference = year_rows(cls.dir / 'Reference_res.csv')
        cls.reference_all = all_rows(cls.dir / 'Reference_res.csv')
        cls.cohort = year_rows(cls.dir / 'Motala.Examples.ContinuousCohort_res.csv')
        cls.cohort_all = all_rows(cls.dir / 'Motala.Examples.ContinuousCohort_res.csv')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_same_years(self):
        self.assertEqual(sorted(self.continuous), list(range(2025, 2034)))

    def test_annual_amounts_follow_the_reference_path(self):
        # Tax and grants are decided for the year on 1 January and paid evenly; the year's total is the decision.
        for i, year in enumerate(range(2026, 2034)):
            r = self.reference[year]
            self.assertAlmostEqual(r['tax'], TAX[i]*TAX_RATE[i]/21.7, places=6, msg=year)
            self.assertAlmostEqual(r['grants'], GRANTS[i], places=6, msg=year)
        for row in self.reference_all:
            t = row['time']
            if 2026 < t < 2027 and abs(t - round(t)) > 1e-6:
                self.assertAlmostEqual(row['finance.tax.rate'], TAX[1]*TAX_RATE[1]/21.7, places=6, msg=t)

    def test_constant_growth_gives_a_constant_yearly_rise(self):
        # With the same growth every year the index rises by the same share every year.
        for key in ('wageIndex', 'priceIndex', 'revenueIndex'):
            rises = [self.continuous[y][key]/self.continuous[y - 1][key] for y in range(2027, 2034)]
            self.assertLess(max(rises) - min(rises), 1e-5, key)

    def test_changed_growth_keeps_the_annual_means(self):
        # A wage jump in 2028 (6 % instead of 3 %): the annual mean still rises by the path's growth every year.
        # The rates within the year are chosen for that (Data.meanPreservingRates); the level itself moves smoothly.
        idx = {y: r['wageIndex'] for y, r in self.reference.items()}
        path = 1.0
        for year, g in zip(range(2026, 2034), WAGES):
            path *= 1 + g
            self.assertAlmostEqual(idx[year]/idx[year - 1] - 1, g, delta=1e-4, msg=str(year))
            self.assertAlmostEqual(idx[year]/path, 1, delta=1e-4, msg=str(year))

    def test_single_years_stay_near_the_five_groups(self):
        # Two calibrations of the same population; they drift apart slowly (under 2 % in five years).
        for year, c in self.cohort.items():
            self.assertLess(abs(c['population']/self.continuous[year]['population'] - 1), 0.02, year)

    def test_population_is_continuous(self):
        # The relabelling at the turn of the year moves no one: no age group jumps at a year end.
        previous = None
        for row in self.cohort_all:
            if previous is not None and abs(row['time'] - previous['time']) < 1e-9:
                for key in ('population', 'p[1]', 'p[2]', 'p[3]', 'p[4]', 'p[5]'):
                    self.assertAlmostEqual(row[key], previous[key], delta=1e-6, msg=f'{key} {row["time"]}')
            previous = row

    def test_base_year_row_is_the_accounts(self):
        # Motala's accounts 2025 (Motala.Data.motala2025): debt, cash, assets, depreciation, tax and grants.
        c = self.continuous[2025]
        for key, value in (('debt', 1040), ('cash', 81), ('assets', 2997), ('depreciation', 180), ('tax', 2330), ('grants', 987)):
            self.assertAlmostEqual(c[key], value, places=6, msg=key)

    def test_stocks_and_flows_balance(self):
        for rows in (self.continuous, self.stress, self.reference, self.cohort):
            for year, c in rows.items():
                for key in ('equityBalance', 'revenueBalance', 'assetBalance', 'cashBalance', 'debtBalance', 'populationBalance'):
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
