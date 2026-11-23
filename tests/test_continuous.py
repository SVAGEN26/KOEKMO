"""Continuous.Economy against Annual and against its own bookkeeping.

The continuous model has its own demography (stocks and flows) and indices that grow within the year,
so it is not identical to Annual. It must still agree where the rules agree: the same reference path
gives the same annual tax and grants, constant growth gives the same annual index, and every stock and
the population reconcile at each year end.

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
            f'loadFile("{ROOT / "modelica/Motala.mo"}"); getErrorString();',
            'loadFile("Reference.mo"); getErrorString();',
            'simulate(Motala.Annual, startTime=2025, stopTime=2033, numberOfIntervals=8, outputFormat="csv"); getErrorString();',
            'simulate(Motala.Continuous, startTime=2025, stopTime=2033, numberOfIntervals=96, outputFormat="csv"); getErrorString();',
            'simulate(Motala.Continuous, startTime=2025, stopTime=2033, numberOfIntervals=96, outputFormat="csv",'
            ' simflags="-override=workingCapitalEnabled=true,collectionDays=30,paymentDays=30,liquidityPolicy=true,cashReserve=150,constructionYears=2",'
            ' fileNamePrefix="Stress"); getErrorString();',
            'simulate(Reference, startTime=2025, stopTime=2033, numberOfIntervals=96, outputFormat="csv"); getErrorString();',
            'simulate(Motala.Examples.AnnualCohort, startTime=2025, stopTime=2030, numberOfIntervals=5, outputFormat="csv"); getErrorString();',
            'simulate(Motala.Examples.ContinuousCohort, startTime=2025, stopTime=2030, numberOfIntervals=60, outputFormat="csv"); getErrorString();'])
        (cls.dir / 'run.mos').write_text(script)
        subprocess.run([OMC, 'run.mos'], cwd=cls.dir, capture_output=True, text=True, timeout=900)
        cls.annual = year_rows(cls.dir / 'Motala.Annual_res.csv')
        cls.continuous = year_rows(cls.dir / 'Motala.Continuous_res.csv')
        cls.stress = year_rows(cls.dir / 'Stress_res.csv')
        cls.reference = year_rows(cls.dir / 'Reference_res.csv')
        cls.reference_all = all_rows(cls.dir / 'Reference_res.csv')
        cls.annual_cohort = year_rows(cls.dir / 'Motala.Examples.AnnualCohort_res.csv')
        cls.cohort = year_rows(cls.dir / 'Motala.Examples.ContinuousCohort_res.csv')
        cls.cohort_all = all_rows(cls.dir / 'Motala.Examples.ContinuousCohort_res.csv')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_same_years(self):
        self.assertEqual(sorted(self.annual), list(range(2025, 2034)))
        self.assertEqual(sorted(self.continuous), sorted(self.annual))

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

    def test_constant_growth_gives_annual_index(self):
        # With the same growth every year the continuous index has Annual's annual means.
        for year, a in self.annual.items():
            c = self.continuous[year]
            for key in ('wageIndex', 'priceIndex', 'revenueIndex'):
                self.assertAlmostEqual(c[key], a[key], places=5, msg=f'{key} {year}')

    def test_changed_growth_is_smoothed_not_delayed(self):
        # A wage jump in 2028 (6 % instead of 3 %): the annual mean rises by about (3 + 4*6 + 3)/6 = 5 % that year
        # and by about (6 + 4*3 + 3)/6 = 3.5 % the year after, and the level ends where the path does.
        idx = {y: r['wageIndex'] for y, r in self.reference.items()}
        self.assertAlmostEqual(idx[2028]/idx[2027] - 1, 0.050, delta=0.003)
        self.assertAlmostEqual(idx[2029]/idx[2028] - 1, 0.035, delta=0.003)
        path = 1.0
        for g in WAGES:
            path *= 1 + g
        self.assertAlmostEqual(idx[2033]/path, 1, delta=0.003)

    def test_demography_close_to_annual(self):
        for year, a in self.annual.items():
            c = self.continuous[year]
            self.assertLess(abs(c['population']/a['population'] - 1), 0.001, year)
            for key in ('tax', 'grants'):
                self.assertLess(abs(c[key]/a[key] - 1), 0.002, f'{key} {year}')
        for year, a in self.annual_cohort.items():
            c = self.cohort[year]
            self.assertLess(abs(c['population']/a['population'] - 1), 0.001, year)
            # Single years age by relabelling at the turn of the year, so a group that only ages matches closely.
            self.assertLess(abs(c['p[3]']/a['p[3]'] - 1), 0.01, year)

    def test_population_is_continuous(self):
        # The relabelling at the turn of the year moves no one: no age group jumps at a year end.
        previous = None
        for row in self.cohort_all:
            if previous is not None and abs(row['time'] - previous['time']) < 1e-9:
                for key in ('population', 'p[1]', 'p[2]', 'p[3]', 'p[4]', 'p[5]'):
                    self.assertAlmostEqual(row[key], previous[key], delta=1e-6, msg=f'{key} {row["time"]}')
            previous = row

    def test_base_year_row_is_the_accounts(self):
        a, c = self.annual[2025], self.continuous[2025]
        for key in ('result', 'cost', 'depreciation', 'interest', 'debt', 'cash', 'assets', 'operatingCash', 'population', 'tax', 'grants'):
            self.assertAlmostEqual(c[key], a[key], places=6, msg=key)

    def test_depreciation_matches_without_construction_time(self):
        for year, a in self.annual.items():
            self.assertAlmostEqual(self.continuous[year]['depreciation'], a['depreciation'], delta=0.5, msg=year)

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
