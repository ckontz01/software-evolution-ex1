#!/usr/bin/env python3
"""Select 30 distinct Guava major/minor families from the frozen tag catalog.

The default/--check mode validates the existing manifest without changing files.
--write regenerates selection metadata, retaining already pinned artifact hashes.
This command never reads graphs, clusters, quality scores, or source-code changes.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
COUNT = 30
CUTOFF = "2026-10-17"
SOURCE_PREFIXES = ["com/google/common/", "com/google/thirdparty/publicsuffix/"]
SOURCE_ROOTS = ["guava/src/", "src/", "guava/src/main/java/", "src/main/java/"]
POLICY = (
    "From the frozen 2026-10-17 tag catalog, retain numeric stable main-project releases "
    "10.0+ and the existing three documented mainline exclusions. Group the 70 eligible "
    "releases into 45 distinct MAJOR.MINOR families, ordered by each family's first release "
    "date. Select family ranks round(i*(45-1)/(30-1)) for i=0..29. Within each selected "
    "family choose its highest eligible stable patch, except that the first family uses "
    "the oldest boundary release 10.0 to preserve the historical start. The final family "
    "uses its latest eligible release 33.7.2. Exactly 30 distinct families are represented "
    "once each. Spacing is uniform in family rank, not calendar time, and adjacent selected "
    "families can be consecutive. Patch representatives are not repeated observations of "
    "the same family. Use plain artifacts before 23.1 and JRE artifacts thereafter. "
    "Selection uses no graphs, clusters, MQ values, or structural-change outcomes."
)


def version_key(version):
    if not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", version):
        raise ValueError(f"Not a numeric stable version: {version}")
    parts = tuple(int(p) for p in version.split("."))
    return parts + (0,) * (3 - len(parts))


def family(version):
    return ".".join(version.split(".")[:2])


def selected_rows(inventory):
    """Pure selection function; returns captured rows plus a complete family audit."""
    exclusions = {row["version"] for row in inventory["additional_exclusions"]}
    eligible = [row for row in inventory["stable_tags_in_date_order"]
                if version_key(row["version"])[0] >= 10
                and row["version"] not in exclusions
                and row["release_date"][:10] <= CUTOFF]
    groups = defaultdict(list)
    for row in eligible:
        groups[family(row["version"])].append(row)
    names = sorted(groups, key=lambda name: (
        min(row["release_date"] for row in groups[name]), version_key(name)))
    if len(eligible) != 70 or len(names) != 45:
        raise ValueError("Frozen catalog must produce 70 eligible releases and 45 families.")
    ranks = [round(Fraction(i * (len(names) - 1), COUNT - 1)) for i in range(COUNT)]
    if len(set(ranks)) != COUNT:
        raise ValueError("Family sampling produced duplicate ranks.")
    representatives = {}
    for name in names:
        representatives[name] = max(groups[name], key=lambda row: version_key(row["version"]))
    # An explicit, fixed endpoint convention, not a data-dependent exception.
    representatives[names[0]] = min(groups[names[0]], key=lambda row: row["release_date"])
    chosen = [deepcopy(representatives[names[rank]]) for rank in ranks]
    if chosen[0]["version"] != "10.0" or chosen[-1]["version"] != "33.7.2":
        raise ValueError("Unexpected frozen-history endpoints.")
    if any(a["release_date"] >= b["release_date"] for a, b in zip(chosen, chosen[1:])):
        raise ValueError("Representative release dates must strictly increase.")
    audit = []
    for rank, name in enumerate(names):
        audit.append({
            "family_rank_zero_based": rank,
            "family": name,
            "eligible_versions": [row["version"] for row in groups[name]],
            "first_release_date": min(row["release_date"] for row in groups[name]),
            "representative": representatives[name]["version"],
            "representative_rule": "oldest_history_boundary" if rank == 0 else "highest_eligible_stable_patch",
            "selected": rank in ranks,
        })
    return chosen, audit, ranks


def validate_manifest(manifest, inventory):
    chosen, audit, ranks = selected_rows(inventory)
    rows = manifest["versions"]
    if len(rows) != COUNT or len({family(r["version"]) for r in rows}) != COUNT:
        raise ValueError("Exactly 30 releases from 30 distinct MAJOR.MINOR families are required.")
    if [r["version"] for r in rows] != [r["version"] for r in chosen]:
        raise ValueError("Selected releases differ from the frozen family-rank rule.")
    stable = inventory["stable_tags_in_date_order"]
    positions = {row["version"]: i for i, row in enumerate(stable)}
    for i, (row, captured) in enumerate(zip(rows, chosen)):
        for key in ("tag", "commit_sha", "release_date", "date_basis"):
            if row[key] != captured[key]:
                raise ValueError(f"Captured {key} differs for {row['version']}")
        if not re.fullmatch(r"[a-f0-9]{40}", row["commit_sha"]):
            raise ValueError("Missing immutable commit SHA.")
        if row["family"] != family(row["version"]) or row["family_rank_zero_based"] != ranks[i]:
            raise ValueError(f"Incorrect family metadata for {row['version']}")
        skipped = [] if i == 0 else [r["version"] for r in stable[
            positions[rows[i - 1]["version"]] + 1:positions[row["version"]]]]
        if row["skipped_stable_since_previous"] != skipped:
            raise ValueError(f"Incorrect intervening releases for {row['version']}")
        if row.get("source_prefixes") != SOURCE_PREFIXES:
            raise ValueError("Ownership prefixes must include the Guava-owned public-suffix implementation.")
    if manifest.get("major_minor_families") != [family(r["version"]) for r in rows]:
        raise ValueError("Top-level family list differs from selected rows.")
    if manifest.get("selected_family_ranks_zero_based") != ranks:
        raise ValueError("Top-level selected family ranks differ.")
    if manifest.get("eligible_major_minor_families") != len(audit):
        raise ValueError("Incorrect eligible-family count.")


def build_manifest(previous, inventory, catalog_sha256):
    chosen, audit, ranks = selected_rows(inventory)
    previous_rows = {row["version"]: row for row in previous["versions"]}
    stable = inventory["stable_tags_in_date_order"]
    positions = {row["version"]: i for i, row in enumerate(stable)}
    rows = []
    for i, (captured, rank) in enumerate(zip(chosen, ranks)):
        version = captured["version"]
        row = deepcopy(captured)
        artifact_version = version + ("-jre" if version_key(version) >= (23, 1, 0) else "")
        row.update({
            "index": i + 1, "family": family(version), "family_rank_zero_based": rank,
            "representative_rule": "oldest_history_boundary" if i == 0 else "highest_eligible_stable_patch",
            "artifact_version": artifact_version, "group_id": "com.google.guava", "artifact_id": "guava",
            # Retained for old callers; the plural key is the authoritative complete scope.
            "source_prefix": SOURCE_PREFIXES[0], "source_prefixes": SOURCE_PREFIXES,
            "source_roots": SOURCE_ROOTS,
            "skipped_stable_since_previous": [] if i == 0 else [r["version"] for r in stable[
                positions[rows[-1]["version"]] + 1:positions[version]]],
            "skipped_families_since_previous": [] if i == 0 else [r["family"] for r in audit[
                ranks[i - 1] + 1:rank]],
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
        "schema_version": 3, "study_revision": 2, "selection_date_utc": CUTOFF,
        "selection_policy": POLICY, "selection_catalog_sha256": catalog_sha256,
        "eligible_major_minor_families": len(audit), "selected_count": COUNT,
        "selected_family_ranks_zero_based": ranks,
        "major_minor_families": [family(r["version"]) for r in rows],
        "external_exclusions": [
            "Project-owned production sources under com.google.common and com.google.thirdparty.publicsuffix define the ownership scope",
            "The public-suffix Java implementation carries Guava Authors headers and is included; package naming alone does not establish external ownership",
            "JDK, failureaccess, listenablefuture compatibility artifact, external annotation libraries, and other external endpoints are excluded",
            "Android, GWT, test, benchmark, and auxiliary-component artifacts are outside the production JRE study",
            "Prerelease distributions are excluded; a Beta API annotation does not exclude the annotated Guava class",
        ],
        "versions": rows,
    })
    validate_manifest(manifest, inventory)
    evidence = {
        "schema_version": 1, "study_revision": 2, "frozen_cutoff_utc": CUTOFF,
        "catalog_path": "data/provenance/tag_inventory.json", "catalog_sha256": catalog_sha256,
        "rule": POLICY, "eligible_releases": 70, "eligible_families": len(audit),
        "selected_count": COUNT, "selected_family_ranks_zero_based": ranks,
        "selected_versions": [r["version"] for r in rows],
        "selected_unique_families": COUNT, "unselected_families": len(audit) - COUNT,
        "family_catalog": audit,
        "selection_inputs_exclude": ["dependency graphs", "clustering outcomes", "quality metrics", "structural identity"],
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
    inventory = json.loads(catalog_bytes)
    existing = json.loads(args.manifest.read_text())
    if args.write:
        revised, evidence = build_manifest(existing, inventory, hashlib.sha256(catalog_bytes).hexdigest())
        write_json(args.manifest, revised)
        write_json(ROOT / "data/provenance/family_selection.json", evidence)
    else:
        validate_manifest(existing, inventory)
        revised = existing
    print(json.dumps({"selected_count": len(revised["versions"]),
                      "unique_families": len(revised["major_minor_families"]),
                      "versions": [r["version"] for r in revised["versions"]],
                      "mode": "write" if args.write else "check"}, indent=2))


if __name__ == "__main__":
    main()
