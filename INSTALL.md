# Run or install JSONIC

JSONIC is the single Python executable named `jsonic`. It needs no extra
packages. Git is needed only for the project's update and export tools.

## Start without installing

From this project directory:

```bash
python3 jsonic --help
python3 examples/demo.py
```

You can copy `jsonic` to another computer and run it with Python there. Examples,
tests, and documentation are useful project files, not runtime dependencies.

## Optional Ubuntu command

To make `jsonic` available from any directory, copy it into your account's
command directory:

```bash
mkdir -p "$HOME/.local/bin" &&
install -m 755 jsonic "$HOME/.local/bin/jsonic" &&
"$HOME/.local/bin/jsonic" --help
```

If the command is not found, add this line to `~/.bashrc` and open a new terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

If Python is missing, install it with `sudo apt install python3`.
After updating the project and testing it, repeat the copy command above to
refresh the optional installed copy.

Removal is just deleting the copy you installed:

```bash
rm -- "$HOME/.local/bin/jsonic"
```

There is no installer, service, package manager integration, or uninstall
program. JSON documents and captured style files are separate from the command.

## Other computers

On macOS, use `python3 /path/to/jsonic input.jsonic --pretty`. On Windows, use:

```powershell
py C:\path\to\jsonic input.jsonic --pretty -o output.json
```

Install Python from [python.org](https://www.python.org/downloads/) if needed.
Use `-o` for file output so JSONIC controls the bytes it writes. Linux has been
verified; native macOS and Windows runs still need verification.

## Development ZIPs

A downloaded `JSONIC.zip` contains the project source. For a fresh copy, extract
it into an empty directory and run the commands above. `update.json` is only
an instruction for the local development updater: a commit message and explicit
file removals. It is not needed to run JSONIC and can be discarded after a
fresh extraction.

In an existing committed development repository, use `./update.py` rather
than extracting over local work. See [updates and snapshots](docs/updates.md).
