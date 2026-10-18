"""Cooperative hooks and fresh module imports must preserve enum behavior."""

import builtins
import json
import sys

seen = []
original = __build_class__


def observer(function, name, *bases, **kwargs):
    seen.append(name)
    return original(function, name, *bases, **kwargs)


builtins.__build_class__ = observer
import enum  # noqa: E402 - install the observer before importing the candidate


def check(value, message):
    if not value:
        raise AssertionError(message)


def typed(base):
    class Mode(base):
        FAST = "fast"

    check(type(Mode.FAST) is Mode, "declared member type")
    check(Mode("fast") is Mode.FAST, "canonical lookup")
    return Mode


def before_import():
    typed(enum.StrEnum)
    check("Mode" in seen, "pre-existing builder must still run")


def cached_import():
    before = __build_class__
    import enum as again

    check(again is enum, "ordinary imports are cached")
    check(__build_class__ is before, "cached imports do not stack builders")


def fresh_import():
    before = __build_class__
    previous = sys.modules["enum"]
    try:
        del sys.modules["enum"]
        import enum as again

        typed(again.StrEnum)
        typed(previous.StrEnum)
        check(__build_class__ is before, "fresh imports reuse the existing dispatcher")
    finally:
        sys.modules["enum"] = previous


def later_hook():
    before = __build_class__
    calls = []

    def later(function, name, *bases, **kwargs):
        calls.append(name)
        return before(function, name, *bases, **kwargs)

    builtins.__build_class__ = later
    previous = sys.modules["enum"]
    try:
        del sys.modules["enum"]
        import enum as again

        typed(again.StrEnum)
        check("Mode" in calls, "a later cooperative hook must run")
        check(__build_class__ is later, "reload must not overwrite a later hook")
    finally:
        builtins.__build_class__ = before
        sys.modules["enum"] = previous


def mini_after_full():
    import enum_mini

    class Mini(enum_mini.Enum):
        A = 1

    check(Mini.A.name == "A" and len(Mini) == 1, "mini container must initialize")
    typed(enum.StrEnum)
    previous = sys.modules["enum"]
    try:
        del sys.modules["enum"]
        import enum as again

        class AnotherMini(enum_mini.Enum):
            B = 2

        check(
            AnotherMini.B.value == 2 and len(AnotherMini) == 1, "mini alias survives full reload"
        )
        typed(again.StrEnum)
    finally:
        sys.modules["enum"] = previous


def mixin_rejection():
    class Constructor:
        def __new__(cls, value):
            return "wrong type"

    try:

        class Invalid(Constructor, enum.StrEnum):
            FAST = "fast"
    except TypeError:
        return
    raise AssertionError("unsupported constructor mixins must fail explicitly")


failures = []
for test in (
    before_import,
    cached_import,
    fresh_import,
    later_hook,
    mini_after_full,
    mixin_rejection,
):
    try:
        test()
    except Exception as error:
        failures.append([test.__name__, type(error).__name__, str(error)])
print(json.dumps({"checks": 6, "failures": failures}))
if failures:
    raise AssertionError("Hook contract failures: " + str(failures))
