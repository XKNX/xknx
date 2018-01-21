"""Implementation of 3.17 Datapoint Types String."""
from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTString(DPTBase):
    """
    Abstraction for KNX 14 Octet String.

    DPT 3.17
    """

    STRING_SIZE = 14

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, cls.STRING_SIZE)
        value = str()
        for byte in raw:
            if byte != 0x00:
                value += chr(byte)
        return value

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if not isinstance(value, str):
            raise ConversionError("Cant serialize DPTString", value=value)
        if not cls._test_boundaries(value):
            raise ConversionError("Cant serialize DPTString", value=value)

        raw = []
        for character in value:
            raw.append(ord(character))
        raw.extend([0] * (cls.STRING_SIZE - len(raw)))
        return raw

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return len(value) <= cls.STRING_SIZE
