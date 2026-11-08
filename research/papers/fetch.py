"""Download the catalogued original PDFs; record failures without fake PDFs.

Run from the project root: python3 scripts/download_research.py
Only Python's standard library is needed. Existing files are never overwritten.
Header and EOF checks reject common HTML error pages, but do not establish that
a PDF is complete, authentic or the correct paper. Inspect downloaded documents.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from http.client import HTTPException
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


DIRECTORY = Path(__file__).resolve().parent
MAX_BYTES = 30_000_000
SUCCESS = {"downloaded", "existing_file_preserved"}


def check_pdf(payload):
    if not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-4096:]:
        raise ValueError("Response lacks a PDF header/end marker; not saved")


def download(url, timeout, retries, receipt):
    request = Request(url, headers={
        "User-Agent": "MotalaResearch-paper-archive/1.0",
        "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.1",
    })
    for attempt in range(retries + 1):
        receipt["attempts"] = attempt + 1
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = response.read(MAX_BYTES + 1)
                receipt["resolvedUrl"] = response.url
                receipt["contentType"] = response.headers.get("Content-Type")
                length = response.headers.get("Content-Length")
            if len(payload) > MAX_BYTES:
                raise ValueError("Response exceeds 30 MB; not saved")
            if length is not None and len(payload) != int(length):
                raise HTTPException("Incomplete response; Content-Length does not match")
            check_pdf(payload)
            return payload
        except (OSError, HTTPException) as exc:
            retryable = not isinstance(exc, HTTPError) or exc.code in (408, 429, 500, 502, 503, 504)
            if isinstance(exc, HTTPError):
                exc.close()
            if attempt == retries or not retryable:
                raise
            print(f"  Download failed: {exc}; retry {attempt + 1}/{retries}", flush=True)
            time.sleep(min(2 ** attempt, 8))


def save_pdf(target, payload):
    # Publish a complete file atomically without overwriting a concurrent download.
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix="." + target.name,
                                     suffix=".part", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            os.link(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)


def fetch(directory=DIRECTORY, *, sources=None, timeout=30, retries=2):
    directory = Path(directory)
    if not math.isfinite(timeout) or timeout <= 0 or retries < 0:
        raise ValueError("Timeout must be positive and finite; retries must be nonnegative")
    if sources is None:
        sources = json.loads((DIRECTORY / "sources.json").read_text(encoding="utf-8"))["sources"]
    directory.mkdir(parents=True, exist_ok=True)
    receipts = []
    for source in sources:
        receipt = {"id": source["id"], "filename": source["filename"],
                   "title": source["title"], "landingUrl": source["url"],
                   "url": source["pdfUrl"],
                   "attemptedAt": datetime.now(timezone.utc).isoformat()}
        print(f"{source['id']}: {source['title']}", flush=True)
        try:
            name = source["filename"]
            if Path(name).name != name or "\\" in name or not name.endswith(".pdf"):
                raise ValueError("Expected a plain PDF filename")
            target = directory / name
            if target.exists():
                if target.stat().st_size > MAX_BYTES:
                    raise ValueError("Existing file exceeds 30 MB; preserved for manual review")
                payload = target.read_bytes()
                check_pdf(payload)
                receipt["status"] = "existing_file_preserved"
            elif not source["pdfUrl"]:
                receipt["status"] = "manual_download_needed"
                receipts.append(receipt)
                print(f"  Manual download needed: {source['url']}\n  Save as: {target}", flush=True)
                continue
            else:
                payload = download(source["pdfUrl"], timeout, retries, receipt)
                save_pdf(target, payload)
                receipt["status"] = "downloaded"
            receipt.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(),
                           validation="PDF header and end marker only; content review pending")
        except (OSError, ValueError, HTTPException) as exc:
            receipt.update(status="failed", error=str(exc))
        receipts.append(receipt)
        print(f"  {receipt['status']}" + (f": {receipt['error']}" if "error" in receipt else ""), flush=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    receipt_path = directory / f"download-receipts-{stamp}.json"
    receipt_path.write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ready = sum(r["status"] in SUCCESS for r in receipts)
    print(f"\n{ready}/{len(receipts)} papers available in {directory.resolve()}")
    print(f"Receipts: {receipt_path}")
    return receipts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DIRECTORY,
                        help="PDF and receipt directory (default: research/papers)")
    parser.add_argument("--list", action="store_true", help="List papers without downloading or writing files")
    parser.add_argument("--only", action="append", metavar="ID", help="Download one paper ID; repeat to select several")
    parser.add_argument("--timeout", type=float, default=30, help="Network timeout in seconds (default: 30)")
    parser.add_argument("--retries", type=int, default=2, help="Extra attempts for transient network failures (default: 2)")
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0 or args.retries < 0:
        parser.error("--timeout must be positive and finite; --retries must be nonnegative")
    sources = json.loads((DIRECTORY / "sources.json").read_text(encoding="utf-8"))["sources"]
    if args.only:
        unknown = set(args.only) - {s["id"] for s in sources}
        if unknown:
            parser.error("Unknown paper ID(s): " + ", ".join(sorted(unknown)) + "; use --list")
        sources = [s for s in sources if s["id"] in args.only]
    if args.list:
        for source in sources:
            print(f"{source['id']}: {source['title']}")
            print(f"  {source['pdfUrl'] or source['url']}")
            print(f"  {source['filename']}" + (" (manual download needed)" if not source["pdfUrl"] else ""))
        return 0
    try:
        results = fetch(args.output, sources=sources, timeout=args.timeout, retries=args.retries)
    except OSError as exc:
        print(f"Cannot write download files or receipts: {exc}", file=sys.stderr)
        return 1
    return 0 if all(r["status"] in SUCCESS for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
