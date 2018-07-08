"""Implementation of Basic KNX datatypes."""
from enum import Enum

from xknx.exceptions import ConversionError


class DPTBinary(object):
    """The DPTBinary is a base class for all datatypes encoded directly into the first Byte of the payload (mostly integer)."""

    # pylint: disable=too-few-public-methods

    # APCI (application layer control information)
    APCI_BITMASK = 0x3F
    APCI_MAX_VALUE = APCI_BITMASK

    def __init__(self, value):
        """Initialize DPTBinary class."""
        if not isinstance(value, int):
            raise TypeError()
        if value > DPTBinary.APCI_BITMASK:
            raise ConversionError("Cant init DPTBinary", value=value)

        self.value = value

    def __eq__(self, other):
        """Equal operator."""
        return DPTComparator.compare(self, other)

    def __str__(self):
        """Return object as readable string."""
        return '<DPTBinary value="{0}" />'.format(self.value)


class DPTArray(object):
    """The DPTArray is a base class for all datatypes appended to the KNX telegram."""

    # pylint: disable=too-few-public-methods
    def __init__(self, value):
        """Initialize DPTArray class."""
        if isinstance(value, int):
            self.value = (value,)
        elif isinstance(value, (list, bytes)):
            self.value = tuple(value,)
        elif isinstance(value, tuple):
            self.value = value
        else:
            raise TypeError()

    def __eq__(self, other):
        """Equal operator."""
        return DPTComparator.compare(self, other)

    def __str__(self):
        """Return object as readable string."""
        return '<DPTArray value="[{0}]" />'.format(
            ','.join(hex(b) for b in self.value))


class DPTComparator():
    """Helper class to compare different types of DPT objects."""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def compare(a, b):
        """Test if 'a' and 'b' are the same."""
        # pylint: disable=invalid-name,too-many-return-statements,len-as-condition
        if a is None and b is None:
            return True

        elif a is None:
            if isinstance(b, DPTBinary):
                return b.value == 0
            elif isinstance(b, DPTArray):
                return len(b.value) == 0

        elif b is None:
            if isinstance(a, DPTBinary):
                return a.value == 0
            elif isinstance(a, DPTArray):
                return len(a.value) == 0

        elif isinstance(a, DPTArray) and isinstance(b, DPTArray):
            return a.value == b.value

        elif isinstance(a, DPTBinary) and isinstance(b, DPTBinary):
            return a.value == b.value

        elif isinstance(a, DPTBinary) and isinstance(b, DPTArray):
            return a.value == 0 and len(b.value) == 0

        elif isinstance(a, DPTArray) and isinstance(b, DPTBinary):
            return len(a.value) == 0 and b.value == 0

        raise TypeError()


class DPTWeekday(Enum):
    """Enum class for week days."""

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7
    NONE = 0
