# Presenting JSONIC

**JSONIC — JavaScript Object Notation with Integrated Comments.**

## A two-minute demonstration

Run `python3 examples/demo.py` from the project directory. Explain what appears:

1. **The problem:** “People need explanations beside configuration values,
   but their existing software expects ordinary JSON.”
2. **The separation:** “JSONIC saves comments and spacing in a companion style
   file, then produces ordinary JSON.”
3. **The edit:** “This step uses Python's normal JSON library to change a value.
   That program knows nothing about comments.”
4. **The restoration:** “The updated value stays; the saved presentation comes
   back. Unchanged data tokens restore the original file byte for byte.”
5. **The contract:** “Array comments belong to positions. Shortening the array
   omits comments for missing positions; it does not move them to the bottom.”

Use the complex example and test suite for follow-up questions. `--pretty`
offers readable ordinary JSON while preserving token spelling and order;
restoration uses the captured presentation.

## Eight concrete strengths

These observations refer to the implementations and workflows examined in
[the comparison](comparison.md), not every possible implementation. Some
differences reflect deliberate priorities rather than bugs.

| JSONIC behavior | Observed comparison |
| --- | --- |
| Exact spaces, tabs, blank-line spaces, line endings, and comment contents when tokens are unchanged. | Hjson and comment-json regenerate surrounding layout; comment-json also stripped blank-line spaces inside a block comment. |
| Comments in every supported gap, including key/colon, colon/value, and value/comma. | Hjson dropped comments in several tested gaps. |
| Number and string/key tokens copied without coercion, including `9007199254740993`, `-0`, and `1.00E+01`. | Default JavaScript workflows rounded or normalized numbers. comment-json can avoid numeric loss with its source-aware reviver. |
| Array styling always follows positions, including nested paths. | comment-json attachment depends on the mutation method. Hjson's exported metadata is also positional. |
| Absent keys and positions receive no comments or orphan appendix. | Hjson extract/merge appended orphan comments for tested missing paths. |
| Root scalar comments, headers/footers, and matching empty-container interiors restore. | comment-json lost root-null comments; Hjson had specific root/empty-array failures. |
| Invalid UTF-8 and invalid JSON syntax fail before replacing output. | Hjson accepts broader syntax and its tested CLI replaced invalid UTF-8; comment-json accepts trailing commas. Unique keys are JSONIC's additional integrity rule. |
| A complete capture → ordinary JSON → restore file workflow with no third-party dependencies. | Hjson already exports comment metadata; comment-json can transfer it through an adapter. JSONIC directly supplies the file workflow and exact-gap rules. |

## Be ready to explain

- **Why bytes:** copying validated tokens avoids numeric rounding and unwanted
  changes to escape sequences.
- **Why paths and positions:** predictable attachment works independently of
  how another program edits the data. It does not infer a comment's meaning.
- **Why a style file:** existing JSON programs need no comment-aware integration.
- **Why the scope stays small:** one executable, whole-file parsing, explicit
  rules, and tests comparing actual bytes. Large-file throughput is unbenchmarked.

Put a comment after its complete value and before the comma when it describes
that member: `"setting": [] /* explanation */,`. It stays with that member
at the same path even if the value changes type. Comments inside a replaced
container cannot follow a scalar; comments after a comma belong to the next entry.

External software can still round a number or rewrite string escapes. JSONIC
preserves what that software returns; it cannot recover discarded data.
Linux has been exercised; native macOS and Windows remain unverified.

## Résumé summary

> Built a Python CLI that separates comments and formatting from JSON data and
> restores them after ordinary JSON processing; implemented byte-preserving
> parsing, deterministic key/index matching, atomic file replacement, and tests
> covering exact round trips, structural edits, and generated documents.

The interview claim is **JSON syntax plus comments, with reversible
presentation**. Explain the exact contract and demonstrate it; comment
preservation and separate metadata are not unique inventions of this project.
