"""Declared-class StrEnum contracts shared with native CPython.

Run native CPython with -I so the adjacent MicroPython overlay is not imported.
Run MicroPython with this directory on its import path.
"""

import json
from enum import Enum, StrEnum


def check(value, message):
    if not value:
        raise AssertionError(message)


def make_mode():
    class Mode(StrEnum):
        FAST = "fast"
        SLOW = "slow"

    return Mode


def identity():
    mode = make_mode()
    check(isinstance(mode, type), "declaration must remain a class")
    check(isinstance(mode.FAST, mode), "member must belong to its declared class")
    check(type(mode.FAST) is mode, "member type must be the declared class")
    check(type(mode.SLOW) is mode, "members must share the declared type")
    check(isinstance(mode.FAST, str), "member must also be a string")
    check(isinstance(mode.FAST, StrEnum), "member must belong to StrEnum")
    check(isinstance(mode.FAST, Enum), "member must belong to Enum")
    check(not isinstance("fast", mode), "raw strings are not enum members")
    other = make_mode()
    check(not isinstance(other.FAST, mode), "different enum classes stay distinct")


def immediate():
    mode = make_mode()
    check(mode.FAST.name == "FAST", "name available immediately")
    check(mode.FAST.value == "fast", "value available immediately")


def lookup():
    mode = make_mode()
    check(mode("fast") is mode.FAST, "raw lookup must be canonical")
    check(mode(mode.FAST) is mode.FAST, "member lookup must preserve identity")
    check(mode("slow") is mode.SLOW, "lookup must distinguish members")
    try:
        mode("missing")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown values must raise ValueError")


def string_operations():
    mode = make_mode()
    member = mode.FAST
    check(str(member) == "fast", "string conversion")
    check(member == "fast" and "fast" == member, "string equality")
    check(member.upper() == "FAST" and member + "!" == "fast!", "string operations")
    check(member[0] == "f" and member[1:] == "ast", "native string indexing and slicing")
    check(hash(member) == hash("fast"), "string hash")
    check({member: 1}["fast"] == 1, "enum-key raw lookup")
    check(json.loads(json.dumps(member)) == "fast", "JSON must encode a string value")


def methods_and_unrelated_classes():
    class Label(StrEnum):
        FAST = "fast"

        def describe(self):
            return self.name + ":" + self.value

    check(Label.FAST.describe() == "FAST:fast", "declared member methods")

    class Ordinary:
        VALUE = "ordinary"

    check(Ordinary.VALUE == "ordinary", "ordinary class values")
    check(not hasattr(Ordinary, "__members__"), "ordinary classes must not be finalized")


def class_iteration():
    mode = make_mode()
    values = list(mode)
    check(len(values) == 2, "class iteration member count")
    check(mode.FAST in mode and "fast" in mode, "class membership")
    check(any(value is mode.FAST for value in values), "class iteration first member")
    check(any(value is mode.SLOW for value in values), "class iteration second member")
    check(list(mode.FAST) == ["f", "a", "s", "t"], "string member iteration")


failures = []
for test in (
    identity,
    immediate,
    lookup,
    string_operations,
    methods_and_unrelated_classes,
    class_iteration,
):
    try:
        test()
    except Exception as error:
        failures.append([test.__name__, type(error).__name__, str(error)])
print(json.dumps({"checks": 6, "failures": failures}))
if failures:
    raise AssertionError("StrEnum contract failures: " + str(failures))
