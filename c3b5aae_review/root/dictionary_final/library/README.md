# Enum with a typed StrEnum profile

This candidate requires patched MicroPython core support for custom metaclasses.
Use the reviewed core series before importing this module; the typed profile is
not supported by unmodified MicroPython 1.29.0 or 1.30.0-preview.

Required build flags:

- `MICROPY_PY_METACLASS_INIT=1`
- `MICROPY_PY_METACLASS_OPS=1`
- `MICROPY_PY_METACLASS_PROPERTIES=1`
- `MICROPY_PY_METACLASS_PREPARE=1`

The core prerequisite, metaclass corrections, JSON string-subclass fixes and
mapping-input fix are separate core changes. The library contribution depends
on them; package CI must use that patched interpreter. The package version in
manifest.py remains the upstream version until a release is agreed.

## Typed StrEnum

```python
from enum import StrEnum
import json

class Mode(StrEnum):
    FAST = "fast"
    SLOW = "slow"

assert isinstance(Mode, type)
assert type(Mode.FAST) is Mode
assert isinstance(Mode.FAST, str)
assert Mode("fast") is Mode.FAST
assert Mode["FAST"] is Mode.FAST
assert len(Mode) == 2
assert repr(Mode.FAST) == "<Mode.FAST: 'fast'>"
assert json.loads(json.dumps({Mode.FAST: Mode.SLOW})) == {"fast": "slow"}
```

Members are immediately available. Class iteration yields typed members; members
retain normal string indexing, slicing, hashing and conversion. Declared member
methods work. Member replacement/deletion and changes to name/value are rejected;
ordinary helper attributes remain permitted. `__members__` is a read-only snapshot
mapping names to members, implementing the documented mapping operations rather
than CPython's mappingproxy type. Private implementation state is not a security
boundary.

Functional creation supports dictionaries, name strings, lists and name/value
pairs. `dump()` produces a reconstructable factory expression. The existing
no-argument initialization call, lookup by name through the call operator and
callable members are retained extensions.

Supported subset: direct single inheritance from StrEnum, no custom constructors,
no duplicate values/aliases, and no extension of an already defined enum. Member
declaration order is not guaranteed. This is not the complete CPython enum module;
features such as auto and Flag are outside this profile.

## Enum, IntEnum and the mini implementation

These retain the original initialized-container design. Their members inherit
raw value types rather than the declared container class. Do not assume the typed
StrEnum identity guarantees apply to these profiles.

Both modules install cooperative, process-wide class-builder hooks. Other hooks
must delegate and preserve class results. Fresh imports and both module orders
are tested; in-place execution into an existing module's globals is not qualified.
The registry retains old imported families, and its memory cost is not benchmarked.

## Tests and attribution

Run the included tests with the required patched interpreter. The general core
contract test skips when JSON/metaclass operators are unavailable; qualification
requires the full check count and never treats that skip as a pass.

This builds on IhorNehrutsa's implementation in micropython-lib PR #980. Typed
member construction is adapted from MrCodeGameAndAnime's Dungeon Drifters StrEnum,
linked in the source. Andrew Leech's custom-metaclass prerequisite is separately
attributed in its original commit. Existing source notices remain intact.
