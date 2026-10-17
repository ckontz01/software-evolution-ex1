#!/usr/bin/env python3
"""Acquire the pinned Guava dataset without executing upstream software.

Normal use: python scripts/fetch_data.py
Offline check: python scripts/fetch_data.py --offline
Repeat endpoint source provenance: python scripts/fetch_data.py --verify-git

--bootstrap is only for the initial collection: it fills absent SHA-256 pins
after validating Maven's SHA-1 sidecars, and never replaces an existing pin.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "EPL484-Software-Evolution-Reproducible-Research/1.0"
JAVA_COMMENTS = re.compile(
    r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
    re.S,
)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(data, algorithm="sha256"):
    return hashlib.new(algorithm, data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def download(url, timeout=40):
    """HTTPS-only public download with bounded retries and response size."""
    if not url.startswith("https://"):
        raise ValueError(f"Expected HTTPS URL: {url}")
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = response.read(100_000_001)
            if len(data) > 100_000_000:
                raise ValueError(f"Unexpectedly large response: {url}")
            return data
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(1 + attempt)
    raise AssertionError("unreachable")


def validate_selection(manifest):
    versions = manifest["versions"]
    inventory = json.loads((ROOT / "data/provenance/tag_inventory.json").read_text())
    stable_rows = inventory["stable_tags_in_date_order"]
    stable_versions = [row["version"] for row in stable_rows]
    stable_positions = {version: i for i, version in enumerate(stable_versions)}
    if len(stable_positions) != len(stable_versions):
        raise ValueError("Duplicate stable release in the source tag inventory.")
    if len(versions) != 30:
        raise ValueError("This study must contain exactly 30 releases.")
    if len({v["version"] for v in versions}) != 30:
        raise ValueError("Repeated release in the selected sample.")
    for i, row in enumerate(versions):
        if not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", row["version"]):
            raise ValueError(f"Nonstable version: {row['version']}")
        if not re.fullmatch(r"[a-f0-9]{40}", row["commit_sha"]):
            raise ValueError("Missing immutable Git commit SHA.")
        if row["version"] not in stable_positions:
            raise ValueError(f"Release absent from captured stable inventory: {row['version']}")
        position = stable_positions[row["version"]]
        captured = stable_rows[position]
        if (row["tag"], row["commit_sha"]) != (captured["tag"], captured["commit_sha"]):
            raise ValueError(f"Tag identity differs from captured inventory: {row['version']}")
        if i:
            previous_position = stable_positions[versions[i - 1]["version"]]
            if position <= previous_position + 1:
                raise ValueError(f"Consecutive or reversed stable release at {row['version']}")
            expected_skipped = stable_versions[previous_position + 1:position]
        else:
            expected_skipped = []
        if row["skipped_stable_since_previous"] != expected_skipped:
            raise ValueError(f"Incorrect intervening stable release metadata at {row['version']}")
        if i and versions[i - 1]["release_date"] >= row["release_date"]:
            raise ValueError("Release dates must increase.")
    if len({tuple(r["version"].split(".")[:2]) for r in versions}) < 10:
        raise ValueError("Fewer than 10 major/minor families.")


def artifact_file(row, kind):
    return ROOT / row[f"{kind}_path"]


def fetch_artifact(row, kind, offline, bootstrap):
    path = artifact_file(row, kind)
    expected = row.get(f"{kind}_sha256")
    if not expected and not bootstrap:
        raise ValueError(f"Unpinned {kind} for {row['version']}; initial collection needs --bootstrap.")
    from_cache = path.exists()
    if from_cache:
        data = path.read_bytes()
    elif offline:
        raise FileNotFoundError(path)
    else:
        data = download(row[f"{kind}_url"])
    sha256 = digest(data)
    if expected and sha256 != expected:
        raise ValueError(f"SHA-256 mismatch: {path}; cached files are never silently overwritten.")

    if kind in ("jar", "sources"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"Corrupt ZIP member {bad} in {path}")
            required_suffix = ".class" if kind == "jar" else ".java"
            if not any(n.endswith(required_suffix) for n in archive.namelist()):
                raise ValueError(f"No {required_suffix} members in {path}")
    else:
        doc = ET.fromstring(data)
        ns = {"m": "http://maven.apache.org/POM/4.0.0"}
        version = doc.findtext("m:version", namespaces=ns) or doc.findtext("m:parent/m:version", namespaces=ns)
        artifact = doc.findtext("m:artifactId", namespaces=ns)
        if version != row.get("artifact_version", row["version"]) or artifact != row["artifact_id"]:
            raise ValueError(f"Maven identity mismatch: {path}")

    published_sha1 = row.get(f"{kind}_maven_sha1")
    if published_sha1:
        if digest(data, "sha1") != published_sha1:
            raise ValueError(f"Pinned Maven SHA-1 mismatch: {path}")
    elif not offline:
        # Maven Central published SHA-1 sidecars exist for the historical releases.
        sidecar = download(row[f"{kind}_url"] + ".sha1").decode().strip()
        match = re.search(r"\b[a-fA-F0-9]{40}\b", sidecar)
        if not match:
            raise ValueError(f"Invalid Maven SHA-1 sidecar: {path}")
        published_sha1 = match.group(0).lower()
        if digest(data, "sha1") != published_sha1:
            raise ValueError(f"Published Maven SHA-1 mismatch: {path}")

    if not from_cache:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".part")
        temporary.write_bytes(data)
        temporary.replace(path)
    return {
        "version": row["version"], "kind": kind, "path": row[f"{kind}_path"],
        "url": row[f"{kind}_url"], "bytes": len(data), "sha256": sha256,
        "maven_sha1": published_sha1, "cached": from_cache,
    }


def source_inventory(row):
    """Source SLOC, raw bytecode counts, and source-to-binary ownership evidence."""
    records = []
    with zipfile.ZipFile(artifact_file(row, "sources")) as archive:
        for name in sorted(archive.namelist()):
            if not name.endswith(".java"):
                continue
            text = archive.read(name).decode("utf-8")
            clean = JAVA_COMMENTS.sub(
                lambda m: "\n" * m.group(0).count("\n")
                if m.group(0).startswith(("//", "/*")) else m.group(0),
                text,
            )
            records.append({
                "path": name,
                "sha256": digest(archive.read(name)),
                "physical_lines": len(text.splitlines()),
                "nonblank_noncomment_lines": sum(bool(s.strip()) for s in clean.splitlines()),
            })
    owned_sources = {r["path"][:-5] for r in records
                     if r["path"].startswith(row["source_prefix"])
                     and not r["path"].endswith("package-info.java")}
    with zipfile.ZipFile(artifact_file(row, "jar")) as archive:
        all_classes = [s for s in archive.namelist() if s.endswith(".class")]
        base_classes = [s for s in all_classes if not s.startswith("META-INF/versions/")]
        unsupported = []
        owned = []
        for name in base_classes:
            outer = name[:-6].split("$", 1)[0]
            if outer in owned_sources:
                owned.append(name)
            elif not name.endswith(("module-info.class", "package-info.class")):
                unsupported.append(name)
    return {
        "version": row["version"], "source_java_files": len(records),
        "source_owned_java_files": sum(r["path"].startswith(row["source_prefix"]) for r in records),
        "source_owned_java_nonblank_noncomment_lines": sum(r["nonblank_noncomment_lines"] for r in records if r["path"].startswith(row["source_prefix"])),
        "java_physical_lines": sum(r["physical_lines"] for r in records),
        "java_nonblank_noncomment_lines": sum(r["nonblank_noncomment_lines"] for r in records),
        "raw_class_entries_including_multi_release": len(all_classes),
        "base_class_entries": len(base_classes),
        "source_owned_base_class_entries": len(owned),
        "base_classes_without_owned_source": unsupported,
        "source_files": records,
        "sloc_definition": "Physical Java lines with noncomment, nonwhitespace content. "
            "A lexical scanner preserves string/character literals and removes line/block comments. "
            "Includes source JAR package/module descriptors; not a logical statement count.",
    }


def compare_git_sources(row, repository, offline):
    """Compare every source-JAR Java file with the immutable tag commit ZIP."""
    commit = row["commit_sha"]
    url = f"https://codeload.github.com/{repository}/zip/{commit}"
    cache = ROOT / ".cache" / "upstream" / f"{commit}.zip"
    if cache.exists():
        data = cache.read_bytes()
    elif offline:
        raise FileNotFoundError(f"Git ZIP unavailable for offline check: {cache}")
    else:
        data = download(url)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(data)
    records = []
    with zipfile.ZipFile(io.BytesIO(data)) as git_zip, \
            zipfile.ZipFile(artifact_file(row, "sources")) as sources:
        # codeload ZIP starts with one repository-and-commit directory.
        git_files = {
            name.split("/", 1)[1]: name
            for name in git_zip.namelist() if "/" in name and not name.endswith("/")
        }
        for name in sorted(sources.namelist()):
            if not name.endswith(".java"):
                continue
            observed = sources.read(name)
            git_paths = [root + name for root in row.get("source_roots", ["src/main/java/"])]
            git_path = next((p for p in git_paths if p in git_files), git_paths[0])
            if git_path in git_files:
                original = git_zip.read(git_files[git_path])
                status = "byte_identical" if observed == original else "mismatch"
                if status == "mismatch" and observed.replace(b"\r\n", b"\n") == original.replace(b"\r\n", b"\n"):
                    status = "line_endings_only"
                record = {"source_path": name, "git_path": git_path,
                          "status": status, "source_sha256": digest(observed),
                          "git_sha256": digest(original)}
            else:
                record = {"source_path": name, "git_path": git_path,
                          "status": "missing_from_git", "source_sha256": digest(observed)}
            records.append(record)
    failures = [r for r in records if r["status"] in ("mismatch", "missing_from_git")]
    evidence = {
        "version": row["version"], "commit_sha": commit, "git_archive_url": url,
        "git_archive_sha256": digest(data), "source_jar_sha256": row["sources_sha256"],
        "compared_java_files": len(records), "all_sources_match": not failures,
        "records": records,
    }
    write_json(ROOT / "data/provenance" / f"git_source_match_{row['version']}.json", evidence)
    if failures:
        raise ValueError(f"Git/Maven source differences for {row['version']}: {failures[:5]}")
    return {k: v for k, v in evidence.items() if k != "records"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "config/versions.json")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--offline", action="store_true", help="Only verify checked-in cached Maven artifacts")
    parser.add_argument("--bootstrap", action="store_true", help="Fill initially absent checksum pins after collection")
    parser.add_argument("--verify-git", action="store_true", help="Compare oldest/latest source JARs to immutable Git commits")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    validate_selection(manifest)
    if not 1 <= args.workers <= 8:
        parser.error("--workers must be between 1 and 8")
    started = utc_now()
    artifacts = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(fetch_artifact, row, kind, args.offline, args.bootstrap): (row, kind)
                   for row in manifest["versions"] for kind in ("jar", "sources", "pom")}
        for future in as_completed(pending):
            result = future.result()
            artifacts.append(result)
            row, kind = pending[future]
            row[f"{kind}_sha256"] = result["sha256"]
            row[f"{kind}_maven_sha1"] = result["maven_sha1"]
    if args.bootstrap:
        write_json(args.manifest, manifest)
    inventories = []
    for row in manifest["versions"]:
        info = source_inventory(row)
        inventories.append({k: v for k, v in info.items() if k != "source_files"})
        write_json(ROOT / "data/provenance" / f"source_inventory_{row['version']}.json", info)
    git_checks = []
    if args.verify_git:
        for row in (manifest["versions"][0], manifest["versions"][-1]):
            git_checks.append(compare_git_sources(row, manifest["repository"], args.offline))
    previous_path = ROOT / "data/provenance/acquisition.json"
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    artifact_order = {v["version"]: i for i, v in enumerate(manifest["versions"])}
    artifacts.sort(key=lambda r: (artifact_order[r["version"]], r["kind"]))
    report = {
        "started_at_utc": started, "completed_at_utc": utc_now(),
        "mode": "offline_verify" if args.offline else "download_or_verify",
        "repository": manifest["repository"], "versions": len(manifest["versions"]),
        "artifact_count": len(artifacts), "total_artifact_bytes": sum(r["bytes"] for r in artifacts),
        "all_pinned_sha256_verified": True, "artifacts": artifacts,
        "source_inventories": inventories,
        "git_endpoint_source_checks": git_checks or previous.get("git_endpoint_source_checks", []),
    }
    write_json(previous_path, report)
    latest = inventories[-1]
    print(json.dumps({
        "versions": report["versions"], "verified_artifacts": len(artifacts),
        "total_mib": round(report["total_artifact_bytes"] / 1024**2, 3),
        "latest": latest["version"],
        "latest_source_java_files": latest["source_java_files"],
        "latest_java_nonblank_noncomment_lines": latest["java_nonblank_noncomment_lines"],
        "latest_source_owned_java_sloc": latest["source_owned_java_nonblank_noncomment_lines"],
        "git_endpoint_source_checks": report["git_endpoint_source_checks"],
    }, indent=2))


if __name__ == "__main__":
    main()

