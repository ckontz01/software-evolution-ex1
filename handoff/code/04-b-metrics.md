# Commit 04 — Lecture quality metrics and MoJoFM

**Student B · 2026-10-19 · 5 complete files · 4 full code/configuration listings**

Source snapshot: `a8186f58fb22ffd7ebbe68964ded49006f12aef4`. Dates are planned work sessions; make the commit when you actually import and review this packet.

## What to understand

Calculate cohesion, coupling and MQ on a small partition; explain why MoJoFM has two directions and why agreement is not architectural ground truth.

## Apply this packet

Set `HANDOFF_DIR` to your extracted student bundle and `TEACHER_REPO` to the teacher checkout. Pull the preceding commit first. Commands below use the `guava-study` layout explained in the main map.

```bash
git -C "$TEACHER_REPO" pull --ff-only origin guava-assignment
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/04-b-metrics" --target "$TEACHER_REPO" --subdir guava-study
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/04-b-metrics" --target "$TEACHER_REPO" --subdir guava-study --apply
cd "$TEACHER_REPO/guava-study"
```

For commit 01, create the shared branch as shown in the main map; its remote branch does not exist until the first push, so omit that first pull.

## Checks before the commit

Run these in the cumulative study directory after applying the packet. For packet 01, first create the Python environment and install the locked requirements as shown in the main map:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_metrics.py' -v
PYTHONPATH=src python -m unittest discover -s tests -p 'test_mojofm.py' -v
```

Stage and inspect only this packet, then use your own Git identity:

```bash
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/04-b-metrics" --target "$TEACHER_REPO" --subdir guava-study --apply --stage
git -C "$TEACHER_REPO" diff --cached --stat
git -C "$TEACHER_REPO" diff --cached
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/04-b-metrics" --target "$TEACHER_REPO" --subdir guava-study --check-staged
git -C "$TEACHER_REPO" commit -m 'import: add lecture MQ metrics and directional MoJoFM (AI-assisted preparation)'
git -C "$TEACHER_REPO" push -u origin guava-assignment
```

Add a commit-message paragraph describing the checks you actually performed and anything you found. The import message identifies the prepared source; it does not claim you originally wrote every line.

## Every file to push

All files below are present under this packet's `payload/` directory in the complete student download. Paths are relative to the study directory.

| File | Bytes | Content |
|---|---:|---|
| `docs/mojofm.md` | 8,101 | documentation or tool provenance |
| `src/evolution/metrics.py` | 7,846 | Full code below |
| `src/evolution/mojofm.py` | 6,913 | Full code below |
| `tests/test_metrics.py` | 4,367 | Full code below |
| `tests/test_mojofm.py` | 8,965 | Full code below |

The machine-readable `packet.json` pins every file's SHA-256 and Git blob. Binary JAR/PDF/ZIP files and large evidence files are supplied as their exact original bytes in the payload, rather than as text pasted into this guide.

## Whole code

The following are complete files, with no omitted functions. Use the payload for copying so file bytes, line endings and original licences stay intact.

### src/evolution/metrics.py

SHA-256: `a5d2c105e70445e9218d7df9f877b731349b03c3d62938562586a6ea8e73164d` · 7,846 bytes

<!-- FULL_SOURCE src/evolution/metrics.py a5d2c105e70445e9218d7df9f877b731349b03c3d62938562586a6ea8e73164d -->
```python
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
```
<!-- END_FULL_SOURCE src/evolution/metrics.py -->

### src/evolution/mojofm.py

SHA-256: `d0b519341b632f867d8e8e0fdfc544b14724a3022f2aed9c7f508fee3bc91192` · 6,913 bytes

<!-- FULL_SOURCE src/evolution/mojofm.py d0b519341b632f867d8e8e0fdfc544b14724a3022f2aed9c7f508fee3bc91192 -->
```python
"""Exact directional Move/Join distance and target-normalized MoJoFM.

The numerator is mno(source, target), NOT the minimum of the two directions.
Wen and Tzerpos, IWPC 2004, sections 3--4, give the exact algorithms used here:
https://www.eecs.yorku.ca/~bil/publications/mojofm.pdf

Only flat, complete partitions of the same node universe are accepted. A caller
comparing different releases or a filtered graph must explicitly project both
partitions onto a declared common universe before invoking this module.
"""
from __future__ import annotations

from collections import Counter, deque
from collections.abc import Mapping


def _validate_partition(partition: Mapping[str, str], name: str) -> dict[str, str]:
    if not isinstance(partition, Mapping):
        raise ValueError(f"{name} must be a node-to-cluster mapping")
    result = dict(partition)
    for node, cluster in result.items():
        if not isinstance(node, str) or not node:
            raise ValueError(f"{name} node identifiers must be nonempty strings")
        if not isinstance(cluster, str) or not cluster:
            raise ValueError(f"{name} cluster identifiers must be nonempty strings")
    return result


def _maximum_matching(adjacency: list[tuple[int, ...]], n_right: int) -> int:
    """Maximum cardinality matching using iterative augmenting paths.

    Each edge is an equally best overlap for its source cluster. Greedily taking
    the first tied target can require unnecessary joins; alternating paths allow
    a previous match to move so that another target group remains nonempty.
    Iteration avoids a recursion-depth dependency for large decompositions.
    """
    left_match = [-1] * len(adjacency)
    right_match = [-1] * n_right
    cardinality = 0
    for start in range(len(adjacency)):
        queue = deque([start])
        seen_left = {start}
        # predecessor[right] is the source that reached that target in the
        # alternating-path search. It also marks already visited targets.
        predecessor: dict[int, int] = {}
        free_right = -1
        while queue and free_right < 0:
            left = queue.popleft()
            for right in adjacency[left]:
                if right in predecessor:
                    continue
                predecessor[right] = left
                matched_left = right_match[right]
                if matched_left < 0:
                    free_right = right
                    break
                if matched_left not in seen_left:
                    seen_left.add(matched_left)
                    queue.append(matched_left)
        if free_right < 0:
            continue
        right = free_right
        while right >= 0:
            left = predecessor[right]
            previous_right = left_match[left]
            left_match[left] = right
            right_match[right] = left
            right = previous_right
        cardinality += 1
    return cardinality


def _normalizer(target: Mapping[str, str]) -> tuple[int, int]:
    """Return maximum distance TO target and its worst-case group count."""
    groups = 0
    for size in sorted(Counter(target.values()).values()):
        if size > groups:
            groups += 1
    return len(target) - groups, groups


def mojo_max_distance(target: Mapping[str, str]) -> int:
    """Return max_X mno(X, target) over all partitions of target's nodes.

    The normalizer depends on all target cluster sizes. In general it is NOT
    n minus the number of target clusters. Empty and one-node universes return
    zero because they each admit only one partition.
    """
    target = _validate_partition(target, "target")
    return _normalizer(target)[0]


def compare_mojofm(source: Mapping[str, str], target: Mapping[str, str]) -> dict:
    """Calculate exact distance and MoJoFM agreement from source to target.

    A Move transfers one node to an existing or newly created cluster. A Join
    merges two whole clusters. Empty clusters disappear without an operation.
    Cluster labels have no semantic effect. All operations have unit cost.

    Returns a 0--100 ``score`` when the target normalizer is positive. For zero
    or one node, the distance is zero but normalized MoJoFM is undefined (0/0):
    ``score`` is None and ``defined`` is False with an explicit ``reason``.
    The reported move and join counts describe one optimal construction; other
    optimal sequences may split their operations differently.

    This measures agreement with the chosen target. Calling it architectural
    recovery accuracy requires an independently validated reference target.
    """
    source = _validate_partition(source, "source")
    target = _validate_partition(target, "target")
    if source.keys() != target.keys():
        only_source = sorted(source.keys() - target.keys())
        only_target = sorted(target.keys() - source.keys())
        raise ValueError(
            "MoJoFM requires the same node universe; "
            f"only_source={only_source!r}, only_target={only_target!r}"
        )

    source_labels = sorted(set(source.values()))
    target_labels = sorted(set(target.values()))
    source_index = {label: i for i, label in enumerate(source_labels)}
    target_index = {label: j for j, label in enumerate(target_labels)}
    intersections: list[Counter[int]] = [Counter() for _ in source_labels]
    for node in sorted(source):
        intersections[source_index[source[node]]][target_index[target[node]]] += 1

    overlap_sum = 0
    adjacency: list[tuple[int, ...]] = []
    for row in intersections:
        largest = max(row.values())
        overlap_sum += largest
        adjacency.append(tuple(sorted(j for j, size in row.items() if size == largest)))
    matched = _maximum_matching(adjacency, len(target_labels))
    moves = len(source) - overlap_sum
    joins = len(source_labels) - matched
    distance = moves + joins
    maximum, normalizer_groups = _normalizer(target)
    if not 0 <= distance <= maximum:
        raise ArithmeticError("MoJo distance is outside its exact target normalizer")

    return {
        "direction": "source_to_target",
        "n_nodes": len(source),
        "source_clusters": len(source_labels),
        "target_clusters": len(target_labels),
        "move_operations": moves,
        "join_operations": joins,
        "matched_target_clusters": matched,
        "normalizer_groups": normalizer_groups,
        "distance": distance,
        "max_distance": maximum,
        "score": 100.0 * (maximum - distance) / maximum if maximum else None,
        "defined": maximum > 0,
        "reason": None if maximum else (
            "empty_universe" if not source else "single_node_universe"
        ),
    }


def mojo_distance(source: Mapping[str, str], target: Mapping[str, str]) -> int:
    """Return the directed minimum number of Move and Join operations."""
    return compare_mojofm(source, target)["distance"]
```
<!-- END_FULL_SOURCE src/evolution/mojofm.py -->

### tests/test_metrics.py

SHA-256: `5a31838dd5a3aafd57acf473e32d924e3b94f6456456bd0e3a7be67eb3f440ef` · 4,367 bytes

<!-- FULL_SOURCE tests/test_metrics.py 5a31838dd5a3aafd57acf473e32d924e3b94f6456456bd0e3a7be67eb3f440ef -->
```python
"""Hand-derived metric oracles and scope checks, independent of aggregation code."""
from itertools import permutations
from pathlib import Path
import tempfile
import unittest

from evolution.metrics import evaluate_partition, write_metric_tables


class LectureMetricTests(unittest.TestCase):
    def test_two_complete_pairs_and_one_crossing_edge(self):
        # mu_1=mu_2=2; n_1=n_2=2; epsilon_12=1.
        # Cohesion=(1+1)/2=1; coupling=1/(2*2*2)=1/8; MQ=7/8.
        nodes = list("abcd")
        edges = [("a", "b"), ("b", "a"), ("c", "d"), ("d", "c"), ("b", "c")]
        assignments = {"a": "one", "b": "one", "c": "two", "d": "two"}
        result = evaluate_partition(nodes, edges, assignments)
        self.assertAlmostEqual(result["cohesion"], 1)
        self.assertAlmostEqual(result["coupling"], 1 / 8)
        self.assertAlmostEqual(result["mq"], 7 / 8)
        self.assertEqual(result["internal_edges"], 4)
        self.assertEqual(result["inter_edges"], 1)
        self.assertAlmostEqual(result["inter_edge_fraction"], 1 / 5)
        self.assertEqual(result["per_pair"][0]["inter_edges_both_directions"], 1)

    def test_macro_cohesion_differs_from_weighted_supplements(self):
        # Three-node cluster with 2 of 6 possible edges, plus one isolate.
        # Mean cohesion=(1/3+0)/2=1/6; size-weighted=1/4.
        result = evaluate_partition(list("abcd"), [("a", "b"), ("b", "a")],
                                    {"a": "one", "b": "one", "c": "one", "d": "two"})
        self.assertAlmostEqual(result["cohesion"], 1 / 6)
        self.assertAlmostEqual(result["size_weighted_cohesion"], 1 / 4)
        self.assertAlmostEqual(result["pair_weighted_cohesion"], 1 / 3)
        self.assertEqual(result["isolates"], 2)
        self.assertEqual(result["singleton_clusters"], 1)

    def test_coupling_average_includes_pairs_with_no_edges(self):
        # Three singleton clusters: pair AB=1/2; AC=BC=0; mean=1/6.
        result = evaluate_partition(list("abc"), [("a", "b")], {n: n for n in "abc"})
        self.assertEqual(len(result["per_pair"]), 3)
        self.assertAlmostEqual(result["coupling"], 1 / 6)
        self.assertAlmostEqual(result["mq"], -1 / 6)

    def test_complete_singleton_partition_counts_both_directions(self):
        nodes = list("abc")
        result = evaluate_partition(nodes, permutations(nodes, 2), {n: n for n in nodes})
        self.assertEqual(result["cohesion"], 0)
        self.assertEqual(result["coupling"], 1)
        self.assertEqual(result["mq"], -1)

    def test_single_cluster_has_zero_coupling(self):
        result = evaluate_partition(["a", "b"], [("a", "b")], {"a": "one", "b": "one"})
        self.assertEqual(result["coupling"], 0)
        self.assertEqual(result["mq"], 0.5)

    def test_empty_and_all_isolated_graphs(self):
        empty = evaluate_partition([], [], {})
        self.assertEqual((empty["mq"], empty["n_clusters"], empty["min_cluster_size"]), (0, 0, 0))
        isolated = evaluate_partition(["a", "b"], [], {"a": "x", "b": "y"})
        self.assertEqual((isolated["mq"], isolated["isolates"]), (0, 2))

    def test_every_class_requires_exactly_one_membership(self):
        for assignments in [{"a": "x"}, {"a": "x", "b": "y", "extra": "z"},
                            [("a", "x"), ("a", "x"), ("b", "y")],
                            [("a", "x"), ("a", "y"), ("b", "y")]]:
            with self.subTest(assignments=assignments), self.assertRaises(ValueError):
                evaluate_partition(["a", "b"], [], assignments)

    def test_graph_requires_explicit_scope_and_binary_cleaning(self):
        cases = [(["a", "a"], []), (["a", "b"], [("a", "outside")]),
                 (["a", "b"], [("a", "a")]),
                 (["a", "b"], [("a", "b"), ("a", "b")])]
        for nodes, edges in cases:
            with self.subTest(nodes=nodes, edges=edges), self.assertRaises(ValueError):
                evaluate_partition(nodes, edges, {node: "one" for node in nodes})

    def test_csvs_preserve_terms_and_headers_when_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = write_metric_tables(evaluate_partition([], [], {}), directory)
            self.assertEqual(len(paths), 3)
            for path in paths.values():
                self.assertTrue(Path(path).read_text().strip())


if __name__ == "__main__":
    unittest.main()
```
<!-- END_FULL_SOURCE tests/test_metrics.py -->

### tests/test_mojofm.py

SHA-256: `3a1b1bc9a7b8523694afd7333d08ac3bda6fadcd2d4ab6621a6a7d5bd7cd2262` · 8,965 bytes

<!-- FULL_SOURCE tests/test_mojofm.py 3a1b1bc9a7b8523694afd7333d08ac3bda6fadcd2d4ab6621a6a7d5bd7cd2262 -->
```python
"""Lecture examples and an independent exact search over Move/Join operations.

The exhaustive oracle constructs the graph of every set partition for n <= 5.
Breadth-first search finds shortest operation sequences without using overlap
maxima, matching, or the production normalizer formula.
"""
from collections import deque
from itertools import combinations
import unittest

from evolution.mojofm import compare_mojofm, mojo_distance, mojo_max_distance


def membership(*groups):
    """Convert explicit test groups into node-to-cluster mappings."""
    return {str(node): str(i) for i, group in enumerate(groups) for node in group}


def canonical(labels):
    """Identify equivalent partitions after relabeling or empty-group removal."""
    renaming = {}
    return tuple(renaming.setdefault(label, len(renaming)) for label in labels)


def set_partitions(n):
    if n == 0:
        return [()]
    states = [(0,)]
    for _ in range(n - 1):
        states = [state + (label,) for state in states
                  for label in range(max(state) + 2)]
    return states


def operation_neighbors(state):
    """Every partition obtainable by one actual Move or Join operation."""
    neighbors = set()
    cluster_count = max(state, default=-1) + 1
    # Move to each current cluster or to one fresh singleton cluster.
    for node in range(len(state)):
        for destination in range(cluster_count + 1):
            changed = list(state)
            changed[node] = destination
            neighbors.add(canonical(changed))
    # Join any two whole clusters. This operation need not have an inverse Join.
    for left, right in combinations(range(cluster_count), 2):
        neighbors.add(canonical(left if group == right else group for group in state))
    neighbors.discard(state)
    return neighbors


def shortest_paths(start, neighbors):
    distance = {start: 0}
    queue = deque([start])
    while queue:
        source = queue.popleft()
        for target in neighbors[source]:
            if target not in distance:
                distance[target] = distance[source] + 1
                queue.append(target)
    return distance


class MoJoFMTests(unittest.TestCase):
    def test_all_lecture_examples_on_pages_30_to_32(self):
        # Position labels for the eight unlabelled nodes in the lecture figure:
        # a/b/c = left top/bottom/middle; d/e/f = right top-left/top-right/middle;
        # g/h = bottom left/right. The reference contains abc, def, gh.
        reference = membership("abc", "def", "gh")
        examples = {
            "A": (membership(*"abcdefgh"), 5, 0.0),
            "B": (membership("abc", "def", "gh"), 0, 100.0),
            "Gamma": (membership("abc", "defgh"), 2, 60.0),
            "Delta": (membership("a", "bcg", "defh"), 3, 40.0),
        }
        for name, (source, distance, score) in examples.items():
            with self.subTest(name=name):
                result = compare_mojofm(source, reference)
                self.assertEqual(result["distance"], distance)
                self.assertEqual(result["max_distance"], 5)
                self.assertEqual(result["score"], score)

    def test_primary_paper_sixteen_object_example(self):
        source = membership(range(1, 5), range(5, 9), range(9, 13), range(13, 17))
        target = membership([1, 2, 7, 8], [4, 5, 6, 11, 12, 13, 14],
                            [9, 10, 15, 16], [3])
        result = compare_mojofm(source, target)
        self.assertEqual(result["move_operations"], 8)
        self.assertEqual(result["join_operations"], 1)
        self.assertEqual(result["matched_target_clusters"], 3)
        self.assertEqual(result["distance"], 9)
        self.assertEqual(result["max_distance"], 12)
        self.assertEqual(result["score"], 25.0)

    def test_tied_overlap_requires_rematching(self):
        # First row can choose either target; second can choose only target 0.
        # Taking target 0 greedily for the first row would add an unnecessary Join.
        source = membership("ab", "c")
        target = membership("ac", "b")
        result = compare_mojofm(source, target)
        self.assertEqual(result["matched_target_clusters"], 2)
        self.assertEqual(result["move_operations"], 1)
        self.assertEqual(result["join_operations"], 0)
        self.assertEqual(result["distance"], 1)

    def test_direction_and_target_normalization_are_not_symmetric(self):
        one = membership("abcd")
        two = membership("ab", "cd")
        forward = compare_mojofm(one, two)
        reverse = compare_mojofm(two, one)
        self.assertEqual((forward["distance"], forward["max_distance"]), (2, 2))
        self.assertEqual((reverse["distance"], reverse["max_distance"]), (1, 3))
        self.assertEqual(forward["score"], 0.0)
        self.assertAlmostEqual(reverse["score"], 100 * 2 / 3)

    def test_normalizer_is_not_always_n_minus_number_of_clusters(self):
        target = membership("a", "b", "cde")
        farthest = membership("abc", "d", "e")
        self.assertEqual(mojo_max_distance(target), 3)
        self.assertEqual(mojo_distance(farthest, target), 3)
        self.assertEqual(compare_mojofm(farthest, target)["score"], 0.0)

    def test_labels_and_mapping_order_do_not_affect_the_score(self):
        source = membership("abc", "d", "ef")
        target = membership("ade", "bcf")
        relabeled_source = {node: f"source-{int(source[node]) + 13}"
                            for node in reversed(list(source))}
        relabeled_target = {node: f"target-{int(target[node]) + 17}"
                            for node in reversed(list(target))}
        self.assertEqual(compare_mojofm(source, target),
                         compare_mojofm(relabeled_source, relabeled_target))

    def test_singletons_one_cluster_and_unobserved_empty_clusters(self):
        singletons = membership(*"abcde")
        one = membership("abcde")
        self.assertEqual(mojo_distance(singletons, one), 4)
        self.assertEqual(mojo_distance(one, singletons), 4)
        self.assertEqual(compare_mojofm(singletons, singletons)["score"], 100.0)
        self.assertEqual(compare_mojofm(one, one)["score"], 100.0)
        self.assertEqual(compare_mojofm(one, one)["source_clusters"], 1)

    def test_zero_normalizer_is_explicitly_undefined(self):
        for source, target, reason in [({}, {}, "empty_universe"),
                                       ({"a": "x"}, {"a": "y"}, "single_node_universe")]:
            with self.subTest(reason=reason):
                result = compare_mojofm(source, target)
                self.assertEqual(result["distance"], 0)
                self.assertEqual(result["max_distance"], 0)
                self.assertFalse(result["defined"])
                self.assertIsNone(result["score"])
                self.assertEqual(result["reason"], reason)

    def test_mismatched_universes_are_rejected_without_projection(self):
        for source, target in [({"a": "x"}, {}), ({}, {"a": "x"}),
                               ({"a": "x", "b": "x"}, {"a": "x", "c": "x"})]:
            with self.subTest(source=source, target=target), self.assertRaises(ValueError):
                compare_mojofm(source, target)

    def test_invalid_memberships_are_rejected(self):
        for partition in [[("a", "x")], {"": "x"}, {1: "x"},
                          {"a": ""}, {"a": None}, {"a": 0}]:
            with self.subTest(partition=partition), self.assertRaises(ValueError):
                compare_mojofm(partition, partition)
            with self.subTest(partition=partition), self.assertRaises(ValueError):
                mojo_max_distance(partition)

    def test_every_partition_pair_through_five_nodes_against_operation_bfs(self):
        pairs = 0
        for n in range(6):
            states = set_partitions(n)
            neighbors = {state: operation_neighbors(state) for state in states}
            actual = {state: shortest_paths(state, neighbors) for state in states}
            assignments = {state: {str(i): str(label) for i, label in enumerate(state)}
                           for state in states}
            for target in states:
                expected_max = max(actual[source][target] for source in states)
                self.assertEqual(mojo_max_distance(assignments[target]), expected_max)
                for source in states:
                    result = compare_mojofm(assignments[source], assignments[target])
                    self.assertEqual(result["distance"], actual[source][target],
                                     (n, source, target))
                    self.assertEqual(result["max_distance"], expected_max)
                    if expected_max:
                        expected = 100 * (expected_max - actual[source][target]) / expected_max
                        self.assertEqual(result["score"], expected)
                    pairs += 1
        self.assertEqual(pairs, 2960)


if __name__ == "__main__":
    unittest.main()
```
<!-- END_FULL_SOURCE tests/test_mojofm.py -->
