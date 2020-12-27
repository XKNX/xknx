"""Helper functions for config validation."""
from enum import Enum
from numbers import Number
import os
import re
from typing import Any, List, Type, TypeVar, Union

import voluptuous as vol
from xknx.dpt import DPTBase
from xknx.telegram import GroupAddress, IndividualAddress

# pylint: disable=invalid-name
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
    value = str(value)
    if value.isdigit() and 0 <= int(value) <= GroupAddress.MAX_FREE:
        return value

    if not GroupAddress.ADDRESS_RE.match(value):
        raise vol.Invalid(f"{value} is not a valid group address")

    return value


def ensure_individual_address(value: str) -> str:
    """Ensure value is a valid individual address."""
    value = str(value)
    if not IndividualAddress.ADDRESS_RE.match(value):
        raise vol.Invalid(f"{value} is not a valid individual address")

    return value


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


def sensor_value_type(value: T) -> T:
    """Validate sensor type."""
    if DPTBase.parse_transcoder(value):
        return value

    if value.lower() in ["binary", "time", "datetime", "date"]:
        return str(value)

    raise vol.Invalid(f"invalid value type {value}")


VALID_ENTITY_ID = re.compile(r"^(?!.+__)(?!_)[\da-z_]+(?<!_)\.(?!_)[\da-z_]+(?<!_)$")


def valid_entity_id(entity_id: str) -> bool:
    """Test if an entity ID is a valid format.

    Format: <domain>.<entity> where both are slugs.
    """
    return VALID_ENTITY_ID.match(entity_id) is not None


def match_all(value: T) -> T:
    """Validate that matches all values."""
    return value
