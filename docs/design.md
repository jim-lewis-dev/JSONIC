# How JSONIC works

JSONIC separates **what the data says** from **how the file is presented**.
The data goes to ordinary JSON software. A companion `.jsonic.style` file
remembers the comments and whitespace so JSONIC can restore them afterward.

## The mechanism

The scanner reads UTF-8 bytes and recognizes strings, numbers, punctuation,
literal values, and gaps between tokens. It understands quoted strings, so a
URL or the text `/* example */` inside a string is never mistaken for a comment.

- **Capture** validates the document and records its gaps by object path,
  member key, and array position. It writes presentation metadata, not data.
- **Raw** validates the document and emits its original JSON tokens, removing
  gaps. Numbers and strings are copied, not decoded and serialized again.
- **Strip** validates the document and removes comment bytes, retaining
  whitespace outside comments and CR/LF bytes inside them.
- **Apply** validates the new data and inserts saved gaps at matching locations.
  It validates the resulting annotated document before emitting it.

These operations share one scanner and grammar. The implementation reads
whole files into memory and uses recursive traversal. It is intended for
configuration and similar documents; excessive nesting gives a clear error.
Large-file throughput has not been benchmarked.

## Exact attachment rules

The supported comments are `//` through the next CR/LF or end of file,
`/* ... */`, and `''' ... '''`. Both block forms can span lines and end at
their first closing delimiter; comments do not nest. Markers inside JSON
strings are ordinary data. `#`, `<!-- ... -->`, and other comment forms are
not supported. Triple single quotes denote comments here, not string values.

Object-member gaps surround the key, colon, and value, keyed by the member's
name within its object path. Text after a comma belongs before the next key.
Renaming or moving a member changes that path; it is not identity matching.

A useful convention is to put an entry's inline explanation after its complete
value and before its comma:

```jsonc
{
  "attempts": 3 /* Includes the first request. */,
  "enabled": true
}
```

That block comment belongs to `attempts`. Putting it after the comma would
attach it to `enabled`. A `//` comment can occupy the same gap only if the
comma appears on a following line, so `/* ... */` is clearer for inline notes.
Comments around a field stay when its value changes type. Only presentation
inside removed descendants has no matching location to restore.

Array gaps belong before and after an element at its numeric position. If
elements move, the comments stay at the positions. If the array gets shorter,
absent positions receive nothing. If it grows, old positions retain their
gaps, including any gap after the former last element. New positions have
no captured indentation or comments.

Nested objects and arrays use the same path rules. Document-leading and
document-trailing presentation is retained. Presentation inside an empty
container applies when that container is still empty. Replacing a container
with a scalar cannot retain presentation that was inside that container.

Applying a style does not erase its saved entries. If a missing key or
position later returns and you apply the same capture, its old style can
return too. Capture again to replace the saved presentation with the current
annotated document. An empty capture writes `{}`, preventing stale comments
from surviving a fresh capture.

## What exact restoration means

An unchanged token stream restores byte for byte: spaces, tabs, newlines,
comments, number spelling, and string escapes. JSONIC preserves the token
spellings presented to it; it cannot reverse rounding, reordering, or escape
normalization performed by a different JSON program.

Restoration is deterministic, not semantic. A comment can become outdated if
its value changes. Newly inserted structure can look compact because no style
exists for it. Edit and recapture when you want a new presentation.

`--strip` preserves line endings, not original comment-column widths: deleting
an inline block comment shifts later text left. Use capture/apply when you
need the original appearance back.

## Errors and file writes

Input must be syntactically valid, use UTF-8, and have unique object keys.
`.jsonic` permits the documented comments; it does not enable trailing commas,
unquoted keys, or alternative number syntax.

Unique keys are an additional JSONIC rule. [The JSON standard](https://www.rfc-editor.org/rfc/rfc8259#section-4)
says names should be unique; its grammar permits duplicates, but implementations
may keep the last value, reject the object, or retain every pair. JSONIC rejects
duplicates to avoid silent data loss and ambiguous key-based style matching.
Escaped spellings of the same decoded key count as duplicates.

Output is computed before it is written. File output uses a temporary file in
the destination directory, flushes it, then replaces the destination. Invalid
input does not overwrite an existing output. POSIX permission bits are retained.
Capture refuses to overwrite its input, and apply refuses to overwrite its
style file. Style files are intended to be generated by JSONIC.

## Related tools

The following comparison describes the linked projects' interfaces and our
tested integration paths. Comment preservation and separate metadata are not
unique to JSONIC. See the [detailed comparison](comparison.md) for whitespace,
arrays, structural edits, validation, and practical costs.

| Tool | Documented approach | Relationship to JSONIC |
| --- | --- | --- |
| [strip-json-comments](https://github.com/sindresorhus/strip-json-comments) | Removes comments, optionally substituting whitespace. | Covers removal; JSONIC also captures and restores presentation. |
| [JSON5](https://json5.org/) | Adds comments and other syntax conveniences; exposes parse/stringify on values. | Broader authoring syntax. JSONIC retains ordinary JSON syntax except comments. |
| [jsonc-parser](https://github.com/microsoft/node-jsonc-parser) | Scans, parses, formats, and applies targeted edits to commented JSON text. | Useful for editing the annotated source directly. |
| [Hjson](https://github.com/hjson/hjson-js) | Offers round-trip comments and exported comment extraction/merge functions. | Can restore separately saved comments after ordinary JSON processing; formatting and missing-path policies differ. |
| [comment-json](https://github.com/kaelzhang/node-comment-json) | Retains comments in enriched JavaScript objects and supports comment-aware operations. | A recursive adapter can transfer comments onto fresh JSON using its helpers; exact original whitespace is not recorded. |

JSONIC supplies the complete capture/process/restore file workflow. Another
program can rewrite ordinary JSON without participating in comment preservation;
JSONIC then reapplies exact captured gaps under explicit path and position
rules, skipping absent locations and inventing no new presentation.

## Why this is an engineering project

The difficult work is preserving syntax while changing presentation, defining
what survives structural edits, and making failures predictable. Tests check
exact expected bytes, ordinary JSON edits, missing keys, reordered and shortened
arrays, comment-like strings, UTF-8, numeric spelling, and file replacement.
Generated cases supplement fixed examples; they do not replace them.
