"""Unit test for KNX DPT 1."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBinary, DPTEnumData
from xknx.dpt.dpt_1 import (
    Ack,
    Alarm,
    BinaryValue,
    Bool,
    ConsumerProducer,
    DayNight,
    DimSendStyle,
    DPT1BitEnum,
    DPTAck,
    DPTAlarm,
    DPTBinaryValue,
    DPTBool,
    DPTConsumerProducer,
    DPTDayNight,
    DPTDimSendStyle,
    DPTEnable,
    DPTEnergyDirection,
    DPTHeatCool,
    DPTInputSource,
    DPTInvert,
    DPTLogicalFunction,
    DPTOccupancy,
    DPTOpenClose,
    DPTRamp,
    DPTReset,
    DPTSceneAB,
    DPTShutterBlindsMode,
    DPTStart,
    DPTState,
    DPTStep,
    DPTSwitch,
    DPTTrigger,
    DPTUpDown,
    DPTWindowDoor,
    Enable,
    EnergyDirection,
    HeatCool,
    InputSource,
    Invert,
    LogicalFunction,
    Occupancy,
    OpenClose,
    Ramp,
    Reset,
    SceneAB,
    ShutterBlindsMode,
    Start,
    State,
    Step,
    Switch,
    Trigger,
    UpDown,
    WindowDoor,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


@pytest.mark.parametrize(
    ("dpt", "value_false", "value_true"),
    [
        (DPTSwitch, Switch.OFF, Switch.ON),
        (DPTBool, Bool.FALSE, Bool.TRUE),
        (DPTEnable, Enable.DISABLE, Enable.ENABLE),
        (DPTRamp, Ramp.NO_RAMP, Ramp.RAMP),
        (DPTAlarm, Alarm.NO_ALARM, Alarm.ALARM),
        (DPTBinaryValue, BinaryValue.LOW, BinaryValue.HIGH),
        (DPTStep, Step.DECREASE, Step.INCREASE),
        (DPTUpDown, UpDown.UP, UpDown.DOWN),
        (DPTOpenClose, OpenClose.OPEN, OpenClose.CLOSE),
        (DPTStart, Start.STOP, Start.START),
        (DPTState, State.INACTIVE, State.ACTIVE),
        (DPTInvert, Invert.NOT_INVERTED, Invert.INVERTED),
        (DPTDimSendStyle, DimSendStyle.START_STOP, DimSendStyle.CYCLICALLY),
        (DPTInputSource, InputSource.FIXED, InputSource.CALCULATED),
        (DPTReset, Reset.NO_ACTION, Reset.RESET),
        (DPTAck, Ack.NO_ACTION, Ack.ACKNOWLEDGE),
        (DPTTrigger, Trigger.TRIGGER_0, Trigger.TRIGGER),
        (DPTOccupancy, Occupancy.NOT_OCCUPIED, Occupancy.OCCUPIED),
        (DPTWindowDoor, WindowDoor.CLOSED, WindowDoor.OPEN),
        (DPTLogicalFunction, LogicalFunction.OR, LogicalFunction.AND),
        (DPTSceneAB, SceneAB.SCENE_A, SceneAB.SCENE_B),
        (
            DPTShutterBlindsMode,
            ShutterBlindsMode.UP_DOWN_MODE,
            ShutterBlindsMode.STEP_STOP_MODE,
        ),
        (DPTDayNight, DayNight.DAY, DayNight.NIGHT),
        (DPTHeatCool, HeatCool.COOL, HeatCool.HEAT),
        (DPTConsumerProducer, ConsumerProducer.CONSUMER, ConsumerProducer.PRODUCER),
        (DPTEnergyDirection, EnergyDirection.POSITIVE, EnergyDirection.NEGATIVE),
    ],
)
class TestDPT1:
    """Test class for KNX DPT 1 values."""

    def test_to_knx(
        self,
        dpt: type[DPT1BitEnum[Any]],
        value_true: DPTEnumData,
        value_false: DPTEnumData,
    ) -> None:
        """Test parsing to KNX."""
        assert dpt.to_knx(value_true) == DPTBinary(1)
        assert dpt.to_knx(value_false) == DPTBinary(0)

    def test_to_knx_by_string(
        self,
        dpt: type[DPT1BitEnum[Any]],
        value_true: DPTEnumData,
        value_false: DPTEnumData,
    ) -> None:
        """Test parsing string values to KNX."""
        assert dpt.to_knx(value_true.name.lower()) == DPTBinary(1)
        assert dpt.to_knx(value_false.name.lower()) == DPTBinary(0)

    def test_to_knx_by_value(
        self,
        dpt: type[DPT1BitEnum[Any]],
        value_true: DPTEnumData,
        value_false: DPTEnumData,
    ) -> None:
        """Test parsing string values to KNX."""
        assert dpt.to_knx(True) == DPTBinary(1)
        assert dpt.to_knx(1) == DPTBinary(1)
        assert dpt.to_knx(False) == DPTBinary(0)
        assert dpt.to_knx(0) == DPTBinary(0)

    def test_to_knx_wrong_value(
        self,
        dpt: type[DPT1BitEnum[Any]],
        value_true: DPTEnumData,
        value_false: DPTEnumData,
    ) -> None:
        """Test serializing to KNX with wrong value."""
        with pytest.raises(ConversionError):
            dpt.to_knx(2)

    def test_from_knx(
        self,
        dpt: type[DPT1BitEnum[Any]],
        value_true: DPTEnumData,
        value_false: DPTEnumData,
    ) -> None:
        """Test parsing from KNX."""
        assert dpt.from_knx(DPTBinary(0)) == value_false
        assert dpt.from_knx(DPTBinary(1)) == value_true

    def test_from_knx_wrong_value(
        self,
        dpt: type[DPT1BitEnum[Any]],
        value_true: DPTEnumData,
        value_false: DPTEnumData,
    ) -> None:
        """Test parsing with wrong value)."""
        with pytest.raises(CouldNotParseTelegram):
            dpt.from_knx(DPTArray((1,)))
        with pytest.raises(CouldNotParseTelegram):
            dpt.from_knx(DPTBinary(2))
