"""Shared synthetic observations; imports no DD application modules."""

import sys
import json
import builtins

CASES = []
ENUM = None
MODE = None
BUILDER_BEFORE = None


def make_mode():
    class Mode(ENUM.StrEnum):
        FAST = "fast"
        SLOW = "slow"
    return Mode


def add(cid, section, requirement, operation, prepared=False, factory=make_mode):
    CASES.append((cid, section, requirement, operation, prepared, factory))


def existing_member(M):
    member = M.FAST
    return M(member) is member


def normalize_sequence(M):
    member = M.FAST
    result = tuple(M(value) for value in (member, "slow"))
    return result[0] is member and result[1] is M.SLOW


def storage_roundtrip(M):
    stored = json.dumps({"mode": M.FAST.value})
    restored = M(json.loads(stored)["mode"])
    return {"identity": restored is M.FAST, "enum_instance": isinstance(restored, M)}


def unrelated(M):
    class Ordinary:
        VALUE = "ordinary"
    return Ordinary.VALUE == "ordinary" and not hasattr(Ordinary, "__members__")


REQUIRED = [
    ("immediate_name", "R01", lambda M: M.FAST.name),
    ("immediate_value", "R01", lambda M: M.FAST.value),
    ("stable_name_value", "R02", lambda M: [M.FAST.name, M.FAST.value, M.FAST.name, M.FAST.value]),
    ("lookup_identity", "R03", lambda M: M("fast") is M.FAST),
    ("repeated_lookup", "R03", lambda M: M("fast") is M("fast")),
    ("existing_member", "R04", existing_member),
    ("invalid_value", "R05", lambda M: M("missing")),
    ("isinstance_enum", "R06", lambda M: isinstance(M.FAST, M)),
    ("isinstance_str", "R06", lambda M: isinstance(M.FAST, str)),
    ("raw_is_not_enum", "R06", lambda M: not isinstance("fast", M)),
    ("equals_raw", "R07", lambda M: M.FAST == "fast"),
    ("raw_equals_member", "R07", lambda M: "fast" == M.FAST),
    ("string_value", "R07", lambda M: str(M.FAST)),
    ("enum_key_raw_lookup", "R08", lambda M: {M.FAST: 1}["fast"]),
    ("hash_matches_raw", "R08", lambda M: hash(M.FAST) == hash("fast")),
    ("mixed_sequence", "R09", normalize_sequence),
    ("storage_roundtrip", "R10", storage_roundtrip),
    ("unrelated_class", "R11", unrelated),
]
for cid, requirement, operation in REQUIRED:
    add(cid, "required", requirement, operation)

# PR-only preparation is an explicit adaptation, never applied to required cases.
for cid, requirement, operation in REQUIRED:
    add("prepared_" + cid, "adaptation", None, operation, prepared=True)


def reassign(M):
    M.FAST = "other"
    return "allowed"


def delete(M):
    del M.FAST
    return "allowed"


def change_value(M):
    M.FAST.value = "other"
    return "allowed"


def mapping(M):
    return {"keys": [str(k) for k in M.__members__],
            "values_are_members": all(isinstance(v, M) for v in M.__members__.values())}


def declaration_order(_):
    class Ordered(ENUM.StrEnum):
        LAST = "last"
        FIRST = "first"
        MIDDLE = "middle"
    if MODE == "pr":
        Ordered()
    return [member.name for member in Ordered() ] if MODE == "pr" else [member.name for member in Ordered]


def duplicate(_):
    class Duplicate(ENUM.StrEnum):
        A = "same"
        B = "same"
    if MODE == "pr":
        Duplicate()
    return {"same_object": Duplicate.B is Duplicate.A, "second_name": Duplicate.B.name}


def malformed(_):
    class Malformed(ENUM.StrEnum):
        VALUE = 1
    if MODE == "pr":
        Malformed()
    return "accepted"


def empty(_):
    class Empty(ENUM.StrEnum):
        pass
    if MODE == "pr":
        Empty()
    return "accepted"


def lower_case(_):
    class Lower(ENUM.StrEnum):
        fast = "fast"
    if MODE == "pr":
        Lower()
    return Lower.fast.name


def plain_equality(_):
    class Plain(ENUM.Enum):
        A = 1
    if MODE == "pr":
        Plain()
    return Plain.A == 1


def integer_type(_):
    class Number(ENUM.IntEnum):
        ONE = 1
    if MODE == "pr":
        Number()
    return {"integer": isinstance(Number.ONE, int), "enum": isinstance(Number.ONE, Number)}


for cid, operation in [
    ("members_mapping", mapping),
    ("class_name_lookup", lambda M: M["FAST"].name),
    ("call_name_lookup", lambda M: M("FAST").name),
    ("class_iteration", lambda M: [member.name for member in M]),
    ("class_length", lambda M: len(M)),
    ("declared_order_adapted", declaration_order),
    ("reassign_member", reassign),
    ("delete_member", delete),
    ("mutate_member_value", change_value),
    ("raw_key_enum_lookup", lambda M: {"fast": 1}[M.FAST]),
    ("member_repr", lambda M: repr(M.FAST)),
    ("member_types_shared", lambda M: type(M.FAST) is type(M.SLOW)),
    ("class_builder_changed", lambda M: __build_class__ is not BUILDER_BEFORE),
    ("class_builder_module_attribute_changed", lambda M: builtins.__build_class__ is not BUILDER_BEFORE),
]:
    add(cid, "diagnostic", None, operation, prepared=True)

for cid, operation in [("aliases", duplicate), ("non_string", malformed),
                       ("empty_enum", empty), ("lowercase_name", lower_case)]:
    add(cid, "policy", None, operation, factory=lambda: None)

for cid, operation in [("plain_enum_raw_equality", plain_equality), ("intenum_type", integer_type)]:
    add(cid, "optional_api", None, operation, factory=lambda: None)


def make_str_subclass():
    class PlainString(str):
        pass
    return PlainString


for cid, operation in [
    ("control_equals_raw", lambda S: S("fast") == "fast"),
    ("control_raw_equals", lambda S: "fast" == S("fast")),
    ("control_hash", lambda S: hash(S("fast")) == hash("fast")),
    ("control_subclass_key", lambda S: {S("fast"): 1}["fast"]),
    ("control_raw_key", lambda S: {"fast": 1}[S("fast")]),
]:
    add(cid, "runtime_control", None, operation, factory=make_str_subclass)


def execute(mode, directory=None):
    global ENUM, MODE, BUILDER_BEFORE
    MODE = mode
    BUILDER_BEFORE = __build_class__
    if directory:
        sys.path.insert(0, directory)
        if "enum" in sys.modules:
            raise RuntimeError("enum was loaded before selecting the candidate")
    import enum
    ENUM = enum
    result = {"protocol": 1,
              "meta": {"implementation": sys.implementation.name,
                       "version": list(sys.implementation.version[:3]),
                       "platform": sys.platform,
                       "machine": getattr(sys.implementation, "_machine", "unknown"),
                       "interpreter_version": sys.version,
                       "enum_file": getattr(enum, "__file__", "unknown")},
              "rows": {}}
    for cid, section, requirement, operation, prepared, factory in CASES:
        # Factory/preparation failures are harness errors, not matching outcomes.
        subject = factory()
        if prepared and mode == "pr" and subject is not None:
            subject()
        try:
            value = operation(subject)
            outcome = {"kind": "value", "value": value}
        except (TypeError, ValueError, KeyError, AttributeError) as error:
            outcome = {"kind": "exception", "type": type(error).__name__}
        result["rows"][cid] = outcome
    return result


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in ("cpython", "dd", "pr"):
        raise RuntimeError("Expected mode cpython/dd/pr and optional enum directory")
    print(json.dumps(execute(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)))
