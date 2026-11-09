"""Build the static site into site/dist without network access.

The forecast engine is OpenModelica's in-browser compiler; stage it first with
scripts/stage_omc.py. The result is plain static files, ready for GitHub Pages.
"""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'site/dist'
OMC = ROOT / 'site/omc-web'
# engine.js is the independent JavaScript reference for the tests; the site never runs it.
NOT_SHIPPED = {'engine.js'}
DATA = ['baseline.json', 'history.json', 'sources.json', 'backtest.json', 'municipal-benchmarks.json',
        'operating-accounts-history.json', 'planning-inputs.json', 'skr-revenue-path.json']


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    manifest_file = OMC / 'manifest.json'
    if not manifest_file.is_file():
        raise SystemExit('OpenModelica web compiler missing. Run scripts/stage_omc.py <share/omc/web> first.')
    manifest = json.loads(manifest_file.read_text())
    for name, entry in manifest['files'].items():
        if sha(OMC / name) != entry['sha256']:
            raise SystemExit(f'site/omc-web/{name} does not match its manifest. Stage the compiler again.')

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    for source in (ROOT / 'site/src').iterdir():
        if source.is_file() and source.name not in NOT_SHIPPED:
            shutil.copy2(source, DIST / source.name)
    for name in DATA:
        shutil.copy2(ROOT / 'data' / name, DIST / name)
    shutil.copy2(ROOT / 'modelica/Kommunekonomi.mo', DIST / 'Kommunekonomi.mo')
    shutil.copy2(ROOT / 'modelica/Motala.mo', DIST / 'Motala.mo')
    shutil.copy2(ROOT / 'modelica/MotalaBrowser.mo', DIST / 'MotalaBrowser.mo')
    shutil.copytree(OMC, DIST / 'omc-web')
    shutil.copy2(ROOT / 'docs/methodology.md', DIST / 'methodology.md')
    shutil.copy2(ROOT / 'LICENSE', DIST / 'LICENSE.txt')
    planning = json.loads((ROOT / 'data/planning-inputs.json').read_text())
    for document in planning['documents']:
        shutil.copy2(ROOT / planning['sources']['archive'] / document['file'], DIST / document['file'])
    (DIST / '.nojekyll').write_text('')
    print('Static site ready in', DIST, '· OpenModelica', manifest['revision'])


if __name__ == '__main__':
    main()
