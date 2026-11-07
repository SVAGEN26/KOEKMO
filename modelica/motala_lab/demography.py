"""Five-cohort transition, annual conservation, and training-only damping selection."""
import numpy as np

DAMPING = (0.0, 0.5, 1.0)


def natural(p, births, rates):
    survivors = np.asarray(p, dtype=float) * (1-np.asarray(rates))
    ageing = survivors / np.array([7, 9, 3, 46, np.inf])
    return survivors-ageing+np.r_[births, ageing[:-1]]


def calibration(history):
    # Only the latest three years enter calibration. Missing older age data
    # must not discard usable recent observations or shorten fiscal history.
    if len(history) < 2 or 'cohorts' not in history[-1]:
        return None
    last = history[-1]
    if min(last['cohorts']) <= 0:
        return None
    rates = np.array([.0004, .0001, .0002, .0018, 0.])
    rates[-1] = (last['deaths']-np.dot(last['cohorts'][:4], rates[:4]))/last['cohorts'][-1]
    if not 0 <= rates[-1] <= 1:
        return None
    recent = history[-3:]
    residuals = [np.asarray(b['cohorts'])-natural(a['cohorts'], b['births'], rates)
                 for a, b in zip(recent, recent[1:])
                 if b['year'] == a['year']+1 and 'cohorts' in a and 'cohorts' in b]
    if not residuals:
        return None
    return {'p0': list(last['cohorts']), 'births0': last['births'],
            'deathRates': rates.tolist(), 'residualMigration': np.mean(residuals, axis=0).tolist()}


def project(history, horizon, damping=1.0):
    c = calibration(history)
    if c is None:
        return None
    p = np.array(c['p0']); out = []
    for step in range(1, horizon+1):
        births = c['births0']*p[3]/c['p0'][3]
        deaths = np.dot(p, c['deathRates'])
        migration = np.array(c['residualMigration'])*damping**step
        new = natural(p, births, c['deathRates'])+migration
        if np.min(new) < 0 or np.sum(new) <= 0:
            return None
        balance = sum(new)-sum(p)-births+deaths-sum(migration)
        if abs(balance) > 1e-7:
            raise ArithmeticError('Population conservation failed')
        out.append({'population': float(sum(new)), 'cohorts': new.tolist(),
                    'births': float(births), 'deaths': float(deaths),
                    'migration': float(sum(migration)), 'populationBalance': float(balance)})
        p = new
    return out


def select_damping(history):
    # All validation targets here are already inside the outer training window.
    scores = []
    for damping in DAMPING:
        errors = []
        for i in range(2, len(history)):
            if history[i]['year'] != history[i-1]['year']+1:
                continue
            prediction = project(history[:i], 1, damping)
            if prediction:
                errors.append(abs(prediction[0]['population']-history[i]['population']))
        if errors:
            scores.append((float(np.mean(errors)), -damping, damping))
    # No evidence: preserve the original transition; do not tune on the next year.
    return min(scores)[2] if scores else 1.0
