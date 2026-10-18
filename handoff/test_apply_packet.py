"""Real-Git fixture checks for the handoff importer, independent of study tests.

Run: python -m unittest discover -s handoff -p 'test_apply_packet.py' -v
All fixture commits use an explicit automated-test identity and current time.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HELPER = Path(__file__).resolve().with_name("apply_packet.py")


def record(path: str, content: bytes, mode: str = "100644") -> dict:
    return {
        "path": path,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "git_blob_sha1": hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest(),
        "mode": mode,
    }


class ApplyPacketTest(unittest.TestCase):
    def setUp(self) -> None:
        fixture_root = HELPER.parent / "verification-work"
        fixture_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="packet-fixture-", dir=fixture_root)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.target = self.base / "teacher"
        self.target.mkdir()
        self.git("init", "-q")
        (self.target / "README.md").write_text("Teacher's starter instructions.\n", encoding="utf-8")
        self.git("add", "--", "README.md")
        self.commit("Automated test fixture baseline")
        self.packet_root = self.base / "packet"
        self.packet_root.mkdir()
        (self.packet_root / "payload").mkdir()

    def git(self, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-c", "user.name=Automated packet validation", "-c", "user.email=automated-test@example.invalid",
             "-c", "commit.gpgsign=false", "-C", str(self.target), *arguments],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )

    def commit(self, message: str) -> None:
        self.git("commit", "-q", "-m", message)

    def packet(self, files: dict[str, bytes] | None = None, prerequisites: list[dict] | None = None) -> dict:
        files = files if files is not None else {"src/main.py": b"print('complete file')\n", "config/settings.json": b'{"seed": 7}\n'}
        manifest = {
            "schema": 1, "source_commit": "f" * 40, "id": "01", "number": 1, "owner": "A",
            "title": "Automated fixture packet", "commit_message": "Import reviewed fixture files",
            "files": [record(name, data) for name, data in files.items()], "prerequisites": prerequisites or [],
        }
        for name, data in files.items():
            path = self.packet_root / "payload" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o644)
        self.write_manifest(manifest)
        return manifest

    def write_manifest(self, manifest: dict) -> None:
        (self.packet_root / "packet.json").write_text(json.dumps(manifest), encoding="utf-8")

    def run_helper(self, *arguments: str, success: bool = True) -> subprocess.CompletedProcess:
        result = subprocess.run(
            [sys.executable, str(HELPER), "--packet", str(self.packet_root), "--target", str(self.target), *arguments],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
            env={**os.environ, "GIT_CEILING_DIRECTORIES": str(self.base)},
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def staged(self) -> set[str]:
        return {item.decode() for item in self.git("diff", "--cached", "--name-only", "-z").stdout.split(b"\0") if item}

    def test_dry_run_does_not_copy_or_stage(self) -> None:
        self.packet()
        index_before = (self.target / ".git" / "index").read_bytes()
        result = self.run_helper()
        self.assertIn("Dry run passed", result.stdout)
        self.assertFalse((self.target / "src").exists())
        self.assertEqual(self.staged(), set())
        self.assertEqual((self.target / ".git" / "index").read_bytes(), index_before)

    def test_apply_stages_only_packet_preserving_unrelated_files(self) -> None:
        manifest = self.packet()
        unrelated = self.target / "personal-notes.txt"
        unrelated.write_text("Keep this untracked.\n")
        head_before = self.git("rev-parse", "HEAD").stdout
        self.run_helper("--apply", "--stage")
        self.assertEqual(self.staged(), {item["path"] for item in manifest["files"]})
        self.assertEqual(unrelated.read_text(), "Keep this untracked.\n")
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, head_before)
        for item in manifest["files"]:
            self.assertEqual((self.target / item["path"]).read_bytes(), (self.packet_root / "payload" / item["path"]).read_bytes())

    def test_subdir_preserves_teacher_readme_and_enforces_prefixed_prerequisite(self) -> None:
        self.packet({"README.md": b"Study instructions.\n"})
        self.run_helper("--subdir", "guava-study", "--apply", "--stage")
        self.assertEqual(self.staged(), {"guava-study/README.md"})
        self.assertEqual((self.target / "README.md").read_text(), "Teacher's starter instructions.\n")
        self.commit("Automated fixture: packet one")
        (self.packet_root / "payload" / "README.md").unlink()
        self.packet({"src/next.py": b"answer = 42\n"}, [record("README.md", b"Study instructions.\n")])
        result = self.run_helper("--subdir", "guava-study", "--apply", "--stage")
        self.assertIn(str(self.target / "guava-study"), result.stdout)
        self.assertEqual(self.staged(), {"guava-study/src/next.py"})

    def test_untracked_prerequisite_is_not_sufficient(self) -> None:
        content = b"already copied but not committed\n"
        (self.target / "earlier.py").write_bytes(content)
        self.packet(prerequisites=[record("earlier.py", content)])
        result = self.run_helper("--apply", success=False)
        self.assertIn("Prerequisite is not committed", result.stderr)
        self.assertFalse((self.target / "src").exists())
        self.git("add", "--", "earlier.py")
        self.run_helper("--apply", success=False)
        self.commit("Automated fixture: prerequisite")
        self.run_helper("--apply")
        self.assertTrue((self.target / "src/main.py").is_file())

    def test_dirty_worktree_and_index_are_blocked(self) -> None:
        self.packet()
        (self.target / "README.md").write_text("Unfinished tracked work.\n")
        self.assertIn("staged changes", self.run_helper("--apply", success=False).stderr)
        self.git("add", "--", "README.md")
        self.run_helper("--apply", success=False)
        self.assertFalse((self.target / "src").exists())

    def test_collision_preflight_makes_no_partial_copy(self) -> None:
        self.packet({"first.txt": b"new\n", "last.txt": b"expected\n"})
        (self.target / "last.txt").write_bytes(b"Keep my work.\n")
        self.assertIn("different content", self.run_helper("--apply", success=False).stderr)
        self.assertFalse((self.target / "first.txt").exists())
        self.assertEqual((self.target / "last.txt").read_bytes(), b"Keep my work.\n")

    def test_tampered_payload_is_rejected_before_copy(self) -> None:
        self.packet()
        (self.packet_root / "payload/src/main.py").write_text("tampered\n")
        self.assertIn("hashes", self.run_helper("--apply", success=False).stderr)
        self.assertFalse((self.target / "config").exists())

    def test_extra_and_missing_payload_files_are_rejected(self) -> None:
        self.packet()
        extra = self.packet_root / "payload/extra.py"
        extra.write_bytes(b"extra\n")
        self.assertIn("inventory", self.run_helper("--apply", success=False).stderr)
        extra.unlink()
        (self.packet_root / "payload/src/main.py").unlink()
        self.assertIn("inventory", self.run_helper("--apply", success=False).stderr)
        self.assertFalse((self.target / "config").exists())

    def test_manifest_traversal_and_git_paths_are_rejected(self) -> None:
        manifest = self.packet({"safe.txt": b"safe\n"})
        for path in ("../escape.txt", "/absolute.txt", "a/../../escape", ".git/config", "a/.GiT/config", "a\\evil.txt", "C:/escape.txt"):
            with self.subTest(path=path):
                manifest["files"][0]["path"] = path
                self.write_manifest(manifest)
                self.assertIn("Unsafe", self.run_helper("--apply", success=False).stderr)
        self.assertFalse((self.target / "safe.txt").exists())

    def test_subdir_traversal_and_symlink_are_rejected(self) -> None:
        self.packet()
        for subdir in ("../outside", ".git/study", "/absolute"):
            with self.subTest(subdir=subdir):
                self.run_helper("--subdir", subdir, "--apply", success=False)
        (self.target / "linked-study").symlink_to(self.base, target_is_directory=True)
        self.assertIn("Symbolic links", self.run_helper("--subdir", "linked-study", "--apply", success=False).stderr)

    def test_source_and_destination_symlinks_are_rejected(self) -> None:
        self.packet({"safe.txt": b"safe\n"})
        source = self.packet_root / "payload/safe.txt"
        source.unlink()
        external = self.base / "external.txt"
        external.write_bytes(b"safe\n")
        source.symlink_to(external)
        self.assertIn("symbolic link", self.run_helper("--apply", success=False).stderr)
        source.unlink()
        source.write_bytes(b"safe\n")
        (self.target / "safe.txt").symlink_to(external)
        self.assertIn("Symbolic links", self.run_helper("--apply", success=False).stderr)
        self.assertEqual(external.read_bytes(), b"safe\n")

    def test_already_committed_packet_is_idempotent(self) -> None:
        self.packet()
        self.run_helper("--apply", "--stage")
        self.commit("Automated fixture: imported packet")
        head_before = self.git("rev-parse", "HEAD").stdout
        result = self.run_helper("--apply", "--stage")
        self.assertIn("No new commit is needed", result.stdout)
        self.assertEqual(self.staged(), set())
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, head_before)

    def test_identical_untracked_files_can_be_staged_without_rewriting(self) -> None:
        self.packet({"existing.txt": b"same bytes\n"})
        destination = self.target / "existing.txt"
        destination.write_bytes(b"same bytes\n")
        before = destination.stat().st_mtime_ns
        self.run_helper("--apply", "--stage")
        self.assertEqual(destination.stat().st_mtime_ns, before)
        self.assertEqual(self.staged(), {"existing.txt"})

    def test_stage_requires_apply(self) -> None:
        self.packet()
        self.assertIn("--stage requires --apply", self.run_helper("--stage", success=False).stderr)

    def test_non_repository_and_nested_target_are_rejected(self) -> None:
        self.packet()
        original = self.target
        self.target = self.base / "not-git"
        self.target.mkdir()
        self.assertIn("nonbare Git checkout", self.run_helper("--apply", success=False).stderr)
        self.target = original / "nested"
        self.target.mkdir()
        self.assertIn("repository root", self.run_helper("--apply", success=False).stderr)

    def test_wrong_committed_prerequisite_mode_is_rejected(self) -> None:
        path = self.target / "earlier.sh"
        path.write_bytes(b"exit 0\n")
        path.chmod(0o755)
        self.git("add", "--", "earlier.sh")
        self.commit("Automated fixture: executable prerequisite")
        self.packet(prerequisites=[record("earlier.sh", b"exit 0\n", "100644")])
        self.assertIn("expected bytes/mode", self.run_helper("--apply", success=False).stderr)

    def test_missing_skip_worktree_prerequisite_is_rejected_without_changes(self) -> None:
        content = b"Committed prerequisite hidden by skip-worktree.\n"
        prerequisite = self.target / "earlier.py"
        prerequisite.write_bytes(content)
        self.git("add", "--", "earlier.py")
        self.commit("Automated fixture: sparse prerequisite")
        self.git("update-index", "--skip-worktree", "--", "earlier.py")
        prerequisite.unlink()
        self.assertEqual(self.git("status", "--porcelain=v1", "--untracked-files=no").stdout, b"")
        self.packet(prerequisites=[record("earlier.py", content)])
        head_before = self.git("rev-parse", "HEAD").stdout
        index_before = (self.target / ".git/index").read_bytes()
        result = self.run_helper("--apply", "--stage", success=False)
        self.assertIn("committed correctly but missing from the working directory", result.stderr)
        self.assertFalse(prerequisite.exists())
        self.assertFalse((self.target / "src").exists())
        self.assertEqual((self.target / ".git/index").read_bytes(), index_before)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, head_before)

    def test_check_staged_accepts_exact_packet_and_rejects_extra_paths(self) -> None:
        self.packet()
        self.run_helper("--apply", "--stage")
        index_before = (self.target / ".git/index").read_bytes()
        self.assertIn("Staged check passed", self.run_helper("--check-staged").stdout)
        self.assertEqual((self.target / ".git/index").read_bytes(), index_before)
        (self.target / "unrelated.txt").write_text("Separate work.\n")
        self.git("add", "--", "unrelated.txt")
        self.assertIn("outside this packet", self.run_helper("--check-staged", success=False).stderr)
        self.assertIn("unrelated.txt", self.staged())

    def test_check_staged_rejects_unstaged_and_incomplete_packets(self) -> None:
        self.packet()
        self.run_helper("--check-staged", success=False)
        self.run_helper("--apply", "--stage")
        (self.target / "src/main.py").write_text("An unfinished edit.\n")
        self.assertIn("unstaged tracked changes", self.run_helper("--check-staged", success=False).stderr)

    def test_staging_filter_changes_are_detected_and_left_reviewable(self) -> None:
        self.packet({"filtered.txt": b"original bytes\n"})
        (self.target / ".gitattributes").write_text("filtered.txt filter=fixture\n")
        self.git("config", "filter.fixture.clean", "tr a-z A-Z")
        self.git("add", "--", ".gitattributes")
        self.commit("Automated fixture: clean filter")
        head_before = self.git("rev-parse", "HEAD").stdout
        self.assertIn("different bytes", self.run_helper("--apply", "--stage", success=False).stderr)
        self.assertEqual((self.target / "filtered.txt").read_bytes(), b"original bytes\n")
        self.assertEqual(self.staged(), {"filtered.txt"})
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, head_before)
        self.assertIn("different bytes", self.run_helper("--check-staged", success=False).stderr)


if __name__ == "__main__":
    unittest.main()
