# What changed, and why

This audit compares the latest executable in the original JSONIC directory
with the cleaned executable. It distinguishes defects from requested behavior
and implementation choices.

The current maintenance cleanup puts executable `update.py` and `export.py`
inside the project. Updates require a clean Git tree, including unrelated
nonignored untracked files. Exports remain read-only and can capture local edits;
their default snapshot stays inside the project and is ignored by Git.
JSONIC's data operations are unchanged by this cleanup.

The preceding changes added token-preserving `--pretty` output and made new files
respect the process umask. Existing mode preservation and symlink-following
remain. Duplicate keys stay rejected; all three comment forms stay supported.
The README, installation instructions, and interview demo are shorter and
include pretty-output restoration. Four focused tests were added.

## Defect corrections

| Change | Previous behavior | Current behavior | Benefit and cost |
| --- | --- | --- | --- |
| Empty capture | A capture with nothing to store could leave an old style file untouched. | Every successful capture replaces the file, even with `{}`. | Removed comments stay removed after recapture. An empty capture now creates a small file. |
| Duplicate names | Capture/apply rejected duplicate keys; raw accepted them. | Every operation rejects duplicates, including equivalently escaped names. | Consistent keyed matching. Uniqueness is a deliberate policy stricter than JSON grammar; some JSON tools accept duplicates. |
| Invalid UTF-8 | Invalid bytes inside values could pass through some operations. | Whole-input UTF-8 validation precedes parsing. | Enforces the stated encoding and avoids silent invalid output. Costs an additional decode pass/allocation. |
| CR-only line endings | `//` ended only at LF, so a bare CR could swallow following content. | CR and LF both terminate line comments. | Handles LF, CRLF, and CR consistently. |
| Capture over its own input | An explicit output equal to the input could replace data with metadata. | Same-path and same-inode aliases are rejected. | Prevents accidentally destroying data. Capture-to-input is deliberately unavailable. |
| Apply over its style | An explicit output could replace the metadata being used. | Output aliases of the style file are rejected. | Protects the capture. This is a guard against an explicit hazardous command, not proof of routine corruption. |
| Existing Unix permission bits | Replacing an existing file changed its mode to `0600`. | Its prior mode bits are copied to the replacement. | Existing `0640`/`0644` permissions survive. Other metadata is not automatically preserved. |
| Unix-only permission call | Our first permission correction used `fchmod` unconditionally. | Calls it only where the API exists. | Fixes a portability regression introduced during our cleanup. The missing-API path is tested; native Windows is not yet verified. |
| File/depth errors | Common failures could expose Python tracebacks. | Clear stderr message and nonzero exit; excessive nesting has a specific error. | Better command-line behavior. Broad exception handling can conceal an internal traceback during debugging. |
| Nonworking test runner | An old runner named a missing executable. | Tests invoke the actual tool and compare meaningful expected results. | Reproducible evidence; finite tests cannot certify every input or platform. |

The original latest implementation already checked ordinary syntax errors,
trailing commas, invalid escapes, and extra root values. Those checks were
retained, not newly invented. It already computed output before replacing a
file and used atomic replacement.

## Requested behavior and retained design

| Decision | What changed or stayed | Tradeoff |
| --- | --- | --- |
| Positional array comments | Existing behavior retained; redundant last-index logic removed and tests added. | Reordered values receive the comments at their new positions. Missing positions are omitted; new ones have no invented style. This was not an array bugfix. |
| Object comments keyed by path | Existing behavior retained. | Rename/move changes the path; it does not automatically move the comment. Text after a comma belongs to the next key. |
| `--raw`, `--mini`, `--minified` | Added aliases for the same compact operation. | Familiar names without multiple implementations. |
| `--strip` | Added removal of comments alone, preserving other whitespace and CR/LF bytes. | Preserves line endings, but not the column width occupied by removed comments. |
| `--pretty` | Added fixed two-space formatting of ordinary JSON, preserving token bytes and key order. | Convenient readable JSON; intentionally replaces layout and line endings. Capture first to restore the original presentation. |
| One current style representation | Removed the format marker and its gate. | No migration machinery. Old incompatible captures should be recreated from the annotated source. |
| Exact token bytes | Existing scanner retained. | Preserves spellings inside JSONIC; cannot reverse rounding or rewriting by another tool. |
| Empty containers | Existing attachment rule retained. | Interior style applies while the container is empty; it cannot be fitted inside a replacement scalar. |

After restoration, the implementation also parses the resulting annotated
document before emitting it. This added consistency check costs another scan.
It checks syntax, not equality with the original data. It was not a correction
of a demonstrated routine failure.

The deliberately damaged-sidecar demonstration is not counted as a normal-use
bug. Removing a captured newline that terminates a line comment changes the
metadata's meaning. It was not evidence that a correct capture lost that newline.

## File permissions, precisely

**The observed mode-bit problem is fixed. Full filesystem metadata preservation
is not implemented.** These are separate claims.

| Situation | Current behavior | Good / bad |
| --- | --- | --- |
| Existing file with mode `0640` | Stays `0640` on POSIX; reproduced against the old `0600` result. | Keeps existing owner/group access bits. |
| New output file | Created with `0666` filtered by the process umask, typically `0644` or `0600`. | Normal file-creation behavior. This replaces the inherited unconditional `0600`; use umask `077` for private new files. |
| Symlink output | Resolves the link and replaces its target; the link remains. | Behaves like ordinary writing through a link, but can affect a target outside the apparent output directory. Retained under the user's delegated choice. |
| Hardlink output | Replaces one path with a new inode; other links keep the old contents. | Atomic replacement avoids partial data but does not act like writing through a shared inode. Inherited and reproduced. |
| Extended attributes | Existing attributes are not copied; loss reproduced. | Small implementation, but unsuitable if those attributes must survive. |
| Owner, group, ACL | Not explicitly preserved; temporary-file/directory defaults apply. | Mode bits alone do not reproduce all access policy. These cases were source-inspected, not independently exercised under multiple accounts. |
| Read-only destination | Replacement may still be permitted when its directory is writable. | This follows replacement semantics, not ordinary opening-for-write semantics. |
| Sudden interruption | Old file survives failures before replacement; replacement itself is atomic. | Requires directory write permission and space for a second file. The directory is not fsynced, so complete power-loss durability is not promised. |

`0600` means owner read/write. `0644` additionally gives everyone read access.
`0640` additionally gives only the file's group read access.

The settled behavior is atomic replacement, existing mode-bit preservation,
new-file umask, and following output symlinks. Temporary creation starts with
the destination's mode filtered by umask; exact existing bits return after
writing. New files use exclusive
creation with normal permissions, without temporarily changing the process
umask. Full filesystem metadata preservation is outside the current contract.

Invalid input produces no partial output and leaves an existing file alone.
That does not mean every I/O failure delivers zero bytes: writing to stdout
can fail after some bytes have already reached a pipe.

## Project maintenance is separate

`./update.py` installs source files with the archive's executable/nonexecutable
mode, stages the changed paths, and commits them. Any nonignored staged,
unstaged, or untracked work stops it before application, even if unrelated to
the update. It never makes a checkpoint commit, stash, or reset automatically.
ZIP removal follows a successful local commit. A missing default download is
a friendly no-op. See [the update workflow](updates.md).

`./export.py` shares the actual project files and Git state without changing
them, including dirty work and useful ignored configuration/style files. Its
default output is `JSONIC-snapshot.zip` inside the project, excluded from Git
and subsequent exports. Both utilities live in the project; the old command
files are removed. Neither changes JSONIC's comment handling or data-file
permission policy.
