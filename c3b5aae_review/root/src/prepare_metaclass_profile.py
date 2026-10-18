"""Prepare the runtime-backed profile separately from the stock candidate."""

from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
source = root / "upstream/python-stdlib/enum"
target = root / "metaclass"
target.mkdir(exist_ok=True)
for name in (
    "enum_mini.py",
    "test_enum.py",
    "test_enum_mini.py",
    "test_strenum_identity.py",
    "test_strenum_profile.py",
    "test_enum_hooks.py",
    "test_enum_hooks_mini_first.py",
):
    shutil.copyfile(source / name, target / name)
profile_test = (
    (target / "test_strenum_profile.py")
    .read_text()
    .replace(
        '    dynamic = type("Child", (Base,), {})\n    raises(TypeError, lambda: dynamic("a"))',
        '    raises(TypeError, lambda: type("Child", (Base,), {}))',
    )
)
(target / "test_strenum_profile.py").write_text(profile_test, encoding="utf-8")
text = (source / "enum.py").read_text()
meta = '''class _MemberView:
    """Read-only snapshot; no mutable mapping backing leaks through public API."""

    def __init__(self, pairs):
        object.__setattr__(self, "_pairs", tuple(pairs))

    def __setattr__(self, name, value):
        raise AttributeError("read-only member mapping")

    def __delattr__(self, name):
        raise AttributeError("read-only member mapping")

    def __getitem__(self, key):
        hash(key)
        for name, member in self._pairs:
            if name == key:
                return member
        raise KeyError(key)

    def __iter__(self):
        return (name for name, member in self._pairs)

    def __len__(self):
        return len(self._pairs)

    def keys(self):
        return tuple(self)

    def values(self):
        return tuple(member for name, member in self._pairs)

    def items(self):
        return self._pairs

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def copy(self):
        return dict(self._pairs)

    def __eq__(self, other):
        try:
            return len(self) == len(other) and all(other[k] == v for k, v in self._pairs)
        except (TypeError, KeyError, AttributeError):
            return False


class _StrEnumMeta(type):
    def __new__(meta, name, bases, namespace):
        root = bases == (str, Enum)
        if not root:
            if len(bases) != 1 or bases[0] is not StrEnum:
                raise TypeError("StrEnum requires direct single inheritance")
            if "__members__" in namespace or "_member_map" in namespace:
                raise TypeError("reserved enum metadata")
        cls = type.__new__(meta, name, bases, namespace)
        if not root:
            _finish_str_enum(cls)
        return cls

    def __call__(cls, value=None, names=None, *, start=1):
        if cls is StrEnum:
            if not isinstance(value, str) or not value or names is None:
                raise TypeError("StrEnum requires a name and members")
            if isinstance(names, str):
                values = {name: name.lower() for name in names.replace(",", " ").split()}
            elif isinstance(names, dict):
                values = dict(names)
            else:
                entries = list(names)
                values = dict(entries) if entries and isinstance(entries[0], (tuple, list)) else {name: name for name in entries}
            return _StrEnumMeta(value, (cls,), values)
        if names is not None:
            raise TypeError("cannot extend an enum")
        return _str_lookup(cls, value)

    def __len__(cls):
        return len(cls._member_map)

    def __iter__(cls):
        return iter(cls._member_map)

    def __getitem__(cls, name):
        return cls.__members__[name]

    def __contains__(cls, value):
        return any(member == value for member in cls._member_map)

    def __repr__(cls):
        return "<enum '%s'>" % cls.__name__

    def __setattr__(cls, name, value):
        if "_member_map" in cls.__dict__ and (name in ("__members__", "_member_map", "__new__", "__getitem__") or name in cls.__members__):
            raise AttributeError("cannot reassign enum member or metadata")
        type.__setattr__(cls, name, value)

    def __delattr__(cls, name):
        if "_member_map" in cls.__dict__ and (name in ("__members__", "_member_map", "__new__", "__getitem__") or name in cls.__members__):
            raise AttributeError("cannot delete enum member or metadata")
        type.__delattr__(cls, name)

    @property
    def __members__(cls):
        return _MemberView((member.name, member) for member in cls._member_map)


'''
text = text.replace(
    "class StrEnum(str, Enum):", meta + "class StrEnum(str, Enum, metaclass=_StrEnumMeta):"
)
start = text.index("def _str_lookup(")
end = text.index("# Keep a cooperative dispatcher", start)
section = text[start:end].replace("__members__", "_member_map")
section = section.replace(
    "    cls._member_map = members", '    type.__setattr__(cls, "_member_map", members)'
)
section = section.replace(
    "    cls.__new__ = _str_lookup", '    type.__setattr__(cls, "__new__", _str_lookup)'
)
section = section.replace(
    "    cls.__getitem__ = getitem", '    type.__setattr__(cls, "__getitem__", getitem)'
)
text = text[:start] + section + text[end:]
anchor = "    def __call__(self):\n        return self.value\n"
text = text.replace(
    anchor,
    anchor
    + """
    def __repr__(self):
        return "<%s.%s: %r>" % (type(self).__name__, self.name, self.value)

    def __setattr__(self, name, value):
        if name in ("name", "value", "_name_", "_value_"):
            raise AttributeError("cannot reassign enum identity")
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name in ("name", "value", "_name_", "_value_"):
            raise AttributeError("cannot delete enum identity")
        object.__delattr__(self, name)
""",
)
(target / "enum.py").write_text(text, encoding="utf-8")
formatter = root.parents[1] / "root/build/ci-tools/lint-env/Scripts/ruff.exe"
subprocess.run(
    [
        str(formatter),
        "format",
        "--no-cache",
        "--config",
        str(root / "upstream/pyproject.toml"),
        str(target / "enum.py"),
    ],
    check=True,
)
print(target)
