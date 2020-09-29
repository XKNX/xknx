"""Helper functions for config validation."""
from enum import Enum
from numbers import Number
import os
from typing import Any, List, Type, TypeVar, Union

import voluptuous as vol
from xknx.dpt import DPTBase
from xknx.telegram import GroupAddress

# typing typevar
T = TypeVar("T")


positive_int = vol.All(vol.Coerce(int), vol.Range(min=0))
port = vol.All(vol.Coerce(int), vol.Range(min=1, max=65535))


def string(value: Any) -> str:
    """Coerce value to string, except for None."""
    if value is None:
        raise vol.Invalid("string value is None")
    if isinstance(value, (list, dict)):
        raise vol.Invalid("value should be a string")

    return str(value)


def boolean(value: Any) -> bool:
    """Validate and coerce a boolean value."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.lower().strip()
        if value in ("1", "true", "yes", "on", "enable"):
            return True
        if value in ("0", "false", "no", "off", "disable"):
            return False
    elif isinstance(value, Number):
        # type ignore: https://github.com/python/mypy/issues/3186
        return value != 0  # type: ignore
    raise vol.Invalid(f"invalid boolean value {value}")


def ensure_list(value: Union[T, List[T], None]) -> List[T]:
    """Wrap value in list if it is not one."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def ensure_group_address(value: str) -> str:
    """Ensure value is a valid KNX group address."""
    if not GroupAddress.ADDRESS_RE.match(value):
        raise vol.Invalid(f"{value} is not a valid group address")

    return str(value)


def isdir(value: Any) -> str:
    """Validate that the value is an existing dir."""
    if value is None:
        raise vol.Invalid("not a directory")
    dir_in = os.path.expanduser(str(value))

    if not os.path.isdir(dir_in):
        raise vol.Invalid("not a directory")
    if not os.access(dir_in, os.W_OK):
        raise vol.Invalid("directory not writable")
    return dir_in


def enum(value: Type[Enum]) -> vol.All:
    """Create validator for specified enum."""
    return vol.All(vol.In(value.__members__), value.__getitem__)


def sensor_value_type(value: str) -> str:
    """Validate sensor type."""
    for dpt in DPTBase.__recursive_subclasses__():
        if dpt.has_distinct_value_type() and dpt.value_type == value:
            return str(value)

    raise vol.Invalid(f"invalid value type {value}")


def match_all(value: T) -> T:
    """Validate that matches all values."""
    return value
