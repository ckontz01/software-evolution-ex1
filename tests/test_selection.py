"""Calendar boundaries, major coverage, provenance and deterministic selection."""
from copy import deepcopy
from datetime import date, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("guava_release_selector", ROOT / "scripts/select_versions.py")
selector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(selector)
EXPECTED = (
    "10.0,11.0,12.0,13.0.1,14.0,15.0,16.0,17.0,18.0,19.0,20.0,21.0,22.0,23.0,"
    "24.0,25.0,26.0,27.0,27.1,28.0,28.2,29.0,30.0,31.0,31.1,32.0.0,33.0.0,"
    "33.4.0,33.5.0,33.7.2"
).split(",")


def dated(version, day):
    return {"version": version, "release_date": (date(2020, 1, 1) + timedelta(days=day)).isoformat()}


class CalendarSelectorTests(unittest.TestCase):
    def test_gap_boundary_is_inclusive_and_infeasible_gap_fails(self):
        left, middle, right = dated("10.0", 0), dated("11.0", 60), dated("12.0", 120)
        chosen, steps = selector.greedy_fill_gaps([right, middle, left], [left, right], 3, 60, 2)
        self.assertEqual([r["version"] for r in chosen], ["10.0", "11.0", "12.0"])
        self.assertEqual(steps[0]["squared_gap_reduction_days2"], 120**2 - 60**2 - 60**2)
        with self.assertRaises(ValueError):
            selector.greedy_fill_gaps([left, middle, right], [left, right], 3, 61, 2)

    def test_equal_gain_uses_earlier_calendar_date_then_numeric_version(self):
        left, right = dated("10.0", 0), dated("20.0", 180)
        early, late = dated("15.0", 60), dated("11.0", 120)
        _, steps = selector.greedy_fill_gaps([right, late, early, left], [left, right], 3, 60, 2)
        self.assertEqual(steps[0]["version"], "15.0")
        two, ten = dated("11.2", 90), dated("11.10", 90)
        for candidates in ([left, ten, two, right], [right, two, ten, left]):
            _, steps = selector.greedy_fill_gaps(candidates, [left, right], 3, 60, 2)
            self.assertEqual(steps[0]["version"], "11.2")

    def test_optional_cap_does_not_charge_the_mandatory_endpoint(self):
        left, right = dated("10.0", 0), dated("15.7", 360)
        a, b = dated("15.4", 120), dated("15.5", 240)
        candidates = [left, a, b, right]
        chosen, steps = selector.greedy_fill_gaps(candidates, [left, right], 4, 60, 2)
        self.assertEqual(len(chosen), 4)
        self.assertEqual([s["optional_count_for_major_after_selection"] for s in steps], [1, 2])
        with self.assertRaises(ValueError):
            selector.greedy_fill_gaps(candidates, [left, right], 4, 60, 1)

    def test_duplicate_family_cannot_be_used_to_reach_requested_count(self):
        left, right = dated("10.0", 0), dated("20.0", 360)
        with self.assertRaises(ValueError):
            selector.greedy_fill_gaps([left, dated("11.0", 120), dated("11.0.1", 240), right],
                                      [left, right], 4, 60, 2)

    def test_dates_are_whole_utc_calendar_days_and_naive_timestamps_fail(self):
        self.assertEqual(selector.release_day({"release_date": "2020-01-02T00:30:00+02:00"}),
                         date(2020, 1, 1))
        self.assertEqual(selector.release_day({"release_date": "2020-01-01T23:59:59Z"}),
                         selector.release_day({"release_date": "2020-01-01"}))
        with self.assertRaises(ValueError):
            selector.release_day({"release_date": "2020-01-01T12:00:00"})


class FrozenSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (ROOT / "data/provenance/tag_inventory.json").read_bytes()
        cls.catalog, cls.catalog_hash = json.loads(raw), hashlib.sha256(raw).hexdigest()
        cls.manifest, cls.evidence = selector.build_manifest({"versions": []}, cls.catalog, cls.catalog_hash)

    def test_approved_sample_covers_every_major_and_fixes_both_endpoints(self):
        rows = self.manifest["versions"]
        self.assertEqual([r["version"] for r in rows], EXPECTED)
        self.assertEqual(len({r["family"] for r in rows}), 30)
        self.assertEqual({int(r["version"].split(".")[0]) for r in rows}, set(range(10, 34)))
        self.assertTrue({f"{major}.0" for major in range(10, 34)} <= {r["family"] for r in rows})
        self.assertEqual(sum(r["selection_role"] == "major_anchor" for r in rows), 24)
        self.assertEqual(sum(r["selection_role"] == "latest_endpoint" for r in rows), 1)
        self.assertEqual(sum(r["selection_role"] == "gap_filling_minor" for r in rows), 5)
        self.assertEqual((self.manifest["schema_version"], self.manifest["study_revision"]), (4, 3))

    def test_actual_dates_give_the_declared_spacing_and_ninety_days_is_infeasible(self):
        dates = [date.fromisoformat(r["release_date"][:10]) for r in self.manifest["versions"]]
        gaps = [(b - a).days for a, b in zip(dates, dates[1:])]
        self.assertEqual((min(gaps), sorted(gaps)[14], max(gaps)), (74, 141, 471))
        self.assertTrue(all(g >= 60 for g in gaps))
        _, audit, _, _, mandatory = selector.selection_details(self.catalog)
        representatives = [{"version": r["representative"], "release_date": r["representative_calendar_date"]}
                           for r in audit]
        mandatory = [{"version": r["version"], "release_date": r["release_date"][:10]} for r in mandatory]
        with self.assertRaisesRegex(ValueError, "Mandatory anchors"):
            selector.greedy_fill_gaps(representatives, mandatory, 30, 90, 2)

    def test_catalog_order_and_outcome_fields_do_not_change_the_selection(self):
        changed = deepcopy(self.catalog)
        changed["stable_tags_in_date_order"].reverse()
        for i, row in enumerate(changed["stable_tags_in_date_order"]):
            row["quality_score"] = i * -1000
            row["classes"] = 0
        rows, _, _ = selector.selected_rows(changed)
        self.assertEqual([r["version"] for r in rows], EXPECTED)
        self.assertEqual(selector.selection_details(changed)[3], self.evidence["optional_selection_steps"])

    def test_corrupt_catalog_and_future_endpoint_are_rejected(self):
        duplicate = deepcopy(self.catalog)
        duplicate["stable_tags_in_date_order"].append(deepcopy(duplicate["stable_tags_in_date_order"][0]))
        with self.assertRaises(ValueError):
            selector.selected_rows(duplicate)
        future = deepcopy(self.catalog)
        next(r for r in future["stable_tags_in_date_order"] if r["version"] == "33.7.2")["release_date"] = "2026-10-18"
        with self.assertRaises(ValueError):
            selector.selected_rows(future)

    def test_manifest_rejects_changed_identity_dates_roles_and_gap_metadata(self):
        changes = [
            (0, "commit_sha", "0" * 40), (0, "release_date", "2011-09-29"),
            (1, "calendar_gap_days_since_previous", 82),
            (1, "skipped_stable_since_previous", ["33.7.2"]),
            (0, "selection_role", "gap_filling_minor"),
        ]
        for index, key, value in changes:
            with self.subTest(key=key):
                changed = deepcopy(self.manifest)
                changed["versions"][index][key] = value
                with self.assertRaises(ValueError):
                    selector.validate_manifest(changed, self.catalog)
        changed = deepcopy(self.manifest)
        changed["versions"][1] = deepcopy(changed["versions"][0])
        with self.assertRaises(ValueError):
            selector.validate_manifest(changed, self.catalog)

    def test_only_matching_artifact_urls_preserve_existing_checksum_pins(self):
        prior = deepcopy(self.manifest)
        for kind in ("jar", "sources", "pom"):
            prior["versions"][0][kind + "_sha256"] = "a" * 64
            prior["versions"][0][kind + "_maven_sha1"] = "b" * 40
        prior["versions"][0]["pom_url"] += ".wrong"
        rebuilt, _ = selector.build_manifest(prior, self.catalog, self.catalog_hash)
        row = rebuilt["versions"][0]
        self.assertEqual(row["jar_sha256"], "a" * 64)
        self.assertEqual(row["sources_maven_sha1"], "b" * 40)
        self.assertNotIn("pom_sha256", row)
        self.assertNotIn("pom_maven_sha1", row)


if __name__ == "__main__":
    unittest.main()
