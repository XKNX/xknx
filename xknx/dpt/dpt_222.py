"""Implementation of KNX DPT 222 3x 2-octet float room temperature setpoints."""

from __future__ import annotations

from dataclasses import dataclass, field

from .dpt import DPTComplex
from .dpt_9 import DPTTemperature, DPTTemperatureDifference2Byte
from .dpt_275 import (
    _RANGE_TEMPERATURE,
    _RANGE_TEMPERATURE_DIFFERENCE,
    _pack_float_or_not_used,
    _RoomTemperatureSetpointSet,
    _unpack_float_or_not_used,
)
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class RoomTemperatureSetpoints3(_RoomTemperatureSetpointSet):
    """
    Representation of room temperature setpoints in °C.

    `comfort`, `standby`, `economy`: float -273..670433.28; None if invalid.
    """

    comfort: float | None = field(default=None, metadata=_RANGE_TEMPERATURE)
    standby: float | None = field(default=None, metadata=_RANGE_TEMPERATURE)
    economy: float | None = field(default=None, metadata=_RANGE_TEMPERATURE)


@dataclass(slots=True)
class RoomTemperatureSetpointShifts3(_RoomTemperatureSetpointSet):
    """
    Representation of room temperature setpoint shifts in K.

    `comfort`, `standby`, `economy`: float -671088.64..670433.28; None if invalid.
    """

    comfort: float | None = field(default=None, metadata=_RANGE_TEMPERATURE_DIFFERENCE)
    standby: float | None = field(default=None, metadata=_RANGE_TEMPERATURE_DIFFERENCE)
    economy: float | None = field(default=None, metadata=_RANGE_TEMPERATURE_DIFFERENCE)


class DPTRoomTemperatureSetpoints3(DPTComplex[RoomTemperatureSetpoints3]):
    """
    Abstraction for KNX 6 octet room temperature setpoints (DPT 222.100).

    DPT_TempRoomSetpSetF16[3] - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.23.1
    7FFFh denotes invalid data per field and maps to `None`.
    """

    data_type = RoomTemperatureSetpoints3
    payload_type = DPTArray
    payload_length = 6
    dpt_main_number = 222
    dpt_sub_number = 100
    value_type = "room_temperature_setpoints_3"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RoomTemperatureSetpoints3:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return RoomTemperatureSetpoints3(
            comfort=_unpack_float_or_not_used(raw[0:2], DPTTemperature),
            standby=_unpack_float_or_not_used(raw[2:4], DPTTemperature),
            economy=_unpack_float_or_not_used(raw[4:6], DPTTemperature),
        )

    @classmethod
    def _to_knx(cls, value: RoomTemperatureSetpoints3) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                *_pack_float_or_not_used(value.comfort, DPTTemperature),
                *_pack_float_or_not_used(value.standby, DPTTemperature),
                *_pack_float_or_not_used(value.economy, DPTTemperature),
            )
        )


class DPTRoomTemperatureSetpointShifts3(DPTComplex[RoomTemperatureSetpointShifts3]):
    """
    Abstraction for KNX 6 octet room temperature setpoint shifts (DPT 222.101).

    DPT_TempRoomSetpSetShiftF16[3] - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.23.2
    7FFFh denotes invalid data per field and maps to `None`.
    """

    data_type = RoomTemperatureSetpointShifts3
    payload_type = DPTArray
    payload_length = 6
    dpt_main_number = 222
    dpt_sub_number = 101
    value_type = "room_temperature_setpoint_shifts_3"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RoomTemperatureSetpointShifts3:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return RoomTemperatureSetpointShifts3(
            comfort=_unpack_float_or_not_used(raw[0:2], DPTTemperatureDifference2Byte),
            standby=_unpack_float_or_not_used(raw[2:4], DPTTemperatureDifference2Byte),
            economy=_unpack_float_or_not_used(raw[4:6], DPTTemperatureDifference2Byte),
        )

    @classmethod
    def _to_knx(cls, value: RoomTemperatureSetpointShifts3) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                *_pack_float_or_not_used(value.comfort, DPTTemperatureDifference2Byte),
                *_pack_float_or_not_used(value.standby, DPTTemperatureDifference2Byte),
                *_pack_float_or_not_used(value.economy, DPTTemperatureDifference2Byte),
            )
        )
