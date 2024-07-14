"""Implementation of different KNX DPT HVAC Operation modes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from .dpt import DPTComplex, DPTComplexData, DPTEnum
from .payload import DPTArray, DPTBinary


# ruff: noqa: RUF012  # Mutable class attributes should be annotated with `typing.ClassVar`
class HVACOperationMode(Enum):
    """Enum for the different KNX HVAC operation modes."""

    AUTO = 0
    COMFORT = 1
    STANDBY = 2
    ECONOMY = 3
    BUILDING_PROTECTION = 4


class DPTHVACMode(DPTEnum[HVACOperationMode]):
    """
    Abstraction for KNX HVAC mode.

    DPT 20.102
    """

    dpt_main_number = 20
    dpt_sub_number = 102
    value_type = "hvac_mode"
    data_type = HVACOperationMode

    @classmethod
    def _to_knx(cls, value: HVACOperationMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class HVACControllerMode(Enum):
    """Enum for the different KNX HVAC controller modes."""

    AUTO = 0
    HEAT = 1
    MORNING_WARMUP = 2
    COOL = 3
    NIGHT_PURGE = 4
    PRECOOL = 5
    OFF = 6
    TEST = 7
    EMERGENCY_HEAT = 8
    FAN_ONLY = 9
    FREE_COOL = 10
    ICE = 11
    MAXIMUM_HEATING_MODE = 12
    ECONOMIC_HEAT_COOL_MODE = 13
    DEHUMIDIFICATION = 14
    CALIBRATION_MODE = 15
    EMERGENCY_COOL_MODE = 16
    EMERGENCY_STEAM_MODE = 17
    NODEM = 20


class DPTHVACContrMode(DPTEnum[HVACControllerMode]):
    """
    Abstraction for KNX HVAC controller mode.

    DPT 20.105
    """

    dpt_main_number = 20
    dpt_sub_number = 105
    value_type = "hvac_controller_mode"
    data_type = HVACControllerMode

    @classmethod
    def _to_knx(cls, value: HVACControllerMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


@dataclass(slots=True)
class HVACStatus(DPTComplexData):
    """Class for HVACStatus."""

    mode: HVACOperationMode
    dew_point: bool
    heat_cool: Literal[HVACControllerMode.HEAT, HVACControllerMode.COOL]
    inactive: bool
    frost_alarm: bool

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> HVACStatus:
        """Init from a dictionary."""
        try:
            _mode = data["mode"]
            _heat_cool = data["heat_cool"]
            try:
                mode = HVACOperationMode[_mode.upper()]
                heat_cool = HVACControllerMode[_heat_cool.upper()]
            except AttributeError as err:
                raise ValueError(
                    f"Invalid type for HVAC mode or heat_cool: {err}"
                ) from err
            if heat_cool not in (HVACControllerMode.HEAT, HVACControllerMode.COOL):
                raise ValueError(f"Invalid value for HVAC heat_cool: {heat_cool=}")
            dew_point = data["dew_point"]
            inactive = data["inactive"]
            frost_alarm = data["frost_alarm"]
        except KeyError as err:
            raise ValueError(f"Missing required key: {err}") from err

        if (
            not isinstance(dew_point, bool)
            or not isinstance(inactive, bool)
            or not isinstance(frost_alarm, bool)
        ):
            raise ValueError(
                f"Invalid value for HVACStatus boolean fields: {dew_point=}, {inactive=}, {frost_alarm=}"
            )

        return cls(
            mode=mode,
            dew_point=dew_point,
            heat_cool=heat_cool,  # type: ignore[arg-type]  # checked by `not in (HVACControllerMode.HEAT, HVACControllerMode.COOL)` above
            inactive=inactive,
            frost_alarm=frost_alarm,
        )

    def as_dict(self) -> dict[str, str | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "mode": self.mode.name.lower(),
            "dew_point": self.dew_point,
            "heat_cool": self.heat_cool.name.lower(),
            "inactive": self.inactive,
            "frost_alarm": self.frost_alarm,
        }


class DPTHVACStatus(DPTComplex[HVACStatus]):
    """
    Abstraction for KNX HVACStatus.

    Non-standardised DP type (in accordance with KNX AN097 “Eberle Status Byte”).
    """

    data_type = HVACStatus
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 20
    dpt_sub_number = 60102
    value_type = "hvac_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> HVACStatus:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)[0]

        mode: HVACOperationMode
        if raw & 0b10000000:
            mode = HVACOperationMode.COMFORT
        elif raw & 0b01000000:
            mode = HVACOperationMode.STANDBY
        elif raw & 0b00100000:
            mode = HVACOperationMode.ECONOMY
        elif raw & 0b00010000:
            mode = HVACOperationMode.BUILDING_PROTECTION
        else:
            mode = HVACOperationMode.AUTO  # not sure if this is possible / valid

        return HVACStatus(
            mode=mode,
            dew_point=bool(raw & 0b00001000),
            heat_cool=HVACControllerMode.HEAT
            if raw & 0b00000100
            else HVACControllerMode.COOL,
            inactive=bool(raw & 0b00000010),
            frost_alarm=bool(raw & 0b00000001),
        )

    @classmethod
    def _to_knx(cls, value: HVACStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        raw = 0
        if value.mode is HVACOperationMode.COMFORT:
            raw |= 0b10000000
        elif value.mode is HVACOperationMode.STANDBY:
            raw |= 0b01000000
        elif value.mode is HVACOperationMode.ECONOMY:
            raw |= 0b00100000
        elif value.mode is HVACOperationMode.BUILDING_PROTECTION:
            raw |= 0b00010000
        if value.dew_point:
            raw |= 0b00001000
        if value.heat_cool is HVACControllerMode.HEAT:
            raw |= 0b00000100
        if value.inactive:
            raw |= 0b00000010
        if value.frost_alarm:
            raw |= 0b00000001
        return DPTArray(raw)
