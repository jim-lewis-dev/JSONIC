"""Workflow tests with fixed expected output and repeatable generated cases."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import random
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "jsonic"
FIXTURES = ROOT / "tests" / "fixtures"
loader = importlib.machinery.SourceFileLoader("jsonic", str(PROGRAM))
spec = importlib.util.spec_from_loader(loader.name, loader)
jsonic = importlib.util.module_from_spec(spec)
loader.exec_module(jsonic)


class JsonicTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)

    def file(self, name, data):
        path = self.work / name
        path.write_bytes(data)
        return path

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, str(PROGRAM), *map(str, args)],
            cwd=self.work, capture_output=True, timeout=15,
        )

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(result.stderr, b"")

    def assert_error(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"jsonic: error:", result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)

    def capture(self, source):
        path = self.file("source.jsonic", source)
        style = self.work / "source.jsonic.style"
        jsonic.cmd_capture(str(path), str(style), allow_comments=True)
        return style

    def restore(self, source, target):
        style = self.capture(source)
        path = self.file("target.json", target)
        return jsonic.cmd_apply_to_bytes(str(path), str(style), allow_comments=False)

    def roundtrip(self, source):
        raw = jsonic.strip_document(source, allow_comments=True)
        restored = self.restore(source, raw)
        self.assertEqual(restored, source)
        clean = jsonic.strip_document(source, allow_comments=True, preserve_whitespace=True)
        self.assertEqual(jsonic.strip_document(clean, allow_comments=False), raw)
        return raw

    def test_retained_fixtures_and_real_examples_roundtrip(self):
        files = sorted(FIXTURES.iterdir()) + sorted((ROOT / "examples").glob("*.jsonic"))
        for path in files:
            if path.name == "reject-trailing-comma.jsonic":
                continue
            with self.subTest(file=path.name):
                raw = self.roundtrip(path.read_bytes())
                json.loads(raw)

    def test_comprehensive_raw_matches_fixed_expected_bytes(self):
        source = (FIXTURES / "comprehensive.jsonic").read_bytes()
        expected = (FIXTURES / "comprehensive.raw.json").read_bytes()
        self.assertEqual(jsonic.strip_document(source, allow_comments=True), expected)

    def test_each_object_gap_and_empty_container_roundtrips(self):
        source = (
            b'/*root*/{/*c1*/"a"/*c2*/:/*c3*/1/*c4*/,'
            b'"empty_object":{/*inside*/},"empty_array":[\'\'\'inside\'\'\']}/*end*/'
        )
        self.assertEqual(self.roundtrip(source), b'{"a":1,"empty_object":{},"empty_array":[]}')

    def test_comment_removal_has_exact_expected_whitespace(self):
        source = b'// header\r\n{\t/*before*/"a" /*key*/: 1, // value\r\n  "b": \'\'\'multi\nline\'\'\' [2/*tail*/]\r\n}\n'
        expected = b'\r\n{\t"a" : 1, \r\n  "b": \n [2]\r\n}\n'
        self.assertEqual(
            jsonic.strip_document(source, allow_comments=True, preserve_whitespace=True),
            expected,
        )
        self.assertEqual(json.loads(expected), {"a": 1, "b": [2]})

    def test_comment_like_strings_are_data(self):
        value = "https://example.com/a//b /* literal */ ''' literal ''' \" \\\\ \n"
        source = b'/*before*/{ "text": ' + json.dumps(value).encode() + b' } // end'
        raw = self.roundtrip(source)
        self.assertEqual(json.loads(raw), {"text": value})
        self.assertIn(b"/* literal */", raw)

    def test_strip_on_plain_json_is_byte_identical(self):
        for source in [b' \t{\r\n "x": [1, 2]\r\n}\n', b'\t true \n', b'1.000E+02']:
            with self.subTest(source=source):
                self.assertEqual(
                    jsonic.strip_document(source, allow_comments=False, preserve_whitespace=True),
                    source,
                )

    def test_line_endings_and_end_of_file_comments(self):
        for newline in (b"\n", b"\r\n", b"\r"):
            with self.subTest(newline=newline):
                source = b'// before' + newline + b'{// inside' + newline + b'"x":1}' + newline + b'// after'
                self.assertEqual(self.roundtrip(source), b'{"x":1}')
                clean = jsonic.strip_document(source, allow_comments=True, preserve_whitespace=True)
                self.assertEqual(clean, newline + b'{' + newline + b'"x":1}' + newline)

    def test_numeric_and_string_token_spelling_survives(self):
        source = b'[ -0, 1.00E+03, 1e9999, 123456789012345678901234567890, "\\u0061\\/" ]'
        self.assertEqual(
            self.roundtrip(source),
            b'[-0,1.00E+03,1e9999,123456789012345678901234567890,"\\u0061\\/"]',
        )

    def test_values_change_without_changing_presentation(self):
        source = b'/*start*/{ "attempts": /*count*/ 3, "enabled": true /*tail*/ }\n'
        target = b'{"attempts":5,"enabled":false}'
        expected = b'/*start*/{ "attempts": /*count*/ 5, "enabled": false /*tail*/ }\n'
        self.assertEqual(self.restore(source, target), expected)

    def test_arrays_retain_positions_for_changed_and_reordered_values(self):
        source = b'[/*zero*/10 /*after0*/, /*one*/20 /*after1*/]'
        cases = [
            (b'[99,88]', b'[/*zero*/99 /*after0*/, /*one*/88 /*after1*/]'),
            (b'[20,10]', b'[/*zero*/20 /*after0*/, /*one*/10 /*after1*/]'),
            (b'[99,88,77]', b'[/*zero*/99 /*after0*/, /*one*/88 /*after1*/,77]'),
            (b'[99]', b'[/*zero*/99 /*after0*/]'),
            (b'[]', b'[]'),
        ]
        for target, expected in cases:
            with self.subTest(target=target):
                self.assertEqual(self.restore(source, target), expected)

    def test_array_old_last_gap_stays_at_its_index(self):
        source = b'[1,2 // index one\n]'
        self.assertEqual(self.restore(source, b'[3,4,5]'), b'[3,4 // index one\n,5]')
        self.assertEqual(self.restore(source, b'[3]'), b'[3]')

    def test_nested_array_styles_use_real_indices(self):
        source = b'[{"x":/*slot0*/1},{"x":/*slot1*/2}]'
        self.assertEqual(
            self.restore(source, b'[{"x":2},{"x":1},{"x":3}]'),
            b'[{"x":/*slot0*/2},{"x":/*slot1*/1},{"x":3}]',
        )
        self.assertEqual(self.restore(source, b'[{"other":7}]'), b'[{"other":7}]')

    def test_object_comments_follow_keys_and_absent_keys_are_ignored(self):
        source = b'{/*a*/"a":1,/*b*/"b":2}'
        self.assertEqual(self.restore(source, b'{"b":20,"a":10}'), b'{/*b*/"b":20,/*a*/"a":10}')
        self.assertEqual(self.restore(source, b'{"b":20,"c":30}'), b'{/*b*/"b":20,"c":30}')
        self.assertEqual(self.restore(source, b'{}'), b'{}')

    def test_comment_after_comma_follows_next_key(self):
        source = b'{"a":1, // before b\n"b":2}'
        self.assertEqual(self.restore(source, b'{"b":3}'), b'{ // before b\n"b":3}')
        self.assertEqual(self.restore(source, b'{"a":3}'), b'{"a":3}')

    def test_unusual_keys_do_not_collide(self):
        source = b'{"a/b":{"~x":/*slash*/1},"a":{"b":{"~x":/*nested*/2}},"":/*empty*/3}'
        target = b'{"":4,"a":{"b":{"~x":5}},"a/b":{"~x":6}}'
        expected = b'{"":/*empty*/4,"a":{"b":{"~x":/*nested*/5}},"a/b":{"~x":/*slash*/6}}'
        self.assertEqual(self.restore(source, target), expected)

    def test_empty_container_and_root_styles(self):
        source = b'/*root*/{"a":[/*empty*/],"b":{/*empty object*/}}/*tail*/'
        self.assertEqual(self.restore(source, b'{"a":[],"b":{}}'), source)
        self.assertEqual(
            self.restore(source, b'{"a":[1],"b":{"x":2}}'),
            b'/*root*/{"a":[1],"b":{"x":2}}/*tail*/',
        )
        self.assertEqual(self.restore(b'[/*element*/1]', b'[]'), b'[]')

    def test_default_capture_replaces_stale_style_even_when_empty(self):
        path = self.file("settings.jsonic", b'/*old*/{"x":1}')
        self.assert_ok(self.cli(path))
        self.assertEqual(self.cli(path, "--apply").stdout, b'/*old*/{"x":1}')
        path.write_bytes(b'{"x":2}')
        self.assert_ok(self.cli(path))
        style = self.work / "settings.jsonic.style"
        self.assertEqual(style.read_bytes(), b'{}\n')
        restored = self.cli(path, "--apply")
        self.assert_ok(restored)
        self.assertEqual(restored.stdout, b'{"x":2}')

    def test_fresh_raw_capture_creates_empty_style(self):
        path = self.file("settings.json", b'{"x":1}')
        self.assert_ok(self.cli(path))
        self.assertEqual((self.work / "settings.jsonic.style").read_bytes(), b'{}\n')
        self.assertEqual(self.cli(path, "--apply").stdout, b'{"x":1}')

    def test_raw_aliases_are_identical_and_do_not_capture(self):
        path = self.file("settings.jsonic", b'{ // comment\n "x": 1 }\n')
        for flag in ("--raw", "--mini", "--minified"):
            with self.subTest(flag=flag):
                result = self.cli(path, flag)
                self.assert_ok(result)
                self.assertEqual(result.stdout, b'{"x":1}')
        self.assertFalse((self.work / "settings.jsonic.style").exists())

    def test_cli_strip_and_explicit_style_roundtrip(self):
        path = ROOT / "examples" / "config.jsonic"
        style = self.work / "chosen.style"
        clean = self.work / "processor-input.json"
        restored = self.work / "restored.jsonic"
        self.assert_ok(self.cli(path, "-o", style))
        self.assertNotIn("format", json.loads(style.read_bytes()))
        self.assert_ok(self.cli(path, "--strip", "-o", clean))
        json.loads(clean.read_bytes())
        self.assert_ok(self.cli(clean, "--apply", style, "-o", restored))
        self.assertEqual(restored.read_bytes(), path.read_bytes())

    def test_process_real_configuration_then_restore_new_values(self):
        source = (ROOT / "examples" / "config.jsonic").read_bytes()
        style = self.capture(source)
        data = json.loads(jsonic.strip_document(source, allow_comments=True))
        data["retry"]["attempts"] = 7
        data["routes"][0]["timeout_seconds"] = 9
        data["routes"].append({"path": "/new", "timeout_seconds": 4})
        target = json.dumps(data, ensure_ascii=False).encode()
        path = self.file("processed.json", target)
        restored = jsonic.cmd_apply_to_bytes(str(path), str(style), allow_comments=False)
        self.assertEqual(jsonic.strip_document(restored, allow_comments=True),
                         jsonic.strip_document(target, allow_comments=False))
        self.assertIn(b'7 /* including the first attempt */', restored)
        self.assertIn(b'/* Position zero: first route checked. */', restored)
        self.assertIn(b'"/new"', restored)

    def test_invalid_inputs_fail_all_operations_without_changing_outputs(self):
        invalid = [
            b'', b' ', b'01', b'-', b'1.', b'1e+', b'+1', b'.1',
            b'NaN', b'Infinity', b'True', b'{}[]', b'[1,]',
            b'{"a":1,}', b'{a:1}', b'{"a" 1}', b'[1 2]',
            b'"bad\\x"', b'"bad\\u12xz"', b'"line\nbreak"', b'"unclosed',
            b'/*unclosed', b"'''unclosed", b'/*only*/', b'1/*x*/2',
            b'{"a":1,"a":2}', b'{"a":1,"\\u0061":2}',
            b'{"value":"\xff"}', b'{"\xff":1}', b'{/*\xff*/"x":1}',
        ]
        style = self.file("valid.style", b'{}')
        for source in invalid:
            path = self.file("invalid.jsonic", source)
            for operation in ([], ["--raw"], ["--strip"], ["--apply", style]):
                with self.subTest(source=source, operation=operation):
                    output = self.file("existing-output", b"unchanged")
                    result = self.cli(path, *operation, "-o", output)
                    self.assert_error(result)
                    self.assertEqual(output.read_bytes(), b"unchanged")

    def test_comments_in_json_rejected_by_every_operation(self):
        path = self.file("strict.json", b'{"x":/*not permitted here*/1}')
        style = self.file("empty.style", b'{}')
        for operation in ([], ["--raw"], ["--strip"], ["--apply", style]):
            with self.subTest(operation=operation):
                self.assert_error(self.cli(path, *operation))

    def test_retained_trailing_comma_example_is_rejected(self):
        result = self.cli(FIXTURES / "reject-trailing-comma.jsonic", "--raw")
        self.assert_error(result)

    def test_file_errors_are_concise(self):
        path = self.file("valid.json", b'{"x":1}')
        for args in (
            [self.work / "missing.json", "--raw"],
            [path, "--apply"],
            [path, "--raw", "-o", self.work / "missing-directory" / "out.json"],
        ):
            with self.subTest(args=args):
                self.assert_error(self.cli(*args))

    def test_in_place_operations_preserve_mode_and_restore_capture(self):
        original = b'/*header*/{\n "x": 1 /*tail*/\n}\n'
        path = self.file("in-place.jsonic", original)
        if os.name == "posix":
            path.chmod(0o640)
        self.assert_ok(self.cli(path))
        self.assert_ok(self.cli(path, "--strip", "-o", path))
        self.assertEqual(json.loads(path.read_bytes()), {"x": 1})
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
        self.assert_ok(self.cli(path, "--raw", "-o", path))
        self.assertEqual(path.read_bytes(), b'{"x":1}')
        self.assert_ok(self.cli(path, "--apply", "-o", path))
        self.assertEqual(path.read_bytes(), original)
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_recapture_and_in_place_writes_without_fchmod(self):
        original = b'/*header*/{ "x": 1 }\n'
        path = self.file("portable.jsonic", original)
        # Exercise the missing API locally; this is not a native Windows run.
        with patch.object(jsonic, "os", wraps=os) as platform_os:
            del platform_os.fchmod
            self.assertFalse(hasattr(platform_os, "fchmod"))
            for operation in ([], [], ["--strip"], ["--raw"], ["--apply"]):
                args = [str(path), *operation]
                if operation:
                    args += ["-o", str(path)]
                self.assertEqual(jsonic.main(args), 0)
            self.assertEqual(path.read_bytes(), original)

    def test_capture_cannot_replace_its_input(self):
        original = b'{ "x": 1 }'
        path = self.file("source.json", original)
        self.assert_error(self.cli(path, "-o", path))
        self.assertEqual(path.read_bytes(), original)

    @unittest.skipUnless(os.name == "posix", "POSIX permissions and symlinks")
    def test_output_symlink_is_followed_without_losing_permissions(self):
        path = self.file("input.json", b'{ "x": 1 }')
        target = self.file("target.json", b"old")
        target.chmod(0o640)
        link = self.work / "link.json"
        link.symlink_to(target.name)
        self.assert_ok(self.cli(path, "--raw", "-o", link))
        self.assertTrue(link.is_symlink())
        self.assertEqual(target.read_bytes(), b'{"x":1}')
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)

    def test_apply_cannot_replace_its_style(self):
        path = self.file("source.jsonic", b'{ "x": 1 }')
        self.assert_ok(self.cli(path))
        style = self.work / "source.jsonic.style"
        original = style.read_bytes()
        self.assert_error(self.cli(path, "--apply", "-o", style))
        self.assertEqual(style.read_bytes(), original)

    def test_deep_input_reports_an_error_instead_of_traceback(self):
        path = self.file("deep.json", b"[" * 600 + b"0" + b"]" * 600)
        result = self.cli(path, "--raw")
        self.assert_error(result)
        self.assertIn(b"nesting", result.stderr)

    def test_cli_help_and_missing_operation_input(self):
        result = self.cli("--help")
        self.assert_ok(result)
        for option in (b"--raw", b"--mini", b"--minified", b"--strip", b"--apply"):
            self.assertIn(option, result.stdout)
        self.assertNotEqual(self.cli().returncode, 0)
        path = self.file("valid.json", b"[]")
        self.assertNotEqual(self.cli(path, "--strip", "--raw").returncode, 0)

    def test_generated_documents_preserve_bytes_and_data(self):
        rng = random.Random(37031)
        gaps = [b"", b" ", b"\t", b"\r\n", b"/*note*/", b"//note\n", b"'''note\nline'''",
                "/* 日本語 */".encode()]
        tokens = [b"null", b"true", b"false", b"-0", b"1.00E+03", b'"\\u0061\\/"',
                  b'"// and /* are data"', '"日本語"'.encode()]

        def gap():
            return rng.choice(gaps)

        def document(depth=0):
            kind = rng.choice(("scalar",) if depth >= 4 else ("scalar", "array", "object"))
            if kind == "scalar":
                return rng.choice(tokens)
            count = rng.randrange(5)
            if kind == "array":
                return b"[" + gap() + (b"," + gap()).join(
                    document(depth + 1) + gap() for _ in range(count)) + b"]"
            keys = rng.sample(["a", "b", "~", "/", "", "π", "a/b~c"], count)
            return b"{" + gap() + (b"," + gap()).join(
                json.dumps(key).encode() + gap() + b":" + gap() + document(depth + 1) + gap()
                for key in keys) + b"}"

        for case in range(300):
            with self.subTest(case=case):
                source = gap() + document() + gap()
                raw = self.roundtrip(source)
                json.loads(raw)

    def test_a_thousand_commented_records(self):
        source = b"[\n" + b",\n".join(
            b'  /* record */ {"id":' + str(i).encode() + b',"active":true}'
            for i in range(1000)
        ) + b"\n]"
        raw = self.roundtrip(source)
        self.assertEqual(json.loads(raw)[-1], {"id": 999, "active": True})


if __name__ == "__main__":
    unittest.main()
