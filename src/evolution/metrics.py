"""Lecture cohesion, coupling and MQ for a directed binary dependency graph.

For cluster i of size n_i, cohesion is mu_i / (n_i * (n_i - 1)).
For each unordered cluster pair i,j, coupling is epsilon_ij / (2*n_i*n_j),
where epsilon_ij counts dependency edges in BOTH directions. MQ is the
unweighted mean cluster cohesion minus the unweighted mean pair coupling.
Singleton cohesion and the coupling of a one-cluster partition are zero.
The diagonal used in KMeans features is never part of the evaluation graph.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
import csv
from itertools import combinations
from pathlib import Path


def validate_graph(nodes: Iterable[str], edges: Iterable[tuple[str, str]]) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
    """Reject ambiguous counts; callers must explicitly clean/deduplicate first."""
    ordered = tuple(nodes)
    if any(not isinstance(n, str) or not n for n in ordered):
        raise ValueError("Class identifiers must be nonempty strings")
    node_set = set(ordered)
    if len(node_set) != len(ordered):
        raise ValueError("Duplicate class identifiers in node manifest")
    unique: set[tuple[str, str]] = set()
    for edge in edges:
        if isinstance(edge, str):
            raise ValueError("An edge must be a source/target pair")
        pair = tuple(edge)
        if len(pair) != 2:
            raise ValueError("An edge must be a source/target pair")
        source, target = pair
        if source not in node_set or target not in node_set:
            raise ValueError(f"Dependency endpoint outside the internal graph: {pair!r}")
        if source == target:
            raise ValueError(f"Self-loop in evaluation graph: {source}")
        if pair in unique:
            raise ValueError(f"Duplicate binary dependency: {pair!r}")
        unique.add(pair)
    return tuple(sorted(ordered)), tuple(sorted(unique))


def validate_partition(nodes: Iterable[str], assignments: Mapping[str, str] | Iterable[tuple[str, str]]) -> dict[str, str]:
    """Require exactly one cluster per class, including every isolated class."""
    expected = set(nodes)
    rows = assignments.items() if isinstance(assignments, Mapping) else assignments
    result: dict[str, str] = {}
    for row in rows:
        if isinstance(row, str) or len(row) != 2:
            raise ValueError("Membership must contain class/cluster pairs")
        node, cluster = row
        if node in result:
            raise ValueError(f"Duplicate cluster membership for {node}")
        if not isinstance(cluster, str) or not cluster:
            raise ValueError("Cluster identifiers must be nonempty strings")
        result[node] = cluster
    missing, extra = expected - result.keys(), result.keys() - expected
    if missing or extra:
        raise ValueError(f"Partition coverage mismatch; missing={sorted(missing)!r}, extra={sorted(extra)!r}")
    return {node: result[node] for node in sorted(expected)}


def evaluate_partition(nodes: Iterable[str], edges: Iterable[tuple[str, str]], assignments: Mapping[str, str] | Iterable[tuple[str, str]]) -> dict:
    """Return required macro metrics, supplementary statistics, and all terms.

    Empty graphs have zero macro metrics by explicit convention. Only nonempty
    clusters exist in a membership representation. Isolates are retained in n_i.
    Raw cluster-size and edge statistics accompany MQ because graph populations
    and the number of clusters can change the meaning of a comparison.
    """
    nodes, edges = validate_graph(nodes, edges)
    membership = validate_partition(nodes, assignments)
    members: dict[str, list[str]] = defaultdict(list)
    for node, cluster in membership.items():
        members[cluster].append(node)
    clusters = sorted(members)
    sizes = {cluster: len(members[cluster]) for cluster in clusters}
    internal: Counter = Counter()
    incoming: Counter = Counter()
    outgoing: Counter = Counter()
    crossing: Counter = Counter()
    incident: set[str] = set()
    for source, target in edges:
        incident.update((source, target))
        left, right = membership[source], membership[target]
        if left == right:
            internal[left] += 1
        else:
            outgoing[left] += 1
            incoming[right] += 1
            crossing[tuple(sorted((left, right)))] += 1
    per_cluster = []
    for cluster in clusters:
        n = sizes[cluster]
        capacity = n * (n - 1)
        per_cluster.append({
            "cluster": cluster,
            "n_classes": n,
            "internal_edges": internal[cluster],
            "possible_internal_edges": capacity,
            "cohesion": internal[cluster] / capacity if capacity else 0.0,
            "incoming_inter_edges": incoming[cluster],
            "outgoing_inter_edges": outgoing[cluster],
        })
    per_pair = []
    for left, right in combinations(clusters, 2):
        capacity = 2 * sizes[left] * sizes[right]
        epsilon = crossing[(left, right)]
        per_pair.append({
            "cluster_i": left,
            "cluster_j": right,
            "n_i": sizes[left],
            "n_j": sizes[right],
            "inter_edges_both_directions": epsilon,
            "possible_inter_edges": capacity,
            "coupling": epsilon / capacity,
        })
    n, m, k = len(nodes), len(edges), len(clusters)
    cohesion = sum(row["cohesion"] for row in per_cluster) / k if k else 0.0
    coupling = sum(row["coupling"] for row in per_pair) / len(per_pair) if per_pair else 0.0
    internal_edges = sum(internal.values())
    inter_edges = m - internal_edges
    internal_capacity = sum(row["possible_internal_edges"] for row in per_cluster)
    return {
        "n_nodes": n,
        "n_edges": m,
        "n_clusters": k,
        "cohesion": cohesion,
        "coupling": coupling,
        "mq": cohesion - coupling,
        "size_weighted_cohesion": sum(row["cohesion"] * row["n_classes"] for row in per_cluster) / n if n else 0.0,
        "pair_weighted_cohesion": internal_edges / internal_capacity if internal_capacity else 0.0,
        "internal_edges": internal_edges,
        "inter_edges": inter_edges,
        "inter_edge_fraction": inter_edges / m if m else 0.0,
        "graph_density": m / (n * (n - 1)) if n > 1 else 0.0,
        "isolates": n - len(incident),
        "min_cluster_size": min(sizes.values(), default=0),
        "max_cluster_size": max(sizes.values(), default=0),
        "mean_cluster_size": n / k if k else 0.0,
        "singleton_clusters": sum(size == 1 for size in sizes.values()),
        "per_cluster": per_cluster,
        "per_pair": per_pair,
    }


def write_metric_tables(result: dict, directory: str | Path) -> dict[str, str]:
    """Save every cluster/pair term plus one summary row without nested cells."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    tables = {
        "per_cluster.csv": (result["per_cluster"], ["cluster", "n_classes", "internal_edges", "possible_internal_edges", "cohesion", "incoming_inter_edges", "outgoing_inter_edges"]),
        "per_pair.csv": (result["per_pair"], ["cluster_i", "cluster_j", "n_i", "n_j", "inter_edges_both_directions", "possible_inter_edges", "coupling"]),
    }
    summary = {key: value for key, value in result.items() if key not in ("per_cluster", "per_pair")}
    tables["metrics_summary.csv"] = ([summary], list(summary))
    paths = {}
    for filename, (rows, columns) in tables.items():
        path = directory / filename
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        paths[filename] = str(path)
    return paths
