"""Standalone Swedish results report; no server or external assets required."""
import csv
from html import escape
from pathlib import Path


def write_report(bundle,directory):
    directory=Path(directory)
    evaluation=bundle['evaluation'];candidate=bundle['candidate']
    with (directory/'errors.csv').open('w',newline='') as f:
        fields=['municipality','originYear','targetYear','horizonYears','metric','unit','definition','evidenceClass','model','actual','prediction','error']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for c in evaluation['cases']:
            for m,v in c['predictions'].items():
                writer.writerow({**{k:c[k] for k in fields[:8]},'model':m,'actual':c['actual'],'prediction':v,'error':v-c['actual']})
    with (directory/'forecast.csv').open('w',newline='') as f:
        fields=['year','population','taxAndGrants','netCost','financeNet','result']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for row in candidate['rows']:writer.writerow({k:row[k] for k in fields})
    names={'result':'Årets resultat','netCost':'Nettokostnad inkl. avskrivningar','taxAndGrants':'Härledda skatter och bidrag',
           'financeNet':'Finansnetto','population':'Befolkning'}
    score_rows=[]
    for s in evaluation['scores']:
        if s['municipality']!=candidate['municipality']:continue
        cells=[escape(names.get(s['metric'],s['metric'])),str(s['horizonYears']),str(s['n'])]
        for m in ('candidate','reference','persistence','trend'):
            cells.append(f"{s['models'][m]['mae']:.2f}" if m in s['models'] else 'Saknas')
        score_rows.append('<tr>'+''.join('<td>'+c+'</td>' for c in cells)+'</tr>')
    forecasts=['<tr>'+''.join(f'<td>{r[k]:.2f}</td>' if k!='year' else f'<td>{r[k]}</td>'
                            for k in ('year','population','taxAndGrants','netCost','financeNet','result'))+'</tr>' for r in candidate['rows']]
    status=bundle['decision']
    html=f'''<!doctype html><html lang="sv"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motala: M1 och jämförelser</title><style>
body{{font:17px/1.55 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#182631;background:#f8fafb}}
h1,h2{{line-height:1.2}}table{{border-collapse:collapse;width:100%;background:white;font-size:.9rem}}td,th{{border-bottom:1px solid #ccd6dc;padding:.6rem;text-align:right}}td:first-child,th:first-child{{text-align:left}}.notice{{background:#fff1cf;padding:1rem;border-left:5px solid #a86708}}code{{overflow-wrap:anywhere}}.scroll{{overflow-x:auto}}</style>
<h1>Motala: kandidat M1 och historisk jämförelse</h1>
<p>Körning <code>{escape(bundle['runId'])}</code>. Prognosdatum {escape(bundle['forecastDate'])}.
Senaste observation {candidate['originYear']}. Modell- och dataversioner finns i manifest.json.</p>
<p class="notice">{escape(status['summary'])} SKR-jämförelse: {escape(bundle['benchmarkStatus'])}.
Historiska resultat är {escape(evaluation['evidenceClass'])}. Ingen överlägsenhet mot SKR är visad.</p>
<h2>Historiska prognosfel för Motala</h2><p>MAE: lägre är bättre. Belopp i mnkr; befolkning i personer.
Horisonten i den retrospektiva tabellen räknas från sista observerade året, inte från ett verifierat historiskt publiceringsdatum.
Modeller jämförs på samma fall. Saknade historiska bruttobokslut gör att M0 bara kan jämföras för befolkning.</p>
<div class="scroll"><table><thead><tr><th>Variabel</th><th>År framåt</th><th>Fall</th><th>M1</th><th>M0</th><th>Senaste värde</th><th>Dämpad trend</th></tr></thead><tbody>{''.join(score_rows)}</tbody></table></div>
<h2>Aktuell prognoskandidat</h2><p>Modellen tränades på {candidate['trainingRows']} kommunår från {candidate['trainingMunicipalities']} kommun(er).
Migreringsresidualernas årliga faktor: {candidate['damping']}.
Skatter och bidrag är en sammanlagd serie rekonstruerad ur avrundade bokslut; den är inte en verifierad SKR-serie.</p>
<div class="scroll"><table><thead><tr><th>År</th><th>Invånare</th><th>Skatter + bidrag</th><th>Nettokostnad</th><th>Finansnetto</th><th>Resultat</th></tr></thead><tbody>{''.join(forecasts)}</tbody></table></div>
<h2>Metodval och begränsningar</h2><ul>{''.join('<li>'+escape(s)+'</li>' for s in candidate['warnings']+evaluation['limitations'])}</ul>
<p>Native Modelica: {escape(bundle['native']['status'])}. Tillgångar, skuld och kassa i Modelica är ett separat finansieringsscenario.
Antaganden om investeringar och pensionsutbetalningar är inte prognosvaliderade.</p>
<h2>Nästa experiment</h2><p>{escape(status['nextExperiment'])}</p>
<p><a href="results.json">Samtliga resultat och deltester</a> · <a href="errors.csv">Prognosfel som CSV</a> ·
<a href="forecast.csv">Prognos som CSV</a> · <a href="manifest.json">Reproducerbarhet</a> · <a href="native/Scenario.mo">Körbar Modelica</a></p></html>'''
    (directory/'report.html').write_text(html)
