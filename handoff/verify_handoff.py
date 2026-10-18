#!/usr/bin/env python3
"""Verify the complete handoff without changing the frozen scientific records.

This standard-library runner verifies every published download and full-source
listing, then rehearses the actual twelve-packet import in a new, nested Git
fixture. Its commits use an explicitly automated verification identity and are
never pushed. It runs only the manifest checks marked during_import, preserving
the recorded study files. Java 17+ and the study's Python packages are required.

Run after build_handoff.py has finished:
    python handoff/verify_handoff.py

Detailed command output is retained under verification_logs/. Large disposable
Git and extraction fixtures remain in ignored verification-work/ directories.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import traceback
from zipfile import ZipFile

import build_handoff


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoff"
SENTINEL = b"Teacher's original starter instructions.\nPreserve this file during the automated handoff verification.\n"
TEST_IDENTITY = {"name": "Handoff Verification", "email": "handoff-verification@example.invalid"}
EXCLUDED_STUDY_DIRECTORIES = (
    "results/baseline_v1",
    "results/reproducibility",
    "results/reproducibility_v3",
)
EXCLUDED_STUDY_FILES = {
    "scripts/audit_revision.py",
    "results/revision_comparison.json",
    "report/style_revision_validation.json",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def record(path: Path) -> dict:
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}


def verify_current_inventory(manifest: dict, payload: dict[str, bytes]) -> dict:
    """Reject superseded studies and verify the precise Git payload boundary."""
    inventory = set(payload)
    require(len(inventory) == manifest["source_file_count"], "Current study payload count does not match the manifest")
    obsolete = sorted(path for path in inventory if path in EXCLUDED_STUDY_FILES or any(
        path == directory or path.startswith(directory + "/") for directory in EXCLUDED_STUDY_DIRECTORIES))
    require(not obsolete, "Superseded files are present in the current handoff payload: " + ", ".join(obsolete))
    require(not any(path == "handoff" or path.startswith("handoff/") for path in inventory),
            "Handoff packaging must not be recursively included in the study payload")
    repository_tree = build_handoff.git("rev-parse", manifest["source_commit"] + "^{tree}").decode().strip()
    require(repository_tree == manifest["repository_tree"], "Pinned repository tree differs from the manifest")
    tracked = set()
    for raw in build_handoff.git("ls-tree", "-rz", "--full-tree", manifest["source_commit"]).split(b"\0"):
        if raw:
            _metadata, path = raw.split(b"\t", 1)
            name = path.decode()
            if not name.startswith("handoff/"):
                tracked.add(name)
    require(inventory == tracked, "Study payload must include every pinned repository file except handoff/**")
    return {"source_files": len(inventory), "repository_tree": repository_tree,
            "source_tree": manifest["source_tree"], "repository_exclusions": ["handoff/**"],
            "superseded_directories_checked": list(EXCLUDED_STUDY_DIRECTORIES),
            "superseded_files_checked": sorted(EXCLUDED_STUDY_FILES),
            "superseded_files_found": [], "exact_filtered_repository_inventory": True}


class SourceBlocks(HTMLParser):
    """Decode actual HTML source blocks; source bytes remain the independent oracle."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: dict[str, str] = {}
        self.active: str | None = None
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "code" and "data-source-path" in attributes:
            require(self.active is None, "Nested source-code blocks in HTML")
            path = attributes["data-source-path"]
            require(path not in self.blocks, f"Duplicate HTML source block: {path}")
            self.active, self.parts = path, []
        elif self.active is not None:
            raise ValueError(f"Unexpected HTML tag inside source code: {tag}")

    def handle_endtag(self, tag):
        if self.active is not None:
            require(tag == "code", f"Unexpected HTML closing tag inside source code: {tag}")
            self.blocks[self.active] = "".join(self.parts)
            self.active, self.parts = None, []

    def handle_data(self, data):
        if self.active is not None:
            self.parts.append(data)


def verify_listings(manifest: dict, payload: dict[str, bytes]) -> dict:
    listed = {f["path"]: f for f in manifest["files"] if f["include_in_full_code_listing"]}
    require(len(listed) == manifest["code_listing_files"], "Complete source/configuration listing count differs from the manifest")
    parser = SourceBlocks()
    parser.feed((HANDOFF / "full_code.html").read_bytes().decode("utf-8"))
    parser.close()
    require(parser.active is None, "Unclosed HTML source block")
    require(set(parser.blocks) == set(listed), "HTML source paths do not match the complete listing inventory")
    for path, text in parser.blocks.items():
        require(text.encode("utf-8") == payload[path], f"HTML does not contain the exact complete file: {path}")

    markdown_seen = {}
    marker = re.compile(r"^<!-- FULL_SOURCE (\S+) ([0-9a-f]{64}) -->\n", re.MULTILINE)
    for packet in manifest["packets"]:
        guide = HANDOFF / "code" / (packet["slug"] + ".md")
        text = guide.read_bytes().decode("utf-8")
        found = set()
        for match in marker.finditer(text):
            path, expected_sha = match.groups()
            require(path in listed, f"Unexpected Markdown source block: {path}")
            require(path not in markdown_seen, f"Duplicate Markdown source block: {path}")
            require(listed[path]["packet"] == packet["id"], f"Markdown source in wrong packet: {path}")
            require(expected_sha == listed[path]["sha256"], f"Wrong Markdown source hash: {path}")
            opening = re.match(r"(`{3,})[^\n]*\n", text[match.end():])
            require(opening is not None, f"Missing Markdown source fence: {path}")
            fence = opening.group(1)
            start = match.end() + opening.end()
            end_token = fence + "\n<!-- END_FULL_SOURCE " + path + " -->"
            end = text.find(end_token, start)
            require(end >= 0, f"Missing closing Markdown source fence: {path}")
            original = payload[path].decode("utf-8")
            expected = original if original.endswith("\n") else original + "\n"
            require(text[start:end] == expected, f"Markdown does not contain the whole original file: {path}")
            markdown_seen[path] = guide.relative_to(ROOT).as_posix()
            found.add(path)
        expected_paths = {f["path"] for f in listed.values() if f["packet"] == packet["id"]}
        require(found == expected_paths, f"Incomplete full-source listing in packet {packet['id']}")
        require(text.count("<!-- END_FULL_SOURCE ") == len(found), f"Unpaired Markdown source marker in packet {packet['id']}")
    require(set(markdown_seen) == set(listed), "Markdown listings do not cover all complete code files")
    return {"html_source_blocks": len(parser.blocks), "markdown_source_blocks": len(markdown_seen),
            "source_bytes": sum(len(payload[p]) for p in listed), "exact_original_contents": True,
            "markdown_only_adjustment": "A final newline is added solely to separate a source file without one from its closing code fence."}


def compact_record(item: dict) -> dict:
    return {key: item[key] for key in ("path", "bytes", "sha256", "git_blob_sha1", "mode")}


def expected_packet_metadata(manifest: dict, packet: dict) -> dict:
    return {"schema": 1, "source_commit": manifest["source_commit"], "id": packet["id"],
            "number": packet["number"], "owner": packet["owner"], "title": packet["title"],
            "commit_message": packet["commit_message"],
            "files": [compact_record(f) for f in manifest["files"] if f["packet"] == packet["id"]],
            "prerequisites": [compact_record(f) for f in manifest["files"] if int(f["packet"]) < packet["number"]]}


def common_entries(manifest: dict) -> dict[str, bytes]:
    map_text = (ROOT / "docs/commit_roadmap.md").read_text()
    map_text = map_text.replace("../handoff/download_manifest.json",
                                manifest["source_repository"] + "/blob/main/handoff/download_manifest.json")
    map_text = map_text.replace("../handoff/", "")
    entries = {
        "COMMIT_MAP.md": map_text.encode(),
        "full_code.html": (HANDOFF / "full_code.html").read_bytes(),
        "manifest.json": (HANDOFF / "manifest.json").read_bytes(),
        "file_inventory.csv": (HANDOFF / "file_inventory.csv").read_bytes(),
        "apply_packet.py": (HANDOFF / "apply_packet.py").read_bytes(),
    }
    for p in manifest["packets"]:
        name = p["slug"] + ".md"
        entries["code/" + name] = (HANDOFF / "code" / name).read_bytes()
    return entries


def packet_entries(manifest: dict, packet: dict, payload: dict[str, bytes]) -> dict[str, bytes]:
    values = {
        "packet.json": (json.dumps(expected_packet_metadata(manifest, packet), indent=2) + "\n").encode(),
        "README.md": (HANDOFF / "code" / (packet["slug"] + ".md")).read_bytes(),
    }
    values.update({"payload/" + name: payload[name] for name in packet["paths"]})
    return values


def compare_zip_member(z: ZipFile, info, expected: bytes) -> None:
    require(info.file_size == len(expected), f"Wrong ZIP member size: {info.filename}")
    require(not info.is_dir(), f"Unexpected directory-only ZIP entry: {info.filename}")
    mode = info.external_attr >> 16
    require(stat.S_ISREG(mode), f"Nonregular ZIP member: {info.filename}")
    offset = 0
    with z.open(info) as stream:
        while block := stream.read(1024 * 1024):
            require(block == expected[offset:offset + len(block)], f"Changed ZIP member bytes: {info.filename}")
            offset += len(block)
    require(offset == len(expected), f"Truncated ZIP member: {info.filename}")


def verify_downloads(manifest: dict, payload: dict[str, bytes], downloads: Path) -> dict:
    receipt = read_json(HANDOFF / "download_manifest.json")
    require(receipt["source_commit"] == manifest["source_commit"], "Download source commit mismatch")
    require(receipt["repository_tree"] == manifest["repository_tree"], "Download repository tree mismatch")
    require(receipt["source_tree"] == manifest["source_tree"], "Download source tree mismatch")
    require(receipt["source_files"] == len(payload), "Download source file count mismatch")
    rows = receipt["downloads"]
    require(len(rows) == 15, "Expected all twelve packet ZIPs, both student ZIPs and the small code guide")
    require(Counter(r["kind"] for r in rows) == {"complete_packet": 12, "complete_student": 2, "code_and_guides_only": 1},
            "Download kind counts differ from the complete handoff")
    actual_names = {p.relative_to(downloads).as_posix() for p in downloads.rglob("*.zip")}
    require(actual_names == {r["relative_path"] for r in rows}, "ZIP directory and download manifest differ")
    common = common_entries(manifest)
    packets = {p["id"]: p for p in manifest["packets"]}
    results = []
    for row in rows:
        path = downloads / row["relative_path"]
        require(path.stat().st_size == row["bytes"], f"Download byte count mismatch: {path.name}")
        require(digest(path) == row["sha256"], f"Download SHA-256 mismatch: {path.name}")
        starts = set()
        if row["kind"] == "complete_packet":
            packet = packets[row["packet"]]
            prefix = packet["slug"] + "/"
            expected = {prefix + name: value for name, value in packet_entries(manifest, packet, payload).items()}
            expected[prefix + "apply_packet.py"] = common["apply_packet.py"]
            require(row["owner"] == packet["owner"] and row["payload_files"] == len(packet["paths"]), "Packet download ownership/count mismatch")
        elif row["kind"] == "complete_student":
            owner = row["owner"]
            require(owner in ("A", "B"), "Unknown student download owner")
            require(row["relative_path"] == "student_" + owner + "_current.zip", "Student download must use the current-study filename")
            prefix = "student_" + owner + "/"
            expected = {prefix + name: value for name, value in common.items()}
            starts.add(prefix + "START_HERE.md")
            owned = [p for p in manifest["packets"] if p["owner"] == owner]
            require(row["packets"] == [p["id"] for p in owned], "Student packet assignment mismatch")
            require(row["payload_files"] == sum(len(p["paths"]) for p in owned), "Student payload count mismatch")
            for packet in owned:
                expected.update({prefix + "packets/" + packet["slug"] + "/" + name: value
                                 for name, value in packet_entries(manifest, packet, payload).items()})
        else:
            require(row["relative_path"] == "complete_code_current.zip", "Code download must use the current-study filename")
            prefix = "complete_code/"
            expected = {prefix + name: value for name, value in common.items()}
            starts.add(prefix + "START_HERE.md")
            for f in manifest["files"]:
                if f["include_in_full_code_listing"]:
                    slug = packets[f["packet"]]["slug"]
                    expected[prefix + "source_files/" + slug + "/" + f["path"]] = payload[f["path"]]
            require(row["code_files"] == manifest["code_listing_files"], "Small code guide is missing complete code files")
        with ZipFile(path) as z:
            names = z.namelist()
            require(len(names) == len(set(names)), f"Duplicate ZIP members: {path.name}")
            require(set(names) == set(expected) | starts, f"ZIP member inventory mismatch: {path.name}")
            require(len(names) == row["members"], f"Download member count mismatch: {path.name}")
            require(sum(i.file_size for i in z.infolist()) == row["uncompressed_bytes"], f"Download uncompressed-size mismatch: {path.name}")
            for info in z.infolist():
                relative = PurePosixPath(info.filename)
                require(not relative.is_absolute() and not any(x in ("", ".", "..", ".git") for x in relative.parts),
                        f"Unsafe ZIP path: {info.filename}")
                if info.filename in starts:
                    content = z.read(info)
                    require(content.startswith(b"# ") and b"COMMIT_MAP.md" in content and b"full_code.html" in content,
                            f"Missing usable START_HERE instructions: {path.name}")
                    require(stat.S_ISREG(info.external_attr >> 16), "START_HERE is not a regular file")
                else:
                    compare_zip_member(z, info, expected[info.filename])
        results.append({**row, "sha256_verified": True, "membership_verified": True,
                        "all_expected_contents_verified": True})
    return {"zip_files": len(results), "complete_packet_zips": 12, "complete_student_zips": 2,
            "small_code_guides": 1, "entries_checked": sum(x["members"] for x in results), "downloads": results}


class Audit:
    def __init__(self, logs: Path, output: Path):
        self.logs, self.output = logs, output
        logs.mkdir(parents=True, exist_ok=True)
        self.commands = []
        self.result = {"schema": 1, "started_at_utc": now(), "status": "running", "commands": self.commands,
                       "scope": "Packaging, complete source listings, helper boundary fixtures and a real cumulative nested import; no new canonical scientific experiments."}
        self.env = os.environ.copy()
        for name in list(self.env):
            if name.startswith("GIT_AUTHOR_") or name.startswith("GIT_COMMITTER_"):
                self.env.pop(name)
        self.env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + self.env.get("PATH", "")
        self.env["LOKY_MAX_CPU_COUNT"] = "1"

    def run(self, arguments: list[str], *, cwd: Path, log: str, label: str) -> subprocess.CompletedProcess:
        started = now()
        stamp = time.perf_counter()
        process = subprocess.run(arguments, cwd=cwd, env=self.env, capture_output=True, text=True)
        elapsed = time.perf_counter() - stamp
        log_path = self.logs / log
        number = len(self.commands) + 1
        with log_path.open("a", encoding="utf-8") as stream:
            stream.write(f"\n## Command {number}: {label}\nStarted UTC: {started}\nDirectory: {cwd}\nCommand: {shlex.join(arguments)}\n")
            stream.write(f"Exit code: {process.returncode}; elapsed seconds: {elapsed:.6f}\n\nSTDOUT\n{process.stdout}\nSTDERR\n{process.stderr}\n")
        item = {"number": number, "label": label, "command": arguments, "cwd": str(cwd),
                "started_at_utc": started, "elapsed_seconds": round(elapsed, 6),
                "exit_code": process.returncode, "log": log_path.relative_to(ROOT).as_posix()}
        matched = re.search(r"Ran (\d+) tests? in ", process.stdout + process.stderr)
        if matched:
            item["unittest_count"] = int(matched.group(1))
        self.commands.append(item)
        write_json(self.output, self.result)
        require(process.returncode == 0, f"{label} failed with exit {process.returncode}; see {log_path}")
        return process

    def git(self, target: Path, *arguments: str) -> bytes:
        result = subprocess.run(["git", "--no-optional-locks", "-C", str(target), *arguments], env=self.env,
                                capture_output=True, check=True)
        return result.stdout


def verify_working_files(study: Path, items: list[dict]) -> None:
    for f in items:
        path = study / f["path"]
        require(path.is_file() and not path.is_symlink(), f"Missing/nonregular imported file: {f['path']}")
        require(path.stat().st_size == f["bytes"] and digest(path) == f["sha256"], f"Imported bytes changed: {f['path']}")
        require(bool(path.stat().st_mode & 0o111) == (f["mode"] == "100755"), f"Imported file mode changed: {f['path']}")


def extract_verified_zip(path: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=False)
    with ZipFile(path) as z:
        prefixes = set()
        for info in z.infolist():
            parts = PurePosixPath(info.filename).parts
            require(parts and not info.is_dir() and not PurePosixPath(info.filename).is_absolute()
                    and not any(p in ("", ".", "..", ".git") for p in parts), f"Unsafe import ZIP member: {info.filename}")
            prefixes.add(parts[0])
            out = destination.joinpath(*parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as source, out.open("xb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
            out.chmod(0o644)
    require(len(prefixes) == 1, "Standalone packet ZIP must have one outer directory")
    return destination / prefixes.pop()


def quarantine_transfer_residue(packet_path: Path, packet: dict, manifest: dict,
                                work: Path, audit: Audit, study_root: Path | None = None) -> None:
    """Preserve narrowly proven external partial copies; never edit a payload file.

    Some synchronized execution environments leave rsync-style partial copies
    beside a file that has already arrived intact. This opt-in recovery accepts
    only an unlisted hidden sibling with a random six-character suffix, whose
    complete contents are an exact shorter prefix of a hash-verified listed
    file. Everything else remains for the unchanged importer to reject.
    """
    payload = study_root if study_root is not None else packet_path / "payload"
    scope = "teacher-fixture" if study_root is not None else "packet-payload"
    items = {f["path"]: f for f in manifest["files"]
             if int(f["packet"]) <= packet["number"] and (study_root is not None or f["packet"] == packet["id"])}
    for path in sorted(payload.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(payload).as_posix()
        if relative in items:
            continue
        match = re.fullmatch(r"\.(.+)\.[A-Za-z0-9]{6}", path.name)
        if match is None:
            continue
        original = path.with_name(match.group(1))
        original_relative = original.relative_to(payload).as_posix()
        expected = items.get(original_relative)
        if expected is None or not original.is_file() or original.is_symlink():
            continue
        size = path.stat().st_size
        if not 0 < size < expected["bytes"] or original.stat().st_size != expected["bytes"] or digest(original) != expected["sha256"]:
            continue
        extra = path.read_bytes()
        with original.open("rb") as source:
            if source.read(size) != extra:
                continue
        target = work / "quarantined-environment-files" / scope / ("packet-" + packet["id"]) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        require(not target.exists(), "Quarantine destination already exists")
        expected_extra_hash = hashlib.sha256(extra).hexdigest()
        path.rename(target)
        require(digest(target) == expected_extra_hash, "External partial copy changed during preservation")
        entry = {"packet": packet["id"], "scope": scope, "unexpected_path": relative,
                 "expected_original_path": original_relative, "bytes": size, "sha256": expected_extra_hash,
                 "quarantine": str(target), "full_original_sha256": expected["sha256"],
                 "full_original_unchanged": True, "exact_shorter_prefix": True,
                 "reason": "Unlisted rsync-style partial copy appeared after exact ZIP extraction; preserved outside payload. The strict importer and all manifest/source bytes are unchanged."}
        audit.result.setdefault("environment_recovery", []).append(entry)
        with (audit.logs / "environment-recovery.log").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, indent=2) + "\n")
        print(f"Preserved one proven external partial copy outside packet {packet['id']} payload", flush=True)


def verify_cumulative_import(audit: Audit, manifest: dict, downloads: Path, work: Path,
                             recover_transfer_residue: bool = False) -> dict:
    teacher = work / "teacher"
    teacher.mkdir()
    study = teacher / "guava-study"
    setup_log = "00-environment-and-helper-tests.log"
    audit.run(["git", "init", "-q", str(teacher)], cwd=work, log=setup_log, label="Initialize disposable teacher fixture")
    for option, value in (("user.name", TEST_IDENTITY["name"]), ("user.email", TEST_IDENTITY["email"]),
                          ("commit.gpgsign", "false"), ("core.autocrlf", "false"), ("core.filemode", "true")):
        audit.git(teacher, "config", "--local", option, value)
    (teacher / "README.md").write_bytes(SENTINEL)
    audit.git(teacher, "add", "--", "README.md")
    audit.run(["git", "-C", str(teacher), "commit", "-q", "-m", "Automated handoff verification: teacher starter fixture"],
              cwd=work, log=setup_log, label="Create explicitly automated baseline commit")
    initial_commit = audit.git(teacher, "rev-parse", "HEAD").decode().strip()
    initial_tracked = {}
    for raw in audit.git(teacher, "ls-tree", "-rz", "--full-tree", "HEAD").split(b"\0"):
        if raw:
            metadata, path = raw.split(b"\t", 1)
            initial_tracked[path.decode()] = tuple(metadata.decode().split())
    cumulative = []
    packet_results = []
    full_suite_count = None
    for packet in manifest["packets"]:
        identifier = packet["id"]
        print(f"Verifying packet {identifier}/12: {packet['title']}", flush=True)
        log = identifier + "-packet-" + identifier + ".log"
        packet_path = extract_verified_zip(downloads / "packets" / (packet["slug"] + ".zip"), work / ("extracted-" + identifier))
        helper = packet_path / "apply_packet.py"
        helper_args = [sys.executable, str(helper), "--packet", str(packet_path), "--target", str(teacher), "--subdir", "guava-study"]
        before_head = audit.git(teacher, "rev-parse", "HEAD")
        before_index = digest(teacher / ".git/index")
        before_presence = {name: (study / name).exists() for name in packet["paths"]}
        dry = audit.run(helper_args, cwd=work, log=log, label=f"Packet {identifier} dry run")
        require("Dry run passed" in dry.stdout, f"Packet {identifier} was not a new successful dry run")
        require(audit.git(teacher, "rev-parse", "HEAD") == before_head and digest(teacher / ".git/index") == before_index,
                f"Packet {identifier} dry run changed Git state")
        require(before_presence == {name: (study / name).exists() for name in packet["paths"]}, f"Packet {identifier} dry run copied files")
        audit.run(helper_args + ["--apply"], cwd=work, log=log, label=f"Packet {identifier} copy complete payload")
        require(not audit.git(teacher, "diff", "--cached", "--name-only", "-z"), f"Packet {identifier} apply unexpectedly staged files")
        cumulative.extend(f for f in manifest["files"] if f["packet"] == identifier)
        checks = []
        for check in packet["stage_checks"]:
            if not check["during_import"]:
                continue
            completed = audit.run(["/bin/bash", "-c", check["command"]], cwd=study, log=log,
                                  label=f"Packet {identifier}: {check['purpose']}")
            checks.append({"command": check["command"], "purpose": check["purpose"], "exit_code": completed.returncode})
            if check["kind"] == "complete_test_suite":
                found = re.search(r"Ran (\d+) tests? in ", completed.stdout + completed.stderr)
                require(found is not None and int(found.group(1)) == 91, "Full cumulative study suite did not run all 91 tests")
                full_suite_count = int(found.group(1))
        verify_working_files(study, cumulative)
        require((teacher / "README.md").read_bytes() == SENTINEL, f"Teacher README changed during packet {identifier}")
        if recover_transfer_residue:
            quarantine_transfer_residue(packet_path, packet, manifest, work, audit)
            quarantine_transfer_residue(packet_path, packet, manifest, work, audit, study_root=study)
        audit.run(helper_args + ["--apply", "--stage"], cwd=work, log=log, label=f"Packet {identifier} stage exact reviewed files")
        changed = {p.decode() for p in audit.git(teacher, "diff", "--cached", "--name-only", "-z").split(b"\0") if p}
        require(changed == {"guava-study/" + p for p in packet["paths"]}, f"Packet {identifier} staged paths differ from its complete inventory")
        index_before = digest(teacher / ".git/index")
        audit.run(helper_args + ["--check-staged"], cwd=work, log=log, label=f"Packet {identifier} read-only staged-blob verification")
        require(digest(teacher / ".git/index") == index_before, f"Packet {identifier} staged check changed the index")
        message = f"Automated handoff verification: import packet {identifier} (test fixture only)"
        audit.run(["git", "-C", str(teacher), "commit", "-q", "-m", message], cwd=work, log=log,
                  label=f"Commit packet {identifier} under the explicit automated-test identity")
        if recover_transfer_residue:
            quarantine_transfer_residue(packet_path, packet, manifest, work, audit, study_root=study)
        require(not audit.git(teacher, "status", "--porcelain=v1", "--untracked-files=all"), f"Packet {identifier} leaves uncommitted changes")
        packet_results.append({"packet": identifier, "assigned_student": packet["owner"], "files": len(packet["paths"]),
                               "cumulative_files": len(cumulative), "dry_run_unchanged": True, "staged_paths_exact": True,
                               "frozen_study_files_unchanged": True, "teacher_readme_preserved": True,
                               "import_checks": checks, "fixture_commit": audit.git(teacher, "rev-parse", "HEAD").decode().strip()})
    require(full_suite_count == 91, "The complete 91-test study suite was not exercised")
    require(len(cumulative) == manifest["source_file_count"], "Cumulative import does not contain the complete current study")
    tree = audit.git(teacher, "rev-parse", "HEAD:guava-study").decode().strip()
    require(tree == manifest["source_tree"], "Final nested study tree differs from the pinned Git source tree")
    tracked = {}
    for raw in audit.git(teacher, "ls-tree", "-rz", "--full-tree", "HEAD").split(b"\0"):
        if not raw:
            continue
        meta, name = raw.split(b"\t", 1)
        mode, kind, blob = meta.decode().split()
        tracked[name.decode()] = (mode, kind, blob)
    study_paths = {"guava-study/" + f["path"] for f in manifest["files"]}
    require(not study_paths.intersection(initial_tracked), "Study import overlaps the original teacher files")
    expected_tracked = set(initial_tracked) | study_paths
    require(set(tracked) == expected_tracked, "Final teacher tree contains missing or unexpected tracked files")
    require(len(tracked) == manifest["source_file_count"] + len(initial_tracked),
            "Final teacher file count differs from the study plus original teacher files")
    for path, original in initial_tracked.items():
        require(tracked[path] == original, f"Original teacher Git object changed: {path}")
    for f in manifest["files"]:
        require(tracked.get("guava-study/" + f["path"]) == (f["mode"], "blob", f["git_blob_sha1"]),
                f"Final committed source blob mismatch: {f['path']}")
    verify_working_files(study, manifest["files"])
    before_head = audit.git(teacher, "rev-parse", "HEAD")
    before_index = digest(teacher / ".git/index")
    repeat = audit.run(helper_args, cwd=work, log="13-final-tree-and-idempotence.log", label="Repeat final packet as an idempotent dry run")
    require("No new commit is needed" in repeat.stdout, "Completed final packet does not report that no new commit is needed")
    require(audit.git(teacher, "rev-parse", "HEAD") == before_head and digest(teacher / ".git/index") == before_index,
            "Final idempotent dry run changed Git state")
    if recover_transfer_residue:
        quarantine_transfer_residue(packet_path, packet, manifest, work, audit, study_root=study)
    require(not audit.git(teacher, "status", "--porcelain=v1", "--untracked-files=all"), "Final idempotent dry run leaves changes")
    require((teacher / "README.md").read_bytes() == SENTINEL, "Original teacher README did not survive the full import")
    history = audit.git(teacher, "log", "--format=%an <%ae>|%cn <%ce>|%s").decode().splitlines()
    expected_identity = f"{TEST_IDENTITY['name']} <{TEST_IDENTITY['email']}>"
    require(len(history) == 13 and all(line.startswith(expected_identity + "|" + expected_identity + "|Automated handoff verification:") for line in history),
            "Fixture commits lack explicit automated-test identities or labels")
    validation = read_json(study / "results/rerun/handoff-p10-validation.json")
    require(validation.get("status") == "passed" and validation.get("failure_count") == 0,
            "Independent cumulative result validation did not pass without failures")
    return {"layout": "Existing teacher Git repository, untouched root README, nested guava-study directory",
            "fixture_path": str(teacher), "fixture_identity": TEST_IDENTITY, "fixture_initial_commit": initial_commit,
            "fixture_final_commit": before_head.decode().strip(), "fixture_commits": len(history),
            "committed_study_files": len(cumulative), "committed_study_tree": tree,
            "original_teacher_files": len(initial_tracked), "committed_teacher_files": len(tracked),
            "source_tree_exact": True, "all_working_source_bytes_exact": True, "teacher_readme_preserved": True,
            "all_packets_applied_from_actual_downloads": True, "full_study_tests": full_suite_count,
            "final_packet_idempotent": True, "empty_commit_created": False, "pushes_performed": 0,
            "packet_results": packet_results, "independent_validation_output": {
                "sha256": digest(study / "results/rerun/handoff-p10-validation.json"),
                "checks_performed": validation.get("checks_performed"), "failure_count": validation.get("failure_count"),
                "status": validation.get("status"), "source": "Actual cumulative packet10 command output; original results/validation.json remains byte-identical."}}


def run_verification(args) -> int:
    logs = HANDOFF / "verification_logs"
    output = HANDOFF / "verification.json"
    for path in logs.glob("*.log") if logs.exists() else []:
        path.unlink()
    audit = Audit(logs, output)
    started = time.perf_counter()
    try:
        manifest = read_json(HANDOFF / "manifest.json")
        audit.result.update({"source_commit": manifest["source_commit"], "repository_tree": manifest["repository_tree"],
                             "source_tree": manifest["source_tree"]})
        inputs = [Path(__file__), HANDOFF / "build_handoff.py", HANDOFF / "apply_packet.py", HANDOFF / "test_apply_packet.py",
                  HANDOFF / "manifest.json", HANDOFF / "download_manifest.json", HANDOFF / "full_code.html",
                  HANDOFF / "file_inventory.csv", ROOT / "docs/commit_roadmap.md"]
        inputs += [HANDOFF / "code" / (p["slug"] + ".md") for p in manifest["packets"]]
        input_records = [record(p) for p in inputs]
        audit.result["verified_input_files"] = input_records
        usage = shutil.disk_usage(HANDOFF)
        require(usage.free > 2_000_000_000, "At least 2 GB free space is required for disposable verification fixtures")
        audit.result["environment"] = {"python": sys.version, "python_executable": sys.executable, "platform": platform.platform(),
                                       "packages": {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "scikit-learn")},
                                       "disk_free_at_start": usage.free}
        java = args.java or audit.env.get("EVOLUTION_JAVA") or shutil.which("java")
        require(java is not None, "Java 17+ is required")
        java = str(Path(java).resolve())
        java_home = Path(java).parent.parent
        libraries = [str(p) for p in (java_home / "lib", java_home / "lib/server") if p.is_dir()]
        audit.env["EVOLUTION_JAVA"] = java
        if libraries:
            audit.env["LD_LIBRARY_PATH"] = os.pathsep.join(libraries + ([audit.env["LD_LIBRARY_PATH"]] if audit.env.get("LD_LIBRARY_PATH") else []))
        java_result = audit.run([java, "-version"], cwd=ROOT, log="00-environment-and-helper-tests.log", label="Record usable Java runtime")
        audit.result["environment"].update({"java_executable": java, "java_version": (java_result.stderr + java_result.stdout).strip(),
                                             "java_library_path": audit.env.get("LD_LIBRARY_PATH", "")})
        print("Reading and verifying the complete pinned source snapshot", flush=True)
        payload = build_handoff.read_source(manifest)
        audit.result["current_inventory"] = verify_current_inventory(manifest, payload)
        audit.result["source_coverage"] = {"files": len(payload), "bytes": sum(map(len, payload.values())),
                                           "each_assigned_exactly_once": True,
                                           "git_tree_blob_mode_length_and_sha256_verified": True,
                                           "owners": {owner: {"packets": len([p for p in manifest["packets"] if p["owner"] == owner]),
                                                               "files": len([f for f in manifest["files"] if f["owner"] == owner])}
                                                      for owner in ("A", "B")}}
        print("Checking all HTML and Markdown full-source listings", flush=True)
        audit.result["listings"] = verify_listings(manifest, payload)
        print("Checking all fifteen complete downloads and every member", flush=True)
        audit.result["bundles"] = verify_downloads(manifest, payload, args.downloads.resolve())
        del payload
        tests = audit.run([sys.executable, "-m", "unittest", "discover", "-s", "handoff", "-p", "test_apply_packet.py", "-v"],
                          cwd=ROOT, log="00-environment-and-helper-tests.log", label="Run independent importer boundary fixtures")
        count = re.search(r"Ran (\d+) tests? in ", tests.stdout + tests.stderr)
        require(count is not None and int(count.group(1)) >= 19, "Importer fixture suite did not run its complete expected boundary tests")
        audit.result["helper_fixtures"] = {"tests": int(count.group(1)), "failures": 0, "scope": "Independent real-Git helper boundary fixtures; distinct from the 91 scientific tests."}
        work_parent = HANDOFF / "verification-work"
        work_parent.mkdir(exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="run-", dir=work_parent))
        audit.result["cumulative_import"] = verify_cumulative_import(audit, manifest, args.downloads.resolve(), work,
                                                                     args.quarantine_transfer_residue)
        for expected in input_records:
            current = ROOT / expected["path"]
            require(current.stat().st_size == expected["bytes"] and digest(current) == expected["sha256"],
                    f"Handoff input changed while verification was running: {expected['path']}; rebuild and repeat verification")
        audit.result["status"] = "passed"
        audit.result["failed_checks"] = 0
        audit.result["finished_at_utc"] = now()
        audit.result["elapsed_seconds"] = round(time.perf_counter() - started, 6)
        audit.result["logs"] = [record(p) for p in sorted(logs.glob("*.log"))]
        write_json(output, audit.result)
        print(json.dumps({"status": "passed", "source_files": manifest["source_file_count"],
                          "full_code_files": manifest["code_listing_files"], "downloads": audit.result["bundles"]["zip_files"],
                          "helper_tests": audit.result["helper_fixtures"]["tests"], "study_tests": 91,
                          "imported_tree": manifest["source_tree"], "receipt": str(output)}, indent=2), flush=True)
        return 0
    except BaseException as error:
        audit.result.update({"status": "failed", "failed_checks": 1, "failure": str(error),
                             "finished_at_utc": now(), "elapsed_seconds": round(time.perf_counter() - started, 6)})
        failure_log = logs / "failure.log"
        failure_log.write_text(traceback.format_exc(), encoding="utf-8")
        audit.result["logs"] = [record(p) for p in sorted(logs.glob("*.log"))]
        write_json(output, audit.result)
        print(f"Handoff verification failed: {error}", file=sys.stderr, flush=True)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads", type=Path, default=HANDOFF / "downloads")
    parser.add_argument("--java", help="Java17+ executable; alternatively use EVOLUTION_JAVA")
    parser.add_argument("--quarantine-transfer-residue", action="store_true",
                        help="Opt-in synchronized-environment recovery: preserve only hash-proven unlisted partial copies outside payload; log every intervention")
    return run_verification(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
