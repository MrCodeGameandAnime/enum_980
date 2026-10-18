# Remaining compatibility boundaries

## Decision status

The candidate is not ready to describe as behaviorally complete. This investigation
changes no implementation files. Existing baseline and candidate sources remain
unchanged; all additional probes and evidence are inside `c3b5aae_review`.
No push, commit or pull request was performed.

## Measured comparison

The same probe ran in eight isolated processes: native CPython 3.12.14, the pinned
c3b5aae baseline on stock MicroPython 1.29.0 Windows, the candidate on that stock
runtime, and the candidate on the existing experimental 1.28.0-preview Windows
runtime; each ran normally and with optimization. All normal/optimized observations
agree. These are diagnostic observations of known failures, not eight passing
CPython-parity tests.

| Operation | Native CPython | c3b5aae baseline | Current candidate on stock 1.29 |
| --- | --- | --- | --- |
| Declared name is a type | Yes | No | Yes |
| `len(Mode)` | 2 | 2 | TypeError |
| `Mode['FAST']` | Canonical member | Canonical member | TypeError |
| Missing subscription | KeyError | KeyError | TypeError |
| Replace/delete class member | AttributeError | AttributeError | Allowed |
| Add/delete ordinary class helper | Allowed | Blocked | Allowed |
| Replace/delete member name | AttributeError | AttributeError | AttributeError |
| Add ordinary member helper | Allowed | Blocked | Blocked |
| Clear `__members__` mapping | Blocked | Allowed | Allowed |
| `repr(Mode)` | `<enum 'Mode'>` | `<enum 'Mode'>` | `<class 'Mode'>` |
| `repr(Mode.FAST)` | `<Mode.FAST: 'fast'>` | Same | `'fast'` |
| JSON scalar/list round trip | Correct | Invalid JSON | Correct |
| JSON dictionary-key round trip | Correct | Wrong key text | Invalid JSON |

The stricter handling of ordinary member helper attributes is inherited from the
baseline. Mutable public metadata is also an existing baseline difference, now
explicitly measured. Protecting only normal member assignment is insufficient
while the metadata can be cleared externally.

## Interpreter causes

### Class length and subscription

In the stock source, `mp_obj_len_maybe` dispatches through the object's type's
`unary_op` slot, and `mp_obj_subscr` dispatches through its `subscr` slot
([obj.c](../../root/build/stock/py/obj.c)). The metatype `mp_type_type` has neither
slot ([objtype.c](../../root/build/stock/py/objtype.c)). Adding `__len__`,
`__getitem__` or `__class_getitem__` in the class body cannot supply these missing
metatype operations. Existing isolated capability probes demonstrate this.

Class iteration happens to have a separate sequence fallback and therefore could
be restored in the previous revision; that does not provide subscription or len.

### Mutation and class representation

The stock `type_attr` writes/deletes class dictionary entries directly. A
class-body `__setattr__` or `__delattr__` protects instances, not the class object.
`type_print` similarly controls the class representation. Matching CPython while
retaining real declared classes requires a suitable metaclass/type protocol.
The existing experimental build is not a complete solution: a custom-metaclass
probe supports length/iteration but still fails subscription and does not enforce
its metaclass assignment/deletion hooks.

CPython's intended mutation behavior is selective: member replacement/deletion is
blocked, ordinary helper attributes are permitted. A blanket class freeze would
not be a parity fix. Metadata needs separate read-only public exposure, with
internal lookup state protected from public mapping mutation.

### Member representation and JSON

Stock `instance_print` selects `__repr__` for PRINT_JSON as well as PRINT_REPR.
Therefore a Python string subclass's custom enum repr is emitted directly into
JSON. This is reproduced with a plain `CustomString(str)` without any enum logic.
Retaining native string repr avoids that scalar/list issue.

However, `dict_print` checks `mp_obj_is_str_or_bytes(key)` before deciding whether
to add quotes ([objdict.c](../../root/build/stock/py/objdict.c)). A Python string
subclass is not recognized by that exact native-type check. The candidate's
native string printer already quotes the key, and dict_print wraps it again:

```text
json.dumps({Mode.FAST: 1}) -> {""fast"": 1}
```

The baseline emits `{"<Mode.FAST: 'fast'>": 1}`, which is parseable but has the
wrong key. Native CPython produces `{"fast": 1}`. Plain string keys work on all
runtimes. A proper runtime fix needs to recognize string-subclass storage for
both JSON values and keys, preserve escaping, and ignore custom repr when
encoding strings. Merely adding enum repr would regress working scalar/list JSON.

## Recommended boundary for subsequent implementation

For complete behavior with real declared types, split the work into:

1. Runtime support: sufficient metaclass/type operations for class length,
   subscription, selective member mutation guards and class repr; JSON handling
   for native string subclasses in both value and dictionary-key positions.
2. Library integration: enum metaclass behavior using those supported protocols,
   member repr, protected public metadata, and parity tests that require every
   desired operation to succeed rather than accepting the failures above.

This changes the deployment requirement from stock 1.29.0 to a runtime with the
necessary support. It is an architectural decision before implementation, not a
small enum-only patch. Another viable deliverable is an explicitly reduced stock
profile, but it cannot honestly be called full parity.

Replacing builtins such as len/isinstance/json globally, returning a container
again, or modifying interpreter memory would evade the problem while changing
the compatibility contract. None of those is implemented here. The source
analysis establishes the boundaries of this conventional pure-Python approach;
it does not claim a universal impossibility theorem.

## Reproduction and evidence

From the enum_980 project directory:

```powershell
& 'C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B c3b5aae_review/root/src/verify_remaining_boundaries.py
```

- [Probe](../root/tests/remaining_boundaries.py)
- [Runner](../root/src/verify_remaining_boundaries.py)
- [Observations and input/runtime hashes](../root/results/remaining-boundaries/observations.json)
- [Earlier capability probe](../root/tests/runtime_capabilities.py)
- [Earlier qualification](compatibility-review.md)

The new JSON-key finding narrows the earlier qualification: that suite established
scalar/list JSON and the recorded DD groups, not dictionary-key serialization.
There is no new Unix-port or physical-board qualification.
