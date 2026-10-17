"""Feature semantics, deterministic recovery, ACDC parsing and isolate integrity."""
from itertools import permutations
from pathlib import Path
import tempfile
import unittest

import numpy as np

from evolution.clustering import build_features, choose_k, cluster_kmeans, parse_acdc_rsf, run_acdc
from evolution.toolchain import ROOT


class StructuralFeatureTests(unittest.TestCase):
    def test_directed_neighbour_features_have_expected_coordinates(self):
        nodes, features = build_features(["b", "a"], [("a", "b")], ["a", "b", "absent"])
        self.assertEqual(nodes, ("a", "b"))
        expected = np.array([[1, 1, 0, 1, 0, 0], [0, 1, 0, 1, 1, 0]], dtype=float) / np.sqrt(3)
        np.testing.assert_allclose(features.toarray(), expected)
        self.assertEqual(features.nnz, 6)

    def test_removed_features_stay_in_schema_but_have_no_evidence(self):
        universe = ["a", "b", "c", "never_present"]
        _, full = build_features(["a", "b", "c"], [("a", "b"), ("b", "c"), ("a", "c")], universe)
        _, filtered = build_features(["a", "c"], [("a", "c")], universe)
        self.assertEqual(full.shape[1], filtered.shape[1])
        self.assertGreater(full[0, 1], 0)
        self.assertEqual(filtered[:, [1, 5]].nnz, 0)
        np.testing.assert_allclose(np.asarray(filtered.multiply(filtered).sum(axis=1)).ravel(), [1, 1])

    def test_isolated_class_has_identity_features_without_graph_edges(self):
        nodes, matrix = build_features(["alone"], [], ["alone", "absent"])
        self.assertEqual(nodes, ("alone",))
        np.testing.assert_allclose(matrix.toarray(), [[1 / np.sqrt(2), 0, 1 / np.sqrt(2), 0]])

    def test_fixed_full_graph_k_is_reused_then_only_clamped(self):
        self.assertEqual(choose_k(800), 20)
        self.assertEqual(choose_k(800, 750), 20)
        self.assertEqual(choose_k(800, 5), 5)
        self.assertEqual(choose_k(0), 0)
        self.assertEqual(choose_k(1), 1)
        with self.assertRaises(ValueError):
            choose_k(10, 11)

    def test_kmeans_is_repeatable_after_input_reordering(self):
        nodes = list("abcdef")
        edges = list(permutations("abc", 2)) + list(permutations("def", 2))
        first, meta = cluster_kmeans(nodes, edges, nodes, 2)
        second, second_meta = cluster_kmeans(reversed(nodes), reversed(edges), nodes, 2)
        self.assertEqual(first, second)
        self.assertEqual(len({first[n] for n in "abc"}), 1)
        self.assertEqual(len({first[n] for n in "def"}), 1)
        self.assertNotEqual(first["a"], first["d"])
        self.assertEqual(meta["feature_universe_sha256"], second_meta["feature_universe_sha256"])

    def test_identical_rows_report_fewer_clusters_without_fake_splitting(self):
        nodes = list("abc")
        assignment, metadata = cluster_kmeans(nodes, permutations(nodes, 2), nodes, 2)
        self.assertEqual(metadata["requested_k"], 2)
        self.assertEqual(metadata["actual_k"], 1)
        self.assertEqual(len(assignment), 3)
        self.assertTrue(metadata["warnings"])

    def test_universe_coverage_and_duplicate_evidence_fail(self):
        for universe in [["a"], ["a", "b", "b"]]:
            with self.assertRaises(ValueError):
                build_features(["a", "b"], [], universe)
        with self.assertRaises(ValueError):
            build_features(["a", "b"], [("a", "b"), ("a", "b")], ["a", "b"])


class AcdcAdapterTests(unittest.TestCase):
    def test_flat_output_and_hierarchy_have_explicit_leaf_parent_meaning(self):
        flat = parse_acdc_rsf("contain c1 a\ncontain c1 b\ncontain c2 c\n", ["a", "b", "c"])
        nested = parse_acdc_rsf("contain top c1\ncontain top c2\ncontain c1 a\ncontain c1 b\ncontain c2 c\n", ["a", "b", "c"])
        self.assertEqual(flat, nested)
        self.assertEqual(flat, {"a": "c1", "b": "c1", "c": "c2"})

    def test_invalid_containment_is_not_silently_scored(self):
        cases = ["contain c a\ncontain c a\n", "contain c1 a\ncontain c2 a\n",
                 "contain c unknown\n", "call c a\n", "contain c1 c2\ncontain c2 c1\n",
                 "contain a b\n"]
        for text in cases:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_acdc_rsf(text, ["a", "b"])

    def test_all_isolate_case_needs_no_java_and_preserves_every_node(self):
        with tempfile.TemporaryDirectory() as directory:
            assignments, metadata = run_acdc(["a", "b"], [], directory, java="no-java-needed")
            self.assertEqual(set(assignments), {"a", "b"})
            self.assertEqual(len(set(assignments.values())), 2)
            self.assertEqual(metadata["isolates_restored_as_singletons"], ["a", "b"])
            self.assertEqual(Path(directory, "input.rsf").read_text(), "")

    @unittest.skipUnless((ROOT / "build/acdc/acdc/ACDC.class").exists(), "Build official ACDC before integration test")
    def test_original_java_process_covers_real_edges_and_isolates(self):
        nodes = ["a", "b", "c", "isolated"]
        edges = [("a", "b"), ("b", "a"), ("b", "c")]
        with tempfile.TemporaryDirectory() as directory:
            assignment, metadata = run_acdc(nodes, edges, directory)
            self.assertEqual(set(assignment), set(nodes))
            self.assertEqual(metadata["returncode"], 0)
            self.assertEqual(metadata["isolates_restored_as_singletons"], ["isolated"])
            self.assertNotIn(assignment["isolated"], [assignment[node] for node in "abc"])
            self.assertEqual(set(metadata["original_containers"]), set("abc"))

    @unittest.skipUnless((ROOT / "build/acdc/acdc/ACDC.class").exists(), "Build official ACDC before integration test")
    def test_file_suffix_prevents_same_package_dominator_name_collisions(self):
        # Original ACDC strips the final dotted suffix to name a cluster.
        # With bare Java IDs both disconnected components would be called pkg.ss.
        nodes = ["pkg." + name for name in "abcdef"]
        edges = list(permutations(nodes[:3], 2)) + list(permutations(nodes[3:], 2))
        with tempfile.TemporaryDirectory() as directory:
            assignment, metadata = run_acdc(nodes, edges, directory)
            self.assertEqual(len({assignment[n] for n in nodes[:3]}), 1)
            self.assertEqual(len({assignment[n] for n in nodes[3:]}), 1)
            self.assertNotEqual(assignment[nodes[0]], assignment[nodes[3]])
            self.assertEqual(set(assignment), set(nodes))
            self.assertTrue(all(token.endswith(".java") for line in
                                Path(directory, "input.rsf").read_text().splitlines()
                                for token in line.split()[1:]))
            self.assertEqual(len(set(metadata["original_containers"].values())), 2)


if __name__ == "__main__":
    unittest.main()
