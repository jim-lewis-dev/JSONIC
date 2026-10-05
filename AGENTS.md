# Development guidance

This file gives coding agents the project's working rules. It is not used by
JSONIC at runtime. Behavior and rationale live in the README and docs.

- Keep one current implementation. No release numbers, numbered artifacts,
  schema identifiers, migrations, compatibility modes, or wrapper commands.
- JSONIC means JavaScript Object Notation with Integrated Comments.
- Preserve the byte-oriented parser, original token spellings, and zero
  third-party dependencies. Do not add a second processing pipeline.
- Arrays match indices; objects match keys at paths. Skip missing addresses.
  Do not follow values, append orphan comments, or invent new presentation.
- Successful capture always replaces its style, including with `{}`.
- Retain `--raw`/`--mini`/`--minified`, `--strip`, `--pretty`, and `--apply`.
  Pretty uses two spaces, LF, and a final newline without rewriting tokens.
- Require strict UTF-8 and unique keys. `.jsonic` additionally accepts `//`,
  `/* ... */`, and triple-single-quote comments. Blocks do not nest.
- Invalid input must fail clearly without replacing an existing output.
- Preserve existing POSIX mode bits, respect umask for new files, and follow
  output symlinks using atomic replacement. Do not promise owner/group,
  ACL/xattr, hardlink, or full power-loss preservation.
- Test real edits, exact expected bytes, round trips, strings resembling
  comments, structural changes, and practical CLI failures. Damaged style
  files are not a product use case. Avoid unnecessary test scaffolding.
- Run `python3 -m unittest discover -s tests -v` and `python3 examples/demo.py`.
  Generated output belongs in temporary directories.
- Use a fresh project snapshot before changes depending on unseen local files.
  Preserve user edits. Keep Git local; do not add remotes or push.
- Deliver changes as `JSONIC.zip`, complete replacement files plus `update.json`
  containing a plainspoken commit message and explicit removals. No backups.
- Keep executable `update.py` and `export.py` inside the project. The updater
  uses Downloads/JSONIC.zip, commits locally, then deletes the ZIP. Refuse any
  nonignored staged, unstaged, or untracked work before application. Never
  checkpoint, stash, or reset it automatically. The user tests after the commit.
- Export may capture dirty work and useful ignored configuration/style files
  without changing Git. Its default output is PROJECT/JSONIC-snapshot.zip,
  ignored by Git and excluded from itself. Exclude caches and build output.
- Keep public docs concise and complete. No development transcripts or
  obsolete transition instructions. Ask about unresolved product choices.
