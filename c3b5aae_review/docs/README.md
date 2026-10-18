> **Current revision:** [qualified dictionary-key correction](dictionary-fix.md) and [complete patch series](../root/dictionary_final/patches/manifest.json). The prior profile report finding is resolved; earlier revisions below are historical.

> **Current revision:** [qualified lifecycle correction](lifecycle-fix.md) and [final patch manifest](../root/lifecycle_final/patches/manifest.json). Earlier candidates and reports below are historical.

> **Final review:** [diff review and remaining core issue](final-review.md),
> [real Unix qualification](unix-qualification.md), and
> [final candidate revision](../root/release_candidate/library/README.md).
> Earlier working locations and measurements below are retained as history.

> **Qualified targets:** [MicroPython 1.29.0](runtime-129-review.md) and [1.30.0-preview at 9a3a0c0d5e](runtime-130-review.md). The earlier 1.28.0-preview work is historical.

# c3b5aae review and subsequent implementation

All subsequent implementation, review, regression work and candidate verification
for this contribution belong in this directory. The reference is the pinned
[c3b5aae baseline](../../c3b5aae/docs/README.md). The original investigation at the
project root is preserved.

## Canonical working locations

- `root/upstream/`: independent Git checkout of the candidate contribution.
  Make implementation, package-test, README, example and upstream CI changes here.
  Its existing branch is `fix/strenum-class-identity`.
- `root/candidate.json`: initial candidate/base commit IDs and source hashes.
  This is a captured record, not a live status file.
- `root/patches/strenum-class-identity.patch`: initial reviewable contribution patch.
- `root/results/`: copied initial comparison data and test logs. Save subsequent
  candidate measurements here with their exact source commit and runtime details.
- `docs/initial-review.md`: copied original review notes. Their paths describe the
  previous locations; this README defines the current working locations.

The main files to review inside `root/upstream/` are:

- `python-stdlib/enum/enum.py`
- `python-stdlib/enum/README.md`
- `python-stdlib/enum/test_strenum_identity.py`
- `python-stdlib/enum/test_strenum_profile.py`
- `python-stdlib/enum/enum_usage.py`
- `python-stdlib/enum/CPy/CPy.py`
- `tools/ci.sh`

## Initial candidate snapshot

The local candidate is `abb4e3bc4818f271f90eabb49cb36eea897747e1`, based on
`c3b5aaeb61c33ee13c70a6d3dfcd95a8b185e297`. It meets the original 11 DD
requirement groups in the recorded corpus. It changes the StrEnum public API:
class iteration/subscription/length, class mutation guards, native string repr
and the `StrEnum.create(...)` factory all need deliberate review. Mixin and
class-builder-hook composition remain unqualified. Review the full notes before
considering this ready for publication.

The candidate's new tests are inside its own checkout and are already included in
its package-test list. For the unchanged comparison corpus, reference
`../c3b5aae/root/src/cases.py`; avoid modifying the original project's runner.

## Revision 2 compatibility work

Subsequent uncommitted work restores direct functional creation and class iteration,
fixes cooperative hook/reimport behavior and the missing mini length method, and
rejects unsupported constructor mixins. The initial patch files and measurements
remain historical snapshots. See [the compatibility review](compatibility-review.md)
for the current status, runtime constraints and reproducible verification command.
Current evidence is in `root/results/revision-2/verification.json`.

## Publication hold

No push and no PR until the user explicitly authorizes publication after review.
The GitHub fork exists, but the candidate remains local. The new checkout has
`origin` set to the user's fork and `upstream` set to IhorNehrutsa's repository.
Its Git objects are independent of the old checkout.

The old `root/build/pr980-patch` and `root/results/strenum-patch` locations are
preserved historical copies. Further work goes here. Existing binaries and tools
under the original `root/build/` may be referenced without modifying them; put any
new tools/builds under this directory's `root/build/`.

## Follow-up boundary investigation

See [the remaining-boundaries report](remaining-boundaries.md) before publication.
It confirms the unresolved class operations and adds a JSON dictionary-key defect;
the prior JSON qualification covered scalar/list values. No implementation changes
were made in this follow-up.

## Runtime-backed implementation

The next profile closes the investigated boundaries using explicit runtime
prerequisites. Start with [the current 1.29.0 review](runtime-129-review.md).
The existing stock candidate remains separate and unchanged.

## Additional preview qualification

The unchanged patch series also qualifies on the pinned 1.30.0-preview snapshot.
See [the preview report](runtime-130-review.md) for the exact commit and evidence.
The 1.29.0 base and its qualified inputs remain intact.
