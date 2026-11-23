#!/usr/bin/env python3
"""Check the units of the Modelica library with OpenModelica's unit checker.

    OMC=/path/to/omc python3 scripts/check_units.py

OpenModelica's checker (--unitChecking) knows only SI units. It says nothing about "MSEK" or "a",
so a check of the library as written passes without checking anything. This script copies
Kommunekonomi.mo to a temporary folder, writes the money units as an SI unit the checker knows
("MSEK" and "SEK" as "mol", "a" as "s", "1/a" as "1/s"), and checks Motala.Annual, Motala.Continuous and
Kommunekonomi.Continuous.Economy. Any equation the checker calls inconsistent fails the script.

What it covers: equations between variables that declare a unit (Kommunekonomi.Units), including
der() of a stock against its flows and the connections between components. It does not cover
algorithm sections: the annual rules (`when calendar.tick` with `:=`), which hold most of Annual and
the yearly steps of Continuous, are not checked. Removing `*Units.year` from the migration step in
Components.Demography goes unnoticed. Variables without a unit are inferred by the checker, not
checked, and SEK and MSEK are the same unit to it (the factor 1e6 is a plain number).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OMC = os.environ.get('OMC') or shutil.which('omc') or '/home/johti17/OpenModelicaWork/om-install/bin/omc'
MODELS = ('Motala.Annual', 'Motala.Continuous', 'Kommunekonomi.Continuous.Economy')
SI = {'"MSEK"': '"mol"', '"MSEK/a"': '"mol/s"', '"SEK"': '"mol"', '"a"': '"s"', '"1/a"': '"1/s"'}


def main():
    source = (ROOT / 'modelica/Kommunekonomi.mo').read_text()
    units = source[source.index('package Units'):source.index('end Units;')]
    translated = units
    for unit, si in SI.items():
        translated = re.sub(rf'unit = {re.escape(unit)}', f'unit = {si}', translated)
    if translated == units:
        raise SystemExit('No units found in Kommunekonomi.Units')
    with tempfile.TemporaryDirectory(prefix='units-') as tmp:
        tmp = Path(tmp)
        (tmp / 'Kommunekonomi.mo').write_text(source.replace(units, translated))
        shutil.copy(ROOT / 'modelica/Motala.mo', tmp)
        (tmp / 'check.mos').write_text('setCommandLineOptions("--unitChecking"); getErrorString();\n'
                                       'loadFile("Kommunekonomi.mo"); getErrorString();\n'
                                       'loadFile("Motala.mo"); getErrorString();\n'
                                       + ''.join(f'checkModel({m}); getErrorString();\n' for m in MODELS))
        out = subprocess.run([OMC, 'check.mos'], cwd=tmp, capture_output=True, text=True, timeout=600).stdout
    checked = re.findall(r'Check of (\S+) completed successfully', out)
    problems = sorted(set(re.findall(r'INCONSISTENT due to specified unit information: ([^\n]+)', out)))
    for p in problems:
        print('inconsistent:', p)
    if checked != list(MODELS):
        print(out[-3000:])
        raise SystemExit(f'Checked {checked}, expected {list(MODELS)}')
    if problems:
        raise SystemExit(f'{len(problems)} equations with inconsistent units')
    print(f'Units consistent in {", ".join(MODELS)}')


if __name__ == '__main__':
    sys.exit(main())
