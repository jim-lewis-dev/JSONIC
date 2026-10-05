# Updates and snapshots

Both executable utilities live inside the project. From its directory:

```bash
./update.py
./export.py
```

`update.py` reads `~/Downloads/JSONIC.zip`, applies it, commits locally, then
removes the downloaded ZIP. `export.py` writes `JSONIC-snapshot.zip` **inside
the project**, replacing the previous snapshot. It is ignored by Git.
The defaults follow the scripts' project, not the terminal's working directory.

## Apply an update

Download `JSONIC.zip` into Downloads and run:

```bash
cd ~/projects/dont_fucking_waste_my_time_JSONIC &&
./update.py
```

The repository needs an existing commit and configured Git author identity.
**Any nonignored staged, unstaged, or untracked work stops the update**, including
unrelated files. Commit, discard, or move that work yourself before retrying.
The updater never creates a checkpoint commit, stashes work, or resets it.

Tests run afterward, when you choose:

```bash
python3 -m unittest discover -s tests -v &&
python3 examples/demo.py
```

`git show --stat` summarizes the committed change. A missing default download
reports “No update waiting.” An identical ZIP is removed without an empty
commit; an explicitly named missing ZIP is an error.

## Share the actual project

```bash
./export.py
```

Attach `~/projects/dont_fucking_waste_my_time_JSONIC/JSONIC-snapshot.zip`.
Export can capture local edits, untracked files, and useful ignored
configuration/style files. `project-state.json` records Git state, diffs,
file hashes, and permissions. Git internals, generated caches/build outputs,
and the snapshot itself are excluded; symlinks are recorded without copying
their targets.

Export does not stage, commit, run tests, or change project files. Review any
private configuration before sharing. A snapshot is for review, not input to
`update.py`.

## Other locations

```bash
./update.py /path/to/JSONIC.zip --project /path/to/project
./update.py --downloads /path/to/downloads
./export.py --project /path/to/project -o /path/to/JSONIC-snapshot.zip
```

Without `-o`, export always writes inside the selected project. Normal JSONIC
use needs neither these utilities nor Git; they support local development.

## What an update contains

`update.json` has two fields:

```json
{"message":"Make JSONIC easier to use","remove":[]}
```

`message` supplies the commit message; `remove` names deliberate file deletions.
The updater consumes this file rather than installing it. It is unrelated to
comment style files. Other ZIP entries are complete replacement files; omitted
paths remain unchanged. Scripts receive executable permissions.

The archive is checked before application. It cannot replace Git internals,
escape the project, or write through an existing symlink. Ignored local files
also cannot be overwritten or deleted by a packaged path. Existing history
remains; nothing is pushed.

If writing or committing fails, the ZIP stays and applied files may remain.
Inspect `git status` before retrying. Each file replacement is atomic; the
whole update is not one transaction. If only ZIP deletion fails after a commit,
remove the ZIP yourself or rerun the updater.

## Start using the renamed tools

If this project still has `jsonic-update`, apply the downloaded change once:

```bash
python3 jsonic-update
```

That update installs `update.py` and `export.py` as executable files and removes
the old project commands. Subsequent updates use `./update.py`.

If no updater is present, this bootstrap applies the ZIP to an **existing,
committed repository**:

```bash
python3 - <<'BOOTSTRAP'
from pathlib import Path
from zipfile import ZipFile
import sys

project = Path.home() / "projects" / "dont_fucking_waste_my_time_JSONIC"
with ZipFile(Path.home() / "Downloads" / "JSONIC.zip") as package:
    source = package.read("update.py")
sys.argv = ["update.py", "--project", str(project)]
exec(compile(source, "update.py", "exec"), {"__name__": "__main__"})
BOOTSTRAP
```

For a fresh ordinary installation, follow [INSTALL.md](../INSTALL.md).

## Remove the old launcher and snapshot

After the new exporter succeeds, this removes the known old launcher symlink
and Downloads snapshot. It leaves the installed `jsonic` command alone:

```bash
./export.py &&
if [ "$(readlink "$HOME/.local/bin/jsonic-update")" = \
     "$HOME/projects/dont_fucking_waste_my_time_JSONIC/jsonic-update" ]; then
    rm -- "$HOME/.local/bin/jsonic-update"
fi &&
rm -f -- "$HOME/Downloads/JSONIC-snapshot.zip"
```

The maintenance utilities require Python and Git and target the local
Ubuntu/POSIX development workflow.
