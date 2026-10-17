"""Instructor class graphs plus separate member-aware supplemental evidence.

Only the unmodified instructor tool contributes primary graph relationships.
The custom ASM pass supplies source ownership, enclosing identities and UE
member evidence; its broader graph is preserved for sensitivity auditing only.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import os
from pathlib import Path
import subprocess
import time
import zipfile

from .graph import read_csv, read_graph, sha256, write_csv, write_json
from .toolchain import (ROOT, INSTRUCTOR_JAR, INSTRUCTOR_SHA256,
                        instructor_classpath, java_env, java_path)


def count_java_lines(text: str) -> dict[str, int]:
    """Count physical/nonblank/code lines with a small Java comment/string lexer.

    This is a size indicator, not a measure of functionality. Text blocks are
    respected. A line containing both code and a comment counts as a code line.
    """
    lines = text.splitlines()
    state = "code"
    code_count = 0
    for line in lines:
        i, has_code = 0, False
        while i < len(line):
            if state == "block":
                end = line.find("*/", i)
                if end < 0:
                    break
                state, i = "code", end + 2
            elif state == "text":
                has_code = True
                end = line.find('"""', i)
                if end < 0:
                    break
                state, i = "code", end + 3
            elif line.startswith("//", i):
                break
            elif line.startswith("/*", i):
                state, i = "block", i + 2
            elif line.startswith('"""', i):
                has_code, state, i = True, "text", i + 3
            elif line[i] in "\"'":
                has_code, quote, i = True, line[i], i + 1
                while i < len(line):
                    if line[i] == "\\":
                        i += 2
                    elif line[i] == quote:
                        i += 1
                        break
                    else:
                        i += 1
            else:
                has_code = has_code or not line[i].isspace()
                i += 1
        code_count += int(has_code)
    return {"physical_java_lines": len(lines), "nonblank_java_lines": sum(bool(x.strip()) for x in lines), "java_code_lines": code_count}



OWNED_PREFIXES = ("com.google.common", "com.google.thirdparty.publicsuffix")
RELATIONS = frozenset({"EXTENDS", "IMPLEMENTS", "METHOD_CALL", "METHOD_PARAMETER",
                       "FIELD_REFERENCE", "TYPE_USAGE", "EXCEPTION_THROWS"})


def make_instructor_input(binary: Path, aliases: list[dict], output: Path) -> dict:
    """Preserve original owned base class bytes in a deterministic input JAR.

    Target libraries, module/package descriptors and MR override entries never
    enter the instructor scanner. Enclosing and source ownership decisions have
    already been taken from the supplemental metadata pass, independently of
    which nodes happen to have edges. This is graph scope normalization, not a
    rewrite of bytecode. The complete original Maven binary remains preserved.
    """
    target = output / "instructor_input.jar"
    temporary = target.with_suffix(".jar.part")
    rows = []
    with zipfile.ZipFile(binary) as original, zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as derived:
        entries = Counter(original.namelist())
        for alias in sorted(aliases, key=lambda r: r["binary_class"]):
            name = alias["binary_class"].replace(".", "/") + ".class"
            if entries[name] != 1:
                raise ValueError(f"Owned binary class does not have one base entry: {name}")
            content = original.read(name)
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            derived.writestr(entry, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            rows.append({"binary_class": alias["binary_class"], "class": alias["class"],
                         "jar_entry": name, "bytes": len(content),
                         "class_sha256": hashlib.sha256(content).hexdigest()})
    temporary.replace(target)
    write_csv(output / "instructor_input_classes.csv", rows,
              ["binary_class", "class", "jar_entry", "bytes", "class_sha256"])
    metadata = {
        "file": target.name, "sha256": sha256(target), "source_binary_sha256": sha256(binary),
        "class_entries": len(rows), "class_bytes": sum(r["bytes"] for r in rows),
        "inventory_sha256": sha256(output / "instructor_input_classes.csv"),
        "policy": "Only source-owned base class entries; original class bytes unchanged; sorted ZIP entries with fixed timestamps; no target execution",
    }
    write_json(output / "instructor_input.json", metadata)
    return metadata


def normalize_instructor(output: Path) -> dict:
    """Normalize only instructor rows into the primary unweighted class graph."""
    classes = read_csv(output / "classes.csv")
    nodes = {r["class"] for r in classes}
    annotations = {r["class"] for r in classes if r["kind"] == "annotation"}
    aliases = {r["binary_class"]: r["class"] for r in read_csv(output / "class_aliases.csv")}
    raw = read_csv(output / "instructor_raw.csv")
    required = {"dependeeClass", "dependencyClass", "DependencyType", "DependencySubtype", "Times"}
    if raw and not required <= set(raw[0]):
        raise ValueError("Unexpected instructor CSV schema")
    typed = set()
    excluded, counts = [], Counter()
    raw_types = Counter()
    for row in raw:
        relation = row["DependencyType"]
        if relation not in RELATIONS:
            raise ValueError(f"Unknown instructor relation: {relation}")
        if int(row["Times"]) < 1:
            raise ValueError("Invalid instructor dependency occurrence count")
        raw_types[relation] += 1
        source, target = aliases.get(row["dependeeClass"]), aliases.get(row["dependencyClass"])
        if source is None or target is None:
            reason = ("both_endpoints_outside_owned_scope" if source is None and target is None
                      else "source_outside_owned_scope" if source is None else "target_outside_owned_scope")
        elif source == target:
            reason = "self_after_outer_merge"
        else:
            counts["accepted_raw_typed_rows"] += 1
            typed.add((source, target, relation))
            continue
        counts[reason] += 1
        excluded.append({**row, "reason": reason})
    edges = {(source, target) for source, target, _ in typed}
    write_csv(output / "dependencies_typed.csv",
              [{"source": a, "target": b, "relation": r} for a, b, r in sorted(typed)],
              ["source", "target", "relation"])
    write_csv(output / "dependencies.csv", [{"source": a, "target": b} for a, b in sorted(edges)],
              ["source", "target"])
    write_csv(output / "instructor_excluded_rows.csv", sorted(excluded, key=lambda r: (
        r["dependeeClass"], r["dependencyClass"], r["DependencyType"], r["DependencySubtype"], int(r["Times"]))),
        ["dependeeClass", "dependencyClass", "DependencyType", "DependencySubtype", "Times", "reason"])
    counts.update({"raw_typed_rows": len(raw), "excluded_raw_typed_rows": len(excluded),
                   "unique_typed_edges": len(typed), "unique_directed_edges": len(edges),
                   "duplicate_normalized_typed_rows": counts["accepted_raw_typed_rows"] - len(typed)})
    write_csv(output / "instructor_normalization_counts.csv",
              [{"metric": k, "value": v} for k, v in sorted(counts.items())], ["metric", "value"])
    supplemental_rows = read_csv(output / "supplemental_dependencies_typed.csv")
    supplemental = {(r["source"], r["target"]) for r in supplemental_rows}
    supplemental_types = {}
    for row in supplemental_rows:
        supplemental_types.setdefault((row["source"], row["target"]), set()).add(row["relation"])
    for name, difference in (("supplemental_only_edges.csv", supplemental - edges),
                             ("instructor_only_edges.csv", edges - supplemental)):
        write_csv(output / name, [{"source": a, "target": b, "target_is_annotation": b in annotations,
                                  "supplemental_relations": ";".join(sorted(supplemental_types.get((a, b), set())))}
                                 for a, b in sorted(difference)],
                  ["source", "target", "target_is_annotation", "supplemental_relations"])
    graph = read_graph(output)
    graph.rsf(output / "full.rsf")
    if not set(graph.nodes) == nodes:
        raise ValueError("Instructor normalization changed the independently collected node inventory")
    counts_supplemental = {r["metric"]: int(r["value"]) for r in read_csv(output / "supplemental_extraction_counts.csv")}
    combined = {**counts_supplemental,
                "supplemental_unique_directed_edges": counts_supplemental["unique_directed_edges"],
                "supplemental_unique_typed_edges": counts_supplemental["unique_typed_edges"],
                "unique_directed_edges": len(edges), "unique_typed_edges": len(typed),
                "instructor_raw_typed_rows": len(raw), "instructor_excluded_raw_typed_rows": len(excluded),
                "primary_isolated_classes": len(graph.isolates), "annotation_classes": len(annotations),
                "primary_annotation_target_edges": sum(b in annotations for a, b in edges)}
    write_csv(output / "extraction_counts.csv", [{"metric": k, "value": v} for k, v in sorted(combined.items())],
              ["metric", "value"])
    return {
        "normalization_counts": dict(sorted(counts.items())),
        "raw_relation_counts": dict(sorted(raw_types.items())),
        "relation_counts": dict(sorted(Counter(r for _, _, r in typed).items())),
        "annotation_classes": len(annotations),
        "annotation_isolated_classes": len(annotations.intersection(graph.isolates)),
        "annotation_target_edges": sum(b in annotations for a, b in edges),
        "annotation_source_edges": sum(a in annotations for a, b in edges),
        "supplemental_dependencies": len(supplemental),
        "supplemental_annotation_target_edges": sum(b in annotations for a, b in supplemental),
        "supplemental_only_edges": len(supplemental - edges),
        "supplemental_only_annotation_target_edges": sum(b in annotations for a, b in supplemental - edges),
        "instructor_only_edges": len(edges - supplemental), "shared_edges": len(edges.intersection(supplemental)),
    }


def extract_artifacts(binary: Path, sources: Path, output: Path, *, java: str | None = None,
                      owned_prefixes: tuple[str, ...] = OWNED_PREFIXES,
                      supplemental_classes: Path | None = None) -> dict:
    """Run both original instructor and supplemental passes on one artifact pair."""
    output.mkdir(parents=True, exist_ok=True)
    executable = java_path(java)
    classpath = instructor_classpath()
    supplemental_classes = supplemental_classes or ROOT / "build/extractor"
    command = [executable, "-Xmx1g", "-cp", os.pathsep.join([str(supplemental_classes), str(ROOT / "tools/asm-9.7.1.jar")]),
               "DependencyExtractor", str(binary), str(sources), str(output), ",".join(owned_prefixes)]
    started = time.perf_counter()
    process = subprocess.run(command, capture_output=True, text=True, env=java_env(executable), timeout=180)
    supplemental_seconds = time.perf_counter() - started
    (output / "supplemental.log").write_text(process.stdout + process.stderr, encoding="utf-8")
    write_json(output / "supplemental_command.json", {"argv": command, "exit_code": process.returncode,
                                                    "role": "ownership, enclosing identities, member evidence and sensitivity graph only"})
    if process.returncode:
        raise RuntimeError(f"Supplemental extraction failed: {binary.name}\n{process.stdout}\n{process.stderr}")
    nodes = {r["class"] for r in read_csv(output / "classes.csv")}
    if not all(any(n.startswith(prefix + ".") for prefix in owned_prefixes) for n in nodes):
        raise ValueError("External class survived source-ownership filtering")
    input_metadata = make_instructor_input(binary, read_csv(output / "class_aliases.csv"), output)
    # A failed upstream invocation must not accidentally reuse a previous CSV.
    (output / "instructor_raw.csv").unlink(missing_ok=True)
    instructor_command = [executable, "-Xmx1g", "-cp", os.pathsep.join(map(str, classpath)),
                          "CompCalc.MainClass", str(output / "instructor_input.jar"), str(output / "instructor_raw.csv")]
    instructor_started = time.perf_counter()
    instructor = subprocess.run(instructor_command, capture_output=True, text=True, env=java_env(executable), timeout=180)
    instructor_seconds = time.perf_counter() - instructor_started
    (output / "instructor.log").write_text(instructor.stdout + instructor.stderr, encoding="utf-8")
    write_json(output / "instructor_command.json", {"argv": instructor_command, "exit_code": instructor.returncode,
                                                   "main_class": "CompCalc.MainClass", "instructor_sha256": INSTRUCTOR_SHA256,
                                                   "input_sha256": input_metadata["sha256"],
                                                   "role": "sole relationship source for the primary class graph"})
    if instructor.returncode or not (output / "instructor_raw.csv").exists():
        raise RuntimeError(f"Instructor extraction failed: {binary.name}\n{instructor.stdout}\n{instructor.stderr}")
    comparison = normalize_instructor(output)
    write_json(output / "extractor_comparison.json", comparison)
    stdout_lines = instructor.stdout.strip().splitlines()
    return {"instructor_input": input_metadata, **comparison,
            "supplemental_extraction_seconds": supplemental_seconds,
            "instructor_extraction_seconds": instructor_seconds,
            "extraction_seconds": time.perf_counter() - started,
            "stdout": "\n".join(stdout_lines if len(stdout_lines) <= 5 else stdout_lines[:2] + stdout_lines[-3:]),
            "stdout_log": "instructor.log", "stderr": instructor.stderr.strip()}


def extract_release(row: dict, output_root: Path, *, java: str | None = None) -> dict:
    version = row["version"]
    output = output_root / version
    for kind in ("jar", "sources", "pom"):
        path = ROOT / row[f"{kind}_path"]
        expected = row[f"{kind}_sha256"]
        if sha256(path) != expected:
            raise ValueError(f"Input checksum mismatch: {version} {kind}")
    audit = extract_artifacts(ROOT / row["jar_path"], ROOT / row["sources_path"], output, java=java)
    graph = read_graph(output)
    classes = read_csv(output / "classes.csv")
    counts = {r["metric"]: int(r["value"]) for r in read_csv(output / "extraction_counts.csv")}
    source_names = sorted({r["source_file"] for r in classes})
    source_sizes = []
    with zipfile.ZipFile(ROOT / row["sources_path"]) as archive:
        for name in source_names:
            source_sizes.append({"source_file": name, **count_java_lines(archive.read(name).decode("utf-8", errors="replace"))})
    write_csv(output / "source_sizes.csv", source_sizes)
    metadata = {
        "schema_version": 2,
        "version": version, "tag": row["tag"], "commit_sha": row["commit_sha"], "date": row["release_date"],
        "date_basis": row["date_basis"], "commit_date": row["commit_date"],
        "classes": len(graph.nodes), "dependencies": len(graph.edges), "isolated_classes": len(graph.isolates),
        "owned_source_files": len(source_names), "raw_binary_classes": counts["owned_binary_classes"],
        "merged_binary_classes": counts["owned_binary_classes"] - len(graph.nodes),
        "excluded_binary_classes": counts["excluded_binary_classes"],
        "unique_member_edges": counts["unique_member_edges"],
        **{key: sum(r[key] for r in source_sizes) for key in ("physical_java_lines", "nonblank_java_lines", "java_code_lines")},
        "primary_extractor": "instructor DependencyExtractor (unmodified CompCalc.MainClass)",
        "instructor_jar_sha256": sha256(INSTRUCTOR_JAR),
        "adapter_sha256": sha256(Path(__file__)),
        "toolchain_sha256": sha256(ROOT / "src/evolution/toolchain.py"),
        "extractor_sha256": sha256(ROOT / "java/DependencyExtractor.java"),
        "extractor_sha256_role": "supplemental Java source; primary relationships come solely from instructor_jar_sha256",
        "supplemental_extractor_sha256": sha256(ROOT / "java/DependencyExtractor.java"),
        "binary_sha256": row["jar_sha256"], "sources_sha256": row["sources_sha256"],
        "pom_sha256": row["pom_sha256"],
        "graph_sha256": sha256(output / "dependencies.csv"), "classes_sha256": sha256(output / "classes.csv"),
        "typed_graph_sha256": sha256(output / "dependencies_typed.csv"),
        "instructor_raw_sha256": sha256(output / "instructor_raw.csv"),
        "member_graph_sha256": sha256(output / "member_dependencies.csv"),
        "static_model": "primary instructor symbolic bytecode relationships; supplemental internal declaration-resolved member uses for UE; no target execution or virtual dispatch expansion",
        "source_ownership": "source-file membership AND com.google.common or com.google.thirdparty.publicsuffix namespace; base entries; enclosing metadata merge; explicit shaded implementation exclusions",
        "owned_namespace_prefixes": list(OWNED_PREFIXES),
        "annotation_policy": "retain owned annotation type nodes and ordinary instructor-recorded code references; do not add annotation-application edges from supplemental ASM",
        "instructor_input_policy": "deterministic JAR containing only owned base class entries; bytecode is unchanged",
        **audit,
    }
    write_json(output / "provenance.json", metadata)
    return metadata
