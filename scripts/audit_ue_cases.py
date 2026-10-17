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
