# JSONIC

**JavaScript Object Notation with Integrated Comments.**

Keep explanations beside JSON values. Let ordinary JSON software change the
data. Restore the comments and original formatting afterward.

One Python executable, no third-party dependencies. JSON syntax stays JSON;
`.jsonic` adds `//`, `/* ... */`, and `''' ... '''` comments between tokens.

## See it work

From the project directory:

```bash
python3 examples/demo.py
```

The demo edits settings with Python's normal JSON library, changes a positional
array, and updates a nested configuration. It shows before/after output and
checks the restored results. Everything it writes goes into a temporary directory.
See the [worked examples](docs/examples.md) for commands and expected behavior.

## The basic workflow

Save this as `settings.jsonic`:

```jsonc
{
  "attempts": 3 /* Total attempts, including the first request. */,
  "enabled": true
}
```

Capture its presentation, then produce ordinary JSON:

```bash
python3 jsonic settings.jsonic
python3 jsonic settings.jsonic --pretty -o settings.json
```

Capture creates `settings.jsonic.style`: comments, whitespace, and their
locations. Let any JSON program change `attempts` to `5` in `settings.json`.
Restore the saved presentation:

```bash
python3 jsonic settings.json --apply -o restored.jsonic
```

The value is now `5`, with its comment and spacing back in place. Capture
**before** removing comments and keep the style file. With unchanged data tokens,
the whole document restores byte for byte.

## Commands

Use `python3 jsonic FILE` with:

| Option | Result |
| --- | --- |
| None | Capture into `<base>.jsonic.style`, replacing the previous capture. |
| `--strip` | Remove comments; keep outside whitespace and all line endings. |
| `--raw`, `--mini`, `--minified` | Remove comments and whitespace outside strings. |
| `--pretty` | Emit comment-free JSON with two-space indentation and a final newline. |
| `--apply [STYLE]` | Restore the named capture, or `<base>.jsonic.style`. |

Use `-o PATH` for file output. Without it, conversions print to the terminal;
capture writes its style file. Only capture changes style metadata.

## Predictable restoration

- Object comments follow keys within their paths. Array comments follow indices,
  even when values change or reorder. Missing entries receive nothing.
- Put a member's note before its comma: `"attempts": 3 /* note */,`.
  After-comma comments belong to the next entry.
- New entries have no captured comments or indentation. Change the annotated
  document and recapture when you want to record a new presentation.
- JSONIC preserves the data tokens it receives. It cannot undo rounding or
  rewriting by another program. Comments can become outdated when data changes.

Input must be UTF-8 and valid JSON with unique object keys; `.jsonic` additionally
allows the documented comments. Invalid input produces a clear error, a nonzero
exit, and no replaced file output.

## Run, install, and verify

Run directly with Python, or [copy the optional command](INSTALL.md) into your
account's command directory. There is no installer or uninstall program.

```bash
python3 -m unittest discover -s tests -v
```

[What the tests prove](docs/testing.md) · [Exact rules](docs/design.md) ·
[Tool comparison](docs/comparison.md) · [Interview demo](docs/presenting.md)

For local project maintenance, `./update.py` applies a downloaded change and
`./export.py` writes `JSONIC-snapshot.zip` inside the project.
See [updates and snapshots](docs/updates.md).
