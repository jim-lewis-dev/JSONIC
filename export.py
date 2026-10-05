#!/usr/bin/env python3
"""Export the current project files and local Git state for review."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import zipfile


SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".venv", "venv", ".tox", ".nox", "node_modules", "build", "dist",
}
STATE_NAME = "project-state.json"
SNAPSHOT_NAME = "JSONIC-snapshot.zip"


class ExportError(Exception):
    pass


def git(repo, *args, optional=False):
    result = subprocess.run(
        ["git", "--no-pager", "-c", "core.fsmonitor=false", "-C", str(repo), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
    )
    if result.returncode:
        if optional:
            return None
        raise ExportError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout.decode("utf-8", errors="replace")


def repository(path):
    path = path.expanduser().resolve()
    if not path.is_dir():
        raise ExportError("Repository directory does not exist: %s" % path)
    root = git(path, "rev-parse", "--show-toplevel")
    return Path(root.strip()).resolve()


def git_state(repo):
    head = git(repo, "rev-parse", "--verify", "HEAD", optional=True)
    branch = git(repo, "symbolic-ref", "--quiet", "--short", "HEAD", optional=True)
    diff_options = ("--binary", "--no-ext-diff", "--no-textconv", "--no-color")
    return {
        "repository": str(repo),
        "branch": branch.strip() if branch else None,
        "head": head.strip() if head else None,
        "recent_commits": git(repo, "log", "-8", "--format=%h %s").splitlines() if head else [],
        "status": git(repo, "status", "--porcelain", "--untracked-files=all"),
        "staged_diff": git(repo, "diff", "--cached", *diff_options),
        "unstaged_diff": git(repo, "diff", *diff_options),
    }


def project_paths(repo, output):
    def unreadable(error):
        raise error

    paths = []
    excluded = []
    for folder, directories, files in os.walk(repo, followlinks=False, onerror=unreadable):
        current = Path(folder)
        for name in sorted(directories):
            path = current / name
            if name in SKIP_DIRS or path.is_symlink():
                directories.remove(name)
                if name in SKIP_DIRS:
                    excluded.append(path.relative_to(repo).as_posix() + "/")
                else:
                    paths.append(path)
        for name in sorted(files):
            path = current / name
            relative = path.relative_to(repo).as_posix()
            if (name == ".git" or name == ".DS_Store" or
                    name.endswith((".pyc", ".pyo")) or path == output
                    or relative == SNAPSHOT_NAME):
                excluded.append(relative)
            else:
                paths.append(path)
    return sorted(paths), sorted(excluded)


def export(repo, output):
    output = output.expanduser()
    output = output.parent.resolve() / output.name
    if output.suffix.lower() != ".zip":
        raise ExportError("Output must be a .zip file")
    if ".git" in output.parts:
        raise ExportError("Output cannot be inside Git's internal directory")
    paths, excluded = project_paths(repo, output)
    state_path = repo / STATE_NAME
    if state_path.exists() or state_path.is_symlink():
        raise ExportError("Reserved snapshot filename already exists: %s" % STATE_NAME)
    state = git_state(repo)
    state["excluded"] = excluded
    state["files"] = []
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent, prefix=".export-", suffix=".zip", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in paths:
                    relative = path.relative_to(repo).as_posix()
                    info = path.lstat()
                    entry = {"path": relative, "mode": oct(stat.S_IMODE(info.st_mode))}
                    if stat.S_ISLNK(info.st_mode):
                        entry.update(type="symlink", target=os.readlink(path))
                    elif stat.S_ISREG(info.st_mode):
                        data = path.read_bytes()
                        entry.update(type="file", size=len(data), sha256=hashlib.sha256(data).hexdigest())
                        archive.writestr(zipfile.ZipInfo.from_file(path, relative), data,
                                         compress_type=zipfile.ZIP_DEFLATED)
                    else:
                        entry.update(type="special", included=False)
                    state["files"].append(entry)
                archive.writestr(STATE_NAME, json.dumps(state, indent=2, ensure_ascii=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    project = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    parser.add_argument("--project", type=Path, default=project,
                        help="project repository (default: this script's directory)")
    parser.add_argument("-o", "--output", type=Path,
                        help="snapshot ZIP (default: PROJECT/JSONIC-snapshot.zip)")
    args = parser.parse_args(argv)
    try:
        repo = repository(args.project)
        output = export(repo, args.output or repo / SNAPSHOT_NAME)
        print(output)
        return 0
    except (ExportError, OSError, ValueError, zipfile.BadZipFile) as error:
        print("export.py: error: %s" % error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
