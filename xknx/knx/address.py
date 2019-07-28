"""
Module for serialization/deserialization and handling of KNX addresses.

The module can handle:

* physical addresses of devices.
* (logical) group addresses.

The module supports all different writings of group addresses:

* 3rn level: "1/2/3"
* 2nd level: "1/2"
* Free format: "123"
"""
from enum import Enum
from re import compile as re_compile

from xknx.exceptions import CouldNotParseAddress


def address_tuple_to_int(address):
    """
    Convert the tuple `address` to an integer.

    Valid values inside the `address` tuple are:
    * Positive Numbers between 0 and 255 (binary)
    """
    if any(not isinstance(byte, int) for byte in address) \
       or any(byte < 0 for byte in address) \
       or any(byte > 255 for byte in address):
        raise CouldNotParseAddress(address)
    return address[0] * 256 + address[1]


class BaseAddress:  # pylint: disable=too-few-public-methods
    """Base class for all knx address types."""

    def __init__(self):
        """Initialize instance variables needed by all subclasses."""
        self.raw = None

    def to_knx(self):
        """
        Serialize to KNX/IP raw data.

        Returns a 2-Byte tuple generated from the raw Value.
        """
        return (self.raw >> 8) & 255, self.raw & 255

    def __eq__(self, other):
        """
        Implement the equal operator.

        Returns `True` if we check against the same subclass and the
        raw Value matches.

        Returns `False` if we check against `None`.
        """
        if other is None:
            return False
        if not isinstance(other, self.__class__):
            raise TypeError()
        return self.raw == other.raw


class PhysicalAddress(BaseAddress):
    """Class for handling KNX pyhsical addresses."""

    MAX_AREA = 15
    MAX_MAIN = 15
    MAX_LINE = 255
    ADDRESS_RE = re_compile(r'^(?P<area>\d{1,2})\.(?P<main>\d{1,2})\.(?P<line>\d{1,3})$')

    def __init__(self, address):
        """Initialize Address class."""
        super().__init__()
        if isinstance(address, str):
            self.raw = self.__string_to_int(address)
        elif isinstance(address, tuple) and len(address) == 2:
            self.raw = address_tuple_to_int(address)
        elif isinstance(address, int):
            self.raw = address
        elif address is None:
            self.raw = 0
        else:
            raise CouldNotParseAddress(address)

        if isinstance(self.raw, int) and self.raw > 65535:
            raise CouldNotParseAddress(address)

    def __string_to_int(self, address):
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
        area = int(match.group('area'))
        main = int(match.group('main'))
        line = int(match.group('line'))
        if area > self.MAX_AREA or main > self.MAX_MAIN or line > self.MAX_LINE:
            raise CouldNotParseAddress(address)
        return (area << 12) + (main << 8) + line

    @property
    def area(self):
        """Return area part of pyhsical address."""
        return (self.raw >> 12) & self.MAX_AREA

    @property
    def main(self):
        """Return main part of pyhsical address."""
        return (self.raw >> 8) & self.MAX_MAIN

    @property
    def line(self):
        """Return line part of pyhsical address."""
        return self.raw & self.MAX_LINE

    @property
    def is_device(self):
        """Return `True` if this address is a valid device address."""
        return self.line != 0

    @property
    def is_line(self):
        """Return `True` if this address is a valid line address."""
        return not self.is_device

    def __repr__(self):
        """Return this object as parsable string."""
        return 'PhysicalAddress("{0.area}.{0.main}.{0.line}")'.format(self)


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

    ADDRESS_RE = re_compile(r'^(?P<main>\d{1,2})(/(?P<middle>\d{1,2}))?/(?P<sub>\d{1,4})$')

    def __init__(self, address, levels=GroupAddressType.LONG):
        """Initialize Address class."""
        super().__init__()
        self.levels = levels

        if isinstance(address, str) and not address.isdigit():
            self.raw = self.__string_to_int(address)
        elif isinstance(address, str) and address.isdigit():
            self.raw = int(address)
        elif isinstance(address, tuple) and len(address) == 2:
            self.raw = address_tuple_to_int(address)
        elif isinstance(address, int):
            self.raw = address
        elif address is None:
            self.raw = 0
        else:
            raise CouldNotParseAddress(address)

        if isinstance(self.raw, int) and self.raw > 65535:
            raise CouldNotParseAddress(address)

    def __string_to_int(self, address):
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
        main = int(match.group('main'))
        middle = int(match.group('middle')) if match.group('middle') is not None else None
        sub = int(match.group('sub'))
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
        return (main << 11) + (middle << 8) + sub if middle is not None else (main << 11) + sub

    @property
    def main(self):
        """
        Return the main group part as an integer.

        Works only if the group dont uses `GroupAddressType.FREE`, returns `None`
        in any other case.
        """
        return (self.raw >> 11) & self.MAX_MAIN if self.levels != GroupAddressType.FREE else None

    @property
    def middle(self):
        """
        Return the middle group part as an integer.

        Works only if the group uses `GroupAddressType.LONG`, returns `None` in
        any other case.
        """
        return (self.raw >> 8) & self.MAX_MIDDLE if self.levels == GroupAddressType.LONG else None

    @property
    def sub(self):
        """
        Return the sub group part as an integer.

        Works with any `GroupAddressType`, as we always have sub groups.
        """
        if self.levels == GroupAddressType.SHORT:
            return self.raw & self.MAX_SUB_SHORT
        if self.levels == GroupAddressType.LONG:
            return self.raw & self.MAX_SUB_LONG
        return self.raw

    def __str__(self):
        """
        Return object as in KNX notation (e.g. '1/2/3').

        Honors the used `GroupAddressType` of this group.
        """
        if self.levels == GroupAddressType.LONG:
            return '{0.main}/{0.middle}/{0.sub}'.format(self)
        if self.levels == GroupAddressType.SHORT:
            return '{0.main}/{0.sub}'.format(self)
        return '{0.sub}'.format(self)

    def __repr__(self):
        """Return object as readable string."""
        return 'GroupAddress("{0}")'.format(self)
