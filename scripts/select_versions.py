#!/usr/bin/env python3
"""Select 30 Guava releases by major coverage and recorded calendar gaps.

Default/--check validates without writing; --write preserves matching artifact
pins. Selection reads only the frozen release catalog and declared parameters.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
COUNT, FIRST_MAJOR, LAST_MAJOR = 30, 10, 33
CUTOFF = "2026-10-17"
MINIMUM_GAP_DAYS, MAX_OPTIONAL_PER_MAJOR = 60, 2
OLDEST_VERSION, LATEST_VERSION = "10.0", "33.7.2"
METHOD = "major_anchors_calendar_greedy_v3"
SOURCE_PREFIXES = ["com/google/common/", "com/google/thirdparty/publicsuffix/"]
SOURCE_ROOTS = ["guava/src/", "src/", "guava/src/main/java/", "src/main/java/"]
DATE_BASIS = ("Whole calendar-day differences: documented dates for date-only records, "
              "UTC calendar dates for timestamped records; no fractional-day weighting.")
PARAMETERS = {
    "requested_count": COUNT, "first_major": FIRST_MAJOR, "last_major": LAST_MAJOR,
    "oldest_endpoint_version": OLDEST_VERSION, "latest_endpoint_version": LATEST_VERSION,
    "representative_rule": "first_eligible_stable_release_per_family", "optional_count": 5,
    "minimum_calendar_gap_days": MINIMUM_GAP_DAYS,
    "max_optional_families_per_major": MAX_OPTIONAL_PER_MAJOR,
    "objective": "greedy_reduction_in_sum_squared_calendar_gaps",
    "tie_break": ["earlier_utc_calendar_date", "numeric_version"],
    "latest_endpoint_counts_as_optional": False,
}
POLICY = (
    "From the frozen 2026-10-17 catalog retain the same 70 eligible stable main-project "
    "releases in 45 MAJOR.MINOR families and the existing three documented mainline "
    "exclusions. Use the first eligible stable release in each family. Require every "
    "MAJOR.0 family from 10 through 33 (24 anchors, including 13.0.1 because ambiguous "
    "13.0 is excluded), preserving the fixed oldest 10.0 and latest 33.7.2 endpoints. "
    "The latest endpoint is the sole exception to the first-release representative "
    "rule and does not count as an optional addition. Fill five remaining slots "
    "greedily: splitting a calendar gap into L and R days reduces the sum of squared "
    "gaps by 2*L*R. Choose the greatest reduction, then the earlier UTC calendar date, "
    "then numeric version. Keep every selected gap at least 60 calendar days and "
    "permit at most two optional minor-family additions in any major. Each selected "
    "family appears once. This balances major-history coverage and calendar spacing; "
    "it does not require an omitted numeric tag between every pair or claim a globally "
    "optimal calendar design. Use plain Maven artifacts before 23.1 and JRE artifacts "
    "thereafter. Selection reads no graphs, clusters, quality values or structural-change outcomes."
)


def version_key(version):
    if not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", version):
        raise ValueError(f"Not a numeric stable version: {version}")
    parts = tuple(int(p) for p in version.split("."))
    return parts + (0,) * (3 - len(parts))


def family(version):
    version_key(version)
    return ".".join(version.split(".")[:2])


def release_day(row):
    value = row["release_date"]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return date.fromisoformat(value)
    instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if instant.tzinfo is None:
        raise ValueError("Timestamped release dates must specify their timezone.")
    return instant.astimezone(timezone.utc).date()


def row_key(row):
    return release_day(row), version_key(row["version"])


def greedy_fill_gaps(representatives, mandatory, target_count, minimum_gap_days,
                     max_optional_per_major):
    """Pure selector. Score 2LR=(L+R)^2-L^2-R^2; cap counts only new additions."""
    if minimum_gap_days < 1 or max_optional_per_major < 0:
        raise ValueError("Gap must be positive and optional-major limit nonnegative.")
    if target_count < len(mandatory):
        raise ValueError("Requested count cannot discard mandatory anchors.")
    candidates, selected = sorted(representatives, key=row_key), sorted(mandatory, key=row_key)
    for rows in (candidates, selected):
        if len({family(r["version"]) for r in rows}) != len(rows):
            raise ValueError("Duplicate representative or mandatory family.")
    if len(selected) < 2 or any(r not in candidates for r in selected):
        raise ValueError("Mandatory endpoints must be candidate representatives.")
    if any((release_day(b) - release_day(a)).days < minimum_gap_days
           for a, b in zip(selected, selected[1:])):
        raise ValueError("Mandatory anchors cannot satisfy the requested calendar gap.")
    counts, steps = Counter(), []
    while len(selected) < target_count:
        selected_families = {family(r["version"]) for r in selected}
        options = []
        for candidate in candidates:
            major = version_key(candidate["version"])[0]
            if family(candidate["version"]) in selected_families or counts[major] >= max_optional_per_major:
                continue
            day = release_day(candidate)
            pos = next((i for i, r in enumerate(selected) if release_day(r) > day), len(selected))
            if pos == 0 or pos == len(selected):
                continue
            left, right = selected[pos - 1:pos + 1]
            left_days, right_days = (day - release_day(left)).days, (release_day(right) - day).days
            if min(left_days, right_days) < minimum_gap_days:
                continue
            key = (-2 * left_days * right_days, day, version_key(candidate["version"]))
            options.append((key, candidate, left, right, left_days, right_days))
        if not options:
            raise ValueError("Too few families satisfy the calendar gap and optional-major cap.")
        key, candidate, left, right, left_days, right_days = min(options, key=lambda x: x[0])
        major = version_key(candidate["version"])[0]
        counts[major] += 1
        steps.append({
            "step": len(steps) + 1, "version": candidate["version"],
            "family": family(candidate["version"]), "calendar_date": release_day(candidate).isoformat(),
            "between_versions": [left["version"], right["version"]],
            "original_gap_days": left_days + right_days,
            "left_gap_days": left_days, "right_gap_days": right_days,
            "squared_gap_reduction_days2": -key[0],
            "optional_count_for_major_after_selection": counts[major],
            "feasible_candidate_count": len(options),
        })
        selected.append(candidate)
        selected.sort(key=row_key)
    return deepcopy(selected), steps


def selection_details(inventory):
    stable = inventory["stable_tags_in_date_order"]
    if len({r["version"] for r in stable}) != len(stable):
        raise ValueError("Captured catalog contains duplicate versions.")
    exclusions = {r["version"] for r in inventory["additional_exclusions"]}
    eligible = sorted((r for r in stable if FIRST_MAJOR <= version_key(r["version"])[0] <= LAST_MAJOR
                       and r["version"] not in exclusions
                       and release_day(r) <= date.fromisoformat(CUTOFF)), key=row_key)
    groups = defaultdict(list)
    for row in eligible:
        groups[family(row["version"])].append(row)
    names = sorted(groups, key=lambda name: row_key(groups[name][0]))
    if len(eligible) != 70 or len(names) != 45:
        raise ValueError("Frozen catalog must produce 70 eligible releases and 45 families.")
    representatives = {name: rows[0] for name, rows in groups.items()}
    latest = next((r for r in eligible if r["version"] == LATEST_VERSION), None)
    if latest is None or eligible[-1]["version"] != LATEST_VERSION:
        raise ValueError("The frozen latest endpoint is missing or inconsistent.")
    representatives[family(LATEST_VERSION)] = latest
    anchor_names = [f"{major}.0" for major in range(FIRST_MAJOR, LAST_MAJOR + 1)]
    if any(name not in representatives for name in anchor_names):
        raise ValueError("Every major from 10 through 33 must have a MAJOR.0 anchor.")
    mandatory = [representatives[name] for name in anchor_names] + [latest]
    chosen, steps = greedy_fill_gaps(list(representatives.values()), mandatory, COUNT,
                                     MINIMUM_GAP_DAYS, MAX_OPTIONAL_PER_MAJOR)
    if chosen[0]["version"] != OLDEST_VERSION or chosen[-1]["version"] != LATEST_VERSION:
        raise ValueError("Unexpected frozen-history endpoints.")
    selected_names = {family(r["version"]) for r in chosen}
    audit = []
    for rank, name in enumerate(names):
        audit.append({
            "family_rank_zero_based": rank, "family": name,
            "eligible_versions": [r["version"] for r in groups[name]],
            "first_release_date": groups[name][0]["release_date"],
            "representative": representatives[name]["version"],
            "representative_calendar_date": release_day(representatives[name]).isoformat(),
            "representative_rule": ("latest_history_endpoint" if name == family(LATEST_VERSION)
                                    else "first_eligible_stable_release"),
            "selected": name in selected_names,
            "selection_role": ("major_anchor" if name in anchor_names else
                               "latest_endpoint" if name == family(LATEST_VERSION) else
                               "gap_filling_minor" if name in selected_names else None),
        })
    ranks = [names.index(family(r["version"])) for r in chosen]
    return chosen, audit, ranks, steps, sorted(mandatory, key=row_key)


def selected_rows(inventory):
    """Preserve the pure three-result interface used by acquisition callers."""
    chosen, audit, ranks, _, _ = selection_details(inventory)
    return chosen, audit, ranks


def calendar_gaps(rows):
    return [{"from_version": a["version"], "to_version": b["version"],
             "from_date": release_day(a).isoformat(), "to_date": release_day(b).isoformat(),
             "gap_days": (release_day(b) - release_day(a)).days}
            for a, b in zip(rows, rows[1:])]


def gap_statistics(rows):
    gaps = [g["gap_days"] for g in calendar_gaps(rows)]
    return {"count": len(gaps), "minimum_days": min(gaps), "median_days": statistics.median(gaps),
            "maximum_days": max(gaps), "mean_days": statistics.mean(gaps),
            "total_span_days": sum(gaps),
            "below_declared_minimum_count": sum(g < MINIMUM_GAP_DAYS for g in gaps)}


def validate_manifest(manifest, inventory):
    chosen, audit, ranks, _, _ = selection_details(inventory)
    rows = manifest["versions"]
    if manifest.get("schema_version") != 4 or manifest.get("study_revision") != 3:
        raise ValueError("Selection requires manifest schema 4 / study revision 3.")
    if (manifest.get("selection_method") != METHOD or manifest.get("selection_parameters") != PARAMETERS
            or manifest.get("selection_policy") != POLICY):
        raise ValueError("Declared selection policy or parameters differ from the frozen rule.")
    if len(rows) != COUNT or len({family(r["version"]) for r in rows}) != COUNT:
        raise ValueError("Exactly 30 releases from 30 distinct families are required.")
    if [r["version"] for r in rows] != [r["version"] for r in chosen]:
        raise ValueError("Selected releases differ from the major-anchor calendar rule.")
    stable = sorted(inventory["stable_tags_in_date_order"], key=row_key)
    positions = {r["version"]: i for i, r in enumerate(stable)}
    for i, (row, captured) in enumerate(zip(rows, chosen)):
        for key in ("tag", "commit_sha", "release_date", "date_basis"):
            if row[key] != captured[key]:
                raise ValueError(f"Captured {key} differs for {row['version']}")
        if not re.fullmatch(r"[a-f0-9]{40}", row["commit_sha"]):
            raise ValueError("Missing immutable commit SHA.")
        if row["family"] != family(row["version"]) or row["family_rank_zero_based"] != ranks[i]:
            raise ValueError(f"Incorrect family metadata for {row['version']}")
        for key in ("representative_rule", "selection_role"):
            if row.get(key) != audit[ranks[i]][key]:
                raise ValueError(f"Incorrect {key} for {row['version']}")
        skipped = [] if i == 0 else [r["version"] for r in stable[
            positions[rows[i - 1]["version"]] + 1:positions[row["version"]]]]
        omitted = [] if i == 0 else [r["family"] for r in audit[ranks[i - 1] + 1:ranks[i]]]
        if row["skipped_stable_since_previous"] != skipped or row["skipped_families_since_previous"] != omitted:
            raise ValueError(f"Incorrect intervening releases or families for {row['version']}")
        if row.get("source_prefixes") != SOURCE_PREFIXES:
            raise ValueError("Guava ownership scope must remain unchanged.")
        gap = None if i == 0 else (release_day(row) - release_day(rows[i - 1])).days
        if row.get("calendar_gap_days_since_previous") != gap:
            raise ValueError(f"Incorrect calendar gap for {row['version']}")
    expected = {"major_minor_families": [family(r["version"]) for r in rows],
                "selected_family_ranks_zero_based": ranks, "eligible_major_minor_families": len(audit),
                "selected_major_numbers": list(range(FIRST_MAJOR, LAST_MAJOR + 1)),
                "calendar_gap_statistics": gap_statistics(chosen)}
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"Top-level {key} differs from the audited selection.")


def build_manifest(previous, inventory, catalog_sha256):
    chosen, audit, ranks, steps, mandatory = selection_details(inventory)
    previous_rows = {r["version"]: r for r in previous["versions"]}
    stable = sorted(inventory["stable_tags_in_date_order"], key=row_key)
    positions = {r["version"]: i for i, r in enumerate(stable)}
    rows = []
    for i, (captured, rank) in enumerate(zip(chosen, ranks)):
        version, row = captured["version"], deepcopy(captured)
        artifact_version = version + ("-jre" if version_key(version) >= (23, 1, 0) else "")
        row.update({
            "index": i + 1, "family": family(version), "family_rank_zero_based": rank,
            "representative_rule": audit[rank]["representative_rule"],
            "selection_role": audit[rank]["selection_role"],
            "calendar_gap_days_since_previous": None if i == 0 else
                (release_day(row) - release_day(rows[-1])).days,
            "artifact_version": artifact_version, "group_id": "com.google.guava", "artifact_id": "guava",
            "source_prefix": SOURCE_PREFIXES[0], "source_prefixes": SOURCE_PREFIXES,
            "source_roots": SOURCE_ROOTS,
            "skipped_stable_since_previous": [] if i == 0 else [r["version"] for r in stable[
                positions[rows[-1]["version"]] + 1:positions[version]]],
            "skipped_families_since_previous": [] if i == 0 else [r["family"] for r in audit[ranks[i - 1] + 1:rank]],
        })
        for kind, suffix in (("jar", ".jar"), ("sources", "-sources.jar"), ("pom", ".pom")):
            filename = f"guava-{artifact_version}{suffix}"
            row[f"{kind}_url"] = f"https://repo.maven.apache.org/maven2/com/google/guava/guava/{artifact_version}/{filename}"
            row[f"{kind}_path"] = f"data/raw/{version}/{filename}"
            old = previous_rows.get(version, {})
            if old.get(f"{kind}_url") == row[f"{kind}_url"]:
                for checksum in ("sha256", "maven_sha1"):
                    key = f"{kind}_{checksum}"
                    if old.get(key):
                        row[key] = old[key]
        rows.append(row)
    manifest = deepcopy(previous)
    manifest.update({
        "schema_version": 4, "study_revision": 3, "selection_date_utc": CUTOFF,
        "selection_method": METHOD, "selection_parameters": deepcopy(PARAMETERS),
        "selection_policy": POLICY, "selection_catalog_sha256": catalog_sha256,
        "eligible_major_minor_families": len(audit), "selected_count": COUNT,
        "selected_family_ranks_zero_based": ranks,
        "major_minor_families": [family(r["version"]) for r in rows],
        "selected_major_numbers": list(range(FIRST_MAJOR, LAST_MAJOR + 1)),
        "calendar_gap_statistics": gap_statistics(rows), "calendar_date_basis": DATE_BASIS,
        "versions": rows,
    })
    validate_manifest(manifest, inventory)
    anchor_gaps = calendar_gaps(mandatory)
    minimum_anchor_gap = min(g["gap_days"] for g in anchor_gaps)
    evidence = {
        "schema_version": 2, "study_revision": 3, "frozen_cutoff_utc": CUTOFF,
        "catalog_path": "data/provenance/tag_inventory.json", "catalog_sha256": catalog_sha256,
        "selection_method": METHOD, "selection_parameters": deepcopy(PARAMETERS), "rule": POLICY,
        "eligible_releases": 70, "eligible_families": len(audit), "selected_count": COUNT,
        "selected_family_ranks_zero_based": ranks, "selected_versions": [r["version"] for r in rows],
        "selected_unique_families": COUNT, "unselected_families": len(audit) - COUNT,
        "selected_major_numbers": list(range(FIRST_MAJOR, LAST_MAJOR + 1)),
        "mandatory_anchors": [{
            "version": r["version"], "family": family(r["version"]), "release_date": r["release_date"],
            "calendar_date": release_day(r).isoformat(),
            "selection_role": "latest_endpoint" if r["version"] == LATEST_VERSION else "major_anchor",
            "rationale": ("Fixed latest stable endpoint; not charged to the optional-major budget."
                          if r["version"] == LATEST_VERSION else
                          "Cover this major's MAJOR.0 milestone with its first eligible stable release."),
        } for r in mandatory],
        "optional_selection_steps": steps, "calendar_date_basis": DATE_BASIS,
        "calendar_gaps": calendar_gaps(rows), "calendar_gap_statistics": gap_statistics(rows),
        "spacing_feasibility": {
            "mandatory_anchor_minimum_gap_days": minimum_anchor_gap,
            "limiting_anchor_pairs": [g for g in anchor_gaps if g["gap_days"] == minimum_anchor_gap],
            "ninety_day_floor_feasible_with_fixed_anchors": minimum_anchor_gap >= 90,
            "note": "A floor above the smallest fixed-anchor gap requires changing an anchor. The greedy objective is not claimed globally optimal.",
        },
        "family_catalog": audit,
        "selection_inputs_include": ["captured stable tag identities", "recorded release dates", "numeric version families", "declared parameters"],
        "selection_inputs_exclude": ["dependency graphs", "clustering outcomes", "quality metrics", "structural identity", "source-code changes"],
    }
    return manifest, evidence


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "config/versions.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/provenance/tag_inventory.json")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    catalog_bytes = args.catalog.read_bytes()
    catalog_sha256 = hashlib.sha256(catalog_bytes).hexdigest()
    inventory, existing = json.loads(catalog_bytes), json.loads(args.manifest.read_text())
    if args.write:
        revised, evidence = build_manifest(existing, inventory, catalog_sha256)
        write_json(args.manifest, revised)
        write_json(ROOT / "data/provenance/family_selection.json", evidence)
    else:
        validate_manifest(existing, inventory)
        if existing.get("selection_catalog_sha256") != catalog_sha256:
            raise ValueError("Catalog bytes do not match the recorded SHA-256.")
        revised = existing
    print(json.dumps({"selected_count": len(revised["versions"]),
                      "unique_families": len(revised["major_minor_families"]),
                      "major_numbers": revised["selected_major_numbers"],
                      "calendar_gap_statistics": revised["calendar_gap_statistics"],
                      "versions": [r["version"] for r in revised["versions"]],
                      "mode": "write" if args.write else "check"}, indent=2))


if __name__ == "__main__":
    main()
