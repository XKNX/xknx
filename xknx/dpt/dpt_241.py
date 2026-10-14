"""Implementation of the KNX status shutter & sunblind actuator data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields as dataclass_fields
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .dpt_5 import DPTScaling
from .payload import DPTArray, DPTBinary

_RANGE_PERCENT = {"value_min": 0, "value_max": 100}

# Status bit fields in order of their bit number in the B16 attributes field.
# Bits 11 to 13 are reserved and shall be 0 - KNX v02.02.01 - Datapoint Types 03.07.02 - §7.4
_STATUS_BITS = (
    "upper_end_position",
    "lower_end_position",
    "lower_predefined_position",
    "target_position_reached",
    "target_height_position_restricted",
    "target_slats_position_restricted",
    "weather_alarm",
    "forced",
    "locked",
    "local_override",
    "failure",
)
_VALID_HEIGHT_POSITION_BIT = 14
_VALID_SLATS_POSITION_BIT = 15


@dataclass(slots=True)
class StatusSAB(DPTComplexData):
    """
    Representation of the status of a shutter & sunblind actuator.

    `height_position`: int 0..100 percent; None if invalid
    `slats_position`: int 0..100 percent; None if invalid
    `upper_end_position`: upper end position reached
    `lower_end_position`: lower end position reached
    `lower_predefined_position`: lower predefined position reached
    `target_position_reached`: target position reached; False while the drive is moving
    `target_height_position_restricted`: target height position can not be reached
    `target_slats_position_restricted`: target slats position can not be reached
    `weather_alarm`: at least one wind, rain or frost alarm input is in alarm
    `forced`: up/down position is forced
    `locked`: movement is locked
    `local_override`: actuator set value is locally overridden
    `failure`: general failure of the actuator or the drive
    """

    height_position: int | None = field(default=None, metadata=_RANGE_PERCENT)
    slats_position: int | None = field(default=None, metadata=_RANGE_PERCENT)
    upper_end_position: bool = False
    lower_end_position: bool = False
    lower_predefined_position: bool = False
    target_position_reached: bool = False
    target_height_position_restricted: bool = False
    target_slats_position_restricted: bool = False
    weather_alarm: bool = False
    forced: bool = False
    locked: bool = False
    local_override: bool = False
    failure: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> StatusSAB:
        """Init from a dictionary. Missing positions are invalid, missing bits False."""
        result: dict[str, Any] = {}
        try:
            for name in ("height_position", "slats_position"):
                value = data.get(name)
                if value is not None:
                    try:
                        value = int(value)
                    except (TypeError, ValueError) as err:
                        raise ValueError(f"Invalid value for {name}: {err}") from err
                result[name] = value
            for name in _STATUS_BITS:
                value = data.get(name, False)
                if not isinstance(value, bool):
                    raise ValueError(
                        f"Invalid value for {name}: {value!r} - bool expected"
                    )
                result[name] = value
        except AttributeError as err:
            raise ValueError(f"Invalid value for StatusSAB: {err}") from err
        return cls(**result)

    def as_dict(self) -> dict[str, int | bool | None]:
        """Create a JSON serializable dictionary."""
        return {
            field_.name: getattr(self, field_.name) for field_ in dataclass_fields(self)
        }


class DPTStatusSAB(DPTComplex[StatusSAB]):
    """Abstraction for KNX 4 octet status shutter & sunblind actuator (DPT 241.800)."""

    data_type = StatusSAB
    payload_type = DPTArray
    payload_length = 4
    dpt_main_number = 241
    dpt_sub_number = 800
    value_type = "status_sab"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> StatusSAB:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        attributes = raw[2] << 8 | raw[3]
        return StatusSAB(
            height_position=DPTScaling.from_knx(DPTArray(raw[0]))
            if attributes >> _VALID_HEIGHT_POSITION_BIT & 0b1
            else None,
            slats_position=DPTScaling.from_knx(DPTArray(raw[1]))
            if attributes >> _VALID_SLATS_POSITION_BIT & 0b1
            else None,
            **{
                name: bool(attributes >> bit & 0b1)
                for bit, name in enumerate(_STATUS_BITS)
            },
        )

    @classmethod
    def _to_knx(cls, value: StatusSAB) -> DPTArray:
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
        attributes = (
            value.height_position is not None
        ) << _VALID_HEIGHT_POSITION_BIT | (
            value.slats_position is not None
        ) << _VALID_SLATS_POSITION_BIT
        for bit, name in enumerate(_STATUS_BITS):
            flag = getattr(value, name)
            if not isinstance(flag, bool):
                raise ValueError(f"Invalid value for {name}: {flag!r} - bool expected")
            attributes |= flag << bit
        return DPTArray((height, slats, attributes >> 8, attributes & 0xFF))
