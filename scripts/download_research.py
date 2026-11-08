#!/usr/bin/env python3
"""Download the project's research papers; run with --help for options."""
from pathlib import Path
import runpy
import sys


if __name__ == "__main__":
    downloader = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "research/papers/fetch.py"),
    )
    sys.exit(downloader["main"]())
