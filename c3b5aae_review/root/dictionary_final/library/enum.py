# enum.py
# Enum/IntEnum containers and a runtime-backed typed StrEnum profile
# version="1.5.0"

import builtins

# ==============================================================================
# Variable & Abbreviation Definitions:
# ==============================================================================
# Functions & Helper Methods:
#   _c(e, n, v, t) -> create_enum_item: Helper function to construct a typed enum instance.
#   _i()        -> items: Classmethod to lazily initialize and return the __members__ dict.
#   a(s, k, v)  -> __setattr__: Inner setter guard raising AttributeError on enum items.
#
# Helper Arguments & Local Variables:
#   e       - enum_name / enum_item: Class name string or instance of an enum item.
#   n       - name: String representing the enum member key (e.g., "RED").
#   v       - value / member value: Value assigned to, searched within, or passed to lookup.
#   c       - class / new_class: Dynamically created Enum subclass via `type()`.
#   t       - value_type: Target constraint type (`int`, `str`, or `None` for generic Enum).
#   l       - names_list: List of parsed string keys from comma/space-separated inputs.
#   d       - dict / mapping: Temporary dictionary for parsed enum members.
#   k, v    - key, value: Key-value pair during iteration over attributes or dictionaries.
#   i       - item: Individual enum member instance during iteration.
#   __members__ - Original containers map members to values; typed StrEnum maps names to members.
#   s, k, o - self, key/attribute_name, other_enum (standard short parameters).
#   f       - function: The body function of the class being defined.
#   b       - bases: Tuple of base classes passed during class creation.
#   kw      - kwargs: Additional keyword arguments passed during class creation.
#   cls     - class object: Target class being created or initialized.
# ==============================================================================


def _c(e, n, v, t=None):
    # Inner guard to prevent modification of enum item attributes
    def a(s, k, v):
        raise AttributeError("cannot set attribute")

    # Type checks for IntEnum and StrEnum
    if t is int and not isinstance(v, int):
        raise TypeError(f"IntEnum member {n!r} value must be int, got {type(v).__name__}")
    elif t is str and not isinstance(v, str):
        raise TypeError(f"StrEnum member {n!r} value must be str, got {type(v).__name__}")

    # Safely extract class name string if a class or object was passed
    e = getattr(e, "__name__", str(e))

    # Create dynamic subclass inheriting the value's type (int, str, float etc.)
    return type(
        f"{e}.{n}",
        (type(v),),
        {
            "name": n,
            "value": v,
            "__str__": lambda s: str(v) if t in (int, str) else f"{e}.{n}",
            "__repr__": lambda s: f"<{e}.{n}: {v!r}>",
            "__call__": lambda s: v,
            "__setattr__": a,
        },
    )(v)


class Enum:
    _v_t = None  # Expected value type constraint (int, str, or None)

    def __new__(cls, value=None, names=None, *, start=1):
        # Functional API: dynamic creation of a new Enum class
        if value is not None and names is not None:
            is_str = cls._v_t is str

            # Parse 'names' parameter into a key-value dictionary
            if isinstance(names, dict):
                d = names
            elif isinstance(names, str):
                # Space or comma-separated string of member names
                l = names.replace(",", " ").split()
                d = (
                    {k: k.lower() for k in l}
                    if is_str
                    else {k: v for v, k in enumerate(l, start=start)}
                )
            elif isinstance(names, (list, tuple)):
                # List/tuple of strings or (name, value) pairs
                if names and isinstance(names[0], (list, tuple)):
                    d = dict(names)
                else:
                    d = (
                        {k: k for k in names}
                        if is_str
                        else {k: v for v, k in enumerate(names, start=start)}
                    )
            else:
                # Other iterables (e.g., sets)
                d = (
                    {k: k for k in names}
                    if is_str
                    else {k: v for v, k in enumerate(names, start=start)}
                )

            # Construct and return a new Enum subclass
            c = type(str(value), (cls,), {})
            for k, v in d.items():
                setattr(c, k, v)
            c._i()
            return c

        if cls not in (Enum, IntEnum, StrEnum):
            # Lazy initialization of subclass members
            cls._i()

            # Lookup existing member by value or name: e.g., Color(1) or Color("RED")
            if value is not None:
                return cls()(value)

        return super().__new__(cls)

    @classmethod
    def __contains__(cls, v):
        # Lookup member by value or name
        for i in cls._i():
            if i.value == v or i.name == v:
                return True
        return False

    @classmethod
    def __call__(cls, v=None):
        if v is None:
            return cls()

        # Lookup member by value or name
        for i in cls._i():
            if i.value == v or i.name == v:
                return i
        raise ValueError(f"{v!r} is not a valid {cls.__name__}")

    @classmethod
    def __getitem__(cls, k):
        # Instance-level container lookup: Color["RED"]
        for i in cls._i():
            if i.name == k:
                return i
        raise KeyError(k)

    # Equality checks if both classes are Enums and have identical __members__ dicts
    __eq__ = classmethod(lambda cls, o: getattr(o, "_i", False) and cls._i() == o._i())
    # Iteration yields enum member instances (keys of __members__)
    __iter__ = classmethod(lambda cls: iter(cls._i()))
    __len__ = classmethod(lambda cls: len(cls._i()))
    __str__ = __repr__ = classmethod(lambda cls: f"<enum '{type(cls).__name__}'>")

    @classmethod
    def __setattr__(cls, k, v):
        raise AttributeError("cannot set attribute")

    @classmethod
    def __delattr__(cls, k):
        raise AttributeError("cannot delete attribute")

    @classmethod
    def dump(cls):
        # Serialize enum members to string representation for eval compatibility
        # cls == eval(cls.dump())
        if cls._v_t is None:
            e = "Enum"
        else:
            e = cls._v_t.__name__[0].upper() + cls._v_t.__name__[1:] + "Enum"
        d = {i.name: i.value for i in cls._i()}
        return f"{e}('{cls.__name__}', {d})"

    @classmethod
    def _i(cls):
        # Initialize and return dictionary mapping enum member instances to their values
        if "__members__" not in cls.__dict__:
            # Convert raw class attributes into typed enum instances
            cls.__members__ = {}
            for k, v in list(cls.__dict__.items()):
                if not k.startswith("_") and not callable(v):
                    if isinstance(v, cls):
                        continue
                    if v in cls.__members__:
                        raise ValueError(f"duplicate value {v!r} in {cls.__name__}")
                    e = _c(cls.__name__, k, v, cls._v_t)
                    setattr(cls, k, e)
                    cls.__members__[e] = v
        return cls.__members__


class IntEnum(Enum):
    _v_t = int


class _MemberView:
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
                values = (
                    dict(entries)
                    if entries and isinstance(entries[0], (tuple, list))
                    else {name: name for name in entries}
                )
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
        if "_member_map" in cls.__dict__ and (
            name in ("__members__", "_member_map", "__new__", "__getitem__")
            or name in cls.__members__
        ):
            raise AttributeError("cannot reassign enum member or metadata")
        type.__setattr__(cls, name, value)

    def __delattr__(cls, name):
        if "_member_map" in cls.__dict__ and (
            name in ("__members__", "_member_map", "__new__", "__getitem__")
            or name in cls.__members__
        ):
            raise AttributeError("cannot delete enum member or metadata")
        type.__delattr__(cls, name)

    @property
    def __members__(cls):
        return _MemberView((member.name, member) for member in cls._member_map)


class StrEnum(str, Enum, metaclass=_StrEnumMeta):
    """String-valued members that retain their declared class on MicroPython."""

    _v_t = str

    def __new__(cls, value=None, names=None, *, start=1):
        if cls is StrEnum:
            if not isinstance(value, str) or not value or names is None:
                raise TypeError("StrEnum requires a name and members")
            return Enum.__new__(cls, value, names, start=start)
        return _str_lookup(cls, value)

    @classmethod
    def _i(cls):
        return _finish_str_enum(cls)

    @classmethod
    def dump(cls):
        values = {member.name: member.value for member in cls._i()}
        return f"StrEnum({cls.__name__!r}, {values!r})"

    def __call__(self):
        return self.value

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


def _str_lookup(cls, value=None):
    # Retain the old optional initialization call as a no-op returning the class.
    if "_member_map" not in cls.__dict__:
        raise TypeError("cannot extend an enum")
    if value is None:
        return cls
    if isinstance(value, cls):
        return value
    for member in cls._member_map:
        if member.value == value or member.name == value:
            return member
    raise ValueError(f"{value!r} is not a valid {cls.__name__}")


def _finish_str_enum(cls):
    # Declared-class construction followed by installing canonical lookup is
    # adapted from Dungeon Drifters' portable StrEnum, by MrCodeGameAndAnime:
    # https://github.com/MrCodeGameandAnime/Dungeon-Drifters/blob/2fa5f9d0ca806e5e7dbd41f3ac9073465d26762b/root/portability/micropython/enum.py
    if cls is StrEnum:
        raise TypeError("StrEnum is a base class")
    if "_member_map" in cls.__dict__:
        if cls.__dict__.get("__new__") is not _str_lookup:
            raise TypeError("_member_map is reserved for enum metadata")
        return cls._member_map
    if "__new__" in cls.__dict__ or "__init__" in cls.__dict__:
        raise TypeError("custom StrEnum constructors are not supported")
    candidates = []
    values = set()
    for name, value in cls.__dict__.items():
        if name.startswith("_") or (callable(value) and not isinstance(value, str)):
            continue
        if not isinstance(value, str):
            raise TypeError(f"StrEnum member {name!r} value must be str")
        value = str(value)
        if value in values:
            raise ValueError(f"duplicate value {value!r} in {cls.__name__}")
        values.add(value)
        candidates.append((name, value))

    # Native-base initialization provides allocation even though MicroPython
    # does not expose str.__new__. This keeps the standard functional API.
    members = {}
    for name, value in candidates:
        if hasattr(str, "__new__"):
            member = str.__new__(cls, value)
        else:
            member = object.__new__(cls)
            super(StrEnum, member).__init__(value)
        object.__setattr__(member, "name", name)
        object.__setattr__(member, "value", value)
        setattr(cls, name, member)
        members[member] = value
    # MicroPython's iterator fallback loads a class's unbound __getitem__.
    # Instances still need ordinary string indexing, hence the two arities.
    ordered = tuple(members)
    missing = object()

    def getitem(subject, index=missing):
        if index is missing:
            return ordered[subject]
        return subject.value[index]

    type.__setattr__(cls, "_member_map", members)
    type.__setattr__(cls, "__new__", _str_lookup)
    type.__setattr__(cls, "__getitem__", getitem)
    return members


# Keep a cooperative dispatcher shared across fresh imports. Each registered
# family retains its own bases and finalizer so existing imported aliases work.
def _make_builder(families, legacy_bases, previous):
    def build(function, name, *bases, **kwargs):
        typed = None
        for family in families:
            if any(isinstance(base, type) and issubclass(base, family[1]) for base in bases):
                typed = family
                break
        if typed is not None and (len(bases) != 1 or bases[0] is not typed[1]):
            raise TypeError("StrEnum requires direct single inheritance")
        cls = previous(function, name, *bases, **kwargs)
        if not isinstance(cls, type):
            return cls
        if typed is not None:
            typed[2](cls)
            return cls
        legacy = [family[0] for family in families]
        legacy.extend(legacy_bases)
        if any(
            isinstance(base, type) and issubclass(base, root) for base in bases for root in legacy
        ):
            return cls()
        return cls

    return build


_SN = "__ENUM_STATE__"
try:
    _state = __ENUM_STATE__
except NameError:
    _state = None
if _state is None:
    _state = {"original": __build_class__}
    setattr(builtins, _SN, _state)
if "families" not in _state:
    _state["families"] = []
    _state.setdefault("legacy_bases", [])
    # Bare lookup observes the effective hook on MicroPython even when reading
    # builtins.__build_class__ still exposes the original module attribute.
    _state["wrapper"] = _make_builder(_state["families"], _state["legacy_bases"], __build_class__)
    builtins.__build_class__ = _state["wrapper"]
_old_base = _state.get("base")
if isinstance(_old_base, type) and not any(_old_base is base for base in _state["legacy_bases"]):
    _state["legacy_bases"].append(_old_base)
_state["families"].append((Enum, StrEnum, _finish_str_enum))
_state["base"] = Enum
