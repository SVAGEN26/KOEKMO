"""Base years built from SCB for any municipality (scripts/prepare_municipality.py)."""
import json
import unittest
from pathlib import Path

from test_base_years import record

ROOT = Path(__file__).resolve().parents[1]


def years(code):
    return json.loads((ROOT / f'data/municipalities/{code}/base-years.json').read_text())['years']


class FromSCB(unittest.TestCase):
    def test_motala_from_scb_matches_the_annual_reports(self):
        """A second source for Motala's base years. From 2023 the definitions agree; before that the
        reports split payroll and pension differently, and SCB's fixed assets include work in progress."""
        scb = years('0583')
        for y in range(2020, 2026):
            r = record(f'motala{y}')
            exact = ['tax', 'depreciation', 'financialIncome', 'interestExpense', 'debt', 'openingDebt', 'cash', 'investment']
            if y != 2021:  # SCB books 19.5 mnkr of 2021's operating revenue as a general grant
                exact += ['grants', 'operatingRevenue']
            if y >= 2023:
                exact += ['payroll', 'pension', 'otherOperatingExpense']
            for key in exact:
                # Other operating expense is the residual of gross costs, so it gathers the rounding of the rest.
                self.assertAlmostEqual(scb[str(y)][key], r[key], delta=3 if key == 'otherOperatingExpense' else 2, msg=f'{y} {key}')
            self.assertAlmostEqual(scb[str(y)]['payroll'] + scb[str(y)]['pension'], r['payroll'] + r['pension'], delta=16, msg=f'{y} personnel')
            for i in range(5):
                self.assertAlmostEqual(scb[str(y)]['grantComponents'][i], r['grantComponents'][i], delta=2, msg=f'{y} grant component {i}')
            self.assertAlmostEqual(scb[str(y)]['priorYearSettlement'], r['priorYearSettlement'], delta=1, msg=f'{y} settlement')

    def test_generated_package_carries_the_base_years(self):
        source = (ROOT / 'modelica/municipalities/Mjolby.mo').read_text()
        self.assertIn('extends Kommunekonomi.Annual(base = Data.mjolby2025', source)
        for y, r in years('0586').items():
            self.assertIn(f'constant BaseYear mjolby{y} = BaseYear(', source)
            self.assertAlmostEqual(sum(r['cohorts'][-1]), r['reportedPopulation'][-1], delta=0.5)
            self.assertEqual(r['openingDebt'], years('0586').get(str(int(y) - 1), {'debt': r['openingDebt']})['debt'])


if __name__ == '__main__':
    unittest.main()
