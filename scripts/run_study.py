#!/usr/bin/env python3
"""Reproduce Guava extraction, the pilot, and all 120 finalized architectures."""
from pathlib import Path
import argparse
import os
import sys

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from evolution.study import ROOT, analyse_all, extract_all, pilot
from evolution.toolchain import build_java

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["all", "extract", "pilot", "analyse"], default="all")
    parser.add_argument("--java")
    parser.add_argument("--graph-root", type=Path, default=ROOT / "data/graphs")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    if args.phase in ("all", "extract"):
        extract_all(args.graph_root, java=args.java)
    else:
        build_java(args.java)
    if args.phase in ("all", "pilot"):
        pilot(args.graph_root, args.output / "pilot", java=args.java)
    if args.phase in ("all", "analyse"):
        analyse_all(args.graph_root, args.output, java=args.java)
