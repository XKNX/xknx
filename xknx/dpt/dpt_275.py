"""
Implementation of KNX room temperature setpoint set data point types.

DPT 275.100 and 275.101 are not part of the Datapoint Types document as of
KNX v02.02.01 - Datapoint Types 03.07.02; they are defined in
KNX v01.03.01 - HVAC S-Mode FBs 07.19.20 - §9.4 for the RTSM (Room
Temperature Setpoint Manager) and related HVAC function blocks.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Final

from .dpt import DPTComplex, DPTComplexData
from .dpt_9 import DPT2ByteFloat, DPTTemperature, DPTTemperatureDifference2Byte
from .payload import DPTArray, DPTBinary

# "For all fields ... only the value 7FFFh shall be used to denote invalid
# data." - KNX v01.03.01 - HVAC S-Mode FBs 07.19.20 - §9.4. This is the largest
# value DPT2ByteFloat can encode, repurposed as a per-field "not used" marker.
_NOT_USED = (0x7F, 0xFF)

# Derived from DPTTemperature/DPTTemperatureDifference2Byte themselves so the
# schema can never drift from the range those classes actually encode/accept.
_RANGE_TEMPERATURE: Final[dict[str, float]] = {
    "value_min": DPTTemperature.value_min,
    "value_max": DPTTemperature.value_max,
    "resolution": DPTTemperature.resolution,
}
_RANGE_TEMPERATURE_DIFFERENCE: Final[dict[str, float]] = {
    "value_min": DPTTemperatureDifference2Byte.value_min,
    "value_max": DPTTemperatureDifference2Byte.value_max,
    "resolution": DPTTemperatureDifference2Byte.resolution,
}


def _pack_float_or_not_used(
    value: float | None, dpt_class: type[DPT2ByteFloat]
) -> tuple[int, ...]:
    """Serialize a single field, encoding None as the KNX "not used" pattern."""
    if value is None:
        return _NOT_USED
    raw = dpt_class.to_knx(value).value
    if raw == _NOT_USED:
        # dpt_class.value_max rounds to the same bit pattern as _NOT_USED, so a
        # real value this close to it would silently read back as None instead.
        raise ValueError(f"{value} is too close to {dpt_class.value_max} to encode")
    return raw


def _unpack_float_or_not_used(
    raw: tuple[int, ...], dpt_class: type[DPT2ByteFloat]
) -> float | None:
    """Parse a single field, decoding the KNX "not used" pattern as None."""
    if raw == _NOT_USED:
        return None
    return dpt_class.from_knx(DPTArray(raw))


@dataclass(slots=True)
class RoomTemperatureSetpoints(DPTComplexData):
    """
    Representation of a room temperature setpoint set.

    `comfort`, `standby`, `economy`, `building_protection`: absolute setpoint
    in °C, -273..670760; None if not used.
    """

    comfort: float | None = field(default=None, metadata=_RANGE_TEMPERATURE)
    standby: float | None = field(default=None, metadata=_RANGE_TEMPERATURE)
    economy: float | None = field(default=None, metadata=_RANGE_TEMPERATURE)
    building_protection: float | None = field(default=None, metadata=_RANGE_TEMPERATURE)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RoomTemperatureSetpoints:
        """Init from a dictionary."""
        result = {}
        for field_name in ("comfort", "standby", "economy", "building_protection"):
            try:
                value = data.get(field_name)
                result[field_name] = float(value) if value is not None else None
            except (TypeError, ValueError) as err:
                raise ValueError(f"Invalid value for {field_name}: {err}") from err
        return cls(**result)

    def as_dict(self) -> dict[str, float | None]:
        """Create a JSON serializable dictionary."""
        return {
            "comfort": self.comfort,
            "standby": self.standby,
            "economy": self.economy,
            "building_protection": self.building_protection,
        }


@dataclass(slots=True)
class RoomTemperatureSetpointsShift(DPTComplexData):
    """
    Representation of a room temperature setpoint shift set.

    `comfort`, `standby`, `economy`, `building_protection`: setpoint shift
    (delta value) in K, -670760..670760; None if not used.
    """

    comfort: float | None = field(default=None, metadata=_RANGE_TEMPERATURE_DIFFERENCE)
    standby: float | None = field(default=None, metadata=_RANGE_TEMPERATURE_DIFFERENCE)
    economy: float | None = field(default=None, metadata=_RANGE_TEMPERATURE_DIFFERENCE)
    building_protection: float | None = field(
        default=None, metadata=_RANGE_TEMPERATURE_DIFFERENCE
    )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RoomTemperatureSetpointsShift:
        """Init from a dictionary."""
        result = {}
        for field_name in ("comfort", "standby", "economy", "building_protection"):
            try:
                value = data.get(field_name)
                result[field_name] = float(value) if value is not None else None
            except (TypeError, ValueError) as err:
                raise ValueError(f"Invalid value for {field_name}: {err}") from err
        return cls(**result)

    def as_dict(self) -> dict[str, float | None]:
        """Create a JSON serializable dictionary."""
        return {
            "comfort": self.comfort,
            "standby": self.standby,
            "economy": self.economy,
            "building_protection": self.building_protection,
        }


class DPTRoomTemperatureSetpointSet(DPTComplex[RoomTemperatureSetpoints]):
    """
    Abstraction for KNX room temperature setpoint set (DPT 275.100).

    KNX v01.03.01 - HVAC S-Mode FBs 07.19.20 - §9.4.1
    """

    data_type = RoomTemperatureSetpoints
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 275
    dpt_sub_number = 100
    value_type = "room_temperature_setpoint_set"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RoomTemperatureSetpoints:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return RoomTemperatureSetpoints(
            comfort=_unpack_float_or_not_used(raw[0:2], DPTTemperature),
            standby=_unpack_float_or_not_used(raw[2:4], DPTTemperature),
            economy=_unpack_float_or_not_used(raw[4:6], DPTTemperature),
            building_protection=_unpack_float_or_not_used(raw[6:8], DPTTemperature),
        )

    @classmethod
    def _to_knx(cls, value: RoomTemperatureSetpoints) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                *_pack_float_or_not_used(value.comfort, DPTTemperature),
                *_pack_float_or_not_used(value.standby, DPTTemperature),
                *_pack_float_or_not_used(value.economy, DPTTemperature),
                *_pack_float_or_not_used(value.building_protection, DPTTemperature),
            )
        )


class DPTRoomTemperatureSetpointSetShift(DPTComplex[RoomTemperatureSetpointsShift]):
    """
    Abstraction for KNX room temperature setpoint set shift (DPT 275.101).

    KNX v01.03.01 - HVAC S-Mode FBs 07.19.20 - §9.4.2
    """

    data_type = RoomTemperatureSetpointsShift
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 275
    dpt_sub_number = 101
    value_type = "room_temperature_setpoint_set_shift"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RoomTemperatureSetpointsShift:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return RoomTemperatureSetpointsShift(
            comfort=_unpack_float_or_not_used(raw[0:2], DPTTemperatureDifference2Byte),
            standby=_unpack_float_or_not_used(raw[2:4], DPTTemperatureDifference2Byte),
            economy=_unpack_float_or_not_used(raw[4:6], DPTTemperatureDifference2Byte),
            building_protection=_unpack_float_or_not_used(
                raw[6:8], DPTTemperatureDifference2Byte
            ),
        )

    @classmethod
    def _to_knx(cls, value: RoomTemperatureSetpointsShift) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                *_pack_float_or_not_used(value.comfort, DPTTemperatureDifference2Byte),
                *_pack_float_or_not_used(value.standby, DPTTemperatureDifference2Byte),
                *_pack_float_or_not_used(value.economy, DPTTemperatureDifference2Byte),
                *_pack_float_or_not_used(
                    value.building_protection, DPTTemperatureDifference2Byte
                ),
            )
        )
