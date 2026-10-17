"""Unit test for KNX DPT 207 8-bit value and 8-bit set objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt import DPTComplex, DPTComplexData
from xknx.dpt.dpt_207 import (
    ActuatorPositionDemand,
    ActuatorPositionStatus,
    BoilerControllerDemand,
    BurnerControllerStatus,
    DPTActPosDemAbs,
    DPTLockSign,
    DPTStatusAct,
    DPTStatusBUC,
    DPTStatusLightingActuator,
    DPTValueDemBOC,
    LightingActuatorStatus,
    LockingSignal,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram

ALL_DPTS: list[type[DPTComplex[Any]]] = [
    DPTStatusBUC,
    DPTLockSign,
    DPTValueDemBOC,
    DPTActPosDemAbs,
    DPTStatusAct,
    DPTStatusLightingActuator,
]


@pytest.mark.parametrize(
    ("dpt_class", "value", "raw"),
    [
        # 207.100 - bit 0 is the validity of the relative power
        (DPTStatusBUC, BurnerControllerStatus(), (0x00, 0x00)),
        (DPTStatusBUC, BurnerControllerStatus(0), (0x00, 0x01)),
        (DPTStatusBUC, BurnerControllerStatus(100), (0x64, 0x01)),
        (DPTStatusBUC, BurnerControllerStatus(fault=True), (0x00, 0x02)),
        (DPTStatusBUC, BurnerControllerStatus(stage_1_active=True), (0x00, 0x04)),
        (DPTStatusBUC, BurnerControllerStatus(stage_2_active=True), (0x00, 0x08)),
        (DPTStatusBUC, BurnerControllerStatus(55, True, True, True), (0x37, 0x0F)),
        # 207.101 - bit 0 is the lock request (validity of the power reduction)
        (DPTLockSign, LockingSignal(), (0x00, 0x00)),
        (DPTLockSign, LockingSignal(0), (0x00, 0x01)),
        (DPTLockSign, LockingSignal(100), (0x64, 0x01)),
        (DPTLockSign, LockingSignal(critical=True), (0x00, 0x02)),
        (DPTLockSign, LockingSignal(30, critical=True), (0x1E, 0x03)),
        # 207.102 - no validity bit
        (DPTValueDemBOC, BoilerControllerDemand(0), (0x00, 0x00)),
        (DPTValueDemBOC, BoilerControllerDemand(100), (0x64, 0x00)),
        (DPTValueDemBOC, BoilerControllerDemand(0, stage_1_control=True), (0x00, 0x01)),
        (DPTValueDemBOC, BoilerControllerDemand(0, stage_2_control=True), (0x00, 0x02)),
        (DPTValueDemBOC, BoilerControllerDemand(75, True, True), (0x4B, 0x03)),
        # 207.104 - bit 0 is the validity of the position demand
        (DPTActPosDemAbs, ActuatorPositionDemand(), (0x00, 0x00)),
        (DPTActPosDemAbs, ActuatorPositionDemand(0), (0x00, 0x01)),
        (DPTActPosDemAbs, ActuatorPositionDemand(100), (0x64, 0x01)),
        (
            DPTActPosDemAbs,
            ActuatorPositionDemand(absolute_load_priority=True),
            (0x00, 0x02),
        ),
        (
            DPTActPosDemAbs,
            ActuatorPositionDemand(shift_load_priority=True),
            (0x00, 0x04),
        ),
        (DPTActPosDemAbs, ActuatorPositionDemand(emergency_demand=True), (0x00, 0x08)),
        (
            DPTActPosDemAbs,
            ActuatorPositionDemand(42, True, True, True),
            (0x2A, 0x0F),
        ),
        # 207.105 - no validity bit
        (DPTStatusAct, ActuatorPositionStatus(0), (0x00, 0x00)),
        (DPTStatusAct, ActuatorPositionStatus(100), (0x64, 0x00)),
        (DPTStatusAct, ActuatorPositionStatus(0, failure=True), (0x00, 0x01)),
        (DPTStatusAct, ActuatorPositionStatus(0, manual_override=True), (0x00, 0x02)),
        (DPTStatusAct, ActuatorPositionStatus(0, calibration_mode=True), (0x00, 0x04)),
        (DPTStatusAct, ActuatorPositionStatus(0, valve_kick=True), (0x00, 0x08)),
        (
            DPTStatusAct,
            ActuatorPositionStatus(0, synchronization_mode=True),
            (0x00, 0x10),
        ),
        (
            DPTStatusAct,
            ActuatorPositionStatus(20, True, True, True, True, True),
            (0x14, 0x1F),
        ),
        # 207.600 - lighting level scaled like DPT 5.001, bit 0 is its validity
        (DPTStatusLightingActuator, LightingActuatorStatus(), (0x00, 0x00)),
        (DPTStatusLightingActuator, LightingActuatorStatus(0), (0x00, 0x01)),
        (DPTStatusLightingActuator, LightingActuatorStatus(50), (0x80, 0x01)),
        (DPTStatusLightingActuator, LightingActuatorStatus(100), (0xFF, 0x01)),
        (
            DPTStatusLightingActuator,
            LightingActuatorStatus(locked=True),
            (0x00, 0x02),
        ),
        (
            DPTStatusLightingActuator,
            LightingActuatorStatus(forced=True),
            (0x00, 0x04),
        ),
        (
            DPTStatusLightingActuator,
            LightingActuatorStatus(night_mode_active=True),
            (0x00, 0x08),
        ),
        (
            DPTStatusLightingActuator,
            LightingActuatorStatus(staircase_lighting_function=True),
            (0x00, 0x10),
        ),
        (
            DPTStatusLightingActuator,
            LightingActuatorStatus(dimming=True),
            (0x00, 0x20),
        ),
        (
            DPTStatusLightingActuator,
            LightingActuatorStatus(local_override=True),
            (0x00, 0x40),
        ),
        (
            DPTStatusLightingActuator,
            LightingActuatorStatus(failure=True),
            (0x00, 0x80),
        ),
        (
            DPTStatusLightingActuator,
            LightingActuatorStatus(100, True, True, True, True, True, True, True),
            (0xFF, 0xFF),
        ),
    ],
)
def test_values(
    dpt_class: type[DPTComplex[Any]], value: DPTComplexData, raw: tuple[int, ...]
) -> None:
    """Test parsing and streaming."""
    knx_value = dpt_class.to_knx(value)
    assert knx_value == DPTArray(raw)
    assert dpt_class.from_knx(knx_value) == value
    # dict round trip
    assert dpt_class.to_knx(value.as_dict()) == knx_value


@pytest.mark.parametrize(
    ("dpt_class", "raw", "value"),
    [
        # reserved bits are ignored
        (DPTStatusBUC, (0x0A, 0xF1), BurnerControllerStatus(10)),
        (DPTLockSign, (0x0A, 0xFD), LockingSignal(10)),
        (DPTValueDemBOC, (0x0A, 0xFC), BoilerControllerDemand(10)),
        (DPTActPosDemAbs, (0x0A, 0xF1), ActuatorPositionDemand(10)),
        (DPTStatusAct, (0x0A, 0xE0), ActuatorPositionStatus(10)),
        # values of invalid fields are ignored
        (DPTStatusBUC, (0xFF, 0x00), BurnerControllerStatus()),
        (DPTLockSign, (0xFF, 0x00), LockingSignal()),
        (DPTActPosDemAbs, (0xFF, 0x00), ActuatorPositionDemand()),
        (DPTStatusLightingActuator, (0xFF, 0x00), LightingActuatorStatus()),
        (DPTStatusLightingActuator, (0x01, 0x01), LightingActuatorStatus(0)),
        (DPTStatusLightingActuator, (0x03, 0x01), LightingActuatorStatus(1)),
    ],
)
def test_from_knx(
    dpt_class: type[DPTComplex[Any]], raw: tuple[int, ...], value: DPTComplexData
) -> None:
    """Test parsing of special payloads."""
    assert dpt_class.from_knx(DPTArray(raw)) == value


@pytest.mark.parametrize(
    ("dpt_class", "raw"),
    [
        (DPTStatusBUC, (0x65, 0x01)),
        (DPTLockSign, (0x65, 0x01)),
        (DPTValueDemBOC, (0x65, 0x00)),
        (DPTActPosDemAbs, (0xFF, 0x01)),
        (DPTStatusAct, (0x65, 0x00)),
    ],
)
def test_from_knx_out_of_range(
    dpt_class: type[DPTComplex[Any]], raw: tuple[int, ...]
) -> None:
    """Test parsing percent values above 100 %."""
    with pytest.raises(ConversionError):
        dpt_class.from_knx(DPTArray(raw))


@pytest.mark.parametrize("dpt_class", ALL_DPTS)
@pytest.mark.parametrize(
    "payload",
    [DPTArray((0x00,)), DPTArray((0x00, 0x00, 0x00)), DPTBinary(1)],
)
def test_from_knx_wrong_payload(
    dpt_class: type[DPTComplex[Any]], payload: DPTArray | DPTBinary
) -> None:
    """Test parsing wrong payloads."""
    with pytest.raises(CouldNotParseTelegram):
        dpt_class.from_knx(payload)


@pytest.mark.parametrize(
    ("dpt_class", "value"),
    [
        (DPTStatusBUC, BurnerControllerStatus(101)),
        (DPTStatusBUC, BurnerControllerStatus(-1)),
        (DPTStatusBUC, {"relative_power": "a"}),
        (DPTStatusBUC, {"fault": 1}),
        (DPTLockSign, LockingSignal(101)),
        (DPTLockSign, {"critical": "yes"}),
        (DPTValueDemBOC, BoilerControllerDemand(101)),
        (DPTValueDemBOC, {}),
        (DPTValueDemBOC, {"relative_demand": 10, "stage_1_control": None}),
        (DPTActPosDemAbs, ActuatorPositionDemand(101)),
        (DPTActPosDemAbs, {"emergency_demand": "a"}),
        (DPTStatusAct, ActuatorPositionStatus(101)),
        (DPTStatusAct, {"failure": True}),
        (DPTStatusLightingActuator, LightingActuatorStatus(101)),
        (DPTStatusLightingActuator, LightingActuatorStatus(-1)),
        (DPTStatusLightingActuator, {"lighting_level": [1]}),
        (DPTStatusLightingActuator, None),
        (DPTStatusLightingActuator, 1),
    ],
)
def test_to_knx_invalid(dpt_class: type[DPTComplex[Any]], value: Any) -> None:
    """Test serializing invalid values."""
    with pytest.raises(ConversionError):
        dpt_class.to_knx(value)


@pytest.mark.parametrize(
    ("data_class", "data", "value"),
    [
        (BurnerControllerStatus, {}, BurnerControllerStatus()),
        (
            BurnerControllerStatus,
            {"relative_power": "20", "stage_2_active": True},
            BurnerControllerStatus(20, stage_2_active=True),
        ),
        (LockingSignal, {"power_reduction": 5}, LockingSignal(5)),
        (
            BoilerControllerDemand,
            {"relative_demand": 5, "stage_1_control": True},
            BoilerControllerDemand(5, stage_1_control=True),
        ),
        (
            ActuatorPositionDemand,
            {"position": None, "shift_load_priority": True},
            ActuatorPositionDemand(shift_load_priority=True),
        ),
        (
            ActuatorPositionStatus,
            {"position": 0, "valve_kick": True},
            ActuatorPositionStatus(0, valve_kick=True),
        ),
        (
            LightingActuatorStatus,
            {"lighting_level": 80, "dimming": True},
            LightingActuatorStatus(80, dimming=True),
        ),
    ],
)
def test_from_dict(
    data_class: type[DPTComplexData], data: dict[str, Any], value: DPTComplexData
) -> None:
    """Test from_dict."""
    assert data_class.from_dict(data) == value


@pytest.mark.parametrize(
    ("data_class", "data"),
    [
        (BurnerControllerStatus, {"relative_power": "a"}),
        (BurnerControllerStatus, {"fault": "true"}),
        (LockingSignal, {"power_reduction": [5]}),
        (BoilerControllerDemand, {}),
        (BoilerControllerDemand, {"relative_demand": None}),
        (ActuatorPositionDemand, {"emergency_demand": 0}),
        (ActuatorPositionStatus, {"failure": False}),
        (LightingActuatorStatus, {"locked": None}),
    ],
)
def test_from_dict_invalid(
    data_class: type[DPTComplexData], data: dict[str, Any]
) -> None:
    """Test from_dict with invalid data."""
    with pytest.raises(ValueError):
        data_class.from_dict(data)


def test_as_dict() -> None:
    """Test as_dict."""
    assert BurnerControllerStatus(10, fault=True).as_dict() == {
        "relative_power": 10,
        "fault": True,
        "stage_1_active": False,
        "stage_2_active": False,
    }
    assert LockingSignal().as_dict() == {"power_reduction": None, "critical": False}
    assert BoilerControllerDemand(1, stage_2_control=True).as_dict() == {
        "relative_demand": 1,
        "stage_1_control": False,
        "stage_2_control": True,
    }
    assert ActuatorPositionDemand(emergency_demand=True).as_dict() == {
        "position": None,
        "absolute_load_priority": False,
        "shift_load_priority": False,
        "emergency_demand": True,
    }
    assert ActuatorPositionStatus(3).as_dict() == {
        "position": 3,
        "failure": False,
        "manual_override": False,
        "calibration_mode": False,
        "valve_kick": False,
        "synchronization_mode": False,
    }
    assert LightingActuatorStatus(99, failure=True).as_dict() == {
        "lighting_level": 99,
        "locked": False,
        "forced": False,
        "night_mode_active": False,
        "staircase_lighting_function": False,
        "dimming": False,
        "local_override": False,
        "failure": True,
    }


def _bool_schema(name: str) -> dict[str, Any]:
    return {"name": name, "type": "boolean", "required": False, "default": False}


def _percent_schema(name: str, required: bool) -> dict[str, Any]:
    return {
        "name": name,
        "type": "integer",
        "required": required,
        "value_min": 0,
        "value_max": 100,
    }


@pytest.mark.parametrize(
    ("dpt_class", "schema"),
    [
        (
            DPTStatusBUC,
            [
                _percent_schema("relative_power", False),
                _bool_schema("fault"),
                _bool_schema("stage_1_active"),
                _bool_schema("stage_2_active"),
            ],
        ),
        (
            DPTLockSign,
            [_percent_schema("power_reduction", False), _bool_schema("critical")],
        ),
        (
            DPTValueDemBOC,
            [
                _percent_schema("relative_demand", True),
                _bool_schema("stage_1_control"),
                _bool_schema("stage_2_control"),
            ],
        ),
        (
            DPTActPosDemAbs,
            [
                _percent_schema("position", False),
                _bool_schema("absolute_load_priority"),
                _bool_schema("shift_load_priority"),
                _bool_schema("emergency_demand"),
            ],
        ),
        (
            DPTStatusAct,
            [
                _percent_schema("position", True),
                _bool_schema("failure"),
                _bool_schema("manual_override"),
                _bool_schema("calibration_mode"),
                _bool_schema("valve_kick"),
                _bool_schema("synchronization_mode"),
            ],
        ),
        (
            DPTStatusLightingActuator,
            [
                _percent_schema("lighting_level", False),
                _bool_schema("locked"),
                _bool_schema("forced"),
                _bool_schema("night_mode_active"),
                _bool_schema("staircase_lighting_function"),
                _bool_schema("dimming"),
                _bool_schema("local_override"),
                _bool_schema("failure"),
            ],
        ),
    ],
)
def test_get_dict_schema(
    dpt_class: type[DPTComplex[Any]], schema: list[dict[str, Any]]
) -> None:
    """Test get_dict_schema."""
    assert dpt_class.get_dict_schema() == schema


@pytest.mark.parametrize(
    ("dpt_class", "dpt_number", "value_type"),
    [
        (DPTStatusBUC, "207.100", "burner_controller_status"),
        (DPTLockSign, "207.101", "locking_signal"),
        (DPTValueDemBOC, "207.102", "boiler_controller_demand"),
        (DPTActPosDemAbs, "207.104", "actuator_position_demand"),
        (DPTStatusAct, "207.105", "actuator_position_status"),
        (DPTStatusLightingActuator, "207.600", "lighting_actuator_status"),
    ],
)
def test_lookup(dpt_class: type[DPTBase], dpt_number: str, value_type: str) -> None:
    """Test lookup by DPT number and value_type."""
    assert DPTBase.parse_transcoder(dpt_number) is dpt_class
    assert DPTBase.parse_transcoder(value_type) is dpt_class
