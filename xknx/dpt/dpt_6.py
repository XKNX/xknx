"""Implementation of Basic KNX 1-Byte signed integer values."""

from __future__ import annotations

from xknx.exceptions import ConversionError

from .dpt import DPTNumeric
from .payload import DPTArray, DPTBinary


class DPTSignedRelativeValue(DPTNumeric):
    """
    Abstraction for KNX 1 Byte "1-octet Signed Relative Value".

    DPT 6.***
    """

    dpt_main_number = 6
    dpt_sub_number: int | None = None
    value_type = "1byte_signed"
    payload_length = 1

    value_min = -128
    value_max = 127
    resolution = 1

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        if raw[0] > cls.value_max:
            return raw[0] - 0x100
        return raw[0]

    @classmethod
    def to_knx(cls, value: int | float) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError("Value out of range")
            if knx_value < 0:
                knx_value += 0x100
            return DPTArray(knx_value & 0xFF)
        except ValueError as err:
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}", value=value
            ) from err

    @classmethod
    def _test_boundaries(cls, value: int) -> bool:
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTPercentV8(DPTSignedRelativeValue):
    """
    Abstraction for KNX DPT_Percent_V8.

    DPT 6.001
    """

    dpt_main_number = 6
    dpt_sub_number = 1
    value_type = "percentV8"
    unit = "%"


class DPTValue1Count(DPTSignedRelativeValue):
    """
    Abstraction for KNX DPT_Value_1_Count.

    DPT 6.010
    """

    dpt_main_number = 6
    dpt_sub_number = 10
    value_type = "counter_pulses"
    unit = "counter pulses"
