"""Small-data baselines and pooled ridge regressions, fitted only on training rows."""
from collections import Counter
import numpy as np
from .data import by_municipality

COMPONENTS = ('taxAndGrants', 'netCost', 'financeNet')
PENALTIES = (0.1, 1., 10., 100.)
MIN_PANEL_MUNICIPALITIES = 5
MIN_PANEL_TRANSITIONS = 40


def trailing_slope(history, metric, per_capita=False):
    recent = history[-5:]
    changes = []
    for a,b in zip(recent, recent[1:]):
        if b['year'] == a['year']+1:
            av = a[metric]/a['population'] if per_capita else a[metric]
            bv = b[metric]/b['population'] if per_capita else b[metric]
            changes.append(bv-av)
    return float(np.mean(changes)) if changes else 0.


def baseline(history, metric, horizon, kind='persistence'):
    # Fixed damping avoids choosing a favourable trend after seeing outcomes.
    slope = trailing_slope(history, metric) if kind == 'trend' else 0.
    return [history[-1][metric]+slope*sum(.5**j for j in range(1,h+1)) for h in range(1,horizon+1)]


def features(previous, last, metric):
    y = last[metric]/last['population']
    delta = y-previous[metric]/previous['population']
    growth = last['population']/previous['population']-1
    cohorts = last.get('cohorts')
    return [y, delta, growth,
            sum(cohorts[:3])/last['population'] if cohorts else float('nan'),
            cohorts[4]/last['population'] if cohorts else float('nan')]


def samples(rows, metric):
    result = []
    for municipality, rs in by_municipality(rows).items():
        for a,b,c in zip(rs, rs[1:], rs[2:]):
            if b['year']==a['year']+1 and c['year']==b['year']+1:
                result.append((features(a,b,metric), c[metric]/c['population']-b[metric]/b['population'],
                               municipality, c['year']))
    return result


def fit_ridge(samples_, penalty):
    x = np.asarray([s[0] for s in samples_], dtype=float)
    feature_indices=np.flatnonzero(np.all(np.isfinite(x),axis=0))
    x=x[:,feature_indices]
    y = np.asarray([s[1] for s in samples_], dtype=float)
    municipalities = sorted({s[2] for s in samples_})
    center=x.mean(axis=0); scale=x.std(axis=0); scale[scale<1e-12]=1.
    effects=np.array([[float(s[2]==m) for m in municipalities] for s in samples_])
    design=np.column_stack([np.ones(len(x)), (x-center)/scale, effects])
    counts=Counter(s[2] for s in samples_)
    weights=np.array([1/counts[s[2]] for s in samples_]); weights*=len(weights)/weights.sum()
    regularizer=np.eye(design.shape[1])*penalty; regularizer[0,0]=0
    coefficient=np.linalg.solve(design.T@(design*weights[:,None])+regularizer, design.T@(y*weights))
    return {'featureIndices':feature_indices.tolist(),'center':center.tolist(),'scale':scale.tolist(),'coefficient':coefficient.tolist(),
            'municipalities':municipalities,'penalty':penalty,'trainingSamples':len(samples_)}


def ridge_delta(fit, x, municipality):
    design=np.r_[1.,(np.array(x)[fit['featureIndices']]-fit['center'])/fit['scale'],
                 [float(municipality==m) for m in fit['municipalities']]]
    return float(design@fit['coefficient'])


def fit_panel(rows, metric):
    ss=samples(rows, metric)
    if len(ss)<MIN_PANEL_TRANSITIONS or len({s[2] for s in ss})<MIN_PANEL_MUNICIPALITIES:
        return None
    candidates=[]
    for penalty in PENALTIES:
        fold_errors=[]
        for year in sorted({s[3] for s in ss})[-3:]:
            train=[s for s in ss if s[3]<year]; test=[s for s in ss if s[3]==year]
            if len(train)<MIN_PANEL_TRANSITIONS or len({s[2] for s in train})<MIN_PANEL_MUNICIPALITIES:
                continue
            fit=fit_ridge(train,penalty)
            fold_errors.extend(abs(ridge_delta(fit,s[0],s[2])-s[1]) for s in test)
        if fold_errors:
            candidates.append((float(np.mean(fold_errors)),-penalty,penalty))
    if not candidates:
        return None
    penalty=min(candidates)[2]
    fit=fit_ridge(ss,penalty)
    fit['validationMAEPerPerson']=min(candidates)[0]
    return fit
