# JSONIC, Hjson, and comment-json

**All three can preserve comments. They preserve different things, and their
editing rules differ.** JSONIC is designed for an existing program that reads
and rewrites ordinary JSON, followed by restoration of the saved presentation.
Hjson offers a more forgiving configuration language. comment-json offers
comment-aware JavaScript objects and array operations.

This comparison combines source inspection with **99 Hjson observations and
91 comment-json observations**, run on October 3, 2026. Detailed behavior below
describes the examined JavaScript implementations, not every Hjson port or a
promise about future releases. `comment-json` means the npm package from
`kaelzhang/node-comment-json`, not Python's separate `commentjson` package.

## The practical difference

| Question | JSONIC | Hjson for JavaScript | comment-json |
| --- | --- | --- | --- |
| What is it? | File transformer with separate presentation metadata | Configuration language, parser, serializer, and CLI | JavaScript parser/serializer with comment helpers |
| Typical workflow | Capture → ordinary JSON processing → restore | Edit Hjson, or edit its parsed objects → stringify | Parse → edit enriched JS objects → stringify |
| Exact unchanged source bytes? | Yes, when restoring the unchanged token stream | No | Sometimes for conventionally formatted input; not a general guarantee |
| Original horizontal whitespace? | Captured and restored | Regenerated | Regenerated |
| Blank lines? | Exact | Some comment-associated blank lines | Preserved in tested interior examples |
| Array attachment? | Always position/path | Outer gaps positional; nested metadata can follow object references | Depends on the operation |
| Missing locations? | Skip their style | Direct arrays skip; metadata merge appends orphan comments | Usually suppress or remove; operation-dependent |
| External JSON processor? | Built-in file workflow | Possible through exported extraction/merge API | Possible with a small adapter |
| Runtime | Python standard library | Node or browser; no runtime package dependencies | JavaScript; two direct runtime dependencies |

**A correction to our earlier description:** a separate comment sidecar is not
unique to JSONIC. Hjson exports `comments.extract` and `comments.merge`.
comment-json's helpers can transfer comments onto freshly parsed JSON; we
verified a recursive adapter. JSONIC's distinction is the complete workflow
and its exact whitespace, token, and attachment contract.

## What the alternatives make easier

[Hjson](https://hjson.github.io/syntax.html) reduces punctuation: it allows
unquoted keys and strings, optional commas, trailing commas, single quotes,
multiline strings, and omitted root braces. It supports `#`, `//`, and block
comments. This is convenient when humans own the configuration and ordinary
JSON is a generated export.

[comment-json](https://github.com/kaelzhang/node-comment-json) is convenient
inside JavaScript applications. Its API resembles `JSON.parse` and
`JSON.stringify`; hidden symbols hold comments, and its `CommentArray` adds
comment-aware array operations. The application can modify data and comments
without managing a separate style file.

Neither approach is inherently inferior. They solve a wider authoring problem
or a different integration problem. JSONIC keeps the original JSON grammar
apart from its supported comments and avoids requiring the data processor to
participate in preservation.

## Comments and whitespace are separate promises

Hjson's `rt.parse`/`rt.stringify` enables `keepWsc`. Despite that name, it does
not record every original gap. comment-json's pretty serializer preserves
useful layout information, especially blank lines, while generating other
formatting from the selected indentation.

| Appearance | JSONIC capture/apply | Hjson round-trip | comment-json pretty output |
| --- | --- | --- | --- |
| Tabs and mixed indentation | Exact | Chosen output indentation | Chosen output indentation |
| Spaces around punctuation | Exact | Normalized | Normalized |
| Compact objects/arrays | Exact | Usually expanded; configurable condensation | Expanded |
| Blank lines without comments | Exact | Generally removed | Retained in our examples |
| Spaces on blank lines | Exact | Not generally retained | Removed |
| Leading/trailing whitespace | Exact | Not exact | Removed in our examples |
| Final newline | Exact | Library omits it; CLI adds one | Removed in our examples |
| CRLF outside comments | Exact | Output EOL setting; embedded comment EOL can produce mixed output | LF |
| Empty-container comments | Exact for matching empty container | Kept in direct round-trip, reformatted | Kept, reformatted |

For example, with Hjson configured to quote keys and retain commas:

```text
Input: { "a" : 1 , "b": [ 2,3 ] }
```

becomes:

```json
{
  "a": 1,
  "b":
  [
    2,
    3
  ]
}
```

Consistent prettification can be a benefit. It is not exact restoration.
comment-json likewise normalizes horizontal layout, although our ordinary
two-space example round-tripped exactly. Its final normalization also removed
whitespace on otherwise blank lines inside block comments.

### Comments in unusual but valid positions

JSONIC records gaps around object keys, colons, values, and array elements.
Hjson drops some comments while parsing:

```text
Input:  {"a"/* key */:/* value */1/* first */,"b":2/* last */}
```

In our Hjson round-trip, `/* key */`, `/* value */`, and `/* first */`
disappeared; `/* last */` survived. `[1/* first */,2/* last */]` showed
the same before-comma loss. These were ordinary valid inputs, with no
metadata editing involved. JSONIC preserves those gaps.

Comment syntax is also different: JSONIC's `''' ... '''` is a **comment**;
Hjson uses that form for a **multiline string**. comment-json supports only
the usual `//` and `/* ... */` forms. Files cannot be relabeled interchangeably.

## Arrays: exactly what follows what?

Imagine these comments describe **positions**, not the current values:

```jsonc
[
  // first choice
  "charlie",
  // second choice
  "alpha",
  // third choice
  "bravo"
]
```

JSONIC attaches them to indices zero, one, and two. How another program
produced the final data is irrelevant. If index zero exists, it gets the
first comment. The same rule applies recursively to paths such as `/0/name`.

The following compares ordinary edits of the alternatives' parsed arrays
with JSONIC applied to the resulting data:

| Edit | JSONIC | Hjson direct round-trip | comment-json |
| --- | --- | --- | --- |
| Replace an element | Comment stays at index | Same | Same |
| Manually exchange two values | Comments stay at indices | Same | Same |
| `reverse` or `sort` | Comments stay at indices | Outer array comments stay | Comments move with elements |
| Insert at the beginning/middle | Existing positions retain their comments | Same outer rule | Aware methods shift comments with existing elements |
| Remove the first/middle element | Shifted value receives its new position's style | Same outer rule | Aware methods move retained elements' comments |
| Append an element | No saved style at new index | No comment at new index | No comment at new index |
| Remove final element | Absent index ignored | Absent index ignored | `pop` removes that comment |
| Shorten through `length` | Missing indices ignored | Missing indices ignored | Hidden comments remain, but are not rendered |
| Make array empty | Element styles ignored | Element comments omitted | Depends on mutation; no elements to annotate |
| Reuse saved style after regrowth | Old positions can regain old style | Retained array metadata can reappear | After length truncation, old comments can reappear |
| Replace with a fresh array | Saved style still applies | Direct metadata lost | Direct metadata lost |

comment-json's behavior is more nuanced than “comments always follow values.”
`fill` and `copyWithin` leave comments at slots. `slice` transfers relevant
comments, while `map`, `filter`, spread, and `Array.from` lost array-level
metadata in our probes. A `CommentArray`-aware `concat` can copy comments,
while ordinary-array concatenation does not. Generic JavaScript operations
need not preserve metadata merely because they preserve data.

**Nested objects matter.** In direct Hjson and comment-json workflows,
reversing an array can carry each nested object's member comments with that
object reference. JSONIC instead restores by the new index path. Hjson's
extract/merge workflow also applies nested metadata by path. A shallow copy
may lose outer comments but retain nested comments through shared references.

**Shrinking does not erase a JSONIC capture.** Applying it to a short array
skips absent indices. Applying the same capture later to a longer array can
restore those indices again. A fresh capture replaces the saved style.
This is deliberate, not value recognition.

The old last element's trailing gap also stays at that index when an array
grows. New positions receive no inferred indent or copied comment. The result
can look compact or uneven; edit and recapture to establish a new layout.

### Concrete comment-json mutation defects observed

Given a parsed three-element array with A/B/C comments:

```javascript
array.splice(1, 0);       // No data change, but B and C comments disappeared.
```

In a separate fresh parse:

```javascript
array.splice(1, 1, 'new'); // B stayed at replacement; unchanged C lost its comment.
```

These are reproducible ordinary-operation findings in the examined package,
not damaged-sidecar tests or claims that every array operation fails.

## Object keys, empty containers, and changed types

There is a useful difference even in the apparently simple case of an inline
comment after a comma:

```jsonc
{
  "a": 1, // same line as a
  // above b
  "b": 2
}
```

After removing `a`, JSONIC retains both comments before `b`: everything after
the comma is part of the next member's preceding gap. comment-json removes
the inline comment with `a` and retains the comment above `b`. Hjson merge
retains the latter and sends the inline comment to its orphan footer. These
were checked directly with all three tools.

This is a cost of JSONIC's literal gap rule: a comment that visually describes
`a` can survive because its storage location belongs to `b`. It is existing
behavior, not a change made for this comparison. If that is undesirable, the
attachment contract would need a deliberate change; no parser can infer the
author's intended meaning from English text.

| Situation | JSONIC | Hjson | comment-json |
| --- | --- | --- | --- |
| Change value under same key | Preserve key's style | Preserve comments | Preserve comments |
| Delete key | Skip its style | Direct round-trip defect below; merge orphans comments | Suppress associated comments |
| Delete then readd key | Same capture can restore style | Retained metadata restores it | Retained symbols can restore it |
| Rename/move key | New path has no old style | Requires metadata handling | `moveComments` helper available |
| Reorder keys externally | Keep target token order | Merge favors remembered source order | JS object enumeration order |
| Integer-like keys | Keep target token order | Round-trip remembers source order | Can reorder numerically |
| Empty becomes nonempty | Empty-interior style does not apply | Mode-dependent | Regenerated structure; explicit metadata handling may be needed |
| Container becomes scalar | Interior styles have no matching container | Interior metadata cannot attach as before | Explicit reassignment does not preserve vanished structure |

JSONIC preserves a member's surrounding gaps even when its value changes type;
styles *inside* a vanished container have no matching location. A container's
own object and array gaps are stored separately. Descendant styles still match
by path and container kind: an object key `"0"` and array index zero can produce
the same descendant path after a structural change. Document prefix/suffix
styles remain independent.

An Hjson direct edit exposed a real deletion problem:

```javascript
const value = Hjson.rt.parse('{\n// old setting\n"a":1,\n"b":2\n}');
delete value.a;
console.log(Hjson.rt.stringify(value));
```

The remembered key `a` was still emitted with the text `undefined`.
Hjson's extraction/merge route removes the key correctly, but moves its
comment to an orphan footer. It also lost an empty array's interior comment
in our experiment, and extracting a document with **only** root comments
returned no comment metadata. Empty-object comments survived that route.

Root scalars have their own limitations: JSONIC preserves their surrounding
presentation; Hjson ordinary parsing accepted our commented scalars but its
round-trip mode failed. comment-json wraps number/string/boolean roots to
carry comments; its documented `null` exception loses root comments.

## Number spelling, string escapes, and validation

JSONIC copies validated data tokens. It does not turn them into machine
numbers and then serialize them again.

| Token | JSONIC | Hjson default | comment-json default |
| --- | --- | --- | --- |
| `-0` | `-0` | `0` | `0` |
| `1.00E+01` | Same token | `10` | `10` |
| `9007199254740993` | Same token | `9007199254740992` | `9007199254740992` |
| `1e400` | Same token | Rejection or string interpretation depending on surrounding syntax in our probes | `null` |

comment-json provides a source-aware reviver; on a supporting runtime,
`JSON.rawJSON(context.source)` preserved these numeric tokens in our test.
That is a valid mitigation, with extra integration work: raw wrappers are
not ordinary numbers for computation. BigInt with a replacer is another
option for large integers.

Hjson normalizes string escapes. comment-json retained unchanged nested string
value escape spellings in pretty output using separately retained raw text;
escaped *key* spelling normalized. Its plain JSON output follows ordinary
serialization. JSONIC preserves both key and value token spellings presented
to it. **None can reconstruct an original number already rounded by an
external processor without separately retaining that original data.**

| Input rule | JSONIC | Hjson | comment-json |
| --- | --- | --- | --- |
| Trailing commas | Reject | Accept | Accept |
| Missing commas | Reject | Accept at permitted line boundaries | Reject |
| Unquoted keys / single quotes | Reject | Accept | Reject |
| Duplicate object names | Reject | Last value wins | Last value wins |
| Unrecognized bare values | Reject | May become strings | Reject |
| Invalid UTF-8 bytes | Reject before parsing | CLI replaced bad byte in our test | API receives strings; caller owns byte decoding |

Duplicate rejection is JSONIC's integrity policy: JSON grammar itself does not
uniformly forbid duplicates. Hjson direct round-trip also retained duplicated
key-order entries, emitting the last value twice in our duplicate example.
comment-json lost a literal `__proto__` member in our valid-data test.

These differences matter for a strict pipeline. Hjson's accepting `01` as a
string is reasonable within its language, but fails the requirement to reject
malformed purported JSON explicitly.

## Can comments survive an ordinary JSON tool?

**Yes for all three, with different amounts of integration.** Ordinary JSON
has nowhere to carry comments, so some annotated source or separate metadata
must remain available.

JSONIC supplies persistent capture/apply commands. Hjson supplies an exported
pair, although its README does not explain that pair:

```javascript
const data = Hjson.rt.parse(source);
const comments = Hjson.comments.extract(data);
// Save comments separately as JSON; process data through ordinary JSON tools.
Hjson.comments.merge(comments, updatedData);
const restored = Hjson.rt.stringify(updatedData);
```

Extraction consumes the attached metadata. Merge restores by matching paths
but appends absent-path comments under `# Orphaned comments:`. That preserves
documentation somewhere, at the cost of stale material at the bottom—the
policy we explicitly chose against. Its formatting and captured-gap limits
still apply.

For comment-json, our adapter recursively matched existing keys/indices in an
old annotated parse and fresh JSON, calling documented `moveComments` and
recursing into matching containers. It restored shorter, longer, reordered,
and nested examples positionally. That helper consumes source comments, so
another independent restoration requires reparsing or copying metadata.
Serializing public comment tokens into a sidecar is possible too; no documented
public extract/merge pair was present. An adapter cannot recover whitespace
that the library never recorded.

Also distinguish **emitting** clean JSON from **reparsing** it. comment-json's
`stringify(value)` without indentation produces clean JSON, but leaves comments
on the existing in-memory object. Calling its pretty serializer later can show
them again. Serializing and reparsing into a fresh object loses that metadata.

## Costs, benefits, and choosing honestly

| Cost or benefit | Hjson | comment-json | JSONIC |
| --- | --- | --- | --- |
| License fee | None; MIT | None; MIT | Repository license must be settled before public reuse terms are promised |
| Integration | Easy Hjson authoring; CLI and many language ports | Easy inside existing JS applications | Easy around programs that already consume ordinary JSON |
| Dependencies | No hjson-js runtime package dependencies | `esprima`, `array-timsort`; TypeScript declarations included | Python standard library only |
| Maintenance burden | Adopt existing project; confirm port-specific preservation | Adopt existing library; understand mutation helpers | We own the parser, contract, and tests |
| New layout | Generates readable formatting | Generates readable formatting | Invents no missing per-item style |
| File writes | Calling application/CLI redirection owns them | Calling application owns them | Validates first, supports atomic replacement and permission handling |
| Working state | Annotated source or retained/extracted metadata | Annotated source or enriched objects/adapted metadata | Annotated source and/or captured style alongside data |

Neither JavaScript library is inherently heavyweight: hjson-js has a small
browser bundle; comment-json and its installed dependencies occupied roughly
half a megabyte in our environment, excluding Node. No comparative speed or
memory benchmark was run. JSONIC also reads whole documents and traverses
recursively; it is not advertised as a streaming large-data processor.

Choose Hjson for pleasant human configuration syntax. Choose comment-json when
a JavaScript application owns the read/edit/write cycle and its mutation
semantics fit. Choose JSONIC when exact captured presentation and consistent
key/index rules must survive independently edited ordinary JSON. JSONIC's
tradeoffs are the extra saved state, intentionally uninferred new formatting,
and responsibility for maintaining our implementation.

## Primary references

- [Hjson API and CLI](https://github.com/hjson/hjson-js)
- [Hjson syntax](https://hjson.github.io/syntax.html),
  [implementation choices](https://hjson.github.io/download.html), and
  [round-trip portability caveat](https://hjson.github.io/faq.html)
- [Hjson comment extraction and merge source](https://github.com/hjson/hjson-js/blob/master/lib/hjson-comments.js)
- [comment-json API, array helpers, and number handling](https://github.com/kaelzhang/node-comment-json)
- [Hjson package declaration](https://github.com/hjson/hjson-js/blob/master/package.json)
  and [license](https://github.com/hjson/hjson-js/blob/master/LICENSE)
- [comment-json package declaration](https://github.com/kaelzhang/node-comment-json/blob/master/package.json)
  and [license](https://github.com/kaelzhang/node-comment-json/blob/master/LICENSE)

Specific output changes and defects above are our own experiments against the
published packages. They supplement these projects' documented intentions;
they should not be mistaken for guarantees about all implementations.
