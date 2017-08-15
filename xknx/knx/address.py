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
from xknx.exceptions import CouldNotParseAddress


class AddressType(Enum):
    """Enum class for different type of addresses."""

    PHYSICAL = 1
    GROUP = 2


class AddressFormat(Enum):
    """Enum class for different writing of addresses."""

    LEVEL2 = 1
    LEVEL3 = 2
    FREE = 3


class Address:
    """Class for handling KNX pyhsical and group addresses."""

    MAX_PYHSICAL_1 = 0x0F  # 15
    MAX_PYHSICAL_2 = 0x0F  # 15
    MAX_PYHSICAL_3 = 0xFF  # 255

    MAX_LEVEL3_1 = 0x1F  # 31
    MAX_LEVEL3_2 = 0x07  # 7
    MAX_LEVEL3_3 = 0xFF  # 255

    MAX_LEVEL2_1 = 0x1F  # 31
    MAX_LEVEL2_2 = 0x07FF  # 2047

    MAX_FREE = 0xFFFF  # 65535

    def __init__(self, address=0, address_type=None, address_format=AddressFormat.LEVEL3):
        """Initialize Address class."""
        self.raw = None
        self.address_format = address_format
        self._set(address, address_type)

    def _set(self, address, address_type):

        self.address_type = \
            address_type if address_type is not None \
            else self._detect_address_type(address)

        if address is None:
            self.raw = 0

        elif isinstance(address, Address):
            self.raw = address.raw
            self.address_format = address.address_format

        elif isinstance(address, str):
            if self.address_type == AddressType.PHYSICAL:
                self._set_str_physical(address)
            else:
                self._set_str_group(address)

        elif isinstance(address, int):
            self._set_int(address)

        elif isinstance(address, tuple):
            self._set_tuple(address)

        else:
            raise TypeError()

    def _set_str_physical(self, address):
        parts = address.split(".")
        if any(not part.isdigit() for part in parts):
            raise CouldNotParseAddress(address)
        if len(parts) != 3:
            raise CouldNotParseAddress(address)
        main = int(parts[0])
        middle = int(parts[1])
        sub = int(parts[2])
        if main > self.MAX_PYHSICAL_1:
            raise CouldNotParseAddress(address)
        if middle > self.MAX_PYHSICAL_2:
            raise CouldNotParseAddress(address)
        if sub > self.MAX_PYHSICAL_3:
            raise CouldNotParseAddress(address)
        self.raw = (main << 12) + (middle << 8) + sub
        self.address_format = AddressFormat.LEVEL3

    def _set_str_group(self, address):
        parts = address.split("/")

        if any(not part.isdigit() for part in parts):
            raise CouldNotParseAddress(address)
        if len(parts) == 1:
            self._set_str_group_free(parts)
        elif len(parts) == 2:
            self._set_str_group_level2(parts)
        elif len(parts) == 3:
            self._set_str_group_level3(parts)
        else:
            raise CouldNotParseAddress(address)

    def _set_str_group_free(self, parts):
        self._set_int(int(parts[0]))
        self.address_format = AddressFormat.FREE

    def _set_str_group_level2(self, parts):
        main = int(parts[0])
        sub = int(parts[1])
        if main > self.MAX_LEVEL2_1:
            raise CouldNotParseAddress(parts)
        if sub > self.MAX_LEVEL2_2:
            raise CouldNotParseAddress(parts)
        self.raw = (main << 11) + sub
        self.address_format = AddressFormat.LEVEL2

    def _set_str_group_level3(self, parts):
        main = int(parts[0])
        middle = int(parts[1])
        sub = int(parts[2])
        if main > self.MAX_LEVEL3_1:
            raise CouldNotParseAddress(parts)
        if middle > self.MAX_LEVEL3_2:
            raise CouldNotParseAddress(parts)
        if sub > self.MAX_LEVEL3_3:
            raise CouldNotParseAddress(parts)
        self.raw = (main << 11) + (middle << 8) + sub
        self.address_format = AddressFormat.LEVEL3

    def _set_tuple(self, address):
        if len(address) != 2 \
                or any(not isinstance(byte, int) for byte in address) \
                or any(byte < 0 for byte in address) \
                or any(byte > 255 for byte in address):
            raise CouldNotParseAddress(address)

        self._set_int(address[0] * 256 + address[1])

    def _set_int(self, raw):
        if not isinstance(raw, int):
            raise CouldNotParseAddress(raw)
        if raw > 65535:
            raise CouldNotParseAddress(raw)
        self.raw = raw

    def get_physical_1(self):
        """Return 1st part of pyhsical address."""
        return (self.raw >> 12) & self.MAX_PYHSICAL_1

    def get_physical_2(self):
        """Return 2nd part of pyhsical address."""
        return (self.raw >> 8) & self.MAX_PYHSICAL_2

    def get_physical_3(self):
        """Return 3rd part of pyhsical address."""
        return self.raw & self.MAX_PYHSICAL_3

    def get_level3_1(self):
        """Return 1st part of level3 group address."""
        return (self.raw >> 11) & self.MAX_LEVEL3_1

    def get_level3_2(self):
        """Return 2nd part of level3 group address."""
        return (self.raw >> 8) & self.MAX_LEVEL3_2

    def get_level3_3(self):
        """Return 3rd part of level3 group address."""
        return self.raw & self.MAX_LEVEL3_3

    def get_level2_1(self):
        """Return 1st part of level2 group address."""
        return (self.raw >> 11) & self.MAX_LEVEL2_1

    def get_level2_2(self):
        """Return 2nd part of level2 group address."""
        return self.raw & self.MAX_LEVEL2_2

    def get_free(self):
        """Return the only part of free format group address."""
        return self.raw & self.MAX_FREE

    def str(self):
        """Return the address in the written string representation."""
        if self.address_type == AddressType.PHYSICAL:
            return self._str_physical()
        elif self.address_format == AddressFormat.FREE:
            return self._str_free()
        elif self.address_format == AddressFormat.LEVEL2:
            return self._str_level2()
        elif self.address_format == AddressFormat.LEVEL3:
            return self._str_level3()
        else:
            raise TypeError()

    def _str_free(self):
        """Return the address in the written string representation in free format."""
        return '{0}'.format(
            self.get_free())

    def _str_level2(self):
        """Return the address in the written string representation in 2nd level format."""
        return '{0}/{1}'.format(
            self.get_level2_1(),
            self.get_level2_2())

    def _str_level3(self):
        """Return the address in the written string representation 3rd level format."""
        return '{0}/{1}/{2}'.format(
            self.get_level3_1(),
            self.get_level3_2(),
            self.get_level3_3())

    def _str_physical(self):
        """Return the address in the written string representation in the format for physical addresses."""
        return '{0}.{1}.{2}'.format(
            self.get_physical_1(),
            self.get_physical_2(),
            self.get_physical_3())

    @staticmethod
    def _detect_address_type(address):
        """Return the type of address from the style of writing."""
        # Physical addresses have either be specified explicitely or
        # in the correct notation. As default an address is a group address.
        if isinstance(address, str) and "." in address:
            return AddressType.PHYSICAL
        elif isinstance(address, Address):
            return address.address_type
        return AddressType.GROUP

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        return (self.raw >> 8) & 255, self.raw & 255

    def __str__(self):
        """Return object as readable string."""
        return '<Address str="{0}" />'.format(self.str())

    def __eq__(self, other):
        """Equal operator."""
        if other is None:
            return False
        if not isinstance(other, Address):
            raise TypeError()
        return self.raw == other.raw
