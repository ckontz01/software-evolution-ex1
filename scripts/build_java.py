#!/usr/bin/env python3
"""Compile the extractor and the unmodified official ACDC sources."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from evolution.toolchain import build_java

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", help="Java 17+ executable; optional when java is on PATH")
    args = parser.parse_args()
    print(json.dumps(build_java(args.java), indent=2))
