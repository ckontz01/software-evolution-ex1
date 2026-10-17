"""Execute one frozen A1/A2/A3/A4 experiment per pinned Guava release."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import sys
import time

from sklearn.metrics import adjusted_rand_score

from .extraction import extract_release
from .graph import Graph, read_csv, read_graph, sha256, write_csv, write_json
from .omnipresent import detect_omnipresent
from .toolchain import ROOT, build_java, java_env, java_path


def manifest() -> dict:
    result = json.loads((ROOT / "config/versions.json").read_text())
    if result["repository"] != "google/guava":
        raise ValueError("This study must use the user-selected google/guava repository")
    versions = result["versions"]
    if len(versions) != 30 or len({v["version"] for v in versions}) != 30:
        raise ValueError("Expected exactly 30 unique selected releases")
    for row in versions:
        if any(token in row["version"].lower() for token in ("alpha", "beta", "rc", "snapshot", "android")):
            raise ValueError(f"Excluded release variant: {row['version']}")
    return result


def settings() -> dict:
    return json.loads((ROOT / "config/analysis.json").read_text())


def save_partition(path: Path, assignments: dict[str, str]) -> None:
    write_csv(path, [{"class": node, "cluster": str(assignments[node])} for node in sorted(assignments)], ["class", "cluster"])
    path.with_suffix(".rsf").write_text("".join(f"contain {assignments[n]} {n}\n" for n in sorted(assignments)))


def load_partition(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    if len(rows) != len({r["class"] for r in rows}):
        raise ValueError(f"Duplicate assignments: {path}")
    return {row["class"]: row["cluster"] for row in rows}


def compare_partitions(a: dict, b: dict, nodes: tuple[str, ...]) -> float | None:
    if len(nodes) < 2:
        return None
    return float(adjusted_rand_score([a[n] for n in nodes], [b[n] for n in nodes]))


def extract_all(output_root: Path = ROOT / "data/graphs", *, java: str | None = None) -> list[dict]:
    source = manifest()
    build_java(java)
    summaries = []
    for row in source["versions"]:
        result = extract_release(row, output_root, java=java)
        summaries.append(result)
        print(f"extract {row['version']}: {result['classes']} classes, {result['dependencies']} edges, {result['extraction_seconds']:.2f}s", flush=True)
    universe = sorted({n for row in source["versions"] for n in read_graph(output_root / row["version"]).nodes})
    write_json(output_root / "feature_universe.json", universe)
    write_json(output_root / "extraction_summary.json", summaries)
    return summaries


def _run_acdc(graph: Graph, directory: Path, config: dict, java: str | None, maximum: int | None = None):
    from .clustering import run_acdc
    return run_acdc(graph.nodes, graph.edges, directory,
                    java=java_path(java), max_size=maximum or config["acdc"]["max_subgraph_size"],
                    patterns=config["acdc"]["patterns"].lstrip("+"))


def _run_kmeans(graph: Graph, universe: list[str], n_full: int, config: dict):
    from .clustering import cluster_kmeans
    k = min(len(graph.nodes), max(1, math.ceil(math.sqrt(n_full / 2)))) if graph.nodes else 0
    return cluster_kmeans(graph.nodes, graph.edges, universe, k,
                          random_state=config["kmeans"]["random_state"], n_init=config["kmeans"]["n_init"])


def pilot(graph_root: Path = ROOT / "data/graphs", output_root: Path = ROOT / "results/pilot", *, java: str | None = None) -> dict:
    from .metrics import evaluate_partition
    source, config = manifest(), settings()
    row = source["versions"][len(source["versions"]) // 2]
    graph = read_graph(graph_root / row["version"])
    universe = json.loads((graph_root / "feature_universe.json").read_text())
    output_root.mkdir(parents=True, exist_ok=True)
    trials = []
    for maximum in config["pilot"]["acdc_max_subgraph_sizes"]:
        assignment, metadata = _run_acdc(graph, output_root / f"acdc_l{maximum}", config, java, maximum)
        measurement = evaluate_partition(graph.nodes, graph.edges, assignment)
        save_partition(output_root / f"acdc_l{maximum}.csv", assignment)
        trials.append({"algorithm": "ACDC", "max_subgraph_size": maximum, "metrics": measurement, "run": metadata})
    assignment, metadata = _run_kmeans(graph, universe, len(graph.nodes), config)
    measurement = evaluate_partition(graph.nodes, graph.edges, assignment)
    save_partition(output_root / "kmeans.csv", assignment)
    trials.append({"algorithm": "kmeans", "metrics": measurement, "run": metadata})
    result = {"version": row["version"], "selection": "middle release by sample index, chosen before metrics",
              "trials": trials, "k_sweep": False, "frozen_configuration_sha256": sha256(ROOT / "config/analysis.json"),
              "decision": "Inspect size distribution and coverage. Retain the documented +so/-l20 default and predeclared k rule unless a concrete pilot failure requires one global revision; record any revision before the final study."}
    write_json(output_root / "pilot.json", result)
    print("pilot completed", row["version"], flush=True)
    return result


def analyse_all(graph_root: Path = ROOT / "data/graphs", output_root: Path = ROOT / "results", *, java: str | None = None) -> dict:
    from .metrics import evaluate_partition, write_metric_tables
    source, config = manifest(), settings()
    universe = json.loads((graph_root / "feature_universe.json").read_text())
    metric_rows, size_rows, common_rows, temporal_rows, runtime_rows = [], [], [], [], []
    previous = None
    for row in source["versions"]:
        version = row["version"]
        directory = output_root / "versions" / version
        directory.mkdir(parents=True, exist_ok=True)
        graph = read_graph(graph_root / version)
        provenance = json.loads((graph_root / version / "provenance.json").read_text())
        started = time.perf_counter()
        noise = detect_omnipresent(graph.nodes, read_csv(graph_root / version / "member_dependencies.csv"),
                                   usage_threshold=config["omnipresent"]["usage_threshold"],
                                   cardinality_threshold=config["omnipresent"]["cardinality_threshold"])
        ue_seconds = time.perf_counter() - started
        write_json(directory / "ue.json", noise.to_dict(include_dedications=True))
        write_csv(directory / "omnipresent.csv", [s.to_dict() for s in noise.scores])
        filtered = graph.without(noise.removed_classes)
        filtered.rsf(directory / "filtered.rsf")
        write_csv(directory / "retained_classes.csv", [{"class": n} for n in filtered.nodes], ["class"])
        size_rows.append({"index": row["index"], "version": version, "date": row["release_date"],
                          **{k: provenance[k] for k in ("classes", "dependencies", "raw_binary_classes", "merged_binary_classes", "excluded_binary_classes", "java_code_lines", "physical_java_lines", "unique_member_edges", "isolated_classes")},
                          "omnipresent_classes": len(noise.removed_classes), "retained_classes": len(filtered.nodes),
                          "retained_dependencies": len(filtered.edges),
                          "edge_retention_fraction": len(filtered.edges) / len(graph.edges) if graph.edges else 1.0})
        architectures = {}
        for condition, method, variant in [("A1", "ACDC", graph), ("A2", "ACDC", filtered), ("A3", "kmeans", graph), ("A4", "kmeans", filtered)]:
            started = time.perf_counter()
            if method == "ACDC":
                assignment, metadata = _run_acdc(variant, directory / f"{condition}_run", config, java)
            else:
                assignment, metadata = _run_kmeans(variant, universe, len(graph.nodes), config)
            elapsed = time.perf_counter() - started
            measurement = evaluate_partition(variant.nodes, variant.edges, assignment)
            save_partition(directory / f"{condition}.csv", assignment)
            write_json(directory / f"{condition}_metrics.json", measurement)
            write_metric_tables(measurement, directory / f"{condition}_quality")
            write_json(directory / f"{condition}_run.json", metadata)
            flat = {key: value for key, value in measurement.items() if value is None or isinstance(value, (int, float, str, bool))}
            metric_rows.append({"index": row["index"], "version": version, "date": row["release_date"], "condition": condition,
                                "algorithm": method, "filtered": condition in ("A2", "A4"), **flat})
            architectures[condition] = assignment
            runtime_rows.append({"version": version, "stage": condition, "seconds": elapsed})
        runtime_rows.extend([{"version": version, "stage": "extraction", "seconds": provenance["extraction_seconds"]},
                             {"version": version, "stage": "UE", "seconds": ue_seconds}])
        for full, without in [("A1", "A2"), ("A3", "A4")]:
            projected = {n: architectures[full][n] for n in filtered.nodes}
            baseline = evaluate_partition(filtered.nodes, filtered.edges, projected)
            recovered = evaluate_partition(filtered.nodes, filtered.edges, architectures[without])
            write_json(directory / f"{full}_projected_to_retained_metrics.json", baseline)
            common_rows.append({"version": version, "full_condition": full, "filtered_condition": without,
                                "common_classes": len(filtered.nodes), "common_edges": len(filtered.edges),
                                "projected_full_mq": baseline["mq"], "recovered_filtered_mq": recovered["mq"],
                                "mq_change_same_graph": recovered["mq"] - baseline["mq"] if baseline["mq"] is not None else None,
                                "adjusted_rand_agreement": compare_partitions(projected, architectures[without], filtered.nodes)})
        if previous:
            old_graph, old_architectures, old_version = previous
            common = tuple(sorted(set(old_graph.nodes) & set(graph.nodes)))
            common_set = set(common)
            old_edges = {e for e in old_graph.edges if set(e) <= common_set}
            new_edges = {e for e in graph.edges if set(e) <= common_set}
            union = old_edges | new_edges
            temporal_rows.append({"previous_version": old_version, "version": version,
                                  "common_classes": len(common), "added_classes": len(set(graph.nodes) - set(old_graph.nodes)),
                                  "removed_classes": len(set(old_graph.nodes) - set(graph.nodes)),
                                  "common_node_edge_jaccard": len(old_edges & new_edges) / len(union) if union else 1.0,
                                  "acdc_adjusted_rand": compare_partitions(old_architectures["A1"], architectures["A1"], common),
                                  "kmeans_adjusted_rand": compare_partitions(old_architectures["A3"], architectures["A3"], common)})
        previous = (graph, architectures, version)
        print(f"analyse {version}: {len(graph.nodes)} classes; UE removed {len(noise.removed_classes)}; A1-A4 complete", flush=True)
    for filename, rows in [("sizes.csv", size_rows), ("metrics.csv", metric_rows), ("same_graph_comparisons.csv", common_rows),
                           ("evolution.csv", temporal_rows), ("runtimes.csv", runtime_rows)]:
        write_csv(output_root / filename, rows)
    run = {"subject": "google/guava", "release_count": len(size_rows), "architecture_count": len(metric_rows),
           "manifest_sha256": sha256(ROOT / "config/versions.json"), "config_sha256": sha256(ROOT / "config/analysis.json"),
           "python": sys.version, "platform": platform.platform(),
           "packages": {n: importlib.metadata.version(n) for n in ("numpy", "scipy", "scikit-learn", "matplotlib", "reportlab")},
           "feature_universe_size": len(universe), "feature_dimensions": 2 * len(universe),
           "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in sorted((ROOT / "src/evolution").glob("*.py"))},
           "java_toolchain": json.loads((ROOT / "build/toolchain.json").read_text()),
           "time_measurement": "perf_counter wall seconds; extraction includes JVM startup and IO; UE excludes member-CSV parsing only when explicitly benchmarked separately"}
    if run["architecture_count"] != 120:
        raise ValueError("Incomplete 30 x 4 study")
    write_json(output_root / "run_manifest.json", run)
    return run
