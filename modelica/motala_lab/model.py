"""M1 candidate: fit independent observations, then project a coherent ledger.

Tax/grant splits and detailed historical cash flows are not invented when only
aggregate accrual observations exist. Current cash/debt scenarios are handled
separately by Modelica and never advertised as historical forecast evidence.
"""
import copy
import math
from . import demography, fiscal
from .data import by_municipality


def _local_choice(history, metric):
    if len(history)<5:
        return 'persistence'
    scores=[]
    for method in ('persistence','trend'):
        errors=[]
        for i in range(2,len(history)):
            if history[i]['year']!=history[i-1]['year']+1:
                continue
            earlier=history[:i]
            # Refit demography within this inner fold as well.
            pop=demography.project(earlier,1,demography.select_damping(earlier))
            if not pop:
                pop=[{'population':earlier[-1]['population']}]
            delta=fiscal.trailing_slope(earlier,metric,True)*.5 if method=='trend' else 0.
            value=(earlier[-1][metric]/earlier[-1]['population']+delta)*pop[0]['population']
            errors.append(abs(value-history[i][metric]))
        if len(errors)>=2:
            scores.append((sum(errors)/len(errors),method!='persistence',method))
    return min(scores)[2] if scores else 'persistence'


def forecast(training_rows, municipality='0583', horizon=3, damp_demography=True, use_panel=True):
    if type(horizon) is not int or not 1<=horizon<=30:
        raise ValueError('Horizon must be 1 to 30 years')
    groups=by_municipality(training_rows)
    history=groups.get(municipality,[])
    if len(history)<2:
        raise ValueError('At least two historical observations required for target municipality')
    if any(b['year']!=a['year']+1 for a,b in zip(history,history[1:])):
        raise ValueError('Target municipality history must be consecutive')
    if any(r['year']>history[-1]['year'] for r in training_rows):
        raise ValueError('Panel contains future observation years relative to target origin')
    damping=demography.select_damping(history) if damp_demography else 1.
    population=demography.project(history,horizon,damping)
    warnings=[]
    if population is None:
        population=[{'population':history[-1]['population']} for _ in range(horizon)]
        warnings.append('Cohort data unavailable or infeasible; population persistence used')
    fits={metric:fiscal.fit_panel(training_rows,metric) if use_panel else None for metric in fiscal.COMPONENTS}
    methods={metric:('ridge' if fits[metric] else _local_choice(history,metric)) for metric in fiscal.COMPONENTS}
    if any(f is None for f in fits.values()):
        warnings.append('Insufficient panel history: simple per-person forecasts used; no ridge model estimated')
    # Recursive predictions; observed future population/expenses never enter.
    state=copy.deepcopy(history[-2:]); rows=[]
    for step in range(1,horizon+1):
        current={'municipality':municipality,'year':history[-1]['year']+step,**population[step-1]}
        for metric in fiscal.COMPONENTS:
            fit=fits[metric]
            if fit:
                delta=fiscal.ridge_delta(fit,fiscal.features(state[-2],state[-1],metric),municipality)
                value=(state[-1][metric]/state[-1]['population']+delta)*current['population']
            else:
                delta=fiscal.trailing_slope(history,metric,True)*sum(.5**j for j in range(1,step+1)) if methods[metric]=='trend' else 0.
                value=(history[-1][metric]/history[-1]['population']+delta)*current['population']
            if not math.isfinite(value) or (metric=='netCost' and value<0):
                value=history[-1][metric]
                warnings.append(f'{metric}, step {step}: infeasible forecast replaced with last observed value')
            current[metric]=float(value)
        current['result']=current['taxAndGrants']-current['netCost']+current['financeNet']
        current['ledgerResidual']=current['result']-current['taxAndGrants']+current['netCost']-current['financeNet']
        rows.append(current); state.append(current)
    return {'model':'M1','originYear':history[-1]['year'],'municipality':municipality,
            'damping':damping,'demographicCalibration':demography.calibration(history),
            'methods':methods,'fits':fits,'warnings':sorted(set(warnings)),
            'trainingRows':len(training_rows),'trainingMunicipalities':len(groups),'rows':rows}
