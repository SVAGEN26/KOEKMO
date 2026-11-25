"""The response test's own arithmetic, and its copy of the model's capacity rule against the Modelica model.

scripts/response_test.py computes the model's service volume in Python from the observed population. That copy
must be the model's rule, or the test says nothing about the model. The model tests run
Finspang.Continuous in OpenModelica and compare; they are skipped without OMC or omc on PATH.
"""
import csv
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import response_test as rt  # noqa: E402

OMC = os.environ.get('OMC') or shutil.which('omc')


class Arithmetic(unittest.TestCase):
    def cases(self, slope, noise, seed=1):
        rng, out = random.Random(seed), []
        for m in range(13):
            trend = rng.gauss(0, 0.01)
            for year in range(2012, 2026):
                x = trend + rng.gauss(0, 0.005)
                out.append({'municipality': m, 'year': year, 'x': x, 'y': 0.03 * (year % 3) + slope * x + rng.gauss(0, noise)})
        return out

    def test_slope_is_recovered_under_year_effects(self):
        b, r2 = rt.slope(self.cases(0.6, 0.0))
        self.assertAlmostEqual(b, 0.6, places=10)
        self.assertAlmostEqual(r2, 1.0, places=10)

    def test_interval_surrounds_the_estimate_and_widens_with_noise(self):
        tight, wide = self.cases(1.0, 0.002), self.cases(1.0, 0.02)
        low, high = rt.interval(tight, reps=400)
        self.assertTrue(low < rt.slope(tight)[0] < high)
        self.assertTrue(0.8 < low and high < 1.2)
        low2, high2 = rt.interval(wide, reps=400)
        self.assertTrue(low2 < rt.slope(wide)[0] < high2)
        self.assertGreater(high2 - low2, 3 * (high - low))

    def test_municipality_effects_remove_a_municipality_trend(self):
        cases = self.cases(1.0, 0.0)
        for c in cases:
            c['y'] += 0.02 * c['municipality']  # unrelated to x within a municipality
        self.assertAlmostEqual(rt.slope(cases, ('year', 'municipality'))[0], 1.0, places=6)

    def test_windows_are_log_changes_and_skip_excluded_years(self):
        x = {y: 1.01 ** (y - 2010) for y in range(2010, 2016)}
        y = {y: 1.02 ** (y - 2010) for y in range(2010, 2016)}
        w = rt.windows(x, y, 'a', 2, 2011)
        self.assertEqual([c['year'] for c in w], [2013, 2014, 2015])
        self.assertAlmostEqual(w[0]['x'], 2 * math.log(1.01))
        self.assertAlmostEqual(w[0]['y'], 2 * math.log(1.02))
        self.assertEqual([c['year'] for c in rt.windows(x, y, 'a', 2, 2011, excluded={2013})], [2015])

    def test_annual_capacity_closes_the_stated_share_of_the_gap(self):
        needs = [[1, 1, 1]] + [[1.2, 0.9, 1.0]] * 3
        volume = rt.annual_volume(needs, [0.5, 0.3, 0.2], adjustment=0.5, fixed_share=0.25)
        target = 0.5 * (0.25 + 0.75 * 1.2) + 0.3 * (0.25 + 0.75 * 0.9) + 0.2
        for k, v in enumerate(volume):
            self.assertAlmostEqual(v, target + (1 - target) * 0.5 ** k)

    def test_continuous_capacity_is_the_integral_of_its_equation(self):
        needs = [[1, 1, 1], [1.05, 0.97, 1.01], [1.12, 0.95, 1.02], [1.10, 0.90, 1.04]]
        ends, means = rt.continuous_capacity(needs, adjustment=0.5, fixed_share=0.25)
        rate, steps, c = -math.log(0.5), 20000, [1.0] * 3
        for k in range(1, len(needs)):
            total = [0.0] * 3
            for s in range(steps):
                u = (s + 0.5) / steps
                for i in range(3):
                    target = 0.25 + 0.75 * (needs[k - 1][i] + (needs[k][i] - needs[k - 1][i]) * u)
                    total[i] += c[i] + 0.5 * rate * (target - c[i]) / steps
                    c[i] += rate * (target - c[i]) / steps
            for i in range(3):
                self.assertAlmostEqual(ends[k][i], c[i], places=6)
                self.assertAlmostEqual(means[k][i], total[i] / steps, places=6)
        # A constant gap closes by the same share in a year as in the annual rule.
        ends, _ = rt.continuous_capacity([[1, 1, 1], [2, 2, 2], [2, 2, 2]], adjustment=0.5, fixed_share=0.0)
        self.assertAlmostEqual((2 - ends[2][0]) / (2 - ends[1][0]), 0.5)

    def test_financing_sources_and_remainder_sum_to_the_need(self):
        record = lambda **k: {'tax': 80, 'grants': 20, 'payroll': 60, 'pension': 5, 'otherOperatingExpense': 30, 'operatingRevenue': 10,
                              'netCostRoundingAdjustment': 0, 'depreciation': 6, 'financialIncome': 1, 'interestExpense': 2,
                              'otherFinancialExpense': 0, 'investment': 20, **k}
        balance = {'081': {2020: 100, 2021: 108}, '033': {2020: 30, 2021: 33}, '065': {2020: 10, 2021: 9}, '089': {2020: 120, 2021: 130},
                   '098': {2020: 40, 2021: 41}, '069': {2020: 25, 2021: 26}, '079': {2020: 15, 2021: 16}}
        data = {'x': {'records': {2020: record(), 2021: record()}, 'balance': balance, 'excluded': set()}}
        (case,) = rt.debt_cases(data)
        self.assertAlmostEqual(case['need'], (20 - 8 - 6) / 100)  # result 8: 100 - 85 - 6 + 1 - 2
        self.assertAlmostEqual(case['bankDebt'], 0.08)
        self.assertAlmostEqual(case['lending'], -0.03)
        self.assertAlmostEqual(case['netBankDebt'], 0.08 - 0.03 + 0.01)
        self.assertAlmostEqual(sum(case[name] for name in rt.SOURCES) + case['remainder'], case['need'])


def simulate(model, intervals):
    with tempfile.TemporaryDirectory(prefix='response-') as tmp:
        tmp = Path(tmp)
        names = 'p\\\\[.\\\\]|demography.cohorts.older\\\\[.\\\\]|population80Plus|population|serviceVolume|capacity\\\\[.\\\\]|educationIndex|careIndex'
        (tmp / 'run.mos').write_text(
            f'loadFile({json.dumps(str(ROOT / "modelica/Kommunekonomi.mo"))}); getErrorString();\n'
            f'loadFile({json.dumps(str(ROOT / "modelica/municipalities/Finspang.mo"))}); getErrorString();\n'
            f'simulate({model}, startTime=2025, stopTime=2033, numberOfIntervals={intervals}, tolerance=1e-9, outputFormat="csv", '
            f'variableFilter="{names}"); getErrorString();\n')
        out = subprocess.run([OMC, 'run.mos'], cwd=tmp, capture_output=True, text=True, timeout=600).stdout
        result = tmp / f'{model}_res.csv'
        if not result.exists():
            raise AssertionError(out[-2000:])
        rows = {}
        with result.open() as handle:
            for row in csv.DictReader(handle):
                t = float(row['time'])
                if abs(t - round(t)) < 1e-9:
                    rows[round(t)] = {k: float(v) for k, v in row.items()}
        return rows


@unittest.skipUnless(OMC, 'OpenModelica (OMC or omc on PATH) is needed')
class AgainstTheModel(unittest.TestCase):
    """The Python rule gives the model's capacity and volume when it is fed the model's own population."""

    @classmethod
    def setUpClass(cls):
        record = json.loads((ROOT / 'data/municipalities/0562/base-years.json').read_text())['years']['2025']
        cls.shares = record['sectorShares']
        cls.education = [w / sum(record['educationShares']) for w in record['educationShares']]
        c65, c80 = record['careCostPerInhabitant']
        cls.care = [c65, c80, c80]
        cls.continuous = simulate('Finspang.Continuous', 96)

    def needs(self, rows):
        # Five age groups: 65+ is split by the model's ageing chain (Continuous.Demography, olderChain).
        group = lambda r: {'education': [r['p[1]'], r['p[2]'], r['p[3]']], 'older': [r[f'demography.cohorts.older[{i}]'] for i in (1, 2, 3)],
                           'total': r['population']}
        base = group(rows[2025])
        return [rt.need(group(rows[y]), base, self.education, self.care) for y in range(2025, 2034)]

    def test_need_is_the_models(self):
        for k, n in enumerate(self.needs(self.continuous)):
            row = self.continuous[2025 + k]
            self.assertAlmostEqual(n[0], row['educationIndex'], places=9)
            self.assertAlmostEqual(n[1], row['careIndex'], places=9)

    def test_continuous_capacity_is_the_models(self):
        # The model's need follows its population through the year; the Python rule joins the year ends with straight
        # lines. The capacity at each year end agrees to 3e-4 (the care need bends within the year as the ageing chain
        # in 65+ moves people into 80+ and they die at higher rates; 2027 elder care: 1.3e-4).
        ends, means = rt.continuous_capacity(self.needs(self.continuous))
        for k in range(1, 9):
            row = self.continuous[2025 + k]
            for i in range(3):
                self.assertAlmostEqual(ends[k][i], row[f'capacity[{i + 1}]'], delta=3e-4, msg=f'{2025 + k} sector {i + 1}')
            self.assertAlmostEqual(sum(s * e for s, e in zip(self.shares, ends[k])), row['serviceVolume'], delta=3e-4)
            # The year's mean lies between the capacities at its ends.
            for i in range(3):
                low, high = sorted((ends[k - 1][i], ends[k][i]))
                self.assertTrue(low - 1e-9 <= means[k][i] <= high + 1e-9)


if __name__ == '__main__':
    unittest.main()
