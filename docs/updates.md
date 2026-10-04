# One command to apply JSONIC updates

Every update is named **JSONIC.zip**. Download it to `~/Downloads` and run:

```bash
~/.local/bin/jsonic-update
```

The updater targets `~/projects/dont_fucking_waste_my_time_JSONIC`. It writes
the packaged project files, makes a local Git commit using the message included
with that change, and removes the downloaded ZIP after success. You then test
the committed code. It does not run tests for you or push anything.

## First-time setup

Download `JSONIC.zip` to Downloads, then paste this complete block once:

```bash
python3 - <<'PY' &&
from pathlib import Path
from zipfile import ZipFile

with ZipFile(Path.home() / "Downloads" / "JSONIC.zip") as package:
    source = package.read("jsonic-update")
exec(compile(source, "jsonic-update", "exec"), {"__name__": "__main__"})
PY
mkdir -p "$HOME/.local/bin" &&
ln -sfn "$HOME/projects/dont_fucking_waste_my_time_JSONIC/jsonic-update" \
    "$HOME/.local/bin/jsonic-update"
```

This applies and commits the first ZIP, then creates the command as a symlink
to the updater inside the project. Later ZIPs can update the tool itself.
The explicit `~/.local/bin/jsonic-update` command works regardless of PATH.

The existing repository must already have its initial commit and Git author
identity configured. The updater uses your existing identity and branch.

## Test afterward

```bash
cd ~/projects/dont_fucking_waste_my_time_JSONIC &&
python3 -m unittest discover -s tests -v &&
python3 examples/demo.py
```

Inspect the last change with `git show --stat` or `git show`. An identical
already-applied ZIP is removed without creating an empty commit.
Running the command again without a new download reports "No update waiting"
and makes no changes. An explicitly named missing archive remains an error.

## Share the current project

Run this from any directory:

```bash
~/projects/dont_fucking_waste_my_time_JSONIC/jsonic-export
```

Attach `~/Downloads/JSONIC-snapshot.zip` to the conversation. It contains the
current project files, including local edits, useful untracked files, and
ignored configuration/style files. Its `project-state.json` records the branch,
current commit, recent commit messages, status, staged/unstaged diffs, file modes,
and file hashes. Git's internal directory, caches, and build/dependency outputs
are excluded. Symlink targets are recorded without copying their contents.

The exporter does not stage, commit, run tests, or alter project files. It
replaces the previous snapshot. Project file contents are included, so inspect
any private configuration before sharing. This is a review snapshot, not an
update package; do not pass it to jsonic-update.

For another repository or destination:

```bash
python3 jsonic-export --repo /path/to/project -o /path/to/JSONIC-snapshot.zip
```

## What the updater changes

- The archive contains complete replacement files and an `update.json` message.
  That message file is consumed by the updater, not copied into the project.
- File removals must be named explicitly in its `remove` list. Unmentioned
  files are left alone; an absent ZIP entry does not mean deletion.
- Packaged scripts receive executable permissions; other packaged source files
  receive ordinary read permissions. This is source installation, separate from
  JSONIC's rules for writing your JSON data files.
- Only the update's file paths are staged. Unrelated untracked experiments and
  generated outputs remain untracked.
- Existing Git history stays in place. No backup directories, extra checkouts,
  remotes, pushes, or numbered downloads are created.

## If something stops

Uncommitted tracked changes stop the update before any files are changed.
Commit or undo those edits first. A packaged path also cannot overwrite or
delete an existing untracked file, including an ignored file.

The ZIP is checked before extraction; it cannot replace Git's internal files,
escape the project directory, or redirect a write through an existing symlink.

If writing or committing fails after application starts, the ZIP remains and
the tool reports that the repository may contain applied changes. Inspect
`git status` and finish or undo that work before retrying. There is no automatic
reset that could erase work you make while diagnosing a failure. A whole ZIP
is not one filesystem transaction; each file replacement is atomic.

If Git succeeds but deleting the ZIP fails, the commit remains successful.
Delete the download yourself or rerun the tool; it will recognize unchanged
content and avoid a second commit.

An alternative ZIP or repository can be named explicitly:

```bash
~/.local/bin/jsonic-update /path/to/JSONIC.zip --repo /path/to/project
```

This updater is for the local Ubuntu/POSIX development workflow and requires
Python and Git. It is independent of JSONIC's capture/strip/restore operation.
