# Install JSONIC

JSONIC is the single file named `jsonic`. It uses Python and its standard
library; there is nothing to install with pip. The examples, tests, and docs
are useful when evaluating it, but are not runtime dependencies.

## Ubuntu and Raspberry Pi OS

Install Python if it is missing:

```bash
sudo apt update && sudo apt install python3
```

After downloading `JSONIC.zip` into Downloads, extract it and check it:

```bash
mkdir -p "$HOME/projects/jsonic" &&
python3 -m zipfile -e "$HOME/Downloads/JSONIC.zip" "$HOME/projects/jsonic" &&
rm "$HOME/projects/jsonic/update.json" &&
cd "$HOME/projects/jsonic" &&
python3 -m unittest discover -s tests -v &&
python3 examples/demo.py
```

If you already have the project, change into that directory instead. To make
the command available to your account, run there:

```bash
mkdir -p "$HOME/.local/bin" &&
install -m 755 jsonic "$HOME/.local/bin/jsonic" &&
"$HOME/.local/bin/jsonic" --help
```

If `jsonic --help` says the command cannot be found, add this line to
`~/.bashrc`, then open a new terminal:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

You can also run `python3 /path/to/jsonic input.jsonic --raw` directly.
Git is only needed if you want to work on the source or obtain it by cloning.

## macOS

Install Python from [python.org](https://www.python.org/downloads/macos/) if
`python3` is unavailable. Extract the archive, then run the same test, demo,
and `install` commands above from its directory. Put the PATH line in
`~/.zshrc` if you use the default zsh shell.

## Windows

Install Python using the [official Windows instructions](https://docs.python.org/3/using/windows.html).
Extract the downloaded archive with an archive tool, open a terminal in the
extracted directory, and run:

```powershell
py jsonic --help
py -m unittest discover -s tests -v
py examples/demo.py
py jsonic examples/settings.jsonic --raw -o settings.json
```

Use `py C:\path\to\jsonic input.jsonic --raw -o output.json` from elsewhere.
The file does not need a `.py` extension. Prefer `-o` to shell redirection so
JSONIC writes the exact bytes itself.

The archive's `update.json` is only used by the development updater; it can be
discarded when installing by hand.

## Another computer, updates, and removal

- **Copy:** move the project archive, or just `jsonic`, to any computer with
  Python. No account, network access, or extra packages are needed at runtime.
- **Update:** replace the executable and rerun the tests. For a user-level
  installation, rerun the same `install` command. Keep code, docs, and tests
  together when changing the project.
- **Remove:** delete `$HOME/.local/bin/jsonic`, or the copy you placed elsewhere.
  Your data and style files are independent of the installation.

The current code and demo have been exercised on Linux. The Windows-only
missing-permission-API case is covered by a simulated test; actual Windows and
macOS runs remain to be checked. Existing POSIX permission bits are preserved
when replacing files; Windows ACL preservation is not a feature promise.

This project is distributed directly as source. The `jsonic` package on npm
belongs to an [unrelated project](https://github.com/jsonicjs/jsonic).

For the existing development repository, use [the one-command ZIP update
workflow](docs/updates.md). It preserves Git history and commits each update.
Updater integration tests require POSIX and Git; they are skipped elsewhere.
