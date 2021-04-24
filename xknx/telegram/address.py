"""
Module for serialization/deserialization and handling of KNX addresses.

The module can handle:

* individual addresses of devices.
* (logical) group addresses.
* xknx internal group addresses.

The module supports all different writings of group addresses:

* 3rn level: "1/2/3"
* 2nd level: "1/2"
* Free format: "123"
"""
from __future__ import annotations

from abc import ABC
from enum import Enum
from re import compile as re_compile
from typing import Optional, Tuple, Union

from xknx.exceptions import CouldNotParseAddress

# TODO: typing - remove need for Optional here
GroupAddressableType = Optional[Union["GroupAddress", str, int, Tuple[int, int]]]
IndividualAddressableType = Optional[
    Union["IndividualAddress", str, int, Tuple[int, int]]
]
InternalGroupAddressableType = Union["InternalGroupAddress", str]
DeviceAddressableType = Union[GroupAddressableType, InternalGroupAddressableType]
DeviceGroupAddress = Union["GroupAddress", "InternalGroupAddress"]


def parse_device_group_address(
    address: DeviceAddressableType,
) -> DeviceGroupAddress:
    """Parse an Addressable type to GroupAddress or InternalGroupAddress."""
    if isinstance(address, (GroupAddress, InternalGroupAddress)):
        return address
    try:
        return GroupAddress(address)
    except CouldNotParseAddress as ex:
        if isinstance(address, str):
            return InternalGroupAddress(address)
        raise ex


def address_tuple_to_int(address: tuple[int, int]) -> int:
    """
    Convert the tuple `address` to an integer.

    Valid values inside the `address` tuple are:
    * Positive Numbers between 0 and 255 (binary)
    """
    if (
        any(not isinstance(byte, int) for byte in address)
        or any(byte < 0 for byte in address)
        or any(byte > 255 for byte in address)
    ):
        raise CouldNotParseAddress(address)
    return int(address[0] * 256 + address[1])


class BaseAddress(ABC):
    """Base class for all knx address types."""

    def __init__(self) -> None:
        """Initialize instance variables needed by all subclasses."""
        self.raw: int = 0

    def to_knx(self) -> tuple[int, int]:
        """
        Serialize to KNX/IP raw data.

        Returns a 2-Byte tuple generated from the raw Value.
        """
        return (self.raw >> 8) & 255, self.raw & 255

    def __eq__(self, other: object | None) -> bool:
        """
        Implement the equal operator.

        Returns `True` if we check against the same subclass and the
        raw Value matches.
        """
        if isinstance(self, type(other)):
            return self.__hash__() == other.__hash__()
        return False

    def __hash__(self) -> int:
        """Hash Address so it can be used as dict key."""
        return self.raw


class IndividualAddress(BaseAddress):
    """Class for handling KNX individual addresses."""

    MAX_AREA = 15
    MAX_MAIN = 15
    MAX_LINE = 255
    ADDRESS_RE = re_compile(
        r"^(?P<area>\d{1,2})\.(?P<main>\d{1,2})\.(?P<line>\d{1,3})$"
    )

    def __init__(self, address: IndividualAddressableType) -> None:
        """Initialize IndividualAddress class."""
        super().__init__()
        if isinstance(address, IndividualAddress):
            self.raw = address.raw
        elif isinstance(address, str):
            if address.isdigit():
                self.raw = int(address)
            else:
                self.raw = self.__string_to_int(address)
        elif isinstance(address, tuple) and len(address) == 2:
            self.raw = address_tuple_to_int(address)
        elif isinstance(address, int):
            self.raw = address
        elif address is None:
            self.raw = 0
        else:
            raise CouldNotParseAddress(address)

        if self.raw > 65535:
            raise CouldNotParseAddress(address)

    def __string_to_int(self, address: str) -> int:
        """
        Parse `address` as string to an integer and do some simple checks.

        Returns the integer representation of `address` if all checks are valid:
        * string matches against the regular expression
        * area, main and line are inside its range

        In any other case, we raise an `CouldNotParseAddress` exception.
        """
        match = self.ADDRESS_RE.match(address)
        if not match:
            raise CouldNotParseAddress(address)
        area = int(match.group("area"))
        main = int(match.group("main"))
        line = int(match.group("line"))
        if area > self.MAX_AREA or main > self.MAX_MAIN or line > self.MAX_LINE:
            raise CouldNotParseAddress(address)
        return (area << 12) + (main << 8) + line

    @property
    def area(self) -> int:
        """Return area part of individual address."""
        return (self.raw >> 12) & self.MAX_AREA

    @property
    def main(self) -> int:
        """Return main part of individual address."""
        return (self.raw >> 8) & self.MAX_MAIN

    @property
    def line(self) -> int:
        """Return line part of individual address."""
        return self.raw & self.MAX_LINE

    @property
    def is_device(self) -> bool:
        """Return `True` if this address is a valid device address."""
        return self.line != 0

    @property
    def is_line(self) -> bool:
        """Return `True` if this address is a valid line address."""
        return not self.is_device

    def __str__(self) -> str:
        """Return object as in KNX notation (e.g. '1.2.3')."""
        return f"{self.area}.{self.main}.{self.line}"

    def __repr__(self) -> str:
        """Return this object as parsable string."""
        return f'IndividualAddress("{self}")'


class GroupAddressType(Enum):
    """
    Possible types of `GroupAddress`.

    KNX knows three types of group addresses:
    * FREE, a integer or hex representation
    * SHORT, a representation like '1/123', without middle groups
    * LONG, a representation like '1/2/34', with middle groups
    """

    FREE = 0
    SHORT = 2
    LONG = 3


class GroupAddress(BaseAddress):
    """Class for handling KNX group addresses."""

    MAX_MAIN = 31
    MAX_MIDDLE = 7
    MAX_SUB_LONG = 255
    MAX_SUB_SHORT = 2047
    MAX_FREE = 65535

    ADDRESS_RE = re_compile(
        r"^(?P<main>\d{1,2})(/(?P<middle>\d{1,2}))?/(?P<sub>\d{1,4})$"
    )

    def __init__(
        self,
        address: GroupAddressableType,
        levels: GroupAddressType = GroupAddressType.LONG,
    ) -> None:
        """Initialize GroupAddress class."""
        super().__init__()
        self.levels = levels

        if isinstance(address, GroupAddress):
            self.raw = address.raw
        elif isinstance(address, str):
            if address.isdigit():
                self.raw = int(address)
            else:
                self.raw = self.__string_to_int(address)
        elif isinstance(address, tuple) and len(address) == 2:
            self.raw = address_tuple_to_int(address)
        elif isinstance(address, int):
            self.raw = address
        elif address is None:
            self.raw = 0
        else:
            raise CouldNotParseAddress(address)

        if self.raw > 65535:
            raise CouldNotParseAddress(address)

    def __string_to_int(self, address: str) -> int:
        """
        Parse `address` as string to an integer and do some simple checks.

        Returns the integer representation of `address` if all checks are valid:
        * string matches against the regular expression
        * main, middle and sub are inside its range

        In any other case, we raise an `CouldNotParseAddress` exception.
        """
        match = self.ADDRESS_RE.match(address)
        if not match:
            raise CouldNotParseAddress(address)
        main = int(match.group("main"))
        middle = (
            int(match.group("middle")) if match.group("middle") is not None else None
        )
        sub = int(match.group("sub"))
        if main > self.MAX_MAIN:
            raise CouldNotParseAddress(address)
        if middle is not None:
            if middle > self.MAX_MIDDLE:
                raise CouldNotParseAddress(address)
            if sub > self.MAX_SUB_LONG:
                raise CouldNotParseAddress(address)
        else:
            if sub > self.MAX_SUB_SHORT:
                raise CouldNotParseAddress(address)
        return (
            (main << 11) + (middle << 8) + sub
            if middle is not None
            else (main << 11) + sub
        )

    @property
    def main(self) -> int | None:
        """
        Return the main group part as an integer.

        Works only if the group dont uses `GroupAddressType.FREE`, returns `None`
        in any other case.
        """
        return (
            (self.raw >> 11) & self.MAX_MAIN
            if self.levels != GroupAddressType.FREE
            else None
        )

    @property
    def middle(self) -> int | None:
        """
        Return the middle group part as an integer.

        Works only if the group uses `GroupAddressType.LONG`, returns `None` in
        any other case.
        """
        return (
            (self.raw >> 8) & self.MAX_MIDDLE
            if self.levels == GroupAddressType.LONG
            else None
        )

    @property
    def sub(self) -> int:
        """
        Return the sub group part as an integer.

        Works with any `GroupAddressType`, as we always have sub groups.
        """
        if self.levels == GroupAddressType.SHORT:
            return self.raw & self.MAX_SUB_SHORT
        if self.levels == GroupAddressType.LONG:
            return self.raw & self.MAX_SUB_LONG
        return self.raw

    def __str__(self) -> str:
        """
        Return object as in KNX notation (e.g. '1/2/3').

        Honors the used `GroupAddressType` of this group.
        """
        if self.levels == GroupAddressType.LONG:
            return f"{self.main}/{self.middle}/{self.sub}"
        if self.levels == GroupAddressType.SHORT:
            return f"{self.main}/{self.sub}"
        return f"{self.sub}"

    def __repr__(self) -> str:
        """Return object as parsable string."""
        return f'GroupAddress("{self}")'


class InternalGroupAddress:
    """Class for handling addresses used internally in xknx devices only."""

    def __init__(self, address: str | InternalGroupAddress) -> None:
        """Initialize InternalGroupAddress class."""
        self.address: str

        if isinstance(address, InternalGroupAddress):
            self.address = address.address
            return
        if not isinstance(address, str):
            raise CouldNotParseAddress(address)

        prefix_length = 1
        if len(address) < 2 or not address[0].lower() == "i":
            raise CouldNotParseAddress(address)
        if address[1] in "-_":
            prefix_length = 2

        self.address = address[prefix_length:].strip()
        if not self.address:
            raise CouldNotParseAddress(address)

    def __str__(self) -> str:
        """Return object as readable string (e.g. 'i-123')."""
        return f"i-{self.address}"

    def __repr__(self) -> str:
        """Return object as parsable string."""
        return f'InternalGroupAddress("{self}")'

    def __eq__(self, other: object | None) -> bool:
        """
        Implement the equal operator.

        Returns `True` if we check against the same subclass and the
        raw Value matches.
        """
        if isinstance(self, type(other)):
            return self.__hash__() == other.__hash__()
        return False

    def __hash__(self) -> int:
        """Hash Address so it can be used as dict key."""
        return hash(self.address)
