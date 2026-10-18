# Commit 09 — Evolution change audits and preserved first baseline

**Student A · 2026-10-22 · 15 complete files · 2 full code/configuration listings**

Source snapshot: `f32e6e831f976eed8bf01faa1d66dbdc34bc49c7`. Dates are planned work sessions; make the commit when you actually import and review this packet.

## What to understand

Investigate the 19.0 to 20.0 change and one later transition; distinguish measured graph changes from release interpretation and historical baseline differences.

## Apply this packet

Set `HANDOFF_DIR` to your extracted student bundle and `TEACHER_REPO` to the teacher checkout. Pull the preceding commit first. Commands below use the `guava-study` layout explained in the main map.

```bash
git -C "$TEACHER_REPO" pull --ff-only origin guava-assignment
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/09-a-evolution-audits" --target "$TEACHER_REPO" --subdir guava-study
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/09-a-evolution-audits" --target "$TEACHER_REPO" --subdir guava-study --apply
cd "$TEACHER_REPO/guava-study"
```

For commit 01, create the shared branch as shown in the main map; its remote branch does not exist until the first push, so omit that first pull.

## Checks before the commit

Run these in the cumulative study directory after applying the packet. For packet 01, first create the Python environment and install the locked requirements as shown in the main map:

```bash
python scripts/audit_change_points.py --output results/rerun/handoff-p09-change-points.json
```

Stage and inspect only this packet, then use your own Git identity:

```bash
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/09-a-evolution-audits" --target "$TEACHER_REPO" --subdir guava-study --apply --stage
git -C "$TEACHER_REPO" diff --cached --stat
git -C "$TEACHER_REPO" diff --cached
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/09-a-evolution-audits" --target "$TEACHER_REPO" --subdir guava-study --check-staged
git -C "$TEACHER_REPO" commit -m 'import: add evolution audits and preserved baseline evidence (AI-assisted preparation)'
git -C "$TEACHER_REPO" push -u origin guava-assignment
```

Add a commit-message paragraph describing the checks you actually performed and anything you found. The import message identifies the prepared source; it does not claim you originally wrote every line.

## Further review checks

The following are useful for learning or final verification. Commands marked as writing evidence belong in a disposable copy, so the next packet still matches the frozen source. These are not additional canonical experiments.

Verify exact old/supplemental/instructor graph decomposition and baseline hashes.

```bash
python scripts/audit_revision.py
```

**Where:** disposable cumulative checkout, preserving immutable packet payloads. **Writes:** rewrites results/revision_comparison.json; use disposable cumulative checkout.

## Every file to push

All files below are present under this packet's `payload/` directory in the complete student download. Paths are relative to the study directory.

| File | Bytes | Content |
|---|---:|---|
| `docs/results_interpretation.md` | 14,169 | documentation or tool provenance |
| `results/baseline_v1/README.md` | 364 | recorded evidence |
| `results/baseline_v1/analysis.json` | 1,384 | recorded evidence |
| `results/baseline_v1/latest_classes.csv` | 80,378 | recorded evidence |
| `results/baseline_v1/latest_dependencies.csv` | 347,898 | recorded evidence |
| `results/baseline_v1/latest_graph_provenance.json` | 488 | recorded evidence |
| `results/baseline_v1/metrics.csv` | 27,774 | recorded evidence |
| `results/baseline_v1/run_manifest.json` | 2,150 | recorded evidence |
| `results/baseline_v1/same_graph_comparisons.csv` | 6,169 | recorded evidence |
| `results/baseline_v1/sizes.csv` | 3,207 | recorded evidence |
| `results/baseline_v1/versions.json` | 57,511 | recorded evidence |
| `results/change_points.json` | 1,574,884 | recorded evidence |
| `results/revision_comparison.json` | 6,772 | recorded evidence |
| `scripts/audit_change_points.py` | 14,856 | Full code below |
| `scripts/audit_revision.py` | 5,852 | Full code below |

The machine-readable `packet.json` pins every file's SHA-256 and Git blob. Binary JAR/PDF/ZIP files and large evidence files are supplied as their exact original bytes in the payload, rather than as text pasted into this guide.

## Whole code

The following are complete files, with no omitted functions. Use the payload for copying so file bytes, line endings and original licences stay intact.

### scripts/audit_change_points.py

SHA-256: `a363af13ad4b62a7cf88ef50eff5e023633e63b955629275ff961b1f42124bfa` · 14,856 bytes

<!-- FULL_SOURCE scripts/audit_change_points.py a363af13ad4b62a7cf88ef50eff5e023633e63b955629275ff961b1f42124bfa -->
```python
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
```
<!-- END_FULL_SOURCE scripts/audit_change_points.py -->

### scripts/audit_revision.py

SHA-256: `412c21d5da788dd000259c609f27c073a3d5546fafd59676e9a35e039073999d` · 5,852 bytes

<!-- FULL_SOURCE scripts/audit_revision.py 412c21d5da788dd000259c609f27c073a3d5546fafd59676e9a35e039073999d -->
```python
#!/usr/bin/env python3
"""Distinguish measured graph-model effects from the combined study revision."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def edges(path):
    return {(r['source'], r['target']) for r in rows(path)}


def main():
    baseline = ROOT / 'results/baseline_v1'
    record = json.loads((baseline / 'latest_graph_provenance.json').read_text())
    for name, expected in record['exported_files'].items():
        if digest(baseline / name) != expected:
            raise ValueError('Preserved original graph changed')
    version = record['version']
    directory = ROOT / 'data/graphs' / version
    old_nodes = {r['class'] for r in rows(baseline / 'latest_classes.csv')}
    new_classes = {r['class']: r for r in rows(directory / 'classes.csv')}
    new_nodes = set(new_classes)
    old = edges(baseline / 'latest_dependencies.csv')
    primary = edges(directory / 'dependencies.csv')
    supplemental = edges(directory / 'supplemental_dependencies.csv')
    annotations = {n for n, r in new_classes.items() if r['kind'] == 'annotation'}
    assert old_nodes <= new_nodes
    assert old == {e for e in supplemental if set(e) <= old_nodes}
    assert primary <= supplemental
    added_scope = new_nodes - old_nodes
    assert all(n.startswith('com.google.thirdparty.publicsuffix.') for n in added_scope)
    primary_in_old_scope = {e for e in primary if set(e) <= old_nodes}
    extra = supplemental - primary
    annotation_extra = {e for e in extra if e[1] in annotations}
    incident = {n for e in primary for n in e}
    old_sizes = {r['version']: r for r in rows(baseline / 'sizes.csv')}
    current_sizes = rows(ROOT / 'results/sizes.csv')
    comparisons = []
    for row in current_sizes:
        if row['version'] in old_sizes:
            previous = old_sizes[row['version']]
            comparisons.append({'version': row['version'],
                'original_classes': int(previous['classes']), 'revised_classes': int(row['classes']),
                'original_edges': int(previous['dependencies']), 'revised_edges': int(row['dependencies']),
                'original_ue_removals': int(previous['omnipresent_classes']),
                'revised_ue_removals': int(row['omnipresent_classes'])})
    types = Counter(r['relation'] for r in rows(directory / 'supplemental_dependencies_typed.csv')
                    if (r['source'], r['target']) in extra and r['target'] not in annotations)
    payload = {
        'schema_version': 1, 'status': 'passed', 'original_commit': record['source_commit'],
        'current_manifest_sha256': digest(ROOT / 'config/versions.json'),
        'current_config_sha256': digest(ROOT / 'config/analysis.json'),
        'latest_version': version, 'latest_controlled_graph_decomposition': {
            'original_common_only': {'classes': len(old_nodes), 'edges': len(old)},
            'supplemental_with_corrected_ownership': {'classes': len(new_nodes), 'edges': len(supplemental)},
            'primary_with_corrected_ownership': {'classes': len(new_nodes), 'edges': len(primary)},
            'instructor_on_original_node_scope': {'classes': len(old_nodes), 'edges': len(primary_in_old_scope)},
            'added_owned_classes': sorted(added_scope),
            'extra_supplemental_edges_from_scope': len(supplemental - old),
            'extra_primary_edges_from_scope': len(primary - primary_in_old_scope),
            'same_node_set_supplemental_minus_instructor': len(extra),
            'same_node_set_annotation_application_edges': len(annotation_extra),
            'same_node_set_other_extractor_edges': len(extra - annotation_extra),
            'other_edge_relation_counts_may_overlap': dict(sorted(types.items())),
            'instructor_only_edges': len(primary - supplemental),
            'annotation_nodes': len(annotations),
            'annotation_isolates': len(annotations - incident),
            'primary_annotation_target_edges': sum(b in annotations for a, b in primary),
            'all_primary_isolates': len(new_nodes - incident),
            'original_edges_exactly_equal_supplemental_projection': True},
        'common_release_count': len(comparisons), 'common_release_size_comparisons': comparisons,
        'interpretation': [
            'At the latest release the graph-set audit separates added first-party ownership from extractor semantics, holding the artifact fixed.',
            'The supplementary graph is an audit and member-evidence aid; none of its extra class edges enter the primary clustering graphs.',
            'Whole-study MQ and agreement differences combine sampling, scope, graph semantics and k policy; they cannot be attributed to any one change.',
            'Annotation declarations remain owned nodes, including isolates. Excluding annotation applications does not mean that all annotations lack runtime semantics.',
            'An identical UE removal count alone is not a proof of extractor or detector correctness. Exact set checks, equation checks and compiled fixtures provide stronger evidence.'],
        'input_sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in [
            baseline/'latest_graph_provenance.json', baseline/'latest_classes.csv', baseline/'latest_dependencies.csv',
            directory/'classes.csv', directory/'dependencies.csv', directory/'supplemental_dependencies.csv']}}
    (ROOT/'results/revision_comparison.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps(payload['latest_controlled_graph_decomposition'],indent=2))


if __name__ == '__main__':
    main()
```
<!-- END_FULL_SOURCE scripts/audit_revision.py -->
