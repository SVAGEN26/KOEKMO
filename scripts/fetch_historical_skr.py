#!/usr/bin/env python3
"""Recover the identified SKR originals from Internet Archive without running macros."""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'data/skr-historical'


def verify(data, entry):
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ValueError(f"SHA-256 mismatch: {entry['file']}")
    digest = base64.b32encode(hashlib.sha1(data).digest()).decode()
    if digest != entry['archiveSha1Base32']:
        raise ValueError(f"Archive digest mismatch: {entry['file']}")
    if entry['file'].endswith('.xlsm'):
        with zipfile.ZipFile(io.BytesIO(data)) as workbook:
            if 'xl/workbook.xml' not in workbook.namelist():
                raise ValueError('Missing workbook.xml')
    elif not data.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise ValueError('Not an OLE Excel workbook')


def main():
    manifest = json.loads((DIRECTORY / 'manifest.json').read_text())
    originals = DIRECTORY / 'originals'
    originals.mkdir(exist_ok=True)
    for entry in manifest['files']:
        target = originals / entry['file']
        if target.exists():
            verify(target.read_bytes(), entry)
            print('Verified existing:', target.name)
            continue
        request = urllib.request.Request(entry['archiveUrl'], headers={
            'User-Agent': 'Motala-economic-research/1.0', 'Accept-Encoding': 'identity'})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
        if data.startswith(b'\x1f\x8b'):
            data = gzip.decompress(data)
        verify(data, entry)
        target.write_bytes(data)
        print('Recovered:', target.name)


if __name__ == '__main__':
    main()
