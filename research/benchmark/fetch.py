"""Archive a public SKR comparison workbook, without modifying model inputs.

Usage: python3 research/benchmark/fetch.py --circular 26:28
The source index and inspection status are separate from download receipts.
A successful download is not a validated extraction of Motala's forecasts.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen
import zipfile


HERE = Path(__file__).resolve().parent


def validate_workbook(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if not {"[Content_Types].xml", "xl/workbook.xml"} <= set(archive.namelist()):
            raise ValueError("Response is not an Excel workbook")
        if archive.testzip() is not None:
            raise ValueError("Corrupt workbook archive")


def fetch(entry):
    receipt = {"circular": entry["circular"], "url": entry["url"],
               "publishedAt": entry["publishedAt"],
               "attemptedAt": datetime.now(timezone.utc).isoformat(),
               "role": "external_benchmark_only", "extractionStatus": "not_extracted"}
    try:
        with urlopen(entry["url"], timeout=30) as response:
            payload = response.read(20_000_001)
            receipt["resolvedUrl"] = response.url
        if len(payload) > 20_000_000:
            raise ValueError("Workbook exceeds 20 MB download limit")
        validate_workbook(payload)
        digest = hashlib.sha256(payload).hexdigest()
        directory = HERE / "raw"
        directory.mkdir(exist_ok=True)
        destination = directory / f"{entry['publishedAt']}-{digest}.xlsm"
        destination.write_bytes(payload)
        receipt.update(status="downloaded", sha256=digest, bytes=len(payload),
                       path=str(destination.relative_to(HERE)))
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        receipt.update(status="download_failed", error=str(exc))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--circular", default="26:28")
    args = parser.parse_args()
    sources = json.loads((HERE / "sources.json").read_text())
    entries = [e for e in sources["workbooks"] if e["circular"] == args.circular]
    if not entries:
        parser.error("Circular is not in the verified source index")
    receipt = fetch(entries[0])
    text = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
    directory = HERE / "receipts"
    directory.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    (directory / f"{args.circular.replace(':', '-')}-{stamp}.json").write_text(text)
    print(text, end="")
    raise SystemExit(0 if receipt["status"] == "downloaded" else 1)
