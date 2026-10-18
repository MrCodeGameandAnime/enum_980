"""Reproduce the profile report with explicit expressions and runtime identity."""
import sys
import json


def outcome(operation):
    try:
        return {"value": operation()}
    except Exception as error:
        return {"exception": type(error).__name__, "message": str(error)}


class Text(str):
    pass


def key_checks(member, raw):
    literal = {"fast": 1}
    dynamic = {"".join(["fa", "st"]): 1}
    subclass = {member: 1}
    mixed = {"fast": 1, 0: 0}
    formerly_mixed = {"fast": 1, 0: 0}
    del formerly_mixed[0]
    assigned = {"fast": 1}
    assigned[member] = 2
    return {
        "eq_raw": member == raw,
        "raw_eq_member": raw == member,
        "hash_matches": hash(member) == hash(raw),
        "literal_raw_key_lookup": outcome(lambda: literal[member]),
        "dynamic_raw_key_lookup": outcome(lambda: dynamic[member]),
        "mixed_raw_key_lookup": outcome(lambda: mixed[member]),
        "formerly_mixed_raw_key_lookup": outcome(lambda: formerly_mixed[member]),
        "member_key_raw_lookup": outcome(lambda: subclass[raw]),
        "member_in_literal_dict": member in literal,
        "member_in_dynamic_dict": member in dynamic,
        "literal_get_with_member": outcome(lambda: literal.get(member)),
        "assign_equal_key_length": len(assigned),
        "assign_equal_key_items": sorted((str(k), v) for k, v in assigned.items()),
        "raw_set_contains_member": member in {"fast"},
        "member_set_contains_raw": raw in {member},
    }


result = {
    "runtime": {
        "implementation": sys.implementation.name,
        "version": list(sys.implementation.version[:3]),
        "build": sys.version,
        "platform": sys.platform,
    },
    "plain_str_subclass": key_checks(Text("fast"), "fast"),
}
if sys.argv[1] != "control":
    if sys.argv[1] == "profile":
        sys.modules.pop("enum", None)
        sys.path.insert(0, sys.argv[2])
    from enum import StrEnum

    class Mode(StrEnum):
        FAST = "fast"
        SLOW = "slow"

    result["strenum"] = key_checks(Mode.FAST, "fast")
    result["iteration"] = {
        "list_Mode_FAST": outcome(lambda: [str(item) for item in Mode.FAST]),
        "list_Mode": outcome(lambda: [item.name for item in Mode]),
        "list_Mode_noargs": outcome(lambda: [item.name for item in Mode()]),
        "members_keys": list(Mode.__members__),
    }
print(json.dumps(result))
