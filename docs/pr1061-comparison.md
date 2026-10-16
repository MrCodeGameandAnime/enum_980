# PR #1061 on its proposed MicroPython core

This is a separate experimental-runtime measurement. The [stock-runtime report](comparison.md) is unchanged.

## Exact build

- Enum PR #1061 revision: `e48685c6ee07f421b14ab2ace99c728e56fc0b87`.
- Companion core PR #18416 revision: `6a56288ad12aca9d99d1e425e1400a53c65aa709`.
- Interpreter: MicroPython 1.28.0-preview, native Windows Win32 port, Release build, MSVC 19.51.
- All four proposed metaclass options enabled explicitly. Runtime probes confirmed prepare, init, operators and metaclass properties.
- No frozen modules; the pinned enum package is imported from external Python files without source changes.
- The core's own library submodule points to an older revision. This test explicitly pairs the current pinned #1061 head with the pinned companion core head.
- Archive hashes, runtime hash, all package-module hashes, interpreter build strings and exact execution commands are in [pr1061-results.json](pr1061-results.json).

## DD requirement groups

PASS means all observations in that requirement match the checked native CPython reference.
The scopes overlap; these totals are not independent defect counts or a full enum conformance ranking.

| Requirement | CPython 3.12 | DD / stock 1.29 | #980 / stock 1.29 | #1061 / experimental core |
| --- | --- | --- | --- | --- |
| R01 | PASS | PASS | DIFF | PASS |
| R02 | PASS | PASS | DIFF | PASS |
| R03 | PASS | PASS | PASS | PASS |
| R04 | PASS | PASS | DIFF | DIFF |
| R05 | PASS | PASS | PASS | PASS |
| R06 | PASS | PASS | DIFF | DIFF |
| R07 | PASS | PASS | PASS | PASS |
| R08 | PASS | PASS | PASS | DIFF |
| R09 | PASS | PASS | DIFF | DIFF |
| R10 | PASS | PASS | DIFF | PASS |
| R11 | PASS | PASS | PASS | PASS |

The proposed pair matches **7 of 11** DD requirement groups across the same 61 observations.

## What improved, and what still differs

- Immediate name/value access and declared-enum instance checks work without an application class-builder hook.
- The new members are not recognized as native strings by isinstance, despite the declared str mixin.
- Passing an existing member back to its enum raises ValueError. The mixed-sequence normalization case fails for the same reason.
- Member hashes differ from the raw string hashes. The enum-key/raw-string lookup observation passes, but the complete R08 hashing contract does not.
- The stored raw-string round trip returns a correctly typed canonical member.
- Additional diagnostics still show missing standard mapping/subscription behavior, different iteration order, and other compatibility differences. These are outside the narrow requirement score.

## Same-interpreter controls

DD and #980 were each run through the same 61 observations on this experimental runtime as well.
- dd: 0 changed outcomes compared with its stock-1.29 run.
- pr980: 0 changed outcomes compared with its stock-1.29 run.

The controls help separate candidate behavior from interpreter-version effects for this corpus; they do not establish general equivalence of the interpreters.

## All observations

| Observation | CPython reference | #1061 / experimental core |
| --- | --- | --- |
| `immediate_name` | `"FAST"` | `"FAST"` |
| `immediate_value` | `"fast"` | `"fast"` |
| `stable_name_value` | `["FAST","fast","FAST","fast"]` | `["FAST","fast","FAST","fast"]` |
| `lookup_identity` | `true` | `true` |
| `repeated_lookup` | `true` | `true` |
| `existing_member` | `true` | `raises ValueError` |
| `invalid_value` | `raises ValueError` | `raises ValueError` |
| `isinstance_enum` | `true` | `true` |
| `isinstance_str` | `true` | `false` |
| `raw_is_not_enum` | `true` | `true` |
| `equals_raw` | `true` | `true` |
| `raw_equals_member` | `true` | `true` |
| `string_value` | `"fast"` | `"fast"` |
| `enum_key_raw_lookup` | `1` | `1` |
| `hash_matches_raw` | `true` | `false` |
| `mixed_sequence` | `true` | `raises ValueError` |
| `storage_roundtrip` | `{"identity":true,"enum_instance":true}` | `{"enum_instance":true,"identity":true}` |
| `unrelated_class` | `true` | `true` |
| `prepared_immediate_name` | `"FAST"` | `"FAST"` |
| `prepared_immediate_value` | `"fast"` | `"fast"` |
| `prepared_stable_name_value` | `["FAST","fast","FAST","fast"]` | `["FAST","fast","FAST","fast"]` |
| `prepared_lookup_identity` | `true` | `true` |
| `prepared_repeated_lookup` | `true` | `true` |
| `prepared_existing_member` | `true` | `raises ValueError` |
| `prepared_invalid_value` | `raises ValueError` | `raises ValueError` |
| `prepared_isinstance_enum` | `true` | `true` |
| `prepared_isinstance_str` | `true` | `false` |
| `prepared_raw_is_not_enum` | `true` | `true` |
| `prepared_equals_raw` | `true` | `true` |
| `prepared_raw_equals_member` | `true` | `true` |
| `prepared_string_value` | `"fast"` | `"fast"` |
| `prepared_enum_key_raw_lookup` | `1` | `1` |
| `prepared_hash_matches_raw` | `true` | `false` |
| `prepared_mixed_sequence` | `true` | `raises ValueError` |
| `prepared_storage_roundtrip` | `{"identity":true,"enum_instance":true}` | `{"enum_instance":true,"identity":true}` |
| `prepared_unrelated_class` | `true` | `true` |
| `members_mapping` | `{"keys":["FAST","SLOW"],"values_are_members":true}` | `raises AttributeError` |
| `class_name_lookup` | `"FAST"` | `raises TypeError` |
| `call_name_lookup` | `raises ValueError` | `raises ValueError` |
| `class_iteration` | `["FAST","SLOW"]` | `["SLOW","FAST"]` |
| `class_length` | `2` | `2` |
| `declared_order_adapted` | `["LAST","FIRST","MIDDLE"]` | `["MIDDLE","LAST","FIRST"]` |
| `reassign_member` | `raises AttributeError` | `"allowed"` |
| `delete_member` | `raises AttributeError` | `"allowed"` |
| `mutate_member_value` | `raises AttributeError` | `raises AttributeError` |
| `raw_key_enum_lookup` | `1` | `raises KeyError` |
| `member_repr` | `"<Mode.FAST: 'fast'>"` | `"<function>"` |
| `member_types_shared` | `true` | `true` |
| `class_builder_changed` | `false` | `false` |
| `class_builder_module_attribute_changed` | `false` | `false` |
| `aliases` | `{"same_object":true,"second_name":"A"}` | `{"second_name":"B","same_object":false}` |
| `non_string` | `raises TypeError` | `raises TypeError` |
| `empty_enum` | `"accepted"` | `"accepted"` |
| `lowercase_name` | `"fast"` | `"fast"` |
| `plain_enum_raw_equality` | `false` | `false` |
| `intenum_type` | `{"integer":true,"enum":true}` | `{"enum":true,"integer":false}` |
| `control_equals_raw` | `true` | `true` |
| `control_raw_equals` | `true` | `true` |
| `control_hash` | `true` | `true` |
| `control_subclass_key` | `1` | `1` |
| `control_raw_key` | `1` | `raises KeyError` |

## Reproduce

1. With CPython 3.12, run `python root/src/prepare_pr1061.py`. This fetches the pinned archives, verifies their SHA256 hashes, extracts the source trees and writes their source records.
2. Build with `./root/src/build-pr1061.ps1 -Python <CPython-3.12-executable> -MSBuild <MSBuild-executable>`. This uses Release/Win32 and the v145 C++ toolset with `root/config/pr1061.props`.
3. Run `python root/src/check_pr1061.py`. The committed stock-runtime baseline is included; the metaclass feature probe and execution logs are regenerated automatically. See [setup details](README.md#pr-1061-experimental-runtime).

No candidate Python or C implementation changes were made. This checks the focused DD-derived corpus, not the PR's full claimed upstream suite, firmware size or embedded-board support.
No upstream comments or changes were submitted.
