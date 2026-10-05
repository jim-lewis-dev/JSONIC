"""Exercise actual ZIP application and commits in disposable repositories."""

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


UPDATER = Path(__file__).resolve().parents[1] / "update.py"


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
            env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
        ).decode().strip()

    def package(self, files=None, remove=None, message="Make the damn update work"):
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("update.json", json.dumps({"message": message, "remove": remove or []}))
            for name, data in (files or {"existing.txt": b"updated\n"}).items():
                info = zipfile.ZipInfo(name)
                info.external_attr = (stat.S_IFREG | (0o755 if name == "update.py" else 0o644)) << 16
                archive.writestr(info, data)

    def run_update(self):
        return subprocess.run(
            [sys.executable, str(UPDATER), str(self.archive), "--project", str(self.repo)],
            capture_output=True, text=True, timeout=30,
        )

    def test_applies_additions_changes_removals_and_one_commit(self):
        self.package({"new/file.txt": b"new\n", "update.py": b"#!/bin/sh\n"}, ["existing.txt"])
        result = self.run_update()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.repo / "existing.txt").exists())
        self.assertEqual((self.repo / "new/file.txt").read_bytes(), b"new\n")
        self.assertEqual(self.git("log", "-1", "--format=%s"), "Make the damn update work")
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "2")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertFalse(self.archive.exists())
        self.assertFalse((self.repo / "update.json").exists())
        self.assertIn("100755", self.git("ls-files", "--stage", "update.py"))
        self.assertEqual(self.git("remote", "-v"), "")

    def test_identical_package_does_not_make_empty_commit(self):
        self.package({"existing.txt": b"original\n"})
        result = self.run_update()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "1")
        self.assertFalse(self.archive.exists())

    def test_no_download_waiting_is_a_friendly_noop(self):
        loader = importlib.machinery.SourceFileLoader("jsonic_update", str(UPDATER))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(module.Path, "home", return_value=self.work), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = module.main(["--project", str(self.repo)])
        self.assertEqual(result, 0)
        self.assertIn("No update waiting", stdout.getvalue())
        self.assertIn("Download JSONIC.zip", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "1")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_explicit_missing_archive_remains_an_error(self):
        result = self.run_update()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("update.py: error:", result.stderr)
        self.assertEqual(self.git("rev-list", "--count", "HEAD"), "1")

    def test_staged_unstaged_and_untracked_work_blocks_updates_without_mutation(self):
        for kind in ("unstaged", "staged", "untracked"):
            with self.subTest(kind=kind):
                self.package()
                target = self.repo / ("local.txt" if kind == "untracked" else "existing.txt")
                target.write_bytes(b"local edit")
                if kind == "staged":
                    self.git("add", "existing.txt")
                status = self.git("status", "--porcelain")
                head = self.git("rev-parse", "HEAD")
                index = (self.repo / ".git" / "index").read_bytes()
                archive = self.archive.read_bytes()
                result = self.run_update()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("uncommitted or untracked work", result.stderr)
                self.assertEqual(target.read_bytes(), b"local edit")
                self.assertEqual(self.archive.read_bytes(), archive)
                self.assertEqual((self.repo / ".git" / "index").read_bytes(), index)
                self.assertEqual(self.git("rev-parse", "HEAD"), head)
                self.assertEqual(self.git("status", "--porcelain"), status)
                if kind == "untracked":
                    self.assertEqual((self.repo / "existing.txt").read_bytes(), b"original\n")
                    target.unlink()
                else:
                    target.write_bytes(b"original\n")
                    if kind == "staged":
                        self.git("add", "existing.txt")

    def test_unrelated_ignored_output_is_left_alone(self):
        (self.repo / ".gitignore").write_text("experiment.json\nJSONIC-snapshot.zip\n")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "Ignore local outputs")
        target = self.repo / "experiment.json"
        target.write_bytes(b'{"keep":true}')
        snapshot = self.repo / "JSONIC-snapshot.zip"
        snapshot.write_bytes(b"keep this snapshot")
        self.package()
        result = self.run_update()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(target.read_bytes(), b'{"keep":true}')
        self.assertEqual(snapshot.read_bytes(), b"keep this snapshot")
        self.assertEqual(self.git("ls-files", "experiment.json"), "")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_no_arguments_use_script_project_and_default_download_from_other_directory(self):
        script = self.repo / "update.py"
        shutil.copyfile(UPDATER, script)
        (self.repo / ".gitignore").write_text("__pycache__/\n")
        self.git("add", "update.py", ".gitignore")
        self.git("commit", "-m", "Install the updater")
        self.archive = self.work / "Downloads" / "JSONIC.zip"
        self.archive.parent.mkdir()
        self.package()
        loader = importlib.machinery.SourceFileLoader("installed_update", str(script))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        old_directory = Path.cwd()
        os.chdir(self.work)
        self.addCleanup(os.chdir, old_directory)
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(module.Path, "home", return_value=self.work), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = module.main([])
        self.assertEqual(result, 0, stderr.getvalue())
        self.assertEqual((self.repo / "existing.txt").read_bytes(), b"updated\n")
        self.assertFalse(self.archive.exists())
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_piped_bootstrap_accepts_project_and_download_directory(self):
        self.package()
        result = subprocess.run(
            [sys.executable, "-", "--project", str(self.repo), "--downloads", str(self.work)],
            input=UPDATER.read_text(), cwd=self.work, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / "existing.txt").read_bytes(), b"updated\n")
        self.assertFalse(self.archive.exists())
        self.assertEqual(self.git("status", "--porcelain"), "")

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
