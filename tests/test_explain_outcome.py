"""The explanation runs (scripts/explain_outcome.py) and SKR's old forecasts (scripts/read_skr_vintages.py).

The data files are checked against each other and against earlier, independent runs. The scripts' own steps are
checked on small made-up inputs; no test here needs OpenModelica or LibreOffice.
"""
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import explain_outcome as eo  # noqa: E402
import read_skr_vintages as skr  # noqa: E402

load = lambda path: json.loads((ROOT / path).read_text())
CODES = sorted(p.parent.name for p in (ROOT / 'data/municipalities').glob('[0-9]*/base-years.json'))
explanation = lambda code: load('data/outcome-explanation.json' if code == '0583' else f'data/municipalities/{code}/outcome-explanation.json')


class Steps(unittest.TestCase):
    def test_years_beyond_the_circular_keep_its_last_rate(self):
        v = {'taxBase': {2022: .035, 2023: .037, 2024: .034}, 'labour': {2022: .016, 2023: .034, 2024: .021},
             'other': {2022: .022, 2023: .02, 2024: .022}, 'nationalNovember': {2021: 100.0, 2022: 101.0, 2023: 102.01, 2024: 103.0301}}
        e = eo.extended(v, [2022, 2023, 2024, 2025, 2026])
        self.assertEqual(e['taxBase'][2025], .034)
        self.assertEqual(e['labour'][2026], .021)
        self.assertAlmostEqual(e['nationalNovember'][2025], 104.060401)  # the last growth, 1 %, kept
        self.assertEqual(v['nationalNovember'].get(2025), None)  # the circular's own table is not changed

    def test_the_paid_rate_is_interest_over_the_mean_debt(self):
        ledgers = {2021: {'debt': 600}, 2022: {'debt': 1000, 'interest': 24}, 2023: {'debt': 0, 'interest': 5}, 2024: {'debt': 0, 'interest': 1}}
        self.assertAlmostEqual(eo.interest_rate(ledgers, 2022), 0.03)
        self.assertAlmostEqual(eo.interest_rate(ledgers, 2023), 0.01)
        self.assertEqual(eo.interest_rate(ledgers, 2024), 0)  # no debt, no rate

    def test_each_step_changes_only_its_own_input(self):
        ledgers, _, _, _ = eo.hv.outcomes()
        years = [2022, 2023, 2024, 2025]
        v = eo.extended(eo.hv.vintage(2021), years)
        source = lambda k: {line.rstrip(',;)') for line in eo.model_source(2021, 4, v, eo.STEPS[:k + 1], ledgers).splitlines()}
        names = lambda lines: sorted(line.split('=')[0].strip() for line in lines if '=' in line)
        expected = {'wages': ['wageGrowthPath'], 'prices': ['priceGrowthPath'], 'pensions': ['pensionExpensePath'],
                    'taxBase': ['referenceTax'], 'interest': ['interestRatePath'], 'investment': ['investmentPath']}
        for k in range(1, len(eo.STEPS)):
            added = names(source(k) - source(k - 1))
            if eo.STEPS[k] == 'grants':
                self.assertIn('grantsByComponent', added)
                self.assertFalse({'wageGrowthPath', 'priceGrowthPath', 'referenceTax', 'pensionExpensePath'} & set(added))
            else:
                self.assertEqual(added, expected[eo.STEPS[k]], eo.STEPS[k])
        believed = eo.model_source(2021, 4, v, eo.STEPS[:1], ledgers)
        self.assertIn('wageGrowthPath = {0.016, 0.034, 0.021, 0.021}', believed)  # circular 21:49, last rate kept for 2025
        self.assertNotIn('investmentPath', believed)


class Explanations(unittest.TestCase):
    def test_every_municipality_has_all_steps_and_years(self):
        for code in CODES:
            d = explanation(code)
            self.assertEqual((d['origin'], d['years']), (2021, [2022, 2023, 2024, 2025]), code)
            self.assertEqual([s['step'] for s in d['steps']], list(eo.STEPS))
            self.assertEqual(len(d['ladder']), len(eo.STEPS) * 4)
            self.assertTrue(d['model'].endswith('.Continuous'))

    def test_the_first_step_is_the_hindcasts_forecast(self):
        # Same assumptions as the skr set of scripts/hindcast_vintages.py, which runs three years instead of four.
        hindcast = {r['year']: r['model'] for r in load('data/vintage-hindcast-continuous.json')['runs']
                    if r['origin'] == 2021 and r['assumptions'] == 'skr'}
        believed = explanation('0583')['runs']['believed']
        self.assertEqual(sorted(hindcast), [2022, 2023, 2024])
        for year, model in hindcast.items():
            for line in ('tax', 'grants', 'payroll', 'result'):
                self.assertAlmostEqual(believed[str(year)][line], model[line], delta=0.01, msg=f'{year} {line}')

    def test_a_step_moves_only_what_its_input_drives(self):
        for code in CODES:
            runs = explanation(code)['runs']
            for year in ('2022', '2025'):
                same = lambda a, b, line: self.assertAlmostEqual(runs[a][year][line], runs[b][year][line], delta=0.02, msg=f'{code} {a}->{b} {line}')
                same('believed', 'wages', 'otherCosts')
                same('believed', 'wages', 'tax')
                same('wages', 'prices', 'payroll')
                same('prices', 'pensions', 'payroll')
                same('pensions', 'taxBase', 'payroll')
                same('taxBase', 'grants', 'tax')
                same('grants', 'interest', 'otherCosts')
                same('interest', 'investment', 'payroll')
                self.assertAlmostEqual(runs['investment'][year]['pension'], explanation(code)['outcome'][year]['pension'], delta=0.01)

    def test_the_remaining_lines_add_up_to_the_remaining_result(self):
        for code in CODES:
            d = explanation(code)
            for r in d['remainingByLine']:
                lines = (r['tax'] + r['grants'] - r['payroll'] - r['pension'] - r['otherCosts'] + r['operatingRevenue']
                         - r['depreciation'] - r['interest'] + r['otherFinancialNet'])
                self.assertAlmostEqual(lines, r['result'], delta=2.5, msg=f'{code} {r["year"]}')  # Motala's reports round to 1 mnkr
                last = d['runs']['investment'][str(r['year'])]['result']
                self.assertAlmostEqual(r['result'], last - d['outcome'][str(r['year'])]['result'])

    def test_the_summary_is_the_files(self):
        summary = load('data/outcome-explanation-summary.json')
        self.assertEqual(sorted(m['municipality'] for m in summary['municipalities']), CODES)
        for m in summary['municipalities']:
            d = explanation(m['municipality'])
            self.assertEqual(m['outcome'], [d['outcome'][str(y)]['result'] for y in d['years']])
            self.assertEqual(m['explained'], [d['runs']['investment'][str(y)]['result'] for y in d['years']])
        self.assertEqual([len(f['rows']) for f in summary['taxAndGrantsForecasts']], [5, 4, 3, 2, 4])
        self.assertTrue(all(r['municipalities'] == 13 for f in summary['taxAndGrantsForecasts'] for r in f['rows']))


class SkrVintages(unittest.TestCase):
    def test_four_workbooks_thirteen_municipalities_eight_years(self):
        d = load('data/skr-historical/forecasts.json')
        manifest = {f['circular']: f for f in load('data/skr-historical/manifest.json')['files']}
        self.assertEqual([v['circular'] for v in d['vintages']], ['21:35', '22:28', '23:56', '24:56'])
        for v in d['vintages']:
            self.assertEqual(v['sha256'], manifest[v['circular']]['sha256'])
            self.assertEqual(sorted(v['municipalities']), CODES)
            for code, m in v['municipalities'].items():
                first = manifest[v['circular']]['firstYear']
                self.assertEqual([r['year'] for r in m['rows']], list(range(first, first + 8)))
                self.assertTrue(all(r['tax'] > 0 and r['grants'] != 0 and r['novemberPopulation'] > 1000 for r in m['rows']), code)

    def test_motala_2021_is_the_earlier_recalculation(self):
        # data/replay-2022.json was read from a copy recalculated by hand on 2026-11-18.
        earlier = {r['year']: r for r in load('data/replay-2022.json')['planning']['revenuePath']['rows']}
        rows = {r['year']: r for r in load('data/skr-historical/forecasts.json')['vintages'][0]['municipalities']['0583']['rows']}
        for year, r in earlier.items():
            self.assertAlmostEqual(rows[year]['tax'], r['tax'], delta=0.001)
            self.assertAlmostEqual(rows[year]['grants'], r['grants'], delta=0.001)
            self.assertEqual(rows[year]['novemberPopulation'], round(r['population']))

    def test_the_forecast_for_the_year_under_way_is_near_the_outcome(self):
        # A wrong municipality or a workbook that was not recalculated would miss by far more than 3 %.
        for v in load('data/skr-historical/forecasts.json')['vintages']:
            for code, m in v['municipalities'].items():
                r = m['rows'][0]
                o = load(f'data/municipalities/{code}/base-years.json')['years'][str(r['year'])]
                self.assertAlmostEqual((r['tax'] + r['grants']) / (o['tax'] + o['grants']), 1, delta=0.03, msg=f'{v["circular"]} {code}')

    def test_selection_sets_the_code_and_empties_the_cached_values(self):
        sheet = ('<worksheet><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" s="280"/>'
                 '<c r="C1" t="str"><f>\'Blad 2 Indata\'!A2</f><v>Ale</v></c></row>'
                 '<row r="2"><c r="A2"><f t="shared" si="1"/><v>7</v></c><c r="B2"><v>5</v></c></row></sheetData></worksheet>')
        parts = {
            '[Content_Types].xml': '<Types><Override PartName="/xl/workbook.xml" ContentType="application/vnd.ms-excel.sheet.macroEnabled.main+xml"/>'
                                   '<Override PartName="/xl/vbaProject.bin" ContentType="application/vnd.ms-office.vbaProject"/></Types>',
            'xl/workbook.xml': '<workbook xmlns:r="r"><sheets><sheet name="Data" sheetId="1" r:id="rId1"/>'
                               '<sheet name="Prognosunderlag" sheetId="2" r:id="rId2"/></sheets><calcPr calcId="191029"/></workbook>',
            'xl/_rels/workbook.xml.rels': '<Relationships><Relationship Id="rId1" Type="t/worksheet" Target="worksheets/sheet1.xml"/>'
                                          '<Relationship Id="rId2" Type="t/worksheet" Target="worksheets/sheet7.xml"/>'
                                          '<Relationship Id="rId3" Type="t/vbaProject" Target="vbaProject.bin"/></Relationships>',
            'xl/worksheets/sheet1.xml': '<worksheet><sheetData><row r="1"><c r="B1"><f>SUM(A1:A2)</f><v>3</v></c></row></sheetData></worksheet>',
            'xl/worksheets/sheet7.xml': sheet, 'xl/vbaProject.bin': 'macro'}
        source, target = io.BytesIO(), io.BytesIO()
        with zipfile.ZipFile(source, 'w') as z:
            for name, text in parts.items():
                z.writestr(name, text)
        skr.select(source, target, '0583')
        with zipfile.ZipFile(target) as z:
            self.assertNotIn('xl/vbaProject.bin', z.namelist())
            front, data = z.read('xl/worksheets/sheet7.xml').decode(), z.read('xl/worksheets/sheet1.xml').decode()
            self.assertIn('<c r="B1" s="280"><v>583</v></c>', front)  # the selection, in the sheet named Prognosunderlag
            self.assertIn("<f>'Blad 2 Indata'!A2</f></c>", front)  # the cached name of another municipality is gone
            self.assertIn('<f t="shared" si="1"/></c>', front)
            self.assertIn('<c r="B2"><v>5</v></c>', front)  # a typed value stays
            self.assertEqual(data.count('<v>'), 0)
            self.assertNotIn('<c r="B1"><v>583', data)  # B1 of another sheet is not the selection
            self.assertIn('fullCalcOnLoad="1"', z.read('xl/workbook.xml').decode())
            self.assertNotIn('vbaProject', z.read('xl/_rels/workbook.xml.rels').decode() + z.read('[Content_Types].xml').decode())
            self.assertNotIn('macroEnabled', z.read('[Content_Types].xml').decode())


if __name__ == '__main__':
    unittest.main()
