"""The mini implementation may be loaded before the full module."""

import enum_mini
import enum


class Mini(enum_mini.Enum):
    A = 1


class Mode(enum.StrEnum):
    FAST = "fast"


if Mini.A.name != "A" or len(Mini) != 1:
    raise AssertionError("mini-first container initialization")
if type(Mode.FAST) is not Mode or Mode("fast") is not Mode.FAST:
    raise AssertionError("typed class after mini-first import")
print("mini-first import checks passed")
