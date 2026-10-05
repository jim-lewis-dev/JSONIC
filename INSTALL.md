# Install JSONIC

JSONIC needs Python and the single file named `jsonic`. No pip, extra packages,
account, or network connection is needed to run it.

## Ubuntu and Raspberry Pi OS

From the project directory, install the command for your account:

```bash
mkdir -p "$HOME/.local/bin" &&
install -m 755 jsonic "$HOME/.local/bin/jsonic" &&
"$HOME/.local/bin/jsonic" --help
```

Then use `jsonic input.jsonic --pretty`, for example. If `jsonic` is not found,
add the following line to `~/.bashrc` and open a new terminal. Running it in the
current terminal also makes the command available immediately:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

If Python is missing, install it first:

```bash
sudo apt update && sudo apt install python3
```

Starting with a downloaded ZIP on a new computer? Extract it first:

```bash
mkdir -p "$HOME/projects/jsonic" &&
python3 -m zipfile -e "$HOME/Downloads/JSONIC.zip" "$HOME/projects/jsonic" &&
rm -f "$HOME/projects/jsonic/update.json" &&
cd "$HOME/projects/jsonic"
```

Run the install block above from there. For the existing development repository,
run `./update.py` as described in [the update workflow](docs/updates.md).

## Run without installing

From the project directory:

```bash
python3 jsonic --help
python3 examples/demo.py
python3 -m unittest discover -s tests -v
```

From elsewhere, use `python3 /path/to/jsonic input.jsonic --raw -o output.json`.
The examples and tests are useful checks, but are not runtime dependencies.

## macOS and Windows

On **macOS**, install Python from [python.org](https://www.python.org/downloads/macos/)
if needed. The extraction and installation commands above also apply. Put the
PATH line in `~/.zshrc` if using zsh.

On **Windows**, install Python using the [official instructions](https://docs.python.org/3/using/windows.html),
extract the ZIP, and open a terminal in that directory:

```powershell
py jsonic --help
py examples/demo.py
py -m unittest discover -s tests -v
py jsonic examples/settings.jsonic --pretty -o settings.json
```

From elsewhere, use `py "C:\path\to\jsonic" input.jsonic --raw -o output.json`.
The executable needs no `.py` extension. Use `-o` so JSONIC writes exact bytes.
Linux is verified; native macOS and Windows runs remain unverified.

## Copy, update, remove

- **Another computer:** copy `jsonic`, or the whole project, and use Python there.
- **Update:** update the source, run its tests, and repeat the install block to
  replace the installed copy.
- **Remove:** delete `$HOME/.local/bin/jsonic`, or the copy placed elsewhere.
  Your JSON and style files remain independent.

A development ZIP may include `update.json` with two fields: `message` is the
local commit message; `remove` lists project files to delete explicitly. The
development updater consumes it. It is unrelated to `.jsonic.style` files,
is unnecessary at runtime, and can be discarded for a normal installation.

The executable `update.py` and `export.py` utilities stay in the project and
run directly from there. Export writes `JSONIC-snapshot.zip` beside them.

The unrelated npm package named `jsonic` is not this tool.
