#!/usr/bin/env python3
"""Build full-code guides and complete student packets from a pinned Git snapshot.

This is a packaging tool, independent of the scientific analysis. It uses only
the Python standard library, reads immutable Git objects, and never commits,
pushes, downloads dependencies, or changes the source study.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import html
import io
import json
from pathlib import Path
import re
import shlex
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoff"
ZIP_DATE = (2026, 10, 18, 0, 0, 0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def read_source(manifest: dict) -> dict[str, bytes]:
    """Verify coverage and read each original blob, including binary evidence."""
    commit = manifest["source_commit"]
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", commit + "^{commit}"],
                      capture_output=True).returncode:
        raise ValueError(
            "Pinned source commit is missing. Fetch it explicitly, then retry:\n"
            f"git fetch --depth 1 origin {commit}")
    tree = git("rev-parse", commit + "^{tree}").decode().strip()
    if tree != manifest["source_tree"]:
        raise ValueError("Pinned source tree does not match the handoff manifest")
    tracked = {}
    for raw in git("ls-tree", "-rz", "--full-tree", commit).split(b"\0"):
        if not raw:
            continue
        head, name = raw.split(b"\t", 1)
        mode, kind, blob = head.decode().split()
        if kind != "blob":
            raise ValueError(f"Unsupported source entry: {name!r}")
        tracked[name.decode()] = (mode, blob)
    assigned = [f["path"] for f in manifest["files"]]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(tracked):
        raise ValueError("Every source file must be assigned exactly once")
    packet_paths = [p for packet in manifest["packets"] for p in packet["paths"]]
    if Counter(packet_paths) != Counter(assigned):
        raise ValueError("Packet paths do not cover the exact source file set")
    by_packet = {packet["id"]: packet for packet in manifest["packets"]}
    payload = {}
    process = subprocess.Popen(["git", "-C", str(ROOT), "cat-file", "--batch"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        assert process.stdin is not None and process.stdout is not None
        for item in manifest["files"]:
            path = item["path"]
            packet = by_packet[item["packet"]]
            if path not in packet["paths"] or item["owner"] != packet["owner"]:
                raise ValueError(f"Ownership mismatch: {path}")
            if tracked[path] != (item["mode"], item["git_blob_sha1"]):
                raise ValueError(f"Git object mismatch: {path}")
            process.stdin.write((item["git_blob_sha1"] + "\n").encode())
            process.stdin.flush()
            blob, kind, size = process.stdout.readline().decode().strip().split()
            if blob != item["git_blob_sha1"] or kind != "blob":
                raise ValueError(f"Unexpected Git object: {path}")
            data = process.stdout.read(int(size))
            if process.stdout.read(1) != b"\n":
                raise ValueError("Git batch framing error")
            if len(data) != item["bytes"] or sha256(data) != item["sha256"]:
                raise ValueError(f"Source SHA-256/length mismatch: {path}")
            payload[path] = data
    finally:
        if process.stdin:
            process.stdin.close()
        if process.stdout:
            process.stdout.close()
        process.wait()
    if process.returncode:
        raise ValueError("Git object reader failed")
    if len(payload) != manifest["source_file_count"]:
        raise ValueError("Source file count does not match the manifest")
    if sum(map(len, payload.values())) != manifest["source_bytes"]:
        raise ValueError("Source byte count does not match the manifest")
    return payload


def code_language(path: str) -> str:
    return {".py": "python", ".java": "java", ".json": "json"}.get(Path(path).suffix, "text")


def packet_records(manifest: dict, packet: dict) -> list[dict]:
    return [f for f in manifest["files"] if f["packet"] == packet["id"]]


def packet_metadata(manifest: dict, packet: dict) -> dict:
    keys = ("path", "bytes", "sha256", "git_blob_sha1", "mode")
    def compact(record):
        return {k: record[k] for k in keys}
    return {
        "schema": 1, "source_commit": manifest["source_commit"],
        "id": packet["id"], "number": packet["number"], "owner": packet["owner"],
        "title": packet["title"], "commit_message": packet["commit_message"],
        "files": [compact(f) for f in packet_records(manifest, packet)],
        "prerequisites": [compact(f) for f in manifest["files"]
                          if int(f["packet"]) < packet["number"]],
    }


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def packet_guide(manifest: dict, packet: dict, payload: dict[str, bytes]) -> str:
    records = packet_records(manifest, packet)
    listed = [f for f in records if f["include_in_full_code_listing"]]
    lines = [f"# Commit {packet['id']} — {packet['title']}", "",
             f"**Student {packet['owner']} · {packet['suggested_date']} · "
             f"{len(records)} complete files · {len(listed)} full code/configuration listings**", "",
             f"Source snapshot: `{manifest['source_commit']}`. Dates are planned work sessions; "
             "make the commit when you actually import and review this packet.", "",
             "## What to understand", "", packet["review_task"], "",
             "## Apply this packet", "",
             "Set `HANDOFF_DIR` to your extracted student bundle and `TEACHER_REPO` to the "
             "teacher checkout. Pull the preceding commit first. Commands below use the "
             "`guava-study` layout explained in the main map.", "", "```bash",
             'git -C "$TEACHER_REPO" pull --ff-only origin guava-assignment',
             f'python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/{packet["slug"]}" --target "$TEACHER_REPO" --subdir guava-study',
             f'python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/{packet["slug"]}" --target "$TEACHER_REPO" --subdir guava-study --apply',
             'cd "$TEACHER_REPO/guava-study"', "```", "",
             "For commit 01, create the shared branch as shown in the main map; its remote "
             "branch does not exist until the first push, so omit that first pull.", "",
             "## Checks before the commit", "",
             "Run these in the cumulative study directory after applying the packet. For packet "
             "01, first create the Python environment and install the locked requirements as "
             "shown in the main map:", "", "```bash"]
    for check in packet["stage_checks"]:
        if check["during_import"]:
            lines.append(check["command"])
    lines += ["```", "", "Stage and inspect only this packet, then use your own Git identity:", "", "```bash",
              f'python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/{packet["slug"]}" --target "$TEACHER_REPO" --subdir guava-study --apply --stage',
              'git -C "$TEACHER_REPO" diff --cached --stat',
              'git -C "$TEACHER_REPO" diff --cached',
              f'python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/{packet["slug"]}" --target "$TEACHER_REPO" --subdir guava-study --check-staged',
              f'git -C "$TEACHER_REPO" commit -m {shlex.quote(packet["commit_message"])}',
              'git -C "$TEACHER_REPO" push -u origin guava-assignment', "```", "",
              "Add a commit-message paragraph describing the checks you actually performed "
              "and anything you found. The import message identifies the prepared source; "
              "it does not claim you originally wrote every line.", ""]
    later = [c for c in packet["stage_checks"] if not c["during_import"]]
    if later:
        lines += ["## Further review checks", "",
                  "The following are useful for learning or final verification. Commands marked "
                  "as writing evidence belong in a disposable copy, so the next packet still "
                  "matches the frozen source. These are not additional canonical experiments.", ""]
        for check in later:
            lines += [check["purpose"] + ".", "", "```bash", check["command"], "```", "",
                      f"**Where:** {check['execution_context']}. **Writes:** {check['writes']}.", ""]
    lines += ["## Every file to push", "",
              "All files below are present under this packet's `payload/` directory in the "
              "complete student download. Paths are relative to the study directory.", "",
              "| File | Bytes | Content |", "|---|---:|---|"]
    for f in records:
        kind = "Full code below" if f["include_in_full_code_listing"] else f["category"].replace("_", " ")
        lines.append(f"| `{f['path']}` | {f['bytes']:,} | {kind} |")
    lines += ["", "The machine-readable `packet.json` pins every file's SHA-256 and Git blob. "
              "Binary JAR/PDF/ZIP files and large evidence files are supplied as their exact "
              "original bytes in the payload, rather than as text pasted into this guide.", "",
              "## Whole code", "",
              "The following are complete files, with no omitted functions. Use the payload "
              "for copying so file bytes, line endings and original licences stay intact.", ""]
    if packet["id"] == "03":
        lines += ["The official ACDC Java files below retain their upstream authorship. "
                  "The instructor supplied DependencyExtractor as a compiled JAR; that "
                  "original JAR is included in full, and unavailable instructor source is "
                  "not invented. `java/DependencyExtractor.java` is our supplemental extractor.", ""]
    for f in listed:
        data = payload[f["path"]].decode("utf-8")
        fence = "`" * max(3, 1 + max((len(x) for x in re.findall(r"`+", data)), default=0))
        lines += [f"### {f['path']}", "", f"SHA-256: `{f['sha256']}` · {f['bytes']:,} bytes", "",
                  f"<!-- FULL_SOURCE {f['path']} {f['sha256']} -->",
                  fence + code_language(f["path"]), data + ("" if data.endswith("\n") else "\n") + fence,
                  f"<!-- END_FULL_SOURCE {f['path']} -->", ""]
    return "\n".join(lines).rstrip() + "\n"


def html_guide(manifest: dict, payload: dict[str, bytes]) -> str:
    esc = html.escape
    body = ["<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">",
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            "<title>Guava assignment — complete code and two-person commit map</title>",
            """<style>
body{font:17px/1.55 Georgia,serif;color:#171717;background:#fff;margin:0 auto;padding:36px 24px;max-width:1100px}
h1,h2,h3,summary,nav,button{font-family:system-ui,sans-serif}h1{line-height:1.18;font-size:2.1rem}h2{margin-top:2.8rem;line-height:1.25}
a{color:inherit;text-decoration:underline;text-underline-offset:3px}p{max-width:85ch}nav{padding:18px;background:#f4f4f4}
table{border-collapse:collapse;width:100%;font:14px/1.45 system-ui,sans-serif}th,td{padding:9px;text-align:left;border-bottom:1px solid #ddd;vertical-align:top}
code{font-family:ui-monospace,Consolas,monospace;font-size:.88em}pre{overflow:auto;padding:18px;background:#f7f7f7;border:1px solid #ddd;line-height:1.5;tab-size:4}
pre code{font-size:13px}details{margin:18px 0;border-top:1px solid #ccc;padding-top:12px}summary{cursor:pointer;font-weight:600;overflow-wrap:anywhere}
.meta{font:13px/1.5 system-ui,sans-serif;color:#444;overflow-wrap:anywhere}.muted{color:#444}button{background:white;border:1px solid #777;padding:8px 12px;margin:8px 8px 8px 0;color:#171717;cursor:pointer}
@media print{body{max-width:none;padding:0;font-size:11pt}nav,button{display:none}details>*{display:block!important}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:8pt}h2{break-before:page}summary{break-after:avoid}a{text-decoration:none}}
</style></head><body>""",
            "<h1>Guava assignment<br>Complete code and commit map</h1>",
            f"<p>Student A: <strong>{esc(manifest['owners']['A'])}</strong>. "
            f"Student B: <strong>{esc(manifest['owners']['B'])}</strong>. "
            "Six ordered imports each, planned for 18–23 October 2026.</p>",
            f"<p>This guide contains all <strong>{manifest['code_listing_files']} code and configuration files</strong> "
            "in full. The complete student ZIPs also contain every assigned data, report, tool and "
            "evidence file. They are ready to copy through the provided helper.</p>",
            f"<p class=\"meta\">Source snapshot: {esc(manifest['source_commit'])}. "
            f"All {manifest['source_file_count']} study files are assigned exactly once. "
            "The new outer guide is separate from the frozen study payload.</p>",
            "<p>Use <strong>COMMIT_MAP.md</strong> for setup, branch commands and the final checklist. "
            "Each packet has its own README and exact payload. The import commits identify "
            "AI-assisted preparation; record your actual review and use your own identity and date.</p>",
            '<button type="button" onclick="document.querySelectorAll(\'details\').forEach(x=>x.open=true)">Expand all code</button>',
            '<button type="button" onclick="document.querySelectorAll(\'details\').forEach(x=>x.open=false)">Collapse all code</button>',
            "<nav aria-label=\"Commit map\"><table><thead><tr><th>Commit</th><th>Owner</th><th>Date</th><th>Work</th><th>Files</th></tr></thead><tbody>"]
    for p in manifest["packets"]:
        body.append(f'<tr><td><a href="#commit-{p["id"]}">{p["id"]}</a></td>'
                    f'<td>{p["owner"]}</td><td>{esc(p["suggested_date"])}</td>'
                    f'<td>{esc(p["title"])}</td><td>{p["file_count"]}</td></tr>')
    body.append("</tbody></table></nav>")
    for p in manifest["packets"]:
        body += [f'<section id="commit-{p["id"]}"><h2>{p["id"]} · Student {p["owner"]}<br>{esc(p["title"])}</h2>',
                 f'<p>{esc(p["review_task"])}</p>',
                 f'<p><strong>Commit message:</strong> <code>{esc(p["commit_message"])}</code></p>',
                 '<p><strong>Checks during import:</strong></p><pre><code>' + esc("\n".join(c["command"] for c in p["stage_checks"] if c["during_import"])) + '</code></pre>',
                 '<p class="muted">The complete file inventory and the commands for this packet '
                 f'are in <code>code/{p["slug"]}.md</code>. Every source block below contains the whole file.</p>']
        for f in packet_records(manifest, p):
            if not f["include_in_full_code_listing"]:
                continue
            body += [f'<details><summary>{esc(f["path"])} · {f["bytes"]:,} bytes</summary>',
                     f'<p class="meta">SHA-256: {f["sha256"]}</p>',
                     f'<pre><code data-source-path="{esc(f["path"], quote=True)}">' +
                     esc(payload[f["path"]].decode("utf-8")) + '</code></pre></details>']
        body.append("</section>")
    body += ["<h2>What is inside the downloads?</h2>",
             "<p>Student A's ZIP has packets 01, 03, 05, 07, 09 and 11. Student B's ZIP has "
             "02, 04, 06, 08, 10 and 12. Each includes this complete code guide for reciprocal "
             "review, the current map, the manifest and the helper. Only the assigned packet "
             "payloads are copied into the teacher repository.</p>",
             "<p>The largest files are the preserved 30-version dataset in packet 05. The instructor "
             "extractor is supplied as its original compiled JAR; all available project and ACDC "
             "source files are printed above. The preserved receipts identify the original commits "
             "they checked. Run and record your own final checks on your imported checkout.</p>",
             "</body></html>"]
    return "\n".join(body) + "\n"


def write_zip(path: Path, entries: dict[str, bytes]) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    temporary.replace(path)
    return {"file": path.name, "bytes": path.stat().st_size,
            "sha256": sha256(path.read_bytes()), "members": len(entries),
            "uncompressed_bytes": sum(map(len, entries.values()))}


def inventory_csv(manifest: dict) -> bytes:
    stream = io.StringIO(newline="")
    columns = ["packet", "owner", "path", "bytes", "mode", "sha256", "git_blob_sha1", "category", "include_in_full_code_listing"]
    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(manifest["files"])
    return stream.getvalue().encode()


def build(manifest: dict, payload: dict[str, bytes], destination: Path, guides_only: bool) -> dict:
    code_dir = HANDOFF / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    guides = {}
    for packet in manifest["packets"]:
        name = packet["slug"] + ".md"
        guides[name] = packet_guide(manifest, packet, payload).encode()
        (code_dir / name).write_bytes(guides[name])
    complete_html = html_guide(manifest, payload).encode()
    (HANDOFF / "full_code.html").write_bytes(complete_html)
    inventory = inventory_csv(manifest)
    (HANDOFF / "file_inventory.csv").write_bytes(inventory)
    result = {"schema": 1, "source_commit": manifest["source_commit"],
              "source_tree": manifest["source_tree"], "source_files": len(payload),
              "source_bytes": sum(map(len, payload.values())),
              "code_listing_files": manifest["code_listing_files"],
              "code_listing_bytes": manifest["code_listing_bytes"], "downloads": []}
    if guides_only:
        return result
    helper = (HANDOFF / "apply_packet.py").read_bytes()
    map_text = (ROOT / "docs/commit_roadmap.md").read_text()
    # The download manifest contains ZIP hashes, so it cannot be embedded in the
    # ZIPs it hashes. Point that one offline-guide link to the published record.
    map_text = map_text.replace("../handoff/download_manifest.json",
                                manifest["source_repository"] + "/blob/main/handoff/download_manifest.json")
    map_text = map_text.replace("../handoff/", "")
    common = {"COMMIT_MAP.md": map_text.encode(), "full_code.html": complete_html,
              "manifest.json": (HANDOFF / "manifest.json").read_bytes(),
              "file_inventory.csv": inventory, "apply_packet.py": helper}
    common.update({"code/" + name: data for name, data in guides.items()})
    packet_entries = {}
    for packet in manifest["packets"]:
        slug = packet["slug"]
        entries = {"packet.json": json_bytes(packet_metadata(manifest, packet)),
                   "README.md": guides[slug + ".md"]}
        entries.update({"payload/" + p: payload[p] for p in packet["paths"]})
        packet_entries[slug] = entries
        # Standalone packet ZIPs contain a runnable helper and their complete metadata.
        standalone = {slug + "/" + name: data for name, data in entries.items()}
        standalone[slug + "/apply_packet.py"] = helper
        row = write_zip(destination / "packets" / (slug + ".zip"), standalone)
        row.update({"kind": "complete_packet", "packet": packet["id"], "owner": packet["owner"],
                    "payload_files": len(packet["paths"]), "relative_path": "packets/" + row["file"]})
        result["downloads"].append(row)
    for owner in ("A", "B"):
        prefix = "student_" + owner + "/"
        owned = [p for p in manifest["packets"] if p["owner"] == owner]
        ids = ", ".join(p["id"] for p in owned)
        start = (f"# Student {owner}: complete Guava handoff\n\n"
                 f"Your packets are **{ids}**, in the shared 01–12 order.\n\n"
                 "Read COMMIT_MAP.md first. Open full_code.html for every source file. "
                 "Each packets/ subdirectory contains the actual complete files to push "
                 "under payload/, plus its own instructions and hash manifest.\n\n"
                 f"Source snapshot: `{manifest['source_commit']}`. The complete study is "
                 "split between both students; your ZIP intentionally contains only your "
                 "six payloads, while both students receive the full guide for cross-review.\n\n"
                 "Set HANDOFF_DIR to this extracted student directory, then follow the "
                 "map. Run the helper with Python 3.12+. The helper never commits or pushes. "
                 "The teacher repository URL remains yours to supply.\n").encode()
        entries = {prefix + name: data for name, data in common.items()}
        entries[prefix + "START_HERE.md"] = start
        for packet in owned:
            slug = packet["slug"]
            entries.update({prefix + "packets/" + slug + "/" + name: data
                            for name, data in packet_entries[slug].items()})
        row = write_zip(destination / f"student_{owner}_complete.zip", entries)
        row.update({"kind": "complete_student", "owner": owner, "packets": [p["id"] for p in owned],
                    "payload_files": sum(len(p["paths"]) for p in owned), "relative_path": row["file"]})
        result["downloads"].append(row)
    # Small code download for reading; the complete student ZIPs are used for import.
    entries = {"complete_code/" + name: data for name, data in common.items()}
    entries["complete_code/START_HERE.md"] = (
        "# Complete readable code\n\nOpen full_code.html or COMMIT_MAP.md. The source_files/ "
        "directory also contains all 61 code/configuration files, grouped by commit. "
        "This small download does not contain the large data/report/tool payloads. "
        "Use student_A_complete.zip and student_B_complete.zip for the full import.\n").encode()
    for f in manifest["files"]:
        if f["include_in_full_code_listing"]:
            slug = next(p["slug"] for p in manifest["packets"] if p["id"] == f["packet"])
            entries["complete_code/source_files/" + slug + "/" + f["path"]] = payload[f["path"]]
    row = write_zip(destination / "complete_code_guide.zip", entries)
    row.update({"kind": "code_and_guides_only", "code_files": manifest["code_listing_files"], "relative_path": row["file"]})
    result["downloads"].append(row)
    (HANDOFF / "download_manifest.json").write_bytes(json_bytes(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HANDOFF / "downloads")
    parser.add_argument("--guides-only", action="store_true", help="Update the readable guides without building ZIPs")
    args = parser.parse_args()
    manifest = json.loads((HANDOFF / "manifest.json").read_text())
    payload = read_source(manifest)
    result = build(manifest, payload, args.output.resolve(), args.guides_only)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
