# JSONIC

Strip comments from JSON, use the data, and restore its comments and formatting.
One executable, using the Python standard library.

```bash
./jsonic settings.jsonic                           # capture presentation
./jsonic settings.jsonic --strip -o settings.json   # JSON, keeping whitespace
./jsonic settings.jsonic --raw -o settings.json     # raw JSON
./jsonic settings.json --apply -o restored.jsonic   # restore presentation
```

`--raw`, `--mini`, and `--minified` are identical. Use `--help` for the CLI.
You can also run the executable as `python3 jsonic`.

## Files and operations

| Input / operation | Behavior |
| --- | --- |
| `.json` input | Strict UTF-8 JSON with unique object keys; comments are rejected. |
| `.jsonic` input | The same JSON tokens, with optional `//`, `/* ... */`, or `''' ... '''` comments between tokens. |
| No operation flag | Capture comments and whitespace into `<base>.jsonic.style`. |
| `--strip` | Remove comments; keep outside-comment whitespace and all line endings, including line endings inside block comments. |
| `--raw`, `--mini`, `--minified` | Remove comments and all whitespace outside strings. |
| `--apply [STYLE]` | Strip the input's presentation and restore the captured style. Default: `<base>.jsonic.style`. |
| `-o PATH` | Write to PATH. In capture mode, PATH receives the style; other modes write their result. |

Capture always replaces the previous style. Capturing fully raw JSON writes
`{}`, so comments removed before recapture do not come back. Capture never
writes a data file. Strip, raw, and apply go to stdout unless `-o` is given;
they do not update the style file.

Style files contain presentation only: gaps before/after tokens, keyed by
object names and array positions. There are no release or schema identifiers,
and no compatibility modes. Generate styles with this executable.

## Restoration rules

- Object-member styling follows the key at its current object path.
- Array-element styling follows the index, regardless of the value there.
- Missing keys and positions are ignored. Their comments are not relocated.
- New keys and positions without captured styling receive no invented style.
- Nested styling follows the same key/index path rules.
- Leading/trailing document presentation is restored. Presentation inside an
  empty container is restored when that container is still empty.

An array example:

```text
Capture:  [/* first */10,/* second */20]
Apply to: [99,88,77]
Result:   [/* first */99,/* second */88,77]

Apply to: [99]
Result:   [/* first */99]
```

Spacing and comments after the former last item also belong to that index;
they stay there if more items are added. There is no special array-tail rule.
For objects, text after a comma is before the next key, so it follows that key.

An unchanged token stream restores byte for byte. Changed values keep their
new token spellings and receive the captured gaps. This is not a pretty
printer: it does not guess indentation, associate comments with values,
recreate removed values, or undo token changes made by another program.

## Try the examples

These commands use a temporary directory for every generated file:

```bash
jsonic_demo_dir="$(mktemp -d)"
./jsonic examples/config.jsonic -o "$jsonic_demo_dir/config.jsonic.style"
./jsonic examples/config.jsonic --strip -o "$jsonic_demo_dir/config.json"
./jsonic "$jsonic_demo_dir/config.json" --apply -o "$jsonic_demo_dir/restored.jsonic"
cmp examples/config.jsonic "$jsonic_demo_dir/restored.jsonic"

./jsonic examples/priority-array.jsonic -o "$jsonic_demo_dir/array.jsonic.style"
printf '["disk","cache"]' > "$jsonic_demo_dir/array.json"
./jsonic "$jsonic_demo_dir/array.json" --apply
```

`config.jsonic` includes nested settings, Unicode, escaped strings, comment
delimiters inside strings, numeric spellings, unusual keys, and empty
containers. `priority-array.jsonic` makes the positional behavior visible.

## Errors and writes

Invalid syntax, trailing commas, duplicate keys, invalid UTF-8, missing files,
and file-write failures produce `jsonic: error: ...` on stderr and a nonzero
exit. No partial data is emitted. Invalid input leaves an existing `-o` file
unchanged. Excessive nesting is reported as an error.

Use `-o` for in-place raw, strip, or apply operations; output is fully computed
before replacement. Capture cannot overwrite its input, and apply cannot
overwrite its style. Existing output permission bits are preserved.

Keep the original annotated file or its captured style if you need its
comments later. Avoid shell redirection back into the input file: the shell
would truncate it before JSONIC can read it.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The suite covers exact round trips, fixed expected raw/stripped output,
changed values, reordered/growing/shrinking/empty arrays, missing object keys,
all comment forms, UTF-8 and line endings, lexical precision, generated
documents, CLI aliases, clean errors, empty recapture, and safe file writes.
The retained comprehensive raw fixture is a fixed expected output.
