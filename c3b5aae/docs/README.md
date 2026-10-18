# c3b5aae: upstream commit baseline

This directory isolates the investigation of IhorNehrutsa's upstream commit
`c3b5aaeb61c33ee13c70a6d3dfcd95a8b185e297` on branch `enum`.
The existing project outside `c3b5aae/` and `c3b5aae_review/` remains the original
working baseline. Its files, source pins, reports and CI are unchanged.

## Contents

- `root/upstream/`: full source tree exported from the exact upstream commit,
  including its enum implementation, original tests, examples and contribution rules.
  This is an upstream-layout snapshot. Treat it as reference material.
- `root/source.json`: commit, tree ID and relevant source/corpus hashes.
- `root/src/cases.py`: byte-preserved copy of the original shared 61-observation corpus.
- `root/tests/test_strenum_identity.py`: shared CPython-reference probe, expected
  to expose the typed-member gap in this baseline. It is additional investigation
  coverage, not a test present in the upstream commit.
- `root/results/`: copied measurements of this upstream commit and the native
  reference. Recorded paths describe where those measurements originally ran.

The recorded comparison meets 9 of the original 11 DD requirement groups.
The shared identity probe fails declared-class identity, direct JSON serialization
and declared-member methods on this baseline. The upstream enum suite passes 13
checks; the mini suite has a pre-existing len(Color) error even though its runner
returns exit code zero. These are copied historical results, not a new execution.

## Reproduction

From this directory, with CPython 3.12 and stock MicroPython 1.29.0:

```sh
python -I -B root/src/cases.py cpython
micropython root/src/cases.py pr root/upstream/python-stdlib/enum
```

Use your actual interpreter path where necessary. The source checkout and generated
logs are excluded from the parent repository by this directory's local ignore rules.
If the upstream snapshot is absent, recreate it from the repository and exact
revision in `root/source.json`, rather than substituting the moving branch head.

All implementation changes, further review and candidate verification belong in
[the review directory](../../c3b5aae_review/docs/README.md). Keep this upstream
source snapshot pinned; document any further baseline measurements separately.
