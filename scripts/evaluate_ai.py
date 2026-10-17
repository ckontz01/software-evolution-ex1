#!/usr/bin/env python3
"""Score the recorded AI partition only after its blind recovery is complete."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evolution.graph import read_csv, read_graph, write_csv, write_json, sha256
from evolution.metrics import evaluate_partition, write_metric_tables
from evolution.mojofm import compare_mojofm
from evolution.study import compare_partitions, load_partition


def main() -> None:
    directory = ROOT / 'results/ai'
    record = json.loads((directory / 'experiment.json').read_text())
    version = record['version']
    if sha256(ROOT / record['prompt_file']) != record['prompt_sha256']:
        raise ValueError('Recorded prompt changed')
    for item in record['input_files']:
        if sha256(ROOT / item['path']) != item['sha256']:
            raise ValueError(f'AI evidence changed: {item["path"]}')
    for item in record.get('additional_prompt_files', []):
        if sha256(ROOT / item['path']) != item['sha256']:
            raise ValueError(f'Additional prompt changed: {item["path"]}')
    graph = read_graph(ROOT / 'data/graphs' / version)
    assignment = load_partition(directory / 'assignment.csv')
    metrics = evaluate_partition(graph.nodes, graph.edges, assignment)
    architecture = json.loads((directory / 'architecture.json').read_text())
    declared = {item['id']: item['class_count'] for item in architecture['modules']}
    if declared != dict(Counter(assignment.values())):
        raise ValueError('AI module declaration counts disagree with actual membership')
    # The archived retained-class manifest is authoritative for comparison scope.
    retained = {r['class'] for r in read_csv(ROOT / 'results/versions' / version / 'retained_classes.csv')}
    filtered = graph.without(set(graph.nodes) - retained)
    projected = {n: assignment[n] for n in filtered.nodes}
    retained_metrics = evaluate_partition(filtered.nodes, filtered.edges, projected)
    write_json(directory / 'metrics.json', metrics)
    write_json(directory / 'retained_metrics.json', retained_metrics)
    write_metric_tables(metrics, directory / 'quality_full')
    write_metric_tables(retained_metrics, directory / 'quality_retained')
    comparisons = []
    details = []
    for condition in ('A1', 'A2', 'A3', 'A4'):
        current = filtered if condition in ('A2', 'A4') else graph
        baseline = load_partition(ROOT / 'results/versions' / version / (condition + '.csv'))
        base_metrics = evaluate_partition(current.nodes, current.edges, baseline)
        ai = projected if current is filtered else assignment
        ai_metrics = retained_metrics if current is filtered else metrics
        forward, reverse = compare_mojofm(ai, baseline), compare_mojofm(baseline, ai)
        comparisons.append({'condition': condition, 'graph': 'retained' if current is filtered else 'full',
                            'n_nodes': len(current.nodes), 'n_edges': len(current.edges),
                            'baseline_mq': base_metrics['mq'], 'ai_mq': ai_metrics['mq'],
                            'adjusted_rand_agreement': compare_partitions(baseline, ai, current.nodes),
                            'mojofm_ai_to_baseline': forward['score'],
                            'mojofm_baseline_to_ai': reverse['score'],
                            'mojo_distance_ai_to_baseline': forward['distance'],
                            'mojo_distance_baseline_to_ai': reverse['distance'],
                            'mojo_max_distance_ai_to_baseline': forward['max_distance'],
                            'mojo_max_distance_baseline_to_ai': reverse['max_distance'],
                            'node_universe_sha256': hashlib.sha256(('\n'.join(sorted(current.nodes)) + '\n').encode()).hexdigest()})
        details.append({'comparison': comparisons[-1], 'ai_to_baseline': forward, 'baseline_to_ai': reverse})
    write_csv(directory / 'comparisons.csv', comparisons)
    write_json(directory / 'partition_comparisons.json', {'version': version, 'comparisons': details})
    outputs = ['initial_hypothesis.md', 'assignment.csv', 'architecture.json', 'response.md', 'activity.json']
    if not all((directory / name).is_file() for name in outputs):
        raise ValueError('Incomplete recorded AI response')
    write_json(directory / 'evaluation.json', {'version': version, 'status': 'passed',
               'classes_assigned_exactly_once': len(assignment), 'modules': len(declared),
               'external_or_invented_classes': 0, 'input_hashes_verified': True,
               'output_sha256': {name: sha256(directory / name) for name in outputs},
               'metric_scope': 'Every comparison uses identical class and edge sets; retained AI assignment is a projection, not a new AI recovery.',
               'quality_claim': 'MoJoFM in both directions measures partition agreement, not accuracy; ARI is supplementary. No validated intended-architecture ground truth is available.'})
    print(json.dumps({'version': version, 'modules': len(declared), 'full_mq': metrics['mq'], 'retained_mq': retained_metrics['mq'], 'comparisons': comparisons}, indent=2))


if __name__ == '__main__':
    main()
