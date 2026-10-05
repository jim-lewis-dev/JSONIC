# Updates and snapshots

Both executable tools live in the project. From its directory:

```bash
./update.py
./export.py
```

The defaults follow the directory containing the scripts, even when called
from elsewhere. Normal JSONIC use needs neither utility nor Git.

## Apply a downloaded change

Download `JSONIC.zip` into `~/Downloads`, then run `./update.py`.
It validates the archive, applies the files, makes one local Git commit, and
removes the downloaded ZIP after success. Nothing is pushed.

The repository must have an existing commit and configured Git author identity.
Any nonignored staged, unstaged, or untracked work stops the update before
application, including unrelated files. Commit, remove, or move that work
yourself. The updater never checkpoints, stashes, or resets it.
An unfinished merge, rebase, cherry-pick, or revert also stops the update,
even if the working tree looks clean. Finish or abort that operation first.

Inspect and test the resulting commit:

```bash
git show --stat
python3 -m unittest discover -s tests -v
python3 examples/demo.py
```

A missing default download reports “No update waiting.” An identical update
is removed without an empty commit. An explicitly named missing ZIP is an error.

## Export the actual project

`./export.py` writes `JSONIC-snapshot.zip` beside the scripts, replacing the
previous snapshot. Git ignores this output, and exports exclude it.
Attach that ZIP when requesting work on the current project.

The snapshot includes working files, local edits, untracked files, and useful
ignored configuration/style files. `project-state.json` records Git status,
diffs, recent history, hashes, and permissions. Git internals, caches, and build
outputs are excluded. Symlink targets are recorded without copying their contents.

Export can capture uncommitted work. It does not stage, commit, run tests, or
modify source files. Review private configuration before sharing. A snapshot
is for review; it is not an update ZIP.

## Optional paths

```bash
./update.py /path/to/JSONIC.zip --project /path/to/project
./update.py --downloads /path/to/downloads
./export.py --project /path/to/project -o /path/to/snapshot.zip
```

Without `-o`, the snapshot always goes inside the selected project.

## What an update contains

`update.json` is consumed by the updater rather than installed:

```json
{"message":"Make JSONIC easier to use","remove":[]}
```

`message` is the commit message; `remove` lists deliberate file deletions.
Other entries are complete replacement files. Omitted paths stay untouched.
Executable permissions are taken from the archive. This metadata has nothing
to do with comment style captures.

Before writing, the updater rejects paths escaping the project, Git internals,
existing symlinks, and collisions with ignored local files. Existing history stays.

If a write or commit fails, the ZIP stays and applied files may remain. Inspect
`git status` before retrying. Individual replacements are atomic; the whole
update is not a transaction. If ZIP deletion alone fails after a commit, remove
the ZIP yourself or rerun the updater.

These maintenance utilities target the local Ubuntu/POSIX development workflow.
