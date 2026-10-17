"""Meaningful UE checks: paper equations, exact thresholds, and scope integrity."""

from fractions import Fraction
import json
import random
import unittest

from evolution.omnipresent import detect_omnipresent


def row(source_class, source_member, target_class, target_member):
    return {
        "source_class": source_class,
        "source_member": f"{source_class}#{source_member}",
        "target_class": target_class,
        "target_member": f"{target_class}#{target_member}",
    }


def exact_paper_oracle(classes, rows, usage=Fraction(17, 20), cardinality=Fraction(9, 10)):
    """Deliberately slow set definitions and Fraction arithmetic from Eq. 1--3.

    This independently expresses the mathematical sets instead of copying the
    optimized implementation's aggregation steps.
    """
    classes = set(classes)
    edges = {
        (r["source_class"], r["source_member"], r["target_class"], r["target_member"])
        for r in rows
        if r["source_class"] in classes
        and r["target_class"] in classes
        and r["source_class"] != r["target_class"]
    }
    result = {}
    for target_class in classes:
        incoming = {edge for edge in edges if edge[2] == target_class}
        callers = {edge[0] for edge in incoming}
        targets = {edge[3] for edge in incoming}
        if not callers:
            result[target_class] = (0, 0, None, None, None, False)
            continue
        dedication = {}
        for caller in callers:
            used = {edge[3] for edge in incoming if edge[0] == caller}
            dedication[caller] = sum(
                (
                    Fraction(1, len({edge[1] for edge in incoming if edge[3] == member}) * len(targets))
                    for member in used
                ),
                Fraction(),
            )
        maximum = max(dedication.values())
        equality = 1 - maximum
        c = 1 - Fraction(1, len(callers))
        result[target_class] = (
            len(callers), len(targets), maximum, equality, c,
            equality >= usage and c >= cardinality,
        )
    return result


class TestUsageEquality(unittest.TestCase):
    def test_empty_and_isolated_classes_have_no_invented_evidence(self):
        self.assertEqual(detect_omnipresent([], []).removed_classes, ())
        result = detect_omnipresent(["Alone"], [])
        score = result.by_class()["Alone"]
        self.assertEqual(score.reason, "no_external_member_use")
        self.assertIsNone(score.usage_equality)
        self.assertIsNone(score.cardinality)
        self.assertEqual(result.retained_classes, ("Alone",))

    def test_cardinality_boundary_is_ten_callers_not_eleven(self):
        for count, expected in [(9, False), (10, True), (11, True)]:
            with self.subTest(count=count):
                callers = [f"C{i}" for i in range(count)]
                edges = [row(caller, "run()", "Utility", "log()") for caller in callers]
                score = detect_omnipresent(callers + ["Utility"], edges).by_class()["Utility"]
                self.assertEqual(score.fanin, count)
                self.assertEqual(score.omnipresent, expected)
                self.assertAlmostEqual(score.max_dedication, 1 / count)

    def test_usage_threshold_is_inclusive_at_exact_point_eighty_five(self):
        callers = [f"C{i}" for i in range(10)]
        edges = [row(caller, "run()", "Utility", "common()") for caller in callers]
        edges += [row(caller, "run()", "Utility", "less_common()") for caller in callers[:5]]
        # mx=2.  Five callers receive 1/(10*2)+1/(5*2)=3/20,
        # so e=17/20=.85 exactly, while c=.90 exactly.
        score = detect_omnipresent(callers + ["Utility"], edges).by_class()["Utility"]
        self.assertTrue(score.omnipresent)
        self.assertTrue(score.usage_equality_passed)
        self.assertTrue(score.cardinality_passed)
        self.assertAlmostEqual(score.usage_equality, 0.85)

    def test_source_members_are_counted_but_target_members_are_sets(self):
        edges = [
            row("A", "first()", "B", "value:I"),
            row("A", "second()", "B", "value:I"),
            row("C", "run()", "B", "value:I"),
        ]
        result = detect_omnipresent(["A", "B", "C"], edges + [edges[0]] * 4)
        score = result.by_class()["B"]
        self.assertEqual(score.fanin, 2)
        self.assertEqual(score.referenced_members, 1)
        self.assertAlmostEqual(score.max_dedication, 1 / 3)
        self.assertEqual({p.source_class: p.dedication for p in result.dedications}, {"A": 1 / 3, "C": 1 / 3})
        self.assertEqual(result.stats.unique_member_edges, 3)
        self.assertEqual(result.stats.duplicate_member_edges, 4)

    def test_rare_setup_method_protects_a_popular_class(self):
        callers = [f"C{i}" for i in range(20)] + ["Startup"]
        edges = [row(caller, "run()", "Logger", "log()") for caller in callers]
        edges.append(row("Startup", "run()", "Logger", "init()"))
        score = detect_omnipresent(callers + ["Logger"], edges).by_class()["Logger"]
        self.assertEqual(score.fanin, 21)
        self.assertTrue(score.cardinality_passed)
        self.assertEqual(score.strongest_caller, "Startup")
        self.assertAlmostEqual(score.max_dedication, Fraction(1, 2) + Fraction(1, 42))
        self.assertFalse(score.omnipresent)
        self.assertEqual(score.reason, "usage_equality_below_threshold")

    def test_external_library_endpoints_do_not_enter_any_count(self):
        edges = [
            row("A", "run()", "Utility", "log()"),
            row("External", "run()", "Utility", "log()"),
            row("A", "run()", "java.lang.String", "length()"),
        ]
        result = detect_omnipresent(["A", "Utility"], edges)
        score = result.by_class()["Utility"]
        self.assertEqual(result.stats.excluded_external_edges, 2)
        self.assertEqual(result.stats.unique_member_edges, 1)
        self.assertEqual(score.max_dedication, 1.0)
        self.assertEqual(score.fanin, 1)

    def test_merged_inner_owners_keep_distinct_original_member_ids(self):
        edges = [
            {"source_class": "Outer", "source_member": "Outer$Inner#run()V",
             "target_class": "Utility", "target_member": "Utility#log()V"},
            {"source_class": "Outer", "source_member": "Outer$1#run()V",
             "target_class": "Utility", "target_member": "Utility#log()V"},
            row("Consumer", "run()", "Utility", "log()V"),
            {"source_class": "Outer", "source_member": "Outer$1#run()V",
             "target_class": "Outer", "target_member": "Outer#accept()V"},
        ]
        result = detect_omnipresent(["Outer", "Consumer", "Utility"], edges)
        score = result.by_class()["Utility"]
        self.assertEqual(result.stats.excluded_intraclass_edges, 1)
        self.assertEqual(score.fanin, 2)
        self.assertAlmostEqual(score.max_dedication, 1 / 3)

    def test_tuple_interface_and_unreferenced_members(self):
        owners = {"A#run()": "A", "B#used:I": "B", "B#unused:I": "B"}
        result = detect_omnipresent(["A", "B"], [("A#run()", "B#used:I")], member_owners=owners)
        score = result.by_class()["B"]
        self.assertEqual(score.referenced_members, 1)
        self.assertEqual(score.max_dedication, 1.0)

    def test_removal_is_simultaneous_without_iterative_recalculation(self):
        callers = [f"C{i}" for i in range(9)]
        edges = [row(caller, "run()", target, "use()") for caller in callers for target in ("U", "V")]
        edges += [row("U", "run()", "V", "use()"), row("V", "run()", "U", "use()")]
        result = detect_omnipresent(callers + ["U", "V"], edges)
        self.assertEqual(result.removed_classes, ("U", "V"))

    def test_serialization_is_deterministic_and_json_safe(self):
        callers = [f"C{i}" for i in range(12)]
        edges = [row(caller, "run()", "U", f"use{index % 3}()") for index, caller in enumerate(callers)]
        first = detect_omnipresent(callers + ["U"], edges)
        rng = random.Random(23)
        rng.shuffle(edges)
        second = detect_omnipresent(list(reversed(callers)) + ["U"], edges)
        self.assertEqual(first.to_dict(include_dedications=True), second.to_dict(include_dedications=True))
        json.dumps(first.to_dict(include_dedications=True), allow_nan=False)

    def test_optimized_result_matches_independent_exact_oracle(self):
        for seed in range(12):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                classes = [f"C{i}" for i in range(14)]
                edges = [
                    row(rng.choice(classes), f"m{rng.randrange(3)}()",
                        rng.choice(classes), f"m{rng.randrange(3)}()")
                    for _ in range(550)
                ]
                edges += edges[:15]
                edges += [row("third.party.Library", "run()", "C0", "m0()")]
                expected = exact_paper_oracle(classes, edges)
                result = detect_omnipresent(classes, edges).by_class()
                for cls, (fanin, mx, maximum, equality, cardinality, removed) in expected.items():
                    score = result[cls]
                    self.assertEqual(score.fanin, fanin)
                    self.assertEqual(score.referenced_members, mx)
                    self.assertEqual(score.omnipresent, removed)
                    if maximum is None:
                        self.assertIsNone(score.max_dedication)
                    else:
                        self.assertAlmostEqual(score.max_dedication, float(maximum), places=14)
                        self.assertAlmostEqual(score.usage_equality, float(equality), places=14)
                        self.assertAlmostEqual(score.cardinality, float(cardinality), places=14)

    def test_input_errors_do_not_silently_remove_evidence(self):
        with self.assertRaisesRegex(ValueError, "require a member_owners"):
            detect_omnipresent(["A", "B"], [("A#m", "B#m")])
        with self.assertRaisesRegex(ValueError, "owner missing"):
            detect_omnipresent(["A", "B"], [("A#m", "B#m")], member_owners={"A#m": "A"})
        with self.assertRaisesRegex(ValueError, "missing"):
            detect_omnipresent(["A", "B"], [{"source_class": "A"}])
        conflicting = [row("A", "run()", "U", "use()"), row("B", "run()", "U", "use()")]
        conflicting[1]["source_member"] = conflicting[0]["source_member"]
        with self.assertRaisesRegex(ValueError, "conflicting owners"):
            detect_omnipresent(["A", "B", "U"], conflicting)
        for invalid in (-0.1, 1.1, float("nan"), float("inf")):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                detect_omnipresent([], [], usage_threshold=invalid)

    def test_zero_and_one_thresholds_keep_empty_evidence_safe(self):
        edges = [row("A", "run()", "B", "use()")]
        low = detect_omnipresent(["A", "B", "Isolated"], edges, usage_threshold=0, cardinality_threshold=0)
        self.assertEqual(low.removed_classes, ("B",))
        high = detect_omnipresent(["A", "B"], edges, usage_threshold=1, cardinality_threshold=1)
        self.assertEqual(high.removed_classes, ())


if __name__ == "__main__":
    unittest.main()
