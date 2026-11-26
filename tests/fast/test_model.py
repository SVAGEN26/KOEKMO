"""Fast tests of the Modelica model itself, through OMPython and native OpenModelica.

Each scenario in tests/fast/Scenarios.mo is a small Modelica model, compiled once (about three seconds) and simulated
natively, so the whole file takes about a minute. These are the tests to run while changing the model:

    python3 -m unittest discover -s tests/fast

The browser's wasm tests (tests/*.test.mjs) are slower; run them before opening a pull request.
Needs OMPython (pip install OMPython) and omc (OPENMODELICAHOME, OMC or omc on PATH); skipped otherwise.
"""
import os
import shutil
import tempfile
import unittest
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
try:
    import numpy as np
    from OMPython import ModelicaSystemOMC
except ImportError:  # pragma: no cover
    ModelicaSystemOMC = None


def omhome():
    if os.environ.get('OPENMODELICAHOME'):
        return os.environ['OPENMODELICAHOME']
    omc = os.environ.get('OMC') or shutil.which('omc') or '/home/johti17/OpenModelicaWork/om-install/bin/omc'
    return str(Path(omc).resolve().parents[1]) if Path(omc).exists() else None


OMHOME = omhome()
SKIP = None if ModelicaSystemOMC and OMHOME else 'OMPython or omc not available'
WORK = None
MODELS = {}


def setUpModule():
    global WORK
    if not SKIP:
        WORK = tempfile.mkdtemp(prefix='koekmo-fast-')


def tearDownModule():
    if WORK:
        shutil.rmtree(WORK, ignore_errors=True)


WRAPPER = 'MotalaBrowserContinuous'


def model(name):
    """Compile a scenario of tests/fast/Scenarios.mo, or the page's wrapper, once per test run; later calls reuse it."""
    if name not in MODELS:
        work = Path(WORK) / name.replace('.', '_')
        work.mkdir()
        libraries = [str(ROOT / 'modelica/Kommunekonomi.mo'), str(ROOT / 'modelica/Motala.mo')]
        file, full = (ROOT / 'modelica/MotalaBrowser.mo', name) if name == WRAPPER else (Path(__file__).with_name('Scenarios.mo'), f'FastTests.{name}')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            m = ModelicaSystemOMC(work_directory=str(work), omhome=OMHOME)
            m.model(model_name=full, model_file=str(file), libraries=libraries)
        MODELS[name] = m
    return MODELS[name]


def run(name, years=8, start=2025, **parameters):
    """Simulate; returns the year-end rows and every stored point (top-level names and the 65+ chain).

    parameters are set for this run and put back afterwards. Only parameters with a literal default can be set
    (the wrapper's inputs); OMPython refuses the others.
    """
    m = model(name)
    m.setSimulationOptions(startTime=start, stopTime=start + years, stepSize=1/12)
    result = Path(m.getWorkDirectory()) / f'run{years}.mat'
    changed = {}
    try:
        for k, v in parameters.items():
            old = m.getParameters(k)
            changed[k] = old[0] if isinstance(old, list) else old
            m.setParameters(**{k: str(v).lower() if isinstance(v, bool) else str(v)})
        m.simulate(resultfile=str(result))
    finally:
        for k, old in changed.items():
            m.setParameters(**{k: str(old)})
    names = m.getSolutions(resultfile=str(result))
    extra = ('demography.older', 'demography.ageing', 'demography.young', 'services.demand', 'services.network', 'finance.depositRate', 'finance.financial.annual', 'revenues.grantParts', 'operations.oneOffCostRate')
    wanted = [n for n in names if n == 'time' or '.' not in n or n.startswith(extra)]
    series = dict(zip(wanted, m.getSolutions(wanted, resultfile=str(result))))
    rows = {}
    for y in range(start, start + years + 1):
        k = int(np.where(np.isclose(series['time'], y))[0][-1])  # the last point at a year end is after its events
        rows[y] = {n: float(v[k]) for n, v in series.items()}
    return rows, series


@unittest.skipIf(SKIP, SKIP)
class Books(unittest.TestCase):
    def test_balances_hold_in_every_year(self):
        for name in ('Base', 'Shrinking', 'WorkingCapital', 'HigherTax'):
            rows, _ = run(name)
            for y, r in rows.items():
                for k in ('populationBalance', 'cashBalance', 'debtBalance', 'assetBalance', 'equityBalance'):
                    self.assertLess(abs(r[k]), 1e-6, f'{name} {y} {k}')

    def test_base_year_row_is_the_accounts(self):
        r = run('Base', years=1)[0][2025]
        for key, value in (('debt', 1040), ('cash', 81), ('assets', 2997), ('depreciation', 180), ('tax', 2330), ('grants', 987)):
            self.assertAlmostEqual(r[key], value, places=6, msg=key)


@unittest.skipIf(SKIP, SKIP)
class OlderPeople(unittest.TestCase):
    """65+ is an ageing chain of three stocks: 65-79, 80-89 and 90+."""

    def test_the_group_is_the_chain(self):
        _, s = run('Base')
        chain = s['demography.older[1]'] + s['demography.older[2]'] + s['demography.older[3]']
        self.assertLess(float(np.max(np.abs(s['p[5]'] - chain))), 1e-6)
        self.assertLess(float(np.max(np.abs(s['population80Plus'] - s['demography.older[2]'] - s['demography.older[3]']))), 1e-6)

    def test_the_oldest_grow_faster_and_care_follows_them(self):
        rows, _ = run('Base')
        a, b = rows[2025], rows[2033]
        older = b['p[5]']/a['p[5]']
        self.assertGreater(b['population80Plus']/a['population80Plus'], older + 0.1, 'Motala: 80+ grows much faster than 65+')
        self.assertGreater(b['careIndex'], older, 'the care need weights 80+ more')

    def test_more_old_people_means_more_deaths(self):
        # With the chain the 65+ death rate rises as 80+ grows; it was fixed before.
        rows, _ = run('Base')
        rate = lambda y: rows[y]['deaths']/((rows[y - 1]['p[5]'] + rows[y]['p[5]'])/2)
        self.assertGreater(rate(2033), rate(2026))


@unittest.skipIf(SKIP, SKIP)
class AgeProfile(unittest.TestCase):
    """Ageing between the stocks follows the base year's single years of age (Data.ageProfile)."""

    def test_those_who_turn_65_are_the_64_year_olds(self):
        # SCB, Motala 31 December 2025: 533 persons aged 64, 486 aged 63 (Motala.Data.SCB.motala2025.population).
        _, s = run('Base', years=2)
        inside = lambda year: (s['time'] > year) & (s['time'] < year + 1)
        flow = lambda year: float(np.mean((s['demography.ageing[4]'])[inside(year)]))
        self.assertAlmostEqual(flow(2025), 533, delta=533*0.04)
        self.assertAlmostEqual(flow(2026), 486, delta=486*0.04)

    def test_the_death_rate_of_each_older_stock_falls_with_the_national_trend(self):
        _, s = run('Base')
        for j in (1, 2, 3):
            rate = s[f'demography.olderRate[{j}]'] if f'demography.olderRate[{j}]' in s else None
            if rate is not None:
                self.assertLess(rate[-1], rate[0])

    def test_eighty_plus_follows_the_cohorts(self):
        # SCB's projection for Motala gives 4 329 persons 80+ in 2033 (data/planning-inputs.json, olderGroups).
        rows, _ = run('Base')
        self.assertAlmostEqual(rows[2033]['population80Plus'], 4329, delta=4329*0.03)


@unittest.skipIf(SKIP, SKIP)
class CostsAndFinance(unittest.TestCase):
    def test_the_pension_cost_follows_the_payroll(self):
        rows, _ = run('Base')
        share = [rows[y]['pensionExpense']/rows[y]['payroll'] for y in range(2026, 2034)]
        self.assertLess(max(share) - min(share), 1e-6)
        self.assertAlmostEqual(share[0], 190/2288, delta=1e-4)
        given, _ = run('GivenPension')
        self.assertAlmostEqual(given[2033]['pensionExpense'], 190, delta=1e-6)

    def test_roads_stay_when_the_population_falls(self):
        # 5.8 % of "other" follows the road network (Kolada N07024 for Motala 2025), not the population.
        _, s = run('Shrinking')
        population = s['population'][-1]/s['population'][0]
        self.assertLess(population, 0.95)
        self.assertAlmostEqual(float(s['services.network'][-1]), 1, delta=1e-9)
        self.assertAlmostEqual(float(s['services.demand[3]'][-1]), 0.0583 + (1 - 0.0583)*population, delta=1e-4)

    def test_cash_above_the_base_years_earns_interest(self):
        rows, s = run('Base')
        extra = rows[2033]['finance.financial.annual'] - 15  # Motala's financial income 2025: 15 mnkr
        mean_cash = float(np.mean(s['cash'][(s['time'] > 2032) & (s['time'] < 2033)]))
        self.assertGreater(extra, 0)
        self.assertAlmostEqual(extra, float(s['finance.depositRate'][-1])*(mean_cash - 81), delta=0.3)

    def test_the_base_years_rate_is_interest_over_mean_debt(self):
        rows, _ = run('Base', years=1)
        self.assertAlmostEqual(rows[2025]['annualInterestRate'], 21/((940 + 1040)/2), delta=1e-9)

    def test_money_borrowed_ahead_is_kept_until_the_deferred_payment(self):
        rows, _ = run('Prefinanced', years=3)
        self.assertGreater(rows[2026]['prefinancing'], 100)
        self.assertLess(rows[2027]['repayment'], 10, 'not repaid in January and borrowed again')

    def test_fees_follow_part_of_an_inflation_shock(self):
        shock, _ = run('InflationShock', years=2)
        fixed, _ = run('NoFeeIndexation', years=2)
        base, _ = run('Base', years=2)
        self.assertAlmostEqual(fixed[2026]['operatingRevenue'], base[2026]['operatingRevenue'], delta=1e-4)
        # 30 % of 3 points in 2026, and of half as much in 2027 (the shock's persistence), of which half shows in 2027's mean.
        gain = shock[2027]['operatingRevenue']/fixed[2027]['operatingRevenue'] - 1
        self.assertAlmostEqual(gain, 0.3*0.03 + 0.3*0.015/2, delta=0.001)


@unittest.skipIf(SKIP, SKIP)
class Decisions(unittest.TestCase):
    def test_tax_rate_is_not_cancelled_by_equalisation(self):
        base, _ = run('Base', years=1)
        raised, _ = run('TaxOnly', years=1)
        self.assertAlmostEqual(raised[2026]['tax'] - base[2026]['tax'], base[2026]['tax']/21.7, delta=1e-6)
        self.assertAlmostEqual(raised[2026]['grants'], base[2026]['grants'], delta=1e-6)

    def test_more_arrivals_raise_the_population_by_about_as_many(self):
        base, _ = run('Base', years=1)
        more, _ = run('MoreArrivals', years=1)
        self.assertAlmostEqual(more[2026]['population'] - base[2026]['population'], 200, delta=2)


@unittest.skipIf(SKIP, SKIP)
class Liquidity(unittest.TestCase):
    def days(self, r, credit=200):
        payments = r['payroll'] + r['pensionCashPayments'] + r['otherOperatingExpense'] + r['annualInvestment'] + r['interest']
        return 365*(r['cash'] + credit)/payments

    def test_cash_starts_at_the_accounts_and_approaches_the_rule(self):
        rows, _ = run('Base')
        self.assertLess(rows[2026]['debt'] - run('NoReserve')[0][2026]['debt'], 40)
        self.assertLess(abs(self.days(rows[2033]) - 30), 2, 'Motala: 30 days, 200 mnkr credit')

    def test_without_the_approach_the_reserve_holds_from_the_first_year(self):
        rows, _ = run('ReserveAtOnce', years=2)
        self.assertLess(abs(self.days(rows[2026]) - 30), 1)


@unittest.skipIf(SKIP, SKIP)
class PageWrapper(unittest.TestCase):
    """The wrapper the page compiles calibrates the population itself, from the history and projection it is sent."""

    def test_without_inputs_the_population_is_motalas_model(self):
        wrapper, _ = run(WRAPPER)
        base, _ = run('Base')
        for y in wrapper:
            self.assertAlmostEqual(wrapper[y]['population'], base[y]['population'], delta=1e-3, msg=y)
            self.assertAlmostEqual(wrapper[y]['p[5]'], base[y]['p[5]'], delta=1e-3, msg=y)

    def test_a_projection_is_followed_at_every_year_end(self):
        import json
        planning = json.loads((ROOT / 'data/planning-inputs.json').read_text())
        rows = [r for r in planning['rows'] if r.get('cohorts')][:5]
        parameters = {}
        for t, r in enumerate(rows, start=1):
            parameters[f'followProjection[{t}]'] = True
            for j, x in enumerate(r['cohorts'], start=1):
                parameters[f'projectedCohorts[{t},{j}]'] = x
        result, _ = run(WRAPPER, years=5, **parameters)
        for t, r in enumerate(rows, start=1):
            y = 2025 + t
            self.assertAlmostEqual(result[y]['population'], sum(r['cohorts']), delta=0.01, msg=y)
            self.assertAlmostEqual(result[y]['p[5]'], r['cohorts'][4], delta=0.01, msg=y)

    def test_a_changed_history_is_calibrated_again(self):
        base, _ = run(WRAPPER, years=1)
        more_deaths, _ = run(WRAPPER, years=1, historyDeaths=600)
        self.assertGreater(more_deaths[2026]['mortalityRates[5]'], base[2026]['mortalityRates[5]'] + 0.01)
        self.assertNotAlmostEqual(more_deaths[2026]['residualMigration[5]'], base[2026]['residualMigration[5]'], delta=1)



def skr_path(years=8):
    """Motala's SKR path as the page sends it: tax, grants, population, tax before settlement, income equalisation, regulation."""
    import json
    planning = json.loads((ROOT / 'data/planning-inputs.json').read_text())
    path = planning['revenuePath']
    parts = {c['year']: c['tkrByOutputRow'] for c in path['provenance']['recalculation']['components']}
    rows = [[r['tax'], r['grants'], r['population'], parts[r['year']]['12']/1000, parts[r['year']]['14']/1000, r['regulation']]
            for r in path['rows'][:years]]
    growth = [r['taxBaseGrowth']/100 for r in planning['rows'][:years]]
    return rows, growth


def sent(rows, growth, **more):
    parameters = {'sourcedRevenueYears': len(rows), **more}
    for i, row in enumerate(rows, start=1):
        parameters[f'taxBaseGrowthPath[{i}]'] = growth[i - 1]
        for j, x in enumerate(row, start=1):
            parameters[f'sourcedRevenue[{i},{j}]'] = x
    return parameters


@unittest.skipIf(SKIP, SKIP)
class StateFrame(unittest.TestCase):
    """The state's frame: the regulation grant is what is left of it, the same per inhabitant in every municipality."""

    @classmethod
    def setUpClass(cls):
        cls.rows, cls.growth = skr_path()
        cls.last = 0.0389  # the tax base growth the page keeps after SKR's last year
        cls.frame, _ = run(WRAPPER, years=12, regulationDecidedYears=2, **sent(cls.rows, cls.growth),
                           **{f'taxBaseGrowthPath[{i}]': cls.last for i in range(9, 13)})
        cls.skr, _ = run(WRAPPER, years=12, stateFrame=False, **sent(cls.rows, cls.growth))  # as the page sends it: no decided years

    def path(self, result, i, j):
        return result[2026][f'revenuePath[{i},{j}]']

    def test_the_decided_years_are_skrs(self):
        for i in (1, 2):
            for j in range(1, 7):
                self.assertAlmostEqual(self.path(self.frame, i, j), self.rows[i - 1][j - 1], delta=1e-6, msg=(i, j))

    def test_the_regulation_grant_per_inhabitant_follows_the_nations_tax_base(self):
        # The wrapper's national population is flat here, so the tax base per inhabitant grows by the tax base's rate.
        decided = self.rows[1][5]/self.rows[1][2]
        capacity = 1.0
        for i in range(3, 13):
            capacity *= 1 + (self.growth[i - 1] if i <= 8 else self.last)
            per_inhabitant = self.path(self.frame, i, 6)/self.path(self.frame, i, 3)
            self.assertAlmostEqual(per_inhabitant, decided*capacity, delta=1e-9, msg=i)
        # SKR's own post shrinks each year; the frame gives 140 mnkr in 2033 against SKR's 15.
        self.assertAlmostEqual(self.path(self.frame, 8, 6), 139.5, delta=0.5)
        self.assertAlmostEqual(self.path(self.skr, 8, 6), self.rows[7][5], delta=1e-6)

    def test_only_the_regulation_grant_differs_from_skr_within_its_years(self):
        for i in range(1, 9):
            self.assertAlmostEqual(self.path(self.frame, i, 1), self.rows[i - 1][0], delta=1e-6, msg=i)
            self.assertAlmostEqual(self.path(self.frame, i, 2) - self.path(self.frame, i, 6), self.rows[i - 1][1] - self.rows[i - 1][5], delta=1e-6, msg=i)
            for j in range(1, 7):
                self.assertAlmostEqual(self.path(self.skr, i, j), self.rows[i - 1][j - 1], delta=1e-6, msg=(i, j))

    def test_after_skrs_last_year_every_part_keeps_its_last_rate(self):
        last, before = self.rows[7], self.rows[6]
        rates = {1: last[0]/before[0], 3: last[2]/before[2], 4: last[0]/before[0], 5: last[4]/before[4]}
        other = (last[1] - last[5])/(before[1] - before[5])
        for result in (self.frame, self.skr):
            for i in range(9, 13):
                for j, rate in rates.items():
                    self.assertAlmostEqual(self.path(result, i, j), last[j - 1]*rate**(i - 8), delta=1e-6, msg=(i, j))
                self.assertAlmostEqual(self.path(result, i, 2) - self.path(result, i, 6), (last[1] - last[5])*other**(i - 8), delta=1e-6, msg=i)
        # Grants keep growing after 2033: 3 to 4 per cent a year with the frame, not a standstill.
        for i in range(9, 13):
            growth = self.path(self.frame, i, 2)/self.path(self.frame, i - 1, 2) - 1
            self.assertGreater(growth, 0.03, msg=i)
            self.assertLess(growth, 0.04, msg=i)
        # SKR's own post keeps its yearly change in kronor and turns into a fee.
        step = last[5] - before[5]
        self.assertAlmostEqual(self.path(self.skr, 10, 6), last[5] + 2*step, delta=1e-6)
        self.assertLess(self.path(self.skr, 10, 6), 0)

    def test_the_model_uses_the_path_and_reports_it(self):
        for y in range(2026, 2038):
            i = y - 2025
            self.assertAlmostEqual(self.frame[y]['referenceRevenue'], self.path(self.frame, i, 1) + self.path(self.frame, i, 2), delta=1e-6, msg=y)
        self.assertGreater(self.frame[2033]['grants'], self.skr[2033]['grants'] + 100)
        self.assertGreater(self.frame[2037]['grants'], self.frame[2033]['grants']*1.1)

    def test_without_a_sourced_path_the_rows_stand_as_given(self):
        wrapper, _ = run(WRAPPER)
        for i in (1, 5, 8):
            self.assertAlmostEqual(self.path(wrapper, i, 1), 2330, delta=1e-9)
            self.assertAlmostEqual(self.path(wrapper, i, 2), 987, delta=1e-9)

    def test_by_component_the_regulation_grant_follows_the_tax_base_per_inhabitant(self):
        frame, _ = run('GrantParts')
        held, _ = run('GrantPartsHeld')
        # The parts are set at the start of each year, so the row of a year end holds the next year's. Year one is SCB's
        # decided amount in both; after that the held grant only follows the population.
        self.assertAlmostEqual(frame[2025]['revenues.grantParts[3]'], held[2025]['revenues.grantParts[3]'], delta=1e-6)
        for y in range(2026, 2033):
            ratio = frame[y]['revenues.grantParts[3]']/held[y]['revenues.grantParts[3]']
            before = frame[y - 1]['revenues.grantParts[3]']/held[y - 1]['revenues.grantParts[3]']
            self.assertGreater(ratio/before, 1.02, msg=y)   # the tax base per inhabitant grows about 3 per cent a year
            self.assertLess(ratio/before, 1.05, msg=y)
        self.assertGreater(frame[2033]['result'], held[2033]['result'])



@unittest.skipIf(SKIP, SKIP)
class OneOffCost(unittest.TestCase):
    """A one-off operating cost, for example repairs after a cloudburst: a flow for a limited time."""

    @classmethod
    def setUpClass(cls):
        cls.base, _ = run('Base')
        cls.event, cls.points = run('Cloudburst')

    def test_the_cost_is_booked_in_the_year_of_the_event_in_that_years_prices(self):
        extra = {y: self.event[y]['cost'] - self.base[y]['cost'] for y in self.base}
        # 56 mnkr in the base year's prices, paid July to December 2027 at the price level then (2 % a year).
        self.assertGreater(extra[2027], 56*1.02)
        self.assertLess(extra[2027], 56*1.02**2.5)
        for y in (2026, 2028, 2030, 2033):
            self.assertAlmostEqual(extra[y], 0, delta=0.05, msg=y)
        self.assertAlmostEqual(self.event[2027]['otherOperatingExpense'] - self.base[2027]['otherOperatingExpense'], extra[2027], delta=1e-3)

    def test_the_result_falls_that_year_and_the_debt_stays_higher(self):
        cost = self.event[2027]['cost'] - self.base[2027]['cost']
        self.assertAlmostEqual(self.base[2027]['result'] - self.event[2027]['result'], cost, delta=1.5)  # and half a year's interest
        for y in range(2028, 2034):
            self.assertGreater(self.event[y]['debt'], self.base[y]['debt'] + 0.9*cost, msg=y)
            self.assertLess(self.base[y]['result'] - self.event[y]['result'], 4, msg=y)   # only the interest on the loan
            self.assertGreater(self.base[y]['result'] - self.event[y]['result'], 0, msg=y)

    def test_the_flow_runs_for_half_a_year_and_the_books_balance(self):
        t, rate = self.points['time'], self.points['operations.oneOffCostRate']
        active = [float(x) for x, r in zip(t, rate) if r > 0]
        self.assertAlmostEqual(min(active), 2026.5, delta=0.09)   # time 2026.5 is 1 July 2027
        self.assertAlmostEqual(max(active), 2027.0, delta=0.09)
        for y in self.event:
            for balance in ('assetBalance', 'cashBalance', 'debtBalance'):
                self.assertAlmostEqual(self.event[y][balance], 0, delta=1e-6, msg=(y, balance))


if __name__ == '__main__':
    unittest.main()
