> **Resolved:** the lifecycle finding below is closed by [the qualified correction](lifecycle-fix.md). This report preserves the original findings.

# Final diff review

## Outcome

The requested diff review and real Unix qualification are complete. The tested
StrEnum subset passes, but the borrowed core prerequisite still has a known
metaclass initialization-order defect. Resolve that before describing the whole
core proposal as CPython-compatible or ready to merge. A package-only PR cannot
provide this profile on stock MicroPython.

## Findings

### Open: metaclass initialization runs inside type.__new__

The borrowed prerequisite calls metaclass `__init__` from `mp_obj_new_type` in
`py/objtype.c` (around line 1701 of the patched 1.29.0 tree). When a custom
metaclass `__new__` calls `type.__new__`, initialization happens before that
custom `__new__` finishes.

```python
events = []
class M(type):
    def __new__(meta, name, bases, namespace):
        events.append("new-before")
        cls = type.__new__(meta, name, bases, namespace)
        events.append("new-after")
        return cls
    def __init__(cls, name, bases, namespace):
        events.append("init")
class C(metaclass=M):
    pass
```

CPython records `new-before, new-after, init`; both patched Unix versions record
`new-before, init, new-after`. Initialization can therefore observe unfinished
class state. This is inherited from the prerequisite, not introduced by the
StrEnum library. The StrEnum metaclass does not define an initialization hook,
so the qualified library profile does not exercise this mismatch.

The fix belongs in the core construction/call lifecycle, followed by direct and
inherited hook-order regression tests and repeat qualification. It is not a
README-only limitation for a general-purpose metaclass contribution.

[Reproduction and both Unix outputs](../root/results/unix/run-20261018T181738Z/final-review-checks.json)

### Fixed: exported documentation described the wrong architecture

The older library diff retained the upstream statement “without metaclasses” and
did not export the runtime-profile README. The final candidate now includes the
required four build flags, core dependency order, supported subset, original
container behavior, hook costs/limits, and source attribution. The module header
and metadata comment now distinguish typed StrEnum from the older containers.
The README example passes on both actual Unix builds.

### Fixed: optional-feature core test failed on stock configurations

The exported general runtime contract now emits `SKIP` when JSON/metaclass
operators are unavailable. Both stock Unix builds take that path. The dedicated
qualification requires exactly eight successful checks, so it cannot silently
accept that skip. Both patched builds execute all eight checks in normal and
optimized modes.

### Fixed: patch export and CI details

The revised library patch adds full parity as its own CI test-list entry and
preserves upstream files that lack a final newline using a valid patch marker.
Candidate Python files pass Ruff 0.11.6 with the pinned upstream configuration.

## Contribution and dependency boundaries

1. Andrew Leech's original custom-metaclass prerequisite remains a byte-identical
   mail patch with his author and Signed-off-by. Do not relabel it as our work.
2. JSON native-string storage, mapping input, metaclass corrections, and runtime
   regressions are separate core changes. The open lifecycle issue also belongs
   here. These must be reviewed against MicroPython core.
3. The typed StrEnum library change is based on IhorNehrutsa's PR #980 and credits
   the DD member-construction adaptation to MrCodeGameAndAnime. It depends on the
   patched core and cannot be offered as a stock-compatible drop-in update.
4. New review diffs remain uncommitted. If commits are later authorized, use
   `MrCodeGameAndAnime <MrCodeGameAndAnime@gmail.com>` for the user's actual work
   and preserve the other authors' existing attribution. Accepted commit history
   determines contributor credit; this review does not guarantee acceptance.

## Current artifacts

Use [the final candidate](../root/release_candidate/library/README.md) and
[its revised patch manifest](../root/release_candidate/patches/manifest.json).
Both pinned core bases and the library base accept the patches cleanly, and all
changed source/test/document contents are reproduced by application.

The previous runtime-129/runtime-130 series, qualified sources and baseline
remain intact. The 6,823-file preview integrity check still passes and confirms
that all recorded 1.29.0 qualification inputs match their original hashes.
The top-level tracked project files have no changes.

[Patch application evidence](../root/release_candidate/patches/application-check.json)

[Real Unix qualification](unix-qualification.md)

Nothing was committed, pushed, posted or opened as a PR.
