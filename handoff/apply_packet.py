#!/usr/bin/env python3
"""Check or import a complete commit packet into an existing Git checkout.

This helper never commits, pushes, changes Git identities, or overwrites files.
Run without --apply first. Use --subdir guava-study to keep a teacher's existing
README and other starter files separate from the imported assignment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from typing import Any


class PacketError(Exception):
    """A packet or target failed a check before it could be used safely."""


def safe_relative(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise PacketError(f"{label} must be a nonempty relative path.")
    parts = value.split("/")
    if (
        PurePosixPath(value).is_absolute()
        or "\\" in value
        or re.match(r"^[A-Za-z]:", value)
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
        or any(part in ("", ".", "..") or part.casefold() == ".git" for part in parts)
    ):
        raise PacketError(f"Unsafe {label}: {value!r}. Use plain relative paths without .git or traversal.")
    return value


def no_symlinks(path: Path, *, allow_missing: bool = False) -> None:
    """Check each existing component without resolving away a symbolic link."""
    path = Path(os.path.abspath(path))
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            if allow_missing:
                return
            raise PacketError(f"Required path does not exist: {current}") from None
        except NotADirectoryError:
            raise PacketError(f"A parent path is a file, not a directory: {current}") from None
        if stat.S_ISLNK(info.st_mode):
            raise PacketError(f"Symbolic links are not accepted in packet or destination paths: {current}")
        if current != path and not stat.S_ISDIR(info.st_mode):
            raise PacketError(f"A parent path is not a directory: {current}")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise PacketError(f"packet.json repeats the key {key!r}.")
        result[key] = value
    return result


def records(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise PacketError(f"packet.json {label} must be a list.")
    found = set()
    validated = []
    for item in value:
        if not isinstance(item, dict):
            raise PacketError(f"Every {label} entry must be a file record.")
        path = safe_relative(item.get("path"), f"{label} path")
        if path in found:
            raise PacketError(f"Duplicate {label} path: {path}")
        found.add(path)
        if type(item.get("bytes")) is not int or item["bytes"] < 0:
            raise PacketError(f"Invalid byte count for {path}.")
        for field, length in (("sha256", 64), ("git_blob_sha1", 40)):
            if not isinstance(item.get(field), str) or not re.fullmatch(rf"[0-9a-f]{{{length}}}", item[field]):
                raise PacketError(f"Invalid {field} for {path}.")
        if item.get("mode") not in ("100644", "100755"):
            raise PacketError(f"Only regular-file Git modes 100644 and 100755 are accepted: {path}")
        validated.append(item)
    return validated


def read_packet(root: Path) -> dict[str, Any]:
    no_symlinks(root)
    if not root.is_dir():
        raise PacketError(f"Packet must be an unpacked directory: {root}")
    manifest = root / "packet.json"
    no_symlinks(manifest)
    if not manifest.is_file():
        raise PacketError(f"packet.json must be a regular file: {manifest}")
    try:
        packet = json.loads(manifest.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PacketError(f"Cannot read packet.json: {error}") from error
    if not isinstance(packet, dict) or type(packet.get("schema")) is not int or packet["schema"] != 1:
        raise PacketError("This helper requires packet.json schema 1.")
    if type(packet.get("number")) is not int or not 1 <= packet["number"] <= 99:
        raise PacketError("Packet number must be an integer from 1 to 99.")
    if packet.get("id") != f"{packet['number']:02d}" or packet.get("owner") not in ("A", "B"):
        raise PacketError("Packet id must match its two-digit number, and owner must be A or B.")
    if not isinstance(packet.get("source_commit"), str) or not re.fullmatch(r"[0-9a-f]{40}", packet["source_commit"]):
        raise PacketError("source_commit must be a complete 40-character Git commit SHA.")
    for field in ("title", "commit_message"):
        value = packet.get(field)
        if not isinstance(value, str) or not value.strip() or any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise PacketError(f"{field} must be nonempty plain text on one line.")
    packet["files"] = records(packet.get("files"), "files")
    packet["prerequisites"] = records(packet.get("prerequisites"), "prerequisites")
    if not packet["files"]:
        raise PacketError("A commit packet must contain at least one file.")
    all_paths = [item["path"] for item in packet["files"] + packet["prerequisites"]]
    if len(all_paths) != len(set(all_paths)):
        raise PacketError("A file cannot be both a current packet file and a prerequisite.")
    path_set = set(all_paths)
    for path in all_paths:
        if any(str(parent) in path_set for parent in PurePosixPath(path).parents):
            raise PacketError(f"A listed file is also used as another file's parent directory: {path}")
    return packet


def file_identity(path: Path) -> tuple[int, str, str]:
    no_symlinks(path)
    if not path.is_file():
        raise PacketError(f"Expected a regular file: {path}")
    size = path.stat().st_size
    sha256 = hashlib.sha256()
    blob = hashlib.sha1(b"blob " + str(size).encode("ascii") + b"\0")
    count = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            count += len(block)
            sha256.update(block)
            blob.update(block)
    return count, sha256.hexdigest(), blob.hexdigest()


def expected_identity(item: dict[str, Any]) -> tuple[int, str, str]:
    return item["bytes"], item["sha256"], item["git_blob_sha1"]


def check_payload(root: Path, items: list[dict[str, Any]]) -> None:
    payload = root / "payload"
    no_symlinks(payload)
    if not payload.is_dir():
        raise PacketError(f"Missing payload directory: {payload}")
    actual = set()

    def walk_error(error: OSError) -> None:
        raise error

    for parent, directories, filenames in os.walk(payload, followlinks=False, onerror=walk_error):
        for name in directories + filenames:
            path = Path(parent) / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise PacketError(f"Payload contains a symbolic link: {path}")
            if not stat.S_ISDIR(info.st_mode) and not stat.S_ISREG(info.st_mode):
                raise PacketError(f"Payload contains a nonregular file: {path}")
        actual.update((Path(parent) / name).relative_to(payload).as_posix() for name in filenames)
    expected = {item["path"] for item in items}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise PacketError(f"Payload inventory does not match packet.json. Missing: {missing}; extra: {extra}.")
    for item in items:
        if file_identity(payload / item["path"]) != expected_identity(item):
            raise PacketError(f"Payload bytes or hashes do not match packet.json: {item['path']}")


def git(target: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "--no-optional-locks", "--literal-pathspecs", "-C", str(target), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise PacketError(f"Git could not complete {' '.join(arguments[:2])}: {detail}")
    return result


def check_git_root(target: Path) -> None:
    no_symlinks(target)
    if not target.is_dir():
        raise PacketError(f"Target must be an existing Git checkout directory: {target}")
    inside = git(target, "rev-parse", "--is-inside-work-tree", check=False)
    if inside.returncode or inside.stdout.strip() != b"true":
        raise PacketError(f"Target is not an existing nonbare Git checkout: {target}")
    top = git(target, "rev-parse", "--show-toplevel").stdout.decode("utf-8").strip()
    if Path(os.path.abspath(top)) != target:
        raise PacketError(f"--target must be the Git repository root: {top}")
    object_format = git(target, "rev-parse", "--show-object-format").stdout.strip()
    if object_format != b"sha1":
        raise PacketError("These packets record Git SHA-1 object IDs; use a normal SHA-1 Git checkout.")


def require_clean(target: Path) -> None:
    status = git(target, "status", "--porcelain=v1", "-z", "--untracked-files=no", "--ignore-submodules=none")
    if status.stdout:
        raise PacketError(
            "The destination has staged changes or modified/deleted tracked files. "
            "Finish or save that work yourself, then retry. Unrelated untracked files are allowed."
        )


def head_sha(target: Path) -> str | None:
    result = git(target, "rev-parse", "--verify", "--quiet", "HEAD", check=False)
    return result.stdout.decode("ascii").strip() if result.returncode == 0 else None


def target_name(path: str, subdir: str) -> str:
    return f"{subdir}/{path}" if subdir else path


def head_files(target: Path, names: list[str], head: str | None) -> dict[str, tuple[str, str]]:
    if head is None:
        return {}
    result = git(target, "ls-tree", "-r", "-z", head, "--", *names)
    found = {}
    for entry in result.stdout.split(b"\0"):
        if entry:
            metadata, raw_path = entry.split(b"\t", 1)
            mode, kind, object_id = metadata.decode("ascii").split(" ")
            found[raw_path.decode("utf-8")] = (mode, object_id) if kind == "blob" else (mode, "")
    return found


def check_destination_path(study_root: Path, item: dict[str, Any]) -> bool:
    destination = study_root / item["path"]
    no_symlinks(destination, allow_missing=True)
    if not destination.exists():
        return False
    if not destination.is_file() or file_identity(destination) != expected_identity(item):
        raise PacketError(
            f"Destination already contains different content at {destination}. Nothing will be overwritten. "
            "Keep your existing work and resolve the difference manually, or choose an unused --subdir."
        )
    executable = bool(destination.stat().st_mode & 0o111)
    if executable != (item["mode"] == "100755"):
        raise PacketError(f"Destination has a different executable-file mode: {destination}. Resolve it manually first.")
    return True


def make_parents(parent: Path, created: list[Path]) -> None:
    missing = []
    cursor = parent
    while not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    no_symlinks(cursor)
    if not cursor.is_dir():
        raise PacketError(f"Destination parent is not a directory: {cursor}")
    for directory in reversed(missing):
        directory.mkdir()
        created.append(directory)


def copy_absent(root: Path, study_root: Path, items: list[dict[str, Any]]) -> None:
    """Copy with exclusive creation, and undo our new files if copying fails."""
    created_files: list[Path] = []
    created_directories: list[Path] = []
    try:
        for item in items:
            source = root / "payload" / item["path"]
            destination = study_root / item["path"]
            no_symlinks(source)
            no_symlinks(destination, allow_missing=True)
            make_parents(destination.parent, created_directories)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(destination, flags, 0o755 if item["mode"] == "100755" else 0o644)
            created_files.append(destination)
            with os.fdopen(descriptor, "wb") as output, source.open("rb") as input_stream:
                for block in iter(lambda: input_stream.read(1024 * 1024), b""):
                    output.write(block)
            destination.chmod(0o755 if item["mode"] == "100755" else 0o644)
            if file_identity(destination) != expected_identity(item):
                raise PacketError(f"Source changed during copying: {item['path']}. Newly copied files will be removed.")
    except BaseException:
        for path in reversed(created_files):
            path.unlink(missing_ok=True)
        for directory in reversed(created_directories):
            try:
                directory.rmdir()
            except OSError:
                pass  # A concurrently created unrelated file must be kept.
        raise


def check_index(target: Path, items: list[dict[str, Any]], subdir: str) -> int:
    names = [target_name(item["path"], subdir) for item in items]
    changed = {
        name.decode("utf-8")
        for name in git(target, "diff", "--cached", "--name-only", "-z").stdout.split(b"\0")
        if name
    }
    if not changed <= set(names):
        raise PacketError(
            "The index changed concurrently and includes paths outside this packet. "
            "Inspect git diff --cached before doing anything else; no commit was made."
        )
    indexed = {}
    for entry in git(target, "ls-files", "--stage", "-z", "--", *names).stdout.split(b"\0"):
        if entry:
            metadata, raw_path = entry.split(b"\t", 1)
            mode, object_id, stage = metadata.decode("ascii").split(" ")
            indexed[raw_path.decode("utf-8")] = (mode, object_id, stage)
    for item, name in zip(items, names):
        if indexed.get(name) != (item["mode"], item["git_blob_sha1"], "0"):
            raise PacketError(
                f"Git staged different bytes or a different mode for {name}; an attribute/filter may have changed it. "
                "Inspect and unstage that packet before committing. No commit was made."
            )
    return len(changed)


def stage_packet(target: Path, items: list[dict[str, Any]], subdir: str) -> int:
    names = [target_name(item["path"], subdir) for item in items]
    result = git(target, "-c", "core.autocrlf=false", "add", "--", *names, check=False)
    if result.returncode:
        raise PacketError(
            "Files were copied, but Git could not stage the complete packet. "
            "Inspect git status and your ignore/attribute rules before retrying. "
            + result.stderr.decode("utf-8", errors="replace").strip()
        )
    return check_index(target, items, subdir)


def run(arguments: argparse.Namespace) -> int:
    packet_root = Path(os.path.abspath(arguments.packet))
    target = Path(os.path.abspath(arguments.target))
    subdir = safe_relative(arguments.subdir, "--subdir") if arguments.subdir else ""
    study_root = target / subdir if subdir else target
    packet = read_packet(packet_root)
    check_payload(packet_root, packet["files"])
    check_git_root(target)
    if arguments.check_staged:
        unstaged = git(target, "diff", "--quiet", "--ignore-submodules=none", check=False)
        if unstaged.returncode:
            raise PacketError("There are unstaged tracked changes. Inspect git diff before checking the staged packet.")
    else:
        require_clean(target)
    no_symlinks(study_root, allow_missing=True)
    if study_root.exists() and not study_root.is_dir():
        raise PacketError(f"Study destination must be a directory: {study_root}")
    head = head_sha(target)
    names = [target_name(item["path"], subdir) for item in packet["files"] + packet["prerequisites"]]
    committed = head_files(target, names, head)
    for item in packet["prerequisites"]:
        name = target_name(item["path"], subdir)
        if committed.get(name) != (item["mode"], item["git_blob_sha1"]):
            raise PacketError(
                f"Prerequisite is not committed in HEAD with the expected bytes/mode: {name}. "
                "Complete, commit, and pull the earlier packets in order, then retry. "
                "An untracked or merely staged copy does not satisfy a prerequisite."
            )
        if not check_destination_path(study_root, item):
            raise PacketError(
                f"Prerequisite is committed correctly but missing from the working directory: {name}. "
                "Restore that file through your checkout or sparse-checkout settings, then retry. "
                "The helper will not change those settings or recreate earlier packets implicitly."
            )
    absent = [item for item in packet["files"] if not check_destination_path(study_root, item)]
    already_committed = all(
        committed.get(target_name(item["path"], subdir)) == (item["mode"], item["git_blob_sha1"])
        for item in packet["files"]
    )
    print(f"Packet {packet['id']} — Student {packet['owner']}: {packet['title']}")
    print(f"Pinned source commit: {packet['source_commit']}")
    print(f"Git repository: {target}")
    print(f"Study working directory (run the packet's checks here): {study_root}")
    print(
        f"Validated {len(packet['files'])} packet files and {len(packet['prerequisites'])} committed prerequisites; "
        f"{len(absent)} files need copying, {len(packet['files']) - len(absent)} are already identical."
    )
    if arguments.check_staged:
        if absent:
            raise PacketError("Some packet files have not been copied. Apply and stage the packet before --check-staged.")
        count = check_index(target, packet["files"], subdir)
        print(f"Staged check passed: {count} changed paths, all packet index blobs/modes exact, and no extra staged paths.")
        if already_committed:
            print("All packet files are already committed in HEAD. No new commit is needed.")
        print("No files or Git state changed. Review the packet's checks before committing with your own identity.")
        return 0
    if already_committed:
        print("All packet files are already committed in HEAD. No new commit is needed.")
        return 0
    if not arguments.apply:
        print("Dry run passed. No files or Git state changed. Add --apply to copy; add --stage to stage only this packet.")
        return 0
    if head_sha(target) != head:
        raise PacketError("HEAD changed during preflight. Nothing was copied; retry after the other Git operation finishes.")
    require_clean(target)
    copy_absent(packet_root, study_root, absent)
    print(f"Copied {len(absent)} new files; existing identical files were kept.")
    if arguments.stage:
        count = stage_packet(target, packet["files"], subdir)
        print(f"Staged and hash-checked {count} changed packet paths. Review git diff --cached before committing.")
    else:
        print("Nothing was staged. Review the files and run the packet's checks before staging its explicit paths.")
    print(f"Suggested commit message: {packet['commit_message']}")
    print("Use your own Git identity and actual commit date. This helper did not commit or push.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, type=Path, help="Unpacked packet directory containing packet.json and payload/")
    parser.add_argument("--target", required=True, type=Path, help="Existing destination Git repository root")
    parser.add_argument("--subdir", default="", help="Optional new study directory inside the target, for example guava-study")
    parser.add_argument("--apply", action="store_true", help="Copy absent files after all preflight checks pass")
    parser.add_argument("--stage", action="store_true", help="With --apply, stage exactly this packet's paths; never commit or push")
    parser.add_argument("--check-staged", action="store_true", help="Read-only check of an already staged packet, including exact index hashes and no extra staged paths")
    arguments = parser.parse_args()
    if arguments.stage and not arguments.apply:
        parser.error("--stage requires --apply; the default is a read-only dry run")
    if arguments.check_staged and (arguments.apply or arguments.stage):
        parser.error("--check-staged is read-only and cannot be combined with --apply or --stage")
    try:
        return run(arguments)
    except (PacketError, OSError, UnicodeError) as error:
        print(f"Packet stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
