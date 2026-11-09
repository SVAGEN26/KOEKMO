"""Prepare reviewed, traceable planning inputs; never execute spreadsheet macros."""
import csv
import hashlib
import json
from pathlib import Path
from import_skr import read_workbook, extract

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'data/downloads/20261106T090534Z'
WORKBOOK = ROOT / 'data/Prognosunderlag-K-2026-2033-26028.xlsm'

def prepare():
    baseline = json.loads((ROOT / 'data/baseline.json').read_text())
    receipt = json.loads((ARCHIVE / 'manifest.json').read_text())
    for item in receipt['files']:
        if hashlib.sha256((ARCHIVE / item['file']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Archive checksum mismatch: ' + item['file'])
    book = read_workbook(WORKBOOK)
    cells = book['Blad 2 Indata']
    population = json.loads((ARCHIVE / 'bep6001-motala.json').read_text(encoding='utf-8-sig'))
    raw = {}
    for item in population['data']:
        area, year, age = item['key']
        if area != '0583':
            raise ValueError('Population input must be Motala')
        raw.setdefault(int(year), {})[int(age)] = float(item['values'][0])
    def groups(year):
        bins = raw[year]
        # Uniform ages inside each five-year bin, explicitly an approximation.
        out = [bins[1] + 2/5*bins[2], 3/5*bins[2] + bins[3] + bins[4]/5,
               3/5*bins[4], bins[4]/5 + sum(bins[i] for i in range(5,14)),
               sum(bins[i] for i in range(14,21))]
        if any(x <= 0 for x in out):
            raise ValueError('Missing or nonpositive age group')
        return out
    start = groups(2025)
    rows = []
    for year in range(2026,2034):
        g = groups(year)
        anchored = [b*x/old for b,x,old in zip(baseline['population'],g,start)]
        total = sum(baseline['population']) * raw[year][21]/raw[2025][21]
        cohorts = [x*total/sum(anchored) for x in anchored]
        col = 'CDEFGHIJ'[year-2026]
        if cells[col+'99']['value'] != year:
            raise ValueError('Unexpected SKR year heading')
        values = {name: cells[col+str(row)]['value'] for name,row in [('taxBaseGrowth',9),('labourCostGrowth',100),('otherPriceGrowth',101)]}
        if any(type(v) not in (int,float) or not -100 < v < 100 for v in values.values()):
            raise ValueError('Invalid SKR rate')
        rows.append({'year':year,'cohorts':cohorts,'sourceTotal':raw[year][21],
                     'olderGroups':[sum(raw[year][i] for i in range(14,17)),sum(raw[year][i] for i in range(17,19)),sum(raw[year][i] for i in range(19,21))],
                     **values,'skrCells':{name:col+str(row) for name,row in [('taxBaseGrowth',9),('labourCostGrowth',100),('otherPriceGrowth',101)]}})
    meta = json.loads((ARCHIVE/'kolada-kpi-metadata.json').read_text())
    kpis = {r['id']:r for r in meta['values']}
    observed = list(csv.DictReader((ARCHIVE/'kolada-motala-2010-2025.csv').open(encoding='utf-8-sig')))
    latest=[]
    for key, definition in kpis.items():
        valid = [r for r in observed if r['kpi']==key and r['gender']=='T' and r['value'] and r['isdeleted'].lower()!='true']
        if valid:
            r=max(valid,key=lambda r:int(r['year']))
            latest.append({'id':key,'title':definition['title'],'description':definition['description'],'year':int(r['year']),'value':float(r['value']),'status':r['status']})
    selection = book['Prognosunderlag']['B1']['value']
    data={'version':1,'municipality':'0583','baseYear':2025,'years':8,'activatedOn':'2026-11-06',
          'rows':rows,'sourceBaseTotal':raw[2025][21],
          'sources':{'archive':'data/downloads/20261106T090534Z',
                     'workbook':WORKBOOK.name,'workbookSha256':hashlib.sha256(WORKBOOK.read_bytes()).hexdigest(),
                     'skrSheet':'Blad 2 Indata','skrCircular':'26:28',
                     'population':'https://statistik.linkoping.se/PXWeb/pxweb/sv/Samlad_planering/Samlad_planering__LevaBo/bep6001.px/',
                     'populationMetadata':'bep6001-metadata.json','kolada':'https://api.kolada.se/v3/docs'},
          'revenueImport':{'status':'needs-municipality-selection-and-recalculation','selectionCell':'Prognosunderlag!B1','cachedSelection':selection,'cachedTax2026':book['Prognosunderlag']['C4']['value'],
                           'message':'Ingen kommun är vald och cachade intäkter är noll. Välj Motala (0583) i B1 och beräkna/spara en kopia innan en kommunal intäktsbana kan importeras. Makron har inte körts.'},
          'koladaLatest':sorted(latest,key=lambda r:r['id']),
          'documents':[{'title':'Budget 2026, plan 2027–2028','file':'budget-2026-plan-2027-2028.pdf'},
                       {'title':'Budget 2025, plan 2026–2027','file':'budget-2025-plan-2026-2027.pdf'}]+[{'title':f'Årsredovisning {y}','file':f'arsredovisning-{y}.pdf'} for y in range(2025,2021,-1)],
          'limitations':['Femårsåldrar delas proportionellt vid modellens åldersgränser. Förändringarna förankras i bokslutets kohorter och totalbefolkning; källprognosens 2025-total är 43132 mot bokslutets 43131.',
                         'Årsvisa restflöden återskapar den förankrade befolkningsbanan. De är inte observerad migration; födslar och dödsfall är fortfarande modellantaganden.',
                         'SKR:s nationella skatteunderlagstillväxt används som förenklad trend från bokslutets skatteintäkter, inte som Motala-prognos över skatter och bidrag.',
                         'SKR:s arbetskraftskostnadsindex är en proxy för lönekostnader exklusive pensioner. Separat pensionskostnad är fortsatt illustrativ.',
                         'Kolada-serier används som jämförelseunderlag, inte som automatiskt skattade kostnadsvikter. Definitioner och enheter måste hållas isär.',
                         'Budget-PDF:erna är tillgängliga som referenser. Framtida budgetbelopp och investeringsplaner är inte numeriskt importerade.']}
    revenue_file=ROOT/'data/skr-revenue-path.json'
    if revenue_file.exists():
        revenue=json.loads(revenue_file.read_text())
        audit=revenue['provenance']['recalculation']
        calculated=ROOT/audit['calculatedFile']
        if audit['sourceSha256']!=data['sources']['workbookSha256'] or hashlib.sha256(calculated.read_bytes()).hexdigest()!=audit['calculatedSha256']:
            raise ValueError('Recalculated workbook provenance mismatch')
        expected=extract(calculated,revenue['provenance']['cellMap'])
        if revenue['municipality']!='0583' or revenue['rows']!=expected['rows'] or [r['year'] for r in revenue['rows']]!=list(range(2026,2034)):
            raise ValueError('Revenue artifact does not match verified workbook cells')
        data['revenuePath']=revenue
        # SKR keeps the state's grant frame fixed in kronor after the budget bill's years. The site holds the
        # regulation grant per inhabitant from the year after the circular instead (see holdRegulation in scenario-inputs.js).
        data['regulationRule']={'heldFrom':int(revenue['vintage'][:4])+1,
            'evidence':'SCB TAB1981: regleringsbidraget per invånare 2005-2026 utan trend utom omföringen 2020-2021; SKR:s belopp för år två och tre för lågt i cirkulären 21:49, 22:54 och 23:56 (data/vintage-hindcast.json, research/data/skr-revenue-vintages.json).'}
        data['revenueImport']={'status':'active-recalculated-motala','selectionCell':'Prognosunderlag!B1','cachedSelection':583,'originalSelection':selection,
                               'message':'Motala (0583) är valt i en omräknad arbetskopia. SKR-referensen 2026–2033 är aktiv och inkluderar slutavräkningar och fastighetsavgift. Scenariot justerar beloppen med modellens förenklade befolknings- och skattesamband. Originalfilen är bevarad och inga makron har körts.'}
        data['limitations'][2]='SKR:s omräknade Motala-belopp är referens. Modellens scenariobelopp kan avvika genom förenklad befolknings-, skattesats- och utjämningsjustering; detta är inte en ny officiell SKR-prognos.'
    return data

if __name__=='__main__':
    output=ROOT/'data/planning-inputs.json'
    output.write_text(json.dumps(prepare(),ensure_ascii=False,indent=2)+'\n')
    print('Prepared', output)
