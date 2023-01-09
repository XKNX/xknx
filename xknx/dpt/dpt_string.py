"""Implementation of 3.17 Datapoint Types String."""
from __future__ import annotations

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTString(DPTBase):
    """
    Abstraction for KNX 14 Octet ASCII string.

    DPT 16.000
    """

    payload_length = 14
    dpt_main_number = 16
    dpt_sub_number = 0
    value_type = "string"
    unit = None

    _encoding = "ascii"

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> str:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)
        return bytes(byte for byte in raw if byte != 0x00).decode(
            cls._encoding, errors="replace"
        )

    @classmethod
    def to_knx(cls, value: str) -> tuple[int, ...]:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = str(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
        except ValueError:
            raise ConversionError(f"Could not serialize {cls.__name__}", value=value)
        # replace invalid characters with question marks
        raw_bytes = knx_value.encode(cls._encoding, errors="replace")
        padding = bytes(cls.payload_length - len(raw_bytes))
        return tuple(raw_bytes + padding)

    @classmethod
    def _test_boundaries(cls, value: str) -> bool:
        """Test if value is within defined range for this object."""
        return len(value) <= cls.payload_length


class DPTLatin1(DPTString):
    """
    Abstraction for KNX 14 Octet Latin-1 (ISO 8859-1) string.

    DPT 16.001
    """

    dpt_main_number = 16
    dpt_sub_number = 1
    value_type = "latin_1"
    _encoding = "latin_1"
