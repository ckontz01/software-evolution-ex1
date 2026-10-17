"""Known knee, weak curve and invalid-evidence cases for the pilot policy."""
import unittest
from evolution.k_selection import select_elbow


class ElbowTests(unittest.TestCase):
    def test_known_bend_selected_independently_of_quality_scores(self):
        points = [{"k": k, "inertia": i, "mq": mq} for k, i, mq in
                  [(2, 100, .9), (10, 40, -.8), (20, 35, 1.0), (30, 30, .8)]]
        result = select_elbow(points)
        self.assertEqual(result["selected_k"], 10)
        self.assertTrue(result["clear_elbow"])
        for p in points:
            p["mq"] = 99
        self.assertEqual(select_elbow(points), result)

    def test_linear_curve_uses_predeclared_fallback(self):
        result = select_elbow([{"k": 2, "inertia": 100}, {"k": 16, "inertia": 60}, {"k": 30, "inertia": 20}])
        self.assertFalse(result["clear_elbow"])
        self.assertEqual(result["selected_k"], 30)

    def test_flat_curve_retains_finite_diagnostics(self):
        result = select_elbow([{"k": 2, "inertia": 0}, {"k": 10, "inertia": 0}], fallback_k=30)
        self.assertFalse(result["clear_elbow"])
        self.assertEqual(result["selected_k"], 10)
        self.assertIsNone(result["curve"][0]["normalized_inertia"])

    def test_duplicate_or_nonfinite_evidence_rejected(self):
        for points in ([], [{"k": 2, "inertia": 5}, {"k": 2, "inertia": 1}], [{"k": 2, "inertia": float('nan')}], [{"k": 2, "inertia": -1}]):
            with self.subTest(points=points), self.assertRaises(ValueError):
                select_elbow(points)


if __name__ == '__main__':
    unittest.main()
