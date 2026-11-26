"""The migration-window test (scripts/hindcast_migration.py): its copy of the demography is the model's."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hindcast_migration as hm  # noqa: E402

ARCHIVES = (ROOT / json.loads((ROOT / 'data/municipalities/ostergotland-sources.json').read_text())['historyArchive'] / 'population.json').exists()


class MigrationGroups(unittest.TestCase):
    """SKR's municipality groups and their migration (data/migration-groups.json, scripts/fetch_migration_groups.py)."""

    @classmethod
    def setUpClass(cls):
        cls.table = json.loads((ROOT / 'data/migration-groups.json').read_text())
        cls.hindcast = json.loads((ROOT / 'data/migration-hindcast.json').read_text())['migrationBasis']

    def test_the_nine_groups_cover_sweden_and_the_county_has_four_of_them(self):
        groups = self.table['groups']
        self.assertEqual(sorted(groups), ['A1', 'A2', 'B3', 'B4', 'B5', 'C6', 'C7', 'C8', 'C9'])
        self.assertEqual(sum(g['municipalities'] for g in groups.values()), 290)
        county = self.table['municipalities']
        self.assertEqual(len(county), 13)
        self.assertEqual({m['group'] for m in county.values()}, {'B3', 'B4', 'B5', 'C7'})
        self.assertEqual((county['0583']['group'], groups['B5']['name']), ('B5', 'Lågpendlingskommun nära större stad'))
        self.assertEqual(county['0580']['group'], 'B3')
        for rates in [g['rates'] for g in groups.values()] + [m['rates'] for m in county.values()]:
            self.assertEqual(sorted(rates), [str(y) for y in range(2000, 2026)])
            self.assertTrue(all(len(r) == 5 and all(abs(x) < 0.2 for x in r) for r in rates.values()))

    def test_the_refugee_years_show_in_the_groups_that_lose_people_otherwise(self):
        # The working ages in rural municipalities: about 4 per 1 000 leave in an ordinary year; 2016, when those granted
        # asylum were placed, 10 per 1 000 arrived. The same year is the peak in Motala's group.
        for group in ('C8', 'B5'):
            rates = {int(y): r[3] for y, r in self.table['groups'][group]['rates'].items()}
            self.assertEqual(max(rates, key=rates.get), 2016, group)
            self.assertGreater(rates[2016], 0.01, group)
        rural = {int(y): r[3] for y, r in self.table['groups']['C8']['rates'].items()}
        self.assertLess(sum(rural[y] for y in range(2018, 2026)) / 8, -0.003)

    def test_the_base_year_records_carry_the_two_year_means(self):
        from prepare_municipality import migration_rates
        for code in ('0562', '0580', '0584'):
            years = json.loads((ROOT / f'data/municipalities/{code}/base-years.json').read_text())['years']
            for year in ('2024', '2025'):
                own, group = migration_rates(self.table, code, int(year))
                self.assertEqual(years[year]['ownMigration'], own)
                self.assertEqual(years[year]['groupMigration'], group)
        motala = (ROOT / 'modelica/municipalities/Motala.mo').read_text()
        own, group = migration_rates(self.table, '0583', 2025)
        self.assertIn('groupMigration = {' + ', '.join(f'{x:g}' for x in group) + '}, ownMigration = {' + ', '.join(f'{x:g}' for x in own) + '}', motala)

    def test_half_own_half_group_gives_the_lowest_error_and_own_is_the_models_window(self):
        windows = json.loads((ROOT / 'data/migration-hindcast.json').read_text())['summary']
        for period, basis in ((k, v) for k, v in self.hindcast.items() if k != 'note'):
            self.assertEqual(basis['own'], windows[period]['modelBirths']['2'])
            for horizon in ('1', '2', '3', '4', '5'):
                self.assertLess(basis['half'][horizon]['meanAbsError'], basis['own'][horizon]['meanAbsError'], (period, horizon))
                self.assertLess(basis['half'][horizon]['meanAbsError'], basis['group'][horizon]['meanAbsError'] + 0.02, (period, horizon))
        recent = self.hindcast['bases2020to2024']
        self.assertAlmostEqual(recent['own']['4']['meanAbsError'], 1.76, delta=0.02)
        self.assertAlmostEqual(recent['half']['4']['meanAbsError'], 1.37, delta=0.02)
        # From the refugee years the group does not help at eight years: it too was calibrated on 2016-2017.
        self.assertGreater(self.hindcast['bases2017to2024']['half']['8']['meanAbsError'], self.hindcast['bases2017to2024']['own']['8']['meanAbsError'])


class Stored(unittest.TestCase):
    def test_the_result_covers_every_window_and_says_what_it_shows(self):
        out = json.loads((ROOT / 'data/migration-hindcast.json').read_text())
        self.assertEqual(out['windows'], [1, 2, 3, 5, 8])
        recent = out['summary']['bases2020to2024']['modelBirths']
        for w in ('2', '3'):
            self.assertEqual(recent[w]['1']['cases'], 13 * 5)
        # From the refugee years the two-year window gives about 6 % too many people after eight years.
        self.assertGreater(out['summary']['bases2017to2024']['modelBirths']['2']['8']['meanError'], 5)
        self.assertEqual(len(out['residualFlowFrom2025']), 13)


@unittest.skipUnless(ARCHIVES, 'SCB archives under data/downloads/ are not in this checkout')
class AgainstTheModel(unittest.TestCase):
    def test_two_years_give_the_models_population(self):
        """The model's own population in the eight-year hindcast (hindsight set, two-year calibration).

        The script steps once a year with a fixed 65+ death rate; the model's flows run during the year and 65+ is an
        ageing chain whose deaths rise as 80+ grows. They agree within 1 per cent (largest: Valdemarsvik 2025 from
        2017, 0.8 %)."""
        runs = [r for r in json.loads((ROOT / 'data/long-hindcast-continuous.json').read_text())['runs'] if r['assumptions'] == 'hindsight']
        cache = {}
        for r in runs:
            code = r['municipality']
            cache.setdefault(code, hm.series(code))
            projected, _ = hm.project(*cache[code], r['origin'], 2)
            self.assertAlmostEqual(sum(projected[r['year']]) / r['model']['population'], 1, delta=1e-2, msg=f"{code} {r['origin']} {r['year']}")


if __name__ == '__main__':
    unittest.main()
