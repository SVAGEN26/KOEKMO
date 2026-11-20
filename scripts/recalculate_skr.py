"""Select a municipality in a copy and recalculate without VBA using local LibreOffice."""
import argparse
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import zipfile
from import_skr import MUNICIPALITIES, read_workbook, extract

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/Prognosunderlag-K-2026-2033-26028.xlsm'
# SKR's workbook is not redistributed. The extract quotes a few figures from it
# with this reference; fetch the workbook from SKR to reproduce them.
CITATION={'publisher':'Sveriges Kommuner och Regioner (SKR)','title':'Prognosunderlag K 2026–2033','circular':'26:28','published':'2026-10-06',
          'url':'https://skr.se/download/18.22a5529f1a0fb7804e67d572/1791283712510/Prognosunderlag-K-2026-2033-26028.xlsm',
          'page':'https://skr.se/ekonomiochbudgetplanering/skatteunderlagsprognoserochmodellverktyg.8271.html',
          'terms':'Selected figures quoted from SKR with reference, for research and comparison. The workbook itself is SKR material and is not redistributed.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('municipality',nargs='?',default='0583',choices=MUNICIPALITIES)
    code=parser.parse_args().municipality
    code_num=int(code)
    name=MUNICIPALITIES[code]
    directory=ROOT/('data/skr-motala' if code=='0583' else f'.local/skr-{code}')
    output=ROOT/('data/skr-revenue-path.json' if code=='0583' else f'data/municipalities/{code}/skr-revenue-path.json')
    runtime=ROOT/'.local/calc-runtime/root'
    program=runtime/'usr/lib/libreoffice/program'
    executable=program/'soffice'
    if not executable.exists():
        raise SystemExit('Local LibreOffice runtime missing; see data/skr-motala/README.md')
    directory.mkdir(parents=True,exist_ok=True)
    stem='Prognosunderlag-Motala-0583' if code=='0583' else f'Prognosunderlag-{code}'
    selected=directory/f'{stem}-selected.xlsm'
    sanitized=directory/f'{stem}.xlsx'
    digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    with zipfile.ZipFile(SOURCE) as src,zipfile.ZipFile(selected,'w',compression=zipfile.ZIP_DEFLATED) as dest:
        for item in src.infolist():
            data=src.read(item.filename)
            if item.filename=='xl/worksheets/sheet1.xml':
                data,n=re.subn(rb'<c r="B1" s="358"/>',f'<c r="B1" s="358"><v>{code_num}</v></c>'.encode(),data)
                if n!=1:raise ValueError('Unexpected selection-cell layout; inspect workbook first')
            if item.filename=='xl/workbook.xml':
                data,n=re.subn(rb'<calcPr[^>]*/>',b'<calcPr calcId="191029" fullCalcOnLoad="1" forceFullCalc="1" calcMode="auto"/>',data)
                if n!=1:raise ValueError('Unexpected calculation settings')
            dest.writestr(item,data)
    with zipfile.ZipFile(selected) as src,zipfile.ZipFile(sanitized,'w',compression=zipfile.ZIP_DEFLATED) as dest:
        for item in src.infolist():
            if 'vbaproject' in item.filename.lower():continue
            data=src.read(item.filename)
            if item.filename=='[Content_Types].xml':
                data=data.replace(b'application/vnd.ms-excel.sheet.macroEnabled.main+xml',b'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml')
                data=re.sub(rb'<Override[^>]*PartName="[^"]*vbaProject[^"]*"[^>]*/>',b'',data)
            if item.filename=='xl/_rels/workbook.xml.rels':
                data=re.sub(rb'<Relationship\b[^>]*Type="[^"]*/vbaProject"[^>]*/>',b'',data)
            if item.filename.startswith('xl/worksheets/') and item.filename.endswith('.xml'):
                data=re.sub(rb'(<f(?:\s[^>]*)?>.*?</f>)<v(?:\s[^>]*)?>.*?</v>',rb'\1<v/>',data)
            dest.writestr(item,data)
    with zipfile.ZipFile(sanitized) as z:
        if any('vbaproject' in n.lower() for n in z.namelist()):raise ValueError('VBA removal failed')
    profile=ROOT/f'.local/calc-runtime/profile-{code}'
    (profile/'user').mkdir(parents=True,exist_ok=True)
    (profile/'user/registrymodifications.xcu').write_text('''<?xml version="1.0" encoding="UTF-8"?><oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop><prop oor:name="DisableMacrosExecution" oor:op="fuse"><value>true</value></prop></item></oor:items>''')
    out=directory/'recalculated';out.mkdir(exist_ok=True)
    env=os.environ.copy();env['LD_LIBRARY_PATH']=str(program)+':'+str(runtime/'usr/lib/x86_64-linux-gnu');env['SAL_USE_VCLPLUGIN']='svp'
    version=subprocess.check_output([str(executable),'--version'],env=env,text=True).strip()
    result=subprocess.run([str(executable),'-env:UserInstallation='+profile.as_uri(),'--headless','--norestore','--convert-to','xlsx:Calc MS Excel 2007 XML','--outdir',str(out),str(sanitized)],env=env,capture_output=True,text=True,timeout=90)
    (directory/'recalculation.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError('LibreOffice recalculation failed; see recalculation.log')
    calculated=out/sanitized.name
    book=read_workbook(calculated)
    if book['Prognosunderlag']['B1']['value']!=code_num or book['Prognosunderlag']['C1']['value']!=name:raise ValueError(f'Calculated selection is not {name}')
    mapping={**({'municipality':code} if code!='0583' else {}),'vintage':'2026-10-06','populationReference':'1 November of the preceding year (Blad 2 Indata C29:J29); not year-end population.',
             'municipalityCheck':{'sheet':'Prognosunderlag','cell':'B1','expected':code_num},
             'calculatedMunicipalityCheck':{'sheet':'Prognosunderlag','cell':'C1'},'rows':[],
             'definition':'Tax is Blad 1 row 38 including tax settlements. Grants are row 40 including general grants/equalisation, LSS and municipal property fee. Regulation is row 18, the regulation grant (negative: fee) within the grants. Original workbook units tkr; converted to mnkr.'}
    components=[]
    for i,year in enumerate(range(2026,2034)):
        col='BCDEFGHI'[i];popcol='CDEFGHIJ'[i]
        if book['Blad 1 Totala intäkter'][col+'9']['value']!=year:raise ValueError('Wrong forecast year')
        values={r:book['Blad 1 Totala intäkter'].get(col+str(r),{}).get('value') or 0 for r in [12,14,16,18,20,22,24,26,28,30,32,34,36,38,40]}
        if any(not isinstance(v,(int,float)) for v in values.values()):raise ValueError('Formula error in revenue components')
        checks=[(values[38],sum(values[r] for r in [12,28,30,32])),(values[40],sum(values[r] for r in [14,16,18,20,22,24,34])),(values[38]+values[40],values[36])]
        if any(abs(a-b)>0.01 for a,b in checks):raise ValueError('Revenue components fail reconciliation')
        mapping['rows'].append({'year':year,'regulation':{'sheet':'Blad 1 Totala intäkter','cell':col+'18','scale':0.001},'tax':{'sheet':'Blad 1 Totala intäkter','cell':col+'38','scale':0.001},'grants':{'sheet':'Blad 1 Totala intäkter','cell':col+'40','scale':0.001},'population':{'sheet':'Blad 2 Indata','cell':popcol+'29'}})
        components.append({'year':year,'tkrByOutputRow':values})
    (directory/'skr-map.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    path=extract(calculated,mapping)
    receipt={'source':SOURCE.name,'sourceSha256':digest,'selectedCopy':selected.name,'cell':'Prognosunderlag!B1','value':code_num,
             'recalculated':True,'engine':version,'calculatedFile':str(calculated.relative_to(ROOT)),
             'calculatedSha256':hashlib.sha256(calculated.read_bytes()).hexdigest(),'vbaRemovedBeforeRecalculation':True,'macrosExecuted':False,'components':components}
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=digest:raise ValueError('Original source changed')
    path['provenance']['recalculation']=receipt
    path['provenance']['circular']=CITATION['circular']
    path['source']=CITATION
    output.write_text(json.dumps(path,ensure_ascii=False,indent=2)+'\n')
    (directory/'selection-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(f'Recalculated and reconciled {name} revenue for {len(path["rows"])} years. Original preserved.')

if __name__=='__main__':main()
