# What the tests prove

Run the complete suite from the project directory:

```bash
python3 -m unittest discover -s tests -v
```

Python's built-in `unittest` runner finds `test_*.py` files and runs their test
methods. `ok` means every assertion in that test passed; `FAIL` or `ERROR`
means the command exits unsuccessfully and shows the failed case. No extra test
package is required. Tests use temporary directories and disposable local Git
repositories, not your documents or project history.

## The evidence

| Test area | What is checked |
| --- | --- |
| Fixed expected output | Exact bytes for stripping, pretty output, comment gaps, changed values, and positional arrays. These expectations are written independently of the implementation. |
| Round trips | Capture → raw or pretty JSON → apply returns the original bytes, including whitespace, comment contents, line endings, escapes, and numeric spelling. |
| Ordinary JSON edits | Another JSON tool changes the data; the restored data matches the edit, comments match keys/indices, and absent entries receive nothing. |
| Input errors | Invalid JSON, duplicate keys, bad UTF-8, and excessive nesting fail clearly; existing file outputs are unchanged. |
| File output | Existing POSIX mode bits, new-file umask, output symlinks, and in-place conversions behave as documented. |
| Update/export | Disposable repositories check clean-tree refusal, one update commit, ZIP cleanup, actual snapshot contents, and snapshot placement. |
| Generated documents | Repeatable combinations of values and comment gaps supplement the fixed cases. Structural edits check target tokens, repeated application, and capture reuse. A thousand-record case checks ordinary scale. |

Round trips are strong evidence for preservation, but they are not enough on
their own: two complementary mistakes could cancel each other. Fixed byte
expectations and independently decoded JSON data check the individual operations.
The runnable examples exercise the public command line and demonstrate the
same contracts with meaningful configurations.

## Automatic checks on GitHub

The [test workflow](../.github/workflows/tests.yml) runs on pushes, pull requests,
and manual requests. Linux runs the complete suite and demo. macOS and Windows
run the JSONIC core and example suites plus the demo; maintenance utilities
target the local POSIX workflow. Each runner uses the current stable Python.

The workflow is included and locally reviewed. Native macOS/Windows support is
confirmed only after those jobs actually pass on GitHub. The Actions tab shows
the result for each operating system; a workflow file alone is not a passed test.

## What is still unproven

Finite tests cannot prove every possible document or I/O failure. The suite
is not a performance benchmark, a power-loss test, or a proof of full filesystem
metadata preservation. Linux is exercised; native macOS and Windows remain
unverified. External JSON software can still change numeric precision or token
spelling before restoration.
