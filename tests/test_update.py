"""Exercise actual ZIP application and commits in disposable repositories."""

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile


UPDATER = Path(__file__).resolve().parents[1] / "jsonic-update"


@unittest.skipUnless(os.name == "posix" and shutil.which("git"), "Updater tests require POSIX and Git")
class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.repo = self.work / "repository with spaces"
        self.repo.mkdir()
        self.archive = self.work / "JSONIC.zip"
        self.git("init", "--template=", "-b", "main")
        self.git("config", "user.name", "JSONIC test")
        self.git("config", "user.email", "jsonic@example.invalid")
        (self.repo / "existing.txt").write_text("original\n")
        self.git("add", ".")
        self.git("commit", "-m", "Initial fixture")

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args], stderr=subprocess.STDOUT,
        ).decode().strip()

    def package(self, files=None, remove=None, message="Make the damn update work"):
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("update.json", json.dumps({"message": message, "remove": remove or []}))
            for name, data in (files or {"existing.txt": b"updated\n"}).items():
                info = zipfile.ZipInfo(name)
                info.external_attr = (stat.S_IFREG | (0o755 if name == "jsonic-update" else 0o644)) << 16
                archive.writestr(info, data)

    def run_update(self):
        return subprocess.run(
            [sys.executable, str(UPDATER), str(self.archive), "--repo", str(self.repo)],
            capture_output=True, text=True, timeout=30,
        )

    def test_applies_additions_changes_removals_and_one_commit(self):
        self.package({"new/file.txt": b"new\n", "jsonic-update": b"#!/bin/sh\n"}, ["existing.txt"])
        result = self.run_update()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.repo / "existing.txt").exists())
        self.assertEqual((self.repo / "new/file.txt").read_bytes(), b"new\n")
        self.assertEqual(self.git("log", "-1", "--format=%s"), "Make the damn update work")
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "2")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertFalse(self.archive.exists())
        self.assertFalse((self.repo / "update.json").exists())
        self.assertIn("100755", self.git("ls-files", "--stage", "jsonic-update"))
        self.assertEqual(self.git("remote", "-v"), "")

    def test_identical_package_does_not_make_empty_commit(self):
        self.package({"existing.txt": b"original\n"})
        result = self.run_update()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "1")
        self.assertFalse(self.archive.exists())

    def test_local_tracked_changes_are_not_overwritten(self):
        self.package()
        target = self.repo / "existing.txt"
        target.write_bytes(b"local edit")
        result = self.run_update()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("uncommitted", result.stderr)
        self.assertEqual(target.read_bytes(), b"local edit")
        self.assertTrue(self.archive.exists())

    def test_unrelated_untracked_output_is_left_alone(self):
        target = self.repo / "experiment.json"
        target.write_bytes(b'{"keep":true}')
        self.package()
        result = self.run_update()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(target.read_bytes(), b'{"keep":true}')
        self.assertEqual(self.git("ls-files", "experiment.json"), "")

    def test_rejects_git_paths_and_traversal_before_writing(self):
        for name in ("../outside.txt", ".git/config", "nested/../../outside.txt", "/absolute.txt"):
            with self.subTest(name=name):
                self.package({"existing.txt": b"updated", name: b"bad"})
                result = self.run_update()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((self.repo / "existing.txt").read_text(), "original\n")
                self.assertEqual(self.git("status", "--porcelain"), "")
                self.assertTrue(self.archive.exists())

    def test_ignored_local_file_is_not_overwritten(self):
        (self.repo / ".gitignore").write_text("local.txt\n")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "Ignore local scratch file")
        local = self.repo / "local.txt"
        local.write_text("keep me")
        for files, remove in [({"local.txt": b"replacement"}, []),
                              ({"existing.txt": b"updated"}, ["local.txt"])]:
            with self.subTest(remove=remove):
                self.package(files, remove)
                result = self.run_update()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Untracked update destination", result.stderr)
                self.assertEqual(local.read_text(), "keep me")
                self.assertTrue(self.archive.exists())

    def test_existing_symlink_cannot_redirect_extraction(self):
        outside = self.work / "outside.txt"
        outside.write_text("keep me")
        (self.repo / "linked.txt").symlink_to(outside)
        self.git("add", "linked.txt")
        self.git("commit", "-m", "Symlink fixture")
        self.package({"linked.txt": b"replacement"})
        result = self.run_update()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)
        self.assertEqual(outside.read_text(), "keep me")

    def test_commit_failure_keeps_archive_and_applied_files(self):
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.parent.mkdir(exist_ok=True)
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        self.package()
        result = self.run_update()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ZIP is retained", result.stderr)
        self.assertTrue(self.archive.exists())
        self.assertEqual((self.repo / "existing.txt").read_text(), "updated\n")
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "1")


if __name__ == "__main__":
    unittest.main()
