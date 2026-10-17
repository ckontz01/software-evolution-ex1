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
