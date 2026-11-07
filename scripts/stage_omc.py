"""Stage OpenModelica's in-browser compiler (wasm-jit) for the web app.

    python3 scripts/stage_omc.py /path/to/build-web/install_cmake/share/omc/web

Copies the omc module, its wasm side modules and OpenModelica's licence into
site/omc-web/ and writes manifest.json with hashes and the compiler revision.
site/omc-web/ is not versioned: the wasm is ~100 MB. Build OpenModelica with
-DOM_OMC_WASM=ON -DRUST_OMC_WASM_MODE=web-release (see README).
"""
import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'site/omc-web'
FILES = ['omc/OpenModelicaCompiler.js', 'omc/OpenModelicaCompiler_bg.wasm']


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('bundle', type=Path, help='share/omc/web of an OpenModelica web build')
    args = parser.parse_args()
    web = args.bundle.resolve()
    for name in FILES:
        if not (web / name).is_file():
            raise SystemExit(f'{web / name} missing; is this share/omc/web of an OM_OMC_WASM build?')
    if not (web / 'wasm-blobs').is_dir():
        raise SystemExit(f'{web / "wasm-blobs"} missing')
    install = web.parents[2]  # .../install_cmake
    licence = install / 'share/doc/openmodelica/copyright'
    if not licence.is_file():
        raise SystemExit(f'{licence} missing; the licence must ship with the compiler')
    revision_file = install.parent / 'OMCompiler/Compiler/omc-revision.txt'
    revision = revision_file.read_text().strip() if revision_file.is_file() else 'unknown'

    if TARGET.exists():
        shutil.rmtree(TARGET)
    (TARGET / 'omc').mkdir(parents=True)
    for name in FILES:
        shutil.copy2(web / name, TARGET / name)
    shutil.copytree(web / 'wasm-blobs', TARGET / 'wasm-blobs')
    shutil.copy2(licence, TARGET / 'LICENSE-OpenModelica.txt')

    staged = sorted(p for p in TARGET.rglob('*') if p.is_file())
    manifest = {
        'compiler': 'OpenModelica omc, web-release (wasm-jit)',
        'revision': revision,
        'commit': (re.search(r'\+g([0-9a-f]+)', revision) or [None, None])[1],
        'source': 'https://github.com/OpenModelica/OpenModelica',
        'licence': 'OSMC-PL 1.8 or GNU AGPL 3, see LICENSE-OpenModelica.txt',
        'stagedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'files': {str(p.relative_to(TARGET)): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in staged},
    }
    (TARGET / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    size = sum(p.stat().st_size for p in staged)
    print(f'Staged {len(staged)} files ({size / 1048576:.0f} MiB) from {revision} into {TARGET}')


if __name__ == '__main__':
    main()
