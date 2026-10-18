"""MicroPython-specific factory and supported-profile regression checks."""

import json
from enum import StrEnum


def check(value, message):
    if not value:
        raise AssertionError(message)


def raises(error_type, function):
    try:
        function()
    except error_type:
        return
    raise AssertionError("expected " + error_type.__name__)


def factory():
    for names in (
        {"FAST": "fast", "SLOW": "slow"},
        "FAST SLOW",
        ["FAST", "SLOW"],
        [("FAST", "fast"), ("SLOW", "slow")],
    ):
        mode = StrEnum("Mode", names)
        check(isinstance(mode, type), "factory must return a class")
        check(type(mode.FAST) is mode, "factory must create declared-class members")
        check(isinstance(mode.FAST, str), "factory members are strings")
        check(mode(mode.FAST.value) is mode.FAST, "factory value lookup")
        check(mode(mode.FAST) is mode.FAST, "factory member lookup")


def original_factory_syntax():
    mode = StrEnum("Mode", {"FAST": "fast", "SLOW": "slow"})
    check(type(mode.FAST) is mode, "direct factory declared type")
    check(mode("fast") is mode.FAST, "direct factory lookup")
    mode = StrEnum(value="Mode", names="FAST SLOW")
    check(type(mode.FAST) is mode and mode.FAST.value == "fast", "keyword factory")


def dump_roundtrip():
    for name in ("Mode", "Mode'quoted"):
        mode = StrEnum(name, {"FAST": "fast"})
        restored = eval(mode.dump())
        check(type(restored.FAST) is restored, "dump must restore declared-class members")
        check(restored.FAST.value == mode.FAST.value, "dump value")


def bad_definitions():
    def duplicate():
        class Duplicate(StrEnum):
            A = "same"
            B = "same"

    def invalid():
        class Invalid(StrEnum):
            A = 1

    raises(ValueError, duplicate)
    raises(TypeError, invalid)
    raises(TypeError, lambda: StrEnum("Invalid", {"A": 1}))
    raises(ValueError, lambda: StrEnum("Invalid", {"A": "same", "B": "same"}))


def members_are_readonly():
    class Mode(StrEnum):
        FAST = "fast"

    raises(AttributeError, lambda: setattr(Mode.FAST, "name", "WRONG"))
    raises(AttributeError, lambda: setattr(Mode.FAST, "value", "wrong"))
    raises(AttributeError, lambda: delattr(Mode.FAST, "value"))
    check(Mode.FAST() == "fast", "legacy callable-member extension")
    check(Mode() is Mode, "legacy initialization call returns the class")
    check(Mode("FAST") is Mode.FAST, "legacy name lookup")


def no_finalized_subclassing():
    class Base(StrEnum):
        A = "a"

    def extend():
        class Child(Base):
            B = "b"

    raises(TypeError, extend)
    raises(TypeError, lambda: Base("Child", {"B": "b"}))
    raises(TypeError, lambda: type("Child", (Base,), {}))


def constructors_are_rejected():
    def custom_init():
        class Custom(StrEnum):
            A = "a"

            def __init__(self, value):
                pass

    def reserved_members():
        class Custom(StrEnum):
            __members__ = {}
            A = "a"

    raises(TypeError, reserved_members)
    raises(TypeError, custom_init)
    raises(TypeError, lambda: StrEnum(None, {"A": "a"}))


def string_subclass_values():
    source = StrEnum("Source", {"FAST": "fast"})
    for names in ({"A": "fast", "B": source.FAST}, {"A": source.FAST, "B": "fast"}):
        raises(ValueError, lambda: StrEnum("Duplicate", names))
    mode = StrEnum("Mode", {"FAST": source.FAST})
    check(type(mode.FAST.value) is str, "stored value is a plain string")


def special_json_values():
    for text in ('a"b', "line\nbreak", "back\\slash", "snowman \u2603"):
        mode = StrEnum("Mode", {"VALUE": text})
        check(json.loads(json.dumps({"mode": mode.VALUE}))["mode"] == text, "JSON escapes")


failures = []
for test in (
    factory,
    original_factory_syntax,
    dump_roundtrip,
    bad_definitions,
    members_are_readonly,
    no_finalized_subclassing,
    constructors_are_rejected,
    string_subclass_values,
    special_json_values,
):
    try:
        test()
    except Exception as error:
        failures.append([test.__name__, type(error).__name__, str(error)])
print(json.dumps({"checks": 9, "failures": failures}))
if failures:
    raise AssertionError("StrEnum profile failures: " + str(failures))
