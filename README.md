# JSONIC

**JavaScript Object Notation with Integrated Comments.**

Write comments beside your JSON. Let ordinary JSON tools change the data.
Restore the comments and formatting afterward. One Python executable; no
third-party dependencies.

## How it works

Save this as `settings.jsonic`:

```jsonc
{
  "attempts": 3 /* Total attempts, including the first request. */,
  "enabled": true
}
```

Capture the presentation, then produce readable, comment-free JSON:

```bash
python3 jsonic settings.jsonic
python3 jsonic settings.jsonic --pretty -o settings.json
```

The capture creates `settings.jsonic.style`: comments, whitespace, and their
locations. Let any JSON tool change `attempts` to `5` in `settings.json`. Restore:

```bash
python3 jsonic settings.json --apply -o restored.jsonic
```

The value is now `5`; its comment and original spacing return. With unchanged
data tokens, the whole file returns byte for byte. Capture **before** removing
comments, and keep the style file.

## Commands

Use `python3 jsonic FILE` with:

| Option | Result |
| --- | --- |
| None | Capture into `<base>.jsonic.style`, replacing any previous capture. |
| `--strip` | Remove comments; retain outside whitespace and all line endings. |
| `--raw`, `--mini`, `--minified` | Remove comments and whitespace outside strings. |
| `--pretty` | Remove comments; use two-space indentation, LF, and a final newline. |
| `--apply [STYLE]` | Restore the named style, or `<base>.jsonic.style`. |

Add `-o PATH` to write output; otherwise conversions print to the terminal.
For capture, `-o` chooses the style file. Only capture writes style metadata.
All conversions preserve data-token spelling and order.

## Restoration rules

- Objects match keys within their paths; arrays match positions, even after reordering.
- Missing entries receive nothing. New entries receive no invented presentation.
- `value /* comment */,` attaches to that member or position, including when
  its value changes type. After the comma, comments belong to the next entry.
- Presentation inside a removed container cannot follow a replacement scalar.

`.json` requires UTF-8 JSON with unique keys. `.jsonic` also permits `//`,
`/* ... */`, and `''' ... '''` comments between tokens. Invalid input produces
an error, a nonzero exit, and no replaced output. Use `-o` for in-place writes.

## Try it

[Install](INSTALL.md), then run from the project directory:

```bash
python3 examples/demo.py
python3 -m unittest discover -s tests -v
```

On Windows, use `py` instead of `python3`.

Examples: [simple](examples/settings.jsonic), [positional array](examples/priority-array.jsonic),
[complex](examples/config.jsonic).

Project maintenance: `./update.py` applies a downloaded update; `./export.py`
writes `JSONIC-snapshot.zip` inside the project for review.

[Exact rules](docs/design.md) · [Tool comparison](docs/comparison.md) ·
[Interview demo](docs/presenting.md) · [Updates and snapshots](docs/updates.md).
