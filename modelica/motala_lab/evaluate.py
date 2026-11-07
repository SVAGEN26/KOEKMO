"""Rolling-origin, nested validation with explicit retrospective/as-of evidence."""
from collections import defaultdict
from datetime import date
import math
from statistics import mean
from .data import METRICS, available, by_municipality
from .demography import project
from .fiscal import baseline
from .model import forecast

COMPARATORS=('reference','persistence','trend')


def evaluate(data, max_horizon=3):
    if type(max_horizon) is not int or not 1 <= max_horizon <= 10:
        raise ValueError('Evaluation horizon must be 1 to 10 years')
    groups=by_municipality(data['rows']); cases=[]; skipped=[]; fits=[]
    tasks=[]
    if data['evidenceClass']=='archived_as_of':
        if not data.get('evaluationOrigins'):
            raise ValueError('Archived evaluation requires explicit forecastDate/informationCutoff origins')
        for item in data['evaluationOrigins']:
            forecast_date=date.fromisoformat(item['forecastDate'])
            cutoff=date.fromisoformat(item['informationCutoff'])
            if cutoff>forecast_date:
                raise ValueError('Information cutoff after forecast date')
            tasks.append((item['municipality'], forecast_date.year, item['informationCutoff'], item['forecastDate']))
    else:
        for municipality, history in sorted(groups.items()):
            tasks.extend((municipality,r['year'],None,None) for r in history[1:-1])
    for municipality, origin, cutoff, forecast_date in tasks:
        observed={r['year']:r for r in groups.get(municipality,[])}
        training=available(data, origin, cutoff)
        own=by_municipality(training).get(municipality,[])
        if len(own)<2:
            skipped.append({'municipality':municipality,'originYear':origin,
                            'reason':'Insufficient accounts available at the information cutoff'})
            continue
        base_year=own[-1]['year']
        # Other municipalities may have newer accounts; keep a common last observation year.
        training=[r for r in training if r['year']<=base_year]
        steps=max_horizon+origin-base_year
        if steps>30:
            skipped.append({'municipality':municipality,'originYear':origin,'reason':'Opening observations too old'})
            continue
        try:
            candidate=forecast(training,municipality,steps)
            no_damping=forecast(training,municipality,steps,damp_demography=False)
            no_panel=forecast(training,municipality,steps,use_panel=False)
        except ValueError as exc:
            skipped.append({'municipality':municipality,'originYear':origin,'reason':str(exc)})
            continue
        fits.append({**{k:candidate[k] for k in ('municipality','originYear','methods','damping','trainingRows','trainingMunicipalities','warnings')},
                     'forecastDate':forecast_date,'informationCutoff':cutoff})
        reference=project(own,steps,1.)
        for h in range(1,max_horizon+1):
            target=origin+h; step=target-base_year
            if target not in observed:
                continue
            actual=observed[target]
            if cutoff and (not actual.get('sourceRelease') or actual['sourceRelease']<=forecast_date):
                skipped.append({'municipality':municipality,'originYear':origin,'targetYear':target,
                                'reason':'Outcome release unavailable or already known'})
                continue
            for metric in METRICS:
                predictions={'candidate':candidate['rows'][step-1][metric],
                             'persistence':baseline(own,metric,step,'persistence')[-1],
                             'trend':baseline(own,metric,step,'trend')[-1],
                             'no_demographic_damping':no_damping['rows'][step-1][metric],
                             'no_panel':no_panel['rows'][step-1][metric]}
                if metric=='population' and reference:
                    predictions['reference']=reference[step-1]['population']
                errors={m:v-actual[metric] for m,v in predictions.items()}
                cases.append({'municipality':municipality,'originYear':origin,'baseYear':base_year,'targetYear':target,
                              'horizonYears':h,'metric':metric,'unit':'persons' if metric=='population' else 'mnkr',
                              'definition':data['definitions'][metric],'evidenceClass':data['evidenceClass'],
                              'forecastDate':forecast_date,'informationCutoff':cutoff,'actual':actual[metric],
                              'predictions':predictions,'errors':errors})
    summaries=score_cases(cases)
    return {'evidenceClass':data['evidenceClass'],'cases':cases,'scores':summaries,'fits':fits,'skipped':skipped,
            'forecastSuperiorityProven':False,
            'limitations':[
                'Current Motala years have already been examined and are development evidence, not a blind final test.',
                'Revised annual-report history is not a preserved historical information set.',
                'Reference M0 historical finance unavailable: gross opening ledgers are missing; only its demographic equations are backtested.',
                'SKR comparisons require independently archived, definition-matched forecasts and outcomes.',
                'More forecast origins for the same target year are not independent outcomes.',
            ]+data.get('sourceNotes',[])}


def score_cases(cases):
    grouped=defaultdict(list)
    for row in cases:
        grouped[(row['municipality'],row['metric'],row['horizonYears'])].append(row)
    scores=[]
    for (municipality,metric,horizon),rows in sorted(grouped.items()):
        models=sorted({m for r in rows for m in r['errors']})
        summary={'municipality':municipality,'metric':metric,'horizonYears':horizon,
                 'n':len(rows),'distinctTargetYears':len({r['targetYear'] for r in rows}),'models':{},'comparisons':{}}
        for model in models:
            errors=[r['errors'][model] for r in rows if model in r['errors']]
            summary['models'][model]={'n':len(errors),'mae':mean(abs(e) for e in errors),
                                     'bias':mean(errors),'rmse':math.sqrt(mean(e*e for e in errors))}
        for model in models:
            if model=='candidate': continue
            matched=[r for r in rows if model in r['errors'] and 'candidate' in r['errors']]
            c=mean(abs(r['errors']['candidate']) for r in matched)
            b=mean(abs(r['errors'][model]) for r in matched)
            summary['comparisons'][model]={'n':len(matched),'meanPairedAbsoluteErrorDifference':c-b,
                                           'relativeMAEImprovement':(b-c)/b if b else None}
        scores.append(summary)
    return scores
