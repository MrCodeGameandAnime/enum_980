> **Resolved:** the confirmed dictionary defect below is closed by [the qualified core correction](dictionary-fix.md). Original findings remain below.

# Independent check of Claude's profile report

## Confirmed: dictionary string-subclass asymmetry

Reproduced on stock and our exact qualified patched builds of MicroPython
1.29.0 and pinned 1.30.0-preview, on actual Unix and Windows ports. Plain string
subclasses reproduce the defect without importing enum. Native CPython 3.12.15
(Unix) and 3.12.14 (Windows) behave correctly. The profile forced on CPython also
behaves correctly.

```python
# Mode.FAST == "fast" and both hashes are equal.
{"fast": 1}[Mode.FAST]  # MicroPython: KeyError; CPython: 1

d = {"fast": 1}
d[Mode.FAST] = 2
len(d)  # MicroPython: 2; CPython: 1
```

Dictionary containment and get() fail in the same direction. The opposite lookup,
`{Mode.FAST: 1}["fast"]`, succeeds. Set membership succeeds in both directions in
the probes. Adding an integer key to the dictionary makes the failing lookup
succeed, including after that integer key is removed.

### Cause

`mp_map_lookup` in `py/map.c`, around lines 173-188, uses the
`all_keys_are_qstrs` shortcut. An exact non-interned str disables pointer-only
comparison; a string subclass does not. Read lookup returns early as missing,
and insertion can skip equality and add a second equal key. The mixed-key control
bypasses the shortcut and succeeds.

This is a pre-existing core defect, preserved by our patches. Earlier parity
coverage tested member-stored/raw-lookup direction and missed the reverse case.
A separate core correction and regressions are required before claiming
bidirectional dictionary-key compatibility. No implementation was changed here.

## Clarified: iteration

On native CPython and the final profile on CPython/MicroPython,
`list(Mode.FAST)` yields `["f", "a", "s", "t"]`.

`list(Mode())` raises TypeError on native CPython because Mode() requires a value;
it yields members in our profile because the documented no-argument extension
returns the class. Claude's “iterate_instance” row is consistent with the latter
expression, not member iteration. Its exact harness is needed to establish which
expression it used.

## Reporting corrections

- Commit `64097a2a723e22d04beebcd83b0e339c968b8f50` belongs to enum_980.
  The report's enum SHA-256 exactly matches our final library. It should identify
  this as our candidate rather than an independently pinned upstream PR head.
- The tested core must be identified by commit, patches/configuration and runtime
  label. The typed profile requires patched core; version 1.29.0 alone is
  insufficient to reproduce it.
- The committed final README explicitly documents duplicate-value rejection and
  unspecified declaration order. Those are not undocumented findings.
- Name-key mapping contents are correct in these observations; ordering is a
  separate documented difference.

## Evidence

[Unix reference, forced profile, stock controls and patched runs](../root/results/unix/profile-report-check/results.json)

[Windows reference, stock controls and patched runs](../root/results/profile-report-check-windows.json)

[Diagnostic probe with explicit expressions](../root/src/probe_profile_report.py)

All runtime binary hashes were checked against their completed qualification
records before execution. Source SHA-256 is recorded with the probe results.
The reference, qualified implementation and previous evidence remain unchanged.
