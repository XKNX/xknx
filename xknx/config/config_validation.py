"""Helper functions for config validation."""
from numbers import Number
from typing import Any, List, TypeVar, Union

import voluptuous as vol
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
        raise vol.Invalid("string is not a valid group address")

    return str(value)
