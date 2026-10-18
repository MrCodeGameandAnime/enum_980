# StrEnum patch: local review

Publication is on hold at the user's request. No branch has been pushed and no
PR has been opened. An empty GitHub fork was created before that instruction.

## Exact scope

- Base: IhorNehrutsa/micropython-lib, branch `enum`, commit
  `c3b5aaeb61c33ee13c70a6d3dfcd95a8b185e297`.
- Local contribution: `abb4e3bc4818f271f90eabb49cb36eea897747e1`.
- Local branch: `fix/strenum-class-identity`.
- Author and Signed-off-by: MrCodeGameandAnime, using the supplied Gmail address.
- Seven changed files. The original investigation baselines and DD remain intact.

## Implementation

`StrEnum` inherits `str` and `Enum`. Its finalizer constructs genuine instances
of the declared subclass, attaches metadata, and installs canonical value lookup.
The class-builder hook returns that class. Native string behavior supplies JSON
encoding and hashing. The code and README attribute the finalization mechanism
to DD and link the pinned original source.

## Public API decisions requiring review

This proposal changes the StrEnum public API. It retains the existing Enum,
IntEnum and mini container implementations.

1. Typed StrEnum class iteration, class subscription and `len(Class)` are absent.
   Ordinary class member assignment/deletion is not intercepted. This is the
   stock-runtime tradeoff for preserving the actual declared class.
2. Functional creation uses `StrEnum.create(...)`; the old `StrEnum(name, names)`
   call is not retained. Stock MicroPython does not expose `str.__new__`, so native
   allocation must remain available until finalization installs lookup.
3. Native string repr is retained for correct stock-MicroPython JSON encoding.
   Enum-style repr is absent for typed StrEnum.
4. The existing nonstandard member-to-value mapping, name lookup by call, callable
   members and optional no-argument initialization remain.
5. Custom constructors, reserved manifest declarations and extending finalized
   typed enums are rejected. Multiple-inheritance/mixin interactions and global
   hook reload/composition need further review; no general compatibility claim
   is made for them.

These are significant API changes. The candidate is a supported-profile proposal,
not a claim of full CPython enum compatibility or a drop-in 1.5 replacement.

## Verification completed

- Unchanged 61-observation corpus: candidate matches native CPython for all 11
  DD requirement groups; current base matches 9. The frameworks are unchanged.
- Native CPython 3.12.14: five shared contract groups pass normally and optimized.
- Actual MicroPython 1.29.0 Windows: five shared groups and six profile groups
  pass normally and optimized.
- Experimental MicroPython 1.28.0-preview Windows: the same groups pass normally
  and optimized; it is separate from the stock 1.29 qualification.
- Existing 13-test enum suite passes normally and optimized on stock 1.29.
- Existing mini suite has an unchanged pre-existing len(Color) failure. Its
  unittest runner exits zero despite that error; exit status alone is insufficient.
- Ruff 0.11.6 formatting and lint checks pass for the implementation/new tests.
- MicroPython commit-message/DCO checker passes with the supplied public email.
- New tests are wired into the existing package-test list and use explicit raises.

No memory measurements, physical-board qualification or new hosted CI results
are claimed for this candidate.

## Review locations

- Checkout: `enum_980/root/build/pr980-patch/`.
- Candidate source: `python-stdlib/enum/enum.py` inside that checkout.
- Candidate docs: `python-stdlib/enum/README.md`.
- Shared checks: `python-stdlib/enum/test_strenum_identity.py`.
- Profile checks: `python-stdlib/enum/test_strenum_profile.py`.
- Patch and local evidence: `enum_980/root/results/strenum-patch/`.

Next action is review with the user. No push or PR until explicitly authorized.
