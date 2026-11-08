import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("paper_fetch", ROOT / "research/papers/fetch.py")
fetch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch)
PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
SOURCE = {"id": "example", "title": "Example paper", "filename": "example.pdf",
          "url": "https://example.invalid/paper", "pdfUrl": "https://example.invalid/paper.pdf"}


def response(payload=PDF, length=None):
    result = io.BytesIO(payload)
    result.url = SOURCE["pdfUrl"]
    result.headers = {"Content-Type": "application/pdf",
                      "Content-Length": str(len(payload) if length is None else length)}
    return result


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))

    def test_success_records_provenance_and_rerun_preserves_file(self):
        destination = self.directory / "new-folder"
        with patch.object(fetch, "urlopen", return_value=response()) as network:
            first = fetch.fetch(destination, sources=[SOURCE])[0]
            second = fetch.fetch(destination, sources=[SOURCE])[0]
        self.assertEqual(network.call_count, 1)
        self.assertEqual(first["status"], "downloaded")
        self.assertEqual(second["status"], "existing_file_preserved")
        self.assertEqual(first["sha256"], hashlib.sha256(PDF).hexdigest())
        self.assertEqual(first["resolvedUrl"], SOURCE["pdfUrl"])
        self.assertEqual((destination / SOURCE["filename"]).read_bytes(), PDF)
        receipts = list(destination.glob("download-receipts-*.json"))
        self.assertEqual(len(receipts), 2)
        self.assertTrue(all(json.loads(p.read_text())[0]["sha256"] == first["sha256"] for p in receipts))

    def test_html_truncation_and_size_limit_never_publish_a_pdf(self):
        cases = [(b"<html>Access denied</html>", None, 1000),
                 (PDF, len(PDF) + 10, 1000), (PDF, None, 20)]
        for payload, length, limit in cases:
            with self.subTest(length=length, limit=limit), \
                    patch.object(fetch, "MAX_BYTES", limit), \
                    patch.object(fetch, "urlopen", return_value=response(payload, length)):
                receipt = fetch.fetch(self.directory, sources=[SOURCE], retries=0)[0]
            self.assertEqual(receipt["status"], "failed")
            self.assertNotIn("sha256", receipt)
            self.assertFalse(list(self.directory.glob("*.pdf")))
            self.assertFalse(list(self.directory.glob("*.part")))

    def test_transient_failure_retries_then_succeeds(self):
        with patch.object(fetch, "urlopen", side_effect=[URLError("DNS failed"), response()]) as network, \
                patch.object(fetch.time, "sleep"):
            receipt = fetch.fetch(self.directory, sources=[SOURCE], retries=1)[0]
        self.assertEqual(receipt["status"], "downloaded")
        self.assertEqual(receipt["attempts"], 2)
        self.assertEqual(network.call_count, 2)

    def test_permanent_http_failure_does_not_retry_or_stop_other_papers(self):
        other = {**SOURCE, "id": "other", "filename": "other.pdf"}
        error = HTTPError(SOURCE["pdfUrl"], 403, "Forbidden", {}, None)
        with patch.object(fetch, "urlopen", side_effect=[error, response()]) as network:
            receipts = fetch.fetch(self.directory, sources=[SOURCE, other])
        self.assertEqual(network.call_count, 2)
        self.assertEqual([r["status"] for r in receipts], ["failed", "downloaded"])

    def test_invalid_existing_file_is_preserved_for_review(self):
        target = self.directory / SOURCE["filename"]
        target.write_bytes(b"an existing file")
        with patch.object(fetch, "urlopen") as network:
            receipt = fetch.fetch(self.directory, sources=[SOURCE])[0]
        network.assert_not_called()
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(target.read_bytes(), b"an existing file")

    def test_manual_download_has_nonzero_exit_and_actionable_receipt(self):
        with patch.object(fetch, "urlopen") as network:
            status = fetch.main(["--only", "nilsson-2020", "--output", str(self.directory)])
        network.assert_not_called()
        self.assertEqual(status, 1)
        receipt = json.loads(next(self.directory.glob("download-receipts-*.json")).read_text())[0]
        self.assertEqual(receipt["status"], "manual_download_needed")
        self.assertIn("9033365", receipt["landingUrl"])
        self.assertNotIn("sha256", receipt)

    def test_atomic_publish_preserves_a_file_added_during_download(self):
        target = self.directory / "paper.pdf"
        target.write_bytes(b"another download")
        with self.assertRaises(FileExistsError):
            fetch.save_pdf(target, PDF)
        self.assertEqual(target.read_bytes(), b"another download")
        self.assertEqual(list(self.directory.iterdir()), [target])

    def test_disk_failure_does_not_leave_partial_papers(self):
        with patch.object(fetch.os, "fsync", side_effect=OSError("Disk full")), \
                self.assertRaises(OSError):
            fetch.save_pdf(self.directory / "paper.pdf", PDF)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_entry_point_lists_from_another_directory_without_writes(self):
        process = subprocess.run([sys.executable, str(ROOT / "scripts/download_research.py"),
                                  "--list", "--only", "cellier-2008"],
                                 cwd=self.directory, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("World3 in Modelica", process.stdout)
        self.assertNotIn("calgary", process.stdout)
        self.assertEqual(list(self.directory.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
