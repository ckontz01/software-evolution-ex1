# Commit 10 — Independent validation and complete study explanations

**Student B · 2026-10-22 · 12 complete files · 2 full code/configuration listings**

Source snapshot: `f32e6e831f976eed8bf01faa1d66dbdc34bc49c7`. Dates are planned work sessions; make the commit when you actually import and review this packet.

## What to understand

Explain what the independent audit checks, why its count differs from the 91 tests, and work through one real Guava UE case using the source-backed evidence.

## Apply this packet

Set `HANDOFF_DIR` to your extracted student bundle and `TEACHER_REPO` to the teacher checkout. Pull the preceding commit first. Commands below use the `guava-study` layout explained in the main map.

```bash
git -C "$TEACHER_REPO" pull --ff-only origin guava-assignment
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/10-b-validation-docs" --target "$TEACHER_REPO" --subdir guava-study
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/10-b-validation-docs" --target "$TEACHER_REPO" --subdir guava-study --apply
cd "$TEACHER_REPO/guava-study"
```

For commit 01, create the shared branch as shown in the main map; its remote branch does not exist until the first push, so omit that first pull.

## Checks before the commit

Run these in the cumulative study directory after applying the packet. For packet 01, first create the Python environment and install the locked requirements as shown in the main map:

```bash
python scripts/validate_results.py --output results/rerun/handoff-p10-validation.json
```

Stage and inspect only this packet, then use your own Git identity:

```bash
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/10-b-validation-docs" --target "$TEACHER_REPO" --subdir guava-study --apply --stage
git -C "$TEACHER_REPO" diff --cached --stat
git -C "$TEACHER_REPO" diff --cached
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/10-b-validation-docs" --target "$TEACHER_REPO" --subdir guava-study --check-staged
git -C "$TEACHER_REPO" commit -m 'import: add independent validation and complete study explanations (AI-assisted preparation)'
git -C "$TEACHER_REPO" push -u origin guava-assignment
```

Add a commit-message paragraph describing the checks you actually performed and anything you found. The import message identifies the prepared source; it does not claim you originally wrote every line.

## Further review checks

The following are useful for learning or final verification. Commands marked as writing evidence belong in a disposable copy, so the next packet still matches the frozen source. These are not additional canonical experiments.

Independently hand-check the real Guava UE examples using exact fractions.

```bash
python scripts/audit_ue_cases.py
```

**Where:** disposable cumulative checkout, preserving immutable packet payloads. **Writes:** rewrites case_checks.json and ue_case_study.md; use disposable cumulative checkout.

## Every file to push

All files below are present under this packet's `payload/` directory in the complete student download. Paths are relative to the study directory.

| File | Bytes | Content |
|---|---:|---|
| `README.md` | 17,049 | documentation or tool provenance |
| `docs/commit_roadmap.md` | 6,880 | documentation or tool provenance |
| `docs/contributions.md` | 2,629 | documentation or tool provenance |
| `docs/course_traceability.md` | 22,466 | documentation or tool provenance |
| `docs/oral_exam_guide.md` | 25,707 | documentation or tool provenance |
| `docs/reproducibility.md` | 9,399 | documentation or tool provenance |
| `docs/ue_case_study.md` | 7,423 | documentation or tool provenance |
| `docs/validation.md` | 8,563 | documentation or tool provenance |
| `results/performance/case_checks.json` | 255,834 | recorded evidence |
| `results/validation.json` | 50,118 | recorded evidence |
| `scripts/audit_ue_cases.py` | 20,569 | Full code below |
| `scripts/validate_results.py` | 91,504 | Full code below |

The machine-readable `packet.json` pins every file's SHA-256 and Git blob. Binary JAR/PDF/ZIP files and large evidence files are supplied as their exact original bytes in the payload, rather than as text pasted into this guide.

## Whole code

The following are complete files, with no omitted functions. Use the payload for copying so file bytes, line endings and original licences stay intact.

### scripts/audit_ue_cases.py

SHA-256: `7768571e47942c9c4bd15a92ea1e062c4d5135791884c335638e99dd563812eb` · 20,569 bytes

<!-- FULL_SOURCE scripts/audit_ue_cases.py 7768571e47942c9c4bd15a92ea1e062c4d5135791884c335638e99dd563812eb -->
````python
#!/usr/bin/env python3
"""Independently recalculate two real UE decisions using exact set definitions."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def rational(value):
    return {"fraction": str(value), "float": float(value)}


def exact_case(class_name, indexed_rows, classes, production, thresholds):
    incoming = [
        (number, row) for number, row in indexed_rows
        if row["target_class"] == class_name
        and row["source_class"] in classes
        and row["target_class"] in classes
        and row["source_class"] != row["target_class"]
    ]
    targets = {row["target_member"] for _, row in incoming}
    callers = {row["source_class"] for _, row in incoming}
    if not targets or not callers:
        raise ValueError(f"Case {class_name} has no incoming member-use evidence")
    source_fanin = {
        member: len({row["source_member"] for _, row in incoming if row["target_member"] == member})
        for member in targets
    }
    # Express the paper's M_AB sets directly.  This audit does not import UE.
    caller_targets = {
        caller: {row["target_member"] for _, row in incoming if row["source_class"] == caller}
        for caller in callers
    }
    dedication = {
        caller: sum(
            (Fraction(1, source_fanin[member] * len(targets)) for member in caller_targets[caller]),
            Fraction(),
        )
        for caller in callers
    }
    strongest = min(dedication, key=lambda caller: (-dedication[caller], caller))
    maximum = dedication[strongest]
    equality = 1 - maximum
    cardinality = 1 - Fraction(1, len(callers))
    removed = equality >= thresholds[0] and cardinality >= thresholds[1]
    score = production[class_name]
    assert score["fanin"] == len(callers)
    assert score["referenced_members"] == len(targets)
    assert score["strongest_caller"] == strongest
    assert score["omnipresent"] == removed
    assert score["usage_equality_passed"] == (equality >= thresholds[0])
    assert score["cardinality_passed"] == (cardinality >= thresholds[1])
    errors = {}
    for name, exact in (("max_dedication", maximum), ("usage_equality", equality), ("cardinality", cardinality)):
        errors[name] = abs(score[name] - float(exact))
        assert math.isclose(score[name], float(exact), rel_tol=0, abs_tol=1e-14)

    def evidence_row(number, row):
        return {"csv_row_number_including_header": number, **row}

    return {
        "class_name": class_name,
        "exact": {
            "fanin": len(callers), "referenced_members": len(targets),
            "max_dedication": rational(maximum), "usage_equality": rational(equality),
            "cardinality": rational(cardinality), "strongest_caller": strongest,
            "omnipresent": removed,
        },
        "production_score": score,
        "verification": {"all_comparisons_passed": True, "absolute_float_errors": errors,
                         "caller_scores_checked_for_maximum": len(callers)},
        "incoming_member_row_count": len(incoming),
        "distinct_incoming_member_pairs": len({(row["source_member"], row["target_member"]) for _, row in incoming}),
        "strongest_caller_terms": [
            {"target_member": member, "source_member_fanin": source_fanin[member],
             "contribution": rational(Fraction(1, source_fanin[member] * len(targets)))}
            for member in sorted(caller_targets[strongest])
        ],
        "strongest_caller_term_fanin_histogram": dict(sorted(Counter(source_fanin[m] for m in caller_targets[strongest]).items())),
        "all_caller_dedications": [
            {"caller": caller, "used_target_members": len(caller_targets[caller]),
             "dedication": rational(dedication[caller])}
            for caller in sorted(callers, key=lambda caller: (-dedication[caller], caller))
        ],
        "all_target_member_evidence": [
            {"target_member": member, "source_member_fanin": source_fanin[member],
             "distinct_caller_classes": len({row["source_class"] for _, row in incoming if row["target_member"] == member}),
             "csv_row_numbers_including_header": [number for number, row in incoming if row["target_member"] == member],
             "example_rows": [evidence_row(number, row) for number, row in incoming if row["target_member"] == member][:2]}
            for member in sorted(targets)
        ],
        "strongest_caller_member_rows": [evidence_row(number, row) for number, row in incoming if row["source_class"] == strongest],
    }


def resolution_audit(graph):
    rows = read_csv(graph / "unresolved_member_uses.csv")
    aliases = {row["binary_class"]: row["class"] for row in read_csv(graph / "class_aliases.csv")}
    counts = {row["metric"]: int(row["value"]) for row in read_csv(graph / "extraction_counts.csv")}
    interclass = [row for row in rows if aliases[row["source_class"]] != aliases[row["symbolic_target"]]]
    return {
        "unresolved_event_rows": len(rows),
        "distinct_recorded_references": len({tuple(row.items()) for row in rows}),
        "unresolved_interclass_event_rows_after_merging": len(interclass),
        "distinct_unresolved_interclass_references_after_merging": len({tuple(row.items()) for row in interclass}),
        "observed_member_use_events": counts["observed_member_use_events"],
        "unresolved_fraction_of_all_observed_member_use_events": len(rows) / counts["observed_member_use_events"],
        "fraction_interpretation": "share of raw observed events, not a completeness or false-negative rate",
        "top_unresolved_members": [{"member": key, "event_rows": count} for key, count in Counter(row["member"] for row in rows).most_common(15)],
        "top_unresolved_normalized_targets": [
            {"class": key, "event_rows": count}
            for key, count in Counter(aliases[row["symbolic_target"]] for row in rows).most_common(15)
        ],
        "interface_resolution_ties": counts.get("interface_resolution_ties", 0),
        "member_resolution_cache_entries": counts.get("member_resolution_cache_entries", 0),
        "member_resolution_cache_hits": counts.get("member_resolution_cache_hits", 0),
        "note": "Unavailable library ancestors and their inherited members are not invented as project member evidence. Raw unresolved rows can contain repeated call sites and intraclass uses.",
    }


def source_interpretation_checks(sources_jar):
    """Verify the source statements used to interpret the two numerical cases."""
    entries = {
        "com/google/common/base/Preconditions.java": [
            "public static void checkArgument(boolean expression)",
            "public static void checkState(boolean expression)",
        ],
        "com/google/common/collect/Iterables.java": [
            "return Iterators.all(iterable.iterator(), predicate);",
            "return Iterators.any(iterable.iterator(), predicate);",
            "return Iterators.find(iterable.iterator(), predicate);",
        ],
    }
    checks = []
    with ZipFile(sources_jar) as archive:
        for entry, markers in entries.items():
            data = archive.read(entry)
            lines = data.decode("utf-8").splitlines()
            found = []
            for marker in markers:
                matches = [(number, line.strip()) for number, line in enumerate(lines, start=1) if marker in line]
                assert len(matches) == 1, (entry, marker, matches)
                found.append({"line_number": matches[0][0], "source_line": matches[0][1]})
            checks.append({"archive_entry": entry, "entry_sha256": hashlib.sha256(data).hexdigest(), "verified_markers": found})
    return checks


def write_report(path, audit):
    version = audit["version"]
    removed, retained = audit["cases"]
    resolution = audit["resolution_coverage"]
    provenance = audit["release_provenance"]
    lines = [
        f"# Two independently checked UE decisions in Guava {version}", "",
        "The checks below reconstruct the paper's mathematical sets directly from the extracted member CSV and use exact rational arithmetic. The audit script does not import the production detector. It checks every caller's dedication before choosing the maximum, then compares both decisions with the finalized `ue.json` output.", "",
        f"Release: `{provenance['tag']}`; commit: `{provenance['commit_sha']}`. The graph has {provenance['classes']:,} normalized project classes and {provenance['unique_member_edges']:,} distinct member edges. UE removes {audit['removed_classes_total']} classes under the fixed e ≥ 0.85 and c ≥ 0.90 rule. These are preprocessing decisions; no extra architecture was generated for this audit.", "",
        f"Complete numerical evidence, exact fractions, CSV row references, all caller scores, and input SHA-256 values are recorded in [case_checks.json](../results/performance/case_checks.json). The primary inputs are [member_dependencies.csv](../data/graphs/{version}/member_dependencies.csv) and [ue.json](../results/versions/{version}/ue.json). The method follows [Yano and Matsuo, 2020, equations 1–3, p. 663](https://doi.org/10.1109/ICSME46990.2020.00068).", "",
        "| Target | Distinct caller classes | Referenced target members | Maximum dedication | Usage equality | Cardinality | Decision |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in audit["cases"]:
        e = case["exact"]
        lines.append(f"| `{case['class_name']}` | {e['fanin']} | {e['referenced_members']} | {e['max_dedication']['float']:.12f} | {e['usage_equality']['float']:.12f} | {e['cardinality']['float']:.12f} | {'Remove' if e['omnipresent'] else 'Retain'} |")
    lines += ["", "## Removed: Preconditions", "",
        f"The strongest caller is `{removed['exact']['strongest_caller']}`. It uses {len(removed['strongest_caller_terms'])} of the {removed['exact']['referenced_members']} externally referenced members of Preconditions. Across the system, the incoming evidence contains {removed['incoming_member_row_count']:,} distinct member edges from {removed['exact']['fanin']} caller classes. Those quantities are different: xm_fanin counts distinct source methods or fields, while cardinality counts classes.", "",
        f"The {len(removed['strongest_caller_terms'])} terms for the strongest caller are shown below. Each overload is a separate target member; JVM descriptors distinguish primitive and reference parameter types. For readability, the class prefix is omitted.", "",
        "| Referenced Preconditions member | Distinct source members using it | Contribution to dedication |",
        "| --- | ---: | ---: |",
    ]
    for term in removed["strongest_caller_terms"]:
        lines.append(f"| `{term['target_member'].split('#',1)[1]}` | {term['source_member_fanin']} | {term['contribution']['fraction']} |")
    lines += ["", f"Adding these exact fractions gives **{removed['exact']['max_dedication']['fraction']} ≈ {removed['exact']['max_dedication']['float']:.12f}**. All {removed['exact']['fanin']} caller scores were checked; none is larger. Therefore e = {removed['exact']['usage_equality']['float']:.12f} and c = 1 − 1/{removed['exact']['fanin']} = {removed['exact']['cardinality']['float']:.12f}. Both thresholds pass, so UE removes Preconditions.", "",
        "Even its strongest caller has a small share of the class's dedication. Its argument and state validation functions are broadly shared in this member-use graph. The conclusion comes from the measured calls and counts, not from matching the class name to a utility-name list. The matching source JAR confirms the `checkArgument` and `checkState` declarations; their entry hashes and line references are in the evidence JSON.", "",
        "## Retained despite many callers: Iterators", "",
        f"Iterators has {retained['exact']['fanin']} caller classes, so its cardinality {retained['exact']['cardinality']['float']:.12f} passes. Its strongest caller is `{retained['exact']['strongest_caller']}`, which uses {len(retained['strongest_caller_terms'])} of its {retained['exact']['referenced_members']} externally referenced members. Many of those operations are used by only one source member in the scoped graph.", "",
        "The complete member list is in the JSON. Grouping equal denominators makes the manual calculation shorter:", "",
        "| xm_fanin of a referenced target member | Number of such members used by Iterables | Combined contribution |",
        "| ---: | ---: | ---: |",
    ]
    for fanin, count in retained["strongest_caller_term_fanin_histogram"].items():
        lines.append(f"| {fanin} | {count} | {count}/({fanin} × {retained['exact']['referenced_members']}) |")
    lines += ["", f"Their sum is **{retained['exact']['max_dedication']['fraction']} ≈ {retained['exact']['max_dedication']['float']:.12f}**. Consequently e = {retained['exact']['usage_equality']['float']:.12f}, below 0.85, so Iterators is retained. The paired Iterables/Iterators usage supplies the specialization evidence. UE can preserve a class that offers utility operations when a particular caller has a strong relationship with it.", "",
        "The matching source JAR also confirms that `Iterables.all`, `Iterables.any`, and `Iterables.find` delegate to their corresponding Iterators operations. These are concrete examples of the wider specialization pattern measured above; the source entry hash and exact lines are recorded in the JSON.", "",
        "This case also explains why a large incoming degree alone is insufficient: both targets have many caller classes, but their maximum dedication scores differ substantially.", "",
        "## What the decisions do not establish", "",
        "The same finalized removal set includes `ImmutableList`, `ImmutableMap`, and `ImmutableCollection`. These are important collection API types. The moderate detector does not guarantee preservation of every important class, and a removal decision does not mean the class is unnecessary or badly designed. Guava itself is a library; useful shared functionality and architectural features overlap. No threshold was adjusted after observing these examples. Architectural quality must also be discussed through the requested clustering/evolution metrics and interpretation, rather than treating UE labels as ground truth.", "",
        "## Quantified extraction limitations", "",
        f"The latest extractor records **{resolution['unresolved_event_rows']} unresolved member-use events**, representing **{resolution['distinct_recorded_references']} distinct recorded references**. After mapping source and target owners through the class aliases, **{resolution['unresolved_interclass_event_rows_after_merging']} events / {resolution['distinct_unresolved_interclass_references_after_merging']} distinct references** cross normalized class boundaries. The remaining recorded events are intraclass after merging.", "",
        f"There are {resolution['observed_member_use_events']:,} observed member-use events overall, so unresolved rows account for {100*resolution['unresolved_fraction_of_all_observed_member_use_events']:.3f}% of that raw event count. This denominator includes external and intraclass events. The percentage is therefore **not** a graph-completeness or false-negative rate. Missing library-ancestor declarations are a known boundary of artifact-only resolution, and the detector does not fabricate them as project members.", "",
        "| Frequently unresolved signature | Recorded event rows |",
        "| --- | ---: |",
    ]
    for item in resolution["top_unresolved_members"][:8]:
        lines.append(f"| `{item['member']}` | {item['event_rows']} |")
    lines += ["", f"There were {resolution['interface_resolution_ties']} interface-resolution ties, resolved deterministically as documented in [omnipresent.md](omnipresent.md). Cached lookups recorded {resolution['member_resolution_cache_hits']:,} hits across {resolution['member_resolution_cache_entries']:,} distinct queries. Full unresolved evidence is retained in [unresolved_member_uses.csv](../data/graphs/{version}/unresolved_member_uses.csv); all emitted graph endpoints remain owned project classes.", "",
        "## Reproduce the independent check", "", "```bash",
        f"python scripts/audit_ue_cases.py --version {version}", "```", "",
        "The script requires the finalized extraction and UE output. It verifies the fixed thresholds and decisions, saves all exact contributions and source-row evidence, and recreates this explanation. Detector performance can be reproduced separately with `python scripts/benchmark_ue.py`.", "",
    ]
    path.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="33.7.2")
    args = parser.parse_args()
    graph = ROOT / "data/graphs" / args.version
    source_jars = sorted((ROOT / "data/raw" / args.version).glob("*sources.jar"))
    assert len(source_jars) == 1
    sources_jar = source_jars[0]
    result_path = ROOT / "results/versions" / args.version / "ue.json"
    production_json = json.loads(result_path.read_text())
    production = {row["class_name"]: row for row in production_json["scores"]}
    thresholds = (Fraction(str(production_json["usage_threshold"])), Fraction(str(production_json["cardinality_threshold"])))
    assert thresholds == (Fraction(17, 20), Fraction(9, 10))
    classes = {row["class"] for row in read_csv(graph / "classes.csv")}
    rows = list(enumerate(read_csv(graph / "member_dependencies.csv"), start=2))
    cases = [exact_case(name, rows, classes, production, thresholds) for name in (
        "com.google.common.base.Preconditions", "com.google.common.collect.Iterators",
    )]
    assert cases[0]["exact"]["omnipresent"] and not cases[1]["exact"]["omnipresent"]
    # Guard the prose's concrete interpretation if a different release is used.
    assert cases[1]["exact"]["strongest_caller"] == "com.google.common.collect.Iterables"
    for case in cases:
        assert case["incoming_member_row_count"] == case["distinct_incoming_member_pairs"]
    assert {
        "com.google.common.collect.ImmutableList",
        "com.google.common.collect.ImmutableMap",
        "com.google.common.collect.ImmutableCollection",
    }.issubset(production_json["removed_classes"])
    inputs = [graph / name for name in ("classes.csv", "member_dependencies.csv", "class_aliases.csv", "unresolved_member_uses.csv", "extraction_counts.csv", "provenance.json")]
    inputs += [result_path, Path(__file__).resolve(), sources_jar]
    release_provenance = json.loads((graph / "provenance.json").read_text())
    assert hashlib.sha256(sources_jar.read_bytes()).hexdigest() == release_provenance["sources_sha256"]
    audit = {
        "schema_version": 1, "version": args.version,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "independent per-class set definitions and exact Fraction arithmetic; production UE is not imported",
        "source_row_numbering": "CSV row number including the header as row 1",
        "input_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs},
        "thresholds": {"usage_equality": rational(thresholds[0]), "cardinality": rational(thresholds[1])},
        "release_provenance": release_provenance,
        "source_interpretation_checks": source_interpretation_checks(sources_jar),
        "removed_classes_total": len(production_json["removed_classes"]),
        "removed_classes": production_json["removed_classes"],
        "cases": cases, "resolution_coverage": resolution_audit(graph),
        "all_checks_passed": True,
    }
    output = ROOT / "results/performance/case_checks.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit, indent=2, allow_nan=False) + "\n")
    write_report(ROOT / "docs/ue_case_study.md", audit)
    for case in cases:
        print(case["class_name"], "exact maximum =", case["exact"]["max_dedication"]["fraction"], "decision verified")
    print(f"Saved {output} and docs/ue_case_study.md")


if __name__ == "__main__":
    main()
````
<!-- END_FULL_SOURCE scripts/audit_ue_cases.py -->

### scripts/validate_results.py

SHA-256: `bad893869fb51868fbc22306e88b4c86a87921f757a7cf844bac4ba965fad797` · 91,504 bytes

<!-- FULL_SOURCE scripts/validate_results.py bad893869fb51868fbc22306e88b4c86a87921f757a7cf844bac4ba965fad797 -->
```python
#!/usr/bin/env python3
"""Independently audit the 30-release Guava study using only Python's stdlib.

No production extraction, detector, clustering or metric function is imported.
This is an artifact audit, not another architecture experiment. It recomputes
the lecture formulas and exact-rational UE decisions from stored graph evidence,
checks archive membership/provenance, and checks all 120 partition populations.
Run after scripts/run_study.py: python scripts/validate_results.py
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
import csv
from datetime import date, datetime, timezone
from fractions import Fraction
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import re
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RELATIONS = {"EXTENDS", "IMPLEMENTS", "METHOD_CALL", "METHOD_PARAMETER",
             "FIELD_REFERENCE", "TYPE_USAGE", "EXCEPTION_THROWS"}
OWNED_PREFIXES = ("com.google.common.", "com.google.thirdparty.publicsuffix.")
SOURCE_PREFIXES = ("com/google/common/", "com/google/thirdparty/publicsuffix/")
INSTRUCTOR_SHA256 = "8e4e857222dba569cc48ddf2bc58d3ac206d4ee1c0d5228b7b69517016450e9c"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def data(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def close(a, b) -> bool:
    a = None if a == "" else a
    b = None if b == "" else b
    if a is None or b is None:
        return a is b
    try:
        return math.isfinite(float(a)) and math.isfinite(float(b)) and math.isclose(
            float(a), float(b), rel_tol=1e-11, abs_tol=1e-12)
    except (TypeError, ValueError):
        return False


def independent_quality(nodes, edges, assignment) -> dict:
    """Lecture formula by edge contributions, independent of saved term tables."""
    sizes = Counter(assignment.values())
    k, n, m = len(sizes), len(nodes), len(edges)
    pair_count = k * (k - 1) // 2
    inner, incoming, outgoing, cross = Counter(), Counter(), Counter(), Counter()
    cohesion_terms, coupling_terms = [], []
    for a, b in edges:
        left, right = assignment[a], assignment[b]
        if left == right:
            inner[left] += 1
            cohesion_terms.append(1 / (k * sizes[left] * (sizes[left] - 1)))
        else:
            incoming[right] += 1
            outgoing[left] += 1
            cross[tuple(sorted((left, right)))] += 1
            coupling_terms.append(1 / (pair_count * 2 * sizes[left] * sizes[right]))
    cohesion, coupling = math.fsum(cohesion_terms), math.fsum(coupling_terms)
    internal = sum(inner.values())
    capacity = sum(s * (s - 1) for s in sizes.values())
    cluster_terms = [{
        "cluster": c, "n_classes": s, "internal_edges": inner[c],
        "possible_internal_edges": s * (s - 1),
        "cohesion": inner[c] / (s * (s - 1)) if s > 1 else 0.0,
        "incoming_inter_edges": incoming[c], "outgoing_inter_edges": outgoing[c],
    } for c, s in sorted(sizes.items())]
    pair_terms = [{
        "cluster_i": a, "cluster_j": b, "n_i": sizes[a], "n_j": sizes[b],
        "inter_edges_both_directions": cross[a, b],
        "possible_inter_edges": 2 * sizes[a] * sizes[b],
        "coupling": cross[a, b] / (2 * sizes[a] * sizes[b]),
    } for a, b in combinations(sorted(sizes), 2)]
    return {
        "n_nodes": n, "n_edges": m, "n_clusters": k,
        "cohesion": cohesion, "coupling": coupling, "mq": cohesion - coupling,
        "size_weighted_cohesion": math.fsum(
            inner[c] / (s - 1) for c, s in sizes.items() if s > 1) / n if n else 0.0,
        "pair_weighted_cohesion": internal / capacity if capacity else 0.0,
        "internal_edges": internal, "inter_edges": m - internal,
        "inter_edge_fraction": (m - internal) / m if m else 0.0,
        "graph_density": m / (n * (n - 1)) if n > 1 else 0.0,
        "isolates": len(set(nodes) - {x for edge in edges for x in edge}),
        "min_cluster_size": min(sizes.values(), default=0),
        "max_cluster_size": max(sizes.values(), default=0),
        "mean_cluster_size": n / k if k else 0.0,
        "singleton_clusters": sum(s == 1 for s in sizes.values()),
        "per_cluster": cluster_terms, "per_pair": pair_terms,
    }


def independent_matching(options, right_count):
    """Unit-capacity max flow, separate from production's matching implementation."""
    left_count = len(options)
    sink = left_count + right_count + 1
    capacity = [dict() for _ in range(sink + 1)]

    def connect(a, b):
        capacity[a][b], capacity[b][a] = 1, 0

    for i, targets in enumerate(options, 1):
        connect(0, i)
        for j in targets:
            connect(i, 1 + left_count + j)
    for j in range(right_count):
        connect(1 + left_count + j, sink)
    flow = 0
    while True:
        predecessors = {0: -1}
        queue = deque([0])
        while queue and sink not in predecessors:
            vertex = queue.popleft()
            for neighbor, available in capacity[vertex].items():
                if available and neighbor not in predecessors:
                    predecessors[neighbor] = vertex
                    queue.append(neighbor)
        if sink not in predecessors:
            return flow
        vertex = sink
        while vertex:
            predecessor = predecessors[vertex]
            capacity[predecessor][vertex] -= 1
            capacity[vertex][predecessor] += 1
            vertex = predecessor
        flow += 1


def independent_mojofm(a, b, nodes) -> dict:
    """Recompute both MoJo terms with flow; use a different denominator algorithm.

    A maximum flow on the tied intersection maxima gives occupied target groups.
    For the denominator, build the target-size Ferrers graph directly: a target
    cluster of size s connects to the first s artificial groups. Its maximum
    matching gives the worst-case group count. This does not reuse production's
    sorted-size recurrence. No production module is used in this check.
    """
    nodes = tuple(nodes)
    left = {label: i for i, label in enumerate(sorted({a[n] for n in nodes}))}
    right = {label: i for i, label in enumerate(sorted({b[n] for n in nodes}))}
    matrix = [[0] * len(right) for _ in left]
    for node in nodes:
        matrix[left[a[node]]][right[b[node]]] += 1
    maxima = [max(row) for row in matrix]
    options = [[j for j, value in enumerate(row) if value == maximum]
               for row, maximum in zip(matrix, maxima)]
    groups = independent_matching(options, len(right))
    moves, joins = len(nodes) - sum(maxima), len(left) - groups
    target_sizes = list(Counter(b[n] for n in nodes).values())
    normalizer_groups = independent_matching([range(size) for size in target_sizes],
                                             max(target_sizes, default=0))
    maximum = len(nodes) - normalizer_groups
    distance = moves + joins
    return {
        "direction": "source_to_target", "n_nodes": len(nodes),
        "source_clusters": len(left), "target_clusters": len(right),
        "move_operations": moves, "join_operations": joins,
        "matched_target_clusters": groups, "normalizer_groups": normalizer_groups,
        "distance": distance, "max_distance": maximum,
        "score": float(Fraction(100 * (maximum - distance), maximum)) if maximum else None,
        "defined": maximum > 0,
        "reason": None if maximum else ("empty_universe" if not nodes else "single_node_universe"),
    }


def independent_inertia(nodes, edges, assignment):
    """Compute normalized [A+I,(A+I)^T] SSE using the centroid sum identity."""
    coordinates = {n: {(0, n), (1, n)} for n in nodes}
    for source, target in edges:
        coordinates[source].add((0, target))
        coordinates[target].add((1, source))
    sizes = Counter(assignment.values())
    sums = defaultdict(lambda: defaultdict(float))
    for node in nodes:
        value = 1 / math.sqrt(len(coordinates[node]))
        for coordinate in sorted(coordinates[node]):
            sums[assignment[node]][coordinate] += value
    return len(nodes) - math.fsum(value * value / sizes[group]
                                 for group, vector in sums.items() for value in vector.values())


def independent_ue(nodes, member_rows, usage, cardinality) -> dict:
    """Re-evaluate paper decisions with exact fractions for every target class."""
    sources, callers, targets = defaultdict(set), defaultdict(set), defaultdict(set)
    for row in member_rows:
        sources[row["target_member"]].add(row["source_member"])
        callers[row["target_member"]].add(row["source_class"])
        targets[row["target_class"]].add(row["target_member"])
    answer = {}
    for node in nodes:
        member_set = targets[node]
        by_caller = defaultdict(Fraction)
        for target in member_set:
            contribution = Fraction(1, len(sources[target]) * len(member_set))
            for caller in callers[target]:
                by_caller[caller] += contribution
        if not by_caller:
            answer[node] = {"fanin": 0, "referenced_members": 0,
                            "max_dedication": None, "usage_equality": None,
                            "cardinality": None, "omnipresent": False}
            continue
        maximum = max(by_caller.values())
        ue = 1 - maximum
        c = 1 - Fraction(1, len(by_caller))
        answer[node] = {"fanin": len(by_caller), "referenced_members": len(member_set),
                        "max_dedication": float(maximum), "usage_equality": float(ue),
                        "cardinality": float(c),
                        "omnipresent": ue >= Fraction(str(usage)) and c >= Fraction(str(cardinality))}
    return answer


def failure_value(value):
    """Keep failures JSON-readable even for paths, bytes, sets and tuple keys."""
    if isinstance(value, dict):
        return {str(key): failure_value(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return [failure_value(item) for item in sorted(value, key=str)]
    if isinstance(value, (list, tuple)):
        return [failure_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}
    return value


class Audit:
    def __init__(self):
        self.counts = Counter()
        self.failures = []
        self.warnings = []
        self.release_evidence = []
        self.ai_evidence = None

    def check(self, condition, name, context, actual=None, expected=None):
        self.counts[name] += 1
        if not condition:
            self.failures.append({"check": name, "context": context,
                                  "actual": failure_value(actual), "expected": failure_value(expected)})

    def equal(self, actual, expected, name, context):
        self.check(actual == expected, name, context, actual, expected)

    def numeric(self, actual, expected, name, context):
        self.check(close(actual, expected), name, context, actual, expected)

    def flat_metrics(self, observed, expected, context):
        for key, value in expected.items():
            if key not in ("per_cluster", "per_pair"):
                self.numeric(observed.get(key), value, "independent_metric_recalculation", f"{context}/{key}")
        self.numeric(float(observed["cohesion"]) - float(observed["coupling"]), observed["mq"],
                     "mq_identity", context)
        for key in ("cohesion", "coupling", "graph_density", "inter_edge_fraction",
                    "size_weighted_cohesion", "pair_weighted_cohesion"):
            value = float(observed[key])
            self.check(0 <= value <= 1, "metric_bounds", f"{context}/{key}", value, "[0,1]")
        self.check(-1 <= float(observed["mq"]) <= 1, "metric_bounds", f"{context}/mq")

    def terms(self, observed, expected, context):
        self.equal(len(observed), len(expected), "term_table_row_counts", context)
        for index, (got, want) in enumerate(zip(observed, expected)):
            for key, value in want.items():
                name = f"{context}/{index}/{key}"
                if isinstance(value, str):
                    self.equal(got.get(key), value, "term_identity", name)
                else:
                    self.numeric(got.get(key), value, "term_value", name)


def read_edges(path: Path):
    return [(r["source"], r["target"]) for r in rows(path)]


def read_rsf(path: Path, relation: str):
    result = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        tokens = line.split()
        if len(tokens) != 3 or tokens[0] != relation:
            raise ValueError(f"Malformed {relation} RSF in {path}: {line}")
        result.append((tokens[1], tokens[2]))
    return result


def read_partition(path: Path, expected_nodes, audit: Audit):
    records = rows(path)
    assignment = {r["class"]: r["cluster"] for r in records}
    audit.equal(len(records), len(assignment), "unique_membership", str(path))
    audit.equal(set(assignment), set(expected_nodes), "complete_membership", str(path))
    audit.check(all(assignment.values()), "nonempty_cluster_labels", str(path))
    rsf = read_rsf(path.with_suffix(".rsf"), "contain")
    audit.equal(sorted(rsf), sorted((c, n) for n, c in assignment.items()), "partition_rsf_matches_csv", str(path))
    return assignment


def independent_calendar_selection(groups, count):
    """Reconstruct calendar selection by explicitly comparing squared-gap sums.

    The selector scores an insertion by its local product formula. This audit
    instead inserts every eligible candidate and subtracts the complete sums of
    squared calendar gaps. Only frozen release metadata enters either method.
    """
    key = lambda version: tuple(map(int, (version + ".0.0").split(".")[:3]))
    day = lambda row: date.fromisoformat(row["release_date"][:10]).toordinal()
    order = lambda row: (day(row), key(row["version"]))
    family = lambda row: ".".join(row["version"].split(".")[:2])
    representatives = {name: min(candidates, key=order) for name, candidates in groups.items()}
    endpoint = max((row for candidates in groups.values() for row in candidates), key=order)
    representatives[family(endpoint)] = endpoint
    anchors = [representatives[f"{major}.0"] for major in range(10, 34)]
    anchors.append(endpoint)
    selected = {family(row): row for row in anchors}
    optional_per_major = Counter()
    steps = []

    def gaps(ordered):
        return [day(b) - day(a) for a, b in zip(ordered, ordered[1:])]

    while len(selected) < count:
        current = sorted(selected.values(), key=order)
        before = sum(gap * gap for gap in gaps(current))
        candidates = []
        for name, row in representatives.items():
            major = key(row["version"])[0]
            if name in selected or optional_per_major[major] >= 2:
                continue
            with_candidate = sorted([*current, row], key=order)
            current_gaps = gaps(with_candidate)
            if min(current_gaps) < 60:
                continue
            position = with_candidate.index(row)
            if position == 0 or position == len(with_candidate) - 1:
                continue
            gain = before - sum(gap * gap for gap in current_gaps)
            candidates.append((gain, row, with_candidate[position - 1], with_candidate[position + 1]))
        if not candidates:
            raise ValueError("Frozen calendar-selection constraints cannot supply 30 releases")
        gain, chosen, left, right = min(candidates, key=lambda item: (-item[0], *order(item[1])))
        selected[family(chosen)] = chosen
        optional_per_major[key(chosen["version"])[0]] += 1
        steps.append({"version": chosen["version"], "family": family(chosen), "gain": gain,
                      "left": left["version"], "right": right["version"],
                      "left_gap_days": day(chosen) - day(left),
                      "right_gap_days": day(right) - day(chosen),
                      "optional_count_for_major_after_selection": optional_per_major[key(chosen["version"])[0]],
                      "feasible_candidate_count": len(candidates)})
    return sorted(selected.values(), key=order), representatives, sorted(anchors, key=order), steps


def audit_family_selection(root, manifest, report):
    """Rebuild anchors, calendar spacing and release identity from the tag catalog."""
    inventory_path = root / "data/provenance/tag_inventory.json"
    inventory = data(inventory_path)
    stable = inventory["stable_tags_in_date_order"]
    excluded = {row["version"] for row in inventory["additional_exclusions"]}
    cutoff = manifest["selection_date_utc"]
    key = lambda version: tuple(map(int, (version + ".0.0").split(".")[:3]))
    eligible = [row for row in stable if key(row["version"])[0] >= 10
                and row["version"] not in excluded and row["release_date"][:10] <= cutoff]
    groups = defaultdict(list)
    for row in eligible:
        groups[".".join(row["version"].split(".")[:2])].append(row)
    family_order = sorted(groups, key=lambda f: (min(r["release_date"] for r in groups[f]), key(f)))
    report.equal(len(eligible), 70, "family_selection_catalog", "eligible releases")
    report.equal(len(family_order), 45, "family_selection_catalog", "eligible major/minor families")
    count = len(manifest["versions"])
    chosen, representatives, anchors, optional_steps = independent_calendar_selection(groups, count)
    selected_families = [".".join(row["version"].split(".")[:2]) for row in chosen]
    ranks = [family_order.index(family) for family in selected_families]
    report.equal(manifest["schema_version"], 4, "selection_schema", "manifest")
    report.equal(manifest["study_revision"], 3, "selection_revision", "manifest")
    report.equal(manifest["selection_method"], "major_anchors_calendar_greedy_v3", "selection_method", "manifest")
    report.equal(cutoff, "2026-10-17", "selection_frozen_cutoff", "manifest")
    parameters = {
        "requested_count": 30, "first_major": 10, "last_major": 33,
        "oldest_endpoint_version": "10.0", "latest_endpoint_version": "33.7.2",
        "representative_rule": "first_eligible_stable_release_per_family", "optional_count": 5,
        "minimum_calendar_gap_days": 60, "max_optional_families_per_major": 2,
        "objective": "greedy_reduction_in_sum_squared_calendar_gaps",
        "tie_break": ["earlier_utc_calendar_date", "numeric_version"],
        "latest_endpoint_counts_as_optional": False,
    }
    report.equal(manifest["selection_parameters"], parameters, "frozen_selection_parameters", "manifest")
    report.equal(manifest["selected_count"], count, "selected_count_metadata", "manifest")
    majors = sorted({key(row["version"])[0] for row in chosen})
    report.equal(majors, list(range(10, 34)), "complete_major_release_coverage", "selection")
    report.equal(manifest["selected_major_numbers"], majors, "selected_major_metadata", "manifest")
    roles = {row["version"]: "major_anchor" for row in anchors}
    roles[chosen[-1]["version"]] = "latest_endpoint"
    roles.update({step["version"]: "gap_filling_minor" for step in optional_steps})

    def gap_rows(sequence):
        return [{"from_version": a["version"], "to_version": b["version"],
                 "from_date": a["release_date"][:10], "to_date": b["release_date"][:10],
                 "gap_days": (date.fromisoformat(b["release_date"][:10]) -
                              date.fromisoformat(a["release_date"][:10])).days}
                for a, b in zip(sequence, sequence[1:])]

    calendar_gaps = gap_rows(chosen)
    day_gaps = [item["gap_days"] for item in calendar_gaps]
    ordered_gaps = sorted(day_gaps)
    gap_statistics = {"count": len(day_gaps), "minimum_days": min(day_gaps),
                      "median_days": ordered_gaps[len(ordered_gaps) // 2], "maximum_days": max(day_gaps),
                      "mean_days": sum(day_gaps) / len(day_gaps), "total_span_days": sum(day_gaps),
                      "below_declared_minimum_count": sum(gap < 60 for gap in day_gaps)}
    report.equal(gap_statistics["below_declared_minimum_count"], 0, "minimum_calendar_spacing", "all selected gaps")
    report.equal(manifest["calendar_gap_statistics"], gap_statistics, "calendar_gap_statistics", "manifest")
    report.equal([r["version"] for r in manifest["versions"]], [r["version"] for r in chosen],
                 "independent_family_selection", "selected representative versions")
    report.equal(len(set(selected_families)), 30, "distinct_selected_families", "manifest")
    report.equal(manifest["major_minor_families"], selected_families, "family_selection_provenance", "families")
    report.equal(manifest["selected_family_ranks_zero_based"], ranks, "family_selection_provenance", "ranks")
    report.equal(manifest["eligible_major_minor_families"], len(family_order), "family_selection_provenance", "family count")
    report.equal(manifest["selection_catalog_sha256"], digest(inventory_path), "selection_catalog_checksum", "manifest")
    for i, (recorded, original) in enumerate(zip(manifest["versions"], chosen)):
        for field in ("tag", "commit_sha", "release_date", "date_basis"):
            report.equal(recorded[field], original[field], "immutable_release_identity", recorded["version"] + "/" + field)
        report.equal(recorded["family"], selected_families[i], "family_selection_provenance", recorded["version"])
        report.equal(recorded["family_rank_zero_based"], ranks[i], "family_selection_provenance", recorded["version"] + "/rank")
        report.equal(recorded["index"], i + 1, "sequential_sample_index", recorded["version"])
        report.equal(recorded["selection_role"], roles[recorded["version"]], "selection_role", recorded["version"])
        expected_rule = "latest_history_endpoint" if roles[recorded["version"]] == "latest_endpoint" else "first_eligible_stable_release"
        report.equal(recorded["representative_rule"], expected_rule, "representative_release_rule", recorded["version"])
        report.equal(recorded["calendar_gap_days_since_previous"], day_gaps[i - 1] if i else None,
                     "selected_calendar_gap", recorded["version"])
        report.equal(recorded["source_prefixes"], list(SOURCE_PREFIXES), "owned_source_prefixes", recorded["version"])
        between = [] if i == 0 else family_order[ranks[i - 1] + 1:ranks[i]]
        report.equal(recorded["skipped_families_since_previous"], between, "skipped_family_provenance", recorded["version"])
        report.check(re.fullmatch(r"[0-9a-f]{40}", recorded["commit_sha"]) is not None,
                     "immutable_commit_pin", recorded["version"])
        expected_flavour = recorded["version"] + ("-jre" if key(recorded["version"]) >= (23, 1, 0) else "")
        report.equal(recorded["artifact_version"], expected_flavour, "one_jre_variant", recorded["version"])
    evidence = data(root / "data/provenance/family_selection.json")
    for field, expected in {"schema_version": 2, "study_revision": 3,
                             "frozen_cutoff_utc": cutoff, "catalog_path": "data/provenance/tag_inventory.json",
                             "catalog_sha256": digest(inventory_path), "eligible_releases": len(eligible),
                             "eligible_families": len(family_order), "selected_count": count,
                             "selected_family_ranks_zero_based": ranks,
                             "selected_versions": [r["version"] for r in chosen],
                             "selected_unique_families": len(set(selected_families)),
                             "unselected_families": len(family_order) - count,
                             "selection_method": "major_anchors_calendar_greedy_v3",
                             "selection_parameters": parameters, "selected_major_numbers": majors,
                             "calendar_gaps": calendar_gaps, "calendar_gap_statistics": gap_statistics,
                             "calendar_date_basis": manifest["calendar_date_basis"],
                             "rule": manifest["selection_policy"]}.items():
        report.equal(evidence[field], expected, "family_selection_evidence", field)
    expected_anchors = [{"version": row["version"], "family": ".".join(row["version"].split(".")[:2]),
                         "release_date": row["release_date"], "calendar_date": row["release_date"][:10],
                         "selection_role": roles[row["version"]],
                         "rationale": "Fixed latest stable endpoint; not charged to the optional-major budget."
                         if roles[row["version"]] == "latest_endpoint"
                         else "Cover this major's MAJOR.0 milestone with its first eligible stable release."}
                        for row in anchors]
    report.equal(evidence["mandatory_anchors"], expected_anchors, "independent_mandatory_anchors", "major milestones and latest boundary")
    captured_by_version = {row["version"]: row for row in eligible}
    expected_steps = [{"step": i + 1, "version": item["version"], "family": item["family"],
                       "calendar_date": captured_by_version[item["version"]]["release_date"][:10],
                       "between_versions": [item["left"], item["right"]],
                       "original_gap_days": item["left_gap_days"] + item["right_gap_days"],
                       "left_gap_days": item["left_gap_days"], "right_gap_days": item["right_gap_days"],
                       "squared_gap_reduction_days2": item["gain"],
                       "optional_count_for_major_after_selection": item["optional_count_for_major_after_selection"],
                       "feasible_candidate_count": item["feasible_candidate_count"]}
                      for i, item in enumerate(optional_steps)]
    report.equal(evidence["optional_selection_steps"], expected_steps, "independent_calendar_selection_steps", "all candidate gains and constraints")
    anchor_gaps = gap_rows(anchors)
    anchor_minimum = min(item["gap_days"] for item in anchor_gaps)
    for field, expected in {"mandatory_anchor_minimum_gap_days": anchor_minimum,
                             "limiting_anchor_pairs": [item for item in anchor_gaps if item["gap_days"] == anchor_minimum],
                             "ninety_day_floor_feasible_with_fixed_anchors": anchor_minimum >= 90}.items():
        report.equal(evidence["spacing_feasibility"][field], expected, "independent_spacing_feasibility", field)
    expected_catalog = [{
        "family_rank_zero_based": i, "family": family,
        "eligible_versions": [r["version"] for r in groups[family]],
        "first_release_date": min(r["release_date"] for r in groups[family]),
        "representative": representatives[family]["version"],
        "representative_calendar_date": representatives[family]["release_date"][:10],
        "representative_rule": "latest_history_endpoint" if representatives[family]["version"] == "33.7.2" else "first_eligible_stable_release",
        "selected": i in ranks,
        "selection_role": roles.get(representatives[family]["version"]),
    } for i, family in enumerate(family_order)]
    report.equal(evidence["family_catalog"], expected_catalog, "independent_family_catalog", "all eligible families")
    return stable


def audit_instructor_input(root, row, directory, alias_map, provenance, report):
    """Check the scoped input JAR against unchanged bytes in the original artifact."""
    version = row["version"]
    record = data(directory / "instructor_input.json")
    inventory_rows = rows(directory / "instructor_input_classes.csv")
    inventory = {r["binary_class"]: r for r in inventory_rows}
    report.equal(len(inventory_rows), len(inventory), "instructor_input_unique_inventory", version)
    report.equal(set(inventory), set(alias_map), "instructor_input_exact_ownership", version)
    report.equal(record, provenance["instructor_input"], "instructor_input_provenance", version)
    report.equal(record["sha256"], digest(directory / "instructor_input.jar"), "instructor_input_checksum", version)
    report.equal(record["inventory_sha256"], digest(directory / "instructor_input_classes.csv"), "instructor_input_inventory_checksum", version)
    report.equal(record["source_binary_sha256"], row["jar_sha256"], "instructor_input_original_binary", version)
    total_bytes = 0
    with zipfile.ZipFile(root / row["jar_path"]) as original, zipfile.ZipFile(directory / "instructor_input.jar") as scoped:
        expected_entries = {binary.replace(".", "/") + ".class" for binary in alias_map}
        report.equal(set(scoped.namelist()), expected_entries, "instructor_scans_owned_base_entries_only", version)
        report.equal(len(scoped.namelist()), len(expected_entries), "no_duplicate_instructor_jar_entries", version)
        original_counts = Counter(original.namelist())
        for binary in sorted(alias_map):
            name = binary.replace(".", "/") + ".class"
            got = inventory[binary]
            report.equal(original_counts[name], 1, "unique_original_owned_class_entry", version + "/" + binary)
            content, scoped_content = original.read(name), scoped.read(name)
            report.check(scoped_content == content, "instructor_class_bytes_unchanged", version + "/" + binary,
                         hashlib.sha256(scoped_content).hexdigest(), hashlib.sha256(content).hexdigest())
            report.equal(got["class"], alias_map[binary], "instructor_input_alias_identity", version + "/" + binary)
            report.equal(got["jar_entry"], name, "instructor_input_entry_identity", version + "/" + binary)
            report.equal(int(got["bytes"]), len(content), "instructor_input_class_size", version + "/" + binary)
            report.equal(got["class_sha256"], hashlib.sha256(content).hexdigest(), "instructor_input_class_checksum", version + "/" + binary)
            report.equal(scoped.getinfo(name).date_time, (1980, 1, 1, 0, 0, 0), "deterministic_instructor_jar_metadata", version + "/" + binary)
            total_bytes += len(content)
    report.equal(record["class_entries"], len(alias_map), "instructor_input_totals", version + "/classes")
    report.equal(record["class_bytes"], total_bytes, "instructor_input_totals", version + "/bytes")
    command = data(directory / "instructor_command.json")
    for field, value in {"exit_code": 0, "main_class": "CompCalc.MainClass", "instructor_sha256": INSTRUCTOR_SHA256,
                         "input_sha256": record["sha256"]}.items():
        report.equal(command[field], value, "instructor_execution_record", version + "/" + field)
    argv = command["argv"]
    report.check("CompCalc.MainClass" in argv and "-cp" in argv, "original_instructor_main_executed", version)
    executable_classpath = argv[argv.index("-cp") + 1]
    report.check(Path(row["jar_path"]).name not in executable_classpath and "instructor_input.jar" not in executable_classpath,
                 "target_classes_not_on_executable_classpath", version)
    report.equal(data(directory / "supplemental_command.json")["exit_code"], 0, "supplemental_execution_succeeded", version)


def audit_instructor_normalization(directory, nodes, aliases, class_rows, provenance, report):
    """Normalize raw upstream rows independently; do not trust supplemental edges."""
    version = provenance["version"]
    expected_typed, excluded = set(), []
    counts, relation_counts = Counter(), Counter()
    for record in rows(directory / "instructor_raw.csv"):
        relation = record["DependencyType"]
        report.check(relation in RELATIONS, "instructor_raw_relation_allowed", version)
        report.check(int(record["Times"]) > 0, "positive_instructor_occurrence_count", version)
        relation_counts[relation] += 1
        source, target = aliases.get(record["dependeeClass"]), aliases.get(record["dependencyClass"])
        if source is not None and target is not None and source != target:
            expected_typed.add((source, target, relation))
            counts["accepted_raw_typed_rows"] += 1
        else:
            reason = ("both_endpoints_outside_owned_scope" if source is None and target is None
                      else "source_outside_owned_scope" if source is None
                      else "target_outside_owned_scope" if target is None else "self_after_outer_merge")
            counts[reason] += 1
            excluded.append({**record, "reason": reason})
    expected_edges = {(a, b) for a, b, _ in expected_typed}
    observed_typed = {(r["source"], r["target"], r["relation"]) for r in rows(directory / "dependencies_typed.csv")}
    report.equal(observed_typed, expected_typed, "primary_typed_graph_exact_instructor_normalization", version)
    report.equal(set(read_edges(directory / "dependencies.csv")), expected_edges, "primary_graph_exact_instructor_union", version)
    counts.update({"raw_typed_rows": sum(relation_counts.values()), "excluded_raw_typed_rows": len(excluded),
                   "unique_typed_edges": len(expected_typed), "unique_directed_edges": len(expected_edges),
                   "duplicate_normalized_typed_rows": counts["accepted_raw_typed_rows"] - len(expected_typed)})
    observed_counts = {r["metric"]: int(r["value"]) for r in rows(directory / "instructor_normalization_counts.csv")}
    report.equal(observed_counts, dict(counts), "instructor_normalization_counts", version)
    sort_key = lambda r: (r["dependeeClass"], r["dependencyClass"], r["DependencyType"], r["DependencySubtype"], int(r["Times"]))
    report.equal(rows(directory / "instructor_excluded_rows.csv"), sorted(excluded, key=sort_key), "instructor_excluded_rows_accounted", version)
    supplemental_rows = rows(directory / "supplemental_dependencies_typed.csv")
    supplemental_typed = {(r["source"], r["target"], r["relation"]) for r in supplemental_rows}
    supplemental = {(a, b) for a, b, _ in supplemental_typed}
    report.equal(len(supplemental_rows), len(supplemental_typed), "unique_supplemental_typed_edges", version)
    report.check(all(a in nodes and b in nodes and a != b and relation in RELATIONS
                     for a, b, relation in supplemental_typed), "supplemental_graph_internal_scope", version)
    report.equal(set(read_edges(directory / "supplemental_dependencies.csv")), supplemental, "supplemental_typed_union", version)
    annotations = {r["class"] for r in class_rows if r["kind"] == "annotation"}
    isolates = set(nodes) - {n for edge in expected_edges for n in edge}
    expected_comparison = {
        "normalization_counts": dict(counts), "raw_relation_counts": dict(relation_counts),
        "relation_counts": dict(Counter(r for _, _, r in expected_typed)),
        "annotation_classes": len(annotations), "annotation_isolated_classes": len(annotations & isolates),
        "annotation_target_edges": sum(b in annotations for a, b in expected_edges),
        "annotation_source_edges": sum(a in annotations for a, b in expected_edges),
        "supplemental_dependencies": len(supplemental),
        "supplemental_annotation_target_edges": sum(b in annotations for a, b in supplemental),
        "supplemental_only_edges": len(supplemental - expected_edges),
        "supplemental_only_annotation_target_edges": sum(b in annotations for a, b in supplemental - expected_edges),
        "instructor_only_edges": len(expected_edges - supplemental), "shared_edges": len(expected_edges & supplemental),
    }
    comparison = data(directory / "extractor_comparison.json")
    for field, value in expected_comparison.items():
        report.equal(comparison[field], value, "independent_extractor_comparison", version + "/" + field)
        report.equal(provenance[field], value, "extractor_comparison_provenance", version + "/" + field)
    supplemental_relations = defaultdict(set)
    for a, b, relation in supplemental_typed:
        supplemental_relations[a, b].add(relation)
    for name, difference in (("supplemental_only_edges.csv", supplemental - expected_edges),
                             ("instructor_only_edges.csv", expected_edges - supplemental)):
        expected_rows = [{"source": a, "target": b, "target_is_annotation": str(b in annotations),
                          "supplemental_relations": ";".join(sorted(supplemental_relations[a, b]))}
                         for a, b in sorted(difference)]
        report.equal(rows(directory / name), expected_rows, "extractor_difference_edges", version + "/" + name)
    return supplemental_typed


def audit_pilot(root, result_root, graph_root, versions, config, run, calibration, report):
    """Recalculate every stored pilot SSE and the predeclared elbow decision."""
    pilot_root = result_root / "pilot"
    pilot = data(pilot_root / "pilot.json")
    selected_version = versions[len(versions) // 2]["version"]
    directory = graph_root / selected_version
    nodes = [r["class"] for r in rows(directory / "classes.csv")]
    edges = read_edges(directory / "dependencies.csv")
    feature_universe = data(graph_root / "feature_universe.json")
    coordinate_hash = hashlib.sha256(("\n".join(feature_universe) + "\n").encode()).hexdigest()
    report.equal(pilot["version"], selected_version, "pilot_preselected_middle_release", "pilot")
    report.equal(pilot["k_sweep"], "one_pilot_only", "one_pilot_k_calibration_only", "pilot")
    report.equal(config["kmeans"]["k_rule"], "ceil(n_full * pilot_k / pilot_n)", "frozen_k_rule", "configuration")
    report.equal(pilot["frozen_configuration_sha256"], run["config_sha256"], "pilot_and_final_same_policy", "pilot")
    for field, expected in {
        "schema_version": 2, "pilot_version": selected_version, "pilot_n": len(nodes),
        "rule": config["kmeans"]["k_rule"], "quality_scores_used_for_selection": False,
        "config_sha256": digest(root / "config/analysis.json"),
        "manifest_sha256": digest(root / "config/versions.json"),
        "graph_sha256": digest(directory / "dependencies.csv"),
        "classes_sha256": digest(directory / "classes.csv"),
        "feature_universe_sha256": digest(graph_root / "feature_universe.json"),
    }.items():
        report.equal(calibration[field], expected, "pilot_calibration_provenance", field)
    report.equal(pilot["k_calibration"], calibration, "pilot_embedded_calibration", "pilot")
    report.equal(run["k_calibration_sha256"], digest(pilot_root / "k_calibration.json"), "final_run_calibration_checksum", "run")
    report.equal(run["pilot_n"], calibration["pilot_n"], "final_run_calibration_identity", "pilot_n")
    report.equal(run["pilot_k"], calibration["pilot_k"], "final_run_calibration_identity", "pilot_k")
    candidates = sorted({min(int(k), len(nodes)) for k in config["pilot"]["k_candidates"]})
    curve = rows(pilot_root / "k_inertia_curve.csv")
    curve_index = {int(r["k"]): r for r in curve}
    report.equal(len(curve), len(candidates), "pilot_candidate_count", "curve")
    report.equal(sorted(curve_index), candidates, "predeclared_pilot_candidates", "curve")
    report.equal({p.stem for p in (pilot_root / "k_candidates").glob("k*.csv")},
                 {f"k{k}" for k in candidates}, "complete_pilot_candidate_partition_inventory", "candidate files")
    fits = {}
    for k in candidates:
        assignment = read_partition(pilot_root / f"k_candidates/k{k}.csv", nodes, report)
        metadata = data(pilot_root / f"k_candidates/k{k}_run.json")
        fits[k] = assignment
        context = f"pilot/k={k}"
        inertia = independent_inertia(nodes, edges, assignment)
        report.numeric(metadata["inertia"], inertia, "independent_pilot_candidate_inertia", context + "/run")
        report.numeric(curve_index[k]["inertia"], inertia, "independent_pilot_candidate_inertia", context + "/curve")
        report.equal(metadata["requested_k"], k, "pilot_requested_k", context)
        report.equal(metadata["actual_k"], len(set(assignment.values())), "pilot_actual_k", context)
        report.numeric(curve_index[k]["actual_k"], metadata["actual_k"], "pilot_curve_fit_metadata", context + "/actual_k")
        report.numeric(curve_index[k]["iterations"], metadata["iterations"], "pilot_curve_fit_metadata", context + "/iterations")
        for field in ("random_state", "n_init", "max_iter", "algorithm"):
            report.equal(metadata[field], config["kmeans"][field], "frozen_pilot_kmeans_parameters", context + "/" + field)
        report.equal(metadata["feature_rows"], len(nodes), "pilot_features", context + "/rows")
        report.equal(metadata["feature_columns"], 2 * len(feature_universe), "pilot_features", context + "/columns")
        report.equal(metadata["feature_universe_sha256"], coordinate_hash, "pilot_features", context + "/coordinate identities")
        report.equal(metadata["feature_nonzeros"], 2 * (len(nodes) + len(edges)), "pilot_features", context + "/nonzeros")
    first, last = curve_index[candidates[0]], curve_index[candidates[-1]]
    span_k = candidates[-1] - candidates[0]
    span_inertia = float(first["inertia"]) - float(last["inertia"])
    points = []
    for k in candidates:
        inertia = float(curve_index[k]["inertia"])
        x = (k - candidates[0]) / span_k if span_k else 0.0
        y = (inertia - float(last["inertia"])) / span_inertia if span_inertia > 0 else None
        gap = 1 - x - y if span_k and span_inertia > 0 else 0.0
        points.append({"k": k, "inertia": inertia, "normalized_k": x,
                       "normalized_inertia": y, "chord_gap": gap})
        for field in ("normalized_k", "normalized_inertia", "chord_gap"):
            report.numeric(curve_index[k][field], points[-1][field], "independent_elbow_geometry", f"k={k}/{field}")
    interior = points[1:-1]
    best = sorted(interior, key=lambda p: (-p["chord_gap"], p["k"]))[0] if interior else None
    minimum = config["pilot"]["minimum_elbow_gap"]
    fallback = config["pilot"]["fallback_k_if_no_clear_elbow"]
    clear = bool(best and best["chord_gap"] >= minimum and span_inertia > 0)
    chosen_k = best["k"] if clear else sorted(candidates, key=lambda k: (abs(k - fallback), k))[0]
    expected_selection = {
        "selected_k": chosen_k, "clear_elbow": clear,
        "reason": "maximum_normalized_chord_gap" if clear else "predeclared_fallback_no_clear_elbow",
        "maximum_interior_gap": best["chord_gap"] if best else 0.0,
        "minimum_gap": minimum, "fallback_requested_k": fallback,
        "nonmonotone_steps": sum(b["inertia"] > a["inertia"] for a, b in zip(points, points[1:])),
    }
    selection = calibration["selection"]
    for field, expected in expected_selection.items():
        if isinstance(expected, (str, bool)):
            report.equal(selection[field], expected, "independent_elbow_decision", field)
        else:
            report.numeric(selection[field], expected, "independent_elbow_decision", field)
    report.terms(selection["curve"], points, "pilot/calibration_curve")
    report.equal(calibration["pilot_k"], chosen_k, "independent_calibrated_k", "pilot")
    report.numeric(calibration["target_mean_class_count"], len(nodes) / chosen_k, "pilot_target_granularity", "pilot")
    report.equal(read_partition(pilot_root / "kmeans.csv", nodes, report), fits[chosen_k], "selected_pilot_partition_is_chosen_fit", "pilot")
    acdc_trials = [r for r in pilot["trials"] if r["algorithm"] == "ACDC"]
    report.equal([r["max_subgraph_size"] for r in acdc_trials], config["pilot"]["acdc_max_subgraph_sizes"], "pilot_acdc_inventory", "pilot")
    report.equal([r["algorithm"] for r in pilot["trials"]].count("kmeans"), 1, "one_selected_k_pilot_summary", "pilot")
    default_acdc_k = None
    for trial in pilot["trials"]:
        filename = f"acdc_l{trial['max_subgraph_size']}.csv" if trial["algorithm"] == "ACDC" else "kmeans.csv"
        assignment = read_partition(pilot_root / filename, nodes, report)
        quality = independent_quality(nodes, edges, assignment)
        report.flat_metrics(trial["metrics"], quality, "pilot/" + filename)
        if trial["algorithm"] == "ACDC" and trial["max_subgraph_size"] == config["acdc"]["max_subgraph_size"]:
            default_acdc_k = len(set(assignment.values()))
    diagnostic = pilot["matched_acdc_k_diagnostic"]
    if config["pilot"]["matched_acdc_k_diagnostic"]:
        report.equal(diagnostic["used_for_k_selection"], False, "matched_k_is_diagnostic_only", "pilot")
        report.equal(diagnostic["k"], default_acdc_k, "matched_k_acdc_granularity", "pilot")
        assignment = read_partition(pilot_root / "kmeans_matched_acdc_k.csv", nodes, report)
        report.equal(diagnostic["run"]["requested_k"], default_acdc_k, "matched_k_fit_identity", "pilot")
        report.numeric(diagnostic["run"]["inertia"], independent_inertia(nodes, edges, assignment), "independent_matched_k_inertia", "pilot")
        report.flat_metrics(diagnostic["metrics"], independent_quality(nodes, edges, assignment), "pilot/matched_acdc_k")


def audit_ai(root, result_root, graph_root, versions, config, report):
    """Independently check the completed recorded AI assignment and evaluation.

    Content hashes attest to preserved evidence. They cannot establish what the
    model privately knew or prove its process declarations independently.
    """
    directory = result_root / "ai"
    record = data(directory / "experiment.json")
    selected = versions[-1]
    version = selected["version"]
    graph = graph_root / version
    report.equal(record["version"], version, "ai_latest_selected_version", "experiment")
    report.equal(record["study_revision"], "v2_instructor_graph_distinct_families", "ai_preserved_experiment_revision", "experiment")
    report.equal(record["schema_version"], 2, "ai_revision_schema", "experiment")

    def repo_file(relative):
        value = Path(relative)
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("AI provenance files must be relative paths within the repository")
        return root / value

    report.equal(digest(repo_file(record["prompt_file"])), record["prompt_sha256"], "ai_preserved_prompt_checksum", "primary prompt")
    expected_names = {"classes.csv", "dependencies.csv", "package_counts.json", "package_dependencies.csv", "package_documentation.txt"}
    report.equal({Path(item["path"]).name for item in record["input_files"]}, expected_names, "ai_exact_input_inventory", "experiment")
    report.equal(len(record["input_files"]), len(expected_names), "ai_unique_input_inventory", "experiment")
    for item in record["input_files"]:
        path = repo_file(item["path"])
        report.equal(path.resolve(), (directory / "inputs" / path.name).resolve(), "ai_evidence_path_identity", path.name)
        report.equal(digest(path), item["sha256"], "ai_input_checksum", item["path"])
        report.equal(path.stat().st_size, item["bytes"], "ai_input_size", item["path"])
    for item in record["additional_prompt_files"]:
        report.equal(digest(repo_file(item["path"])), item["sha256"], "ai_additional_prompt_checksum", item["path"])
    source_provenance_path = directory / "source_graph_provenance.json"
    report.equal(record["input_provenance"]["graph_provenance_sha256"], digest(source_provenance_path),
                 "ai_preserved_source_graph_provenance_checksum", version)
    source_provenance = data(source_provenance_path)
    report.equal(source_provenance["version"], version, "ai_preserved_source_graph_version", version)
    report.equal(record["input_provenance"]["sources_jar_sha256"], selected["sources_sha256"], "ai_source_provenance_checksum", version)
    for filename in ("classes.csv", "dependencies.csv"):
        report.equal(digest(directory / "inputs" / filename), digest(graph / filename), "ai_uses_same_primary_graph_evidence", filename)
        provenance_key = "classes_sha256" if filename == "classes.csv" else "graph_sha256"
        report.equal(source_provenance[provenance_key], digest(directory / "inputs" / filename),
                     "ai_preserved_source_provenance_matches_original_input", filename)
    class_rows = rows(graph / "classes.csv")
    nodes = {r["class"] for r in class_rows}
    edges = read_edges(graph / "dependencies.csv")
    packages = {r["class"]: r["package"] for r in class_rows}
    report.equal(data(directory / "inputs/package_counts.json"), dict(Counter(packages.values())), "independent_ai_package_counts", version)
    expected_package_edges = Counter((packages[a], packages[b]) for a, b in edges)
    package_rows = rows(directory / "inputs/package_dependencies.csv")
    observed_package_edges = {(r["source_package"], r["target_package"]): int(r["dependencies"]) for r in package_rows}
    report.equal(len(package_rows), len(observed_package_edges), "ai_unique_package_dependency_rows", version)
    report.equal(observed_package_edges, dict(expected_package_edges), "independent_ai_package_dependencies", version)
    with zipfile.ZipFile(root / selected["sources_path"]) as archive:
        available = set(archive.namelist())
        documentation = []
        for package in sorted(set(packages.values())):
            filename = package.replace(".", "/") + "/package-info.java"
            if filename in available:
                documentation.append(f"===== {filename} =====\n" + archive.read(filename).decode("utf-8") + "\n")
    report.equal((directory / "inputs/package_documentation.txt").read_text(encoding="utf-8"), "\n".join(documentation),
                 "ai_package_documentation_from_matching_source_archive", version)
    report.equal(repo_file(record["assignment_file"]).resolve(), (directory / "assignment.csv").resolve(), "ai_assignment_path_identity", version)
    assignment_rows = rows(directory / "assignment.csv")
    assignment = {r["class"]: r["cluster"] for r in assignment_rows}
    report.equal(len(assignment_rows), len(assignment), "ai_unique_class_membership", version)
    report.equal(set(assignment), nodes, "ai_complete_internal_class_coverage", version)
    report.check(all(assignment.values()), "ai_nonempty_cluster_labels", version)
    architecture = data(directory / "architecture.json")
    report.equal(architecture["subject"]["release"], version, "ai_architecture_target_release", version)
    declared = {r["id"]: r["class_count"] for r in architecture["modules"]}
    report.equal(len(architecture["modules"]), len(declared), "ai_unique_module_identifiers", version)
    report.equal(declared, dict(Counter(assignment.values())), "ai_declared_module_counts_match_membership", version)
    evaluation = data(directory / "evaluation.json")
    report.equal(evaluation["version"], version, "ai_evaluation_version", version)
    report.equal(evaluation["study_revision"], config["study_revision"], "ai_current_evaluation_revision", version)
    report.equal(evaluation["source_experiment_revision"], record["study_revision"], "ai_evaluation_preserves_source_revision", version)
    report.equal(evaluation["evaluation_of_preserved_assignment"], True, "ai_reuse_declared", version)
    report.equal(evaluation["config_sha256"], digest(root / "config/analysis.json"), "ai_evaluation_config_checksum", version)
    report.equal(evaluation["manifest_sha256"], digest(root / "config/versions.json"), "ai_evaluation_sample_checksum", version)
    report.equal(repo_file(evaluation["source_graph_provenance_file"]).resolve(), source_provenance_path.resolve(),
                 "ai_source_graph_provenance_path_identity", version)
    report.equal(evaluation["source_graph_provenance_sha256"], digest(source_provenance_path),
                 "ai_evaluation_source_provenance_checksum", version)
    report.equal(evaluation["current_graph_provenance_sha256"], digest(graph / "provenance.json"),
                 "ai_evaluation_current_provenance_checksum", version)
    report.equal(evaluation["status"], "passed", "ai_evaluation_completed", version)
    report.equal(evaluation["classes_assigned_exactly_once"], len(nodes), "ai_evaluation_coverage", version)
    report.equal(evaluation["modules"], len(declared), "ai_evaluation_module_count", version)
    report.equal(evaluation["external_or_invented_classes"], len(set(assignment) - nodes), "ai_external_class_count", version)
    output_names = {"initial_hypothesis.md", "assignment.csv", "architecture.json", "response.md", "activity.json"}
    report.equal(set(evaluation["output_sha256"]), output_names, "ai_output_checksum_inventory", version)
    for filename, expected in evaluation["output_sha256"].items():
        report.equal(digest(directory / filename), expected, "ai_preserved_output_checksum", filename)
    retained = {r["class"] for r in rows(result_root / "versions" / version / "retained_classes.csv")}
    retained_edges = [(a, b) for a, b in edges if a in retained and b in retained]
    quality_by_scope = {}
    for scope, scope_nodes, scope_edges, metric_file in (("full", nodes, edges, "metrics.json"),
                                                       ("retained", retained, retained_edges, "retained_metrics.json")):
        projected = {n: assignment[n] for n in scope_nodes}
        quality = independent_quality(scope_nodes, scope_edges, projected)
        quality_by_scope[scope] = quality
        observed = data(directory / metric_file)
        report.flat_metrics(observed, quality, f"ai/{scope}/JSON")
        summaries = rows(directory / f"quality_{scope}/metrics_summary.csv")
        report.equal(len(summaries), 1, "ai_quality_summary_count", scope)
        report.flat_metrics(summaries[0], quality, f"ai/{scope}/summary")
        for table in ("per_cluster", "per_pair"):
            report.terms(observed[table], quality[table], f"ai/{scope}/JSON/{table}")
            report.terms(rows(directory / f"quality_{scope}/{table}.csv"), quality[table], f"ai/{scope}/CSV/{table}")
    comparisons = rows(directory / "comparisons.csv")
    details = data(directory / "partition_comparisons.json")
    comparison_index = {r["condition"]: r for r in comparisons}
    detail_index = {r["comparison"]["condition"]: r for r in details["comparisons"]}
    report.equal(details["version"], version, "ai_comparison_version", version)
    report.equal(set(comparison_index), {"A1", "A2", "A3", "A4"}, "ai_comparison_inventory", version)
    report.equal(set(detail_index), set(comparison_index), "ai_detailed_comparison_inventory", version)
    report.equal(len(comparisons), 4, "unique_ai_comparisons", "CSV")
    report.equal(len(details["comparisons"]), 4, "unique_ai_comparisons", "JSON")
    for condition in ("A1", "A2", "A3", "A4"):
        filtered = condition in ("A2", "A4")
        scope = "retained" if filtered else "full"
        current_nodes, current_edges = (retained, retained_edges) if filtered else (nodes, edges)
        baseline = read_partition(result_root / "versions" / version / f"{condition}.csv", current_nodes, report)
        forward = independent_mojofm(assignment, baseline, current_nodes)
        reverse = independent_mojofm(baseline, assignment, current_nodes)
        expected = {
            "condition": condition, "graph": scope, "n_nodes": len(current_nodes), "n_edges": len(current_edges),
            "baseline_mq": independent_quality(current_nodes, current_edges, baseline)["mq"],
            "ai_mq": quality_by_scope[scope]["mq"],
            "mojofm_ai_to_baseline": forward["score"], "mojofm_baseline_to_ai": reverse["score"],
            "mojo_distance_ai_to_baseline": forward["distance"], "mojo_distance_baseline_to_ai": reverse["distance"],
            "mojo_max_distance_ai_to_baseline": forward["max_distance"], "mojo_max_distance_baseline_to_ai": reverse["max_distance"],
            "node_universe_sha256": hashlib.sha256(("\n".join(sorted(current_nodes)) + "\n").encode()).hexdigest(),
        }
        report.equal(set(comparison_index[condition]), set(expected), "ai_comparison_exact_schema", f"{condition}/CSV")
        report.equal(set(detail_index[condition]["comparison"]), set(expected), "ai_comparison_exact_schema", f"{condition}/JSON")
        for field, value in expected.items():
            for got, label in ((comparison_index[condition], "CSV"), (detail_index[condition]["comparison"], "JSON")):
                context = f"ai/{condition}/{field}/{label}"
                if isinstance(value, str):
                    report.equal(got[field], value, "ai_comparison_scope_and_identity", context)
                else:
                    report.numeric(got[field], value, "independent_ai_comparison", context)
        for direction, want in (("ai_to_baseline", forward), ("baseline_to_ai", reverse)):
            got = detail_index[condition][direction]
            for field, value in want.items():
                context = f"ai/{condition}/{direction}/{field}"
                if isinstance(value, (str, bool)):
                    report.equal(got[field], value, "independent_ai_mojofm_terms", context)
                else:
                    report.numeric(got[field], value, "independent_ai_mojofm_terms", context)
    report.ai_evidence = {"version": version, "classes": len(nodes), "modules": len(declared),
                          "comparison_conditions": sorted(comparison_index),
                          "scope": "preserved inputs/outputs, coverage, lecture metrics and bidirectional partition agreement"}


def audit(root: Path, result_root: Path, graph_root: Path, *, include_ai: bool = True) -> Audit:
    report = Audit()
    # A hand-derived identity guards the independent audit's own arithmetic.
    example = independent_quality("abcd", [("a", "b"), ("b", "a"), ("c", "d"),
                                          ("d", "c"), ("b", "c")],
                                  {"a": "x", "b": "x", "c": "y", "d": "y"})
    report.numeric(example["mq"], 7 / 8, "independent_hand_example", "two complete directed pairs and one cross edge")
    reference = {n: str(i) for i, group in enumerate(("abc", "def", "gh")) for n in group}
    for groups, distance, score in [([*"abcdefgh"], 5, 0), (["abc", "def", "gh"], 0, 100),
                                     (["abc", "defgh"], 2, 60), (["a", "bcg", "defh"], 3, 40)]:
        source = {n: str(i) for i, group in enumerate(groups) for n in group}
        check = independent_mojofm(source, reference, reference)
        report.equal(check["distance"], distance, "independent_mojo_lecture_example", str(groups))
        report.equal(check["max_distance"], 5, "independent_mojo_lecture_normalizer", str(groups))
        report.numeric(check["score"], score, "independent_mojo_lecture_score", str(groups))
    manifest, config = data(root / "config/versions.json"), data(root / "config/analysis.json")
    versions = manifest["versions"]
    version_ids = [r["version"] for r in versions]
    report.equal(manifest["repository"], "google/guava", "subject", "manifest")
    report.equal(len(versions), 30, "release_count", "manifest")
    report.equal(len(set(version_ids)), 30, "unique_release_count", "manifest")
    stable = audit_family_selection(root, manifest, report)
    stable_ids = [r["version"] for r in stable]
    for i, row in enumerate(versions):
        version = row["version"]
        report.check(re.fullmatch(r"\d+\.\d+(?:\.\d+)?", version) is not None,
                     "stable_release_only", version)
        artifact = row["artifact_version"]
        report.check(artifact == version or artifact == version + "-jre", "one_jre_variant", version, artifact)
        if i:
            previous = versions[i - 1]
            report.check(previous["release_date"] < row["release_date"], "chronological_sampling", version)
            start, stop = stable_ids.index(previous["version"]), stable_ids.index(version)
            skipped = stable_ids[start + 1:stop]
            report.equal(row["skipped_stable_since_previous"], skipped, "skipped_release_provenance", version)
        else:
            report.equal(row["skipped_stable_since_previous"], [], "skipped_release_provenance", version)
    report.equal(set(config["relation_types"]), RELATIONS, "frozen_policy", "seven relations")
    report.equal(config["comparison_metrics"], ["MoJoFM_source_to_reference", "MoJoFM_reverse"],
                 "frozen_policy", "directional partition comparison metrics")
    for key, expected in {"subject": "google/guava", "relation_weight": 1,
                          "graph": "binary_directed_union_no_self_loops", "merge_inner_and_anonymous": True,
                          "multi_release_policy": "base_class_entries_only", "singleton_cohesion": 0,
                          "empty_partition_metrics": 0, "schema_version": 3,
                          "study_revision": "v3_spaced_releases_no_ari"}.items():
        report.equal(config[key], expected, "frozen_policy", key)
    instructor_path = root / "third_party/dependency_extractor/DependencyExtractor.jar"
    instructor_source = data(root / "third_party/dependency_extractor/source.json")
    report.equal(digest(instructor_path), INSTRUCTOR_SHA256, "unmodified_instructor_tool", "supplied JAR")
    report.equal(instructor_source["jar_sha256"], INSTRUCTOR_SHA256, "instructor_tool_provenance", "supplied JAR")
    with zipfile.ZipFile(instructor_path) as instructor_archive:
        for filename, expected in instructor_source["bundled_libraries"].items():
            content = instructor_archive.read(filename)
            report.equal(hashlib.sha256(content).hexdigest(), expected["sha256"], "unmodified_instructor_nested_library", filename)
            report.equal(len(content), expected["bytes"], "instructor_library_size", filename)
    calibration = data(result_root / "pilot/k_calibration.json")
    metric_rows = rows(result_root / "metrics.csv")
    size_rows = rows(result_root / "sizes.csv")
    common_rows = rows(result_root / "same_graph_comparisons.csv")
    temporal_rows = rows(result_root / "evolution.csv")
    runtime_rows = rows(result_root / "runtimes.csv")
    comparison_rows = rows(result_root / "partition_comparisons.csv")
    expected_comparison_count = 4 * len(versions) + 2 * (len(versions) - 1)
    for filename, actual, expected in [("metrics.csv", metric_rows, 120), ("sizes.csv", size_rows, 30),
                                       ("same_graph_comparisons.csv", common_rows, 60),
                                       ("evolution.csv", temporal_rows, 29), ("runtimes.csv", runtime_rows, 180),
                                       ("partition_comparisons.csv", comparison_rows, expected_comparison_count)]:
        report.equal(len(actual), expected, "aggregate_row_count", filename)
    metric_index = {(r["version"], r["condition"]): r for r in metric_rows}
    report.equal(len(metric_index), 120, "one_final_architecture_per_condition", "metrics.csv")
    report.equal(set(metric_index), {(v, c) for v in version_ids for c in ("A1", "A2", "A3", "A4")},
                 "exact_condition_inventory", "metrics.csv")
    size_index = {r["version"]: r for r in size_rows}
    common_index = {(r["version"], r["full_condition"]): r for r in common_rows}
    runtime_index = {(r["version"], r["stage"]): r for r in runtime_rows}
    comparison_key = lambda r: (r["version"], r["scope"], r["source_condition"], r["reference_condition"], r["previous_version"])
    comparison_index = {comparison_key(r): r for r in comparison_rows}
    report.equal(len(comparison_index), expected_comparison_count, "unique_partition_comparisons", "partition_comparisons.csv")
    expected_comparison_keys = set()
    report.equal(set(size_index), set(version_ids), "size_inventory", "sizes.csv")
    report.equal(set(common_index), {(v, c) for v in version_ids for c in ("A1", "A3")},
                 "same_graph_inventory", "same_graph_comparisons.csv")
    report.equal(len(list((result_root / "versions").glob("*/A[1-4].csv"))), 120,
                 "final_partition_file_inventory", "results/versions")
    report.equal(len(runtime_index), 180, "runtime_inventory", "runtimes.csv")
    report.equal(set(runtime_index), {(v, c) for v in version_ids for c in ("A1", "A2", "A3", "A4", "extraction", "UE")},
                 "runtime_inventory", "runtimes.csv keys")
    for row in runtime_rows:
        report.check(math.isfinite(float(row["seconds"])) and float(row["seconds"]) >= 0,
                     "finite_nonnegative_runtime", f"{row['version']}/{row['stage']}")
    universe = data(graph_root / "feature_universe.json")
    universe_hash = hashlib.sha256(("\n".join(universe) + "\n").encode()).hexdigest()
    report.equal(universe, sorted(set(universe)), "fixed_feature_schema", "unique sorted universe")
    observed_universe = set()
    previous = None
    for row in versions:
        version = row["version"]
        directory, output = graph_root / version, result_root / "versions" / version
        class_rows = rows(directory / "classes.csv")
        nodes = [r["class"] for r in class_rows]
        node_set = set(nodes)
        edges = read_edges(directory / "dependencies.csv")
        edge_set = set(edges)
        observed_universe.update(nodes)
        report.equal(len(nodes), len(node_set), "unique_graph_nodes", version)
        report.equal(len(edges), len(edge_set), "binary_edges", version)
        report.check(all(a in node_set and b in node_set and a != b for a, b in edges),
                     "internal_only_loop_free_edges", version)
        report.check(all(n.startswith(OWNED_PREFIXES) for n in nodes),
                     "owned_outermost_class_scope", version)
        report.equal(read_rsf(directory / "full.rsf", "call"), edges, "graph_rsf_matches_csv", version)
        typed = rows(directory / "dependencies_typed.csv")
        report.equal({(r["source"], r["target"]) for r in typed}, edge_set, "relation_union_equals_graph", version)
        report.check({r["relation"] for r in typed} <= RELATIONS, "only_seven_allowed_relations", version)
        report.equal(len(typed), len({tuple(r.values()) for r in typed}), "unique_typed_edges", version)
        provenance = data(directory / "provenance.json")
        report.equal(provenance["schema_version"], 2, "instructor_graph_schema", version)
        report.equal(provenance["primary_extractor"], "instructor DependencyExtractor (unmodified CompCalc.MainClass)",
                     "single_primary_extractor_policy", version)
        report.equal(provenance["instructor_jar_sha256"], INSTRUCTOR_SHA256, "single_primary_extractor_policy", version + "/JAR")
        report.equal(provenance["adapter_sha256"], digest(root / "src/evolution/extraction.py"), "single_adapter_policy", version)
        report.equal(provenance["toolchain_sha256"], digest(root / "src/evolution/toolchain.py"), "single_toolchain_policy", version)
        report.equal(provenance["supplemental_extractor_sha256"], digest(root / "java/DependencyExtractor.java"),
                     "single_supplemental_extractor_policy", version)
        report.equal(provenance["owned_namespace_prefixes"], [p[:-1] for p in OWNED_PREFIXES], "owned_namespace_policy", version)
        report.equal(provenance["classes_sha256"], digest(directory / "classes.csv"), "graph_checksum", version + "/classes")
        report.equal(provenance["graph_sha256"], digest(directory / "dependencies.csv"), "graph_checksum", version + "/dependencies")
        report.equal(provenance["extractor_sha256"], digest(root / "java/DependencyExtractor.java"), "single_extractor_policy", version)
        for field, filename in (("typed_graph_sha256", "dependencies_typed.csv"), ("instructor_raw_sha256", "instructor_raw.csv"),
                                ("member_graph_sha256", "member_dependencies.csv")):
            report.equal(provenance[field], digest(directory / filename), "graph_checksum", version + "/" + filename)
        for key, value in (("version", version), ("tag", row["tag"]), ("commit_sha", row["commit_sha"]),
                           ("date", row["release_date"]), ("binary_sha256", row["jar_sha256"]),
                           ("sources_sha256", row["sources_sha256"]), ("pom_sha256", row["pom_sha256"])):
            report.equal(provenance[key], value, "extraction_provenance", version + "/" + key)
        for kind in ("jar", "sources", "pom"):
            report.equal(digest(root / row[f"{kind}_path"]), row[f"{kind}_sha256"], "artifact_sha256", f"{version}/{kind}")
        aliases = rows(directory / "class_aliases.csv")
        alias_map = {r["binary_class"]: r["class"] for r in aliases}
        report.equal(len(aliases), len(alias_map), "unique_binary_alias", version)
        report.equal(set(alias_map.values()), node_set, "every_binary_merged_to_owned_node", version)
        report.check(all(r["binary_class"] == r["class"] or r["binary_class"].startswith(r["class"] + "$")
                         for r in aliases), "guava_nested_alias_reconciliation", version)
        report.check(all(alias_map.get(n) == n for n in nodes), "canonical_outer_aliases_are_fixed_points", version)
        alias_counts = Counter(alias_map.values())
        for r in class_rows:
            report.equal(int(r["raw_binary_classes"]), alias_counts[r["class"]], "merged_class_member_counts", version + "/" + r["class"])
        with zipfile.ZipFile(root / row["sources_path"]) as source_archive:
            source_names = set(source_archive.namelist())
        report.check(all(r["source_file"] in source_names and r["source_file"].startswith(SOURCE_PREFIXES) for r in aliases),
                     "source_ownership_in_same_version", version)
        excluded = rows(directory / "excluded_classes.csv")
        excluded_names = {r["binary_class"] for r in excluded}
        with zipfile.ZipFile(root / row["jar_path"]) as archive:
            base_classes = {n[:-6].replace("/", ".") for n in archive.namelist() if n.endswith(".class")
                            and not n.startswith("META-INF/versions/") and not n.endswith("package-info.class")
                            and not n.endswith("module-info.class")}
        report.equal(set(alias_map) | excluded_names, base_classes, "all_jar_classes_accounted_for", version)
        report.check(not set(alias_map) & excluded_names, "excluded_classes_never_analyzed", version)
        report.equal(len(aliases) - len(nodes), provenance["merged_binary_classes"], "merged_count_provenance", version)
        audit_instructor_input(root, row, directory, alias_map, provenance, report)
        supplemental_typed = audit_instructor_normalization(directory, node_set, alias_map, class_rows, provenance, report)
        member_rows = rows(directory / "member_dependencies.csv")
        report.equal(len(member_rows), len({(r["source_member"], r["target_member"]) for r in member_rows}), "unique_member_references", version)
        supplemental_edges = {(a, b) for a, b, _ in supplemental_typed}
        report.check(all((r["source_class"], r["target_class"]) in supplemental_edges for r in member_rows),
                     "member_edges_within_supplemental_graph", version)
        report.check(all(r["source_class"] in node_set and r["target_class"] in node_set
                         and r["source_class"] != r["target_class"] for r in member_rows),
                     "ue_member_evidence_internal_and_interclass", version)
        report.check(all((r["source_class"], r["target_class"],
                          "METHOD_CALL" if r["target_member"].split("#", 1)[1].startswith("M:") else "FIELD_REFERENCE")
                         in supplemental_typed for r in member_rows), "ue_member_relation_evidence", version)
        report.check(all(alias_map.get(r[side + "_member"].split("#")[0]) == r[side + "_class"]
                         for r in member_rows for side in ("source", "target")), "member_identity_survives_outer_merge", version)
        ue = data(output / "ue.json")
        report.numeric(ue["usage_threshold"], config["omnipresent"]["usage_threshold"], "frozen_ue_thresholds", version)
        report.numeric(ue["cardinality_threshold"], config["omnipresent"]["cardinality_threshold"], "frozen_ue_thresholds", version)
        expected_ue = independent_ue(nodes, member_rows, ue["usage_threshold"], ue["cardinality_threshold"])
        expected_removed = {n for n, score in expected_ue.items() if score["omnipresent"]}
        report.equal(set(ue["removed_classes"]), expected_removed, "exact_rational_ue_decisions", version)
        observed_scores = {r["class_name"]: r for r in ue["scores"]}
        report.equal(set(observed_scores), node_set, "complete_ue_score_population", version)
        for node, expected_score in expected_ue.items():
            for key, value in expected_score.items():
                report.numeric(observed_scores[node][key], value, "independent_ue_score", f"{version}/{node}/{key}")
        retained = node_set - expected_removed
        filtered_edges = [(a, b) for a, b in edges if a in retained and b in retained]
        report.equal({r["class"] for r in rows(output / "retained_classes.csv")}, retained, "retained_class_population", version)
        report.equal(read_rsf(output / "filtered.rsf", "call"), filtered_edges, "filtered_graph_is_induced", version)
        expected_sizes = {"classes": len(nodes), "dependencies": len(edges), "raw_binary_classes": len(aliases),
                          "merged_binary_classes": len(aliases) - len(nodes), "excluded_binary_classes": len(excluded),
                          "unique_member_edges": len(member_rows), "omnipresent_classes": len(expected_removed),
                          "retained_classes": len(retained), "retained_dependencies": len(filtered_edges),
                          "isolated_classes": len(node_set - {n for e in edges for n in e}),
                          "edge_retention_fraction": len(filtered_edges) / len(edges) if edges else 1.0}
        for key, value in expected_sizes.items():
            report.numeric(size_index[version][key], value, "size_aggregate_matches_evidence", version + "/" + key)
        report.equal(size_index[version]["date"], row["release_date"], "date_provenance", version)
        source_sizes = rows(directory / "source_sizes.csv")
        report.equal({r["source_file"] for r in source_sizes}, {r["source_file"] for r in class_rows},
                     "counted_source_population", version)
        for key in ("java_code_lines", "physical_java_lines"):
            expected = sum(int(r[key]) for r in source_sizes)
            report.numeric(provenance[key], expected, "source_size_reconciliation", version + "/" + key)
            report.numeric(size_index[version][key], expected, "source_size_reconciliation", version + "/" + key)
        if version == version_ids[-1]:
            report.check(int(size_index[version]["java_code_lines"]) >= 10000, "latest_code_size_eligibility", version)
        partitions = {}
        condition_evidence = {}
        for condition in ("A1", "A2", "A3", "A4"):
            filtered = condition in ("A2", "A4")
            current_nodes, current_edges = (retained, filtered_edges) if filtered else (node_set, edges)
            context = f"{version}/{condition}"
            assignment = read_partition(output / f"{condition}.csv", current_nodes, report)
            partitions[condition] = assignment
            quality = independent_quality(current_nodes, current_edges, assignment)
            recorded = data(output / f"{condition}_metrics.json")
            report.flat_metrics(recorded, quality, context + "/JSON")
            report.flat_metrics(metric_index[version, condition], quality, context + "/aggregate")
            report.equal(metric_index[version, condition]["algorithm"], "ACDC" if condition in ("A1", "A2") else "kmeans",
                         "condition_algorithm_identity", context)
            report.equal(metric_index[version, condition]["filtered"], str(filtered), "condition_population_identity", context)
            summary_rows = rows(output / f"{condition}_quality/metrics_summary.csv")
            report.equal(len(summary_rows), 1, "quality_summary_row_count", context)
            report.flat_metrics(summary_rows[0], quality, context + "/summary")
            for table in ("per_cluster", "per_pair"):
                report.terms(recorded[table], quality[table], context + "/JSON/" + table)
                report.terms(rows(output / f"{condition}_quality/{table}.csv"), quality[table], context + "/CSV/" + table)
            metadata = data(output / f"{condition}_run.json")
            report.equal(metadata["actual_k"], quality["n_clusters"], "reported_actual_k", context)
            if condition in ("A1", "A2"):
                report.equal(metadata["patterns"].lstrip("+"), config["acdc"]["patterns"].lstrip("+"), "frozen_acdc_policy", context)
                report.equal(metadata["subgraph_max_size"], config["acdc"]["max_subgraph_size"], "frozen_acdc_policy", context)
                report.equal(config["acdc"]["node_ids"], "class_plus_java_suffix", "frozen_acdc_policy", context)
                report.equal(metadata["node_id_encoding"], "append_.java_suffix_to_preserve_unique_ACDC_file_basenames",
                             "acdc_unique_filename_basenames", context)
                identity_map = rows(output / f"{condition}_run/node_id_map.csv")
                report.equal({r["class"]: r["acdc_node"] for r in identity_map},
                             {n: n + ".java" for n in current_nodes}, "acdc_reversible_id_map", context)
                report.equal(read_rsf(output / f"{condition}_run/input.rsf", "call"),
                             [(a + ".java", b + ".java") for a, b in current_edges],
                             "acdc_input_preserves_exact_graph", context)
                isolates = set(current_nodes) - {n for e in current_edges for n in e}
                report.equal(set(metadata["isolates_restored_as_singletons"]), isolates, "acdc_isolates_preserved", context)
                sizes = Counter(assignment.values())
                report.check(all(sizes[assignment[n]] == 1 for n in isolates), "acdc_isolate_singletons", context)
            else:
                requested = min(len(current_nodes), math.ceil(Fraction(len(nodes) * calibration["pilot_k"], calibration["pilot_n"]))) if current_nodes else 0
                report.equal(metadata["requested_k"], requested, "predeclared_k_from_full_n", context)
                report.equal(metadata["feature_rows"], len(current_nodes), "fixed_feature_schema", context + "/rows")
                report.equal(metadata["feature_columns"], 2 * len(universe), "fixed_feature_schema", context + "/columns")
                report.equal(metadata["feature_universe_sha256"], universe_hash, "fixed_feature_schema", context + "/coordinate identities")
                report.equal(metadata["feature_nonzeros"], 2 * (len(current_nodes) + len(current_edges)), "feature_identity_plus_edges_only", context)
                for key in ("random_state", "n_init", "max_iter", "algorithm"):
                    report.equal(metadata[key], config["kmeans"][key], "frozen_kmeans_parameters", context + "/" + key)
                if metadata["actual_k"] != requested:
                    report.warnings.append({"context": context, "message": "Actual KMeans clusters differ from requested k", "metadata": metadata})
            condition_evidence[condition] = {key: quality[key] for key in ("n_nodes", "n_edges", "n_clusters", "mq", "max_cluster_size", "singleton_clusters")}
        comparison_file = data(output / "partition_comparisons.json")
        report.equal(comparison_file["version"], version, "detailed_comparison_version", version)
        detail_index = {comparison_key(item["comparison"]): item for item in comparison_file["comparisons"]}
        expected_local_keys = set()

        def check_comparison(scope, source_label, target_label, a, b, comparison_nodes, old_version="", n_edges=None):
            key = (version, scope, source_label, target_label, old_version)
            expected_comparison_keys.add(key)
            expected_local_keys.add(key)
            recorded_csv, recorded_json = comparison_index[key], detail_index[key]
            forward = independent_mojofm(a, b, comparison_nodes)
            reverse = independent_mojofm(b, a, comparison_nodes)
            expected_row = {
                "version": version, "previous_version": old_version, "scope": scope,
                "source_condition": source_label, "reference_condition": target_label,
                "n_nodes": len(comparison_nodes), "n_edges": n_edges,
                "source_clusters": forward["source_clusters"], "reference_clusters": forward["target_clusters"],
                "mojo_distance": forward["distance"], "mojo_max_distance": forward["max_distance"], "mojofm": forward["score"],
                "reverse_mojo_distance": reverse["distance"], "reverse_mojo_max_distance": reverse["max_distance"],
                "reverse_mojofm": reverse["score"],
                "node_universe_sha256": hashlib.sha256(("\n".join(sorted(comparison_nodes)) + "\n").encode()).hexdigest(),
                "interpretation": "directional partition agreement; reference is not validated ground truth",
            }
            report.equal(set(recorded_csv), set(expected_row), "comparison_exact_schema", str(key) + "/CSV")
            report.equal(set(recorded_json["comparison"]), set(expected_row), "comparison_exact_schema", str(key) + "/JSON")
            for field, expected in expected_row.items():
                context = f"{version}/{scope}/{source_label}_to_{target_label}/{field}"
                for observed, label in ((recorded_csv, "CSV"), (recorded_json["comparison"], "JSON")):
                    if isinstance(expected, str):
                        report.equal(observed[field], expected, "comparison_identity_and_population", context + "/" + label)
                    else:
                        report.numeric(observed[field], expected, "independent_partition_comparison", context + "/" + label)
            for direction, expected_result in (("forward", forward), ("reverse", reverse)):
                for field, expected in expected_result.items():
                    context = f"{version}/{scope}/{source_label}_to_{target_label}/{direction}/{field}"
                    if isinstance(expected, (str, bool)):
                        report.equal(recorded_json[direction][field], expected, "independent_mojofm_terms", context)
                    else:
                        report.numeric(recorded_json[direction][field], expected, "independent_mojofm_terms", context)
                report.check(0 <= expected_result["distance"] <= expected_result["max_distance"], "mojo_target_distance_bounds", context)
            return forward, reverse

        for full, filtered in (("A1", "A2"), ("A3", "A4")):
            baseline = independent_quality(retained, filtered_edges, {n: partitions[full][n] for n in retained})
            recovered = independent_quality(retained, filtered_edges, partitions[filtered])
            observed = common_index[version, full]
            report.equal(observed["filtered_condition"], filtered, "same_graph_condition_pair", version)
            forward, reverse = check_comparison("full_vs_filtered_retained", full, filtered,
                                                partitions[full], partitions[filtered], retained, n_edges=len(filtered_edges))
            expected = {"common_classes": len(retained), "common_edges": len(filtered_edges),
                        "projected_full_mq": baseline["mq"], "recovered_filtered_mq": recovered["mq"],
                        "mq_change_same_graph": recovered["mq"] - baseline["mq"],
                        "mojofm_full_to_filtered": forward["score"], "mojofm_filtered_to_full": reverse["score"],
                        "mojo_distance_full_to_filtered": forward["distance"],
                        "mojo_distance_filtered_to_full": reverse["distance"]}
            report.equal(set(observed), set(expected) | {"version", "full_condition", "filtered_condition"},
                         "same_graph_exact_schema", version + "/" + full)
            for key, value in expected.items():
                report.numeric(observed[key], value, "same_graph_recalculation", f"{version}/{full}/{key}")
            report.flat_metrics(data(output / f"{full}_projected_to_retained_metrics.json"), baseline, f"{version}/{full}/projected")
        check_comparison("algorithms_full", "A1", "A3", partitions["A1"], partitions["A3"], node_set, n_edges=len(edges))
        check_comparison("algorithms_retained", "A2", "A4", partitions["A2"], partitions["A4"], retained, n_edges=len(filtered_edges))
        if previous is not None:
            old_nodes, old_edges, old_partitions, old_version = previous
            common = node_set & old_nodes
            left = {e for e in old_edges if e[0] in common and e[1] in common}
            right = {e for e in edges if e[0] in common and e[1] in common}
            observed = temporal_rows[row["index"] - 2]
            report.equal((observed["previous_version"], observed["version"]), (old_version, version), "temporal_pair_identity", version)
            expected = {"common_classes": len(common), "added_classes": len(node_set - old_nodes),
                        "removed_classes": len(old_nodes - node_set),
                        "common_node_edge_jaccard": len(left & right) / len(left | right) if left | right else 1.0}
            for condition, label in (("A1", "acdc"), ("A3", "kmeans")):
                forward, reverse = check_comparison("temporal_full_common", condition, condition,
                                                    old_partitions[condition], partitions[condition], common, old_version=old_version)
                expected[label + "_mojofm_previous_to_current"] = forward["score"]
                expected[label + "_mojofm_current_to_previous"] = reverse["score"]
            report.equal(set(observed), set(expected) | {"previous_version", "version"},
                         "temporal_exact_schema", version)
            for key, value in expected.items():
                report.numeric(observed[key], value, "temporal_recalculation", version + "/" + key)
        report.equal(set(detail_index), expected_local_keys, "detailed_comparison_inventory", version)
        report.equal(len(comparison_file["comparisons"]), len(expected_local_keys), "unique_detailed_comparisons", version)
        previous = (node_set, edges, partitions, version)
        report.release_evidence.append({"version": version, **expected_sizes, "conditions": condition_evidence})
    report.equal(set(universe), observed_universe, "fixed_feature_schema", "union across all30 releases")
    report.equal(set(comparison_index), expected_comparison_keys, "exact_partition_comparison_inventory", "all versions")
    run = data(result_root / "run_manifest.json")
    report.equal(run["release_count"], 30, "run_manifest_totals", "releases")
    report.equal(run["architecture_count"], 120, "run_manifest_totals", "architectures")
    report.equal(run["comparison_count"], expected_comparison_count, "run_manifest_totals", "partition comparisons")
    report.equal(run["study_revision"], config["study_revision"], "run_revision_identity", "run")
    report.equal(run["manifest_sha256"], digest(root / "config/versions.json"), "frozen_manifest_checksum", "run")
    report.equal(run["config_sha256"], digest(root / "config/analysis.json"), "frozen_config_checksum", "run")
    report.equal(set(run["source_sha256"]), {str(p.relative_to(root)) for p in (root / "src/evolution").glob("*.py")},
                 "complete_core_implementation_hash_inventory", "run")
    for path, expected in run["source_sha256"].items():
        report.equal(digest(root / path), expected, "frozen_implementation_checksum", path)
    audit_pilot(root, result_root, graph_root, versions, config, run, calibration, report)
    if include_ai:
        audit_ai(root, result_root, graph_root, versions, config, report)
    return report


def json_safe(value):
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(type(value).__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--results", type=Path)
    parser.add_argument("--graphs", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--skip-ai", action="store_true", help="Explicitly audit the core study only; record that AI was not checked")
    args = parser.parse_args()
    result_root = args.results or args.root / "results"
    output = args.output or result_root / "validation.json"
    try:
        report = audit(args.root, result_root, args.graphs or args.root / "data/graphs", include_ai=not args.skip_ai)
    except Exception as error:
        result = {"status": "incomplete", "error_type": type(error).__name__, "error": str(error)}
    else:
        result = {"status": "passed" if not report.failures else "failed",
                  "checks_performed": sum(report.counts.values()), "check_categories": dict(sorted(report.counts.items())),
                  "failure_count": len(report.failures), "failures": report.failures,
                  "warnings": report.warnings, "releases": report.release_evidence,
                  "ai": report.ai_evidence if report.ai_evidence is not None else {"status": "skipped_by_explicit_flag"}}
    result.update({"validated_at_utc": datetime.now(timezone.utc).isoformat(),
                   "validator_sha256": digest(Path(__file__)),
                   "method": "stdlib-only independent artifact audit; exact instructor-row normalization and original-byte input check; edge-contribution lecture MQ; exact-rational UE; residual-network max-flow MoJo with Ferrers-graph normalization; centroid-identity pilot inertia",
                   "scope": "30 source-owned Guava graphs,120 finalized A1-A4 partitions,178 bidirectional partition comparisons,60 retained-graph MQ comparisons,29 temporal transitions,all predeclared pilot fits" + ("; completed AI evidence and four comparisons" if not args.skip_ai else "; AI explicitly excluded by --skip-ai"),
                   "limitations": ["Provenance/membership checks do not prove a static extractor sees runtime reflection or all dynamic dispatch.",
                                   "Passing structural checks does not prove the recovered clusters match intended architecture.",
                                   "No new architecture is created by this validation.",
                                   "AI input/output hashes preserve its record; they do not independently prove private model knowledge or process declarations."]})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, default=json_safe, allow_nan=False) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "checks_performed", "failure_count", "error") if key in result}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
```
<!-- END_FULL_SOURCE scripts/validate_results.py -->
