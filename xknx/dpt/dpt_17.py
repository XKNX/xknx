"""Implementation of KNX DPT 17 Scene."""

from __future__ import annotations

from xknx.exceptions import ConversionError

from .dpt_5 import DPTValue1ByteUnsigned
from .payload import DPTArray, DPTBinary


class DPTSceneNumber(DPTValue1ByteUnsigned):
    """
    Abstraction for KNX 1 Octet Scene Number.

    DPT 17.001
    """

    dpt_main_number = 17
    dpt_sub_number = 1
    value_type = "scene_number"

    value_min = 1
    value_max = 64

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        value = cls.validate_payload(payload)[0] + 1

        if not cls._test_boundaries(value):
            raise ConversionError(
                f"Could not parse {cls.dpt_name()}", value=value, payload=payload
            )

        return value

    @classmethod
    def to_knx(cls, value: int | float) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value) - 1
            if not cls._test_boundaries(knx_value + 1):
                raise ValueError("Value out of range")
            return DPTArray(knx_value)
        except ValueError as err:
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}", value=value
            ) from err
