"""Synthetic stress cases test methods; actual observations test integration."""
import copy
import json
import math
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from motala_lab import data,demography,fiscal,model,evaluate,modelica


def synthetic_panel():
    rows=[]
    for i in range(6):
        for year in range(2000,2016):
            t=year-2000
            population=20000+1000*i+30*t
            revenue=1200+60*i+25*t
            cost=1100+50*i+22*t
            finance=-3-.2*t
            rows.append({'municipality':f'{i+1:04d}','year':year,'population':population,
                         'taxAndGrants':revenue,'netCost':cost,'financeNet':finance,
                         'result':revenue-cost+finance,'source':'synthetic fixture',
                         'vintage':'synthetic-v1','retrievedAt':'2026-10-13','sourceRelease':f'{year+1}-03-01'})
    return {'schemaVersion':1,'scope':'kommunen','moneyUnit':'mnkr',
            'definitions':data.DEFINITIONS,'evidenceClass':'retrospective','rows':rows}


class ResearchTests(unittest.TestCase):
    def test_frozen_reference_and_accounting_definitions(self):
        data.verify_reference()
        observations=data.load()
        for r in observations['rows']:
            self.assertAlmostEqual(r['taxAndGrants']-r['netCost']+r['financeNet'],r['result'])
            if 'cohorts' in r:
                self.assertAlmostEqual(sum(r['cohorts']),r['population'])
            self.assertIsNone(r['sourceRelease'])
        self.assertIn('reconstructed',observations['definitions']['taxAndGrants'])

    def test_rejects_unreconciled_ledger_and_mislabelled_real_time(self):
        for mutate in (lambda d:d['rows'][0].update(result=1e9),
                       lambda d:d.update(evidenceClass='archived_as_of'),
                       lambda d:d['rows'][0].update(population=float('nan')),
                       lambda d:d.update(moneyUnit='SEK')):
            d=data.load();mutate(d)
            with self.assertRaises(ValueError):data.validate(d)

    def test_candidate_never_sees_future_rows(self):
        d=data.load();train=data.available(d,2022)
        first=model.forecast(train,horizon=3)
        changed=copy.deepcopy(d)
        for r in changed['rows']:
            if r['year']>2022:
                r['netCost']*=100;r['taxAndGrants']*=100
        self.assertEqual(first,model.forecast(data.available(changed,2022),horizon=3))
        # A later-year peer observation must be rejected even if it isn't Motala.
        bad=train+[dict(d['rows'][-1],municipality='9999')]
        with self.assertRaises(ValueError):model.forecast(bad)

    def test_outer_predictions_are_invariant_to_later_outcomes(self):
        d=data.load();before=evaluate.evaluate(d,1)
        changed=copy.deepcopy(d)
        for r in changed['rows']:
            if r['year']>=2024:
                r['netCost']+=500;r['result']-=500
        after=evaluate.evaluate(changed,1)
        key=lambda r:(r['municipality'],r['originYear'],r['targetYear'],r['metric'])
        b={key(r):r['predictions'] for r in before['cases'] if r['originYear']<=2023}
        a={key(r):r['predictions'] for r in after['cases'] if r['originYear']<=2023}
        self.assertEqual(b,a)

    def test_nested_damping_never_uses_next_target(self):
        history=data.load()['rows'][:3]
        self.assertIn(demography.select_damping(history),demography.DAMPING)
        self.assertEqual(demography.select_damping(history[:2]),1.)
        c=demography.project(history,8,.5)
        for r in c:self.assertLess(abs(r['populationBalance']),1e-7)

    def test_demography_matches_frozen_javascript_at_current_origin(self):
        baseline=json.loads(subprocess.check_output(['node',str(data.ROOT/'motala_lab/run_reference.mjs')],text=True))
        p=demography.project(data.load()['rows'],8,1.)
        for actual,expected in zip(p,baseline['rows'][1:]):
            self.assertAlmostEqual(actual['population'],expected['population'],places=7)
            for a,b in zip(actual['cohorts'],expected['cohorts']):self.assertAlmostEqual(a,b,places=7)

    def test_panel_activates_with_real_sample_thresholds(self):
        d=data.validate(synthetic_panel())
        fit=fiscal.fit_panel(d['rows'],'netCost')
        self.assertIsNotNone(fit)
        self.assertIn(fit['penalty'],fiscal.PENALTIES)
        candidate=model.forecast(d['rows'],'0001',3)
        self.assertEqual(candidate['methods']['netCost'],'ridge')
        self.assertTrue(all(math.isfinite(r['result']) for r in candidate['rows']))
        # Existing short local data must not masquerade as a trained panel model.
        small=model.forecast(data.load()['rows'])
        self.assertTrue(all(f is None for f in small['fits'].values()))

    def test_standardization_uses_training_only_and_regularizes_effects(self):
        ss=fiscal.samples(synthetic_panel()['rows'],'netCost')
        train=[r for r in ss if r[3]<2010]
        fit=fiscal.fit_ridge(train,10.)
        self.assertEqual(fit['featureIndices'],[0,1,2])
        np.testing.assert_allclose(fit['center'],np.mean([s[0][:3] for s in train],axis=0))
        self.assertEqual(fit['trainingSamples'],len(train))

    def test_archived_evaluation_requires_origins_and_filters_releases(self):
        d=synthetic_panel();d['evidenceClass']='archived_as_of'
        with self.assertRaises(ValueError):evaluate.evaluate(d)
        d['evaluationOrigins']=[{'municipality':'0001','forecastDate':'2013-04-01','informationCutoff':'2013-03-31'}]
        result=evaluate.evaluate(d,1)
        self.assertTrue(result['cases'])
        self.assertTrue(all(r['baseYear']==2012 and r['targetYear']==2014 and r['horizonYears']==1 for r in result['cases']))
        delayed=copy.deepcopy(d)
        for r in delayed['rows']:
            if r['year']==2012:r['sourceRelease']='2014-01-01'
        self.assertTrue(all(r['year']<2012 for r in data.available(delayed,2013,'2013-03-31')))

    def test_missing_cohorts_use_explicit_fallback(self):
        d=synthetic_panel()
        result=model.forecast(d['rows'],'0001',2)
        self.assertIn('Cohort data unavailable',result['warnings'][0])
        self.assertIsNone(result['demographicCalibration'])

    def test_old_age_data_gaps_preserve_recent_cohort_forecast(self):
        rows=data.load()['rows']
        expected=demography.project(rows[-3:],3,.5)
        self.assertIsNotNone(expected)
        incomplete=copy.deepcopy(rows)
        for row in incomplete[:-3]:row.pop('cohorts',None)
        self.assertEqual(expected,demography.project(incomplete,3,.5))
        incomplete[-2].pop('cohorts')
        self.assertIsNone(demography.project(incomplete,3,.5))
        # The first economic origin has two years but only one age observation.
        first=model.forecast(rows[:2],horizon=1)
        self.assertIsNone(first['demographicCalibration'])
        self.assertEqual(first['rows'][0]['population'],rows[1]['population'])

    def test_local_selection_uses_same_population_fallback_as_forecast(self):
        rows=[]
        for year in range(2010,2016):
            rows.append({'year':year,'municipality':'0583','population':1000,
                         'netCost':100+10*(year-2010),'taxAndGrants':110+10*(year-2010),
                         'financeNet':0,'result':10})
        candidate=model.forecast(rows,use_panel=False)
        self.assertEqual(candidate['methods']['netCost'],'trend')
        self.assertIsNone(candidate['demographicCalibration'])

    def test_repeatability_and_benchmark_independence(self):
        rows=data.load()['rows'];first=model.forecast(rows)
        with patch('pathlib.Path.read_text',side_effect=AssertionError('Candidate must not open benchmark data')):
            second=model.forecast(rows)
        self.assertEqual(first,second)
        for row in first['rows']:self.assertAlmostEqual(row['ledgerResidual'],0)

    def test_native_modelica_with_pension_bridge_and_varying_investment(self):
        d=data.load();initial=d['rows'][-1];candidate=model.forecast(d['rows'],horizon=3)
        financing={'assets0':1000,'depreciation0':100,'debt0':1,'cash0':80,
                   'investmentPath':[0,700,0],'pensionAccrualMinusCashPath':[0,30,-20]}
        with tempfile.TemporaryDirectory(prefix='motala-test-native-') as directory:
            result=modelica.validate_native(candidate,initial,financing,directory)
            self.assertEqual(result['status'],'passed')
            import csv
            with open(Path(directory)/'Scenario_res.csv') as f:rs=list(csv.DictReader(f))
            r=[r for r in rs if abs(float(r['time'])-1)<1e-8][-1]
            self.assertEqual(float(r['debt']),0)
            self.assertGreater(float(r['cash']),80)


if __name__=='__main__':unittest.main()
