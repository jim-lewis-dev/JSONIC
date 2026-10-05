# Three practical examples

From the project directory, run:

```bash
python3 examples/demo.py
```

On Windows, use `py` instead of `python3`. The demo uses the actual CLI and
Python's ordinary `json` library. All generated files are temporary; the
examples stay unchanged. It verifies exact restoration through both `--raw`
and `--pretty`, then checks that each edited document retains the editor's
data and token spellings.

## Change a setting without losing its explanation

[settings.jsonic](../examples/settings.jsonic) starts with:

```jsonc
{
  "attempts": 3 /* Total attempts, including the first request. */,
  "enabled": true
}
```

JSONIC captures the presentation and exports:

```json
{"attempts":3,"enabled":true}
```

Python loads that ordinary JSON, sets `attempts` to `5`, and writes it back.
Restoration produces:

```jsonc
{
  "attempts": 5 /* Total attempts, including the first request. */,
  "enabled": true
}
```

The explanation sits before the comma, so it belongs to `attempts`.

## Change the fallback order

[priority-array.jsonic](../examples/priority-array.jsonic) describes ordered
configuration sources. Its comments explain priority slots. The demo reorders
the values, appends a fallback, then shortens the array. Omitting the shared
header, the outputs are:

```jsonc
["network" /* First choice. */, "local" /* Second choice. */, "cache" /* Third choice. */]
["network" /* First choice. */, "local" /* Second choice. */, "cache" /* Third choice. */,"defaults"]
["network" /* First choice. */]
```

The new fourth position has no captured comment or spacing. Missing positions
leave no comments at the bottom. Applying does not erase the capture: the demo
regrows the array and verifies those saved slot comments return. Recapture the
current annotated file when you want to replace the saved presentation.

## Edit a nested application configuration

[config.jsonic](../examples/config.jsonic) includes retry settings, ordered
routes, Unicode, escaped strings, literal comment markers, and empty containers.
The demo changes nested values, appends `/metrics`, replaces optional overrides
with `false`, and removes the queue setting.

The outer field note survives the type change:

```jsonc
"empty_options": false /* Optional overrides; false disables them. */
```

Its former interior note and the deleted queue's note are omitted. The new
route has no invented presentation. Python changes `1.00E+01` to `10.0` while
serializing; JSONIC preserves that returned spelling, not the earlier one.

Inspect readable ordinary JSON without writing any files:

```bash
python3 jsonic examples/config.jsonic --pretty
```

The [demo source](../examples/demo.py) shows each edit. Focused integration tests
compare complete expected documents, check edited data independently, and
verify the demo leaves no files behind:

```bash
python3 -m unittest discover -s tests -p test_examples.py -v
```
