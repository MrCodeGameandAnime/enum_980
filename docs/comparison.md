# Three-way enum comparison

Same synthetic cases derived from [DD requirements](requirements.md), run on three implementations.

## Sources

| Mode | Interpreter | Platform | Source SHA256 |
| --- | --- | --- | --- |
| cpython | cpython 3.12.14 | win32 | `f35e542d8c4c1d2b5e910138d726fa48774925f3c4dc5462793ebcb66aa55501` |
| dd | micropython 1.29.0 | win32 | `609ed29724b8ed91d4fe8f41961814c8f3f4c8032650fcac6ffc4b29cd95a5f2` |
| pr | micropython 1.29.0 | win32 | `28ccf75b957ceb74b9cfe23a0114d3feb86ef4759eaa36f5698a56e225d4564c` |

DD source snapshot revision: `2fa5f9d0ca806e5e7dbd41f3ac9073465d26762b`.
PR #980 pinned revision: `f1a9f168ad4bb19a487e54a28c81f77863179560`.

Runtime machine/build strings, module paths, exact commands, and every raw outcome are in
[three-way-results.json](three-way-results.json). Revisions identify source history; file hashes identify the executed bytes.

Every observation creates a fresh class. Each implementation runs in a separate process.
Required cases have no preparatory enum calls. Adapted cases explicitly call the PR's enum with no arguments first; CPython and DD need no such preparation.
Initialization and factory failures abort measurement. Recorded exceptions below come from the observed operation.

## DD requirements

PASS means every observation for that requirement matches the checked native CPython reference.

| Requirement | CPython | DD on MicroPython | PR on MicroPython |
| --- | --- | --- | --- |
| R01 | PASS | PASS | DIFF |
| R02 | PASS | PASS | DIFF |
| R03 | PASS | PASS | PASS |
| R04 | PASS | PASS | DIFF |
| R05 | PASS | PASS | PASS |
| R06 | PASS | PASS | DIFF |
| R07 | PASS | PASS | PASS |
| R08 | PASS | PASS | PASS |
| R09 | PASS | PASS | DIFF |
| R10 | PASS | PASS | DIFF |
| R11 | PASS | PASS | PASS |

## Required observations

| Observation | CPython | DD / MicroPython | PR / MicroPython |
| --- | --- | --- | --- |
| `immediate_name` | `"FAST"` | `"FAST"` | `raises AttributeError` |
| `immediate_value` | `"fast"` | `"fast"` | `raises AttributeError` |
| `stable_name_value` | `["FAST","fast","FAST","fast"]` | `["FAST","fast","FAST","fast"]` | `raises AttributeError` |
| `lookup_identity` | `true` | `true` | `true` |
| `repeated_lookup` | `true` | `true` | `true` |
| `existing_member` | `true` | `true` | `false` |
| `invalid_value` | `raises ValueError` | `raises ValueError` | `raises ValueError` |
| `isinstance_enum` | `true` | `true` | `false` |
| `isinstance_str` | `true` | `true` | `true` |
| `raw_is_not_enum` | `true` | `true` | `true` |
| `equals_raw` | `true` | `true` | `true` |
| `raw_equals_member` | `true` | `true` | `true` |
| `string_value` | `"fast"` | `"fast"` | `"fast"` |
| `enum_key_raw_lookup` | `1` | `1` | `1` |
| `hash_matches_raw` | `true` | `true` | `true` |
| `mixed_sequence` | `true` | `true` | `false` |
| `storage_roundtrip` | `{"identity":true,"enum_instance":true}` | `{"enum_instance":true,"identity":true}` | `raises AttributeError` |
| `unrelated_class` | `true` | `true` | `true` |

## Explicit PR initialization adaptation

| Observation | CPython | DD / MicroPython | PR / MicroPython |
| --- | --- | --- | --- |
| `prepared_immediate_name` | `"FAST"` | `"FAST"` | `"FAST"` |
| `prepared_immediate_value` | `"fast"` | `"fast"` | `"fast"` |
| `prepared_stable_name_value` | `["FAST","fast","FAST","fast"]` | `["FAST","fast","FAST","fast"]` | `["FAST","fast","FAST","fast"]` |
| `prepared_lookup_identity` | `true` | `true` | `true` |
| `prepared_repeated_lookup` | `true` | `true` | `true` |
| `prepared_existing_member` | `true` | `true` | `true` |
| `prepared_invalid_value` | `raises ValueError` | `raises ValueError` | `raises ValueError` |
| `prepared_isinstance_enum` | `true` | `true` | `false` |
| `prepared_isinstance_str` | `true` | `true` | `true` |
| `prepared_raw_is_not_enum` | `true` | `true` | `true` |
| `prepared_equals_raw` | `true` | `true` | `true` |
| `prepared_raw_equals_member` | `true` | `true` | `true` |
| `prepared_string_value` | `"fast"` | `"fast"` | `"fast"` |
| `prepared_enum_key_raw_lookup` | `1` | `1` | `1` |
| `prepared_hash_matches_raw` | `true` | `true` | `true` |
| `prepared_mixed_sequence` | `true` | `true` | `true` |
| `prepared_storage_roundtrip` | `{"identity":true,"enum_instance":true}` | `{"enum_instance":true,"identity":true}` | `{"enum_instance":false,"identity":true}` |
| `prepared_unrelated_class` | `true` | `true` | `true` |

## Application policies and alias behavior

| Observation | CPython | DD / MicroPython | PR / MicroPython |
| --- | --- | --- | --- |
| `aliases` | `{"same_object":true,"second_name":"A"}` | `raises ValueError` | `{"second_name":"B","same_object":false}` |
| `non_string` | `raises TypeError` | `raises TypeError` | `raises TypeError` |
| `empty_enum` | `"accepted"` | `raises TypeError` | `"accepted"` |
| `lowercase_name` | `"fast"` | `raises TypeError` | `"fast"` |

## Additional compatibility observations

| Observation | CPython | DD / MicroPython | PR / MicroPython |
| --- | --- | --- | --- |
| `members_mapping` | `{"keys":["FAST","SLOW"],"values_are_members":true}` | `{"values_are_members":true,"keys":["slow","fast"]}` | `{"values_are_members":false,"keys":["slow","fast"]}` |
| `class_name_lookup` | `"FAST"` | `raises TypeError` | `raises TypeError` |
| `call_name_lookup` | `raises ValueError` | `raises ValueError` | `"FAST"` |
| `class_iteration` | `["FAST","SLOW"]` | `raises TypeError` | `raises KeyError` |
| `class_length` | `2` | `raises TypeError` | `raises TypeError` |
| `declared_order_adapted` | `["LAST","FIRST","MIDDLE"]` | `raises TypeError` | `["MIDDLE","LAST","FIRST"]` |
| `reassign_member` | `raises AttributeError` | `"allowed"` | `"allowed"` |
| `delete_member` | `raises AttributeError` | `"allowed"` | `"allowed"` |
| `mutate_member_value` | `raises AttributeError` | `"allowed"` | `raises AttributeError` |
| `raw_key_enum_lookup` | `1` | `raises KeyError` | `raises KeyError` |
| `member_repr` | `"<Mode.FAST: 'fast'>"` | `"'fast'"` | `"<Mode.FAST: 'fast'>"` |
| `member_types_shared` | `true` | `true` | `false` |
| `class_builder_changed` | `false` | `true` | `false` |
| `class_builder_module_attribute_changed` | `false` | `false` | `false` |

## APIs outside DD's StrEnum subset

| Observation | CPython | DD / MicroPython | PR / MicroPython |
| --- | --- | --- | --- |
| `plain_enum_raw_equality` | `false` | `raises AttributeError` | `true` |
| `intenum_type` | `{"integer":true,"enum":true}` | `raises AttributeError` | `{"enum":false,"integer":true}` |

## Plain str subclass controls

| Observation | CPython | DD / MicroPython | PR / MicroPython |
| --- | --- | --- | --- |
| `control_equals_raw` | `true` | `true` | `true` |
| `control_raw_equals` | `true` | `true` | `true` |
| `control_hash` | `true` | `true` | `true` |
| `control_subclass_key` | `1` | `1` | `1` |
| `control_raw_key` | `1` | `raises KeyError` | `raises KeyError` |

## Interpretation boundaries

- The requirement summary concerns DD's existing narrow use case; it is not a full enum conformance score.
- Application policy differences (including DD rejecting aliases) are separate from required behavior.
- Plain-string-subclass controls identify possible interpreter effects. Compare both dictionary lookup directions before attributing a difference to enum code.
- DD's class-builder interception is recorded separately. Passing R11 only checks the ordinary class scenario; it does not establish general hook safety.
- On this MicroPython build, effective builtin lookup observes the changed class builder while explicit builtins-module attribute access still exposes the original. Both observations are retained to avoid reporting the hook as absent.
- This run measures semantics, not memory, firmware size, or execution overhead.
- Missing APIs and deliberately different syntax remain visible; matching exceptions alone do not establish useful feature support.
- Claude's supplied report used a Unix port. The platform above identifies this local run; port-dependent outcomes must not be silently combined.

## Reproduce

From the enum project directory, using CPython 3.12:

```sh
python root/src/prepare_sources.py --dd-root <DD-repository>
python root/src/compare.py --micropython <MicroPython-1.29.0-executable>
python -B -m unittest discover -s root/tests -v
```

The source preparation command copies only the original DD enum module and downloads the PR enum module at its pinned commit.
It does not import DD gameplay code. All runtime cases are synthetic. No upstream comments or changes are submitted.
