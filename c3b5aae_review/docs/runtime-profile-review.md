> **Historical preview qualification.** Superseded by [the current 1.29.0 review](runtime-129-review.md). Current build and verification entry points now target 1.29.0.

# Runtime-backed typed StrEnum review

## Outcome and boundary

The four requested gaps and the JSON dictionary-key defect are implemented and
verified in a separate runtime-backed profile. This is ready for the user's code
review, not publication. Nothing has been committed, pushed, or submitted as a PR.

The profile requires a patched experimental interpreter based on
`andrewleech/micropython@6a56288ad12aca9d99d1e425e1400a53c65aa709`
(MicroPython 1.28.0-preview, Windows Win32), with these flags enabled:

- `MICROPY_PY_METACLASS_INIT`
- `MICROPY_PY_METACLASS_OPS`
- `MICROPY_PY_METACLASS_PROPERTIES`
- `MICROPY_PY_METACLASS_PREPARE`

It is not a solution that runs unchanged on stock MicroPython 1.29.0. Runtime
prerequisites must be reviewed/landed before the corresponding library profile
can be proposed as a default. The metaclass prerequisite is existing work by
others; the review patches are deltas against that exact pin, not a claim of
having implemented the prerequisite itself.

## Implemented behavior

| Operation | Runtime-backed result |
| --- | --- |
| Declared name and members | Actual class; `type(Mode.FAST) is Mode` |
| Class length | `len(Mode)` reports member count |
| Name subscription | Canonical member; missing names raise KeyError; unhashable keys raise TypeError |
| Class iteration | Typed members; native string member indexing still works |
| Class mutation | Member replacement/deletion rejected; ordinary helper attributes allowed |
| Member mutation | Name/value protected; ordinary helper attributes allowed |
| Public metadata | Read-only name-to-member mapping; cannot clear, overwrite or delete it |
| Class representation | `<enum 'Mode'>` |
| Member representation | `<Mode.FAST: 'fast'>`; native string conversion preserved |
| JSON values and keys | Native string storage encoded correctly, including quotes, escapes, control characters and Unicode |
| Functional API | Direct creation and canonical lookup retained |

The public member mapping is a read-only snapshot implementing the exercised
mapping operations; it is not CPython's `mappingproxy` type. Deliberate access to
private implementation state is outside public mutation guarantees, as it also
is for CPython's private enum internals.

## Runtime changes

1. Metaclass operations: subscription and assignment/deletion dispatch, explicit
   raw `type.__setattr__` / `type.__delattr__` delegates, and metaclass repr.
2. Class recognition: custom-metaclass classes accepted by subclass/instance
   checks and native-base/super paths. Dynamic `type(name, bases, namespace)`
   selects the appropriate metaclass and rejects conflicting/invalid inputs.
3. Keyword call forwarding: preserve every positional and keyword argument,
   including calls exceeding the stack argument buffer. The prerequisite's
   keyword path could assert/crash before this fix.
4. JSON: encode native string storage independently of custom Python repr,
   and avoid duplicate quoting of string-subclass dictionary keys.
5. Mapping inputs: dict construction/update honors a mapping's keys/getitem
   protocol. This permits normal `dict(Mode.__members__)` conversion rather
   than requiring an enum-specific workaround.

Ordinary classes retain their instance protocols. Regression tests also cover
inherited metaclass operations and invalid raw setter/deleter receivers.

## Review locations

- [Runtime-backed enum](../root/metaclass/enum.py)
- [Shared boundary parity tests](../root/tests/test_full_parity.py)
- [General runtime contracts](../root/tests/test_runtime_contracts.py)
- [Runtime preparation](../root/src/prepare_compat_runtime.py)
- [Profile preparation](../root/src/prepare_metaclass_profile.py)
- [Build helper](../root/src/build_compat_runtime.ps1)
- [Profile verification](../root/src/verify_runtime_profile.py)
- [Upstream regression verification](../root/src/verify_core_regressions.py)

The existing stock candidate remains under `root/upstream/`. Its six previously
qualified implementation/test hashes remain unchanged. The pinned `c3b5aae/`
reference and original tracked project files remain unchanged.

## Verification evidence

- CPython 3.12.14 reference and forced overlay, plus the patched experimental
  MicroPython runtime; normal and optimized modes.
- 33 qualification commands passed: 8 general runtime contract groups,
  4 boundary parity groups, shared/profile/hook checks, both module orders,
  and original 13 enum plus 7 mini tests on MicroPython.
- The original 61-observation corpus passes all 11 DD requirement groups.
  This is not a claim that every diagnostic or every CPython Enum feature matches.
- Broader differential check: 548 upstream basics/JSON tests passed on both the
  unmodified prerequisite and patched runtime, 17,080 individual cases each;
  identical 43-test skip sets; zero new failures.
- Ruff 0.11.6 passes with the pinned upstream project configuration.
- All five patches apply cleanly to Git-normalized pinned source copies and
  reproduce the verified runtime/enum source text.

An earlier broad extmod attempt stopped because a machine test required an
uninstalled unittest package; it is retained as diagnostic evidence and is not
counted as a successful run. That attempt also caught an invalid type-factory
input regression, which was fixed before the final passing basics/JSON run.

[Qualification and input hashes](../root/results/runtime-profile/verification.json)

[Upstream comparison, skips and runtime hashes](../root/results/core-regression-final/comparison.json)

## Patch set

Apply the core patches to the pinned experimental core in this order:

1. [JSON string subclasses](../root/patches/json-string-subclasses.patch)
2. [Dictionary mapping inputs](../root/patches/dictionary-mapping-input.patch)
3. [Metaclass operations and correctness](../root/patches/metaclass-operations.patch)
4. [Runtime regression tests](../root/patches/runtime-regression-tests.patch)

Apply the separate [library profile patch](../root/patches/typed-strenum-runtime-profile.patch)
to the library baseline `c3b5aaeb61c33ee13c70a6d3dfcd95a8b185e297` only with the
runtime prerequisites available. It includes the regression scripts and proposed
package-test list. The earlier stock-profile patch is preserved as historical work.

[Patch hashes and intended commit author](../root/patches/runtime-profile-patches.json)

The patches have no commit identity until committed. Intended author and eventual
Signed-off-by identity: `MrCodeGameAndAnime <MrCodeGameAndAnime@gmail.com>`.
Upstream must preserve that authorship when incorporating this contribution.

## Repeat the targeted qualification

From enum_980:

```powershell
& 'C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B c3b5aae_review/root/src/verify_runtime_profile.py
```

To prepare/build locally using the existing pinned prerequisite sources:

```powershell
python -B c3b5aae_review/root/src/prepare_compat_runtime.py
./c3b5aae_review/root/src/build_compat_runtime.ps1
python -B c3b5aae_review/root/src/prepare_metaclass_profile.py
```

The local preparation scripts reference preserved source/tool locations in this
investigation. For another checkout, obtain the exact prerequisite core pin and
apply the exported patches; the source tree itself is not embedded in the patches.
The profile generator uses the investigation's pinned Ruff installation.

## Scope still deliberately limited

This closes the enumerated boundaries; it does not implement all of CPython's
Enum module. Existing restrictions such as direct single inheritance, rejected
custom constructors/duplicate values, legacy functional/name-lookup extensions,
and the separate Enum/IntEnum container profiles remain. Class declaration order
is not newly guaranteed. No claim is made that all possible metaclass protocols
are complete in the underlying experimental prerequisite.

There is no Unix-port, physical-board, constrained-heap, performance or independent
review qualification for this revision. The remaining work before publication is
reviewing this exact diff and agreeing on the runtime/library dependency path,
not pretending the library patch alone repairs stock MicroPython.
