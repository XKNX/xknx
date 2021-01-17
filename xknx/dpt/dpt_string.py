"""Implementation of 3.17 Datapoint Types String."""
from typing import Tuple

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTString(DPTBase):
    """
    Abstraction for KNX 14 Octet ASCII String.

    DPT 16.000
    """

    payload_length = 14
    dpt_main_number = 16
    dpt_sub_number = 0
    value_type = "string"
    unit = ""

    @classmethod
    def from_knx(cls, raw: Tuple[int, ...]) -> str:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)
        value = ""
        for byte in raw:
            if byte != 0x00:
                value += chr(byte)
        return value

    @classmethod
    def to_knx(cls, value: str) -> Tuple[int, ...]:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = str(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            raw = []
            for character in knx_value:
                raw.append(ord(character))
            raw.extend([0] * (cls.payload_length - len(raw)))
            return tuple(raw)
        except ValueError:
            raise ConversionError("Could not serialize %s" % cls.__name__, value=value)

    @classmethod
    def _test_boundaries(cls, value: str) -> bool:
        """Test if value is within defined range for this object."""
        return len(value) <= cls.payload_length
