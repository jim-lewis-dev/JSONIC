# Presenting JSONIC

## Recommended home

Make a public GitHub repository the source of truth. Lead with the README,
working demo, tests, and a clear license. Pin it on your profile and link it
from your résumé or portfolio.

A small project page can provide a friendlier entrance. GitHub Pages can host
static HTML, CSS, and JavaScript from the same repository; it needs no separate
application server. Keep the source, installation, and download links pointing
to the repository so there is only one implementation to maintain.

Suggested repository description:

> Capture JSON comments and formatting, process ordinary JSON, and restore the
> presentation. A dependency-free Python command-line tool.

Use **JSONIC — reversible comments for JSON** as the visible title. A repository
name such as `jsonic-comments` distinguishes it from the unrelated
[`jsonic` parser](https://github.com/jsonicjs/jsonic). The local directory name
does not need to match the public repository name.

## A short interview demo

Run `python3 examples/demo.py` and explain the results:

1. Humans write explanations beside configuration values.
2. JSONIC saves that presentation and hands standard JSON to another program.
3. That program changes a value using its ordinary JSON library.
4. JSONIC restores the saved comments and spacing around the new value.
5. A shortened array shows the explicit rule: comments belong to positions,
   and missing positions receive no comment.

The last step is useful evidence of a deliberate contract. Follow it with the
test command if asked about correctness, rather than presenting a wall of tests
before explaining the problem.

Suggested project summary for a résumé:

> Built a Python CLI that separates comments and formatting from JSON data and
> restores them after ordinary JSON processing; implemented byte-preserving
> parsing, deterministic key/index matching, safe file replacement, and tests
> covering exact round trips, structural edits, and generated documents.

Be ready to explain these choices:

- Why a byte scanner preserves number spellings and escape sequences that
  parsing and serializing values can change.
- Why object paths and array positions provide predictable matching.
- Why comments for removed entries are omitted and new style is not guessed.
- Why a separate style file lets existing programs stay unaware of comments.
- Why whole-file parsing and a named-file CLI are sufficient for this scope.

## The project page

Keep it to a single page: a one-sentence promise, a visible annotated → raw →
edited-and-restored example, an installation command, and links to source,
tests, and the exact restoration rules. A small example selector can show
changed values, a shortened array, and the nested configuration.

Generate displayed results with the actual CLI. Do not write a second parser
in JavaScript just for the page. If a live arbitrary-input playground is later
worth adding, decide how to run the existing implementation there.

## Before publishing

- Confirm the GitHub account and repository name.
- Choose a license and copyright attribution. MIT is a straightforward option
  for allowing reuse; review its terms before adding `LICENSE`.
- Run the suite and demo on native Windows and macOS if claiming those systems
  as verified. Linux is already checked.
- Enable automated tests on pushes once the repository exists. Keep status
  claims tied to actual runs.
- Publish the repository, then the optional project page. Add both links to
  your profile and résumé.

The prepared package is local. No public repository or website has been
created, no license has been granted, and no remote has been configured.

References: [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages),
[repository licensing](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).
