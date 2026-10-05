# Presenting JSONIC

## A two-minute demonstration

Run `python3 examples/demo.py` and explain the results:

1. **The problem:** configuration needs explanations, but existing tools expect
   ordinary JSON. A comment should survive an unrelated data edit.
2. **The mechanism:** capture comments and whitespace in a companion style
   file, then emit ordinary JSON. The next program needs no JSONIC integration.
3. **The useful edit:** Python's normal JSON library changes settings. Restoring
   the capture brings the presentation back around the new values.
4. **The array rule:** comments describe positions. Changed/reordered values
   keep positional notes, shortened arrays omit missing notes, and added
   positions do not receive invented comments.
5. **The deeper case:** nested configuration demonstrates keys, paths, arrays,
   removals, and value-type changes together.

Use [worked examples](examples.md) for slower walkthroughs and
[the test guide](testing.md) for the evidence.

## Engineering decisions worth discussing

- **Bytes rather than reserialization:** copy validated tokens so numbers and
  escapes survive. JSONIC does not turn `9007199254740993` into a machine float.
- **Explicit attachment rather than guessing:** paths and indices make behavior
  predictable after edits. The tool cannot know whether a comment is still true.
- **Separate presentation:** ordinary JSON software can operate without retaining
  comment-aware objects or metadata in its own data model.
- **Small scope:** one executable, no dependencies, explicit syntax and file
  behavior. Whole-file parsing trades streaming capacity for simpler code.
- **Independent checks:** exact expected bytes and decoded data supplement round
  trips, because round trips alone can conceal paired mistakes.

A note after a complete value and before its comma belongs to that entry:
`"setting": [] /* explanation */,`. Interior comments cannot survive replacing
that container with a scalar. New paths have no stored layout. External tools
can still discard number precision; restoration cannot reconstruct lost data.

## Claims to make accurately

JSONIC provides a complete capture → ordinary JSON → restore command-line
workflow with exact presentation recovery when tokens are unchanged. Separate
comment metadata and comment preservation are not unique inventions; competing
tools make different tradeoffs. See [the comparison](comparison.md).

Linux and the documented examples are exercised. Native macOS/Windows and
large-file throughput remain unverified. Describe these limits plainly.

## Résumé summary

> Built a dependency-free Python CLI that separates comments and formatting
> from JSON data and restores them after ordinary JSON processing; implemented
> byte-preserving parsing, deterministic key/index matching, atomic file output,
> and tests for exact round trips, structural edits, and failure behavior.
