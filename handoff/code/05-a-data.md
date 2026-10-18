# Commit 05 — Acquisition, preserved data and archive restoration

**Student A · 2026-10-20 · 75 complete files · 4 full code/configuration listings**

Source snapshot: `a8186f58fb22ffd7ebbe68964ded49006f12aef4`. Dates are planned work sessions; make the commit when you actually import and review this packet.

## What to understand

Trace an original JAR/source JAR/POM to its SHA-256 and release; restore one archive and explain the scope exclusions and 2,385 archived evidence files.

## Apply this packet

Set `HANDOFF_DIR` to your extracted student bundle and `TEACHER_REPO` to the teacher checkout. Pull the preceding commit first. Commands below use the `guava-study` layout explained in the main map.

```bash
git -C "$TEACHER_REPO" pull --ff-only origin guava-assignment
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/05-a-data" --target "$TEACHER_REPO" --subdir guava-study
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/05-a-data" --target "$TEACHER_REPO" --subdir guava-study --apply
cd "$TEACHER_REPO/guava-study"
```

For commit 01, create the shared branch as shown in the main map; its remote branch does not exist until the first push, so omit that first pull.

## Checks before the commit

Run these in the cumulative study directory after applying the packet. For packet 01, first create the Python environment and install the locked requirements as shown in the main map:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_archives.py' -v
python scripts/unpack_data.py --verify-only
python scripts/unpack_data.py
```

Stage and inspect only this packet, then use your own Git identity:

```bash
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/05-a-data" --target "$TEACHER_REPO" --subdir guava-study --apply --stage
git -C "$TEACHER_REPO" diff --cached --stat
git -C "$TEACHER_REPO" diff --cached
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/05-a-data" --target "$TEACHER_REPO" --subdir guava-study --check-staged
git -C "$TEACHER_REPO" commit -m 'import: add pinned artifacts and verified archive restoration (AI-assisted preparation)'
git -C "$TEACHER_REPO" push -u origin guava-assignment
```

Add a commit-message paragraph describing the checks you actually performed and anything you found. The import message identifies the prepared source; it does not claim you originally wrote every line.

## Further review checks

The following are useful for learning or final verification. Commands marked as writing evidence belong in a disposable copy, so the next packet still matches the frozen source. These are not additional canonical experiments.

Verify all 90 artifacts and both endpoint source matches.

```bash
python scripts/fetch_data.py --offline --verify-git
```

**Where:** disposable cumulative checkout, preserving immutable packet payloads. **Writes:** rewrites acquisition timestamps and provenance; use disposable cumulative checkout.

## Every file to push

All files below are present under this packet's `payload/` directory in the complete student download. Paths are relative to the study directory.

| File | Bytes | Content |
|---|---:|---|
| `archives/README.md` | 4,531 | documentation or tool provenance |
| `archives/manifest.json` | 483,823 | documentation or tool provenance |
| `archives/pilot.zip.b64` | 614,000 | encoded archive payload |
| `archives/upstream_git.zip` | 10,189,206 | binary archive payload |
| `archives/versions/guava-10.0.zip.b64` | 5,330,596 | encoded archive payload |
| `archives/versions/guava-11.0.zip.b64` | 5,920,192 | encoded archive payload |
| `archives/versions/guava-12.0.zip.b64` | 6,414,276 | encoded archive payload |
| `archives/versions/guava-13.0.1.zip.b64` | 6,770,064 | encoded archive payload |
| `archives/versions/guava-14.0.zip.b64` | 7,716,960 | encoded archive payload |
| `archives/versions/guava-15.0.zip.b64` | 7,818,900 | encoded archive payload |
| `archives/versions/guava-16.0.zip.b64` | 7,995,540 | encoded archive payload |
| `archives/versions/guava-17.0.zip.b64` | 8,075,532 | encoded archive payload |
| `archives/versions/guava-18.0.zip.b64` | 8,113,692 | encoded archive payload |
| `archives/versions/guava-19.0.zip.b64` | 8,310,192 | encoded archive payload |
| `archives/versions/guava-20.0.zip.b64` | 8,914,068 | encoded archive payload |
| `archives/versions/guava-21.0.zip.b64` | 9,187,612 | encoded archive payload |
| `archives/versions/guava-22.0.zip.b64` | 9,396,788 | encoded archive payload |
| `archives/versions/guava-23.0.zip.b64` | 9,566,268 | encoded archive payload |
| `archives/versions/guava-24.0.zip.b64` | 9,928,632 | encoded archive payload |
| `archives/versions/guava-25.0.zip.b64` | 10,005,028 | encoded archive payload |
| `archives/versions/guava-26.0.zip.b64` | 10,020,288 | encoded archive payload |
| `archives/versions/guava-27.0.zip.b64` | 10,039,684 | encoded archive payload |
| `archives/versions/guava-27.1.zip.b64` | 10,045,120 | encoded archive payload |
| `archives/versions/guava-28.0.zip.b64` | 10,053,696 | encoded archive payload |
| `archives/versions/guava-28.2.zip.b64` | 10,199,480 | encoded archive payload |
| `archives/versions/guava-29.0.zip.b64` | 10,233,192 | encoded archive payload |
| `archives/versions/guava-30.0.zip.b64` | 10,460,736 | encoded archive payload |
| `archives/versions/guava-31.0.zip.b64` | 11,047,292 | encoded archive payload |
| `archives/versions/guava-31.1.zip.b64` | 11,021,380 | encoded archive payload |
| `archives/versions/guava-32.0.0.zip.b64` | 11,259,884 | encoded archive payload |
| `archives/versions/guava-33.0.0.zip.b64` | 11,300,392 | encoded archive payload |
| `archives/versions/guava-33.4.0.zip.b64` | 11,459,416 | encoded archive payload |
| `archives/versions/guava-33.5.0.zip.b64` | 11,141,056 | encoded archive payload |
| `archives/versions/guava-33.7.2.zip.b64` | 11,330,300 | encoded archive payload |
| `data/graphs/extraction_summary.json` | 145,868 | recorded evidence |
| `data/graphs/feature_universe.json` | 34,872 | recorded evidence |
| `data/provenance/SHA256SUMS` | 9,054 | recorded evidence |
| `data/provenance/acquisition.json` | 63,195 | recorded evidence |
| `data/provenance/git_source_match_10.0.json` | 122,859 | recorded evidence |
| `data/provenance/git_source_match_33.7.2.json` | 230,045 | recorded evidence |
| `data/provenance/source_inventory_10.0.json` | 75,298 | recorded evidence |
| `data/provenance/source_inventory_11.0.json` | 84,314 | recorded evidence |
| `data/provenance/source_inventory_12.0.json` | 88,643 | recorded evidence |
| `data/provenance/source_inventory_13.0.1.json` | 90,786 | recorded evidence |
| `data/provenance/source_inventory_14.0.json` | 97,615 | recorded evidence |
| `data/provenance/source_inventory_15.0.json` | 104,734 | recorded evidence |
| `data/provenance/source_inventory_16.0.json` | 106,607 | recorded evidence |
| `data/provenance/source_inventory_17.0.json` | 107,303 | recorded evidence |
| `data/provenance/source_inventory_18.0.json` | 107,990 | recorded evidence |
| `data/provenance/source_inventory_19.0.json` | 108,018 | recorded evidence |
| `data/provenance/source_inventory_20.0.json` | 122,021 | recorded evidence |
| `data/provenance/source_inventory_21.0.json` | 123,655 | recorded evidence |
| `data/provenance/source_inventory_22.0.json` | 125,618 | recorded evidence |
| `data/provenance/source_inventory_23.0.json` | 128,365 | recorded evidence |
| `data/provenance/source_inventory_24.0.json` | 130,207 | recorded evidence |
| `data/provenance/source_inventory_25.0.json` | 131,380 | recorded evidence |
| `data/provenance/source_inventory_26.0.json` | 131,850 | recorded evidence |
| `data/provenance/source_inventory_27.0.json` | 132,242 | recorded evidence |
| `data/provenance/source_inventory_27.1.json` | 131,864 | recorded evidence |
| `data/provenance/source_inventory_28.0.json` | 131,377 | recorded evidence |
| `data/provenance/source_inventory_28.2.json` | 132,296 | recorded evidence |
| `data/provenance/source_inventory_29.0.json` | 133,447 | recorded evidence |
| `data/provenance/source_inventory_30.0.json` | 134,834 | recorded evidence |
| `data/provenance/source_inventory_31.0.json` | 142,593 | recorded evidence |
| `data/provenance/source_inventory_31.1.json` | 142,817 | recorded evidence |
| `data/provenance/source_inventory_32.0.0.json` | 143,739 | recorded evidence |
| `data/provenance/source_inventory_33.0.0.json` | 143,234 | recorded evidence |
| `data/provenance/source_inventory_33.4.0.json` | 145,307 | recorded evidence |
| `data/provenance/source_inventory_33.5.0.json` | 139,728 | recorded evidence |
| `data/provenance/source_inventory_33.7.2.json` | 140,627 | recorded evidence |
| `docs/data_acquisition.md` | 7,542 | documentation or tool provenance |
| `scripts/fetch_data.py` | 14,747 | Full code below |
| `scripts/package_data.py` | 8,432 | Full code below |
| `scripts/unpack_data.py` | 8,560 | Full code below |
| `tests/test_archives.py` | 14,207 | Full code below |

The machine-readable `packet.json` pins every file's SHA-256 and Git blob. Binary JAR/PDF/ZIP files and large evidence files are supplied as their exact original bytes in the payload, rather than as text pasted into this guide.

## Whole code

The following are complete files, with no omitted functions. Use the payload for copying so file bytes, line endings and original licences stay intact.

### scripts/fetch_data.py

SHA-256: `9c5ab82086db85e3274033329650cf1f26300637ff77f6be6d5dc6bac027fd91` · 14,747 bytes

<!-- FULL_SOURCE scripts/fetch_data.py 9c5ab82086db85e3274033329650cf1f26300637ff77f6be6d5dc6bac027fd91 -->
```python
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

from select_versions import validate_manifest

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
    inventory = json.loads((ROOT / "data/provenance/tag_inventory.json").read_text())
    validate_manifest(manifest, inventory)


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
    prefixes = tuple(row.get("source_prefixes", [row["source_prefix"]]))
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
                     if r["path"].startswith(prefixes)
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
        "source_ownership_prefixes": list(prefixes),
        "source_owned_java_files": sum(r["path"].startswith(prefixes) for r in records),
        "source_owned_java_nonblank_noncomment_lines": sum(r["nonblank_noncomment_lines"] for r in records if r["path"].startswith(prefixes)),
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
    cache = ROOT / "data" / "upstream_git" / f"{commit}.zip"
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
    checksum_lines = [f"{row[f'{kind}_sha256']}  {row[f'{kind}_path']}"
                      for row in manifest["versions"] for kind in ("jar", "sources", "pom")]
    checksum_path = ROOT / "data/provenance/SHA256SUMS"
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_path.write_text("\n".join(checksum_lines) + "\n")
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
        "study_revision": manifest.get("study_revision", 1),
        "selected_versions": [row["version"] for row in manifest["versions"]],
        "selected_unique_families": len({row.get("family", ".".join(row["version"].split(".")[:2]))
                                          for row in manifest["versions"]}),
        "selection_manifest_sha256": digest(args.manifest.read_bytes()),
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

```
<!-- END_FULL_SOURCE scripts/fetch_data.py -->

### scripts/package_data.py

SHA-256: `2844a2c5baf961dd3e9142fcc98f72ac28b76e792d78219bd11e15d39208d30f` · 8,432 bytes

<!-- FULL_SOURCE scripts/package_data.py 2844a2c5baf961dd3e9142fcc98f72ac28b76e792d78219bd11e15d39208d30f -->
```python
#!/usr/bin/env python3
"""Package complete raw and computed data without discarding any study evidence."""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PART_BYTES = 512 * 1024


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def store_base64(bundle: dict, content: bytes) -> dict:
    """Store the exact logical ZIP as canonical, unwrapped ASCII base64."""
    if len(content) != bundle['bytes'] or hashlib.sha256(content).hexdigest() != bundle['sha256']:
        raise ValueError('Logical ZIP identity differs before base64 storage')
    relative = PurePosixPath(bundle['path'])
    if relative.is_absolute() or '..' in relative.parts or relative.as_posix() != bundle['path'] or relative.parts[0] != 'archives' or relative.suffix != '.zip' or '\\' in bundle['path']:
        raise ValueError(f'Invalid logical ZIP path: {bundle["path"]}')
    physical = ROOT / (bundle['path'] + '.b64')
    physical.parent.mkdir(parents=True, exist_ok=True)
    encoded = base64.b64encode(content)
    encoded_sha = hashlib.sha256(encoded).hexdigest()
    if not physical.exists() or digest(physical) != encoded_sha:
        with tempfile.NamedTemporaryFile(prefix='encoded-stage-', dir=physical.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
        try:
            temporary.replace(physical)
        finally:
            temporary.unlink(missing_ok=True)
    record = {key: value for key, value in bundle.items()
              if key not in ('storage', 'part_size_bytes', 'parts', 'encoded_file')}
    record.update(storage='base64', encoded_file={
        'path': physical.relative_to(ROOT).as_posix(), 'bytes': len(encoded),
        'sha256': encoded_sha, 'text_encoding': 'ascii'})
    return record


def pack(name: str, paths: list[Path], *, multipart: bool | None = None) -> dict:
    relative_name = PurePosixPath(name)
    if relative_name.is_absolute() or '..' in relative_name.parts or str(relative_name) != name or '\\' in name:
        raise ValueError(f'Invalid bundle name: {name}')
    target = ROOT / 'archives' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    members = []
    seen = set()
    with tempfile.TemporaryDirectory(prefix='package-stage-', dir=target.parent) as directory:
        stage = Path(directory)
        temporary = stage / 'complete.zip'
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(paths):
                if not path.is_file() or '__pycache__' in path.parts or path.name.endswith('.part'):
                    continue
                relative = path.relative_to(ROOT).as_posix()
                if not path.resolve().is_relative_to(ROOT.resolve()) or path.is_symlink():
                    raise ValueError(f'Source is not an ordinary repository file: {path}')
                if relative in seen:
                    raise ValueError(f'Duplicate archive member: {relative}')
                seen.add(relative)
                content = path.read_bytes()
                info = zipfile.ZipInfo(relative, date_time=(2026, 10, 17, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
                members.append({'path': relative, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()})
        record = {'path': target.relative_to(ROOT).as_posix(), 'bytes': temporary.stat().st_size,
                  'sha256': digest(temporary), 'member_count': len(members), 'members': members}
        if multipart is False:
            record['storage'] = 'whole'
            if not target.exists() or digest(target) != record['sha256']:
                temporary.replace(target)
            return record
        if multipart is None:
            return store_base64(record, temporary.read_bytes())
        record.update({'storage': 'multipart', 'part_size_bytes': PART_BYTES, 'parts': []})
        with temporary.open('rb') as stream:
            index = 1
            while content := stream.read(PART_BYTES):
                physical = target.with_name(f'{target.name}.{record["sha256"]}.part{index:04d}')
                staged = stage / physical.name
                staged.write_bytes(content)
                part = {'index': index, 'path': physical.relative_to(ROOT).as_posix(),
                        'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
                record['parts'].append(part)
                index += 1
        # All parts are complete before publishing any. Hash-qualified paths
        # preserve the previous generation until the new manifest is installed.
        for part in record['parts']:
            physical = ROOT / part['path']
            staged = stage / physical.name
            if not physical.exists() or digest(physical) != part['sha256']:
                staged.replace(physical)
        return record


def obsolete_bundles(expected_names: set[str]) -> list[str]:
    """Catch superseded whole ZIPs, numbered parts, and unfinished old ZIPs."""
    return sorted(p.name for p in (ROOT / 'archives/versions').glob('guava-*.zip*')
                  if p.name.split('.zip', 1)[0] + '.zip' not in expected_names)


def remove_superseded_storage(bundles: list[dict]) -> None:
    """Run only after the replacement manifest has been atomically installed."""
    for bundle in bundles:
        if bundle['storage'] not in ('multipart', 'base64'):
            continue
        logical = ROOT / bundle['path']
        keep = {ROOT / part['path'] for part in bundle.get('parts', [])}
        for old in logical.parent.glob(logical.name + '.*part*'):
            if old.is_file() and old not in keep:
                old.unlink()
        if logical.exists():
            logical.unlink()


def main() -> None:
    manifest = json.loads((ROOT / 'config/versions.json').read_text())
    expected_names = {f"guava-{r['version']}.zip" for r in manifest['versions']}
    obsolete = obsolete_bundles(expected_names)
    if obsolete:
        raise ValueError(f'Archive superseded release bundles before packaging the revised cohort: {obsolete}')
    bundles = []
    for release in manifest['versions']:
        version = release['version']
        paths = []
        for prefix in ('data/raw', 'data/graphs', 'results/versions'):
            directory = ROOT / prefix / version
            if not directory.is_dir():
                raise FileNotFoundError(directory)
            paths.extend(directory.rglob('*'))
        record = pack(f'versions/guava-{version}.zip', paths)
        record['version'] = version
        bundles.append(record)
        print(version, record['member_count'], record['bytes'], flush=True)
    bundles.append(pack('pilot.zip', list((ROOT / 'results/pilot').rglob('*'))))
    git_archives = sorted((ROOT / 'data/upstream_git').glob('*.zip'))
    if len(git_archives) != 2:
        raise ValueError('Expected the first and last immutable Git source archives')
    bundles.append(pack('upstream_git.zip', git_archives, multipart=False))
    payload = {'schema_version': 3,
               'format': 'Logical standard ZIP/deflate; fixed timestamps; complete original file bytes; version and pilot ZIPs stored as canonical padded RFC4648 base64 ASCII without whitespace in .zip.b64 files',
               'purpose': 'All 90 pinned acquired artifacts and every finalized per-release computed file are preserved, including instructor raw output, unchanged scoped input JARs, supplementary member evidence, algorithm logs and directional MoJoFM details. The pilot bundle includes every k candidate assignment. Unfinished .part files are excluded. Unpack to restore the documented working hierarchy.',
               'version_manifest_sha256': digest(ROOT / 'config/versions.json'),
               'bundles': bundles}
    temporary_manifest = ROOT / 'archives/manifest.json.tmp'
    temporary_manifest.write_text(json.dumps(payload, indent=2) + '\n')
    temporary_manifest.replace(ROOT / 'archives/manifest.json')
    remove_superseded_storage(bundles)


if __name__ == '__main__':
    main()
```
<!-- END_FULL_SOURCE scripts/package_data.py -->

### scripts/unpack_data.py

SHA-256: `8d765df3fbf89a03e83ed7dedc7632727f1c86b122340538fba32453438c56d0` · 8,560 bytes

<!-- FULL_SOURCE scripts/unpack_data.py 8d765df3fbf89a03e83ed7dedc7632727f1c86b122340538fba32453438c56d0 -->
```python
#!/usr/bin/env python3
"""Verify and restore all preserved study data, or one selected release."""
from __future__ import annotations
import argparse
import base64
import binascii
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PART_BYTES = 512 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(name: str, allowed_roots: tuple[str, ...]) -> Path:
    """Reject traversal, alternate separators, and filesystem symlink escapes."""
    if not isinstance(name, str) or not name or '\\' in name or '\0' in name:
        raise ValueError(f'Invalid archive path: {name!r}')
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or relative.as_posix() != name or len(relative.parts) < 2 or relative.parts[0] not in allowed_roots:
        raise ValueError(f'Invalid archive path: {name}')
    target = ROOT
    for piece in relative.parts:
        target /= piece
        if target.is_symlink():
            raise ValueError(f'Symlink in archive path: {name}')
    if not target.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError(f'Archive path escapes repository: {name}')
    return target


def logical_zip_bytes(bundle: dict) -> bytes:
    logical = safe_path(bundle['path'], ('archives',))
    if logical.suffix != '.zip' or not re.fullmatch(r'[0-9a-f]{64}', bundle['sha256']):
        raise ValueError(f'Invalid logical ZIP record: {bundle["path"]}')
    storage = bundle.get('storage', 'whole')
    if storage == 'whole':
        if bundle.get('parts') or bundle.get('encoded_file'):
            raise ValueError('Whole ZIP record cannot also declare another physical storage')
        content = logical.read_bytes()
    elif storage == 'base64':
        encoded_file = bundle.get('encoded_file')
        if not isinstance(encoded_file, dict) or bundle.get('parts') or bundle.get('part_size_bytes'):
            raise ValueError('Base64 ZIP requires a single encoded file record')
        physical = safe_path(encoded_file['path'], ('archives',))
        expected_size = 4 * ((bundle['bytes'] + 2) // 3)
        if encoded_file['path'] != bundle['path'] + '.b64' or encoded_file.get('text_encoding') != 'ascii' or not re.fullmatch(r'[0-9a-f]{64}', encoded_file['sha256']):
            raise ValueError('Invalid encoded ZIP path or encoding record')
        encoded = physical.read_bytes()
        if encoded_file['bytes'] != expected_size or len(encoded) != expected_size or sha(encoded) != encoded_file['sha256']:
            raise ValueError(f'Encoded ZIP checksum/size mismatch: {encoded_file["path"]}')
        try:
            content = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as error:
            raise ValueError('Invalid strict base64 ZIP content') from error
        if base64.b64encode(content) != encoded:
            raise ValueError('Base64 ZIP content is not canonical padded RFC4648')
    elif storage == 'multipart':
        if bundle.get('encoded_file'):
            raise ValueError('Multipart ZIP cannot also declare an encoded file')
        if bundle.get('part_size_bytes') != PART_BYTES or not bundle.get('parts'):
            raise ValueError('Multipart ZIP requires ordered 512KiB parts')
        expected_count = (bundle['bytes'] + PART_BYTES - 1) // PART_BYTES
        if len(bundle['parts']) != expected_count:
            raise ValueError('Physical part count does not match logical ZIP size')
        pieces = []
        for index, part in enumerate(bundle['parts'], 1):
            physical = safe_path(part['path'], ('archives',))
            expected_path = f'{bundle["path"]}.{bundle["sha256"]}.part{index:04d}'
            if part['index'] != index or part['path'] != expected_path:
                raise ValueError(f'Physical part order/path mismatch: {part["path"]}')
            expected_bytes = min(PART_BYTES, bundle['bytes'] - (index - 1) * PART_BYTES)
            piece = physical.read_bytes()
            if part['bytes'] != expected_bytes or len(piece) != expected_bytes or sha(piece) != part['sha256']:
                raise ValueError(f'Physical part checksum/size mismatch: {part["path"]}')
            pieces.append(piece)
        content = b''.join(pieces)
    else:
        raise ValueError(f'Unknown archive storage: {storage}')
    if len(content) != bundle['bytes'] or sha(content) != bundle['sha256']:
        raise ValueError(f'Logical ZIP checksum/size mismatch: {bundle["path"]}')
    return content


def checked_members(bundle: dict):
    """Validate the complete ZIP inventory; yield verified file bytes only."""
    expected = {member['path']: member for member in bundle['members']}
    if len(expected) != len(bundle['members']) or bundle['member_count'] != len(expected):
        raise ValueError(f'Duplicate/mismatched manifest members: {bundle["path"]}')
    for name in expected:
        safe_path(name, ('data', 'results'))
    with zipfile.ZipFile(io.BytesIO(logical_zip_bytes(bundle))) as archive:
        if len(archive.namelist()) != len(expected) or set(archive.namelist()) != set(expected):
            raise ValueError(f'Archive member set mismatch: {bundle["path"]}')
        for name, record in expected.items():
            info = archive.getinfo(name)
            if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError(f'Archive member is not a regular file: {name}')
            content = archive.read(name)
            if len(content) != record['bytes'] or sha(content) != record['sha256']:
                raise ValueError(f'Member checksum mismatch: {name}')
            yield name, content


def restore_bundles(bundles: list[dict], *, verify_only: bool = False) -> int:
    """Preflight every selected bundle and destination before restoring anything."""
    if len({bundle['path'] for bundle in bundles}) != len(bundles):
        raise ValueError('Duplicate logical archive paths')
    seen = set()
    for bundle in bundles:
        for name, content in checked_members(bundle):
            if name in seen:
                raise ValueError(f'Member occurs in multiple bundles: {name}')
            seen.add(name)
            target = safe_path(name, ('data', 'results'))
            if not verify_only and target.exists() and (not target.is_file() or target.read_bytes() != content):
                raise ValueError(f'Existing file differs; move it aside before restoring: {target}')
    if not verify_only:
        for bundle in bundles:
            for name, content in checked_members(bundle):
                target = safe_path(name, ('data', 'results'))
                if target.exists():
                    if not target.is_file() or target.read_bytes() != content:
                        raise ValueError(f'Existing file differs; move it aside before restoring: {target}')
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                # Exclusive creation preserves local files even if another
                # process creates one after the preflight check.
                with target.open('xb') as stream:
                    stream.write(content)
    return len(seen)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', help='Restore only this selected release (all by default)')
    parser.add_argument('--verify-only', action='store_true', help='Check archives and member hashes without writing')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'archives/manifest.json').read_text())
    if manifest.get('schema_version', 1) not in (1, 2, 3):
        raise ValueError('Unsupported archive manifest schema')
    if manifest.get('schema_version') == 2 and manifest.get('physical_part_size_bytes') != PART_BYTES:
        raise ValueError('Unexpected multipart archive size policy')
    bundles = [b for b in manifest['bundles'] if not args.version or b.get('version') == args.version]
    if not bundles:
        parser.error('Version is not in the preserved dataset')
    files = restore_bundles(bundles, verify_only=args.verify_only)
    for bundle in bundles:
        print(f'{bundle["path"]}: verified {bundle["member_count"]} files', flush=True)
    print(f'Verified {files} files in {len(bundles)} archives' + ('; no files written' if args.verify_only else '; working hierarchy restored'))


if __name__ == '__main__':
    main()
```
<!-- END_FULL_SOURCE scripts/unpack_data.py -->

### tests/test_archives.py

SHA-256: `c97265cfb677836f21cd03afe6c08f2851e6bb357b5a7ed10433887b21510731` · 14,207 bytes

<!-- FULL_SOURCE tests/test_archives.py c97265cfb677836f21cd03afe6c08f2851e6bb357b5a7ed10433887b21510731 -->
```python
"""Round trips and failure boundaries for encoded and legacy evidence archives."""
import base64
from copy import deepcopy
import hashlib
import importlib.util
import io
from pathlib import Path
import random
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile


REPOSITORY = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name, REPOSITORY / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


packager = script('package_data')
unpacker = script('unpack_data')


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.patches = [patch.object(module, 'ROOT', self.root) for module in (packager, unpacker)]
        for context in self.patches:
            context.start()
            self.addCleanup(context.stop)
        self.contents = {
            'data/raw/demo/a.bin': random.Random(484).randbytes(packager.PART_BYTES * 2 + 137),
            'results/versions/demo/b.txt': b'Complete evidence; preserved newlines.\r\n',
        }
        for name, content in self.contents.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

    def bundle(self, multipart=True):
        return packager.pack('versions/guava-10.0.zip', [self.root / n for n in self.contents], multipart=multipart)

    def clear_sources(self):
        for name in ('data', 'results'):
            if (self.root / name).exists():
                shutil.rmtree(self.root / name)

    def assert_no_restoration(self):
        self.assertFalse((self.root / 'data').exists())
        self.assertFalse((self.root / 'results').exists())

    def test_deterministic_multipart_round_trip_and_standard_zip_bytes(self):
        bundle = self.bundle()
        self.assertEqual(bundle, self.bundle())
        self.assertGreaterEqual(len(bundle['parts']), 3)
        self.assertTrue(all(p['bytes'] == 512 * 1024 for p in bundle['parts'][:-1]))
        self.assertFalse((self.root / bundle['path']).exists())
        content = unpacker.logical_zip_bytes(bundle)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            self.assertEqual({n: archive.read(n) for n in archive.namelist()}, self.contents)
        self.clear_sources()
        self.assertEqual(unpacker.restore_bundles([bundle]), 2)

        self.assertEqual({n: (self.root / n).read_bytes() for n in self.contents}, self.contents)
        self.assertEqual(unpacker.restore_bundles([bundle]), 2)

    def test_default_base64_round_trip_preserves_exact_standard_zip(self):
        bundle = self.bundle(multipart=None)
        self.assertEqual(bundle['storage'], 'base64')
        self.assertEqual(bundle, self.bundle(multipart=None))
        encoded = bundle['encoded_file']
        stored = (self.root / encoded['path']).read_bytes()
        self.assertEqual(encoded['path'], bundle['path'] + '.b64')
        self.assertEqual(encoded['text_encoding'], 'ascii')
        self.assertEqual(stored.decode('ascii').encode('utf-8'), stored)
        self.assertEqual(hashlib.sha256(stored).hexdigest(), encoded['sha256'])
        self.assertEqual(encoded['bytes'], 4 * ((bundle['bytes'] + 2) // 3))
        legacy = self.bundle(multipart=True)
        content = unpacker.logical_zip_bytes(bundle)
        self.assertEqual(base64.b64decode(stored, validate=True), content)
        self.assertEqual(content, unpacker.logical_zip_bytes(legacy))
        self.assertFalse((self.root / bundle['path']).exists())
        self.clear_sources()
        self.assertEqual(unpacker.restore_bundles([bundle]), 2)
        self.assertEqual({n: (self.root / n).read_bytes() for n in self.contents}, self.contents)
        self.assertEqual(unpacker.restore_bundles([bundle]), 2)

    def test_missing_encoded_file_does_not_restore_any_member(self):
        bundle = self.bundle(multipart=None)
        (self.root / bundle['encoded_file']['path']).unlink()
        self.clear_sources()
        with self.assertRaises(FileNotFoundError):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_encoded_checksum_detects_corrupted_text_before_restoration(self):
        bundle = self.bundle(multipart=None)
        physical = self.root / bundle['encoded_file']['path']
        encoded = bytearray(physical.read_bytes())
        encoded[0] = ord('A') if encoded[0] != ord('A') else ord('B')
        physical.write_bytes(encoded)
        self.clear_sources()
        with self.assertRaisesRegex(ValueError, 'Encoded ZIP checksum'):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_decoded_zip_hash_is_checked_when_encoded_hash_matches(self):
        bundle = self.bundle(multipart=None)
        physical = self.root / bundle['encoded_file']['path']
        content = bytearray(unpacker.logical_zip_bytes(bundle))
        content[-1] ^= 1
        encoded = base64.b64encode(content)
        physical.write_bytes(encoded)
        bundle['encoded_file']['sha256'] = hashlib.sha256(encoded).hexdigest()
        self.clear_sources()
        with self.assertRaisesRegex(ValueError, 'Logical ZIP checksum'):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_strict_base64_rejects_whitespace_and_noncanonical_padding(self):
        original = packager.pack('versions/guava-empty.zip', [])
        physical = self.root / original['encoded_file']['path']
        original_encoded = physical.read_bytes()
        self.assertTrue(original_encoded.endswith(b'=='))
        self.clear_sources()
        alphabet = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        for mutation, message in [('whitespace', 'strict base64'), ('padding_bits', 'not canonical')]:
            with self.subTest(mutation=mutation):
                bundle = deepcopy(original)
                encoded = bytearray(original_encoded)
                if mutation == 'whitespace':
                    encoded[0] = ord(' ')
                else:
                    encoded[-3] = alphabet[alphabet.index(encoded[-3]) + 1]
                physical.write_bytes(encoded)
                bundle['encoded_file']['sha256'] = hashlib.sha256(encoded).hexdigest()
                with self.assertRaisesRegex(ValueError, message):
                    unpacker.restore_bundles([bundle])
                self.assert_no_restoration()

    def test_unsafe_encoded_file_paths_and_symlinks_are_rejected(self):
        original = self.bundle(multipart=None)
        self.clear_sources()
        for name in ('archives/../outside.b64', '/tmp/outside.b64', 'archives/wrong.zip.b64'):
            with self.subTest(path=name):
                bundle = deepcopy(original)
                bundle['encoded_file']['path'] = name
                with self.assertRaises(ValueError):
                    unpacker.restore_bundles([bundle])
                self.assert_no_restoration()
        physical = self.root / original['encoded_file']['path']
        elsewhere = self.root / 'elsewhere.b64'
        physical.replace(elsewhere)
        physical.symlink_to(elsewhere)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            unpacker.restore_bundles([original])
        self.assert_no_restoration()

    def test_base64_cleanup_preserves_new_storage_and_removes_old_parts(self):
        old = self.bundle(multipart=True)
        new = self.bundle(multipart=None)
        self.assertEqual(old['sha256'], new['sha256'])
        self.assertEqual(unpacker.logical_zip_bytes(old), unpacker.logical_zip_bytes(new))
        packager.remove_superseded_storage([new])
        self.assertTrue((self.root / new['encoded_file']['path']).is_file())
        self.assertTrue(all(not (self.root / p['path']).exists() for p in old['parts']))
        self.assertEqual(unpacker.restore_bundles([new], verify_only=True), 2)

    def test_legacy_whole_zip_and_unchanged_whole_file(self):
        bundle = self.bundle(multipart=False)
        original = (self.root / bundle['path']).stat().st_mtime_ns
        self.assertEqual(bundle, self.bundle(multipart=False))
        self.assertEqual((self.root / bundle['path']).stat().st_mtime_ns, original)
        del bundle['storage']
        self.clear_sources()
        self.assertEqual(unpacker.restore_bundles([bundle]), 2)
        self.assertEqual((self.root / next(iter(self.contents))).read_bytes(), next(iter(self.contents.values())))

    def test_missing_part_does_not_restore_any_file(self):
        bundle = self.bundle()
        (self.root / bundle['parts'][-1]['path']).unlink()
        self.clear_sources()
        with self.assertRaises(FileNotFoundError):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_corrupted_part_does_not_restore_any_file(self):
        bundle = self.bundle()
        path = self.root / bundle['parts'][-1]['path']
        content = bytearray(path.read_bytes())
        content[-1] ^= 1
        path.write_bytes(content)
        self.clear_sources()
        with self.assertRaisesRegex(ValueError, 'Physical part checksum'):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_reordered_parts_and_incorrect_declared_size_are_rejected(self):
        original = self.bundle()
        self.clear_sources()
        for mutation in ('order', 'size'):
            with self.subTest(mutation=mutation):
                bundle = deepcopy(original)
                if mutation == 'order':
                    bundle['parts'].reverse()
                else:
                    bundle['parts'][0]['bytes'] -= 1
                with self.assertRaises(ValueError):
                    unpacker.restore_bundles([bundle])
                self.assert_no_restoration()

    def test_whole_zip_hash_is_checked_even_when_part_hashes_match(self):
        bundle = self.bundle()
        part = bundle['parts'][-1]
        path = self.root / part['path']
        content = bytearray(path.read_bytes())
        content[-1] ^= 1
        path.write_bytes(content)
        part['sha256'] = hashlib.sha256(content).hexdigest()
        self.clear_sources()
        with self.assertRaisesRegex(ValueError, 'Logical ZIP checksum'):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_late_member_corruption_is_detected_before_earlier_member_write(self):
        bundle = self.bundle()
        bundle['members'][-1]['sha256'] = '0' * 64
        self.clear_sources()
        with self.assertRaisesRegex(ValueError, 'Member checksum'):
            unpacker.restore_bundles([bundle])
        self.assert_no_restoration()

    def test_differing_local_file_blocks_all_restoration(self):
        bundle = self.bundle()
        self.clear_sources()
        conflict = self.root / 'results/versions/demo/b.txt'
        conflict.parent.mkdir(parents=True)
        conflict.write_bytes(b'My local changes')
        with self.assertRaisesRegex(ValueError, 'Existing file differs'):
            unpacker.restore_bundles([bundle])
        self.assertFalse((self.root / 'data').exists())
        self.assertEqual(conflict.read_bytes(), b'My local changes')

    def test_verify_only_writes_nothing(self):
        bundle = self.bundle()
        self.clear_sources()
        self.assertEqual(unpacker.restore_bundles([bundle], verify_only=True), 2)
        self.assert_no_restoration()

    def test_unsafe_logical_part_and_member_paths_are_rejected(self):
        original = self.bundle()
        self.clear_sources()
        for kind, value in [('logical', 'archives/../outside.zip'),
                            ('part', '/tmp/outside.part'),
                            ('member', 'data/../../outside'),
                            ('member', 'data\\outside'),
                            ('member', 'data//outside'),
                            ('member', 'data')]:
            with self.subTest(kind=kind, value=value):
                bundle = deepcopy(original)
                if kind == 'logical':
                    bundle['path'] = value
                elif kind == 'part':
                    bundle['parts'][0]['path'] = value
                else:
                    bundle['members'][0]['path'] = value
                with self.assertRaises(ValueError):
                    unpacker.restore_bundles([bundle])
                self.assert_no_restoration()

    def test_symlink_destination_is_rejected(self):
        bundle = self.bundle()
        self.clear_sources()
        (self.root / 'elsewhere').mkdir()
        (self.root / 'data').symlink_to(self.root / 'elsewhere', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            unpacker.restore_bundles([bundle])
        self.assertEqual(list((self.root / 'elsewhere').iterdir()), [])

    def test_obsolete_detection_includes_numbered_parts(self):
        self.bundle()
        obsolete = self.root / ('archives/versions/guava-9.0.zip.' + 'a' * 64 + '.part0001')
        obsolete.write_bytes(b'old generation')
        encoded = self.root / 'archives/versions/guava-9.1.zip.b64'
        encoded.write_bytes(b'old encoded release')
        self.assertEqual(packager.obsolete_bundles({'guava-10.0.zip'}), sorted([obsolete.name, encoded.name]))

    def test_old_generation_survives_until_manifest_switch(self):
        old = self.bundle()
        first = self.root / next(iter(self.contents))
        first.write_bytes(b'New evidence')
        new = self.bundle()
        self.assertNotEqual(old['sha256'], new['sha256'])
        self.assertEqual(unpacker.restore_bundles([old], verify_only=True), 2)
        packager.remove_superseded_storage([new])
        self.assertTrue(all((self.root / p['path']).is_file() for p in new['parts']))
        self.assertTrue(all(not (self.root / p['path']).exists() for p in old['parts']))


if __name__ == '__main__':
    unittest.main()
```
<!-- END_FULL_SOURCE tests/test_archives.py -->
