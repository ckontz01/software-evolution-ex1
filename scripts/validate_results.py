#!/usr/bin/env python3
"""Independently audit the 30-release Guava study using only Python's stdlib.

No production extraction, detector, clustering or metric function is imported.
This is an artifact audit, not another architecture experiment. It recomputes
the lecture formulas and exact-rational UE decisions from stored graph evidence,
checks archive membership/provenance, and checks all 120 partition populations.
Run after scripts/run_study.py: python scripts/validate_results.py
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import re
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RELATIONS = {"EXTENDS", "IMPLEMENTS", "METHOD_CALL", "METHOD_PARAMETER",
             "FIELD_REFERENCE", "TYPE_USAGE", "EXCEPTION_THROWS"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def data(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def close(a, b) -> bool:
    if a is None or b is None:
        return a is b
    try:
        return math.isfinite(float(a)) and math.isfinite(float(b)) and math.isclose(
            float(a), float(b), rel_tol=1e-11, abs_tol=1e-12)
    except (TypeError, ValueError):
        return False


def independent_quality(nodes, edges, assignment) -> dict:
    """Lecture formula by edge contributions, independent of saved term tables."""
    sizes = Counter(assignment.values())
    k, n, m = len(sizes), len(nodes), len(edges)
    pair_count = k * (k - 1) // 2
    inner, incoming, outgoing, cross = Counter(), Counter(), Counter(), Counter()
    cohesion_terms, coupling_terms = [], []
    for a, b in edges:
        left, right = assignment[a], assignment[b]
        if left == right:
            inner[left] += 1
            cohesion_terms.append(1 / (k * sizes[left] * (sizes[left] - 1)))
        else:
            incoming[right] += 1
            outgoing[left] += 1
            cross[tuple(sorted((left, right)))] += 1
            coupling_terms.append(1 / (pair_count * 2 * sizes[left] * sizes[right]))
    cohesion, coupling = math.fsum(cohesion_terms), math.fsum(coupling_terms)
    internal = sum(inner.values())
    capacity = sum(s * (s - 1) for s in sizes.values())
    cluster_terms = [{
        "cluster": c, "n_classes": s, "internal_edges": inner[c],
        "possible_internal_edges": s * (s - 1),
        "cohesion": inner[c] / (s * (s - 1)) if s > 1 else 0.0,
        "incoming_inter_edges": incoming[c], "outgoing_inter_edges": outgoing[c],
    } for c, s in sorted(sizes.items())]
    pair_terms = [{
        "cluster_i": a, "cluster_j": b, "n_i": sizes[a], "n_j": sizes[b],
        "inter_edges_both_directions": cross[a, b],
        "possible_inter_edges": 2 * sizes[a] * sizes[b],
        "coupling": cross[a, b] / (2 * sizes[a] * sizes[b]),
    } for a, b in combinations(sorted(sizes), 2)]
    return {
        "n_nodes": n, "n_edges": m, "n_clusters": k,
        "cohesion": cohesion, "coupling": coupling, "mq": cohesion - coupling,
        "size_weighted_cohesion": math.fsum(
            inner[c] / (s - 1) for c, s in sizes.items() if s > 1) / n if n else 0.0,
        "pair_weighted_cohesion": internal / capacity if capacity else 0.0,
        "internal_edges": internal, "inter_edges": m - internal,
        "inter_edge_fraction": (m - internal) / m if m else 0.0,
        "graph_density": m / (n * (n - 1)) if n > 1 else 0.0,
        "isolates": len(set(nodes) - {x for edge in edges for x in edge}),
        "min_cluster_size": min(sizes.values(), default=0),
        "max_cluster_size": max(sizes.values(), default=0),
        "mean_cluster_size": n / k if k else 0.0,
        "singleton_clusters": sum(s == 1 for s in sizes.values()),
        "per_cluster": cluster_terms, "per_pair": pair_terms,
    }


def independent_ari(a, b, nodes) -> float | None:
    """Adjusted Rand index directly from the contingency-table definition."""
    if len(nodes) < 2:
        return None
    choose2 = lambda x: x * (x - 1) // 2
    cells = Counter((a[n], b[n]) for n in nodes)
    left = Counter(a[n] for n in nodes)
    right = Counter(b[n] for n in nodes)
    observed = sum(choose2(v) for v in cells.values())
    total_pairs = choose2(len(nodes))
    left_pairs = sum(choose2(v) for v in left.values())
    right_pairs = sum(choose2(v) for v in right.values())
    expected = Fraction(left_pairs * right_pairs, total_pairs)
    maximum = Fraction(left_pairs + right_pairs, 2)
    return float((observed - expected) / (maximum - expected)) if maximum != expected else 1.0


def independent_ue(nodes, member_rows, usage, cardinality) -> dict:
    """Re-evaluate paper decisions with exact fractions for every target class."""
    sources, callers, targets = defaultdict(set), defaultdict(set), defaultdict(set)
    for row in member_rows:
        sources[row["target_member"]].add(row["source_member"])
        callers[row["target_member"]].add(row["source_class"])
        targets[row["target_class"]].add(row["target_member"])
    answer = {}
    for node in nodes:
        member_set = targets[node]
        by_caller = defaultdict(Fraction)
        for target in member_set:
            contribution = Fraction(1, len(sources[target]) * len(member_set))
            for caller in callers[target]:
                by_caller[caller] += contribution
        if not by_caller:
            answer[node] = {"fanin": 0, "referenced_members": 0,
                            "max_dedication": None, "usage_equality": None,
                            "cardinality": None, "omnipresent": False}
            continue
        maximum = max(by_caller.values())
        ue = 1 - maximum
        c = 1 - Fraction(1, len(by_caller))
        answer[node] = {"fanin": len(by_caller), "referenced_members": len(member_set),
                        "max_dedication": float(maximum), "usage_equality": float(ue),
                        "cardinality": float(c),
                        "omnipresent": ue >= Fraction(str(usage)) and c >= Fraction(str(cardinality))}
    return answer


class Audit:
    def __init__(self):
        self.counts = Counter()
        self.failures = []
        self.warnings = []
        self.release_evidence = []

    def check(self, condition, name, context, actual=None, expected=None):
        self.counts[name] += 1
        if not condition:
            self.failures.append({"check": name, "context": context,
                                  "actual": actual, "expected": expected})

    def equal(self, actual, expected, name, context):
        self.check(actual == expected, name, context, actual, expected)

    def numeric(self, actual, expected, name, context):
        self.check(close(actual, expected), name, context, actual, expected)

    def flat_metrics(self, observed, expected, context):
        for key, value in expected.items():
            if key not in ("per_cluster", "per_pair"):
                self.numeric(observed.get(key), value, "independent_metric_recalculation", f"{context}/{key}")
        self.numeric(float(observed["cohesion"]) - float(observed["coupling"]), observed["mq"],
                     "mq_identity", context)
        for key in ("cohesion", "coupling", "graph_density", "inter_edge_fraction",
                    "size_weighted_cohesion", "pair_weighted_cohesion"):
            value = float(observed[key])
            self.check(0 <= value <= 1, "metric_bounds", f"{context}/{key}", value, "[0,1]")
        self.check(-1 <= float(observed["mq"]) <= 1, "metric_bounds", f"{context}/mq")

    def terms(self, observed, expected, context):
        self.equal(len(observed), len(expected), "term_table_row_counts", context)
        for index, (got, want) in enumerate(zip(observed, expected)):
            for key, value in want.items():
                name = f"{context}/{index}/{key}"
                if isinstance(value, str):
                    self.equal(got.get(key), value, "term_identity", name)
                else:
                    self.numeric(got.get(key), value, "term_value", name)


def read_edges(path: Path):
    return [(r["source"], r["target"]) for r in rows(path)]


def read_rsf(path: Path, relation: str):
    result = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        tokens = line.split()
        if len(tokens) != 3 or tokens[0] != relation:
            raise ValueError(f"Malformed {relation} RSF in {path}: {line}")
        result.append((tokens[1], tokens[2]))
    return result


def read_partition(path: Path, expected_nodes, audit: Audit):
    records = rows(path)
    assignment = {r["class"]: r["cluster"] for r in records}
    audit.equal(len(records), len(assignment), "unique_membership", str(path))
    audit.equal(set(assignment), set(expected_nodes), "complete_membership", str(path))
    audit.check(all(assignment.values()), "nonempty_cluster_labels", str(path))
    rsf = read_rsf(path.with_suffix(".rsf"), "contain")
    audit.equal(sorted(rsf), sorted((c, n) for n, c in assignment.items()), "partition_rsf_matches_csv", str(path))
    return assignment


def audit(root: Path, result_root: Path, graph_root: Path) -> Audit:
    report = Audit()
    # A hand-derived identity guards the independent audit's own arithmetic.
    example = independent_quality("abcd", [("a", "b"), ("b", "a"), ("c", "d"),
                                          ("d", "c"), ("b", "c")],
                                  {"a": "x", "b": "x", "c": "y", "d": "y"})
    report.numeric(example["mq"], 7 / 8, "independent_hand_example", "two complete directed pairs and one cross edge")
    manifest, config = data(root / "config/versions.json"), data(root / "config/analysis.json")
    versions = manifest["versions"]
    version_ids = [r["version"] for r in versions]
    report.equal(manifest["repository"], "google/guava", "subject", "manifest")
    report.equal(len(versions), 30, "release_count", "manifest")
    report.equal(len(set(version_ids)), 30, "unique_release_count", "manifest")
    stable = data(root / "data/provenance/tag_inventory.json")["stable_tags_in_date_order"]
    stable_ids = [r["version"] for r in stable]
    for i, row in enumerate(versions):
        version = row["version"]
        report.check(re.fullmatch(r"\d+\.\d+(?:\.\d+)?", version) is not None,
                     "stable_release_only", version)
        artifact = row["artifact_version"]
        report.check(artifact == version or artifact == version + "-jre", "one_jre_variant", version, artifact)
        if i:
            previous = versions[i - 1]
            report.check(previous["release_date"] < row["release_date"], "chronological_sampling", version)
            start, stop = stable_ids.index(previous["version"]), stable_ids.index(version)
            skipped = stable_ids[start + 1:stop]
            report.check(len(skipped) > 0, "sporadic_sampling", version, skipped)
            report.equal(row["skipped_stable_since_previous"], skipped, "skipped_release_provenance", version)
        else:
            report.equal(row["skipped_stable_since_previous"], [], "skipped_release_provenance", version)
    report.equal(set(config["relation_types"]), RELATIONS, "frozen_policy", "seven relations")
    for key, expected in {"subject": "google/guava", "relation_weight": 1,
                          "graph": "binary_directed_union_no_self_loops", "merge_inner_and_anonymous": True,
                          "multi_release_policy": "base_class_entries_only", "singleton_cohesion": 0,
                          "empty_partition_metrics": 0}.items():
        report.equal(config[key], expected, "frozen_policy", key)
    metric_rows = rows(result_root / "metrics.csv")
    size_rows = rows(result_root / "sizes.csv")
    common_rows = rows(result_root / "same_graph_comparisons.csv")
    temporal_rows = rows(result_root / "evolution.csv")
    runtime_rows = rows(result_root / "runtimes.csv")
    for filename, actual, expected in [("metrics.csv", metric_rows, 120), ("sizes.csv", size_rows, 30),
                                       ("same_graph_comparisons.csv", common_rows, 60),
                                       ("evolution.csv", temporal_rows, 29), ("runtimes.csv", runtime_rows, 180)]:
        report.equal(len(actual), expected, "aggregate_row_count", filename)
    metric_index = {(r["version"], r["condition"]): r for r in metric_rows}
    report.equal(len(metric_index), 120, "one_final_architecture_per_condition", "metrics.csv")
    report.equal(set(metric_index), {(v, c) for v in version_ids for c in ("A1", "A2", "A3", "A4")},
                 "exact_condition_inventory", "metrics.csv")
    size_index = {r["version"]: r for r in size_rows}
    common_index = {(r["version"], r["full_condition"]): r for r in common_rows}
    runtime_index = {(r["version"], r["stage"]): r for r in runtime_rows}
    report.equal(set(size_index), set(version_ids), "size_inventory", "sizes.csv")
    report.equal(set(common_index), {(v, c) for v in version_ids for c in ("A1", "A3")},
                 "same_graph_inventory", "same_graph_comparisons.csv")
    report.equal(len(list((result_root / "versions").glob("*/A[1-4].csv"))), 120,
                 "final_partition_file_inventory", "results/versions")
    report.equal(len(runtime_index), 180, "runtime_inventory", "runtimes.csv")
    report.equal(set(runtime_index), {(v, c) for v in version_ids for c in ("A1", "A2", "A3", "A4", "extraction", "UE")},
                 "runtime_inventory", "runtimes.csv keys")
    for row in runtime_rows:
        report.check(math.isfinite(float(row["seconds"])) and float(row["seconds"]) >= 0,
                     "finite_nonnegative_runtime", f"{row['version']}/{row['stage']}")
    universe = data(graph_root / "feature_universe.json")
    universe_hash = hashlib.sha256(("\n".join(universe) + "\n").encode()).hexdigest()
    report.equal(universe, sorted(set(universe)), "fixed_feature_schema", "unique sorted universe")
    observed_universe = set()
    previous = None
    for row in versions:
        version = row["version"]
        directory, output = graph_root / version, result_root / "versions" / version
        class_rows = rows(directory / "classes.csv")
        nodes = [r["class"] for r in class_rows]
        node_set = set(nodes)
        edges = read_edges(directory / "dependencies.csv")
        edge_set = set(edges)
        observed_universe.update(nodes)
        report.equal(len(nodes), len(node_set), "unique_graph_nodes", version)
        report.equal(len(edges), len(edge_set), "binary_edges", version)
        report.check(all(a in node_set and b in node_set and a != b for a, b in edges),
                     "internal_only_loop_free_edges", version)
        report.check(all(n.startswith("com.google.common.") and "$" not in n for n in nodes),
                     "owned_outermost_class_scope", version)
        report.equal(read_rsf(directory / "full.rsf", "call"), edges, "graph_rsf_matches_csv", version)
        typed = rows(directory / "dependencies_typed.csv")
        report.equal({(r["source"], r["target"]) for r in typed}, edge_set, "relation_union_equals_graph", version)
        report.check({r["relation"] for r in typed} <= RELATIONS, "only_seven_allowed_relations", version)
        report.equal(len(typed), len({tuple(r.values()) for r in typed}), "unique_typed_edges", version)
        provenance = data(directory / "provenance.json")
        report.equal(provenance["classes_sha256"], digest(directory / "classes.csv"), "graph_checksum", version + "/classes")
        report.equal(provenance["graph_sha256"], digest(directory / "dependencies.csv"), "graph_checksum", version + "/dependencies")
        report.equal(provenance["extractor_sha256"], digest(root / "java/DependencyExtractor.java"), "single_extractor_policy", version)
        for key, value in (("version", version), ("tag", row["tag"]), ("commit_sha", row["commit_sha"]),
                           ("date", row["release_date"]), ("binary_sha256", row["jar_sha256"]),
                           ("sources_sha256", row["sources_sha256"])):
            report.equal(provenance[key], value, "extraction_provenance", version + "/" + key)
        for kind in ("jar", "sources", "pom"):
            report.equal(digest(root / row[f"{kind}_path"]), row[f"{kind}_sha256"], "artifact_sha256", f"{version}/{kind}")
        aliases = rows(directory / "class_aliases.csv")
        alias_map = {r["binary_class"]: r["class"] for r in aliases}
        report.equal(len(aliases), len(alias_map), "unique_binary_alias", version)
        report.equal(set(alias_map.values()), node_set, "every_binary_merged_to_owned_node", version)
        report.check(all(r["binary_class"].split("$")[0] == r["class"] for r in aliases), "guava_nested_alias_reconciliation", version)
        alias_counts = Counter(alias_map.values())
        for r in class_rows:
            report.equal(int(r["raw_binary_classes"]), alias_counts[r["class"]], "merged_class_member_counts", version + "/" + r["class"])
        with zipfile.ZipFile(root / row["sources_path"]) as source_archive:
            source_names = set(source_archive.namelist())
        report.check(all(r["source_file"] in source_names and r["source_file"].startswith("com/google/common/") for r in aliases),
                     "source_ownership_in_same_version", version)
        excluded = rows(directory / "excluded_classes.csv")
        excluded_names = {r["binary_class"] for r in excluded}
        with zipfile.ZipFile(root / row["jar_path"]) as archive:
            base_classes = {n[:-6].replace("/", ".") for n in archive.namelist() if n.endswith(".class")
                            and not n.startswith("META-INF/versions/") and not n.endswith("package-info.class")
                            and not n.endswith("module-info.class")}
        report.equal(set(alias_map) | excluded_names, base_classes, "all_jar_classes_accounted_for", version)
        report.check(not set(alias_map) & excluded_names, "excluded_classes_never_analyzed", version)
        report.equal(len(aliases) - len(nodes), provenance["merged_binary_classes"], "merged_count_provenance", version)
        member_rows = rows(directory / "member_dependencies.csv")
        report.equal(len(member_rows), len({(r["source_member"], r["target_member"]) for r in member_rows}), "unique_member_references", version)
        report.check(all((r["source_class"], r["target_class"]) in edge_set for r in member_rows), "member_edges_within_class_graph", version)
        report.check(all(alias_map.get(r[side + "_member"].split("#")[0]) == r[side + "_class"]
                         for r in member_rows for side in ("source", "target")), "member_identity_survives_outer_merge", version)
        ue = data(output / "ue.json")
        report.numeric(ue["usage_threshold"], config["omnipresent"]["usage_threshold"], "frozen_ue_thresholds", version)
        report.numeric(ue["cardinality_threshold"], config["omnipresent"]["cardinality_threshold"], "frozen_ue_thresholds", version)
        expected_ue = independent_ue(nodes, member_rows, ue["usage_threshold"], ue["cardinality_threshold"])
        expected_removed = {n for n, score in expected_ue.items() if score["omnipresent"]}
        report.equal(set(ue["removed_classes"]), expected_removed, "exact_rational_ue_decisions", version)
        observed_scores = {r["class_name"]: r for r in ue["scores"]}
        report.equal(set(observed_scores), node_set, "complete_ue_score_population", version)
        for node, expected_score in expected_ue.items():
            for key, value in expected_score.items():
                report.numeric(observed_scores[node][key], value, "independent_ue_score", f"{version}/{node}/{key}")
        retained = node_set - expected_removed
        filtered_edges = [(a, b) for a, b in edges if a in retained and b in retained]
        report.equal({r["class"] for r in rows(output / "retained_classes.csv")}, retained, "retained_class_population", version)
        report.equal(read_rsf(output / "filtered.rsf", "call"), filtered_edges, "filtered_graph_is_induced", version)
        expected_sizes = {"classes": len(nodes), "dependencies": len(edges), "raw_binary_classes": len(aliases),
                          "merged_binary_classes": len(aliases) - len(nodes), "excluded_binary_classes": len(excluded),
                          "unique_member_edges": len(member_rows), "omnipresent_classes": len(expected_removed),
                          "retained_classes": len(retained), "retained_dependencies": len(filtered_edges),
                          "isolated_classes": len(node_set - {n for e in edges for n in e}),
                          "edge_retention_fraction": len(filtered_edges) / len(edges) if edges else 1.0}
        for key, value in expected_sizes.items():
            report.numeric(size_index[version][key], value, "size_aggregate_matches_evidence", version + "/" + key)
        report.equal(size_index[version]["date"], row["release_date"], "date_provenance", version)
        source_sizes = rows(directory / "source_sizes.csv")
        report.equal({r["source_file"] for r in source_sizes}, {r["source_file"] for r in class_rows},
                     "counted_source_population", version)
        for key in ("java_code_lines", "physical_java_lines"):
            expected = sum(int(r[key]) for r in source_sizes)
            report.numeric(provenance[key], expected, "source_size_reconciliation", version + "/" + key)
            report.numeric(size_index[version][key], expected, "source_size_reconciliation", version + "/" + key)
        if version == version_ids[-1]:
            report.check(int(size_index[version]["java_code_lines"]) >= 10000, "latest_code_size_eligibility", version)
        partitions = {}
        condition_evidence = {}
        for condition in ("A1", "A2", "A3", "A4"):
            filtered = condition in ("A2", "A4")
            current_nodes, current_edges = (retained, filtered_edges) if filtered else (node_set, edges)
            context = f"{version}/{condition}"
            assignment = read_partition(output / f"{condition}.csv", current_nodes, report)
            partitions[condition] = assignment
            quality = independent_quality(current_nodes, current_edges, assignment)
            recorded = data(output / f"{condition}_metrics.json")
            report.flat_metrics(recorded, quality, context + "/JSON")
            report.flat_metrics(metric_index[version, condition], quality, context + "/aggregate")
            report.equal(metric_index[version, condition]["algorithm"], "ACDC" if condition in ("A1", "A2") else "kmeans",
                         "condition_algorithm_identity", context)
            report.equal(metric_index[version, condition]["filtered"], str(filtered), "condition_population_identity", context)
            summary_rows = rows(output / f"{condition}_quality/metrics_summary.csv")
            report.equal(len(summary_rows), 1, "quality_summary_row_count", context)
            report.flat_metrics(summary_rows[0], quality, context + "/summary")
            for table in ("per_cluster", "per_pair"):
                report.terms(recorded[table], quality[table], context + "/JSON/" + table)
                report.terms(rows(output / f"{condition}_quality/{table}.csv"), quality[table], context + "/CSV/" + table)
            metadata = data(output / f"{condition}_run.json")
            report.equal(metadata["actual_k"], quality["n_clusters"], "reported_actual_k", context)
            if condition in ("A1", "A2"):
                report.equal(metadata["patterns"].lstrip("+"), config["acdc"]["patterns"].lstrip("+"), "frozen_acdc_policy", context)
                report.equal(metadata["subgraph_max_size"], config["acdc"]["max_subgraph_size"], "frozen_acdc_policy", context)
                report.equal(config["acdc"]["node_ids"], "class_plus_java_suffix", "frozen_acdc_policy", context)
                report.equal(metadata["node_id_encoding"], "append_.java_suffix_to_preserve_unique_ACDC_file_basenames",
                             "acdc_unique_filename_basenames", context)
                identity_map = rows(output / f"{condition}_run/node_id_map.csv")
                report.equal({r["class"]: r["acdc_node"] for r in identity_map},
                             {n: n + ".java" for n in current_nodes}, "acdc_reversible_id_map", context)
                report.equal(read_rsf(output / f"{condition}_run/input.rsf", "call"),
                             [(a + ".java", b + ".java") for a, b in current_edges],
                             "acdc_input_preserves_exact_graph", context)
                isolates = set(current_nodes) - {n for e in current_edges for n in e}
                report.equal(set(metadata["isolates_restored_as_singletons"]), isolates, "acdc_isolates_preserved", context)
                sizes = Counter(assignment.values())
                report.check(all(sizes[assignment[n]] == 1 for n in isolates), "acdc_isolate_singletons", context)
            else:
                requested = min(len(current_nodes), math.ceil(math.sqrt(len(nodes) / 2))) if current_nodes else 0
                report.equal(metadata["requested_k"], requested, "predeclared_k_from_full_n", context)
                report.equal(metadata["feature_rows"], len(current_nodes), "fixed_feature_schema", context + "/rows")
                report.equal(metadata["feature_columns"], 2 * len(universe), "fixed_feature_schema", context + "/columns")
                report.equal(metadata["feature_universe_sha256"], universe_hash, "fixed_feature_schema", context + "/coordinate identities")
                report.equal(metadata["feature_nonzeros"], 2 * (len(current_nodes) + len(current_edges)), "feature_identity_plus_edges_only", context)
                for key in ("random_state", "n_init", "max_iter", "algorithm"):
                    report.equal(metadata[key], config["kmeans"][key], "frozen_kmeans_parameters", context + "/" + key)
                if metadata["actual_k"] != requested:
                    report.warnings.append({"context": context, "message": "Actual KMeans clusters differ from requested k", "metadata": metadata})
            condition_evidence[condition] = {key: quality[key] for key in ("n_nodes", "n_edges", "n_clusters", "mq", "max_cluster_size", "singleton_clusters")}
        for full, filtered in (("A1", "A2"), ("A3", "A4")):
            baseline = independent_quality(retained, filtered_edges, {n: partitions[full][n] for n in retained})
            recovered = independent_quality(retained, filtered_edges, partitions[filtered])
            observed = common_index[version, full]
            report.equal(observed["filtered_condition"], filtered, "same_graph_condition_pair", version)
            expected = {"common_classes": len(retained), "common_edges": len(filtered_edges),
                        "projected_full_mq": baseline["mq"], "recovered_filtered_mq": recovered["mq"],
                        "mq_change_same_graph": recovered["mq"] - baseline["mq"],
                        "adjusted_rand_agreement": independent_ari(partitions[full], partitions[filtered], retained)}
            for key, value in expected.items():
                report.numeric(observed[key], value, "same_graph_recalculation", f"{version}/{full}/{key}")
            report.flat_metrics(data(output / f"{full}_projected_to_retained_metrics.json"), baseline, f"{version}/{full}/projected")
        if previous is not None:
            old_nodes, old_edges, old_partitions, old_version = previous
            common = node_set & old_nodes
            left = {e for e in old_edges if e[0] in common and e[1] in common}
            right = {e for e in edges if e[0] in common and e[1] in common}
            observed = temporal_rows[row["index"] - 2]
            report.equal((observed["previous_version"], observed["version"]), (old_version, version), "temporal_pair_identity", version)
            expected = {"common_classes": len(common), "added_classes": len(node_set - old_nodes),
                        "removed_classes": len(old_nodes - node_set),
                        "common_node_edge_jaccard": len(left & right) / len(left | right) if left | right else 1.0,
                        "acdc_adjusted_rand": independent_ari(old_partitions["A1"], partitions["A1"], common),
                        "kmeans_adjusted_rand": independent_ari(old_partitions["A3"], partitions["A3"], common)}
            for key, value in expected.items():
                report.numeric(observed[key], value, "temporal_recalculation", version + "/" + key)
        previous = (node_set, edges, partitions, version)
        report.release_evidence.append({"version": version, **expected_sizes, "conditions": condition_evidence})
    report.equal(set(universe), observed_universe, "fixed_feature_schema", "union across all30 releases")
    run = data(result_root / "run_manifest.json")
    report.equal(run["release_count"], 30, "run_manifest_totals", "releases")
    report.equal(run["architecture_count"], 120, "run_manifest_totals", "architectures")
    report.equal(run["manifest_sha256"], digest(root / "config/versions.json"), "frozen_manifest_checksum", "run")
    report.equal(run["config_sha256"], digest(root / "config/analysis.json"), "frozen_config_checksum", "run")
    for path, expected in run["source_sha256"].items():
        report.equal(digest(root / path), expected, "frozen_implementation_checksum", path)
    pilot = data(result_root / "pilot/pilot.json")
    report.equal(pilot["version"], versions[len(versions) // 2]["version"], "pilot_preselected_middle_release", "pilot")
    report.equal(pilot["k_sweep"], False, "no_k_sweep", "pilot")
    report.equal(pilot["frozen_configuration_sha256"], run["config_sha256"], "pilot_and_final_same_policy", "pilot")
    report.equal([r["max_subgraph_size"] for r in pilot["trials"] if r["algorithm"] == "ACDC"],
                 config["pilot"]["acdc_max_subgraph_sizes"], "pilot_acdc_inventory", "pilot")
    return report


def json_safe(value):
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(type(value).__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--results", type=Path)
    parser.add_argument("--graphs", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result_root = args.results or args.root / "results"
    output = args.output or result_root / "validation.json"
    try:
        report = audit(args.root, result_root, args.graphs or args.root / "data/graphs")
    except Exception as error:
        result = {"status": "incomplete", "error_type": type(error).__name__, "error": str(error)}
    else:
        result = {"status": "passed" if not report.failures else "failed",
                  "checks_performed": sum(report.counts.values()), "check_categories": dict(sorted(report.counts.items())),
                  "failure_count": len(report.failures), "failures": report.failures,
                  "warnings": report.warnings, "releases": report.release_evidence}
    result.update({"validated_at_utc": datetime.now(timezone.utc).isoformat(),
                   "validator_sha256": digest(Path(__file__)),
                   "method": "stdlib-only independent artifact audit; edge-contribution lecture MQ; exact-rational UE; contingency-table ARI",
                   "scope": "30 source-owned Guava graphs,120 finalized A1-A4 partitions,60 retained-graph comparisons,29 temporal transitions; pilot inventory checked separately",
                   "limitations": ["Provenance/membership checks do not prove a static extractor sees runtime reflection or all dynamic dispatch.",
                                   "Passing structural checks does not prove the recovered clusters match intended architecture.",
                                   "No new architecture is created by this validation."]})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, default=json_safe, allow_nan=False) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "checks_performed", "failure_count", "error") if key in result}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
