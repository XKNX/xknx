"""
Implementation of KNX DPT 206 mode and time delay data point types.

KNX v02.02.01 - Datapoint Types 03.07.02 - §4.12
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Final, TypeVar

from ..exceptions import ConversionError
from .dpt import DPTComplex, DPTComplexData, DPTComplexFieldSchema, DPTEnumData
from .dpt_7 import DPTTimePeriodMin
from .dpt_20 import BuildingMode, DHWMode, HVACOperationMode, OccupancyMode
from .payload import DPTArray, DPTBinary

RANGE_DELAY_TIME: Final[dict[str, int]] = {"value_min": 1, "value_max": 65_535}

_EnumT = TypeVar("_EnumT", bound=DPTEnumData)


def _check_mapping(data: Any, name: str) -> Mapping[str, Any]:
    """Raise ValueError if `data` is not a mapping."""
    if not isinstance(data, Mapping):
        raise ValueError(f"Invalid value for {name}: {data!r}")
    return data


def _delay_time_from_dict(data: Mapping[str, Any]) -> int | None:
    """Parse the optional `delay_time` of a dictionary."""
    delay_time = data.get("delay_time")
    if delay_time is None:
        return None
    try:
        return int(delay_time)
    except (TypeError, ValueError) as err:
        raise ValueError(f"Invalid value for delay_time: {err}") from err


def _mode_from_dict(data: Mapping[str, Any], enum_type: type[_EnumT]) -> _EnumT | None:
    """Parse the `mode` of a dictionary; None if it is missing."""
    mode = data.get("mode")
    if mode is None:
        return None
    return enum_type.parse(mode)


def _without_auto_option(
    schema: list[DPTComplexFieldSchema],
) -> list[DPTComplexFieldSchema]:
    """Remove the `auto` option - its raw value 0 means undefined in DPT 206."""
    for entry in schema:
        if entry["name"] == "mode":
            entry["options"] = [
                option for option in entry["options"] if option != "auto"
            ]
    return schema


def _parse(
    dpt: type[DPTComplex[Any]], payload: DPTArray | DPTBinary
) -> tuple[int | None, int]:
    """Return the delay time (None if 0) and the raw mode value."""
    raw = dpt.validate_payload(payload)
    delay_time = DPTTimePeriodMin.from_knx(DPTArray(raw[:2]))
    return (delay_time or None), raw[2]


def _to_raw(delay_time: int | None, mode: int) -> DPTArray:
    """Serialize a delay time (None as 0) and a raw mode value."""
    if delay_time is None:
        return DPTArray((0x00, 0x00, mode))
    if not 1 <= delay_time <= 65_535:
        raise ConversionError(f"Delay time out of range 1..65535: {delay_time}")
    return DPTArray((*DPTTimePeriodMin.to_knx(delay_time).value, mode))


@dataclass(slots=True)
class HVACModeNext(DPTComplexData):
    """
    Value of DPT 206.100 DPT_HVACModeNext: an HVAC mode and its time delay.

    `mode`: HVACOperationMode (DPT 20.102; AUTO is not supported); None if undefined
    `delay_time`: int 1..65535 minutes; None if undefined
    """

    mode: HVACOperationMode | None = None
    delay_time: int | None = field(default=None, metadata=RANGE_DELAY_TIME)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> HVACModeNext:
        """Init from a dictionary."""
        data = _check_mapping(data, cls.__name__)
        return cls(
            mode=_mode_from_dict(data, HVACOperationMode),
            delay_time=_delay_time_from_dict(data),
        )

    def as_dict(self) -> dict[str, str | int | None]:
        """Create a JSON serializable dictionary."""
        return {
            "mode": self.mode.name.lower() if self.mode is not None else None,
            "delay_time": self.delay_time,
        }

    @classmethod
    def get_dict_schema(cls) -> list[DPTComplexFieldSchema]:
        """Return schema for the dict used in as_dict() / from_dict()."""
        # zero-argument super() fails in slots dataclasses on Python 3.11
        return _without_auto_option(
            super(HVACModeNext, cls).get_dict_schema()  # pylint: disable=super-with-arguments
        )


class DPTHVACModeNext(DPTComplex[HVACModeNext]):
    """
    Abstraction for KNX 3 octet HVAC Mode & Time delay (DPT 206.100 DPT_HVACModeNext).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.12.1
    """

    data_type = HVACModeNext
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 206
    dpt_sub_number = 100
    value_type = "hvac_mode_next"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> HVACModeNext:
        """Parse/deserialize from KNX/IP raw data."""
        delay_time, mode = _parse(cls, payload)
        if mode > HVACOperationMode.BUILDING_PROTECTION.value:
            raise ConversionError(
                f"Payload not supported for {cls.dpt_name()}", raw=payload
            )
        return HVACModeNext(
            mode=HVACOperationMode(mode) if mode else None,
            delay_time=delay_time,
        )

    @classmethod
    def _to_knx(cls, value: HVACModeNext) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if value.mode is None:
            return _to_raw(value.delay_time, 0)
        mode = HVACOperationMode(value.mode)
        if mode is HVACOperationMode.AUTO:
            raise ConversionError("HVAC mode AUTO is not supported")
        return _to_raw(value.delay_time, mode.value)


@dataclass(slots=True)
class DHWModeNext(DPTComplexData):
    """
    Value of DPT 206.102 DPT_DHWModeNext: a domestic hot water mode and its time delay.

    `mode`: DHWMode (DPT 20.103; AUTO is not supported); None if undefined
    `delay_time`: int 1..65535 minutes; None if undefined
    """

    mode: DHWMode | None = None
    delay_time: int | None = field(default=None, metadata=RANGE_DELAY_TIME)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DHWModeNext:
        """Init from a dictionary."""
        data = _check_mapping(data, cls.__name__)
        return cls(
            mode=_mode_from_dict(data, DHWMode),
            delay_time=_delay_time_from_dict(data),
        )

    def as_dict(self) -> dict[str, str | int | None]:
        """Create a JSON serializable dictionary."""
        return {
            "mode": self.mode.name.lower() if self.mode is not None else None,
            "delay_time": self.delay_time,
        }

    @classmethod
    def get_dict_schema(cls) -> list[DPTComplexFieldSchema]:
        """Return schema for the dict used in as_dict() / from_dict()."""
        # zero-argument super() fails in slots dataclasses on Python 3.11
        return _without_auto_option(
            super(DHWModeNext, cls).get_dict_schema()  # pylint: disable=super-with-arguments
        )


class DPTDHWModeNext(DPTComplex[DHWModeNext]):
    """
    Abstraction for KNX 3 octet DHW Mode & Time delay (DPT 206.102 DPT_DHWModeNext).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.12.2
    """

    data_type = DHWModeNext
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 206
    dpt_sub_number = 102
    value_type = "dhw_mode_next"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> DHWModeNext:
        """Parse/deserialize from KNX/IP raw data."""
        delay_time, mode = _parse(cls, payload)
        if mode > DHWMode.OFF_FROST_PROTECT.value:
            raise ConversionError(
                f"Payload not supported for {cls.dpt_name()}", raw=payload
            )
        return DHWModeNext(
            mode=DHWMode(mode) if mode else None,
            delay_time=delay_time,
        )

    @classmethod
    def _to_knx(cls, value: DHWModeNext) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if value.mode is None:
            return _to_raw(value.delay_time, 0)
        mode = DHWMode(value.mode)
        if mode is DHWMode.AUTO:
            raise ConversionError("DHW mode AUTO is not supported")
        return _to_raw(value.delay_time, mode.value)


@dataclass(slots=True)
class OccupancyModeNext(DPTComplexData):
    """
    Value of DPT 206.104 DPT_OccModeNext: an occupancy mode and its time delay.

    `mode`: OccupancyMode (DPT 20.003)
    `delay_time`: int 1..65535 minutes; None if the next mode is not available
    """

    mode: OccupancyMode
    delay_time: int | None = field(default=None, metadata=RANGE_DELAY_TIME)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> OccupancyModeNext:
        """Init from a dictionary."""
        data = _check_mapping(data, cls.__name__)
        mode = _mode_from_dict(data, OccupancyMode)
        if mode is None:
            raise ValueError("Missing required key: 'mode'")
        return cls(mode=mode, delay_time=_delay_time_from_dict(data))

    def as_dict(self) -> dict[str, str | int | None]:
        """Create a JSON serializable dictionary."""
        return {
            "mode": self.mode.name.lower(),
            "delay_time": self.delay_time,
        }


class DPTOccModeNext(DPTComplex[OccupancyModeNext]):
    """
    Abstraction for KNX 3 octet Occupancy Mode & Time delay (DPT 206.104 DPT_OccModeNext).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.12.3
    """

    data_type = OccupancyModeNext
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 206
    dpt_sub_number = 104
    value_type = "occupancy_mode_next"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> OccupancyModeNext:
        """Parse/deserialize from KNX/IP raw data."""
        delay_time, mode = _parse(cls, payload)
        try:
            return OccupancyModeNext(
                mode=OccupancyMode(mode),
                delay_time=delay_time,
            )
        except ValueError:
            raise ConversionError(
                f"Payload not supported for {cls.dpt_name()}", raw=payload
            ) from None

    @classmethod
    def _to_knx(cls, value: OccupancyModeNext) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _to_raw(value.delay_time, OccupancyMode(value.mode).value)


@dataclass(slots=True)
class BuildingModeNext(DPTComplexData):
    """
    Value of DPT 206.105 DPT_BuildingModeNext: a building mode and its time delay.

    `mode`: BuildingMode (DPT 20.002)
    `delay_time`: int 1..65535 minutes; None if the next mode is not available
    """

    mode: BuildingMode
    delay_time: int | None = field(default=None, metadata=RANGE_DELAY_TIME)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BuildingModeNext:
        """Init from a dictionary."""
        data = _check_mapping(data, cls.__name__)
        mode = _mode_from_dict(data, BuildingMode)
        if mode is None:
            raise ValueError("Missing required key: 'mode'")
        return cls(mode=mode, delay_time=_delay_time_from_dict(data))

    def as_dict(self) -> dict[str, str | int | None]:
        """Create a JSON serializable dictionary."""
        return {
            "mode": self.mode.name.lower(),
            "delay_time": self.delay_time,
        }


class DPTBuildingModeNext(DPTComplex[BuildingModeNext]):
    """
    Abstraction for KNX 3 octet Building Mode & Time delay (DPT 206.105 DPT_BuildingModeNext).

    The format line of the spec says "N8U16", its octet diagram and field table
    U16N8 (delay time first), which is implemented.
    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.12.4
    """

    data_type = BuildingModeNext
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 206
    dpt_sub_number = 105
    value_type = "building_mode_next"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> BuildingModeNext:
        """Parse/deserialize from KNX/IP raw data."""
        delay_time, mode = _parse(cls, payload)
        try:
            return BuildingModeNext(
                mode=BuildingMode(mode),
                delay_time=delay_time,
            )
        except ValueError:
            raise ConversionError(
                f"Payload not supported for {cls.dpt_name()}", raw=payload
            ) from None

    @classmethod
    def _to_knx(cls, value: BuildingModeNext) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _to_raw(value.delay_time, BuildingMode(value.mode).value)
