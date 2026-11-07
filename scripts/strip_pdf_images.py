"""Remove the images from the archived PDFs and update the archive manifest.

    python3 scripts/strip_pdf_images.py data/downloads/20261106T090534Z

Photos and other third-party images in municipal documents can carry rights of
their own, so the archive keeps only text and vector content. Each image becomes a
blank one, labelled "Bild borttagen" where it was visible (scripts/strip_pdf_images.js,
needs mutool). The manifest keeps the downloaded file's bytes and SHA-256 as
originalBytes/originalSha256 and records the stripped file's as bytes/sha256, so
prepare_planning_inputs.py still verifies every file. Already stripped files are skipped.
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    manifest_file = args.archive / 'manifest.json'
    manifest = json.loads(manifest_file.read_text())
    for item in manifest['files']:
        if not item['file'].endswith('.pdf') or item.get('imagesRemoved'):
            continue
        path = args.archive / item['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise SystemExit(f'{path} does not match the manifest; refusing to strip an unknown file')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'stripped.pdf'
            result = subprocess.run(['mutool', 'run', str(ROOT / 'scripts/strip_pdf_images.js'), str(path), str(out)],
                                    check=True, capture_output=True, text=True)
            count = int(result.stdout.strip().splitlines()[-1])
            data = out.read_bytes()
        path.write_bytes(data)
        item.update(originalBytes=item['bytes'], originalSha256=item['sha256'], bytes=len(data),
                    sha256=hashlib.sha256(data).hexdigest(), imagesRemoved=True, imagesReplaced=count)
        print(f'{item["file"]}: {count} images replaced, {item["originalBytes"]} -> {len(data)} bytes')
    notes = manifest.setdefault('notes', [])
    note = ('PDF images are removed (scripts/strip_pdf_images.py): photos and other images can carry '
            'third-party rights. originalSha256 identifies the downloaded file; the source URL has the original.')
    if isinstance(notes, list) and note not in notes:
        notes.append(note)
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
