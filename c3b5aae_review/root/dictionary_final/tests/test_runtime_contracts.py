"""General interpreter contracts, shared with CPython; no enum dependency."""

try:
    import json

    class _FeatureMeta(type):
        def __len__(cls):
            return 0

    class _FeatureProbe(metaclass=_FeatureMeta):
        pass

    if len(_FeatureProbe) != 0:
        raise TypeError("metaclass operators unavailable")
except (ImportError, TypeError, AttributeError):
    print("SKIP")
    raise SystemExit(0)


def check(value, message):
    if not value:
        raise AssertionError(message)


def rejected(error, operation):
    try:
        operation()
    except error:
        return
    raise AssertionError("expected " + error.__name__)


class Meta(type):
    def __len__(cls):
        return 2

    def __getitem__(cls, key):
        return {"A": 1, "B": 2}[key]

    def __repr__(cls):
        return "<checked class>"

    def __setattr__(cls, key, value):
        if key == "A":
            raise AttributeError("protected")
        type.__setattr__(cls, key, value)

    def __delattr__(cls, key):
        if key == "A":
            raise AttributeError("protected")
        type.__delattr__(cls, key)


class DerivedMeta(Meta):
    pass


class Checked(metaclass=DerivedMeta):
    A = 1


def operators():
    check(len(Checked) == 2, "metaclass length")
    check(Checked["A"] == 1, "inherited metaclass subscription")
    rejected(KeyError, lambda: Checked["missing"])
    check(repr(Checked) == "<checked class>", "inherited metaclass repr")


def mutation():
    rejected(AttributeError, lambda: setattr(Checked, "A", 9))
    rejected(AttributeError, lambda: delattr(Checked, "A"))
    Checked.helper = 3
    check(Checked.helper == 3, "raw type setter")
    del Checked.helper
    rejected(AttributeError, lambda: getattr(Checked, "helper"))


def ordinary():
    class Plain:
        def __len__(self):
            return 7

        def __getitem__(self, key):
            return key

        def __repr__(self):
            return "instance"

    check(len(Plain()) == 7 and Plain()["x"] == "x", "instance protocols")
    rejected(TypeError, lambda: len(Plain))
    rejected(TypeError, lambda: Plain["x"])
    check(repr(Plain) != "instance", "class repr unchanged")
    Plain.value = 8
    del Plain.value


def strings():
    class Text(str):
        def __repr__(self):
            return "<not JSON>"

        def __str__(self):
            return "not the storage"

    for raw in ("fast", 'a"b\\c\n\t', "", "caf\u00e9", "\x01"):
        value = Text(raw)
        check(json.loads(json.dumps(value)) == raw, "subclass JSON value")
        check(json.loads(json.dumps([value])) == [raw], "nested JSON value")
        check(json.loads(json.dumps({value: value})) == {raw: raw}, "subclass JSON key")
        check(repr(value) == "<not JSON>", "repr still honored outside JSON")


def class_identity():
    class Text(str, metaclass=Meta):
        pass

    check(issubclass(Text, str), "metaclass native subclass")
    value = Text("fast")
    check(type(value) is Text and isinstance(value, Text), "custom metaclass instance identity")
    check(isinstance(value, str), "native base identity")
    check(super(Text, value).upper() == "FAST", "super with custom metaclass")


def dynamic_metaclass():
    child = type("Child", (Checked,), {})
    check(type(child) is DerivedMeta, "type factory preserves metaclass")
    check(child["B"] == 2, "dynamic class inherited operators")


def keyword_call():
    class Calling(type):
        def __call__(cls, *args, **kwargs):
            return [list(args), kwargs]

    class Callable(metaclass=Calling):
        pass

    check(Callable(value=3) == [[], {"value": 3}], "keyword call forwarding")
    check(
        Callable(1, 2, 3, 4, 5, 6, 7, 8, 9, a=1, b=2)
        == [[1, 2, 3, 4, 5, 6, 7, 8, 9], {"a": 1, "b": 2}],
        "heap call forwarding",
    )


def mapping_input():
    class Mapping:
        def keys(self):
            return ["A", "B"]

        def __getitem__(self, key):
            return {"A": 1, "B": 2}[key]

        def __iter__(self):
            raise AssertionError("keys protocol must take precedence")

    check(dict(Mapping()) == {"A": 1, "B": 2}, "mapping conversion")
    target = {"C": 3}
    target.update(Mapping(), D=4)
    check(target == {"A": 1, "B": 2, "C": 3, "D": 4}, "mapping update")
    check(dict([("A", 1)]) == {"A": 1}, "pair input preserved")  # noqa: C406
    rejected(TypeError, lambda: type.__setattr__(3, "x", 1))
    rejected(TypeError, lambda: type.__delattr__(3, "x"))


failures = []
for test in (
    operators,
    mutation,
    ordinary,
    strings,
    class_identity,
    dynamic_metaclass,
    keyword_call,
    mapping_input,
):
    try:
        test()
    except Exception as error:
        failures.append([test.__name__, type(error).__name__, str(error)])
print(json.dumps({"checks": 8, "failures": failures}))
if failures:
    raise AssertionError("runtime compatibility failures")
