# How JSONIC works

JSONIC separates the JSON data from its presentation. A companion
`.jsonic.style` file records comments and whitespace at structural addresses.
Other software edits ordinary JSON; applying the capture inserts presentation
at the addresses that still exist.

## One byte-oriented scanner

The scanner validates UTF-8, JSON strings, numbers, punctuation, literals, and
gaps between tokens. Comment markers inside strings are data. Numbers and
strings are copied as tokens, avoiding numeric conversion and escape rewriting.

| Operation | Behavior |
| --- | --- |
| Capture | Record gaps by path/key/index. Always replace the style file, even with an empty `{}` capture. |
| Raw | Emit the original JSON tokens without comments or outside whitespace. |
| Strip | Delete comment bytes, keeping outside whitespace and CR/LF bytes within comments. |
| Pretty | Emit original tokens with two-space indentation, LF, and a final newline. Empty containers stay inline. |
| Apply | Insert captured gaps at matching addresses, then validate the restored document. |

Capture writes presentation metadata, not a copy of the data. The other modes
never update that capture. All operations read whole files into memory and use
recursive traversal. Excessive nesting receives a clear error; this is not a
streaming parser. Large-file throughput remains unbenchmarked.

## Comment syntax

`.jsonic` accepts ordinary JSON plus these comments between tokens:

- `//` through the next CR/LF or end of file.
- `/* ... */` through the first closing delimiter.
- `''' ... '''` through the first closing delimiter.

Blocks can span lines and do not nest. Triple quotes mark comments, not string
values. `.json` accepts no comments. Neither extension enables trailing commas,
unquoted keys, alternative numbers, or other syntax extensions.

## Where presentation belongs

Object-member gaps belong to their key within the object's path. Arrays use
numeric positions, regardless of what values occupy those positions.
Nested containers follow the same structural address rules.

Put a member's inline note after its complete value and before its comma:

```jsonc
{
  "attempts": 3 /* Includes the first request. */,
  "enabled": true
}
```

That note belongs to `attempts`, even if its value changes type. After-comma
comments belong before the next entry. A line comment before a comma requires
the comma on a following line; a block comment is clearer for inline notes.

| Structural change | Restoration |
| --- | --- |
| Change a value or reorder object keys | Captured gaps follow the key at its path. |
| Reorder or replace array elements | Captured gaps stay at their indices. |
| Remove a key or shorten an array | Missing addresses receive nothing. No orphan footer is created. |
| Add a key or grow an array | New addresses have no captured comments or indentation. |
| Replace a container with a scalar | Outer member gaps survive; interior presentation has no address. |
| Keep an empty container empty | Its captured interior presentation returns. |

The gap after the former last array element remains at that index when the
array grows. New entries can therefore look compact. JSONIC does not infer
comment meaning or invent layout; edit the annotated file and recapture when
new structure needs presentation.

Paths use JSON Pointer escaping. An array index `0` and an object key `"0"`
can produce the same descendant address. Matching descendant presentation can
survive such an ancestor type change; container-specific gaps depend on the
current container kind. Renaming or moving a member changes its address.

Root-leading and root-trailing presentation is retained. Applying a capture
does not erase missing entries from it: if an address later returns, its saved
style can return. Capture again to replace the saved state. A removed comment
stays removed after recapturing the edited annotated document.

## Exactness and limits

An unchanged token stream restores the entire original document byte for byte,
including comment contents, tabs, blank-line spaces, line endings, number
spelling, and string escapes. JSONIC preserves the tokens it receives; it cannot
undo rounding, reordering, or normalization performed by external software.
Comments may become outdated when values change.

`--strip` preserves line endings, not the column widths occupied by removed
comments. Capture/apply is the operation for restoring the original appearance.

## Validation and file output

Input must be UTF-8, syntactically valid, and have unique object keys. Equivalent
escaped spellings count as duplicates. Uniqueness is an extra JSONIC integrity
rule: the [JSON standard](https://www.rfc-editor.org/rfc/rfc8259#section-4)
recommends it but its grammar permits duplicates. JSONIC rejects them because
key-based attachment would be ambiguous.

Output is computed before file writing. Invalid input leaves existing outputs
unchanged. Files are written through a temporary sibling and atomic replacement.
Existing POSIX mode bits are preserved; new files respect the process umask.
Output symlinks remain links and their targets are replaced. Owner/group, ACLs,
extended attributes, and hardlink identity are not explicitly preserved.
Atomic replacement is not a promise of power-loss durability.

Capture cannot overwrite its input, and apply cannot overwrite its style file.
Style files are generated captures. See [tests](testing.md) for the evidence
and [comparisons](comparison.md) for different approaches to commented JSON.
