# Commit 06 — ACDC adapter, k-means and pilot k selection

**Student B · 2026-10-20 · 5 complete files · 4 full code/configuration listings**

Source snapshot: `f32e6e831f976eed8bf01faa1d66dbdc34bc49c7`. Dates are planned work sessions; make the commit when you actually import and review this packet.

## What to understand

Build one incoming/outgoing feature row, explain fixed feature identity, the pilot elbow and the rule that produces k for each final release. Explain ACDC separately.

## Apply this packet

Set `HANDOFF_DIR` to your extracted student bundle and `TEACHER_REPO` to the teacher checkout. Pull the preceding commit first. Commands below use the `guava-study` layout explained in the main map.

```bash
git -C "$TEACHER_REPO" pull --ff-only origin guava-assignment
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/06-b-clustering" --target "$TEACHER_REPO" --subdir guava-study
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/06-b-clustering" --target "$TEACHER_REPO" --subdir guava-study --apply
cd "$TEACHER_REPO/guava-study"
```

For commit 01, create the shared branch as shown in the main map; its remote branch does not exist until the first push, so omit that first pull.

## Checks before the commit

Run these in the cumulative study directory after applying the packet. For packet 01, first create the Python environment and install the locked requirements as shown in the main map:

```bash
python scripts/run_checks.py
```

Stage and inspect only this packet, then use your own Git identity:

```bash
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/06-b-clustering" --target "$TEACHER_REPO" --subdir guava-study --apply --stage
git -C "$TEACHER_REPO" diff --cached --stat
git -C "$TEACHER_REPO" diff --cached
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/06-b-clustering" --target "$TEACHER_REPO" --subdir guava-study --check-staged
git -C "$TEACHER_REPO" commit -m 'import: add ACDC and k-means recovery with pilot k selection (AI-assisted preparation)'
git -C "$TEACHER_REPO" push -u origin guava-assignment
```

Add a commit-message paragraph describing the checks you actually performed and anything you found. The import message identifies the prepared source; it does not claim you originally wrote every line.

## Every file to push

All files below are present under this packet's `payload/` directory in the complete student download. Paths are relative to the study directory.

| File | Bytes | Content |
|---|---:|---|
| `docs/pilot_decision.md` | 5,050 | documentation or tool provenance |
| `src/evolution/clustering.py` | 13,138 | Full code below |
| `src/evolution/k_selection.py` | 2,520 | Full code below |
| `tests/test_clustering.py` | 7,081 | Full code below |
| `tests/test_k_selection.py` | 1,596 | Full code below |

The machine-readable `packet.json` pins every file's SHA-256 and Git blob. Binary JAR/PDF/ZIP files and large evidence files are supplied as their exact original bytes in the payload, rather than as text pasted into this guide.

## Whole code

The following are complete files, with no omitted functions. Use the payload for copying so file bytes, line endings and original licences stay intact.

### src/evolution/clustering.py

SHA-256: `e1718db8ae33c802b795c4f95538d23baba4b8da5fc23f1805ce80790d846da7` · 13,138 bytes

<!-- FULL_SOURCE src/evolution/clustering.py e1718db8ae33c802b795c4f95538d23baba4b8da5fc23f1805ce80790d846da7 -->
```python
"""Deterministic structural KMeans and an adapter to the original York ACDC.

KMeans uses fixed union-class coordinates, outgoing and incoming neighbours,
identity only in features, and row L2 normalization. The metric graph always
remains a directed, binary graph without self-loops or external nodes.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
import warnings

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from threadpoolctl import threadpool_limits

from .metrics import validate_graph, validate_partition
from .toolchain import ROOT, java_env, java_path


def choose_k(n_full: int, n_remaining: int | None = None, *, pilot_n: int, pilot_k: int) -> int:
    """Transfer one pilot's empirically selected granularity to every version.

    Exact integer ceil(n_full * pilot_k / pilot_n), reused for full/filtered
    conditions. This is an explicit extrapolation, not a per-version optimum.
    """
    if n_full < 0 or (n_remaining is not None and not 0 <= n_remaining <= n_full):
        raise ValueError("Invalid full/remaining node counts")
    if not isinstance(pilot_n, int) or not isinstance(pilot_k, int) or not 1 <= pilot_k <= pilot_n:
        raise ValueError("Pilot calibration must have 1 <= pilot_k <= pilot_n")
    remaining = n_full if n_remaining is None else n_remaining
    if remaining == 0:
        return 0
    return min(remaining, max(1, (n_full * pilot_k + pilot_n - 1) // pilot_n))


def build_features(nodes: Iterable[str], edges: Iterable[tuple[str, str]], universe: Iterable[str]) -> tuple[tuple[str, ...], csr_matrix]:
    """Sparse X=[A+I,(A+I).T], embedded into the supplied union coordinates.

    The row order is sorted class names. Column order is the exact supplied
    universe, outgoing first and incoming second. Absent/removed classes retain
    their coordinates but have zero columns; filtered graphs must pass only
    retained nodes and retained-endpoint edges. No package labels are features.
    """
    nodes, edges = validate_graph(nodes, edges)
    universe = tuple(universe)
    if any(not isinstance(node, str) or not node for node in universe) or len(set(universe)) != len(universe):
        raise ValueError("Feature universe must contain unique class identifiers")
    columns = {node: index for index, node in enumerate(universe)}
    if not set(nodes) <= columns.keys():
        raise ValueError("Feature universe omits current graph classes")
    rows = {node: index for index, node in enumerate(nodes)}
    width = len(universe)
    row_ids, column_ids = [], []
    for node in nodes:
        row_ids.extend((rows[node], rows[node]))
        column_ids.extend((columns[node], width + columns[node]))
    for source, target in edges:
        row_ids.extend((rows[source], rows[target]))
        column_ids.extend((columns[target], width + columns[source]))
    matrix = csr_matrix((np.ones(len(row_ids), dtype=np.float64), (row_ids, column_ids)), shape=(len(nodes), 2 * width))
    matrix.sort_indices()
    if nodes:
        matrix = normalize(matrix, norm="l2", axis=1, copy=False)
    return nodes, matrix


def _canonical_assignment(nodes: Iterable[str], labels: Iterable[object], prefix: str) -> dict[str, str]:
    groups: dict[object, list[str]] = defaultdict(list)
    for node, label in zip(nodes, labels, strict=True):
        groups[label].append(node)
    ordered = sorted(groups.values(), key=lambda members: min(members))
    return {node: f"{prefix}_{index:04d}" for index, members in enumerate(ordered) for node in sorted(members)}


def cluster_kmeans(nodes: Iterable[str], edges: Iterable[tuple[str, str]], universe: Iterable[str], k: int, random_state: int = 484, n_init: int = 10) -> tuple[dict[str, str], dict]:
    """Run the frozen KMeans configuration once and retain warnings/diagnostics."""
    started = time.perf_counter()
    universe = tuple(universe)
    ordered, matrix = build_features(nodes, edges, universe)
    if not isinstance(k, int) or k < 0 or (ordered and k < 1):
        raise ValueError("k must be positive for a nonempty graph")
    requested = k
    effective = min(k, len(ordered))
    if n_init < 1:
        raise ValueError("n_init must be positive")
    caught = []
    if ordered:
        model = KMeans(n_clusters=effective, init="k-means++", n_init=n_init, max_iter=300, tol=1e-4, random_state=random_state, algorithm="lloyd")
        with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=1):
            warnings.simplefilter("always")
            labels = model.fit_predict(matrix)
        assignment = _canonical_assignment(ordered, labels, "kmeans")
        inertia, iterations = float(model.inertia_), int(model.n_iter_)
    else:
        assignment, inertia, iterations = {}, 0.0, 0
    validate_partition(ordered, assignment)
    sizes = Counter(assignment.values())
    metadata = {
        "method": "KMeans",
        "requested_k": requested,
        "clamped_k": effective,
        "actual_k": len(sizes),
        "random_state": random_state,
        "n_init": n_init,
        "max_iter": 300,
        "tol": 1e-4,
        "algorithm": "lloyd",
        "features": "[A+I,(A+I).T] in fixed union coordinates; row L2 normalized",
        "feature_rows": matrix.shape[0],
        "feature_columns": matrix.shape[1],
        "feature_nonzeros": matrix.nnz,
        "feature_universe_sha256": hashlib.sha256(("\n".join(universe) + "\n").encode()).hexdigest(),
        "inertia": inertia,
        "iterations": iterations,
        "warnings": [str(item.message) for item in caught],
        "min_cluster_size": min(sizes.values(), default=0),
        "max_cluster_size": max(sizes.values(), default=0),
        "singleton_clusters": sum(size == 1 for size in sizes.values()),
        "elapsed_seconds": time.perf_counter() - started,
    }
    return dict(sorted(assignment.items())), metadata


def parse_acdc_rsf(text: str, nodes: Iterable[str]) -> dict[str, str]:
    """Flatten a valid containment forest to the immediate parent of each class.

    ACDC's default output is already fine-grained/flat. Accepting a hierarchy
    here is explicit: groups are direct sibling classes, not top-level groups.
    Missing classes are returned as missing; the caller distinguishes genuine
    isolates from a tool failure before filling any memberships.
    """
    expected = set(nodes)
    parents: dict[str, str] = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 3 or fields[0] != "contain":
            raise ValueError(f"Invalid ACDC containment at line {number}: {line!r}")
        _, parent, child = fields
        if child in parents:
            raise ValueError(f"Duplicate ACDC membership for {child}")
        if parent == child or parent in expected:
            raise ValueError(f"Invalid ACDC container at line {number}")
        parents[child] = parent
    containers = set(parents.values())
    unknown_leaves = set(parents) - containers - expected
    if unknown_leaves:
        raise ValueError(f"Unknown classes in ACDC output: {sorted(unknown_leaves)!r}")
    for start in parents:
        seen = set()
        current = start
        while current in parents:
            if current in seen:
                raise ValueError("Cyclic ACDC containment hierarchy")
            seen.add(current)
            current = parents[current]
    return {node: parents[node] for node in sorted(expected) if node in parents}


def run_acdc(nodes: Iterable[str], edges: Iterable[tuple[str, str]], directory: str | Path, java: str | None = None, max_size: int = 20, patterns: str = "so", timeout: float = 300) -> tuple[dict[str, str], dict]:
    """Execute original ACDC; preserve true dependency-free nodes as singletons.

    Input contains only real call edges. Isolates cannot appear in that format,
    so they are explicitly restored outside the unmodified algorithm. Every
    non-isolated class must appear in ACDC output or this function fails.
    max_size bounds SubGraph construction, not the later orphan container.

    Original ACDC assumes file names: Node.getBaseName removes the last dotted
    suffix to name a dominator cluster. Bare Java qualified names would therefore
    collapse different classes in one package to identical cluster names. Each
    class is reversibly encoded as CLASS.java only for the external tool; its
    output is decoded before evaluation. The original Java source is unchanged.
    """
    started = time.perf_counter()
    nodes, edges = validate_graph(nodes, edges)
    if not isinstance(max_size, int) or max_size < 1:
        raise ValueError("ACDC max_size must be a positive integer")
    if not patterns or any(letter not in "bso" for letter in patterns) or len(set(patterns)) != len(patterns):
        raise ValueError("ACDC patterns must be a nonrepeated lowercase subset of bso")
    if any(any(character.isspace() for character in node) for node in nodes):
        raise ValueError("RSF class identifiers cannot contain whitespace")
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    input_path = directory / "input.rsf"
    output_path = directory / "acdc_raw.rsf"
    encoded = {node: node + ".java" for node in nodes}
    decoded = {value: key for key, value in encoded.items()}
    with (directory / "node_id_map.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["class", "acdc_node"])
        writer.writeheader()
        writer.writerows({"class": node, "acdc_node": encoded[node]} for node in nodes)
    input_path.write_text("".join(f"call {encoded[source]} {encoded[target]}\n" for source, target in edges), encoding="utf-8")
    # Never accept an output left by a prior invocation after an exit(0) error.
    if output_path.exists():
        output_path.unlink()
    incident = {node for edge in edges for node in edge}
    isolates = sorted(set(nodes) - incident)
    command, stdout, stderr, returncode = [], "", "", 0
    raw = {}
    if edges:
        executable = java_path(java)
        classpath = ROOT / "build/acdc"
        if not (classpath / "acdc/ACDC.class").exists():
            raise RuntimeError("ACDC is not compiled; run the Java build step")
        command = [executable, "-Djava.awt.headless=true", "-cp", str(classpath), "acdc.ACDC", str(input_path), str(output_path), "+" + patterns, f"-l{max_size}", "-d1"]
        completed = subprocess.run(command, capture_output=True, text=True, env=java_env(executable), timeout=timeout)
        stdout, stderr, returncode = completed.stdout, completed.stderr, completed.returncode
        (directory / "acdc_stdout.log").write_text(stdout, encoding="utf-8")
        (directory / "acdc_stderr.log").write_text(stderr, encoding="utf-8")
        if returncode or not output_path.exists():
            raise RuntimeError(f"ACDC failed (exit {returncode}); inspect logs in {directory}")
        tool_assignment = parse_acdc_rsf(output_path.read_text(encoding="utf-8"), encoded.values())
        raw = {decoded[node]: container for node, container in tool_assignment.items()}
        if set(raw) != incident:
            raise ValueError(f"ACDC coverage mismatch: missing incident nodes {sorted(incident - raw.keys())!r}; unexpected {sorted(raw.keys() - incident)!r}")
    else:
        output_path.write_text("", encoding="utf-8")
        (directory / "acdc_stdout.log").write_text("No dependency edges; all manifest nodes preserved as singleton clusters.\n", encoding="utf-8")
        (directory / "acdc_stderr.log").write_text("", encoding="utf-8")
    # Tagged label tuples prevent a real container name colliding with an isolate.
    labels = [("acdc", raw[node]) if node in raw else ("isolate", node) for node in nodes]
    assignment = _canonical_assignment(nodes, labels, "acdc")
    validate_partition(nodes, assignment)
    sizes = Counter(assignment.values())
    metadata = {
        "method": "ACDC (original York implementation)",
        "patterns": patterns,
        "subgraph_max_size": max_size,
        "output_mode": "flat fine-grained (default DownInducer)",
        "node_id_encoding": "append_.java_suffix_to_preserve_unique_ACDC_file_basenames",
        "command": command,
        "returncode": returncode,
        "isolates_restored_as_singletons": isolates,
        "original_containers": raw,
        "actual_k": len(sizes),
        "min_cluster_size": min(sizes.values(), default=0),
        "max_cluster_size": max(sizes.values(), default=0),
        "singleton_clusters": sum(size == 1 for size in sizes.values()),
        "elapsed_seconds": time.perf_counter() - started,
    }
    (directory / "acdc_execution.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return dict(sorted(assignment.items())), metadata
```
<!-- END_FULL_SOURCE src/evolution/clustering.py -->

### src/evolution/k_selection.py

SHA-256: `1b1efe5e6e38d3825de284a4412935f3babc0b1f41979e16c599d83f84bcd9f9` · 2,520 bytes

<!-- FULL_SOURCE src/evolution/k_selection.py 1b1efe5e6e38d3825de284a4412935f3babc0b1f41979e16c599d83f84bcd9f9 -->
```python
"""One-pilot inertia elbow; no final-MQ information enters the selection."""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping


def select_elbow(points: Iterable[Mapping], *, minimum_gap: float = 0.02,
                 fallback_k: int = 30) -> dict:
    """Find the largest positive gap below the normalized endpoint chord.

    With x=(k-k_min)/(k_max-k_min) and y=(I-I_last)/(I_first-I_last),
    gap=1-x-y. Smaller k wins exact ties. A predeclared nearest-candidate
    fallback handles flat/nondecreasing/no-clear-elbow curves. The full raw
    curve and any nonmonotonicity are retained; no smoothing changes evidence.
    """
    curve = sorted([{"k": int(p["k"]), "inertia": float(p["inertia"])} for p in points], key=lambda p: p["k"])
    if not curve or len({p["k"] for p in curve}) != len(curve):
        raise ValueError("Need a nonempty curve with unique candidate k values")
    if any(p["k"] < 1 or not math.isfinite(p["inertia"]) or p["inertia"] < 0 for p in curve):
        raise ValueError("Candidate k/inertia is invalid")
    if not math.isfinite(minimum_gap) or minimum_gap < 0 or fallback_k < 1:
        raise ValueError("Invalid elbow policy")
    k_span = curve[-1]["k"] - curve[0]["k"]
    i_span = curve[0]["inertia"] - curve[-1]["inertia"]
    for point in curve:
        point["normalized_k"] = (point["k"] - curve[0]["k"]) / k_span if k_span else 0.0
        point["normalized_inertia"] = (point["inertia"] - curve[-1]["inertia"]) / i_span if i_span > 0 else None
        point["chord_gap"] = (1.0 - point["normalized_k"] - point["normalized_inertia"]) if k_span and i_span > 0 else 0.0
    interior = curve[1:-1]
    best = max(interior, key=lambda p: (p["chord_gap"], -p["k"])) if interior else None
    clear = bool(best and best["chord_gap"] >= minimum_gap and i_span > 0)
    selected = best if clear else min(curve, key=lambda p: (abs(p["k"] - fallback_k), p["k"]))
    return {
        "selected_k": selected["k"], "clear_elbow": clear,
        "reason": "maximum_normalized_chord_gap" if clear else "predeclared_fallback_no_clear_elbow",
        "maximum_interior_gap": best["chord_gap"] if best else 0.0,
        "minimum_gap": minimum_gap, "fallback_requested_k": fallback_k,
        "nonmonotone_steps": sum(b["inertia"] > a["inertia"] for a, b in zip(curve, curve[1:])),
        "curve": curve,
        "interpretation": "Pilot inertia geometry only; not an optimal or true architectural cluster count; no MQ used in selection",
    }
```
<!-- END_FULL_SOURCE src/evolution/k_selection.py -->

### tests/test_clustering.py

SHA-256: `0670ee5d04062fd5e42d7b3603afc1ba61beb55b0cc233d3f821fcbe23d3d555` · 7,081 bytes

<!-- FULL_SOURCE tests/test_clustering.py 0670ee5d04062fd5e42d7b3603afc1ba61beb55b0cc233d3f821fcbe23d3d555 -->
```python
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
        calibration = {"pilot_n": 400, "pilot_k": 30}
        self.assertEqual(choose_k(800, **calibration), 60)
        self.assertEqual(choose_k(800, 750, **calibration), 60)
        self.assertEqual(choose_k(801, **calibration), 61)
        self.assertEqual(choose_k(800, 5, **calibration), 5)
        self.assertEqual(choose_k(0, **calibration), 0)
        self.assertEqual(choose_k(1, **calibration), 1)
        with self.assertRaises(ValueError):
            choose_k(10, 11, **calibration)
        with self.assertRaises(ValueError):
            choose_k(10, pilot_n=0, pilot_k=1)

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
```
<!-- END_FULL_SOURCE tests/test_clustering.py -->

### tests/test_k_selection.py

SHA-256: `a76b784ec0d080d486fe7a6f9f4c1b2fb11c503a0d71665854e4fbd3b1708bd3` · 1,596 bytes

<!-- FULL_SOURCE tests/test_k_selection.py a76b784ec0d080d486fe7a6f9f4c1b2fb11c503a0d71665854e4fbd3b1708bd3 -->
```python
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
```
<!-- END_FULL_SOURCE tests/test_k_selection.py -->
