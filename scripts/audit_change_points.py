#!/usr/bin/env python3
"""Reproduce the graph/source evidence behind the reported Guava change points.

Read-only with respect to finalized inputs: writes only results/change_points.json.
In a packaged checkout, first run python scripts/unpack_data.py.
No production extraction, clustering, detector or metric function is imported.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]


def csv_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def require(condition, description):
    if not condition:
        raise ValueError(description)


def snapshot(root, release):
    directory = root / "data/graphs" / release["version"]
    if not (directory / "classes.csv").is_file():
        raise FileNotFoundError("Expanded inputs are missing; run python scripts/unpack_data.py first")
    class_records = csv_rows(directory / "classes.csv")
    classes = {r["class"]: r for r in class_records}
    edge_records = csv_rows(directory / "dependencies.csv")
    edge_rows = {(r["source"], r["target"]): i for i, r in enumerate(edge_records, 2)}
    edges = set(edge_rows)
    require(len(classes) == len(class_records), "Duplicate class identity")
    require(len(edges) == len(edge_records), "Duplicate directed binary edge")
    require(all(a in classes and b in classes and a != b for a, b in edges), "Invalid graph scope or loop")
    provenance = json.loads((directory / "provenance.json").read_text())
    hashes = {name: sha256(directory / name) for name in
              ("classes.csv", "dependencies.csv", "dependencies_typed.csv", "provenance.json")}
    require(hashes["classes.csv"] == provenance["classes_sha256"], "Class checksum differs from production provenance")
    require(hashes["dependencies.csv"] == provenance["graph_sha256"], "Edge checksum differs from production provenance")
    require(provenance["binary_sha256"] == release["jar_sha256"], "Wrong binary provenance")
    require(provenance["sources_sha256"] == release["sources_sha256"], "Wrong source provenance")
    return {
        "classes": classes, "edges": edges, "edge_rows": edge_rows,
        "typed_counts": Counter(r["relation"] for r in csv_rows(directory / "dependencies_typed.csv")),
        "provenance": {
            "version": release["version"], "tag": release["tag"], "commit_sha": release["commit_sha"],
            "graph_directory": str(directory.relative_to(root)),
            "production_file_sha256": hashes,
            "binary_artifact": {"path": release["jar_path"], "manifest_sha256": release["jar_sha256"]},
            "sources_artifact": {"path": release["sources_path"], "manifest_sha256": release["sources_sha256"]},
            "extractor_sha256": provenance["extractor_sha256"],
        },
    }


def difference(before_version, after_version, snapshots):
    before, after = snapshots[before_version], snapshots[after_version]
    old_classes, new_classes = before["classes"], after["classes"]
    old_nodes, new_nodes = set(old_classes), set(new_classes)
    old_edges, new_edges = before["edges"], after["edges"]
    added_nodes, removed_nodes = new_nodes - old_nodes, old_nodes - new_nodes
    added_edges, removed_edges = new_edges - old_edges, old_edges - new_edges
    added_annotations = {n for n in added_nodes if new_classes[n]["kind"] == "annotation"}
    removed_annotations = {n for n in removed_nodes if old_classes[n]["kind"] == "annotation"}
    added_to_annotations = {e for e in added_edges if new_classes[e[1]]["kind"] == "annotation"}
    removed_to_removed_annotations = {e for e in removed_edges if e[1] in removed_annotations}
    common = old_nodes & new_nodes
    common_old = {e for e in old_edges if e[0] in common and e[1] in common}
    common_new = {e for e in new_edges if e[0] in common and e[1] in common}
    union = common_old | common_new
    top = lambda pairs: [{"class": n, "edges": count} for n, count in
                         sorted(Counter(b for a, b in pairs).items(), key=lambda item: (-item[1], item[0]))]
    return {
        "before_version": before_version, "after_version": after_version,
        "counts": {
            "classes_before": len(old_nodes), "classes_after": len(new_nodes),
            "added_classes": len(added_nodes), "removed_classes": len(removed_nodes),
            "added_annotation_classes": len(added_annotations), "removed_annotation_classes": len(removed_annotations),
            "edges_before": len(old_edges), "edges_after": len(new_edges),
            "added_edges": len(added_edges), "removed_edges": len(removed_edges),
            "net_edge_change": len(new_edges) - len(old_edges),
            "edge_change_percent": 100 * (len(new_edges) / len(old_edges) - 1) if old_edges else None,
            "class_change_percent": 100 * (len(new_nodes) / len(old_nodes) - 1) if old_nodes else None,
            "annotation_classes_before": sum(r['kind'] == 'annotation' for r in old_classes.values()),
            "annotation_classes_after": sum(r['kind'] == 'annotation' for r in new_classes.values()),
            "non_annotation_classes_before": sum(r['kind'] != 'annotation' for r in old_classes.values()),
            "non_annotation_classes_after": sum(r['kind'] != 'annotation' for r in new_classes.values()),
            "added_edges_to_annotation_types": len(added_to_annotations),
            "removed_edges_to_removed_annotation_types": len(removed_to_removed_annotations),
            "common_classes": len(common),
            "common_node_edge_jaccard": len(common_old & common_new) / len(union) if union else 1.0,
        },
        "added_classes": [new_classes[n] for n in sorted(added_nodes)],
        "removed_classes": [old_classes[n] for n in sorted(removed_nodes)],
        "added_annotation_classes": sorted(added_annotations),
        "removed_annotation_classes": sorted(removed_annotations),
        "added_classes_by_package": dict(sorted(Counter(new_classes[n]['package'] for n in added_nodes).items())),
        "removed_classes_by_package": dict(sorted(Counter(old_classes[n]['package'] for n in removed_nodes).items())),
        "typed_edge_counts_before": dict(sorted(before["typed_counts"].items())),
        "typed_edge_counts_after": dict(sorted(after["typed_counts"].items())),
        "added_edges_by_target": top(added_edges), "removed_edges_by_target": top(removed_edges),
        "added_edges": [{"source": a, "target": b,
                         "after_dependencies_csv_row_including_header": after["edge_rows"][a, b],
                         "target_is_annotation": new_classes[b]["kind"] == "annotation"}
                        for a, b in sorted(added_edges)],
        "removed_edges": [{"source": a, "target": b,
                           "before_dependencies_csv_row_including_header": before["edge_rows"][a, b],
                           "target_is_removed_annotation": b in removed_annotations}
                          for a, b in sorted(removed_edges)],
    }


def source_markers(root, release):
    archive_path = root / release["sources_path"]
    actual_hash = sha256(archive_path)
    require(actual_hash == release["sources_sha256"], "Pinned source JAR checksum mismatch")
    paths = (
        "com/google/common/collect/Lists.java",
        "com/google/common/collect/package-info.java",
        "com/google/common/collect/ElementTypesAreNonnullByDefault.java",
    )
    needles = ("@ElementTypesAreNonnullByDefault", "@interface ElementTypesAreNonnullByDefault",
               "@NullMarked", "import org.jspecify.annotations.NullMarked;")
    evidence = []
    with ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        for name in paths:
            row = {"source_path_within_jar": name, "present": name in names}
            if name in names:
                content = archive.read(name)
                row.update({
                    "source_file_sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content),
                    "matching_lines": [{"line_1_based": i, "text": text, "matched_markers": matches}
                                       for i, text in enumerate(content.decode("utf-8").splitlines(), 1)
                                       if (matches := [needle for needle in needles if needle in text])],
                })
            evidence.append(row)
    return {"version": release["version"], "sources_jar_path": release["sources_path"],
            "sources_jar_sha256": actual_hash, "line_number_basis": "1-based lines of exact UTF-8 source-JAR entry",
            "marker_searches": list(needles), "files": evidence}


def run(root):
    manifest_path = root / "config/versions.json"
    manifest = json.loads(manifest_path.read_text())
    require(manifest["repository"] == "google/guava", "Wrong study subject")
    releases = {r["version"]: r for r in manifest["versions"]}
    selected = [r['version'] for r in manifest['versions']]
    snapshots = {v: snapshot(root, releases[v]) for v in selected}
    pairs = list(zip(selected, selected[1:]))
    changes = [difference(a, b, snapshots) for a, b in pairs]
    size_rows = {r['version']: r for r in csv_rows(root / 'results/sizes.csv')}
    for v in selected:
        require(len(snapshots[v]['classes']) == int(size_rows[v]['classes']), f'Size summary disagrees for {v}')
        require(len(snapshots[v]['edges']) == int(size_rows[v]['dependencies']), f'Edge summary disagrees for {v}')
    unchanged = []
    for a, b in pairs:
        left, right = snapshots[a], snapshots[b]
        same_nodes, same_edges = set(left["classes"]) == set(right["classes"]), left["edges"] == right["edges"]
        if same_nodes and same_edges:
            unchanged.append({"before_version": a, "after_version": b,
                          "same_canonical_class_identities": same_nodes, "same_directed_binary_edges": same_edges,
                          "class_count": len(left["classes"]), "edge_count": len(left["edges"]),
                          "classes_csv_byte_identical": left["provenance"]["production_file_sha256"]["classes.csv"] == right["provenance"]["production_file_sha256"]["classes.csv"],
                          "dependencies_csv_byte_identical": left["provenance"]["production_file_sha256"]["dependencies.csv"] == right["provenance"]["production_file_sha256"]["dependencies.csv"]})
    annotation_change = max(changes, key=lambda r: r['counts']['removed_annotation_classes'])
    sources = [source_markers(root, releases[v]) for v in
               (annotation_change['before_version'], annotation_change['after_version'])]
    # For every observed class addition/removal, preserve the exact source-entry
    # hash. These are observations of selected snapshots, not claims about the
    # first historical introduction/removal of a feature.
    needed = {v: set() for v in selected}
    for change in changes:
        for key, version_key in [('added_classes', 'after_version'), ('removed_classes', 'before_version')]:
            needed[change[version_key]].update(r['source_file'] for r in change[key])
    source_entries = []
    for v in selected:
        path = root / releases[v]['sources_path']
        require(sha256(path) == releases[v]['sources_sha256'], f'Wrong source artifact for {v}')
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            entries = []
            for name in sorted(needed[v]):
                require(name in names, f'Missing owned source {v}: {name}')
                content = archive.read(name)
                entries.append({'source_path_within_jar': name, 'bytes': len(content),
                                'sha256': hashlib.sha256(content).hexdigest()})
        source_entries.append({'version': v, 'sources_jar_path': releases[v]['sources_path'],
                               'sources_jar_sha256': releases[v]['sources_sha256'], 'files': entries})
    ranked = sorted(changes, key=lambda r: (-abs(r['counts']['edge_change_percent']), r['after_version']))
    return {
        "schema_version": 2, "status": "passed", "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_script_sha256": sha256(Path(__file__)), "versions_manifest_sha256": sha256(manifest_path),
        "method": "Independent set differences over finalized owned-class binary graphs; annotation kinds from class inventory; exact pinned source-JAR entry search",
        "inputs": [snapshots[v]["provenance"] for v in selected], "change_points": changes,
        "transition_count": len(changes),
        "largest_absolute_percentage_edge_changes": [
            {'before_version': r['before_version'], 'after_version': r['after_version'], 'counts': r['counts']}
            for r in ranked[:5]],
        "source_entries_for_observed_class_changes": source_entries,
        "source_evidence": sources, "unchanged_graph_pairs": unchanged,
        "interpretation_limits": [
            "Typed relation counts can overlap within one directed binary class edge and must not be summed as the binary edge count.",
            "Annotation migrations can change the owned-type inventory even when annotation applications are excluded from primary edges. The source markers document metadata changes, not architectural repair.",
            "Largest transitions are ranked for descriptive discussion only after executing the fixed cohort; they do not determine release selection or parameter choices.",
            "Different-length release intervals and bytecode/compiler effects limit causal interpretation; dependency count alone is not semantic complexity.",
            "Equal class/dependency graphs do not imply identical source text or release artifacts.",
            "This audit creates no new architecture and modifies no finalized per-version input/output file.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.root)
    output = args.output or args.root / "results/change_points.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "change_points": len(result["change_points"]),
                      "unchanged_pairs": len(result["unchanged_graph_pairs"]), "output": str(output)}))


if __name__ == "__main__":
    main()
