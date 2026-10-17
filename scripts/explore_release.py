#!/usr/bin/env python3
"""Optional, explicitly separate parameter exploration for a single release.

This does not alter the frozen study or its configuration. --k lets a reviewer
choose the number of k-means clusters directly without a k sweep.
"""
import argparse
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('LOKY_MAX_CPU_COUNT', '1')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evolution.clustering import choose_k, cluster_kmeans, run_acdc
from evolution.graph import read_csv, read_graph, write_json
from evolution.metrics import evaluate_partition, write_metric_tables
from evolution.omnipresent import detect_omnipresent
from evolution.study import save_partition
from evolution.toolchain import build_java

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='33.7.2')
    parser.add_argument('--k', type=int, help='Explicit k, shared by full/filtered fits; default frozen size rule')
    parser.add_argument('--acdc-size', type=int, default=20)
    parser.add_argument('--usage-threshold', type=float, default=.85)
    parser.add_argument('--cardinality-threshold', type=float, default=.90)
    parser.add_argument('--output', type=Path, required=True, help='Must be a new directory; choose results/rerun/...')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output must be a new directory so recorded results are not overwritten')
    source = ROOT / 'data/graphs' / args.version
    graph = read_graph(source)
    universe = json.loads((ROOT / 'data/graphs/feature_universe.json').read_text())
    noise = detect_omnipresent(graph.nodes, read_csv(source / 'member_dependencies.csv'),
                               usage_threshold=args.usage_threshold, cardinality_threshold=args.cardinality_threshold)
    filtered = graph.without(noise.removed_classes)
    k = args.k if args.k is not None else choose_k(len(graph.nodes))
    if k < 1 or args.acdc_size < 1:
        parser.error('k and acdc-size must be positive')
    build_java()
    args.output.mkdir(parents=True)
    write_json(args.output / 'experiment.json', {**vars(args), 'output': str(args.output), 'k': k,
                'status': 'optional exploration, excluded from frozen30-release results'})
    write_json(args.output / 'ue.json', noise.to_dict(include_dedications=True))
    for condition, method, current in [('A1','ACDC',graph),('A2','ACDC',filtered),('A3','kmeans',graph),('A4','kmeans',filtered)]:
        if method == 'ACDC':
            assignment, metadata = run_acdc(current.nodes, current.edges, args.output / (condition+'_run'), max_size=args.acdc_size)
        else:
            assignment, metadata = cluster_kmeans(current.nodes, current.edges, universe, k, random_state=484, n_init=10)
        save_partition(args.output / (condition+'.csv'), assignment)
        write_json(args.output / (condition+'_run.json'), metadata)
        metrics = evaluate_partition(current.nodes, current.edges, assignment)
        write_json(args.output / (condition+'_metrics.json'), metrics)
        write_metric_tables(metrics, args.output / (condition+'_quality'))
        print(condition, 'clusters', metrics['n_clusters'], 'MQ', metrics['mq'])
