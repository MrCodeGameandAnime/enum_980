# MicroPython 1.29.0 port plan

The user corrected the runtime target: use MicroPython 1.29.0, not the older
experimental tree. Keep the preview work as reference and preserve all original
project and c3b5aae baseline files. No commit, push or PR is authorized.

## Verified pins

- Library: c3b5aaeb61c33ee13c70a6d3dfcd95a8b185e297.
- Its tools/ci.sh clones micropython/micropython without selecting a preview pin.
- Core base: 0fd6c573ea815774668bbb16b8e197c8822368b2 (v1.29.0).
- Metaclass prerequisite implementation: Andrew Leech's
  b5df14fe6560cce5fb23758692baad8f37955c88, parent
  2dc2e30d98ee225070e990586526f8e43b3c95a2.

## Implementation

- [x] Record exact 1.29.0 input and prerequisite commit-patch hashes.
- [x] Apply only the prerequisite's six-file implementation delta to an isolated
  1.29.0 tree, retaining all other 1.29.0 files.
- [x] Port the reviewed metaclass/JSON/mapping corrections onto that tree.
- [x] Build Windows Win32 with the same four required feature flags.
- [x] Run runtime and enum parity, original suites and DD corpus, normal/optimized.
- [x] Compare the unmodified and patched 1.29.0 interpreters across upstream
  basics/JSON tests; document any changed failures and skip sets.
- [x] Export a complete patch set against 1.29.0 and verify clean application.
- [x] Update the current review entry point, preserving preview evidence as history.

Passing these checks establishes the tested 1.29.0 target. It does not by itself
establish compatibility with a newer upstream main commit or claim that the
patched interpreter is an unmodified stock release.

## Outcome

Completed on the exact 1.29.0 source base. See runtime-129-review.md for
verification, patch series and unqualified environments. Publication remains held.
