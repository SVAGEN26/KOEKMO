#!/usr/bin/env python3
"""Read SKR's own old forecasts of tax and general grants for the 13 municipalities, from the recovered workbooks.

    python3 scripts/read_skr_vintages.py [code ...]

The four workbooks (data/skr-historical/manifest.json; fetch with scripts/fetch_historical_skr.py) are general:
a municipality is chosen in Prognosunderlag!B1 and every amount is a formula. For each workbook and municipality
this script

  1. checks the original's SHA-256 against the manifest,
  2. writes a copy with the municipality's code in B1, the VBA project removed and every cached formula value
     emptied (the 2021 workbook is an XLS; LibreOffice converts it first, with macros disabled),
  3. lets a local LibreOffice recalculate the copy, with macro execution disabled,
  4. reads Blad 1 Totala intäkter: tax (row 38, with the settlements) and general grants (row 40, with LSS
     equalisation and the property fee) for the workbook's eight years, and checks the municipality's name,
     the circular, the years, that tax and grants sum to row 36 and that each is the sum of its parts.

Written to data/skr-historical/forecasts.json: mnkr, two totals a year, with the cell they came from. The
workbooks and the recalculated copies stay local (data/skr-historical/originals and recalculated, git-ignored).

LibreOffice: .local/calc-runtime/root as in scripts/recalculate_skr.py, or CALC_RUNTIME=/path/to/calc-runtime.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from import_skr import MUNICIPALITIES, read_workbook

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'data/skr-historical'
RUNTIME = Path(os.environ.get('CALC_RUNTIME') or ROOT / '.local/calc-runtime')
PROGRAM = RUNTIME / 'root/usr/lib/libreoffice/program'
TOTALS, INPUTS, FRONT = 'Blad 1 Totala intäkter', 'Blad 2 Indata', 'Prognosunderlag'
TAX_PARTS, GRANT_PARTS = (12, 28, 30, 32), (14, 16, 18, 20, 22, 24, 34)
# No macros, and every formula recalculated when a workbook is loaded.
PROFILE = '''<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema">
<item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop><prop oor:name="DisableMacrosExecution" oor:op="fuse"><value>true</value></prop></item>
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value></prop></item>
</oor:items>
'''


def convert(source, directory, profile):
    """LibreOffice loads the workbook, recalculates it and saves it as XLSX in the directory."""
    env = {**os.environ, 'LD_LIBRARY_PATH': f'{PROGRAM}:{RUNTIME / "root/usr/lib/x86_64-linux-gnu"}', 'SAL_USE_VCLPLUGIN': 'svp'}
    (profile / 'user').mkdir(parents=True, exist_ok=True)
    (profile / 'user/registrymodifications.xcu').write_text(PROFILE)
    done = subprocess.run([str(PROGRAM / 'soffice'), '-env:UserInstallation=' + profile.as_uri(), '--headless', '--norestore',
                           '--convert-to', 'xlsx:Calc MS Excel 2007 XML', '--outdir', str(directory), str(source)],
                          env=env, capture_output=True, text=True, timeout=180)
    out = directory / (source.stem + '.xlsx')
    if done.returncode or not out.exists():
        raise RuntimeError(f'LibreOffice failed on {source.name}: {done.stdout}{done.stderr}')
    return out


def sheet_path(archive, name):
    """The part that holds a sheet, from the workbook's own relations."""
    relations = dict(re.findall(r'<Relationship\b[^>]*?Id="([^"]+)"[^>]*?Target="([^"]+)"', archive.read('xl/_rels/workbook.xml.rels').decode())
                     + [(i, t) for t, i in re.findall(r'<Relationship\b[^>]*?Target="([^"]+)"[^>]*?Id="([^"]+)"', archive.read('xl/_rels/workbook.xml.rels').decode())])
    sheet = re.search(rf'<sheet\b[^>]*name="{re.escape(name)}"[^>]*r:id="([^"]+)"', archive.read('xl/workbook.xml').decode())
    target = relations[sheet.group(1)]
    return target.lstrip('/') if target.startswith('/') else 'xl/' + target


def select(source, target, code):
    """A macro-free copy with the municipality's code in Prognosunderlag!B1 and no cached formula values."""
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as dest:
        front = sheet_path(src, FRONT)
        for item in src.infolist():
            if 'vbaproject' in item.filename.lower():
                continue
            data = src.read(item.filename)
            if item.filename == front:
                data, n = re.subn(rb'<c r="B1"((?: [a-z]+="[^"]*")*?)(?: t="[^"]*")?(?:/>|>.*?</c>)',
                                  lambda m: b'<c r="B1"' + m.group(1) + f'><v>{int(code)}</v></c>'.encode(), data, count=1)
                if n != 1:
                    raise ValueError(f'{source.name}: no selection cell B1 in {front}')
            if item.filename == 'xl/workbook.xml':
                calc = b'<calcPr calcId="191029" fullCalcOnLoad="1" forceFullCalc="1" calcMode="auto"/>'
                data, n = re.subn(rb'<calcPr[^>]*/>', calc, data)
                if n != 1:
                    raise ValueError(f'{source.name}: unexpected calculation settings')
            if item.filename == '[Content_Types].xml':
                data = data.replace(b'application/vnd.ms-excel.sheet.macroEnabled.main+xml',
                                    b'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml')
                data = re.sub(rb'<Override[^>]*PartName="[^"]*vbaProject[^"]*"[^>]*/>', b'', data)
            if item.filename == 'xl/_rels/workbook.xml.rels':
                data = re.sub(rb'<Relationship\b[^>]*Type="[^"]*/vbaProject"[^>]*/>', b'', data)
            if item.filename.startswith('xl/worksheets/') and item.filename.endswith('.xml') and item.filename != front:
                data = re.sub(rb'(<f\b[^>]*/>|<f\b[^>]*>[^<]*</f>)<v\b[^>]*>[^<]*</v>', rb'\1', data)
            elif item.filename == front:
                data = re.sub(rb'(<f\b[^>]*/>|<f\b[^>]*>[^<]*</f>)<v\b[^>]*>[^<]*</v>', rb'\1', data)
            dest.writestr(item.filename, data)


def read(calculated, entry, code):
    """Tax and grants per year from a recalculated copy, after the checks in the module text."""
    book = read_workbook(calculated)
    front, totals, inputs = book[FRONT], book[TOTALS], book[INPUTS]
    value = lambda sheet, cell: (sheet.get(cell) or {}).get('value')
    if value(front, 'B1') != int(code) or value(front, 'C1') != MUNICIPALITIES[code]:
        raise ValueError(f'{entry["circular"]} {code}: selection is {value(front, "B1")} {value(front, "C1")}')
    if value(front, 'A2') != entry['circular']:
        raise ValueError(f'{entry["circular"]}: workbook says {value(front, "A2")}')
    rows = []
    for i, year in enumerate(range(entry['firstYear'], entry['lastYear'] + 1)):
        column, november = 'BCDEFGHI'[i], 'CDEFGHIJ'[i]
        if value(totals, column + '9') != year:
            raise ValueError(f'{entry["circular"]}: column {column} is {value(totals, column + "9")}, not {year}')
        cell = {r: value(totals, f'{column}{r}') or 0 for r in (*TAX_PARTS, *GRANT_PARTS, 36, 38, 40)}
        if any(not isinstance(v, (int, float)) for v in cell.values()):
            raise ValueError(f'{entry["circular"]} {code} {year}: formula error')
        checks = [(cell[38], sum(cell[r] for r in TAX_PARTS)), (cell[40], sum(cell[r] for r in GRANT_PARTS)), (cell[36], cell[38] + cell[40])]
        if cell[38] <= 0 or cell[40] == 0 or any(abs(a - b) > 0.01 for a, b in checks):
            raise ValueError(f'{entry["circular"]} {code} {year}: parts do not sum: {cell}')
        rows.append({'year': year, 'tax': round(cell[38] / 1000, 3), 'grants': round(cell[40] / 1000, 3),
                     'novemberPopulation': round(value(inputs, november + '29')), 'cells': [f'{column}38', f'{column}40']})
    return rows


def main():
    codes = sys.argv[1:] or sorted(MUNICIPALITIES)
    if not (PROGRAM / 'soffice').exists():
        raise SystemExit('Local LibreOffice runtime missing; see data/skr-motala/README.md, or set CALC_RUNTIME')
    manifest = json.loads((HERE / 'manifest.json').read_text())
    output = HERE / 'forecasts.json'
    vintages = {v['circular']: v for v in json.loads(output.read_text())['vintages']} if output.exists() else {}
    with tempfile.TemporaryDirectory(prefix='skr-vintages-') as tmp:
        tmp = Path(tmp)
        for entry in manifest['files']:
            original = HERE / 'originals' / entry['file']
            if hashlib.sha256(original.read_bytes()).hexdigest() != entry['sha256']:
                raise SystemExit(f'{original.name}: checksum differs from the manifest')
            circular = entry['circular'].replace(':', '')
            source = original if original.suffix == '.xlsm' else convert(original, tmp / 'converted', tmp / 'profile')
            keep = HERE / 'recalculated' / circular
            keep.mkdir(parents=True, exist_ok=True)
            vintage = vintages.setdefault(entry['circular'], {})
            vintage.update({'circular': entry['circular'], 'published': entry['publicationDate'], 'file': entry['file'],
                            'sha256': entry['sha256'], 'originalUrl': entry['originalUrl'], 'archiveUrl': entry['archiveUrl']})
            vintage.setdefault('municipalities', {})
            for code in codes:
                selected = tmp / f'{circular}-{code}' / f'Prognosunderlag-{code}-{circular}.xlsx'
                selected.parent.mkdir()
                select(source, selected, code)
                calculated = convert(selected, keep, tmp / 'profile')
                vintage['municipalities'][code] = {'name': MUNICIPALITIES[code], 'rows': read(calculated, entry, code),
                                                   'recalculatedSha256': hashlib.sha256(calculated.read_bytes()).hexdigest()}
                print(entry['circular'], code, MUNICIPALITIES[code], 'ok', flush=True)
            vintage['municipalities'] = dict(sorted(vintage['municipalities'].items()))
            if hashlib.sha256(original.read_bytes()).hexdigest() != entry['sha256']:
                raise SystemExit(f'{original.name} changed during the run')
    engine = subprocess.run([str(PROGRAM / 'soffice'), '--version'], capture_output=True, text=True,
                            env={**os.environ, 'LD_LIBRARY_PATH': f'{PROGRAM}:{RUNTIME / "root/usr/lib/x86_64-linux-gnu"}'}).stdout.strip()
    output.write_text(json.dumps({
        'source': {'publisher': 'Sveriges Kommuner och Regioner (SKR)', 'title': 'Prognosunderlag K (kommuner)',
                   'retrievedFrom': 'Internet Archive; addresses and checksums in manifest.json',
                   'terms': 'Selected figures quoted from SKR with reference, for research and comparison. The workbooks are SKR material and are not redistributed.'},
        'definition': 'SKR\'s forecast at the time. tax: Blad 1 Totala intäkter row 38, tax revenue with the settlements. '
                      'grants: row 40, general grants and equalisation with LSS equalisation and the property fee. '
                      'Workbook unit tkr; here mnkr. novemberPopulation: Blad 2 Indata row 29, the municipality\'s '
                      'inhabitants 1 November of the year before, as the workbook assumed.',
        'method': 'Municipality selected in Prognosunderlag!B1 of a macro-free copy, cached values emptied, recalculated in '
                  f'{engine} with macro execution disabled. Name, circular, years and sums checked (scripts/read_skr_vintages.py).',
        'sheet': TOTALS,
        'vintages': sorted(vintages.values(), key=lambda v: v['published'])}, ensure_ascii=False, indent=1) + '\n')


if __name__ == '__main__':
    main()
