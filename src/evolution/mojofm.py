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
