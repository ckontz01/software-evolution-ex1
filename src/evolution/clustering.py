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
