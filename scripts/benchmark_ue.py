#!/usr/bin/env python3
"""Benchmark JNode-UE on a deterministic graph with analytically known scores."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import platform
import resource
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from evolution.omnipresent import detect_omnipresent


def run_benchmark(sizes: list[int], degree: int = 20, repeats: int = 3) -> dict:
    if not sizes or degree < 1 or repeats < 1 or any(n <= degree for n in sizes):
        raise ValueError("sizes must exceed the positive degree; repeats must be positive")
    cases = []
    for count in sizes:
        classes = [f"C{i:05d}" for i in range(count)]
        owners = {f"{c}#run()V": c for c in classes}
        owners.update({f"{c}#accept()V": c for c in classes})
        edges = [
            (f"{classes[i]}#run()V", f"{classes[(i + j) % count]}#accept()V")
            for i in range(count) for j in range(1, degree + 1)
        ]
        expected_equality = 1 - 1 / degree
        expected_removed = count if degree >= 10 else 0
        durations = []
        for _ in range(repeats):
            gc.collect()
            start = time.perf_counter()
            result = detect_omnipresent(classes, edges, member_owners=owners)
            durations.append(time.perf_counter() - start)
            # Assertions execute outside the timed region.  Every answer follows
            # from the regular ring construction, independently of the detector.
            assert result.stats.unique_member_edges == count * degree
            assert result.stats.class_pairs == count * degree
            assert result.stats.duplicate_member_edges == 0
            assert len(result.removed_classes) == expected_removed
            assert all(
                score.fanin == degree
                and score.referenced_members == 1
                and abs(score.max_dedication - 1 / degree) < 1e-14
                and abs(score.usage_equality - expected_equality) < 1e-14
                and abs(score.cardinality - expected_equality) < 1e-14
                for score in result.scores
            )
        peak_native = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_mib = peak_native / (1024 * 1024 if sys.platform == "darwin" else 1024)
        cases.append({
            "classes": count,
            "distinct_member_references": len(edges),
            "class_pairs": result.stats.class_pairs,
            "runs_seconds": durations,
            "median_seconds": statistics.median(durations),
            "process_high_water_rss_mib": peak_mib,
            "expected_fanin": degree,
            "expected_referenced_members_per_target": 1,
            "expected_max_dedication": 1 / degree,
            "expected_usage_equality": expected_equality,
            "expected_cardinality": expected_equality,
            "expected_removed_classes": expected_removed,
            "observed_removed_classes": len(result.removed_classes),
            "all_expected_outputs_checked": True,
        })
        del result, classes, owners, edges

    return {
        "schema_version": 1,
        "algorithm": "JNode-UE (Yano and Matsuo, 2020)",
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "construction": {
            "name": "directed indexed ring with fixed outgoing offsets",
            "edge_rule": "C_i#run()V -> C_((i+j) mod N)#accept()V, j=1..degree",
            "degree": degree,
            "randomness": "none",
            "thresholds": {"usage_equality": 0.85, "cardinality": 0.90},
        },
        "measurement_protocol": {
            "repeats": repeats,
            "summary": "median",
            "timed_region": "detect_omnipresent only, including input validation, diagnostics and output ordering",
            "excluded_from_timing": ["input creation", "garbage collection", "expected-output checks"],
            "memory": "process high-water RSS, cumulative across cases, including input and result objects",
            "previous_result_retained_until_next_call_completes": True,
            "limitations": "synthetic scaling evidence; excludes downloads, extraction and clustering; environment-dependent timing",
        },
        "code_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT / "src/evolution/omnipresent.py", Path(__file__).resolve())
        },
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", default="1000,5000,10000", help="comma-separated class counts")
    parser.add_argument("--degree", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "results/performance/ue_benchmark.json")
    args = parser.parse_args()
    data = run_benchmark([int(value) for value in args.sizes.split(",")], args.degree, args.repeats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    for case in data["cases"]:
        print(f"{case['classes']} classes / {case['distinct_member_references']} references: "
              f"{case['median_seconds']:.6f} s; expected outputs verified")
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
