"""Public-CLI checks for the documented examples and their actual JSON edits."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "jsonic"
EXAMPLES = ROOT / "examples"


class ExampleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)

    def cli(self, *args):
        result = subprocess.run(
            [sys.executable, str(PROGRAM), *map(str, args)],
            cwd=self.work, capture_output=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(result.stderr, b"")
        return result.stdout

    def capture_example(self, name):
        source = self.work / name
        source.write_bytes((EXAMPLES / name).read_bytes())
        self.assertEqual(self.cli(source), b"")
        data = source.with_suffix(".json")
        data.write_bytes(self.cli(source, "--raw"))
        return data, self.work / (source.stem + ".jsonic.style")

    def restore_edit(self, data, values):
        target = json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        data.write_bytes(target)
        output = self.work / "restored.jsonic"
        restored = self.cli(data, "--apply")
        output.write_bytes(restored)
        clean = self.cli(output, "--raw")
        self.assertEqual(json.loads(clean), values)
        self.assertEqual(clean, target)
        return restored

    def test_retry_edit_preserves_complete_presentation(self):
        data, style = self.capture_example("settings.jsonic")
        values = json.loads(data.read_bytes())
        values["attempts"] = 5
        captured = style.read_bytes()
        self.assertEqual(
            self.restore_edit(data, values),
            b'{\n  "attempts": 5 /* Total attempts, including the first request. */,\n'
            b'  "enabled": true\n}\n',
        )
        self.assertEqual(style.read_bytes(), captured)

    def test_priority_capture_is_reusable_across_reorder_shrink_and_growth(self):
        data, style = self.capture_example("priority-array.jsonic")
        captured = style.read_bytes()
        header = b'/* Configuration sources are tried in order; notes describe priority slots. */\n'
        cases = [
            (["network", "local", "cache"],
             b'["network" /* First choice. */, "local" /* Second choice. */, "cache" /* Third choice. */]\n'),
            (["network"], b'["network" /* First choice. */]\n'),
            ([], b'[]\n'),
            (["network", "local", "cache", "defaults"],
             b'["network" /* First choice. */, "local" /* Second choice. */, "cache" /* Third choice. */,"defaults"]\n'),
        ]
        for values, expected in cases:
            with self.subTest(values=values):
                self.assertEqual(self.restore_edit(data, values), header + expected)
                self.assertEqual(style.read_bytes(), captured)

    def test_nested_edit_has_complete_expected_document_and_data(self):
        data, style = self.capture_example("config.jsonic")
        values = json.loads(data.read_bytes())
        values["retry"]["attempts"] = 5
        values["routes"][1]["timeout_seconds"] = 45
        values["routes"].append({"path": "/metrics", "timeout_seconds": 5})
        values["empty_options"] = False
        del values["empty_queue"]
        expected = r"""/* An annotated application configuration.
   Capture this file before handing ordinary JSON to another program. */
{
    "service": "field-kit",
    "endpoint": "https://example.com/api",
    "literal_text": "These are data: // not a comment; /* not a comment */; ''' not a comment '''",

    /* Operations may change the values while these notes remain in place. */
    "retry": {
        "attempts": 5 /* including the first attempt */,
        "delay_seconds": 10.0,
        "enabled": true
    },

    "routes": [
        /* Position zero: first route checked. */
        { "path": "/health", "timeout_seconds": 2 },
        /* Position one: next route checked, regardless of its value. */
        { "path": "/jobs", "timeout_seconds": 45 }
    ,{"path":"/metrics","timeout_seconds":5}],

    "labels": { "日本語": "こんにちは", "units": "µs" },
    "path/with~characters": { "": "an empty key is legal" },
    "empty_options": false /* Optional overrides; false disables them. */,
    "escaped_text": "quote=\" slash=/ backslash=\\ newline=\n"
}
// Configuration ends here.
""".encode("utf-8")
        captured = style.read_bytes()
        self.assertEqual(self.restore_edit(data, values), expected)
        self.assertEqual(style.read_bytes(), captured)

    def test_demo_runs_from_elsewhere_and_leaves_no_artifacts(self):
        before = {p.name: p.read_bytes() for p in EXAMPLES.iterdir() if p.is_file()}
        env = os.environ.copy()
        env["TMPDIR"] = str(self.work)
        env["TMP"] = str(self.work)
        env["TEMP"] = str(self.work)
        result = subprocess.run(
            [sys.executable, str(EXAMPLES / "demo.py")],
            cwd=self.work, capture_output=True, timeout=30, env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(result.stderr, b"")
        self.assertIn(b"PASS: all three examples restore exactly", result.stdout)
        self.assertEqual(list(self.work.iterdir()), [])
        after = {p.name: p.read_bytes() for p in EXAMPLES.iterdir() if p.is_file()}
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
