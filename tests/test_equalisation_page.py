"""The page that explains the equalisation system (site/src/utjamning.html) and its table for the 13 municipalities."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EqualisationPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / 'site/src/utjamning.html').read_text()
        cls.county = json.loads((ROOT / 'data/equalisation-county.json').read_text())
        cls.all = json.loads((ROOT / 'data/equalisation.json').read_text())

    def test_the_table_is_scbs_latest_year_for_the_13_municipalities(self):
        self.assertEqual(self.county['year'], self.all['years'][1])
        self.assertEqual(len(self.county['municipalities']), 13)
        for m in self.county['municipalities']:
            source = self.all['municipalities'][m['code']]['years'][str(self.county['year'])]
            for field in ('income', 'cost', 'structure', 'regulation', 'total', 'lss'):
                self.assertEqual(m[field], source[field], (m['name'], field))
            self.assertEqual(m['income'] + m['cost'] + m['structure'] + m['regulation'], m['total'], m['name'])

    def test_the_regulation_grant_on_the_page_is_the_tables(self):
        regulation = {m['regulation'] for m in self.county['municipalities']}
        self.assertEqual(len(regulation), 1)  # the same per inhabitant everywhere
        self.assertIn(f'{regulation.pop():,}'.replace(',', ' '), self.page)
        # 29 694 mnkr is what is left of the appropriation when the other parts are paid.
        self.assertEqual(107988 - 14319 + 12068 - 12143 + 1039, 94633)
        self.assertEqual(124327 - 94633, 29694)
        for amount in ('124 327', '94 633', '29 694', '107 988', '14 319', '12 068', '12 143', '1 039'):
            self.assertIn(amount, self.page)

    def test_the_count_of_receiving_municipalities_is_scbs_table(self):
        income = [m['years'][str(self.county['year'])]['income'] for m in self.all['municipalities'].values()]
        self.assertEqual((sum(x > 0 for x in income), sum(x < 0 for x in income)), (273, 17))
        self.assertIn('273 kommuner bidrag och 17 betalade avgift', self.page)

    def test_the_example_follows_from_the_stated_numbers(self):
        self.assertIn('293 581', self.page)
        self.assertIn('18,93', self.page)
        self.assertAlmostEqual((1.15 - 0.90) * 293581 * 0.1893, 13900, delta=10)
        self.assertIn('≈ 13 900', self.page)
        parts = (15127, 13934, 10077, 5826, 5038, 1567, 756, 239, 110)
        self.assertEqual(sum(parts), 52674)
        for part in parts + (52674,):
            self.assertIn(f'{part:,}'.replace(',', ' '), self.page)

    def test_every_claim_points_to_a_listed_source(self):
        listed = set(re.findall(r'<li id="(k\d+)">', self.page))
        cited = set(re.findall(r'href="#(k\d+)"', self.page))
        self.assertEqual(cited, listed)
        self.assertGreaterEqual(len(listed), 10)
        sources = self.page[self.page.index('<ol class="sources">'):]
        links = re.findall(r'href="(https://[^"]+)"', sources)
        self.assertGreaterEqual(len(links), len(listed))
        for link in links:
            self.assertRegex(link, r'^https://(www\.riksdagen\.se|data\.riksdagen\.se|www\.scb\.se|www\.regeringen\.se|skatteverket\.se)/')

    def test_the_page_is_shipped_and_linked(self):
        self.assertIn('href="utjamning.html"', (ROOT / 'site/src/index.html').read_text())
        self.assertIn("'equalisation-county.json'", (ROOT / 'scripts/build.py').read_text())
        self.assertIn('lang="sv"', self.page)


if __name__ == '__main__':
    unittest.main()
