# PR #980 Python-only contribution

## Active candidate

- Upstream base: `c3b5aaeb61c33ee13c70a6d3dfcd95a8b185e297`.
- Restored candidate: `abb4e3bc4818f271f90eabb49cb36eea897747e1`.
- Local checkout: `root/upstream/`, branch `fix/strenum-class-identity`.
- Target: stock MicroPython 1.29.0. Changes are limited to the Python library,
  its tests and documentation.

The checkout is intentionally ignored by the enclosing repository. Its Git
history preserves the candidate commit. The original Python-only patch export
is in `root/patches/strenum-class-identity.patch`.

Later Python-only edits are saved in the checkout's stash:
`87549d633a69fdc00b4b7327abe51a0138a893a6`. They are not applied.

The interpreter experiment and its local builds, patches, tools, snapshots and
reports have been removed. This cleanup does not rewrite earlier Git commits.

## Supported scope

The candidate preserves real StrEnum subclass identity on stock MicroPython.
Class length, class subscription, class mutation protection and enum-style
representation remain outside this candidate's supported profile. See the
candidate's own README for the exact API and limitations.

[Initial review](initial-review.md) records the original candidate and stock
runtime observations. Retained logs are historical evidence, not a new test run.
No implementation tests or builds were run during cleanup.

Publication remains on hold pending the user's review. No commit, push or PR is
authorized by this cleanup.
