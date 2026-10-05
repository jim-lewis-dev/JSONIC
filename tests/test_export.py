"""Snapshot tests using disposable repositories with real local changes."""
import hashlib
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


PROGRAM = Path(__file__).resolve().parents[1] / "export.py"


@unittest.skipUnless(shutil.which("git"), "Git is required for repository snapshots")
class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.repo = self.work / "project"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.output = self.work / "JSONIC-snapshot.zip"

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), "-c", "user.name=JSONIC test",
             "-c", "user.email=jsonic-test@example.invalid", *args],
            check=True, capture_output=True, timeout=15,
        ).stdout

    def file(self, name, data):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def cli(self, *args, program=PROGRAM):
        return subprocess.run(
            [sys.executable, str(program), *map(str, args)],
            cwd=self.work, capture_output=True, timeout=15,
        )

    def snapshot(self, *args):
        result = self.cli("--project", self.repo, "-o", self.output, *args)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(result.stderr, b"")
        with zipfile.ZipFile(self.output) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        return files, json.loads(files["project-state.json"])

    def test_snapshot_contains_real_files_and_each_kind_of_local_change(self):
        self.file("settings.json", b'{"count":1}\n')
        self.file(".gitignore", b'*.style\n__pycache__/\nnode_modules/\nbuild/\n')
        self.git("add", ".")
        self.git("commit", "-m", "Start sample")
        self.file("settings.json", b'{"count":2}\n')
        self.git("add", "settings.json")
        self.file("settings.json", b'{"count":3}\n')
        binary = bytes(range(256)) + b'\x00\xff\r\n'
        self.file("assets/raw.bin", binary)
        self.file("settings.jsonic.style", b'{"root_prefix_style":"/* note */"}\n')
        self.file(".editorconfig", b'root = true\n')
        self.file("__pycache__/cached.pyc", b"discard")
        self.file("node_modules/package/index.js", b"discard")
        self.file("build/generated", b"discard")
        self.file("JSONIC-snapshot.zip", b"previous snapshot")
        self.file("fixtures/sample.zip", b"real project data")
        before = self.git("status", "--porcelain", "--untracked-files=all")
        files, state = self.snapshot()
        self.assertEqual(files["settings.json"], b'{"count":3}\n')
        self.assertEqual(files["assets/raw.bin"], binary)
        self.assertIn("settings.jsonic.style", files)
        self.assertIn(".editorconfig", files)
        self.assertIn(".gitignore", files)
        self.assertEqual(files["fixtures/sample.zip"], b"real project data")
        self.assertNotIn("JSONIC-snapshot.zip", files)
        self.assertIn("JSONIC-snapshot.zip", state["excluded"])
        for prefix in (".git/", "__pycache__/", "node_modules/", "build/"):
            self.assertFalse(any(path.startswith(prefix) for path in files))
        self.assertEqual(state["branch"], "main")
        self.assertEqual(state["head"], self.git("rev-parse", "HEAD").decode().strip())
        self.assertEqual(state["status"], before.decode())
        self.assertIn('+{"count":2}', state["staged_diff"])
        self.assertIn('+{"count":3}', state["unstaged_diff"])
        self.assertIn("Start sample", state["recent_commits"][0])
        inventory = {entry["path"]: entry for entry in state["files"]}
        self.assertEqual(inventory["assets/raw.bin"]["sha256"], hashlib.sha256(binary).hexdigest())
        self.assertEqual(inventory["assets/raw.bin"]["size"], len(binary))
        self.assertEqual(before, self.git("status", "--porcelain", "--untracked-files=all"))

    def test_unborn_repository_and_repeated_inside_project_output(self):
        self.file("new.json", b'{}')
        self.output = self.repo / "snapshot.zip"
        _, initial = self.snapshot()
        self.assertIsNone(initial["head"])
        self.assertEqual(initial["recent_commits"], [])
        self.file("new.json", b'{"changed":true}')
        files, state = self.snapshot()
        self.assertEqual(files["new.json"], b'{"changed":true}')
        self.assertNotIn("snapshot.zip", files)
        self.assertIn("snapshot.zip", state["excluded"])
        self.assertFalse(list(self.repo.glob(".export-*.zip")))

    def test_symlinks_record_targets_without_reading_outside_content(self):
        secret = self.work / "outside.txt"
        secret.write_bytes(b"outside content must never appear")
        try:
            (self.repo / "outside-link").symlink_to(secret)
            (self.repo / "directory-link").symlink_to(self.work, target_is_directory=True)
            (self.repo / "missing-link").symlink_to("missing")
        except OSError as error:
            self.skipTest("Symlink creation unavailable: %s" % error)
        files, state = self.snapshot()
        self.assertEqual(set(files), {"project-state.json"})
        inventory = {entry["path"]: entry for entry in state["files"]}
        self.assertEqual(inventory["outside-link"]["target"], str(secret))
        self.assertEqual(inventory["directory-link"]["type"], "symlink")
        self.assertEqual(inventory["missing-link"]["target"], "missing")
        self.assertNotIn(secret.read_bytes(), b"".join(files.values()))

    def test_launcher_symlink_uses_script_repository_instead_of_working_directory(self):
        script = self.repo / "export.py"
        shutil.copyfile(PROGRAM, script)
        launcher = self.work / "launcher"
        try:
            launcher.symlink_to(script)
        except OSError as error:
            self.skipTest("Symlink creation unavailable: %s" % error)
        self.file("correct.json", b'{}')
        result = self.cli("-o", self.output, program=launcher)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        with zipfile.ZipFile(self.output) as archive:
            self.assertIn("correct.json", archive.namelist())
            state = json.loads(archive.read("project-state.json"))
        self.assertEqual(state["repository"], str(self.repo.resolve()))

    def test_no_arguments_export_beside_scripts_and_ignored_snapshot_keeps_git_clean(self):
        script = self.repo / "export.py"
        shutil.copyfile(PROGRAM, script)
        self.file(".gitignore", b"/JSONIC-snapshot.zip\n")
        self.file("correct.json", b'{}')
        self.git("add", ".")
        self.git("commit", "-m", "Project with local export")
        output = self.repo / "JSONIC-snapshot.zip"
        for _ in range(2):
            result = self.cli(program=script)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
            self.assertEqual(result.stdout.decode().strip(), str(output))
            with zipfile.ZipFile(output) as archive:
                self.assertIn("correct.json", archive.namelist())
                self.assertNotIn("JSONIC-snapshot.zip", archive.namelist())
            self.assertEqual(self.git("status", "--porcelain"), b"")

    @unittest.skipUnless(os.name == "posix", "POSIX executable permission bits")
    def test_executable_permissions_are_recorded_and_preserved_in_zip(self):
        executable = self.file("run", b'#!/bin/sh\nexit 0\n')
        executable.chmod(0o755)
        _, state = self.snapshot()
        self.assertEqual(state["files"][0]["mode"], "0o755")
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(stat.S_IMODE(archive.getinfo("run").external_attr >> 16), 0o755)

    def test_errors_are_concise_and_keep_previous_snapshot(self):
        self.output.write_bytes(b"previous snapshot")
        for args in (
            ["--project", self.work / "missing"],
            ["--project", self.work],
            ["--project", self.repo, "-o", self.repo / ".git" / "bad.zip"],
            ["--project", self.repo, "-o", self.repo / "settings.json"],
        ):
            with self.subTest(args=args):
                result = self.cli("-o", self.output, *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"export.py: error:", result.stderr)
                self.assertNotIn(b"Traceback", result.stderr)
                self.assertEqual(self.output.read_bytes(), b"previous snapshot")
        self.file("project-state.json/original", b"preserve this directory")
        result = self.cli("--project", self.repo, "-o", self.output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"Reserved snapshot filename", result.stderr)
        self.assertEqual(self.output.read_bytes(), b"previous snapshot")


if __name__ == "__main__":
    unittest.main()
