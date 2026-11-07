"""Read cached spreadsheet cells without third-party packages or running macros."""
import sys
import argparse
import hashlib
import json
import math
from pathlib import Path
import posixpath
import zipfile
import xml.etree.ElementTree as ET

NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
PKG='{http://schemas.openxmlformats.org/package/2006/relationships}'

def is_motala(value):
    """Recognise the municipality independently of the caller's cell mapping."""
    if isinstance(value,str):
        return value.strip().casefold() in ('motala','0583','583','583.0')
    return type(value) in (int,float) and value==583

def read_workbook(filename):
    with zipfile.ZipFile(filename) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            strings=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        relations={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets={}
        for sheet in ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',NS):
            target=relations[sheet.attrib['{'+NS['r']+'}id']]
            path=target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl',target))
            cells={}
            for c in ET.fromstring(z.read(path)).findall('.//m:sheetData/m:row/m:c',NS):
                typ=c.attrib.get('t')
                v=c.find('m:v',NS)
                formula=c.find('m:f',NS)
                raw=v.text if v is not None else None
                if typ=='s' and raw is not None: value=strings[int(raw)]
                elif typ=='inlineStr': value=''.join(c.find('m:is',NS).itertext())
                elif typ in ('str','e'): value=raw
                elif raw is None: value=None
                else:
                    try: value=float(raw)
                    except ValueError: value=raw
                cells[c.attrib['r']]={'value':value,'formula':formula.text if formula is not None else None}
            sheets[sheet.attrib['name']]=cells
    return sheets

def extract(filename,mapping):
    sheets=read_workbook(filename)
    def get(ref):
        try: cell=sheets[ref['sheet']][ref['cell']]
        except KeyError as e: raise ValueError(f'Missing mapped cell {ref}') from e
        if cell['value'] is None: raise ValueError(f'No cached value in {ref}; calculate and save the workbook in Excel first')
        return cell['value']
    check=mapping['municipalityCheck']
    if not is_motala(check['expected']): raise ValueError('Municipality mapping must identify Motala (0583)')
    if not is_motala(get(check)): raise ValueError('Municipality selection must be Motala (0583); select Motala and recalculate/save first')
    # The selection cell is user input. Without a recalculation its formula caches still hold the previous
    # municipality's figures, so a formula cell that derives the name from the selection must agree too.
    calculated=mapping.get('calculatedMunicipalityCheck')
    if calculated:
        try: cell=sheets[calculated['sheet']][calculated['cell']]
        except KeyError as e: raise ValueError(f'Missing mapped cell {calculated}') from e
        if not cell['formula']: raise ValueError('calculatedMunicipalityCheck must point at a formula cell')
        if not is_motala(cell['value']): raise ValueError('Calculated municipality is not Motala; the workbook was not recalculated after selection')
    else:
        print('Warning: no calculatedMunicipalityCheck in mapping; cached values may belong to the previously selected municipality',file=sys.stderr)
    rows=[]
    for entry in mapping['rows']:
        row={'year':entry['year']}
        for field in ['tax','grants','population']:
            value=get(entry[field])
            if not isinstance(value,(int,float)): raise ValueError(f'Non-numeric {field}: {value}')
            scale=entry[field].get('scale',1)
            row[field]=value*scale
            if not math.isfinite(row[field]) or row[field]<=0: raise ValueError(f'Nonpositive or nonfinite {field}; mapping must use positive revenue totals')
        rows.append(row)
    if len({r['year'] for r in rows})!=len(rows): raise ValueError('Duplicate mapped year')
    return {'municipality':'0583','vintage':mapping['vintage'],'populationReference':mapping['populationReference'],'rows':rows,'provenance':{'workbook':filename.name,'sha256':hashlib.sha256(filename.read_bytes()).hexdigest(),'cellMap':mapping,'cachedFormulasNotRecalculated':True,'calculatedMunicipalityVerified':bool(calculated)}}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workbook',type=Path)
    parser.add_argument('--inspect',action='store_true')
    parser.add_argument('--sheet')
    parser.add_argument('--map',dest='mapping',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.inspect:
        for name,cells in read_workbook(args.workbook).items():
            print(f'\nWorksheet {name}: {len(cells)} populated cells')
            selected=[(key,c) for key,c in cells.items() if args.sheet==name or str(c['value']).strip().lower() in ('motala','0583','583','583.0')]
            for key,c in selected[:250]: print(key,json.dumps(c,ensure_ascii=False))
        return
    if not args.mapping or not args.output: parser.error('Use --inspect, or both --map and --output')
    try: output=extract(args.workbook,json.loads(args.mapping.read_text()))
    except (ValueError,KeyError) as e: raise SystemExit(str(e))
    args.output.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n')
    print('Extracted',len(output['rows']),'years into',args.output)

if __name__=='__main__': main()
