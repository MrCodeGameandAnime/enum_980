# Dictionary cross-type key correction

## Result

The confirmed reverse dictionary-key defect is corrected on both pinned runtimes,
on actual Unix standard and Windows Win32 builds. Native CPython agrees with the
new regression outputs. The enum implementation itself is byte-identical to the
preceding qualified candidate.

```python
{"fast": 1}[Mode.FAST]  # 1

d = {"fast": 1}
d[Mode.FAST] = 2
assert len(d) == 1
assert d["fast"] == 2
```

## Core change

Patch 9 changes only `py/map.c`. Interned-string lookups retain pointer comparison.
A non-interned string, or an object marked as supporting cross-type equality,
uses the normal map hash/equality path. This preserves user-defined methods and
the originally stored key, rather than converting every lookup key to a string.
The correction covers ordinary string subclasses and other hashable objects that
compare equal to a string. It adds no enum-specific runtime machinery.

The identical patch applies independently to unmodified 1.29.0 and the pinned
preview. Separate stock-based Unix builds, with no metaclass patches or feature
flags, pass the 16 new core regression groups normally and with optimization.

## Tests and qualification

The new core test has 16 groups covering reads, writes, both lookup directions,
deletion, pop, setdefault, update, deduplication, growth, map layouts, read-only
maps, OrderedDict, custom equality/hash methods, generic equivalent keys and
unhashable subclasses. Four library groups check the same behavior with actual
StrEnum members, including character iteration.

These regressions passed first on native CPython and failed on the previous
MicroPython builds. The corrected complete profile passes them on all four
runtime/port combinations, normally and with optimization. Existing lifecycle,
interpreter, enum, hook and parity tests also pass, including all 11 DD requirement
groups over the unchanged 61 observations.

| Port | Version | Upstream tests passed per build | Individual cases per build | Skips |
| --- | --- | ---: | ---: | ---: |
| Windows | 1.29.0 | 549 | 17,403 | 40 |
| Windows | 1.30.0-preview | 551 | 17,425 | 40 |
| Unix | 1.29.0 | 560 | 17,484 | 29 |
| Unix | 1.30.0-preview | 562 | 17,506 | 29 |

Counts apply separately to stock and patched builds. Every comparison has zero
failures and matching skip sets. The three exported core regression files also
pass through the upstream Unix runner. Original report probes now confirm both
lookup directions and one-key replacement; README examples still pass.

- [Windows qualification, exact commands and input/binary hashes](../root/results/windows-dictionary-final-run-20261018T231915Z/qualification.json)
- [Unix qualification, exact commands and input/binary hashes](../root/results/unix/dictionary-final-run-20261018T231904Z/qualification.json)
- [Exported upstream regressions, source fidelity and original-report probes](../root/results/unix/dictionary-final-run-20261018T231904Z/final-review-checks.json)
- [Standalone core-patch qualification on both source pins](../root/results/unix/dictionary-independent/verification.json)
- [Before-fix regression evidence](../root/results/unix/dictionary-red/results.json)
- [Cross-platform hashes and previous-source preservation](../root/results/dictionary-final-integrity.json)

## Patches and reproduction

Current files are in `root/dictionary_final/`:

- [Complete patch manifest and explicit apply order](../root/dictionary_final/patches/manifest.json)
- [Independent core correction: patch 9](../root/dictionary_final/patches/0009-dictionary-cross-type-keys.patch)
- [Core regressions: patch 10](../root/dictionary_final/patches/0010-dictionary-key-regressions.patch)
- [Library regression and CI entry: patch 11](../root/dictionary_final/patches/0011-strenum-dictionary-tests.patch)
- [Clean source and library application checks](../root/dictionary_final/patches/application-check.json)

The export check also found malformed UTF-8 README context in the preceding
library patch: earlier tooling had decoded the baseline using Windows' default
encoding. This revision regenerates patch 6 from actual upstream UTF-8 text.
The applied library/README contents remain unchanged; the new library regression
and CI entry are separate patch 11. The new series applies cleanly to both core
pins and the c3b5aae library baseline.

Saved tooling under `root/src/` includes `export_dictionary_final.py`,
`qualify_unix_dictionary_final.py`, `qualify_windows_dictionary_final.py`,
`verify_dictionary_independent.py`, `verify_dictionary_unix.py` and
`verify_dictionary_integrity.py`. Unix uses the existing pinned Docker image and
Linux work volume; Windows uses CPython 3.12 and the existing MSBuild configuration.
Candidate Python lint passes under the pinned upstream Ruff configuration.

Previous qualified sources, binaries, patches and their recorded inputs remain
intact. Existing attribution is preserved. All new corrections remain local,
uncommitted review work; nothing was pushed or submitted.
