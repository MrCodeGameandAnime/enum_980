# Revision 2 compatibility review

## Status

The candidate remains local and uncommitted above initial candidate
`abb4e3bc4818f271f90eabb49cb36eea897747e1`, based on upstream
`c3b5aaeb61c33ee13c70a6d3dfcd95a8b185e297`.
No push or pull request is authorized. The original investigation and pinned
`c3b5aae/` baseline remain reference material.

## Compatibility changes

| Behavior | Initial candidate | Revision 2 |
| --- | --- | --- |
| Declared class and typed string members | Supported | Preserved |
| Direct `StrEnum(name, names)` factory | Replaced with `.create()` | Original direct factory restored; draft `.create()` removed |
| Iterating the declared class | Unavailable | Restored through sequence fallback |
| Class membership | Unavailable | Restored through iteration |
| String member indexing and slicing | Native behavior | Preserved alongside class iteration |
| Cooperative class-builder hooks and fresh imports | Unqualified | Tested before/after hooks, fresh imports and existing aliases |
| Full/mini module import order | Unqualified | Both orders tested |
| Mini container length | Missing upstream method | Method added and existing suite passes |
| Constructor mixins/custom constructors | Unqualified | Explicitly rejected for typed StrEnum |
| `len(Mode)` / `Mode['FAST']` | Unavailable | Still unavailable |
| Class-level mutation protection | Unavailable | Still unavailable |

The typed profile keeps native string representation so stock MicroPython JSON
serialization remains correct. Enum-style repr is a deliberate remaining difference.
Member declaration order is not promised. Existing Enum and IntEnum container
profiles remain separate from the typed StrEnum profile.

## Findings behind the fixes

Native string construction does not require replacing the functional factory API.
On MicroPython, `object.__new__(cls)` followed by the native string initializer
through `super(StrEnum, member).__init__(value)` creates an actual instance of the
declared string subclass. CPython uses `str.__new__` instead. The initial factory
workaround was therefore unnecessary.

Stock MicroPython reads and writes builtin module attributes through different
paths: a write can enter the builtin override dictionary while a module attribute
read still sees the original globals. Bare builtin lookup observes the effective
override. The dispatcher now retrieves its shared state through that effective
lookup, retains registered enum families, and composes with delegating hooks.
The wrapper closes over family lists rather than its containing state dictionary.
Fresh imports retain old aliases without stacking another main dispatcher.

Callable string members must be considered values rather than discarded as
methods. Values from another string enum are normalized to plain strings before
duplicate detection. Both duplicate orders and escaped/Unicode values are tested.

The mini module also lacked its length method independently of hook composition.
That method is now present, and the full and mini implementations cooperate in
either import order.

## Runtime constraints

The bounded capability probes and the stock interpreter sources explain the
remaining class-level differences. The stock `mp_type_type` does not provide
ordinary Python classes with the custom metaclass operations needed for class
length or subscription. Class namespace writes bypass class-body instance mutation
hooks. The runtime sequence fallback does allow iteration through `__getitem__`,
which is why iteration could be restored without changing the interpreter.

Relevant source locations, referenced read-only, are `py/objtype.c` (native instance
creation, super initialization and type operations), `py/runtime.c` (sequence
iteration fallback), and `py/objmodule.c` (builtin overrides) in the stock source
checkout. These are constraints of the tested approach on stock MicroPython,
not a claim that every possible implementation is impossible.

Non-delegating hooks, hooks replacing ordinary class results, in-place execution
of a module into its existing globals, and constructor mixins are outside the
qualified profile. Fresh imports intentionally retain registered old families;
the resulting memory cost has not been benchmarked. No heap-constrained board
qualification or performance claim is made here.

## Verification

Final verification ran 32 commands successfully, in normal and optimized modes:

- Native CPython 3.12.14 shared contract: 6 groups.
- Stock MicroPython 1.29.0 Windows Win32: shared contract 6, profile 9, hook 6,
  mini-first checks, and the existing 13 enum plus 7 mini tests.
- Experimental MicroPython 1.28.0-preview Windows with metaclass work: the same
  checks. This is additional evidence, not a stock 1.29 qualification.
- The unchanged 61-observation corpus passes all 11 DD requirement groups on
  the stock candidate. This does not mean every diagnostic observation matches
  CPython.

The host runner checks test output as well as process status because the bundled
unittest runner can exit successfully after failed assertions. Regression checks
also remain active under optimization.

From the `enum_980` project directory:

```powershell
& 'C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B c3b5aae_review/root/src/verify_candidate.py --micropython 'C:/Users/User/Documents/Dev/Python/micropython/enum_980/root/build/stock/ports/windows/build-standard/ReleaseWin32/micropython.exe' --experimental 'C:/Users/User/Documents/Dev/Python/micropython/enum_980/root/results/clean-checkout/root/build/pr1061/core/ports/windows/build-standard/ReleaseWin32/micropython.exe'
```

`../root/results/revision-2/verification.json` records commands, exact runtime and
input hashes, working-diff hash, capabilities and corpus results. Adjacent files
contain stdout/stderr. Runtime probes are in
`../root/tests/runtime_capabilities.py`. The unchanged initial patch and candidate
metadata describe the initial snapshot; they do not represent this working diff.

Ruff 0.11.6 passes on both implementations and all four regression scripts.
Hosted CI, Unix-port qualification and physical devices have not been run for
this revision. The remaining API tradeoffs need review before proposing upstream.

## Follow-up boundary investigation

See [the remaining-boundaries report](remaining-boundaries.md) before publication.
It confirms the unresolved class operations and adds a JSON dictionary-key defect;
the prior JSON qualification covered scalar/list values. No implementation changes
were made in this follow-up.
