# JSONIC, Hjson, and comment-json

**Choose by workflow and preservation rules.** All three can keep comments.
JSONIC supplies capture → ordinary JSON processing → restoration. Hjson makes
configuration easier to write. comment-json provides comment-aware JavaScript
objects and array operations.

The findings below come from source inspection and 99 Hjson / 91 comment-json
observations on October 3, 2026. They describe the tested JavaScript packages,
not every Hjson implementation or future release. Here, comment-json means the
[npm JavaScript project](https://github.com/kaelzhang/node-comment-json), not
Python's similarly named library.
The automated suite in this repository verifies JSONIC only; these comparisons
are dated research findings, not a maintained benchmark of the other tools.

## Features that matter

| Requirement | JSONIC | Hjson for JavaScript | comment-json |
| --- | --- | --- | --- |
| Exact unchanged source restoration | Yes, with unchanged data tokens and saved style | No general byte guarantee | Some conventional layouts; no general byte guarantee |
| Tabs, punctuation spacing, exterior whitespace | Captured exactly | Regenerated | Regenerated |
| Blank lines | Exact | Some comment-associated lines | Interior blank lines retained in tested cases |
| Array comments | Position and nested path | Outer positions; nested objects can carry their own metadata | Depends on mutation method |
| External ordinary JSON processing | Built-in capture/apply | Exported comment extraction/merge | Comment-transfer adapter possible |
| Relaxed data syntax | Comments only; unique keys required | Optional punctuation, unquoted strings/keys, and more | Comments and trailing commas |
| Runtime | Python standard library | Node/browser; no runtime package dependencies in tested package | JavaScript; two direct dependencies in tested package |

## Presentation and data fidelity

JSONIC records gaps around keys, colons, values, and array elements. Hjson and
comment-json generate output formatting. Uniform formatting is useful, but it
cannot reproduce arbitrary original indentation, spaces, or line endings.
comment-json preserves more blank-line structure than a simple pretty-printer;
that still differs from preserving every whitespace byte.

For example, Hjson round-tripping `[1/* first */,2/* last */]` dropped the first
comment in our test. It also dropped comments around object colons. JSONIC
retains these supported gaps. comment-json retained comments across those kinds
of gaps, while normalizing their layout.

JSONIC copies tokens such as `1.00E+01`, `-0`, and `9007199254740993`. Default
JavaScript parse/serialize workflows normalized the first two and rounded the
large integer. comment-json can preserve numeric source text with an explicit
source-aware reviver; that requires integration and changes how values are
represented. It also preserved unchanged nested string escapes in pretty
output, so it would be inaccurate to say it normalizes every string.

JSONIC cannot undo rounding or escape changes already made by another program.
Its `--pretty` formats clean JSON while retaining the tokens it receives;
`--strip` removes comments while retaining outside whitespace and line endings.
Neither operation restores an earlier data value.

## Arrays and missing data

With captured `[/* first */10,/* second */20]`, JSONIC restores `[99,88,77]` as:

```jsonc
[/* first */99,/* second */88,77]
```

A shorter `[99]` receives only the first comment. New indices get no invented
style. Reapplying the same capture after regrowth can restore old positions;
a fresh capture replaces that saved state.

| Operation | Hjson direct round-trip | comment-json |
| --- | --- | --- |
| Replace an element directly | Comment stays at index | Same |
| Reverse/sort | Outer comments stay at indices | Comments move with elements |
| Insert/remove using array methods | Outer comments remain positional | Aware methods generally shift comments with elements |
| Truncate through `length`, then regrow | Stored index comments can return | Same |
| Replace with freshly parsed JSON | Attached metadata is lost | Attached metadata is lost |

Nested object comments can travel with object references in both libraries.
JSONIC consistently uses the resulting path. comment-json's direct assignments,
`fill`, and `copyWithin` remain positional; generic copying and methods such as
`map` can lose comment metadata. Its behavior is not universal identity tracking.

JSONIC has a deliberate attachment tradeoff: everything after a comma belongs
to the next member's preceding gap. In `"a":1, /* about a */ "b":2`, deleting
`a` leaves that comment before `b`. It does not infer what the prose describes.
Missing keys receive no style; interior comments cannot survive a vanished
container. See [exact rules](design.md).

## Separate metadata is not unique

Hjson exports `comments.extract` and `comments.merge`: comments can be saved
separately and merged onto processed JSON. In our tests, absent-path comments
were appended under an orphan footer. JSONIC instead skips absent locations.
Hjson's extraction route also lost some root-only and empty-array comments.

A recursive adapter using comment-json's `moveComments` restored comments onto
fresh JSON by matching keys and indices in our tests. These helpers consume
source metadata; repeated independent restorations need reparsing or retained
copies. Neither adapter recovers whitespace the parser never recorded.

## Practical costs and choosing

Hjson suits human-owned configuration with relaxed syntax. comment-json suits
applications already doing their editing in JavaScript. Both are MIT-licensed,
with no purchase required; adopting either avoids maintaining a custom parser.

JSONIC suits existing JSON processors that should remain unaware of comments.
Its costs are keeping an annotated source or style file, maintaining its parser
and tests, and accepting that newly added structure has no saved presentation.
Restoration may therefore look uneven until edited and recaptured.

There is no demonstrated speed advantage. JSONIC reads whole documents and
uses recursive traversal. The alternatives are small libraries; their calling
applications own file writes and permissions. JSONIC supplies file handling,
which is an integration benefit rather than a parser-quality comparison.

## Methods and references

The comparison exercised unchanged output, ordinary edits, array mutations,
missing keys, external JSON serialization, whitespace, and token spelling.
Hjson used `rt.parse`/`rt.stringify`, including `{quotes: 'all', separator: true}`;
comment-json used `parse`/`stringify(value, null, 2)`. Its unindented
`stringify(value)` deliberately emits clean JSON.

Try JSONIC's checked examples and tests:

```bash
python3 examples/demo.py
python3 -m unittest discover -s tests -v
```

Primary references: [Hjson API](https://github.com/hjson/hjson-js),
[syntax](https://hjson.github.io/syntax.html),
[extraction/merge source](https://github.com/hjson/hjson-js/blob/master/lib/hjson-comments.js),
and [comment-json API](https://github.com/kaelzhang/node-comment-json).
