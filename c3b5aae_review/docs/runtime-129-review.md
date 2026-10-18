# Current review: MicroPython 1.29.0

## Corrected target

This is the current runtime-backed review. It supersedes the preview-based
qualification in runtime-profile-review.md. The implementation now builds from
**micropython/micropython v1.29.0**, commit
`0fd6c573ea815774668bbb16b8e197c8822368b2`.

The library pin `c3b5aaeb61c33ee13c70a6d3dfcd95a8b185e297` does **not** pin
MicroPython 1.28.0-preview. Its tools/ci.sh clones micropython/micropython's
default branch without selecting a revision. Using the older preview as our runtime
base was therefore unnecessary and has been corrected.

The metaclass prerequisite is ported as Andrew Leech's specific implementation
commit `b5df14fe6560cce5fb23758692baad8f37955c88`; the rest of the older preview
source tree is not used. That prerequisite retains its original attribution.
Our metaclass/JSON/mapping corrections are separate patches against the 1.29.0 port.

## What was retained from 1.29.0

Every tracked 1.29.0 source file is retained. Only eight intended source files
change:

- py/modbuiltins.c
- py/mpconfig.h
- py/obj.h
- py/objobject.c
- py/objtype.c
- py/vm.c
- py/obj.c
- py/objdict.c

[The source-scope record](../root/results/runtime-129/port-scope.json) records
base and ported hashes. The source version remains 1.29.0. The copied-source
build explicitly sets its label to `v1.29.0-enum980-review`, preventing it from
mistakenly inheriting the parent enum_980 repository's Git hash.

This remains a **patched 1.29.0 runtime**, not unmodified stock MicroPython.
The four metaclass feature flags in root/config/compat.props are required.
The port targets the release commit; a moving upstream main branch still needs
its own integration check at submission time.

## Behavior verified

The same runtime-backed enum implementation closes the four requested boundaries
on the new base:

- Real declared classes and correctly typed string members.
- Class length and canonical name subscription, including error cases.
- Selective member mutation protection and read-only public name-to-member metadata.
- Class/member enum representation while preserving string operations.
- Correct JSON values, nested values and dictionary keys, including escaping,
  control characters, Unicode and a string subclass overriding repr/str.

Functional creation, declared methods, ordinary helper attributes, hook composition
and both module import orders remain covered. The original Enum/mini suites and
DD corpus run against this exact 1.29.0 build.

## Evidence

- **33 qualification commands pass**, native CPython 3.12.14 and patched
  MicroPython 1.29.0, normal and optimized modes.
- All **11 DD requirement groups** pass over the unchanged 61-observation corpus.
- **549 upstream basics/JSON tests pass on both unmodified and patched 1.29.0**,
  17,403 individual cases per interpreter, identical 40-test skip sets and zero
  new failures.
- The upstream suite uses unittest from 1.29.0's own micropython-lib submodule
  pin `ee4bb8ff139e24c42b739935fbd8ec7c4d061e02`, verified against its Git blob hash.
- The complete six-patch core/library series applies cleanly to pristine,
  Git-normalized 1.29.0 and c3b5aae source copies and reproduces all changed sources.
- Ruff 0.11.6 passes with the pinned library configuration.

[Targeted qualification, runtime identity and input hashes](../root/results/runtime-129-profile/verification.json)

[Stock/patched upstream comparison](../root/results/core-regression-129-qualified/comparison.json)

[Test dependency pin](../root/build/runtime-129-test-dependency.json)

The first upstream attempt stopped at a missing unittest dependency and is not
counted as passing. The correct pinned dependency was installed before the final
successful comparison. Earlier preview results are historical evidence only.

## Current code and patches

- [Runtime-backed enum source](../root/metaclass/enum.py)
- [Boundary parity tests](../root/tests/test_full_parity.py)
- [General runtime contracts](../root/tests/test_runtime_contracts.py)
- [1.29.0 source preparation](../root/src/prepare_runtime_129.py)
- [Pinned test dependency preparation](../root/src/prepare_runtime_129_deps.py)
- [1.29.0 build helper](../root/src/build_runtime_129.ps1)
- [Current targeted verification](../root/src/verify_runtime_profile.py)
- [Current upstream comparison](../root/src/verify_core_regressions.py)
- [Patch export and clean-application verification](../root/src/export_runtime_129.py)

[Complete series manifest, hashes and attribution](../root/patches/runtime-129/manifest.json)

Apply core patches 0001 through 0005, in order, to the pinned 1.29.0 source.
Apply library patch 0006 separately to the pinned c3b5aae library. The library
profile requires the patched core; it is not a standalone cure for stock 1.29.0.
The core series contains the entire prerequisite delta, so no preview checkout
is needed to apply it.

The generic prepare/build/export/check entry points now dispatch to the 1.29.0
workflow. Explicitly named *_preview scripts preserve the previous workflow.
The original stock candidate in root/upstream/ remains unchanged.

## Commands

From enum_980, using CPython 3.12:

```powershell
python -B c3b5aae_review/root/src/prepare_runtime_129.py
python -B c3b5aae_review/root/src/prepare_runtime_129_deps.py
./c3b5aae_review/root/src/build_runtime_129.ps1
python -B c3b5aae_review/root/src/verify_runtime_profile.py
python -B c3b5aae_review/root/src/verify_core_regressions.py
python -B c3b5aae_review/root/src/export_runtime_129.py
```

Preparation references the existing clean pinned stock checkout; the dependency
helper uses authenticated gh to read the exact public dependency blob. Exported
patches can instead be applied directly to separately obtained pinned sources.
The local build helper expects MSBuild/v145 and the configured CPython runtime.

## Scope and publication

The same intentional subset restrictions remain: direct single inheritance,
rejected custom constructors/duplicate values, legacy functional/name-lookup
extensions, and separate Enum/IntEnum container behavior. The public read-only
mapping is not CPython's mappingproxy type. This is targeted compatibility work,
not a claim that the entire CPython Enum module or every metaclass protocol is
implemented.

Qualification is Windows Win32. Unix, physical boards, constrained heaps and
performance remain unqualified for this revision. No independent reviewer has
reviewed this new port yet.

All work stays in c3b5aae_review. The original project, c3b5aae baseline and stock
candidate are preserved. No new commits, pushes or PRs have been made for this port. Intended author
for our commits remains MrCodeGameAndAnime <MrCodeGameAndAnime@gmail.com>;
Andrew Leech's prerequisite remains separately attributed.
