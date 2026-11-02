"""Implementation of the KNX 240 data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .dpt_5 import DPTScaling
from .payload import DPTArray, DPTBinary

_RANGE_PERCENT = {"value_min": 0, "value_max": 100}


@dataclass(slots=True)
class CombinedPosition(DPTComplexData):
    """
    Representation of a combined height and slats position of shutters and blinds.

    `height_position`: int 0..100 %; None if invalid.
    `slats_position`: int 0..100 %; None if invalid.
    """

    height_position: int | None = field(default=None, metadata=_RANGE_PERCENT)
    slats_position: int | None = field(default=None, metadata=_RANGE_PERCENT)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CombinedPosition:
        """Init from a dictionary."""
        result: dict[str, int | None] = {}
        for key in ("height_position", "slats_position"):
            try:
                value = data.get(key)
                result[key] = int(value) if value is not None else None
            except (AttributeError, TypeError, ValueError) as err:
                raise ValueError(f"Invalid value for {key}: {err}") from err
        return cls(**result)

    def as_dict(self) -> dict[str, int | None]:
        """Create a JSON serializable dictionary."""
        return {
            "height_position": self.height_position,
            "slats_position": self.slats_position,
        }


class DPTCombinedPosition(DPTComplex[CombinedPosition]):
    """
    Abstraction for KNX 3 octet combined position (DPT 240.800).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §7.2.1
    The format line there says 2 octets, but the U8U8B8 layout defines 3.
    """

    data_type = CombinedPosition
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 240
    dpt_sub_number = 800
    value_type = "combined_position"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> CombinedPosition:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        # reserved bits 2..7 of the attributes octet are ignored
        height_valid = raw[2] & 0b1
        slats_valid = raw[2] >> 1 & 0b1
        return CombinedPosition(
            height_position=(
                DPTScaling.from_knx(DPTArray((raw[0],))) if height_valid else None
            ),
            slats_position=(
                DPTScaling.from_knx(DPTArray((raw[1],))) if slats_valid else None
            ),
        )

    @classmethod
    def _to_knx(cls, value: CombinedPosition) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        height = (
            DPTScaling.to_knx(value.height_position).value[0]
            if value.height_position is not None
            else 0
        )
        slats = (
            DPTScaling.to_knx(value.slats_position).value[0]
            if value.slats_position is not None
            else 0
        )
        return DPTArray(
            (
                height,
                slats,
                (value.slats_position is not None) << 1
                | (value.height_position is not None),
            )
        )
