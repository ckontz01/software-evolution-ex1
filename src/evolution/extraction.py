"""Run member-aware bytecode extraction against checksum-pinned release artifacts."""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile

from .graph import read_csv, read_graph, sha256, write_csv, write_json
from .toolchain import ROOT, java_env, java_path


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


def extract_release(row: dict, output_root: Path, *, java: str | None = None) -> dict:
    version = row["version"]
    output = output_root / version
    for kind in ("jar", "sources", "pom"):
        path = ROOT / row[f"{kind}_path"]
        expected = row[f"{kind}_sha256"]
        if sha256(path) != expected:
            raise ValueError(f"Input checksum mismatch: {version} {kind}")
    executable = java_path(java)
    command = [executable, "-Xmx1g", "-cp", os.pathsep.join([str(ROOT / "build/extractor"), str(ROOT / "tools/asm-9.7.1.jar")]),
               "DependencyExtractor", str(ROOT / row["jar_path"]), str(ROOT / row["sources_path"]), str(output), "com.google.common"]
    started = time.perf_counter()
    process = subprocess.run(command, capture_output=True, text=True, env=java_env(executable), timeout=180)
    elapsed = time.perf_counter() - started
    if process.returncode:
        raise RuntimeError(f"Extraction failed: {version}\n{process.stdout}\n{process.stderr}")
    graph = read_graph(output)
    # All accepted class identities must be owned production Guava classes.
    if not all(n.startswith("com.google.common.") for n in graph.nodes):
        raise ValueError(f"External class survived extraction: {version}")
    graph.rsf(output / "full.rsf")
    classes = read_csv(output / "classes.csv")
    counts = {r["metric"]: int(r["value"]) for r in read_csv(output / "extraction_counts.csv")}
    source_names = sorted({r["source_file"] for r in classes})
    source_sizes = []
    with zipfile.ZipFile(ROOT / row["sources_path"]) as archive:
        for name in source_names:
            source_sizes.append({"source_file": name, **count_java_lines(archive.read(name).decode("utf-8", errors="replace"))})
    write_csv(output / "source_sizes.csv", source_sizes)
    relation_counts = Counter(r["relation"] for r in read_csv(output / "dependencies_typed.csv"))
    metadata = {
        "version": version, "tag": row["tag"], "commit_sha": row["commit_sha"], "date": row["release_date"],
        "date_basis": row["date_basis"], "commit_date": row["commit_date"],
        "classes": len(graph.nodes), "dependencies": len(graph.edges), "isolated_classes": len(graph.isolates),
        "owned_source_files": len(source_names), "raw_binary_classes": counts["owned_binary_classes"],
        "merged_binary_classes": counts["owned_binary_classes"] - len(graph.nodes),
        "excluded_binary_classes": counts["excluded_binary_classes"],
        "unique_member_edges": counts["unique_member_edges"],
        **{key: sum(r[key] for r in source_sizes) for key in ("physical_java_lines", "nonblank_java_lines", "java_code_lines")},
        "relation_counts": dict(sorted(relation_counts.items())),
        "extractor_sha256": sha256(ROOT / "java/DependencyExtractor.java"),
        "binary_sha256": row["jar_sha256"], "sources_sha256": row["sources_sha256"],
        "graph_sha256": sha256(output / "dependencies.csv"), "classes_sha256": sha256(output / "classes.csv"),
        "extraction_seconds": elapsed,
        "static_model": "base-class bytecode; symbolic calls with internal declaration resolution; no virtual dispatch expansion",
        "source_ownership": "com.google.common namespace AND source-file membership; explicit shaded-code exclusion; outer metadata merging",
        "stdout": process.stdout.strip(), "stderr": process.stderr.strip(),
    }
    write_json(output / "provenance.json", metadata)
    return metadata
