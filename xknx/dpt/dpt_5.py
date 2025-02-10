"""Implementation of Basic KNX DPT_1_Ucount Values."""

from __future__ import annotations

from xknx.exceptions import ConversionError

from .dpt import DPTNumeric
from .payload import DPTArray, DPTBinary


class DPTValue1ByteUnsigned(DPTNumeric):
    """
    Abstraction for KNX 1 Octet.

    DPT 5.***
    """

    dpt_main_number = 5
    dpt_sub_number: int | None = None
    value_type = "1byte_unsigned"
    payload_length = 1

    value_min = 0
    value_max = 255
    resolution = 1

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        value = cls.validate_payload(payload)[0]

        if not cls._test_boundaries(value):
            raise ConversionError(
                f"Could not parse {cls.dpt_name()}", value=value, payload=payload
            )

        return value

    @classmethod
    def to_knx(cls, value: int | float) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError(f"Value out of range {cls.value_min}..{cls.value_max}")
            return DPTArray(knx_value)
        except ValueError as err:
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}", value=value
            ) from err

    @classmethod
    def _test_boundaries(cls, value: int) -> bool:
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


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
    def from_knx(cls, payload: DPTArray | DPTBinary) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        knx_value = cls.validate_payload(payload)[0]
        delta = cls.value_max - cls.value_min
        value = round((knx_value / 255) * delta) + cls.value_min

        if not cls._test_boundaries(value):
            raise ConversionError(
                f"Could not parse {cls.dpt_name()}", value=value, payload=payload
            )
        return value

    @classmethod
    def to_knx(cls, value: float) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            percent_value = float(value)
            if not cls._test_boundaries(percent_value):
                raise ValueError("Value out of range")
            delta = cls.value_max - cls.value_min
            knx_value = round((percent_value - cls.value_min) / delta * 255)

            return DPTArray(knx_value)
        except ValueError as err:
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}", value=value
            ) from err

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


class DPTPercentU8(DPTValue1ByteUnsigned):
    """
    Abstraction for KNX 1 Octet Percent.

    DPT 5.004
    """

    dpt_main_number = 5
    dpt_sub_number = 4
    value_type = "percentU8"
    unit = "%"
    resolution = 1


class DPTDecimalFactor(DPTValue1ByteUnsigned):
    """
    Abstraction for KNX 1 Octet Percent.

    DPT 5.005
    """

    dpt_main_number = 5
    dpt_sub_number = 5
    value_type = "decimal_factor"


class DPTTariff(DPTValue1ByteUnsigned):
    """
    Abstraction for KNX 1 Octet tariff information.

    DPT 5.006
    """

    dpt_main_number = 5
    dpt_sub_number = 6
    value_type = "tariff"
    value_max = 254


class DPTValue1Ucount(DPTValue1ByteUnsigned):
    """
    Abstraction for KNX 1 Octet counter pulses.

    DPT 5.010
    """

    dpt_main_number = 5
    dpt_sub_number = 10
    value_type = "pulse"
    unit = "counter pulses"
