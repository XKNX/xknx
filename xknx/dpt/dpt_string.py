"""Implementation of 3.17 Datapoint Types String."""
from __future__ import annotations

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
    def from_knx(cls, raw: tuple[int, ...]) -> str:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)
        value = ""
        for byte in raw:
            if byte != 0x00:
                value += chr(byte)
        return value

    @classmethod
    def to_knx(cls, value: str) -> tuple[int, ...]:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = str(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            raw = [ord(character) for character in knx_value]
            raw.extend([0] * (cls.payload_length - len(raw)))
            # replace invalid characters with question marks
            # bytes(knx_value, 'ascii') would raise UnicodeEncodeError
            return tuple(map(lambda char: char if char <= 0xFF else ord("?"), raw))
        except ValueError:
            raise ConversionError(f"Could not serialize {cls.__name__}", value=value)

    @classmethod
    def _test_boundaries(cls, value: str) -> bool:
        """Test if value is within defined range for this object."""
        return len(value) <= cls.payload_length
