"""Run the README workflow using the real CLI and temporary files."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "jsonic"
EXAMPLES = ROOT / "examples"


def run(*args):
    subprocess.run([sys.executable, str(PROGRAM), *map(str, args)], check=True)


def show(label, data):
    print(label, flush=True)
    print(data.decode("utf-8").rstrip(), flush=True)
    print(flush=True)


def require(condition, message):
    if not condition:
        raise SystemExit("Demo failed: " + message)


def main():
    with tempfile.TemporaryDirectory(prefix="jsonic-demo-") as directory:
        work = Path(directory)
        source = EXAMPLES / "settings.jsonic"
        style = work / "settings.jsonic.style"
        data = work / "settings.json"
        restored = work / "restored.jsonic"

        original = source.read_bytes()
        show("Annotated configuration", original)
        run(source, "-o", style)
        run(source, "--raw", "-o", data)
        show("Ordinary JSON for any JSON tool", data.read_bytes())
        run(data, "--apply", "-o", restored)
        require(restored.read_bytes() == original, "unchanged round trip")

        # This step uses only Python's ordinary JSON library.
        values = json.loads(data.read_bytes())
        values["attempts"] = 5
        data.write_bytes(json.dumps(values, separators=(",", ":")).encode("utf-8"))
        run(data, "--apply", "-o", restored)
        expected = original.replace(b'"attempts": 3', b'"attempts": 5')
        require(restored.read_bytes() == expected, "changed value with saved presentation")
        show("After an ordinary JSON edit and restoration", restored.read_bytes())

        array_source = work / "positions.jsonic"
        array_data = work / "positions.json"
        array_output = work / "positions-restored.jsonic"
        array_source.write_bytes(b'[/* first */10,/* second */20]\n')
        run(array_source)
        array_data.write_bytes(b'[99]')
        run(array_data, "--apply", "-o", array_output)
        require(array_output.read_bytes() == b'[/* first */99]\n', "absent array position")
        show("Array capture", array_source.read_bytes())
        show("Restored onto [99]: absent position receives no comment", array_output.read_bytes())

        complex_source = EXAMPLES / "config.jsonic"
        complex_style = work / "config.jsonic.style"
        complex_data = work / "config.json"
        complex_output = work / "config-restored.jsonic"
        run(complex_source, "-o", complex_style)
        run(complex_source, "--raw", "-o", complex_data)
        json.loads(complex_data.read_bytes())
        run(complex_data, "--apply", "-o", complex_output)
        require(complex_output.read_bytes() == complex_source.read_bytes(), "complex round trip")

    print("PASS: exact restoration, a real JSON edit, positional comments, and the complex example.")


if __name__ == "__main__":
    main()
