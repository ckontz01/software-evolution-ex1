#!/usr/bin/env python3
"""Verify a pristine checkout of an exact published study commit, offline.

Example (clone separately, then run from that clone):
  EVOLUTION_JAVA=/path/to/java python scripts/verify_clean_checkout.py \
    --expected-commit FULL_COMMIT_SHA --output /path/to/new/evidence

The output directory must be new or empty; keeping it outside the checkout is
recommended. This runner does not clone, fetch, change branches, install Python
packages, or select parameters. It restores the committed archives and uses the
committed pilot calibration. Python requirements and Java 17+ must already be
available. The bundled tool JARs are checked before fetch_tools.py is invoked,
so that step cannot require a download in a valid checkout.

The final receipt distinguishes a repeat execution of the implementation from
the separate stdlib-only mathematical/artifact validator. The recorded AI
response is re-evaluated, not generated again. Timings and paths are preserved
as evidence, but explicitly excluded from deterministic byte comparisons.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time
import traceback
from zipfile import ZipFile
import zlib


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
VOLATILE_TRACKED_OUTPUTS = {
    "data/provenance/acquisition.json",
    "results/validation.json",
    "results/change_points.json",
    "results/performance/case_checks.json",
}
GRAPH_METADATA_EXCLUSIONS = {
    "instructor.log", "instructor_command.json", "supplemental.log",
    "supplemental_command.json", "provenance.json",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8", errors="strict")


def relative(path, base):
    try:
        return Path(path).resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(Path(path).resolve())


def committed_file_inventory():
    """Check file bytes against Git objects, rather than trusting status alone."""
    object_format = git("rev-parse", "--show-object-format").strip()
    require(object_format in ("sha1", "sha256"), "Unknown Git object format")
    inventory = []
    for entry in git("ls-tree", "-r", "-z", "--full-tree", "HEAD").split("\0"):
        if not entry:
            continue
        prefix, name = entry.split("\t", 1)
        mode, kind, expected = prefix.split()
        require(kind == "blob", f"Unsupported submodule in verification tree: {name}")
        path = ROOT / name
        content = os.fsencode(os.readlink(path)) if mode == "120000" else path.read_bytes()
        actual = hashlib.new(object_format, f"blob {len(content)}\0".encode() + content).hexdigest()
        require(actual == expected, f"Working bytes differ from committed Git blob: {name}")
        inventory.append({"path": name, "mode": mode, "bytes": len(content),
                          "git_blob": expected, "sha256": hashlib.sha256(content).hexdigest()})
    return inventory


def byte_comparison(expected, actual, output, *, description=None):
    expected, actual = Path(expected), Path(actual)
    return {"archived": relative(expected, ROOT), "reproduced": relative(actual, output),
            "archived_sha256": sha(expected), "reproduced_sha256": sha(actual),
            "archived_bytes": expected.stat().st_size, "reproduced_bytes": actual.stat().st_size,
            "byte_identical": expected.read_bytes() == actual.read_bytes(),
            **({"description": description} if description else {})}


def reproduce_latest(output, expected_commit):
    """Execute the latest pipeline afresh; archived earlier data are references."""
    require(git("rev-parse", "HEAD").strip() == expected_commit, "Commit changed before latest reproduction")
    sys.path.insert(0, str(ROOT / "src"))
    from evolution.extraction import extract_release
    from evolution.graph import read_csv, read_graph, write_csv, write_json
    from evolution.metrics import evaluate_partition, write_metric_tables
    from evolution.mojofm import compare_mojofm
    from evolution.omnipresent import detect_omnipresent
    from evolution.study import _run_acdc, _run_kmeans, load_partition, save_partition
    from evolution.toolchain import java_path

    manifest = read_json(ROOT / "config/versions.json")
    config = read_json(ROOT / "config/analysis.json")
    calibration_path = ROOT / "results/pilot/k_calibration.json"
    calibration = read_json(calibration_path)
    require(calibration["config_sha256"] == sha(ROOT / "config/analysis.json"), "Stale pilot configuration")
    require(calibration["manifest_sha256"] == sha(ROOT / "config/versions.json"), "Stale pilot sample")
    require(calibration["feature_universe_sha256"] == sha(ROOT / "data/graphs/feature_universe.json"), "Stale feature universe")
    row = manifest["versions"][-1]
    version = row["version"]
    work = output / "work"
    require(not work.exists(), "Latest reproduction work directory already exists")
    graph_root = work / "graphs"
    directory = work / "results" / version
    directory.mkdir(parents=True)
    executable = java_path()
    extraction = extract_release(row, graph_root, java=executable)
    graph_dir = graph_root / version
    graph = read_graph(graph_dir)
    noise = detect_omnipresent(graph.nodes, read_csv(graph_dir / "member_dependencies.csv"),
                              usage_threshold=config["omnipresent"]["usage_threshold"],
                              cardinality_threshold=config["omnipresent"]["cardinality_threshold"])
    write_json(directory / "ue.json", noise.to_dict(include_dedications=True))
    write_csv(directory / "omnipresent.csv", [score.to_dict() for score in noise.scores])
    filtered = graph.without(noise.removed_classes)
    filtered.rsf(directory / "filtered.rsf")
    write_csv(directory / "retained_classes.csv", [{"class": n} for n in filtered.nodes], ["class"])
    universe = read_json(ROOT / "data/graphs/feature_universe.json")
    architectures = {}
    for condition, current in (("A1", graph), ("A2", filtered), ("A3", graph), ("A4", filtered)):
        if condition in ("A1", "A2"):
            assignment, metadata = _run_acdc(current, directory / (condition + "_run"), config, executable)
        else:
            assignment, metadata = _run_kmeans(current, universe, len(graph.nodes), config, calibration)
        save_partition(directory / (condition + ".csv"), assignment)
        measurement = evaluate_partition(current.nodes, current.edges, assignment)
        write_json(directory / (condition + "_metrics.json"), measurement)
        write_metric_tables(measurement, directory / (condition + "_quality"))
        write_json(directory / (condition + "_run.json"), metadata)
        architectures[condition] = assignment

    # Regenerate all six latest-release comparison records. The two temporal
    # records use the previous *archived* release as the stated reference.
    details, common_rows = [], []
    def comparison(scope, left, right, a, b, nodes, previous_version="", n_edges=None):
        a, b = {n: a[n] for n in nodes}, {n: b[n] for n in nodes}
        forward, reverse = compare_mojofm(a, b), compare_mojofm(b, a)
        value = {"version": version, "previous_version": previous_version, "scope": scope,
                 "source_condition": left, "reference_condition": right,
                 "n_nodes": len(nodes), "n_edges": n_edges,
                 "source_clusters": forward["source_clusters"], "reference_clusters": forward["target_clusters"],
                 "mojo_distance": forward["distance"], "mojo_max_distance": forward["max_distance"], "mojofm": forward["score"],
                 "reverse_mojo_distance": reverse["distance"], "reverse_mojo_max_distance": reverse["max_distance"], "reverse_mojofm": reverse["score"],
                 "node_universe_sha256": hashlib.sha256(("\n".join(sorted(nodes)) + "\n").encode()).hexdigest(),
                 "interpretation": "directional partition agreement; reference is not validated ground truth"}
        details.append({"comparison": value, "forward": forward, "reverse": reverse})
        return value

    for full, without in (("A1", "A2"), ("A3", "A4")):
        projected = {n: architectures[full][n] for n in filtered.nodes}
        baseline = evaluate_partition(filtered.nodes, filtered.edges, projected)
        recovered = evaluate_partition(filtered.nodes, filtered.edges, architectures[without])
        write_json(directory / f"{full}_projected_to_retained_metrics.json", baseline)
        value = comparison("full_vs_filtered_retained", full, without, projected,
                           architectures[without], filtered.nodes, n_edges=len(filtered.edges))
        common_rows.append({"version": version, "full_condition": full, "filtered_condition": without,
                            "common_classes": len(filtered.nodes), "common_edges": len(filtered.edges),
                            "projected_full_mq": baseline["mq"], "recovered_filtered_mq": recovered["mq"],
                            "mq_change_same_graph": recovered["mq"] - baseline["mq"] if baseline["mq"] is not None else None,
                            "mojofm_full_to_filtered": value["mojofm"], "mojofm_filtered_to_full": value["reverse_mojofm"],
                            "mojo_distance_full_to_filtered": value["mojo_distance"],
                            "mojo_distance_filtered_to_full": value["reverse_mojo_distance"]})
    comparison("algorithms_full", "A1", "A3", architectures["A1"], architectures["A3"], graph.nodes, n_edges=len(graph.edges))
    comparison("algorithms_retained", "A2", "A4", architectures["A2"], architectures["A4"], filtered.nodes, n_edges=len(filtered.edges))
    old_version = manifest["versions"][-2]["version"]
    old_graph = read_graph(ROOT / "data/graphs" / old_version)
    common = tuple(sorted(set(old_graph.nodes) & set(graph.nodes)))
    old_partitions = {condition: load_partition(ROOT / "results/versions" / old_version / (condition + ".csv"))
                      for condition in ("A1", "A3")}
    acdc = comparison("temporal_full_common", "A1", "A1", old_partitions["A1"], architectures["A1"], common, old_version)
    kmeans = comparison("temporal_full_common", "A3", "A3", old_partitions["A3"], architectures["A3"], common, old_version)
    write_json(directory / "partition_comparisons.json", {"version": version, "comparisons": details})
    common_set = set(common)
    old_edges = {e for e in old_graph.edges if set(e) <= common_set}
    new_edges = {e for e in graph.edges if set(e) <= common_set}
    edge_union = old_edges | new_edges
    temporal = {"previous_version": old_version, "version": version, "common_classes": len(common),
                "added_classes": len(set(graph.nodes) - set(old_graph.nodes)),
                "removed_classes": len(set(old_graph.nodes) - set(graph.nodes)),
                "common_node_edge_jaccard": len(old_edges & new_edges) / len(edge_union) if edge_union else 1.0,
                "acdc_mojofm_previous_to_current": acdc["mojofm"], "acdc_mojofm_current_to_previous": acdc["reverse_mojofm"],
                "kmeans_mojofm_previous_to_current": kmeans["mojofm"], "kmeans_mojofm_current_to_previous": kmeans["reverse_mojofm"]}

    pairs = []
    expected_graph = ROOT / "data/graphs" / version
    expected_results = ROOT / "results/versions" / version
    for expected in sorted(expected_graph.iterdir()):
        if expected.is_file() and expected.name not in GRAPH_METADATA_EXCLUSIONS:
            pairs.append((expected, graph_dir / expected.name))
    result_names = ["ue.json", "omnipresent.csv", "filtered.rsf", "retained_classes.csv", "partition_comparisons.json",
                    "A1_projected_to_retained_metrics.json", "A3_projected_to_retained_metrics.json"]
    for condition in ("A1", "A2", "A3", "A4"):
        result_names.extend(condition + suffix for suffix in (".csv", ".rsf", "_metrics.json"))
        result_names.extend(f"{condition}_quality/{name}.csv" for name in ("metrics_summary", "per_cluster", "per_pair"))
        if condition in ("A1", "A2"):
            result_names.extend(f"{condition}_run/{name}" for name in ("acdc_raw.rsf", "input.rsf", "node_id_map.csv"))
    pairs.extend((expected_results / name, directory / name) for name in result_names)
    comparisons = [byte_comparison(a, b, output) for a, b in pairs]
    for name, values in (("partition_comparisons.csv", [item["comparison"] for item in details]),
                         ("same_graph_comparisons.csv", common_rows), ("evolution.csv", [temporal])):
        archived_rows = [item for item in read_csv(ROOT / "results" / name) if item["version"] == version]
        expected_subset = output / "reference" / ("latest_" + name)
        write_csv(expected_subset, archived_rows)
        generated = directory / name
        write_csv(generated, values)
        comparisons.append(byte_comparison(expected_subset, generated, output,
                           description=f"Latest-release row projection of results/{name}; original column order retained"))

    # Independently establish that the newly scoped JAR contains original class
    # bytes, in addition to comparing the complete deterministic ZIP bytes.
    class_checks = []
    with ZipFile(ROOT / row["jar_path"]) as original, ZipFile(graph_dir / "instructor_input.jar") as scoped:
        for name in scoped.namelist():
            observed, source = scoped.read(name), original.read(name)
            class_checks.append({"jar_entry": name, "bytes": len(observed),
                                 "source_sha256": hashlib.sha256(source).hexdigest(),
                                 "scoped_sha256": hashlib.sha256(observed).hexdigest(),
                                 "byte_identical": source == observed})
    write_csv(output / "original_class_byte_checks.csv", class_checks)
    ignored_provenance = ("extraction_seconds", "instructor_extraction_seconds", "supplemental_extraction_seconds", "stdout", "stderr")
    old_provenance = read_json(expected_graph / "provenance.json")
    normalized_old = {k: v for k, v in old_provenance.items() if k not in ignored_provenance}
    normalized_new = {k: v for k, v in extraction.items() if k not in ignored_provenance}
    metadata_match = normalized_old == normalized_new
    run_metadata = []
    for condition in ("A1", "A2", "A3", "A4"):
        name = condition + "_run.json"
        ignored = ["elapsed_seconds"] + (["command"] if condition in ("A1", "A2") else [])
        before, after = read_json(expected_results / name), read_json(directory / name)
        run_metadata.append({"file": name, "omitted_top_level_fields": ignored,
                             "equal_after_declared_omissions": {k: v for k, v in before.items() if k not in ignored} == {k: v for k, v in after.items() if k not in ignored}})
    passed = (all(item["byte_identical"] for item in comparisons)
              and all(item["byte_identical"] for item in class_checks)
              and metadata_match and all(item["equal_after_declared_omissions"] for item in run_metadata))
    result = {"status": "passed" if passed else "failed", "version": version,
              "canonical_classes": len(graph.nodes), "edges": len(graph.edges), "isolates": len(graph.isolates),
              "removed_classes": list(noise.removed_classes), "retained_classes": len(filtered.nodes), "retained_edges": len(filtered.edges),
              "frozen_k_calibration_sha256": sha(calibration_path), "pilot_n": calibration["pilot_n"], "pilot_k": calibration["pilot_k"],
              "byte_comparisons": comparisons, "comparison_count": len(comparisons),
              "original_class_byte_checks": {"count": len(class_checks), "all_passed": all(item["byte_identical"] for item in class_checks),
                                               "file": "original_class_byte_checks.csv", "sha256": sha(output / "original_class_byte_checks.csv")},
              "provenance_comparison": {"equal_after_declared_omissions": metadata_match, "omitted_top_level_fields": list(ignored_provenance)},
              "architecture_run_metadata_comparisons": run_metadata,
              "excluded_from_byte_comparison": {"graph_files": sorted(GRAPH_METADATA_EXCLUSIONS),
                  "architecture_files": ["A1_run.json", "A2_run.json", "A3_run.json", "A4_run.json",
                                         "A1_run/acdc_execution.json", "A2_run/acdc_execution.json",
                                         "A1_run/acdc_stdout.log", "A1_run/acdc_stderr.log", "A2_run/acdc_stdout.log", "A2_run/acdc_stderr.log"],
                  "reason": "Execution metadata/logs can contain elapsed time or absolute input/output paths; regenerated files are preserved under work/"},
              "temporal_reference": {"version": old_version, "source": "archived previous-release graph and A1/A3 partitions; only the latest release was re-extracted"},
              "scope": "Repeat execution of published extraction, UE and four recovery conditions; an extra verification run, excluded from finalized study architecture counts"}
    save(output / "latest_reproduction.json", result)
    print(json.dumps({"status": result["status"], "version": version, "byte_comparisons": len(comparisons), "original_class_bytes_checked": len(class_checks)}), flush=True)
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--expected-commit", required=True, help="Full published Git commit SHA to verify; no branch name")
    parser.add_argument("--output", required=True, type=Path, help="New or empty evidence directory; preferably outside the checkout")
    parser.add_argument("--command-timeout", type=int, default=1800, help="Maximum seconds per verification command (default: 1800)")
    parser.add_argument("--latest-only", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    require(re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", args.expected_commit) is not None, "Supply a full hexadecimal Git commit SHA")
    require(args.command_timeout > 0, "Command timeout must be positive")
    expected_commit = args.expected_commit.lower()
    output = args.output.resolve()
    if args.latest_only:
        return reproduce_latest(output, expected_commit)
    require(not output.exists() or output.is_dir() and not any(output.iterdir()), "Evidence directory must be new or empty")
    # Inspect the tree before creating an output directory inside it.
    observed = git("rev-parse", "HEAD").strip()
    require(observed == expected_commit, f"HEAD is {observed}, expected {expected_commit}")
    require(Path(git("rev-parse", "--show-toplevel").strip()).resolve() == ROOT, "Runner is not at the checkout root")
    initial_status = git("status", "--porcelain=v1", "--untracked-files=all")
    require(not initial_status, "Verification requires a clean checkout, including no untracked files")
    manifest = read_json(ROOT / "config/versions.json")
    generated_paths = [ROOT / name for name in ("build", "data/raw", "data/upstream_git", "results/versions", "results/pilot")]
    generated_paths += [ROOT / "data/graphs" / row["version"] for row in manifest["versions"]]
    existing = [relative(path, ROOT) for path in generated_paths if path.exists() and (not path.is_dir() or any(path.iterdir()))]
    require(not existing, f"Expected a fresh checkout without expanded data or build caches: {existing}")
    output.mkdir(parents=True, exist_ok=True)
    receipt_path = output / "receipt.json"
    receipt = {"schema_version": 2, "status": "running", "started_at_utc": now(),
               "checkout": str(ROOT), "expected_commit": expected_commit, "initial_commit": observed,
               "initial_git_status": initial_status, "initial_generated_paths_present": existing,
               "git_preflight_argv": [["git", "rev-parse", "HEAD"], ["git", "rev-parse", "--show-toplevel"],
                                       ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                                       ["git", "rev-parse", "--show-object-format"], ["git", "ls-tree", "-r", "-z", "--full-tree", "HEAD"]],
               "runner_path": "scripts/verify_clean_checkout.py", "runner_sha256": sha(__file__),
               "invocation_argv": [PYTHON, *sys.argv], "commands": [],
               "network_policy": "The runner performs no clone/fetch/install. Tool assets must already be bundled; Maven and endpoint Git archives are verified with --offline.",
               "scope": "All selected-release artifacts and independent validation; fresh extraction/UE/A1-A4 for latest release; recorded AI response re-evaluation"}
    save(receipt_path, receipt)
    env = os.environ.copy()
    env["LOKY_MAX_CPU_COUNT"] = "1"
    try:
        inventory = committed_file_inventory()
        save(output / "committed_file_checksums.json", inventory)
        receipt["committed_file_count"] = len(inventory)
        receipt["committed_file_checksums_sha256"] = sha(output / "committed_file_checksums.json")
        sys.path.insert(0, str(ROOT / "src"))
        from evolution.toolchain import java_env, java_path, verify_tools
        verify_tools()  # fail locally before a helper could attempt a download
        executable = java_path()
        env["EVOLUTION_JAVA"] = executable
        env.update({key: value for key, value in java_env(executable).items() if key == "LD_LIBRARY_PATH"})
        versions = {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "scikit-learn", "matplotlib", "reportlab")}
        receipt["environment"] = {"python": sys.version, "python_executable": PYTHON, "platform": platform.platform(),
                                  "zlib_compile_version": zlib.ZLIB_VERSION, "zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION,
                                  "packages": versions, "EVOLUTION_JAVA": executable, "LOKY_MAX_CPU_COUNT": "1",
                                  "thread_environment": {key: env[key] for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS") if key in env}}
        original_results = {}
        ai_files = ["metrics.json", "retained_metrics.json", "comparisons.csv", "partition_comparisons.json", "evaluation.json"]
        ai_files += [f"quality_{scope}/{name}.csv" for scope in ("full", "retained") for name in ("metrics_summary", "per_cluster", "per_pair")]
        audited_files = {"results/validation.json": ["validated_at_utc"], "results/change_points.json": ["audited_at_utc"],
                         "results/performance/case_checks.json": ["checked_at_utc"], "results/revision_comparison.json": [],
                         "docs/ue_case_study.md": []}
        audited_files.update({"results/ai/" + name: [] for name in ai_files})
        for name in audited_files:
            path = ROOT / name
            reference = output / "reference" / name
            reference.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, reference)
            original_results[name] = reference

        commands = [
            ("java-version", [executable, "-version"]),
            ("unpack-data", [PYTHON, "scripts/unpack_data.py"]),
            ("verify-tools", [PYTHON, "scripts/fetch_tools.py"]),
            ("verify-artifacts-offline", [PYTHON, "scripts/fetch_data.py", "--offline", "--verify-git"]),
            ("verify-version-selection", [PYTHON, "scripts/select_versions.py", "--check"]),
            ("correctness-tests", [PYTHON, "scripts/run_checks.py"]),
            ("independent-full-validation", [PYTHON, "scripts/validate_results.py"]),
            ("recorded-ai-evaluation", [PYTHON, "scripts/evaluate_ai.py"]),
            ("change-point-audit", [PYTHON, "scripts/audit_change_points.py"]),
            ("revision-audit", [PYTHON, "scripts/audit_revision.py"]),
            ("ue-case-audit", [PYTHON, "scripts/audit_ue_cases.py", "--version", manifest["versions"][-1]["version"]]),
            ("latest-repeat-execution", [PYTHON, str(Path(__file__).resolve()), "--expected-commit", expected_commit,
                                         "--output", str(output), "--latest-only"]),
        ]
        for index, (label, command) in enumerate(commands, 1):
            started, started_at = time.perf_counter(), now()
            log = output / f"{index:02d}-{label}.log"
            print("RUN", shlex.join(command), flush=True)
            with log.open("w", encoding="utf-8") as stream:
                try:
                    completed = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=args.command_timeout)
                    exit_code, timed_out = completed.returncode, False
                except subprocess.TimeoutExpired:
                    exit_code, timed_out = None, True
            entry = {"label": label, "argv": command, "cwd": str(ROOT), "started_at_utc": started_at,
                     "completed_at_utc": now(), "exit_code": exit_code, "timed_out": timed_out,
                     "elapsed_seconds": time.perf_counter() - started, "log": log.name, "log_sha256": sha(log)}
            receipt["commands"].append(entry)
            save(receipt_path, receipt)
            require(exit_code == 0 and not timed_out, f"Command failed: {label}; see {log}")
            if label == "correctness-tests":
                matches = re.findall(r"Ran (\d+) tests?", log.read_text(encoding="utf-8"))
                require(len(matches) == 1 and int(matches[0]) > 0, "Test runner did not report an executed test count")
                receipt["tests_executed"] = int(matches[0])
            print("PASS", label, flush=True)

        repeated = []
        for name, omissions in audited_files.items():
            reference, actual = original_results[name], ROOT / name
            record = byte_comparison(reference, actual, output)
            record["committed_output"] = name
            if omissions:
                before, after = read_json(reference), read_json(actual)
                record["omitted_top_level_fields"] = omissions
                record["equal_after_declared_omissions"] = {k: v for k, v in before.items() if k not in omissions} == {k: v for k, v in after.items() if k not in omissions}
                require(record["equal_after_declared_omissions"], f"Recomputed audit differs beyond timestamp: {name}")
            else:
                require(record["byte_identical"], f"Recomputed deterministic output differs: {name}")
            repeated.append(record)
        save(output / "recomputed_output_comparisons.json", repeated)
        receipt["recomputed_output_comparisons_sha256"] = sha(output / "recomputed_output_comparisons.json")
        receipt["recomputed_output_count"] = len(repeated)
        receipt["latest_reproduction"] = read_json(output / "latest_reproduction.json")
        receipt["independent_validation"] = {key: read_json(ROOT / "results/validation.json")[key]
                                             for key in ("status", "checks_performed", "failure_count", "ai")}
        require(receipt["latest_reproduction"]["status"] == "passed", "Latest repeat execution failed")
        require(receipt["independent_validation"]["status"] == "passed", "Independent validation did not pass")
        require(read_json(ROOT / "results/ai/evaluation.json")["status"] == "passed", "AI re-evaluation did not pass")
        receipt["final_commit"] = git("rev-parse", "HEAD").strip()
        require(receipt["final_commit"] == expected_commit, "Commit changed during verification")
        changed = []
        for item in inventory:
            path = ROOT / item["path"]
            content = os.fsencode(os.readlink(path)) if item["mode"] == "120000" else path.read_bytes()
            after = hashlib.sha256(content).hexdigest()
            if after != item["sha256"]:
                changed.append({"path": item["path"], "before_sha256": item["sha256"], "after_sha256": after,
                                "allowed_variable_audit_output": item["path"] in VOLATILE_TRACKED_OUTPUTS})
        require(all(item["allowed_variable_audit_output"] for item in changed), "Unexpected tracked file mutation during verification")
        receipt["tracked_file_changes"] = changed
        receipt["final_git_status"] = git("status", "--porcelain=v1", "--untracked-files=all")
        receipt["pdf_files"] = [{"path": item["path"], "sha256": item["sha256"], "unchanged_from_committed_bytes": sha(ROOT / item["path"]) == item["sha256"]}
                                for item in inventory if item["path"].lower().endswith(".pdf")]
        receipt["archives"] = {"manifest_sha256": sha(ROOT / "archives/manifest.json"),
                               "bundle_count": len(read_json(ROOT / "archives/manifest.json")["bundles"]),
                               "member_count": sum(bundle["member_count"] for bundle in read_json(ROOT / "archives/manifest.json")["bundles"])}
        receipt["status"] = "passed"
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error_type"] = type(error).__name__
        receipt["error"] = str(error)
        (output / "failure.log").write_text(traceback.format_exc(), encoding="utf-8")
        print("FAILED", str(error), flush=True)
    receipt["completed_at_utc"] = now()
    save(receipt_path, receipt)
    print(json.dumps({"status": receipt["status"], "commit": observed, "receipt": str(receipt_path)}), flush=True)
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
