"""Implementation of scaled KNX DPT_1_Ucount Values."""
from __future__ import annotations

from xknx.exceptions import ConversionError

from .dpt import DPTNumeric


class DPTScaling(DPTNumeric):
    """
    Abstraction for KNX 1 Octet Percent.

    DPT 5.001
    """

    dpt_main_number = 5
    dpt_sub_number = 1
    value_type = "percent"
    unit = "%"
    payload_length = 1

    value_min = 0
    value_max = 100
    resolution = 1

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)

        knx_value = raw[0]
        delta = cls.value_max - cls.value_min
        value = round((knx_value / 255) * delta) + cls.value_min

        if not cls._test_boundaries(value):
            raise ConversionError(
                f"Could not parse {cls.__name__}", value=value, raw=raw
            )

        return value

    @classmethod
    def to_knx(cls, value: float) -> tuple[int]:
        """Serialize to KNX/IP raw data."""
        try:
            percent_value = float(value)
            if not cls._test_boundaries(percent_value):
                raise ValueError
            delta = cls.value_max - cls.value_min
            knx_value = round((percent_value - cls.value_min) / delta * 255)

            return (knx_value,)
        except ValueError:
            raise ConversionError(f"Could not serialize {cls.__name__}", value=value)

    @classmethod
    def _test_boundaries(cls, value: float) -> bool:
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTAngle(DPTScaling):
    """
    Abstraction for KNX 1 Octet Angle.

    DPT 5.003
    """

    dpt_main_number = 5
    dpt_sub_number = 3
    value_type = "angle"
    unit = "°"

    value_min = 0
    value_max = 360
    resolution = 1
