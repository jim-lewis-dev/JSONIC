# JSONIC

**JavaScript Object Notation with Integrated Comments.**

**Write comments beside your JSON. Use ordinary JSON tools. Bring the comments back.**

JSONIC saves comments and formatting separately from the data. Your existing
program can read and update normal JSON; JSONIC then puts the saved presentation
around the updated values. One Python executable. No third-party dependencies.

## See it work

Write `settings.jsonic`:

```jsonc
{
  // Total attempts, including the first request.
  "attempts": 3,
  "enabled": true
}
```

Capture its presentation, then produce ordinary JSON:

```bash
python3 jsonic settings.jsonic
python3 jsonic settings.jsonic --raw -o settings.json
```

The first command creates `settings.jsonic.style`, a companion file containing
the comments, whitespace, and where they belong. The second produces:

```json
{"attempts":3,"enabled":true}
```

Let any JSON tool change `attempts` to `5` in `settings.json`. Then restore:

```bash
python3 jsonic settings.json --apply -o restored.jsonic
```

```jsonc
{
  // Total attempts, including the first request.
  "attempts": 5,
  "enabled": true
}
```

**The new data stays. The saved comments and formatting return.**
Without changes to the data tokens, the complete file returns byte for byte.

## Try it now

From the downloaded project directory:

```bash
python3 examples/demo.py
```

The demo performs a real JSON edit, shows the restored result, demonstrates a
shortened array, and checks exact restoration of the complex example. It uses
temporary files and leaves the examples untouched. On Windows, use `py` in
place of `python3`.

[Install on Ubuntu, macOS, or Windows](INSTALL.md).

## Everyday commands

With the command installed on Ubuntu or macOS, use the commands below.
Otherwise run `python3 jsonic ...`, or `py jsonic ...` on Windows.

| Command | Result |
| --- | --- |
| `jsonic settings.jsonic` | Save presentation to `settings.jsonic.style`. |
| `jsonic settings.jsonic --strip` | Remove comments, keeping surrounding whitespace and line endings. |
| `jsonic settings.jsonic --raw` | Remove comments and all whitespace outside strings. |
| `jsonic settings.json --apply` | Restore presentation from `settings.jsonic.style`. |
| `jsonic settings.json --apply other.style` | Restore from an explicitly chosen style file. |

`--mini` and `--minified` are aliases for `--raw`. Add `-o PATH` to write a
result; strip, raw, and apply otherwise write to the terminal. In capture mode,
`-o` chooses the style file. Capture must happen **before** comments are removed.

## Predictable restoration

- **Object comments follow keys** within the same object path.
- **Array comments follow positions**, even when the values change or reorder.
- Missing keys or positions do not receive comments. Their comments are not moved.
- New keys or positions have no saved presentation; JSONIC invents none.
- Capturing again replaces the saved presentation, including an empty capture.

```text
Captured: [/* first */10,/* second */20]
New data: [99,88,77]
Restored: [/* first */99,/* second */88,77]

New data: [99]
Restored: [/* first */99]
```

JSONIC preserves token spellings such as `1.00E+03` and `"\u0061"`. It does not
undo changes another program makes to those spellings, infer comment meaning,
or pretty-print new entries. [Exact rules and design](docs/design.md).

## Valid input, clear failures

`.json` accepts UTF-8 JSON with unique object keys. `.jsonic` accepts the same
syntax plus `//`, `/* ... */`, and `''' ... '''` comments between tokens.
Strings containing comment markers remain data.

Invalid syntax, trailing commas, duplicate keys, and invalid UTF-8 produce a
clear error and a nonzero exit. Invalid input leaves an existing output file
unchanged. Use `-o` for in-place operations; do not redirect the shell back into
the input file. Keep the annotated source or its style file for restoration.

## Examples and tests

| Example | What it shows |
| --- | --- |
| [settings.jsonic](examples/settings.jsonic) | A small, useful configuration with an explanatory comment. |
| [priority-array.jsonic](examples/priority-array.jsonic) | Comments describing first, second, and third positions. |
| [config.jsonic](examples/config.jsonic) | Nested settings, routes, Unicode, escaped strings, exact number spellings, and empty containers. |

```bash
python3 -m unittest discover -s tests -v
```

Tests cover exact bytes, changed values, structural edits, all comment forms,
clean failures, file replacement, 300 generated documents, and a thousand
commented records. Linux execution is verified; native macOS and Windows runs
remain to be verified.

## Where it fits

Use JSONIC when humans maintain annotated configuration and existing software
expects ordinary JSON. Its separate style file carries presentation through
that workflow without changing the consuming program.

Other projects also preserve comments. JSONIC's focus is **capture → process
ordinary JSON → restore**, with explicit key and position rules.
[Detailed comparison with Hjson and comment-json](docs/comparison.md).

[What changed and the permission tradeoffs](docs/changes.md) ·
[Apply and commit a downloaded update](docs/updates.md).

To share your project's actual files and Git state for review, run
`python3 jsonic-export` from the project directory, then attach
`~/Downloads/JSONIC-snapshot.zip`. The export includes local edits and useful
untracked files without changing the repository. [Export details](docs/updates.md#share-the-current-project).
