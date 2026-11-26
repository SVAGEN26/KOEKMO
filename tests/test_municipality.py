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
        source = (ROOT / 'modelica/municipalities/Mjolby/package.mo').read_text()
        self.assertIn('extends Kommunekonomi.Continuous.Economy(base = Data.mjolby2025', source)
        for y, r in years('0586').items():
            self.assertIn(f'constant BaseYear mjolby{y} = BaseYear(', source)
            self.assertAlmostEqual(sum(r['cohorts'][-1]), r['reportedPopulation'][-1], delta=0.5)
            self.assertEqual(r['openingDebt'], years('0586').get(str(int(y) - 1), {'debt': r['openingDebt']})['debt'])


class OwnDebt(unittest.TestCase):
    """Debt is the municipality's own: what it has lent on to its companies is taken out, with the interest on it."""

    def inputs(self, code):
        return json.loads((ROOT / f'data/municipalities/{code}/annual-report-inputs.json').read_text())

    def test_finspang_is_the_external_borrowing_less_the_loans_to_its_companies(self):
        # Annual report 2025: borrowed 131, lent on 138, so the municipality's own loans fell by 7.
        r, external = years('0562'), self.inputs('0562')['externalBankDebt']
        for y in ('2024', '2025'):
            self.assertAlmostEqual(r[y]['debt'], external[y] - r[y]['onLending']['loans'], places=6)
        self.assertAlmostEqual(r['2025']['debt'], 290, delta=0.5)
        self.assertAlmostEqual(r['2025']['debt'] - r['2024']['debt'], 131 - 138, delta=0.6)
        self.assertEqual(r['2025']['openingDebt'], r['2024']['debt'])

    def test_reported_own_debt_is_used_where_scb_does_not_give_it(self):
        for code in ('0580', '0581'):
            for y, own in self.inputs(code)['ownDebt'].items():
                self.assertEqual(years(code)[y]['debt'], own, msg=f'{code} {y}')
        # Linköping's finance report, 31 December 2025: 16 616 borrowed, 15 516 of it for the companies.
        self.assertEqual(years('0580')['2025']['debt'] + years('0580')['2025']['onLending']['loans'], 16616)
        # Norrköping's annual report 2025: the group's gross debt is 17 955, the municipality's 8 852.
        self.assertEqual(years('0581')['2025']['debt'] + years('0581')['2025']['onLending']['loans'], 17955)

    def test_the_result_is_scbs_with_the_lent_part_taken_out(self):
        """Taking the lent part's interest out of both cost and income leaves the result as SCB publishes it."""
        for code in ('0562', '0563', '0580'):
            for name, y in (('web.json', '2025'), ('web-2024.json', '2024')):
                published = json.loads((ROOT / f'data/municipalities/{code}/{name}').read_text())['baseline']['publishedResult']
                r = years(code)[y]
                self.assertGreater(r['onLending']['interest'], 0, msg=f'{code} {y}')
                net = r['payroll'] + r['pension'] + r['otherOperatingExpense'] - r['operatingRevenue'] + r['depreciation']
                result = r['tax'] + r['grants'] - net + r['financialIncome'] - r['interestExpense'] - r['otherFinancialExpense']
                self.assertAlmostEqual(result, published, delta=0.01, msg=f'{code} {y}')
        for code in ('0562', '0563', '0580', '0581'):
            for y, r in years(code).items():
                self.assertGreaterEqual(r['debt'], 0, msg=f'{code} {y}')
                self.assertGreaterEqual(r['interestExpense'], 0, msg=f'{code} {y}')
                self.assertGreaterEqual(r['financialIncome'], 0, msg=f'{code} {y}')
        # Linköping 2025: 361 mnkr of interest on 16.6 billion; 23 of it is on the municipality's own 1.1 billion,
        # the rate it pays on all its borrowing.
        lin = years('0580')['2025']
        self.assertAlmostEqual(lin['interestExpense'] / ((lin['debt'] + lin['openingDebt']) / 2), 360.753 / ((16616 + 16583) / 2), places=6)

    def test_interest_on_the_lent_part_leaves_cost_and_income_alike(self):
        """Against SCB's tables: the same amount leaves interest expense and financial income, and it is never more
        than the interest income booked. The downloaded tables are not in git, so this runs where they are."""
        archive = lambda code: ROOT / json.loads((ROOT / f'data/municipalities/{code}/base-years.json').read_text())['archive']
        codes = ('0562', '0563', '0580', '0581')
        if not all((archive(code) / 'TAB6782.json').exists() for code in codes):
            self.skipTest('SCB archives under data/downloads/ are not in this checkout')
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        from prepare_municipality import jsonstat
        for code in codes:
            rr, tx = jsonstat(archive(code) / 'TAB6777.json'), jsonstat(archive(code) / 'TAB6782.json')
            supplement = self.inputs(code) if (ROOT / f'data/municipalities/{code}/annual-report-inputs.json').exists() else {}
            for y, r in years(code).items():
                lent = r.get('onLending')
                if not lent:
                    continue
                gross = supplement.get('bankInterest', {}).get(y, tx['380'][int(y)])
                self.assertAlmostEqual(r['interestExpense'] + lent['interest'], gross, places=6, msg=f'{code} {y}')
                self.assertAlmostEqual(r['financialIncome'] + lent['interest'], rr['060'][int(y)], places=6, msg=f'{code} {y}')
                self.assertGreaterEqual(lent['interest'], 0)
                self.assertLessEqual(lent['interest'], max(tx['260'][int(y)], 0) + 1e-9, msg=f'{code} {y}: more than the interest income')

    def test_a_municipality_without_such_loans_is_unchanged(self):
        for code in ('0586', '0582', '0509'):
            for y, r in years(code).items():
                self.assertNotIn('onLending', r, msg=f'{code} {y}')


if __name__ == '__main__':
    unittest.main()
