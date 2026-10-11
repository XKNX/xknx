"""Implementation of KNX DPT 20.xxx 1 octet enumerations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .dpt import DPTComplex, DPTComplexData, DPTEnum, DPTEnumData
from .dpt_1 import HeatCool
from .payload import DPTArray, DPTBinary


class ErrorClassSystem(DPTEnumData):
    """
    Enum for the KNX system error classes.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21: values 19 to 255 are
    reserved and shall not be used.
    """

    NO_FAULT = 0
    GENERAL_DEVICE_FAULT = 1
    COMMUNICATION_FAULT = 2
    CONFIGURATION_FAULT = 3
    HARDWARE_FAULT = 4
    SOFTWARE_FAULT = 5
    INSUFFICIENT_NON_VOLATILE_MEMORY = 6
    INSUFFICIENT_VOLATILE_MEMORY = 7
    MEMORY_ALLOCATION_COMMAND_WITH_SIZE_0_RECEIVED = 8
    CRC_ERROR = 9
    WATCHDOG_RESET_DETECTED = 10
    INVALID_OPCODE_DETECTED = 11
    GENERAL_PROTECTION_FAULT = 12
    MAXIMAL_TABLE_LENGTH_EXCEEDED = 13
    UNDEFINED_LOAD_COMMAND_RECEIVED = 14
    GROUP_ADDRESS_TABLE_IS_NOT_SORTED = 15
    INVALID_CONNECTION_NUMBER = 16
    INVALID_GROUP_OBJECT_NUMBER = 17
    GROUP_OBJECT_TYPE_EXCEEDS_MAX_APDU_LENGTH = 18


class DPTErrorClassSystem(DPTEnum[ErrorClassSystem]):
    """
    Abstraction for KNX system error class.

    DPT 20.011 - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21. Also the
    Datapoint Type of `PID_ERROR_CODE` - KNX v01.10.01 - Resources 03.05.01 -
    §4.2.28: it holds the last error that occurred before the load state
    'Error' was set, and is reset to 0 (no fault) when the load state changes
    from 'Error' to a different state. A device may implement a subset of the
    error classes only.
    """

    dpt_main_number = 20
    dpt_sub_number = 11
    value_type = "error_class_system"
    data_type = ErrorClassSystem

    @classmethod
    def _to_knx(cls, value: ErrorClassSystem) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class HVACOperationMode(DPTEnumData):
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


class HVACControllerMode(DPTEnumData):
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
    heat_cool: HeatCool
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
                heat_cool = HeatCool[_heat_cool.upper()]
            except AttributeError as err:
                raise ValueError(
                    f"Invalid type for HVAC mode or heat_cool: {err}"
                ) from err
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
            heat_cool=heat_cool,
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
        if raw & 0x1:
            mode = HVACOperationMode.COMFORT
        elif raw & 0x2:
            mode = HVACOperationMode.STANDBY
        elif raw & 0x4:
            mode = HVACOperationMode.ECONOMY
        elif raw & 0x8:
            mode = HVACOperationMode.BUILDING_PROTECTION
        else:
            mode = HVACOperationMode.AUTO  # not sure if this is possible / valid

        return HVACStatus(
            mode=mode,
            dew_point=bool(raw & 0x10),
            heat_cool=HeatCool.HEAT if raw & 0x20 else HeatCool.COOL,
            inactive=bool(raw & 0x40),
            frost_alarm=bool(raw & 0x80),
        )

    @classmethod
    def _to_knx(cls, value: HVACStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        raw = 0
        if value.mode is HVACOperationMode.COMFORT:
            raw |= 0x1
        elif value.mode is HVACOperationMode.STANDBY:
            raw |= 0x2
        elif value.mode is HVACOperationMode.ECONOMY:
            raw |= 0x4
        elif value.mode is HVACOperationMode.BUILDING_PROTECTION:
            raw |= 0x8
        if value.dew_point:
            raw |= 0x10
        if value.heat_cool is HeatCool.HEAT:
            raw |= 0x20
        if value.inactive:
            raw |= 0x40
        if value.frost_alarm:
            raw |= 0x80
        return DPTArray(raw)
