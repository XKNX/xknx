"""Unit test for DPT 2 objects."""

from typing import Any

import pytest

from xknx.dpt import (
    DPT2BitBoolean,
    DPTArray,
    DPTBase,
    DPTBinary,
    DPTBoolControl,
    DPTSwitchControl,
)
from xknx.dpt.dpt_1 import (
    Alarm,
    BinaryValue,
    Bool,
    Enable,
    Invert,
    Ramp,
    Start,
    State,
    Step,
    Switch,
    UpDown,
)
from xknx.dpt.dpt_2 import (
    AlarmControl,
    BinaryValueControl,
    BoolControl,
    Direction1Control,
    Direction2Control,
    DPTAlarmControl,
    DPTBinaryValueControl,
    DPTDirection1Control,
    DPTDirection2Control,
    DPTEnableControl,
    DPTInvertControl,
    DPTRampControl,
    DPTStartControl,
    DPTStateControl,
    DPTStepControl,
    EnableControl,
    InvertControl,
    RampControl,
    StartControl,
    StateControl,
    StepControl,
    SwitchControl,
)
from xknx.exceptions import CouldNotParseTelegram


class TestBinaryControlData:
    """Test class for BinaryControl data objects."""

    @pytest.mark.parametrize(
        ("data", "dict_value"),
        [
            (
                SwitchControl(control=False, value=Switch.OFF),
                {"control": False, "value": "off"},
            ),
            (
                SwitchControl(control=True, value=Switch.ON),
                {"control": True, "value": "on"},
            ),
            (
                BoolControl(control=False, value=Bool.TRUE),
                {"control": False, "value": "true"},
            ),
            (
                EnableControl(control=True, value=Enable.ENABLE),
                {"control": True, "value": "enable"},
            ),
            (
                StepControl(control=False, value=Step.INCREASE),
                {"control": False, "value": "increase"},
            ),
            (
                Direction1Control(control=True, value=UpDown.DOWN),
                {"control": True, "value": "down"},
            ),
            (
                Direction2Control(control=False, value=UpDown.UP),
                {"control": False, "value": "up"},
            ),
        ],
    )
    def test_dict(self, data: SwitchControl, dict_value: dict[str, Any]) -> None:
        """Test from_dict and as_dict methods."""
        assert data.__class__.from_dict(dict_value) == data
        assert data.as_dict() == dict_value

    @pytest.mark.parametrize(
        ("cls", "dict_value"),
        [
            (SwitchControl, {"control": True, "value": "invalid"}),
            (SwitchControl, {"control": "invalid", "value": "on"}),
            (SwitchControl, {"control": True}),  # missing value
            (SwitchControl, {"value": "on"}),  # missing control
            (BoolControl, {"control": True, "value": "invalid"}),
            (
                EnableControl,
                {"control": True, "value": "on"},
            ),  # wrong enum value for Enable
        ],
    )
    def test_dict_invalid(
        self, cls: type[SwitchControl], dict_value: dict[str, Any]
    ) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            cls.from_dict(dict_value)


@pytest.mark.parametrize(
    ("dpt_cls", "data_cls", "value_false", "value_true"),
    [
        (DPTSwitchControl, SwitchControl, Switch.OFF, Switch.ON),
        (DPTBoolControl, BoolControl, Bool.FALSE, Bool.TRUE),
        (DPT2BitBoolean, BoolControl, Bool.FALSE, Bool.TRUE),
        (DPTEnableControl, EnableControl, Enable.DISABLE, Enable.ENABLE),
        (DPTRampControl, RampControl, Ramp.NO_RAMP, Ramp.RAMP),
        (DPTAlarmControl, AlarmControl, Alarm.NO_ALARM, Alarm.ALARM),
        (DPTBinaryValueControl, BinaryValueControl, BinaryValue.LOW, BinaryValue.HIGH),
        (DPTStepControl, StepControl, Step.DECREASE, Step.INCREASE),
        (DPTDirection1Control, Direction1Control, UpDown.UP, UpDown.DOWN),
        (DPTDirection2Control, Direction2Control, UpDown.UP, UpDown.DOWN),
        (DPTStartControl, StartControl, Start.STOP, Start.START),
        (DPTStateControl, StateControl, State.INACTIVE, State.ACTIVE),
        (DPTInvertControl, InvertControl, Invert.NOT_INVERTED, Invert.INVERTED),
    ],
)
class TestDPTBinaryControl:
    """Test class for DPT 2 transcoding."""

    def test_all_raw_values(
        self,
        dpt_cls: type[DPTSwitchControl],
        data_cls: type[SwitchControl],
        value_false: Switch,
        value_true: Switch,
    ) -> None:
        """Test all 4 possible raw values (0-3) round-trip correctly."""
        expected = [
            data_cls(control=False, value=value_false),  # raw 0: c=0 v=0
            data_cls(control=False, value=value_true),  # raw 1: c=0 v=1
            data_cls(control=True, value=value_false),  # raw 2: c=1 v=0
            data_cls(control=True, value=value_true),  # raw 3: c=1 v=1
        ]
        for raw, exp in enumerate(expected):
            decoded = dpt_cls.from_knx(DPTBinary(raw))
            assert decoded == exp, f"Decode failed for raw={raw}"
            encoded = dpt_cls.to_knx(exp)
            assert encoded == DPTBinary(raw), f"Encode failed for {exp}"

    def test_from_knx_to_knx_roundtrip(
        self,
        dpt_cls: type[DPTSwitchControl],
        data_cls: type[SwitchControl],
        value_false: Switch,
        value_true: Switch,
    ) -> None:
        """Test from_knx -> to_knx round-trip for all raw values."""
        for raw in range(4):
            payload = DPTBinary(raw)
            assert dpt_cls.to_knx(dpt_cls.from_knx(payload)) == payload

    def test_to_knx_from_dict(
        self,
        dpt_cls: type[DPTSwitchControl],
        data_cls: type[SwitchControl],
        value_false: Switch,
        value_true: Switch,
    ) -> None:
        """Test that to_knx accepts a dict via DPTComplex.to_knx."""
        sample = data_cls(control=True, value=value_true)
        as_dict = sample.as_dict()
        assert dpt_cls.to_knx(as_dict) == dpt_cls.to_knx(sample)

    def test_dpt_number(
        self,
        dpt_cls: type[DPTSwitchControl],
        data_cls: type[SwitchControl],
        value_false: Switch,
        value_true: Switch,
    ) -> None:
        """Test DPT main number is 2."""
        assert dpt_cls.dpt_main_number == 2

    def test_invalid_payload_type(
        self,
        dpt_cls: type[DPTSwitchControl],
        data_cls: type[SwitchControl],
        value_false: Switch,
        value_true: Switch,
    ) -> None:
        """Test that wrong payload type raises CouldNotParseTelegram."""
        with pytest.raises(CouldNotParseTelegram):
            dpt_cls.from_knx(DPTArray((0,)))

    def test_invalid_payload_value(
        self,
        dpt_cls: type[DPTSwitchControl],
        data_cls: type[SwitchControl],
        value_false: Switch,
        value_true: Switch,
    ) -> None:
        """Test that a value >= 4 (exceeds 2-bit range) raises CouldNotParseTelegram."""
        with pytest.raises(CouldNotParseTelegram):
            dpt_cls.from_knx(DPTBinary(4))


class TestDPTBinaryControlSchema:
    """Test get_dict_schema for DPT 2 classes."""

    def test_switch_control_schema(self) -> None:
        """Test schema for DPTSwitchControl has correct fields."""
        schema = DPTSwitchControl.get_dict_schema()
        names = {f["name"] for f in schema}
        assert names == {"control", "value"}
        value_field = next(f for f in schema if f["name"] == "value")
        assert value_field["type"] == "enum"
        assert value_field["options"] == ["off", "on"]

    def test_bool_control_schema(self) -> None:
        """Test schema for DPTBoolControl has correct enum options."""
        schema = DPTBoolControl.get_dict_schema()
        value_field = next(f for f in schema if f["name"] == "value")
        assert value_field["options"] == ["false", "true"]


class TestDPT2BitBoolean:
    """Test the generic DPT 2 (2.*** boolean control) transcoder."""

    def test_transcoder_lookup(self) -> None:
        """Generic DPT 2 is found by main number and value_type; subtypes still win."""
        assert DPTBase.parse_transcoder(2) is DPT2BitBoolean
        assert DPTBase.parse_transcoder("2bit") is DPT2BitBoolean
        assert DPTBase.parse_transcoder("2.001") is DPTSwitchControl
        assert DPTBase.parse_transcoder("2.002") is DPTBoolControl

    def test_generic_matches_dptboolcontrol(self) -> None:
        """Generic DPT 2 decodes/encodes the same as DPTBoolControl (2.002)."""
        value = BoolControl(control=True, value=Bool.TRUE)
        assert DPT2BitBoolean.from_knx(DPTBinary(3)) == value
        assert DPT2BitBoolean.to_knx(value) == DPTBoolControl.to_knx(value)
