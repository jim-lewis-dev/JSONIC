# Presenting JSONIC

JSONIC demonstrates a precise contract: preserve human explanations while
existing software processes ordinary JSON.

## A 60–90 second demonstration

Run `python3 examples/demo.py`, then point to three results:

1. **Setting changed, explanation retained.** “A configuration file documents
   why a setting exists. JSONIC captures those comments and spaces, exports
   ordinary JSON, and restores the presentation after Python changes the value.
   The consuming program needs no comment-aware integration.”
2. **Array behavior is deliberate.** “These comments describe priority slots.
   Reordering values keeps comments at their positions; shortening the array
   omits missing slots. New entries receive no invented presentation.”
3. **Limits are visible.** “The nested example changes values and structure.
   A field's outer note survives a type change; removed interior notes do not.
   Python normalizes a number's spelling, and JSONIC preserves what Python
   returned. It cannot recover information another program discarded.”

Finish with the evidence: unchanged tokens round-trip byte for byte; independent
expected documents and decoded JSON verify edited results. The demo leaves no
files behind. Use [worked examples](examples.md) for a slower walkthrough.

## Questions to prepare for

| Interview question | Answer grounded in the implementation |
| --- | --- |
| Why not just parse and serialize JSON? | That can change numeric spelling, precision, escapes, and formatting. The scanner validates syntax and copies value tokens as bytes; decoded object keys are used for matching. |
| How do you decide which comment belongs where? | Capture records gaps at structural paths. Object members match keys; array elements match indices. A note before the comma belongs to the current entry, regardless of its value's type. |
| Why a separate style file? | Ordinary JSON tools can rewrite data without preserving special in-memory objects. Applying the saved capture restores matching presentation afterward. |
| How do you know a round trip is correct? | Round trips alone can hide paired bugs. Tests also compare complete, independently specified output, decode edited JSON, exercise CLI failures, and check atomic-replacement failure cleanup. |
| What does atomic output guarantee? | A file is prepared in a temporary sibling and replaced after writing succeeds. Invalid input leaves existing output alone. This does not promise full metadata preservation or power-loss durability. |

[Design details](design.md) and [test evidence](testing.md) support these answers.

## Keep the claims precise

Hjson and comment-json also preserve comments; separate metadata is not unique.
JSONIC combines a complete file workflow with exact captured gaps, token
preservation, and explicit key/index rules. The [comparison](comparison.md)
describes measured differences without claiming universal superiority.

Comments can become outdated, new structure lacks captured indentation, and
missing entries remain in the saved capture until recapture. Parsing uses
whole-file buffers and recursion. Large-file throughput and native macOS/Windows
remain unverified; Linux and the runnable examples are exercised.

## Résumé summary

> Built a dependency-free Python CLI that restores JSON comments and formatting
> after ordinary JSON processing; implemented byte-preserving parsing,
> deterministic key/index matching, atomic file output, and tests covering exact
> round trips, structural edits, and failure behavior.
