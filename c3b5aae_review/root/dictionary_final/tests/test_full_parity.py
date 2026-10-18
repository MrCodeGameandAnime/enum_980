"""Require the full typed profile; run natively or with the reviewed enum profile."""

import json
from enum import StrEnum


def check(value, message):
    if not value:
        raise AssertionError(message)


def raises(kind, operation):
    try:
        operation()
    except kind:
        return
    raise AssertionError("expected " + kind.__name__)


def mode():
    class Mode(StrEnum):
        FAST = "fast"
        SLOW = "slow"

    return Mode


def operators():
    cls = mode()
    check(isinstance(cls, type) and type(cls.FAST) is cls, "declared type")
    check(len(cls) == 2, "class length")
    check(cls["FAST"] is cls.FAST, "canonical subscription")
    raises(KeyError, lambda: cls["missing"])
    raises(KeyError, lambda: cls[3])
    raises(TypeError, lambda: cls[[]])
    check(set(cls) == {cls.FAST, cls.SLOW}, "class iteration")
    check(cls("fast") is cls.FAST, "canonical value lookup")


def protection():
    cls = mode()
    raises(AttributeError, lambda: setattr(cls, "FAST", "changed"))
    raises(AttributeError, lambda: delattr(cls, "FAST"))
    raises(AttributeError, lambda: setattr(cls.FAST, "name", "changed"))
    raises(AttributeError, lambda: delattr(cls.FAST, "value"))
    cls.helper = 3
    check(cls.helper == 3, "allow unrelated helper")
    del cls.helper
    mapping = cls.__members__
    check(mapping["FAST"] is cls.FAST, "public member mapping")

    def replace_mapping():
        mapping["FAST"] = cls.SLOW

    raises(TypeError, replace_mapping)
    raises(AttributeError, lambda: mapping.clear())
    raises(AttributeError, lambda: setattr(cls, "__members__", {}))
    raises(AttributeError, lambda: delattr(cls, "__members__"))
    check(dict(mapping) == {"FAST": cls.FAST, "SLOW": cls.SLOW}, "mapping conversion")
    check(mapping.get("missing", 3) == 3, "mapping get default")
    cls.FAST.helper = 3
    check(cls.FAST.helper == 3, "member helper allowed")
    del cls.FAST.helper
    check(cls["FAST"] is cls.FAST and len(cls) == 2, "metadata remains intact")


def representations():
    cls = mode()
    check(repr(cls) == "<enum 'Mode'>", "class repr")
    check(repr(cls.FAST) == "<Mode.FAST: 'fast'>", "member repr")
    check(str(cls.FAST) == "fast", "member str")
    check(repr([cls.FAST]) == "[<Mode.FAST: 'fast'>]", "nested repr")


def serialization():
    for raw in ("fast", 'a"b\\c\n\t', "", "caf\u00e9", "\x01"):
        cls = StrEnum("Mode", {"FAST": raw})
        check(type(cls.FAST) is cls, "factory typed member")
        check(json.loads(json.dumps(cls.FAST)) == raw, "JSON scalar")
        check(json.loads(json.dumps([cls.FAST])) == [raw], "JSON list")
        check(json.loads(json.dumps({cls.FAST: cls.FAST})) == {raw: raw}, "JSON keys and values")


failures = []
for test in (operators, protection, representations, serialization):
    try:
        test()
    except Exception as error:
        failures.append([test.__name__, type(error).__name__, str(error)])
print(json.dumps({"checks": 4, "failures": failures}))
if failures:
    raise AssertionError("enum parity failures")
