"""Initialization eligibility uses the requested, not selected, metaclass."""
import json


def check(value, message):
    if not value:
        raise AssertionError(message)


def dynamic_factory():
    events = []

    class Other(type):
        def __init__(cls, name, bases, namespace):
            events.append(("other-init", name))

    existing = type.__new__(Other, "Existing", (), {})

    class Meta(type):
        def __new__(meta, name, bases, namespace):
            events.append(("new", name))
            return existing

    base = type.__new__(Meta, "Base", (), {})
    events[:] = []
    result = type("Requested", (base,), {})
    check(result is existing, "factory result identity")
    check(events == [("new", "Requested"), ("other-init", "Requested")], "requested type eligibility")


def selected_subclass():
    events = []

    class Meta(type):
        def __new__(meta, name, bases, namespace):
            return existing

        def __init__(cls, name, bases, namespace):
            events.append(name)

    class Derived(Meta):
        pass

    existing = type.__new__(Meta, "Existing", (), {})
    base = type.__new__(Derived, "Base", (), {})
    events[:] = []
    result = Meta("Requested", (base,), {})
    check(result is existing and events == ["Requested"], "selected subtype must not narrow eligibility")


failures = []
for test in (dynamic_factory, selected_subclass):
    try:
        test()
    except Exception as error:
        failures.append([test.__name__, type(error).__name__, str(error)])
print(json.dumps({"checks": 2, "failures": failures}))
if failures:
    raise AssertionError("metaclass selection lifecycle failures")
