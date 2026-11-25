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
    wanted = [n for n in names if n == 'time' or '.' not in n or n.startswith('demography.older')]
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


if __name__ == '__main__':
    unittest.main()
