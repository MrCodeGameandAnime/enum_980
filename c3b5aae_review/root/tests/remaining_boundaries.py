"""Measure the four unresolved API boundaries without changing the candidate."""
import json
import sys
from enum import StrEnum


def make_mode():
    class Mode(StrEnum):
        FAST = "fast"
        SLOW = "slow"
    return Mode


def record(operation):
    try:
        return {"value": operation()}
    except Exception as error:
        return {"exception": type(error).__name__, "message": str(error)}


def mutation(target, operation):
    mode = make_mode()
    obj = mode if target == "class" else mode.FAST
    name = "FAST" if target == "class" else "name"
    if operation == "replace":
        setattr(obj, name, "changed")
    elif operation == "delete":
        delattr(obj, name)
    elif operation == "add":
        setattr(obj, "helper", 42)
    elif operation == "delete_helper":
        setattr(obj, "helper", 42)
        delattr(obj, "helper")
    return "allowed"


def metadata_mutation():
    mode = make_mode()
    mode.__members__.clear()
    return "allowed"


mode = make_mode()
results = {
    "class_is_type": isinstance(mode, type),
    "length": record(lambda: len(mode)),
    "subscription": record(lambda: mode["FAST"] is mode.FAST),
    "subscription_missing": record(lambda: mode["MISSING"]),
    "member_repr": record(lambda: repr(mode.FAST)),
    "class_repr": record(lambda: repr(mode)),
    "member_str": record(lambda: str(mode.FAST)),
    "json_member": record(lambda: json.dumps(mode.FAST)),
    "json_member_roundtrip": record(lambda: json.loads(json.dumps(mode.FAST)) == "fast"),
    "json_list_roundtrip": record(lambda: json.loads(json.dumps([mode.FAST])) == ["fast"]),
    "json_key_text": record(lambda: json.dumps({mode.FAST: 1})),
    "json_key_roundtrip": record(lambda: json.loads(json.dumps({mode.FAST: 1})) == {"fast": 1}),
    "member_map_mutation": record(metadata_mutation),
    "native_string_key": record(lambda: json.loads(json.dumps({"fast": 1})) == {"fast": 1}),
}
for target in ("class", "member"):
    for action in ("replace", "delete", "add", "delete_helper"):
        results[target + "_" + action] = record(lambda: mutation(target, action))


class CustomString(str):
    def __repr__(self):
        return "<CustomString: 'fast'>"


custom = CustomString("fast")
results["custom_repr_string"] = {
    "repr": record(lambda: repr(custom)),
    "json": record(lambda: json.dumps(custom)),
    "json_roundtrip": record(lambda: json.loads(json.dumps(custom)) == "fast"),
}
print(json.dumps({"implementation": sys.implementation.name,
                  "version": list(sys.implementation.version[:3]),
                  "platform": sys.platform, "results": results}))
