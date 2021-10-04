"""Implementation of Basic KNX 1-Byte signed integer values."""
from __future__ import annotations

from xknx.exceptions import ConversionError

from .dpt import DPTNumeric


class DPTSignedRelativeValue(DPTNumeric):
    """
    Abstraction for KNX 1 Byte "1-octet Signed Relative Value".

    DPT 6.***
    """

    dpt_main_number = 6
    dpt_sub_number: int | None = None
    value_type = "1byte_signed"
    unit = ""
    payload_length = 1

    value_min = -128
    value_max = 127
    resolution = 1

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)
        if raw[0] > cls.value_max:
            return raw[0] - 0x100
        return raw[0]

    @classmethod
    def to_knx(cls, value: int | float) -> tuple[int]:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            if knx_value < 0:
                knx_value += 0x100
            return (knx_value & 0xFF,)
        except ValueError:
            raise ConversionError(f"Could not serialize {cls.__name__}", value=value)

    @classmethod
    def _test_boundaries(cls, value: int) -> bool:
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTPercentV8(DPTSignedRelativeValue):
    """Abstraction for KNX DPT_Percent_V8.

    DPT 6.001
    """

    dpt_main_number = 6
    dpt_sub_number = 1
    value_type = "percentV8"
    unit = "%"


class DPTValue1Count(DPTSignedRelativeValue):
    """Abstraction for KNX DPT_Value_1_Count.

    DPT 6.010
    """

    dpt_main_number = 6
    dpt_sub_number = 10
    value_type = "counter_pulses"
    unit = "counter pulses"
