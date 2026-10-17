"""Execute one frozen A1/A2/A3/A4 experiment per pinned Guava release."""
from __future__ import annotations

from dataclasses import asdict
from datetime import date
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import sys
import time

from .extraction import extract_release
from .graph import Graph, read_csv, read_graph, sha256, write_csv, write_json
from .omnipresent import detect_omnipresent
from .mojofm import compare_mojofm
from .toolchain import ROOT, build_java, java_env, java_path


def manifest() -> dict:
    result = json.loads((ROOT / "config/versions.json").read_text())
    if result["repository"] != "google/guava":
        raise ValueError("This study must use the user-selected google/guava repository")
    versions = result["versions"]
    if len(versions) != 30 or len({v["version"] for v in versions}) != 30:
        raise ValueError("Expected exactly 30 unique selected releases")
    if len({tuple(v["version"].split(".")[:2]) for v in versions}) != 30:
        raise ValueError("Revised study requires 30 distinct major/minor families")
    if result.get("selection_method") != "major_anchors_calendar_greedy_v3":
        raise ValueError("Expected the frozen major-anchor and calendar-spacing selection rule")
    if {int(v["version"].split(".")[0]) for v in versions} != set(range(10, 34)):
        raise ValueError("The selected history must cover every major release from 10 through 33")
    days = [date.fromisoformat(v["release_date"][:10]).toordinal() for v in versions]
    if any(later - earlier < 60 for earlier, later in zip(days, days[1:])):
        raise ValueError("Selected releases must be ordered at least 60 UTC calendar days apart")
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


def _run_kmeans(graph: Graph, universe: list[str], n_full: int, config: dict, calibration: dict):
    from .clustering import choose_k, cluster_kmeans
    k = choose_k(n_full, len(graph.nodes), pilot_n=calibration["pilot_n"], pilot_k=calibration["pilot_k"])
    return cluster_kmeans(graph.nodes, graph.edges, universe, k,
                          random_state=config["kmeans"]["random_state"], n_init=config["kmeans"]["n_init"])


def pilot(graph_root: Path = ROOT / "data/graphs", output_root: Path = ROOT / "results/pilot", *, java: str | None = None) -> dict:
    from .metrics import evaluate_partition
    from .clustering import cluster_kmeans
    from .k_selection import select_elbow
    source, config = manifest(), settings()
    row = source["versions"][len(source["versions"]) // 2]
    graph = read_graph(graph_root / row["version"])
    universe = json.loads((graph_root / "feature_universe.json").read_text())
    output_root.mkdir(parents=True, exist_ok=True)
    trials, acdc_assignments = [], {}
    for maximum in config["pilot"]["acdc_max_subgraph_sizes"]:
        assignment, metadata = _run_acdc(graph, output_root / f"acdc_l{maximum}", config, java, maximum)
        measurement = evaluate_partition(graph.nodes, graph.edges, assignment)
        save_partition(output_root / f"acdc_l{maximum}.csv", assignment)
        trials.append({"algorithm": "ACDC", "max_subgraph_size": maximum, "metrics": measurement, "run": metadata})
        acdc_assignments[maximum] = assignment
    candidates = sorted({min(k, len(graph.nodes)) for k in config["pilot"]["k_candidates"]})
    fits, curve = {}, []
    for k in candidates:
        assignment, metadata = cluster_kmeans(graph.nodes, graph.edges, universe, k,
                          random_state=config["kmeans"]["random_state"], n_init=config["kmeans"]["n_init"])
        fits[k] = (assignment, metadata)
        save_partition(output_root / "k_candidates" / f"k{k}.csv", assignment)
        write_json(output_root / "k_candidates" / f"k{k}_run.json", metadata)
        curve.append({"k": k, "inertia": metadata["inertia"], "actual_k": metadata["actual_k"],
                      "iterations": metadata["iterations"], "elapsed_seconds": metadata["elapsed_seconds"]})
        print(f"pilot inertia k={k}: {metadata['inertia']:.6f}", flush=True)
    elbow = select_elbow(curve, minimum_gap=config["pilot"]["minimum_elbow_gap"],
                         fallback_k=config["pilot"]["fallback_k_if_no_clear_elbow"])
    selected_k = elbow["selected_k"]
    calibration = {"schema_version": 2, "pilot_version": row["version"], "pilot_n": len(graph.nodes), "pilot_k": selected_k,
                   "target_mean_class_count": len(graph.nodes) / selected_k,
                   "rule": config["kmeans"]["k_rule"], "selection": elbow,
                   "config_sha256": sha256(ROOT / "config/analysis.json"),
                   "manifest_sha256": sha256(ROOT / "config/versions.json"),
                   "graph_sha256": sha256(graph_root / row["version"] / "dependencies.csv"),
                   "classes_sha256": sha256(graph_root / row["version"] / "classes.csv"),
                   "feature_universe_sha256": sha256(graph_root / "feature_universe.json"),
                   "quality_scores_used_for_selection": False}
    write_json(output_root / "k_calibration.json", calibration)
    curve_by_k = {item["k"]: item for item in elbow["curve"]}
    write_csv(output_root / "k_inertia_curve.csv", [{**item, **curve_by_k[item["k"]]} for item in curve])
    assignment, metadata = fits[selected_k]
    measurement = evaluate_partition(graph.nodes, graph.edges, assignment)
    save_partition(output_root / "kmeans.csv", assignment)
    trials.append({"algorithm": "kmeans", "metrics": measurement, "run": metadata})
    matched = None
    if config["pilot"].get("matched_acdc_k_diagnostic"):
        default_acdc = acdc_assignments[config["acdc"]["max_subgraph_size"]]
        matched_k = len(set(default_acdc.values()))
        matched_assignment, matched_metadata = fits.get(matched_k, (None, None))
        if matched_assignment is None:
            matched_assignment, matched_metadata = cluster_kmeans(graph.nodes, graph.edges, universe, matched_k,
                       random_state=config["kmeans"]["random_state"], n_init=config["kmeans"]["n_init"])
        save_partition(output_root / "kmeans_matched_acdc_k.csv", matched_assignment)
        matched = {"k": matched_k, "metrics": evaluate_partition(graph.nodes, graph.edges, matched_assignment),
                   "run": matched_metadata, "used_for_k_selection": False,
                   "purpose": "One-pilot granularity diagnostic; not an extra final architecture or selection criterion"}
    result = {"version": row["version"], "selection": "middle release by sample index, chosen before metrics",
              "trials": trials, "k_sweep": "one_pilot_only", "k_calibration": calibration,
              "matched_acdc_k_diagnostic": matched,
              "frozen_configuration_sha256": sha256(ROOT / "config/analysis.json"),
              "decision": "Retain instructor semantics and ACDC +so/-l20. Select one pilot elbow using inertia only; transfer its mean granularity by the frozen integer-ceiling rule to all releases. Report the matched-k diagnostic without optimizing MQ."}
    write_json(output_root / "pilot.json", result)
    print("pilot completed", row["version"], flush=True)
    return result


def analyse_all(graph_root: Path = ROOT / "data/graphs", output_root: Path = ROOT / "results", *, java: str | None = None) -> dict:
    from .metrics import evaluate_partition, write_metric_tables
    source, config = manifest(), settings()
    universe = json.loads((graph_root / "feature_universe.json").read_text())
    calibration_path = output_root / "pilot/k_calibration.json"
    calibration = json.loads(calibration_path.read_text())
    if calibration["config_sha256"] != sha256(ROOT / "config/analysis.json") or calibration["manifest_sha256"] != sha256(ROOT / "config/versions.json"):
        raise ValueError("Pilot calibration does not match the frozen configuration and sample; rerun the pilot")
    metric_rows, size_rows, common_rows, temporal_rows, runtime_rows = [], [], [], [], []
    comparison_rows = []
    previous = None
    for row in source["versions"]:
        version = row["version"]
        comparison_details = []
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
                          "annotation_classes": provenance["annotation_classes"],
                          "non_annotation_classes": len(graph.nodes) - provenance["annotation_classes"],
                          "annotation_isolates": provenance["annotation_isolated_classes"],
                          "annotation_target_edges": provenance["annotation_target_edges"],
                          "omnipresent_classes": len(noise.removed_classes), "retained_classes": len(filtered.nodes),
                          "retained_dependencies": len(filtered.edges),
                          "edge_retention_fraction": len(filtered.edges) / len(graph.edges) if graph.edges else 1.0})
        architectures = {}
        for condition, method, variant in [("A1", "ACDC", graph), ("A2", "ACDC", filtered), ("A3", "kmeans", graph), ("A4", "kmeans", filtered)]:
            started = time.perf_counter()
            if method == "ACDC":
                assignment, metadata = _run_acdc(variant, directory / f"{condition}_run", config, java)
            else:
                assignment, metadata = _run_kmeans(variant, universe, len(graph.nodes), config, calibration)
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
        def record_comparison(scope, source_label, reference_label, a, b, nodes, previous_version="", n_edges=None):
            projected_a, projected_b = {n: a[n] for n in nodes}, {n: b[n] for n in nodes}
            forward, reverse = compare_mojofm(projected_a, projected_b), compare_mojofm(projected_b, projected_a)
            comparison = {"version": version, "previous_version": previous_version, "scope": scope,
                          "source_condition": source_label, "reference_condition": reference_label,
                          "n_nodes": len(nodes), "n_edges": n_edges,
                          "source_clusters": forward["source_clusters"], "reference_clusters": forward["target_clusters"],
                          "mojo_distance": forward["distance"], "mojo_max_distance": forward["max_distance"], "mojofm": forward["score"],
                          "reverse_mojo_distance": reverse["distance"], "reverse_mojo_max_distance": reverse["max_distance"], "reverse_mojofm": reverse["score"],
                          "node_universe_sha256": hashlib.sha256(("\n".join(sorted(nodes)) + "\n").encode()).hexdigest(),
                          "interpretation": "directional partition agreement; reference is not validated ground truth"}
            comparison_rows.append(comparison)
            comparison_details.append({"comparison": comparison, "forward": forward, "reverse": reverse})
            return comparison
        for full, without in [("A1", "A2"), ("A3", "A4")]:
            projected = {n: architectures[full][n] for n in filtered.nodes}
            baseline = evaluate_partition(filtered.nodes, filtered.edges, projected)
            recovered = evaluate_partition(filtered.nodes, filtered.edges, architectures[without])
            write_json(directory / f"{full}_projected_to_retained_metrics.json", baseline)
            comparison = record_comparison("full_vs_filtered_retained", full, without, projected, architectures[without], filtered.nodes, n_edges=len(filtered.edges))
            common_rows.append({"version": version, "full_condition": full, "filtered_condition": without,
                                "common_classes": len(filtered.nodes), "common_edges": len(filtered.edges),
                                "projected_full_mq": baseline["mq"], "recovered_filtered_mq": recovered["mq"],
                                "mq_change_same_graph": recovered["mq"] - baseline["mq"] if baseline["mq"] is not None else None,
                                "mojofm_full_to_filtered": comparison["mojofm"], "mojofm_filtered_to_full": comparison["reverse_mojofm"],
                                "mojo_distance_full_to_filtered": comparison["mojo_distance"],
                                "mojo_distance_filtered_to_full": comparison["reverse_mojo_distance"]})
        record_comparison("algorithms_full", "A1", "A3", architectures["A1"], architectures["A3"], graph.nodes, n_edges=len(graph.edges))
        record_comparison("algorithms_retained", "A2", "A4", architectures["A2"], architectures["A4"], filtered.nodes, n_edges=len(filtered.edges))
        if previous:
            old_graph, old_architectures, old_version = previous
            common = tuple(sorted(set(old_graph.nodes) & set(graph.nodes)))
            common_set = set(common)
            old_edges = {e for e in old_graph.edges if set(e) <= common_set}
            new_edges = {e for e in graph.edges if set(e) <= common_set}
            union = old_edges | new_edges
            acdc_comparison = record_comparison("temporal_full_common", "A1", "A1", old_architectures["A1"], architectures["A1"], common, previous_version=old_version)
            kmeans_comparison = record_comparison("temporal_full_common", "A3", "A3", old_architectures["A3"], architectures["A3"], common, previous_version=old_version)
            temporal_rows.append({"previous_version": old_version, "version": version,
                                  "common_classes": len(common), "added_classes": len(set(graph.nodes) - set(old_graph.nodes)),
                                  "removed_classes": len(set(old_graph.nodes) - set(graph.nodes)),
                                  "common_node_edge_jaccard": len(old_edges & new_edges) / len(union) if union else 1.0,
                                  "acdc_mojofm_previous_to_current": acdc_comparison["mojofm"],
                                  "acdc_mojofm_current_to_previous": acdc_comparison["reverse_mojofm"],
                                  "kmeans_mojofm_previous_to_current": kmeans_comparison["mojofm"],
                                  "kmeans_mojofm_current_to_previous": kmeans_comparison["reverse_mojofm"]})
        write_json(directory / "partition_comparisons.json", {"version": version, "comparisons": comparison_details})
        previous = (graph, architectures, version)
        print(f"analyse {version}: {len(graph.nodes)} classes; UE removed {len(noise.removed_classes)}; A1-A4 complete", flush=True)
    for filename, rows in [("sizes.csv", size_rows), ("metrics.csv", metric_rows), ("same_graph_comparisons.csv", common_rows),
                           ("evolution.csv", temporal_rows), ("runtimes.csv", runtime_rows), ("partition_comparisons.csv", comparison_rows)]:
        write_csv(output_root / filename, rows)
    run = {"subject": "google/guava", "release_count": len(size_rows), "architecture_count": len(metric_rows),
           "study_revision": config["study_revision"], "comparison_count": len(comparison_rows),
           "k_calibration_sha256": sha256(calibration_path), "pilot_n": calibration["pilot_n"], "pilot_k": calibration["pilot_k"],
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
