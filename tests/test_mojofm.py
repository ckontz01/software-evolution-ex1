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
