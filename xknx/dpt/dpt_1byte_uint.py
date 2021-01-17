"""Implementation of Basic KNX DPT_1_Ucount Values."""
from typing import Optional, Tuple

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTValue1ByteUnsigned(DPTBase):
    """
    Abstraction for KNX 1 Octet.

    DPT 5.***
    """

    value_min = 0
    value_max = 255
    dpt_main_number = 5
    dpt_sub_number: Optional[int] = None
    value_type = "1byte_unsigned"
    unit = ""
    resolution = 1
    payload_length = 1

    @classmethod
    def from_knx(cls, raw: Tuple[int, ...]) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)

        value = raw[0]

        if not cls._test_boundaries(value):
            raise ConversionError(
                "Could not parse %s" % cls.__name__, value=value, raw=raw
            )

        return value

    @classmethod
    def to_knx(cls, value: int) -> Tuple[int]:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            return (knx_value,)
        except ValueError:
            raise ConversionError("Could not serialize %s" % cls.__name__, value=value)

    @classmethod
    def _test_boundaries(cls, value: int) -> bool:
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTPercentU8(DPTValue1ByteUnsigned):
    """
    Abstraction for KNX 1 Octet Percent.

    DPT 5.004
    """

    dpt_main_number = 5
    dpt_sub_number = 4
    value_type = "percentU8"
    unit = "%"


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


class DPTSceneNumber(DPTValue1ByteUnsigned):
    """
    Abstraction for KNX 1 Octet Scene Number.

    DPT 17.001
    """

    value_min = 1
    value_max = 64
    dpt_main_number = 17
    dpt_sub_number = 1
    value_type = "scene_number"
    unit = ""

    @classmethod
    def from_knx(cls, raw: Tuple[int, ...]) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)

        value = raw[0] + 1

        if not cls._test_boundaries(value):
            raise ConversionError(
                "Could not parse %s" % cls.__name__, value=value, raw=raw
            )

        return value

    @classmethod
    def to_knx(cls, value: int) -> Tuple[int]:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value) - 1
            if not cls._test_boundaries(knx_value + 1):
                raise ValueError
            return (knx_value,)
        except ValueError:
            raise ConversionError("Could not serialize %s" % cls.__name__, value=value)
