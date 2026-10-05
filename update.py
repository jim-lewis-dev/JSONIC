#!/usr/bin/env python3
"""Apply JSONIC.zip to the local repository, commit it, then remove the ZIP."""

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import stat
import subprocess
import sys
import tempfile
import zipfile


class UpdateError(Exception):
    pass


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
    )
    if result.returncode:
        raise UpdateError(result.stderr.strip() or result.stdout.strip() or "Git failed")
    return result.stdout.strip()


def safe_name(name):
    path = PurePosixPath(name)
    if (not name or "\\" in name or path.is_absolute()
            or any(part in ("", ".", "..", ".git") for part in name.split("/"))
            or ":" in name or "\0" in name):
        raise UpdateError("Unsafe archive path: %r" % name)
    return name


def destination(repo, name):
    target = repo / safe_name(name)
    for part in (target, *target.parents):
        if part == repo:
            break
        if part.is_symlink():
            raise UpdateError("Update path is a symlink: %s" % part)
    if target.exists() and not target.is_file():
        raise UpdateError("Update path is not a regular file: %s" % target)
    return target


def read_update(archive):
    files = {}
    with zipfile.ZipFile(archive) as package:
        for info in package.infolist():
            if info.is_dir():
                continue
            name = safe_name(info.filename)
            if name in files:
                raise UpdateError("Duplicate archive path: %s" % name)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise UpdateError("Archive contains a symlink: %s" % name)
            files[name] = (package.read(info), 0o755 if mode & 0o111 else 0o644)

    if "update.json" not in files:
        raise UpdateError("ZIP is missing update.json")
    metadata = json.loads(files.pop("update.json")[0])
    if not isinstance(metadata, dict):
        raise UpdateError("update.json must contain an object")
    message = metadata.get("message")
    remove = metadata.get("remove", [])
    if not isinstance(message, str) or not message.strip():
        raise UpdateError("Update needs a nonempty commit message")
    if not isinstance(remove, list) or any(not isinstance(name, str) for name in remove):
        raise UpdateError("Update removals must be a list of file paths")
    for name in remove:
        safe_name(name)
        if name == "update.json" or name in files:
            raise UpdateError("Conflicting update path: %s" % name)
    if not files and not remove:
        raise UpdateError("Update contains no project files")
    return files, list(dict.fromkeys(remove)), message.strip()


def write_file(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def apply_update(repo, archive):
    repo = repo.expanduser().resolve()
    archive = archive.expanduser().resolve()
    files, remove, message = read_update(archive)
    if Path(git(repo, "rev-parse", "--show-toplevel")).resolve() != repo:
        raise UpdateError("Target must be the root of its own Git repository")
    git(repo, "rev-parse", "--verify", "HEAD")
    if git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise UpdateError("Repository has uncommitted or untracked work. Commit, remove, or ignore it, then run again.")
    git(repo, "var", "GIT_AUTHOR_IDENT")
    git(repo, "var", "GIT_COMMITTER_IDENT")

    # Check every destination before changing any project files.
    targets = {name: destination(repo, name) for name in [*files, *remove]}
    tracked = set(git(repo, "ls-files", "-z").split("\0"))
    for name, target in targets.items():
        if target.exists() and name not in tracked:
            raise UpdateError("Untracked update destination already exists: %s" % target)
        for parent in target.parents:
            if parent == repo:
                break
            if parent.exists() and not parent.is_dir():
                raise UpdateError("Update parent is not a directory: %s" % parent)
        if target == archive:
            raise UpdateError("Archive must not be an update destination")
    changed = []
    for name, (data, mode) in files.items():
        target = targets[name]
        if (not target.exists() or target.read_bytes() != data
                or stat.S_IMODE(target.stat().st_mode) != mode):
            changed.append(name)
    changed.extend(name for name in remove if targets[name].exists())
    if not changed:
        archive.unlink()
        print("Already applied. Removed the downloaded ZIP.")
        return

    print("Commit: %s" % message, flush=True)
    for name in changed:
        print("  %s %s" % ("remove" if name in remove else "write", name), flush=True)
    try:
        for name in changed:
            if name in files:
                data, mode = files[name]
                write_file(targets[name], data, mode)
            else:
                targets[name].unlink()
        git(repo, "add", "-A", "--", *changed)
        if git(repo, "diff", "--cached", "--name-only"):
            print(git(repo, "commit", "-m", message), flush=True)
        else:
            print("File modes refreshed; Git already has the same content.", flush=True)
    except (UpdateError, OSError):
        print("Update stopped while applying or committing files. The ZIP is retained.\n"
              "Inspect git status; finish or undo those changes before retrying.", file=sys.stderr)
        raise
    archive.unlink()
    print("Update is recorded in Git. Removed the downloaded ZIP.")
    print("Test it now: cd %s && python3 -m unittest discover -s tests -v" % shlex.quote(str(repo)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", type=Path)
    project = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    parser.add_argument("--project", type=Path, default=project,
                        help="project repository (default: this script's directory)")
    parser.add_argument("--downloads", type=Path, default=Path.home() / "Downloads",
                        help="download directory (default: ~/Downloads)")
    args = parser.parse_args(argv)
    archive = args.archive or args.downloads.expanduser() / "JSONIC.zip"
    if args.archive is None and not archive.exists():
        print("No update waiting. Download JSONIC.zip to %s, then run update.py." % archive.parent)
        return 0
    try:
        apply_update(args.project, archive)
    except (UpdateError, OSError, ValueError, zipfile.BadZipFile) as error:
        print("update.py: error: %s" % error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
