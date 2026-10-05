#!/usr/bin/env python3
"""Demonstrate three real JSON workflows; all generated files are temporary."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "jsonic"
EXAMPLES = ROOT / "examples"


def run(*args):
    result = subprocess.run(
        [sys.executable, str(PROGRAM), *map(str, args)],
        capture_output=True, check=False,
    )
    if result.returncode:
        raise SystemExit(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


def require(condition, message):
    if not condition:
        raise SystemExit("Demo failed: " + message)


def show(label, data):
    print(label, flush=True)
    print(data.decode("utf-8").rstrip(), flush=True)
    print(flush=True)


def prepare(name, work):
    """Capture once and prove both ordinary JSON layouts restore exactly."""
    source = EXAMPLES / name
    style = work / (source.stem + ".jsonic.style")
    data = work / (source.stem + ".json")
    original = source.read_bytes()
    run(source, "-o", style)
    for mode in ("--raw", "--pretty"):
        data.write_bytes(run(source, mode))
        json.loads(data.read_bytes())
        require(run(data, "--apply", style) == original, name + " exact " + mode + " round trip")
    # The external editor starts with the compact, ordinary JSON export.
    data.write_bytes(run(source, "--raw"))
    return original, style, data


def restore_edit(values, data, style):
    """The editor uses only Python's normal JSON API; restoration uses the CLI."""
    target = json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    data.write_bytes(target)
    saved_style = style.read_bytes()
    restored = run(data, "--apply", style)
    output = data.with_name(data.stem + "-restored.jsonic")
    output.write_bytes(restored)
    clean = run(output, "--raw")
    require(json.loads(clean) == values, "restoration changed the edited data")
    require(clean == target, "restoration changed the edited token spellings")
    require(style.read_bytes() == saved_style, "applying changed the saved style")
    return restored


def settings_demo(work):
    original, style, data = prepare("settings.jsonic", work)
    show("Retry settings — annotated source", original)
    show("Ordinary JSON handed to the editor", data.read_bytes())
    values = json.loads(data.read_bytes())
    values["attempts"] = 5
    restored = restore_edit(values, data, style)
    require(
        restored == original.replace(b'"attempts": 3', b'"attempts": 5'),
        "retry setting lost its original presentation",
    )
    show("After Python changes attempts to 5, then JSONIC restores", restored)


def priority_demo(work):
    original, style, data = prepare("priority-array.jsonic", work)
    show("Fallback sources — original priority slots", original)
    values = json.loads(data.read_bytes())
    values[:] = [values[2], values[0], values[1]]
    changed = restore_edit(values, data, style)
    require(b'"network" /* First choice. */' in changed, "comments followed values instead of positions")
    show("Reordered: network now occupies the first slot", changed)

    values.append("defaults")
    grown = restore_edit(values, data, style)
    require(b'/* Third choice. */,"defaults"]' in grown, "new slot received invented presentation")
    show("Appended: defaults has no captured comment or spacing", grown)

    del values[1:]
    shortened = restore_edit(values, data, style)
    require(b'/* Second choice. */' not in shortened and b'/* Third choice. */' not in shortened,
            "missing slots left comments in the output")
    show("Shortened: only the first slot's comment is restored", shortened)

    values.extend(["local", "cache", "defaults"])
    require(restore_edit(values, data, style) == grown, "skipping absent slots erased their saved style")
    print("Missing-slot comments stay in the capture; reusing it can restore them later.\n", flush=True)


def config_excerpt(document):
    keys = (b'"attempts":', b'"delay_seconds":', b'"/jobs"', b'"/metrics"',
            b'"empty_options":', b'"empty_queue":')
    return b"\n".join(line for line in document.splitlines() if any(key in line for key in keys))


def complex_demo(work):
    original, style, data = prepare("config.jsonic", work)
    require(b'1.00E+01' in run(EXAMPLES / "config.jsonic", "--pretty"),
            "pretty output changed a numeric token")
    show("Nested configuration — original excerpts", config_excerpt(original))
    values = json.loads(data.read_bytes())
    values["retry"]["attempts"] = 5
    values["routes"][1]["timeout_seconds"] = 45
    values["routes"].append({"path": "/metrics", "timeout_seconds": 5})
    values["empty_options"] = False
    del values["empty_queue"]
    restored = restore_edit(values, data, style)
    require(b'false /* Optional overrides; false disables them. */' in restored,
            "field comment was lost when its value changed type")
    require(b'nothing configured yet' not in restored and b'no queued work' not in restored,
            "removed interior or key comments were restored")
    require(b'{"path":"/metrics","timeout_seconds":5}]' in restored,
            "new route acquired invented formatting")
    require(b'"delay_seconds": 10.0' in restored, "restoration replaced the editor's numeric spelling")
    show("After Python edits nested values, appends a route, and removes structure", config_excerpt(restored))
    print("The field note survives object → false; its interior note and removed queue note do not.", flush=True)
    print("Python rewrote 1.00E+01 to 10.0. JSONIC preserves that edited spelling.\n", flush=True)


def main():
    # Match JSONIC's UTF-8 output even when Windows redirects a legacy-code-page stream.
    sys.stdout.reconfigure(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="jsonic-demo-") as directory:
        work = Path(directory)
        settings_demo(work)
        priority_demo(work)
        complex_demo(work)
    print("PASS: all three examples restore exactly through raw/pretty JSON; edited data and token bytes survive restoration.")
    print("Examples are unchanged; temporary outputs have been removed.")


if __name__ == "__main__":
    main()
