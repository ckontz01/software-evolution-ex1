# Commit 02 — Usage Equality detector and exact tests

**Student B · 2026-10-18 · 6 complete files · 4 full code/configuration listings**

Source snapshot: `f32e6e831f976eed8bf01faa1d66dbdc34bc49c7`. Dates are planned work sessions; make the commit when you actually import and review this packet.

## What to understand

Work through one dedication/equality example, the two inclusive thresholds, original member identities and the no-member-evidence case.

## Apply this packet

Set `HANDOFF_DIR` to your extracted student bundle and `TEACHER_REPO` to the teacher checkout. Pull the preceding commit first. Commands below use the `guava-study` layout explained in the main map.

```bash
git -C "$TEACHER_REPO" pull --ff-only origin guava-assignment
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/02-b-usage-equality" --target "$TEACHER_REPO" --subdir guava-study
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/02-b-usage-equality" --target "$TEACHER_REPO" --subdir guava-study --apply
cd "$TEACHER_REPO/guava-study"
```

For commit 01, create the shared branch as shown in the main map; its remote branch does not exist until the first push, so omit that first pull.

## Checks before the commit

Run these in the cumulative study directory after applying the packet. For packet 01, first create the Python environment and install the locked requirements as shown in the main map:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_omnipresent.py' -v
```

Stage and inspect only this packet, then use your own Git identity:

```bash
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/02-b-usage-equality" --target "$TEACHER_REPO" --subdir guava-study --apply --stage
git -C "$TEACHER_REPO" diff --cached --stat
git -C "$TEACHER_REPO" diff --cached
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/02-b-usage-equality" --target "$TEACHER_REPO" --subdir guava-study --check-staged
git -C "$TEACHER_REPO" commit -m 'import: add paper-based Usage Equality detector and exact tests (AI-assisted preparation)'
git -C "$TEACHER_REPO" push -u origin guava-assignment
```

Add a commit-message paragraph describing the checks you actually performed and anything you found. The import message identifies the prepared source; it does not claim you originally wrote every line.

## Further review checks

The following are useful for learning or final verification. Commands marked as writing evidence belong in a disposable copy, so the next packet still matches the frozen source. These are not additional canonical experiments.

Optionally measure the detector on known-answer synthetic inputs.

```bash
python scripts/benchmark_ue.py --sizes 1000,5000,10000 --repeats 3 --output results/rerun/handoff-p02-benchmark.json
```

**Where:** cumulative packet checkout. **Writes:** new ignored results/rerun file; original benchmark unchanged.

## Every file to push

All files below are present under this packet's `payload/` directory in the complete student download. Paths are relative to the study directory.

| File | Bytes | Content |
|---|---:|---|
| `docs/omnipresent.md` | 16,545 | documentation or tool provenance |
| `results/performance/ue_benchmark.json` | 3,269 | recorded evidence |
| `scripts/benchmark_ue.py` | 5,641 | Full code below |
| `scripts/jnode_ue.py` | 2,151 | Full code below |
| `src/evolution/omnipresent.py` | 12,279 | Full code below |
| `tests/test_omnipresent.py` | 11,240 | Full code below |

The machine-readable `packet.json` pins every file's SHA-256 and Git blob. Binary JAR/PDF/ZIP files and large evidence files are supplied as their exact original bytes in the payload, rather than as text pasted into this guide.

## Whole code

The following are complete files, with no omitted functions. Use the payload for copying so file bytes, line endings and original licences stay intact.

### scripts/benchmark_ue.py

SHA-256: `671c93da02ef2aa3eba839a33201b9bd82c751d9dee6b35ef95fd3e21bd490d3` · 5,641 bytes

<!-- FULL_SOURCE scripts/benchmark_ue.py 671c93da02ef2aa3eba839a33201b9bd82c751d9dee6b35ef95fd3e21bd490d3 -->
```python
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
```
<!-- END_FULL_SOURCE scripts/benchmark_ue.py -->

### scripts/jnode_ue.py

SHA-256: `a02f2b189538cfea37aad37062aa3c78e3a042cfe8f7020f9e2e774341e185a4` · 2,151 bytes

<!-- FULL_SOURCE scripts/jnode_ue.py a02f2b189538cfea37aad37062aa3c78e3a042cfe8f7020f9e2e774341e185a4 -->
```python
#!/usr/bin/env python3
"""Run the paper-based JNode-UE replacement as a standalone explainable tool."""
import argparse
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evolution.graph import read_csv, write_csv, write_json
from evolution.omnipresent import detect_omnipresent

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classes', type=Path, required=True, help='Extractor classes.csv, with class column')
    parser.add_argument('--members', type=Path, required=True, help='Extractor member_dependencies.csv')
    parser.add_argument('--output', type=Path, required=True, help='New output directory')
    parser.add_argument('--usage-threshold', type=float, default=.85)
    parser.add_argument('--cardinality-threshold', type=float, default=.90)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output directory to preserve any previous run')
    classes = [r['class'] for r in read_csv(args.classes)]
    rows = read_csv(args.members)
    started = time.perf_counter()
    result = detect_omnipresent(classes, rows, usage_threshold=args.usage_threshold,
                                cardinality_threshold=args.cardinality_threshold)
    seconds = time.perf_counter() - started
    args.output.mkdir(parents=True)
    write_json(args.output / 'ue.json', result.to_dict(include_dedications=True))
    write_csv(args.output / 'omnipresent.csv', [r.to_dict() for r in result.scores])
    write_csv(args.output / 'removed_classes.csv', [{'class': n} for n in result.removed_classes], ['class'])
    write_json(args.output / 'run.json', {'method': 'Yano and Matsuo2020 UE; not historical ComponentRank JNode',
                'classes_file': str(args.classes), 'members_file': str(args.members),
                'detector_seconds_excluding_csv_io': seconds, 'classes': len(classes),
                'removed': len(result.removed_classes)})
    print(f'JNode-UE: {len(result.removed_classes)} of {len(classes)} classes; {seconds:.6f}s detector-only')
```
<!-- END_FULL_SOURCE scripts/jnode_ue.py -->

### src/evolution/omnipresent.py

SHA-256: `b8dea8f90a2c7c48757e87ac388c43ff97bc228450f99836a12c473dc107ac17` · 12,279 bytes

<!-- FULL_SOURCE src/evolution/omnipresent.py b8dea8f90a2c7c48757e87ac388c43ff97bc228450f99836a12c473dc107ac17 -->
```python
"""JNode-UE: member-aware omnipresent detection from Yano and Matsuo (2020).

This is the usage-equality (UE) method in equations 1--3, printed page 663,
of ``Moderate Detection and Removal of Omnipresent Modules in Software
Clustering``.  It is a replacement for, not an implementation of, the earlier
ComponentRank/shortest-path JNode algorithm compared with UE in that paper.

The input owners must already be canonical, outermost project classes.  Member
identifiers must retain their original declaring class, kind, and descriptor:
merging class owners must not merge distinct methods with the same signature.
Only distinct method/field member dependencies supply evidence for UE.  Other
class relations (such as inheritance) do not become fabricated member edges.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from fractions import Fraction
from math import fsum, isfinite, ulp
from typing import TypeAlias


MemberEdge: TypeAlias = tuple[str, str] | Mapping[str, str]


@dataclass(frozen=True, slots=True)
class UEClassScore:
    """The complete decision for one normalized project class."""

    class_name: str
    fanin: int
    referenced_members: int
    max_dedication: float | None
    usage_equality: float | None
    cardinality: float | None
    strongest_caller: str | None
    usage_equality_passed: bool
    cardinality_passed: bool
    omnipresent: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class UEDedication:
    """Equation 1 for a distinct pair of owner classes."""

    source_class: str
    target_class: str
    referenced_members: int
    dedication: float


@dataclass(frozen=True, slots=True)
class UEStats:
    """Counts reconciling input rows with the scoped, deduplicated evidence."""

    classes: int
    input_member_edges: int
    excluded_external_edges: int
    excluded_intraclass_edges: int
    duplicate_member_edges: int
    unique_member_edges: int
    referenced_target_members: int
    class_pairs: int


@dataclass(frozen=True, slots=True)
class UEResult:
    usage_threshold: float
    cardinality_threshold: float
    scores: tuple[UEClassScore, ...]
    dedications: tuple[UEDedication, ...]
    stats: UEStats

    @property
    def removed_classes(self) -> tuple[str, ...]:
        return tuple(score.class_name for score in self.scores if score.omnipresent)

    @property
    def retained_classes(self) -> tuple[str, ...]:
        return tuple(score.class_name for score in self.scores if not score.omnipresent)

    def by_class(self) -> dict[str, UEClassScore]:
        return {score.class_name: score for score in self.scores}

    def to_dict(self, *, include_dedications: bool = False) -> dict:
        """Return JSON-safe, deterministically ordered evidence.

        Per-class decisions always appear.  The optional pair table is useful
        when explaining an individual decision but can make release JSON large.
        """
        result = {
            "algorithm": "JNode-UE (Yano and Matsuo, 2020)",
            "scope": "resolved project member-use graph; normalized outermost owners",
            "usage_threshold": self.usage_threshold,
            "cardinality_threshold": self.cardinality_threshold,
            "removed_classes": list(self.removed_classes),
            "scores": [score.to_dict() for score in self.scores],
            "stats": asdict(self.stats),
        }
        if include_dedications:
            result["dedications"] = [asdict(pair) for pair in self.dedications]
        return result


def _threshold(value: float, name: str) -> tuple[float, Fraction]:
    numeric = float(value)
    if not isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise ValueError(f"{name} must be finite and between 0 and 1 inclusive")
    # Treat the textual decimal threshold as the intended value.  In particular,
    # ceil(1 / (1 - 0.9)) with binary floats would incorrectly require 11 callers.
    return numeric, Fraction(str(value))


def _at_most_exact_boundary(
    value: float, denominators: list[int], cutoff: Fraction
) -> bool:
    """Compare a reciprocal sum without changing an inclusive boundary.

    Fast floating-point evaluation suffices away from the cutoff.  Only at a
    binary-rounding boundary do we sum exact rational values.  This is not an
    epsilon that changes the paper's decision rule.
    """
    limit = float(cutoff)
    rounding_margin = 8 * max(ulp(value), ulp(limit))
    if value < limit - rounding_margin:
        return True
    if value > limit + rounding_margin:
        return False
    return sum((Fraction(1, denominator) for denominator in denominators), Fraction()) <= cutoff


def detect_omnipresent(
    classes: Iterable[str],
    member_edges: Iterable[MemberEdge],
    *,
    member_owners: Mapping[str, str] | None = None,
    usage_threshold: float = 0.85,
    cardinality_threshold: float = 0.90,
) -> UEResult:
    """Detect all omnipresent classes once on the original scoped graph.

    ``member_edges`` accepts either dictionaries with ``source_class``,
    ``source_member``, ``target_class``, ``target_member``, or two-tuples of
    globally unique member IDs.  The tuple form requires ``member_owners``.
    Owners are normalized project class names.  A missing tuple owner is an
    input error; an explicitly out-of-scope owner is filtered as external.

    Exact member pairs and class-to-target-member pairs are deduplicated
    separately.  Two different methods of A calling the same B method increase
    that method's xm_fanin twice but contribute it only once to D_M(A, B).

    Hash aggregation is linear in the number of distinct member references,
    class pairs, and classes.  Deterministic output sorting additionally costs
    O(C log C + N log N), for C class pairs and N classes.  No dense graph,
    shortest-path enumeration, iteration, or post-removal recomputation occurs.
    """
    usage_float, usage_fraction = _threshold(usage_threshold, "usage_threshold")
    cardinality_float, cardinality_fraction = _threshold(
        cardinality_threshold, "cardinality_threshold"
    )
    class_set = set(classes)
    if any(not isinstance(name, str) or not name for name in class_set):
        raise ValueError("classes must contain nonempty class names")

    owners: dict[str, str] = {}
    source_members_by_target: dict[str, set[str]] = defaultdict(set)
    caller_classes_by_target: dict[str, set[str]] = defaultdict(set)
    target_members_by_class: dict[str, set[str]] = defaultdict(set)
    input_count = excluded_external = excluded_intraclass = duplicate_count = 0

    for edge in member_edges:
        input_count += 1
        if isinstance(edge, Mapping):
            try:
                source = edge["source_member"]
                target = edge["target_member"]
                source_class = edge["source_class"]
                target_class = edge["target_class"]
            except KeyError as exc:
                raise ValueError(f"member edge is missing {exc.args[0]!r}") from exc
        else:
            if member_owners is None:
                raise ValueError("tuple member edges require a member_owners mapping")
            if isinstance(edge, (str, bytes)) or len(edge) != 2:
                raise ValueError("member edges must be pairs of member identifiers")
            source, target = edge
            try:
                source_class = member_owners[source]
                target_class = member_owners[target]
            except KeyError as exc:
                raise ValueError(f"owner missing for member {exc.args[0]!r}") from exc

        if any(not isinstance(item, str) or not item for item in (source, target, source_class, target_class)):
            raise ValueError("member IDs and owner class names must be nonempty strings")
        if source_class not in class_set or target_class not in class_set:
            excluded_external += 1
            continue
        if source_class == target_class:
            excluded_intraclass += 1
            continue

        for member, owner in ((source, source_class), (target, target_class)):
            previous = owners.setdefault(member, owner)
            if previous != owner:
                raise ValueError(
                    f"member ID {member!r} has conflicting owners {previous!r} and {owner!r}; "
                    "use globally unique member identifiers"
                )

        callers = source_members_by_target[target]
        if source in callers:
            duplicate_count += 1
            continue
        callers.add(source)
        caller_classes_by_target[target].add(source_class)
        target_members_by_class[target_class].add(target)

    # Each target member contributes once for each distinct CALLER CLASS;
    # the denominator still counts all distinct caller MEMBERS outside B.
    pair_denominators: dict[tuple[str, str], list[int]] = defaultdict(list)
    callers_by_class: dict[str, set[str]] = defaultdict(set)
    for target, caller_members in source_members_by_target.items():
        target_class = owners[target]
        denominator = len(caller_members) * len(target_members_by_class[target_class])
        for caller_class in caller_classes_by_target[target]:
            pair_denominators[caller_class, target_class].append(denominator)
            callers_by_class[target_class].add(caller_class)

    maximum: dict[str, float] = {}
    strongest: dict[str, str] = {}
    equality_passed: dict[str, bool] = defaultdict(lambda: True)
    dedication_rows: list[UEDedication] = []
    for (source_class, target_class), denominators in sorted(pair_denominators.items()):
        dedication = fsum(1 / denominator for denominator in denominators)
        dedication_rows.append(
            UEDedication(source_class, target_class, len(denominators), dedication)
        )
        if target_class not in maximum or dedication > maximum[target_class]:
            maximum[target_class] = dedication
            strongest[target_class] = source_class
        if not _at_most_exact_boundary(dedication, denominators, 1 - usage_fraction):
            equality_passed[target_class] = False

    score_rows: list[UEClassScore] = []
    for class_name in sorted(class_set):
        fanin = len(callers_by_class.get(class_name, ()))
        member_count = len(target_members_by_class.get(class_name, ()))
        if fanin == 0:
            # The paper leaves max(empty) and 1/0 undefined.  Keep the class;
            # no outside member-use evidence cannot establish omnipresence.
            score_rows.append(
                UEClassScore(class_name, 0, 0, None, None, None, None, False, False, False,
                             "no_external_member_use")
            )
            continue
        max_dedication = maximum[class_name]
        equality = 1.0 - max_dedication
        cardinality = 1.0 - 1.0 / fanin
        passes_e = equality_passed[class_name]
        passes_c = fanin * (1 - cardinality_fraction) >= 1
        is_omnipresent = passes_e and passes_c
        if not passes_e:
            reason = "usage_equality_below_threshold"
        elif not passes_c:
            reason = "cardinality_below_threshold"
        else:
            reason = "usage_equality_and_cardinality_at_or_above_thresholds"
        score_rows.append(
            UEClassScore(class_name, fanin, member_count, max_dedication, equality, cardinality,
                         strongest[class_name], passes_e, passes_c, is_omnipresent, reason)
        )

    return UEResult(
        usage_float,
        cardinality_float,
        tuple(score_rows),
        tuple(dedication_rows),
        UEStats(
            classes=len(class_set),
            input_member_edges=input_count,
            excluded_external_edges=excluded_external,
            excluded_intraclass_edges=excluded_intraclass,
            duplicate_member_edges=duplicate_count,
            unique_member_edges=sum(len(sources) for sources in source_members_by_target.values()),
            referenced_target_members=len(source_members_by_target),
            class_pairs=len(pair_denominators),
        ),
    )
```
<!-- END_FULL_SOURCE src/evolution/omnipresent.py -->

### tests/test_omnipresent.py

SHA-256: `170c1ffb84493da581981463be3e2d4828ac79e2a9fd5fbc2f02bad4e6bd2154` · 11,240 bytes

<!-- FULL_SOURCE tests/test_omnipresent.py 170c1ffb84493da581981463be3e2d4828ac79e2a9fd5fbc2f02bad4e6bd2154 -->
```python
"""Meaningful UE checks: paper equations, exact thresholds, and scope integrity."""

from fractions import Fraction
import json
import random
import unittest

from evolution.omnipresent import detect_omnipresent


def row(source_class, source_member, target_class, target_member):
    return {
        "source_class": source_class,
        "source_member": f"{source_class}#{source_member}",
        "target_class": target_class,
        "target_member": f"{target_class}#{target_member}",
    }


def exact_paper_oracle(classes, rows, usage=Fraction(17, 20), cardinality=Fraction(9, 10)):
    """Deliberately slow set definitions and Fraction arithmetic from Eq. 1--3.

    This independently expresses the mathematical sets instead of copying the
    optimized implementation's aggregation steps.
    """
    classes = set(classes)
    edges = {
        (r["source_class"], r["source_member"], r["target_class"], r["target_member"])
        for r in rows
        if r["source_class"] in classes
        and r["target_class"] in classes
        and r["source_class"] != r["target_class"]
    }
    result = {}
    for target_class in classes:
        incoming = {edge for edge in edges if edge[2] == target_class}
        callers = {edge[0] for edge in incoming}
        targets = {edge[3] for edge in incoming}
        if not callers:
            result[target_class] = (0, 0, None, None, None, False)
            continue
        dedication = {}
        for caller in callers:
            used = {edge[3] for edge in incoming if edge[0] == caller}
            dedication[caller] = sum(
                (
                    Fraction(1, len({edge[1] for edge in incoming if edge[3] == member}) * len(targets))
                    for member in used
                ),
                Fraction(),
            )
        maximum = max(dedication.values())
        equality = 1 - maximum
        c = 1 - Fraction(1, len(callers))
        result[target_class] = (
            len(callers), len(targets), maximum, equality, c,
            equality >= usage and c >= cardinality,
        )
    return result


class TestUsageEquality(unittest.TestCase):
    def test_empty_and_isolated_classes_have_no_invented_evidence(self):
        self.assertEqual(detect_omnipresent([], []).removed_classes, ())
        result = detect_omnipresent(["Alone"], [])
        score = result.by_class()["Alone"]
        self.assertEqual(score.reason, "no_external_member_use")
        self.assertIsNone(score.usage_equality)
        self.assertIsNone(score.cardinality)
        self.assertEqual(result.retained_classes, ("Alone",))

    def test_cardinality_boundary_is_ten_callers_not_eleven(self):
        for count, expected in [(9, False), (10, True), (11, True)]:
            with self.subTest(count=count):
                callers = [f"C{i}" for i in range(count)]
                edges = [row(caller, "run()", "Utility", "log()") for caller in callers]
                score = detect_omnipresent(callers + ["Utility"], edges).by_class()["Utility"]
                self.assertEqual(score.fanin, count)
                self.assertEqual(score.omnipresent, expected)
                self.assertAlmostEqual(score.max_dedication, 1 / count)

    def test_usage_threshold_is_inclusive_at_exact_point_eighty_five(self):
        callers = [f"C{i}" for i in range(10)]
        edges = [row(caller, "run()", "Utility", "common()") for caller in callers]
        edges += [row(caller, "run()", "Utility", "less_common()") for caller in callers[:5]]
        # mx=2.  Five callers receive 1/(10*2)+1/(5*2)=3/20,
        # so e=17/20=.85 exactly, while c=.90 exactly.
        score = detect_omnipresent(callers + ["Utility"], edges).by_class()["Utility"]
        self.assertTrue(score.omnipresent)
        self.assertTrue(score.usage_equality_passed)
        self.assertTrue(score.cardinality_passed)
        self.assertAlmostEqual(score.usage_equality, 0.85)

    def test_source_members_are_counted_but_target_members_are_sets(self):
        edges = [
            row("A", "first()", "B", "value:I"),
            row("A", "second()", "B", "value:I"),
            row("C", "run()", "B", "value:I"),
        ]
        result = detect_omnipresent(["A", "B", "C"], edges + [edges[0]] * 4)
        score = result.by_class()["B"]
        self.assertEqual(score.fanin, 2)
        self.assertEqual(score.referenced_members, 1)
        self.assertAlmostEqual(score.max_dedication, 1 / 3)
        self.assertEqual({p.source_class: p.dedication for p in result.dedications}, {"A": 1 / 3, "C": 1 / 3})
        self.assertEqual(result.stats.unique_member_edges, 3)
        self.assertEqual(result.stats.duplicate_member_edges, 4)

    def test_rare_setup_method_protects_a_popular_class(self):
        callers = [f"C{i}" for i in range(20)] + ["Startup"]
        edges = [row(caller, "run()", "Logger", "log()") for caller in callers]
        edges.append(row("Startup", "run()", "Logger", "init()"))
        score = detect_omnipresent(callers + ["Logger"], edges).by_class()["Logger"]
        self.assertEqual(score.fanin, 21)
        self.assertTrue(score.cardinality_passed)
        self.assertEqual(score.strongest_caller, "Startup")
        self.assertAlmostEqual(score.max_dedication, Fraction(1, 2) + Fraction(1, 42))
        self.assertFalse(score.omnipresent)
        self.assertEqual(score.reason, "usage_equality_below_threshold")

    def test_external_library_endpoints_do_not_enter_any_count(self):
        edges = [
            row("A", "run()", "Utility", "log()"),
            row("External", "run()", "Utility", "log()"),
            row("A", "run()", "java.lang.String", "length()"),
        ]
        result = detect_omnipresent(["A", "Utility"], edges)
        score = result.by_class()["Utility"]
        self.assertEqual(result.stats.excluded_external_edges, 2)
        self.assertEqual(result.stats.unique_member_edges, 1)
        self.assertEqual(score.max_dedication, 1.0)
        self.assertEqual(score.fanin, 1)

    def test_merged_inner_owners_keep_distinct_original_member_ids(self):
        edges = [
            {"source_class": "Outer", "source_member": "Outer$Inner#run()V",
             "target_class": "Utility", "target_member": "Utility#log()V"},
            {"source_class": "Outer", "source_member": "Outer$1#run()V",
             "target_class": "Utility", "target_member": "Utility#log()V"},
            row("Consumer", "run()", "Utility", "log()V"),
            {"source_class": "Outer", "source_member": "Outer$1#run()V",
             "target_class": "Outer", "target_member": "Outer#accept()V"},
        ]
        result = detect_omnipresent(["Outer", "Consumer", "Utility"], edges)
        score = result.by_class()["Utility"]
        self.assertEqual(result.stats.excluded_intraclass_edges, 1)
        self.assertEqual(score.fanin, 2)
        self.assertAlmostEqual(score.max_dedication, 1 / 3)

    def test_tuple_interface_and_unreferenced_members(self):
        owners = {"A#run()": "A", "B#used:I": "B", "B#unused:I": "B"}
        result = detect_omnipresent(["A", "B"], [("A#run()", "B#used:I")], member_owners=owners)
        score = result.by_class()["B"]
        self.assertEqual(score.referenced_members, 1)
        self.assertEqual(score.max_dedication, 1.0)

    def test_removal_is_simultaneous_without_iterative_recalculation(self):
        callers = [f"C{i}" for i in range(9)]
        edges = [row(caller, "run()", target, "use()") for caller in callers for target in ("U", "V")]
        edges += [row("U", "run()", "V", "use()"), row("V", "run()", "U", "use()")]
        result = detect_omnipresent(callers + ["U", "V"], edges)
        self.assertEqual(result.removed_classes, ("U", "V"))

    def test_serialization_is_deterministic_and_json_safe(self):
        callers = [f"C{i}" for i in range(12)]
        edges = [row(caller, "run()", "U", f"use{index % 3}()") for index, caller in enumerate(callers)]
        first = detect_omnipresent(callers + ["U"], edges)
        rng = random.Random(23)
        rng.shuffle(edges)
        second = detect_omnipresent(list(reversed(callers)) + ["U"], edges)
        self.assertEqual(first.to_dict(include_dedications=True), second.to_dict(include_dedications=True))
        json.dumps(first.to_dict(include_dedications=True), allow_nan=False)

    def test_optimized_result_matches_independent_exact_oracle(self):
        for seed in range(12):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                classes = [f"C{i}" for i in range(14)]
                edges = [
                    row(rng.choice(classes), f"m{rng.randrange(3)}()",
                        rng.choice(classes), f"m{rng.randrange(3)}()")
                    for _ in range(550)
                ]
                edges += edges[:15]
                edges += [row("third.party.Library", "run()", "C0", "m0()")]
                expected = exact_paper_oracle(classes, edges)
                result = detect_omnipresent(classes, edges).by_class()
                for cls, (fanin, mx, maximum, equality, cardinality, removed) in expected.items():
                    score = result[cls]
                    self.assertEqual(score.fanin, fanin)
                    self.assertEqual(score.referenced_members, mx)
                    self.assertEqual(score.omnipresent, removed)
                    if maximum is None:
                        self.assertIsNone(score.max_dedication)
                    else:
                        self.assertAlmostEqual(score.max_dedication, float(maximum), places=14)
                        self.assertAlmostEqual(score.usage_equality, float(equality), places=14)
                        self.assertAlmostEqual(score.cardinality, float(cardinality), places=14)

    def test_input_errors_do_not_silently_remove_evidence(self):
        with self.assertRaisesRegex(ValueError, "require a member_owners"):
            detect_omnipresent(["A", "B"], [("A#m", "B#m")])
        with self.assertRaisesRegex(ValueError, "owner missing"):
            detect_omnipresent(["A", "B"], [("A#m", "B#m")], member_owners={"A#m": "A"})
        with self.assertRaisesRegex(ValueError, "missing"):
            detect_omnipresent(["A", "B"], [{"source_class": "A"}])
        conflicting = [row("A", "run()", "U", "use()"), row("B", "run()", "U", "use()")]
        conflicting[1]["source_member"] = conflicting[0]["source_member"]
        with self.assertRaisesRegex(ValueError, "conflicting owners"):
            detect_omnipresent(["A", "B", "U"], conflicting)
        for invalid in (-0.1, 1.1, float("nan"), float("inf")):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                detect_omnipresent([], [], usage_threshold=invalid)

    def test_zero_and_one_thresholds_keep_empty_evidence_safe(self):
        edges = [row("A", "run()", "B", "use()")]
        low = detect_omnipresent(["A", "B", "Isolated"], edges, usage_threshold=0, cardinality_threshold=0)
        self.assertEqual(low.removed_classes, ("B",))
        high = detect_omnipresent(["A", "B"], edges, usage_threshold=1, cardinality_threshold=1)
        self.assertEqual(high.removed_classes, ())


if __name__ == "__main__":
    unittest.main()
```
<!-- END_FULL_SOURCE tests/test_omnipresent.py -->
