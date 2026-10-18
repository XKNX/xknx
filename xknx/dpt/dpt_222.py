"""Implementation of KNX DPT 222 3x 2-octet float room temperature setpoints."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields as dataclass_fields
from typing import Any, Self

from .dpt import DPTComplex, DPTComplexData
from .dpt_9 import (
    DPT_9_INVALID_DATA,
    DPT2ByteFloat,
    DPTTemperature,
    DPTTemperatureDifference2Byte,
)
from .payload import DPTArray, DPTBinary

_RANGE_SETPOINT = {
    "value_min": DPTTemperature.value_min,
    "value_max": DPTTemperature.value_max,
    "resolution": DPTTemperature.resolution,
}
_RANGE_SETPOINT_SHIFT = {
    "value_min": DPTTemperatureDifference2Byte.value_min,
    "value_max": DPTTemperatureDifference2Byte.value_max,
    "resolution": DPTTemperatureDifference2Byte.resolution,
}


class _ComfortStandbyEconomy(DPTComplexData):
    """Base for the comfort / standby / economy float triples; `None` is invalid data."""

    __slots__ = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Init from a dictionary."""
        result: dict[str, float | None] = {}
        for field_ in dataclass_fields(cls):
            value = data.get(field_.name)
            if value is not None:
                try:
                    value = float(value)
                except (TypeError, ValueError) as err:
                    raise ValueError(f"Invalid value for {field_.name}: {err}") from err
            result[field_.name] = value
        return cls(**result)

    def as_dict(self) -> dict[str, float | None]:
        """Create a JSON serializable dictionary."""
        return {
            field_.name: getattr(self, field_.name) for field_ in dataclass_fields(self)
        }


def _decode(
    raw: tuple[int, ...], transcoder: type[DPT2ByteFloat]
) -> tuple[float | None, float | None, float | None]:
    """Decode three 2-octet floats; 7FFFh decodes to `None`."""
    comfort, standby, economy = (
        None
        if raw[i : i + 2] == DPT_9_INVALID_DATA
        else transcoder.from_knx(DPTArray(raw[i : i + 2]))
        for i in (0, 2, 4)
    )
    return comfort, standby, economy


def _encode(
    values: tuple[float | None, float | None, float | None],
    transcoder: type[DPT2ByteFloat],
) -> DPTArray:
    """Encode three 2-octet floats; `None` encodes to 7FFFh."""
    raw: list[int] = []
    for value in values:
        raw.extend(DPT_9_INVALID_DATA if value is None else transcoder.to_knx(value).value)
    return DPTArray(raw)


@dataclass(slots=True)
class RoomTemperatureSetpoints(_ComfortStandbyEconomy):
    """
    Representation of room temperature setpoints in °C.

    `comfort`, `standby`, `economy`: float -273..670433.28; None if invalid.
    """

    comfort: float | None = field(default=None, metadata=_RANGE_SETPOINT)
    standby: float | None = field(default=None, metadata=_RANGE_SETPOINT)
    economy: float | None = field(default=None, metadata=_RANGE_SETPOINT)


@dataclass(slots=True)
class RoomTemperatureSetpointShifts(_ComfortStandbyEconomy):
    """
    Representation of room temperature setpoint shifts in K.

    `comfort`, `standby`, `economy`: float -671088.64..670433.28; None if invalid.
    """

    comfort: float | None = field(default=None, metadata=_RANGE_SETPOINT_SHIFT)
    standby: float | None = field(default=None, metadata=_RANGE_SETPOINT_SHIFT)
    economy: float | None = field(default=None, metadata=_RANGE_SETPOINT_SHIFT)


class DPTRoomTemperatureSetpoints(DPTComplex[RoomTemperatureSetpoints]):
    """
    Abstraction for KNX 6 octet room temperature setpoints (DPT 222.100).

    DPT_TempRoomSetpSetF16[3] - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.23.1
    """

    data_type = RoomTemperatureSetpoints
    payload_type = DPTArray
    payload_length = 6
    dpt_main_number = 222
    dpt_sub_number = 100
    value_type = "room_temperature_setpoints"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RoomTemperatureSetpoints:
        """Parse/deserialize from KNX/IP raw data."""
        comfort, standby, economy = _decode(
            cls.validate_payload(payload), DPTTemperature
        )
        return RoomTemperatureSetpoints(
            comfort=comfort, standby=standby, economy=economy
        )

    @classmethod
    def _to_knx(cls, value: RoomTemperatureSetpoints) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _encode((value.comfort, value.standby, value.economy), DPTTemperature)


class DPTRoomTemperatureSetpointShifts(DPTComplex[RoomTemperatureSetpointShifts]):
    """
    Abstraction for KNX 6 octet room temperature setpoint shifts (DPT 222.101).

    DPT_TempRoomSetpSetShiftF16[3] - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.23.2
    """

    data_type = RoomTemperatureSetpointShifts
    payload_type = DPTArray
    payload_length = 6
    dpt_main_number = 222
    dpt_sub_number = 101
    value_type = "room_temperature_setpoint_shifts"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RoomTemperatureSetpointShifts:
        """Parse/deserialize from KNX/IP raw data."""
        comfort, standby, economy = _decode(
            cls.validate_payload(payload), DPTTemperatureDifference2Byte
        )
        return RoomTemperatureSetpointShifts(
            comfort=comfort, standby=standby, economy=economy
        )

    @classmethod
    def _to_knx(cls, value: RoomTemperatureSetpointShifts) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _encode(
            (value.comfort, value.standby, value.economy),
            DPTTemperatureDifference2Byte,
        )
