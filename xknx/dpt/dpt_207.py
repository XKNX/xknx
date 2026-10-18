"""
Implementation of KNX DPT 207 8-bit value and 8-bit set data point types.

KNX v02.02.01 - Datapoint Types 03.07.02 - §4.13 and §6.5.1
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..exceptions import ConversionError
from .dpt import DPTComplex, DPTComplexData
from .dpt_5 import DPTPercentU8, DPTScaling
from .helpers.metadata import RANGE_PERCENT
from .payload import DPTArray, DPTBinary


def _check_mapping(data: Any, name: str) -> Mapping[str, Any]:
    """Raise ValueError if `data` is not a mapping."""
    if not isinstance(data, Mapping):
        raise ValueError(f"Invalid value for {name}: {data!r}")
    return data


def _bool_from_dict(data: Mapping[str, Any], key: str) -> bool:
    """Parse an optional boolean of a dictionary, defaulting to False."""
    value = data.get(key, False)
    if value not in (True, False):
        raise ValueError(f"Invalid value for {key}: {value!r}")
    return bool(value)


def _percent_from_dict(data: Mapping[str, Any], key: str) -> int | None:
    """Parse an optional percent value of a dictionary."""
    value = data.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as err:
        raise ValueError(f"Invalid value for {key}: {err}") from err


def _required_percent_from_dict(data: Mapping[str, Any], key: str) -> int:
    """Parse a required percent value of a dictionary."""
    value = _percent_from_dict(data, key)
    if value is None:
        raise ValueError(f"Missing required key: {key!r}")
    return value


def _percent_from_knx(dpt: type[DPTComplex[Any]], raw: int) -> int:
    """Return a percent value with 1 % resolution."""
    if raw > 100:
        raise ConversionError(f"Payload not supported for {dpt.dpt_name()}", raw=raw)
    return raw


def _percent_to_knx(value: int | None) -> int:
    """
    Return the raw value of a percent value with 1 % resolution; None as 0.

    Encoded like DPT 5.004 (U8, 1 % resolution), limited to 0..100 %.
    """
    if value is None:
        return 0
    raw = DPTPercentU8.to_knx(value).value[0]
    if raw > 100:
        raise ConversionError(f"Percent value out of range 0..100: {value}")
    return raw


def _bit(raw: int, bit: int) -> bool:
    """Return a bit of the attributes octet."""
    return bool(raw >> bit & 0b1)


def _bits(*bits: bool) -> int:
    """Return the attributes octet of bits starting with bit 0."""
    return sum(bool(bit) << index for index, bit in enumerate(bits))


@dataclass(slots=True)
class BurnerControllerStatus(DPTComplexData):
    """
    Value of DPT 207.100 DPT_StatusBUC: a burner controller status.

    `relative_power`: int 0..100 %; None if invalid
    `fault`: burner failure
    `stage_1_active`: stage 1 or base stage active
    `stage_2_active`: stage 2 or modulation active
    """

    relative_power: int | None = field(default=None, metadata=RANGE_PERCENT)
    fault: bool = False
    stage_1_active: bool = False
    stage_2_active: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BurnerControllerStatus:
        """Init from a dictionary."""
        data = _check_mapping(data, cls.__name__)
        return cls(
            relative_power=_percent_from_dict(data, "relative_power"),
            fault=_bool_from_dict(data, "fault"),
            stage_1_active=_bool_from_dict(data, "stage_1_active"),
            stage_2_active=_bool_from_dict(data, "stage_2_active"),
        )

    def as_dict(self) -> dict[str, int | bool | None]:
        """Create a JSON serializable dictionary."""
        return {
            "relative_power": self.relative_power,
            "fault": self.fault,
            "stage_1_active": self.stage_1_active,
            "stage_2_active": self.stage_2_active,
        }


class DPTStatusBUC(DPTComplex[BurnerControllerStatus]):
    """
    Abstraction for KNX 2 octet Status Burner Controller (DPT 207.100 DPT_StatusBUC).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.13.1
    """

    data_type = BurnerControllerStatus
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 207
    dpt_sub_number = 100
    value_type = "burner_controller_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> BurnerControllerStatus:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return BurnerControllerStatus(
            relative_power=_percent_from_knx(cls, raw[0]) if _bit(raw[1], 0) else None,
            fault=_bit(raw[1], 1),
            stage_1_active=_bit(raw[1], 2),
            stage_2_active=_bit(raw[1], 3),
        )

    @classmethod
    def _to_knx(cls, value: BurnerControllerStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                _percent_to_knx(value.relative_power),
                _bits(
                    value.relative_power is not None,
                    value.fault,
                    value.stage_1_active,
                    value.stage_2_active,
                ),
            )
        )


@dataclass(slots=True)
class LockingSignal(DPTComplexData):
    """
    Value of DPT 207.101 DPT_LockSign: a locking signal.

    `power_reduction`: int 0..100 % requested power reduction;
        None if no power reduction is requested (the LockRequest bit is the
        validity of this field)
    `critical`: overload is critical
    """

    power_reduction: int | None = field(default=None, metadata=RANGE_PERCENT)
    critical: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LockingSignal:
        """Init from a dictionary."""
        data = _check_mapping(data, cls.__name__)
        return cls(
            power_reduction=_percent_from_dict(data, "power_reduction"),
            critical=_bool_from_dict(data, "critical"),
        )

    def as_dict(self) -> dict[str, int | bool | None]:
        """Create a JSON serializable dictionary."""
        return {
            "power_reduction": self.power_reduction,
            "critical": self.critical,
        }


class DPTLockSign(DPTComplex[LockingSignal]):
    """
    Abstraction for KNX 2 octet Locking Signal (DPT 207.101 DPT_LockSign).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.13.2
    """

    data_type = LockingSignal
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 207
    dpt_sub_number = 101
    value_type = "locking_signal"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> LockingSignal:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return LockingSignal(
            power_reduction=_percent_from_knx(cls, raw[0]) if _bit(raw[1], 0) else None,
            critical=_bit(raw[1], 1),
        )

    @classmethod
    def _to_knx(cls, value: LockingSignal) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                _percent_to_knx(value.power_reduction),
                _bits(value.power_reduction is not None, value.critical),
            )
        )


@dataclass(slots=True)
class BoilerControllerDemand(DPTComplexData):
    """
    Value of DPT 207.102 DPT_ValueDemBOC: a boiler controller demand signal.

    `relative_demand`: int 0..100 % for a modulating burner
    `stage_1_control`: operation of stage 1 or base stage on
    `stage_2_control`: stage 2 of a two stage burner on
    """

    relative_demand: int = field(metadata=RANGE_PERCENT)
    stage_1_control: bool = False
    stage_2_control: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BoilerControllerDemand:
        """Init from a dictionary."""
        data = _check_mapping(data, cls.__name__)
        return cls(
            relative_demand=_required_percent_from_dict(data, "relative_demand"),
            stage_1_control=_bool_from_dict(data, "stage_1_control"),
            stage_2_control=_bool_from_dict(data, "stage_2_control"),
        )

    def as_dict(self) -> dict[str, int | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "relative_demand": self.relative_demand,
            "stage_1_control": self.stage_1_control,
            "stage_2_control": self.stage_2_control,
        }


class DPTValueDemBOC(DPTComplex[BoilerControllerDemand]):
    """
    Abstraction for KNX 2 octet Boiler Controller Demand Signal (DPT 207.102 DPT_ValueDemBOC).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.13.3
    """

    data_type = BoilerControllerDemand
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 207
    dpt_sub_number = 102
    value_type = "boiler_controller_demand"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> BoilerControllerDemand:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return BoilerControllerDemand(
            relative_demand=_percent_from_knx(cls, raw[0]),
            stage_1_control=_bit(raw[1], 0),
            stage_2_control=_bit(raw[1], 1),
        )

    @classmethod
    def _to_knx(cls, value: BoilerControllerDemand) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                _percent_to_knx(value.relative_demand),
                _bits(value.stage_1_control, value.stage_2_control),
            )
        )


@dataclass(slots=True)
class ActuatorPositionDemand(DPTComplexData):
    """
    Value of DPT 207.104 DPT_ActPosDemAbs: an actuator position demand.

    `position`: int 0..100 % absolute actuator position demand; None if invalid (no demand)
    `absolute_load_priority`: absolute load priority
    `shift_load_priority`: shift load priority
    `emergency_demand`: emergency demand for room frost protection or de-icing
    """

    position: int | None = field(default=None, metadata=RANGE_PERCENT)
    absolute_load_priority: bool = False
    shift_load_priority: bool = False
    emergency_demand: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ActuatorPositionDemand:
        """Init from a dictionary."""
        data = _check_mapping(data, cls.__name__)
        return cls(
            position=_percent_from_dict(data, "position"),
            absolute_load_priority=_bool_from_dict(data, "absolute_load_priority"),
            shift_load_priority=_bool_from_dict(data, "shift_load_priority"),
            emergency_demand=_bool_from_dict(data, "emergency_demand"),
        )

    def as_dict(self) -> dict[str, int | bool | None]:
        """Create a JSON serializable dictionary."""
        return {
            "position": self.position,
            "absolute_load_priority": self.absolute_load_priority,
            "shift_load_priority": self.shift_load_priority,
            "emergency_demand": self.emergency_demand,
        }


class DPTActPosDemAbs(DPTComplex[ActuatorPositionDemand]):
    """
    Abstraction for KNX 2 octet Actuator Position Demand (DPT 207.104 DPT_ActPosDemAbs).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.13.4
    """

    data_type = ActuatorPositionDemand
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 207
    dpt_sub_number = 104
    value_type = "actuator_position_demand"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ActuatorPositionDemand:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return ActuatorPositionDemand(
            position=_percent_from_knx(cls, raw[0]) if _bit(raw[1], 0) else None,
            absolute_load_priority=_bit(raw[1], 1),
            shift_load_priority=_bit(raw[1], 2),
            emergency_demand=_bit(raw[1], 3),
        )

    @classmethod
    def _to_knx(cls, value: ActuatorPositionDemand) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                _percent_to_knx(value.position),
                _bits(
                    value.position is not None,
                    value.absolute_load_priority,
                    value.shift_load_priority,
                    value.emergency_demand,
                ),
            )
        )


@dataclass(slots=True)
class ActuatorPositionStatus(DPTComplexData):
    """
    Value of DPT 207.105 DPT_StatusAct: an actuator position status.

    `position`: int 0..100 % actual actuator position
    `failure`: actuator has a failure
    `manual_override`: actuator position is manually overridden
    `calibration_mode`: actuator is in calibration mode
    `valve_kick`: valve is executing a valve kick
    `synchronization_mode`: actuator is executing a synchronization of the stroke model
    """

    position: int = field(metadata=RANGE_PERCENT)
    failure: bool = False
    manual_override: bool = False
    calibration_mode: bool = False
    valve_kick: bool = False
    synchronization_mode: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ActuatorPositionStatus:
        """Init from a dictionary."""
        data = _check_mapping(data, cls.__name__)
        return cls(
            position=_required_percent_from_dict(data, "position"),
            failure=_bool_from_dict(data, "failure"),
            manual_override=_bool_from_dict(data, "manual_override"),
            calibration_mode=_bool_from_dict(data, "calibration_mode"),
            valve_kick=_bool_from_dict(data, "valve_kick"),
            synchronization_mode=_bool_from_dict(data, "synchronization_mode"),
        )

    def as_dict(self) -> dict[str, int | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "position": self.position,
            "failure": self.failure,
            "manual_override": self.manual_override,
            "calibration_mode": self.calibration_mode,
            "valve_kick": self.valve_kick,
            "synchronization_mode": self.synchronization_mode,
        }


class DPTStatusAct(DPTComplex[ActuatorPositionStatus]):
    """
    Abstraction for KNX 2 octet Actuator Position Status (DPT 207.105 DPT_StatusAct).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.13.5
    """

    data_type = ActuatorPositionStatus
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 207
    dpt_sub_number = 105
    value_type = "actuator_position_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ActuatorPositionStatus:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return ActuatorPositionStatus(
            position=_percent_from_knx(cls, raw[0]),
            failure=_bit(raw[1], 0),
            manual_override=_bit(raw[1], 1),
            calibration_mode=_bit(raw[1], 2),
            valve_kick=_bit(raw[1], 3),
            synchronization_mode=_bit(raw[1], 4),
        )

    @classmethod
    def _to_knx(cls, value: ActuatorPositionStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                _percent_to_knx(value.position),
                _bits(
                    value.failure,
                    value.manual_override,
                    value.calibration_mode,
                    value.valve_kick,
                    value.synchronization_mode,
                ),
            )
        )


@dataclass(slots=True)
class LightingActuatorStatus(DPTComplexData):
    """
    Value of DPT 207.600 DPT_StatusLightingActuator: a lighting actuator status.

    `lighting_level`: int 0..100 % current lighting level; None if invalid
    `locked`: actuator is locked
    `forced`: forced on/off control is active
    `night_mode_active`: night mode is active
    `staircase_lighting_function`: staircase lighting function is active
    `dimming`: actuator is in state dimming
    `local_override`: actuator setvalue is locally overridden
    `failure`: general actuator failure
    """

    lighting_level: int | None = field(default=None, metadata=RANGE_PERCENT)
    locked: bool = False
    forced: bool = False
    night_mode_active: bool = False
    staircase_lighting_function: bool = False
    dimming: bool = False
    local_override: bool = False
    failure: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LightingActuatorStatus:
        """Init from a dictionary."""
        data = _check_mapping(data, cls.__name__)
        return cls(
            lighting_level=_percent_from_dict(data, "lighting_level"),
            locked=_bool_from_dict(data, "locked"),
            forced=_bool_from_dict(data, "forced"),
            night_mode_active=_bool_from_dict(data, "night_mode_active"),
            staircase_lighting_function=_bool_from_dict(
                data, "staircase_lighting_function"
            ),
            dimming=_bool_from_dict(data, "dimming"),
            local_override=_bool_from_dict(data, "local_override"),
            failure=_bool_from_dict(data, "failure"),
        )

    def as_dict(self) -> dict[str, int | bool | None]:
        """Create a JSON serializable dictionary."""
        return {
            "lighting_level": self.lighting_level,
            "locked": self.locked,
            "forced": self.forced,
            "night_mode_active": self.night_mode_active,
            "staircase_lighting_function": self.staircase_lighting_function,
            "dimming": self.dimming,
            "local_override": self.local_override,
            "failure": self.failure,
        }


class DPTStatusLightingActuator(DPTComplex[LightingActuatorStatus]):
    """
    Abstraction for KNX 2 octet Status Lighting Actuator (DPT 207.600 DPT_StatusLightingActuator).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.5.1
    """

    data_type = LightingActuatorStatus
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 207
    dpt_sub_number = 600
    value_type = "lighting_actuator_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> LightingActuatorStatus:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return LightingActuatorStatus(
            lighting_level=DPTScaling.from_knx(DPTArray(raw[0]))
            if _bit(raw[1], 0)
            else None,
            locked=_bit(raw[1], 1),
            forced=_bit(raw[1], 2),
            night_mode_active=_bit(raw[1], 3),
            staircase_lighting_function=_bit(raw[1], 4),
            dimming=_bit(raw[1], 5),
            local_override=_bit(raw[1], 6),
            failure=_bit(raw[1], 7),
        )

    @classmethod
    def _to_knx(cls, value: LightingActuatorStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        lighting_level = (
            DPTScaling.to_knx(value.lighting_level).value[0]
            if value.lighting_level is not None
            else 0
        )
        return DPTArray(
            (
                lighting_level,
                _bits(
                    value.lighting_level is not None,
                    value.locked,
                    value.forced,
                    value.night_mode_active,
                    value.staircase_lighting_function,
                    value.dimming,
                    value.local_override,
                    value.failure,
                ),
            )
        )
