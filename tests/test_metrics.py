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
