"""Implementation of KNX 1-Bit KNX values."""

from __future__ import annotations

from .dpt import DPTEnum, DPTEnumData, EnumDataT
from .payload import DPTBinary


class DPT1BitEnum(DPTEnum[EnumDataT]):
    """Base class for KNX 1-Bit values encoded as Enums."""

    payload_type = DPTBinary
    payload_length = 1
    dpt_main_number = 1


class Switch(DPTEnumData):
    """Enum for switching control."""

    OFF = False
    ON = True


class DPTSwitch(DPT1BitEnum[Switch]):
    """Abstraction for KNX 1-Bit switch value."""

    dpt_main_number = 1
    dpt_sub_number = 1
    value_type = "switch"
    data_type = Switch

    @classmethod
    def _to_knx(cls, value: Switch) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class Bool(DPTEnumData):
    """Enum for switching control."""

    FALSE = False
    TRUE = True


class DPTBool(DPT1BitEnum[Bool]):
    """Abstraction for KNX 1-Bit bool value."""

    dpt_main_number = 1
    dpt_sub_number = 2
    value_type = "bool"
    data_type = Bool

    @classmethod
    def _to_knx(cls, value: Bool) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class Enable(DPTEnumData):
    """Enum for enable control."""

    DISABLE = False
    ENABLE = True


class DPTEnable(DPT1BitEnum[Enable]):
    """Abstraction for KNX 1-Bit enable value."""

    dpt_main_number = 1
    dpt_sub_number = 3
    value_type = "enable"
    data_type = Enable

    @classmethod
    def _to_knx(cls, value: Enable) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class Ramp(DPTEnumData):
    """Enum for ramp control."""

    NO_RAMP = False
    RAMP = True


class DPTRamp(DPT1BitEnum[Ramp]):
    """Abstraction for KNX 1-Bit ramp value."""

    dpt_main_number = 1
    dpt_sub_number = 4
    value_type = "ramp"
    data_type = Ramp

    @classmethod
    def _to_knx(cls, value: Ramp) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class Alarm(DPTEnumData):
    """Enum for alarm control."""

    NO_ALARM = False
    ALARM = True


class DPTAlarm(DPT1BitEnum[Alarm]):
    """Abstraction for KNX 1-Bit alarm value."""

    dpt_main_number = 1
    dpt_sub_number = 5
    value_type = "alarm"
    data_type = Alarm

    @classmethod
    def _to_knx(cls, value: Alarm) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class BinaryValue(DPTEnumData):
    """Enum for binary value control."""

    LOW = False
    HIGH = True


class DPTBinaryValue(DPT1BitEnum[BinaryValue]):
    """Abstraction for KNX 1-Bit binary_value value."""

    dpt_main_number = 1
    dpt_sub_number = 6
    value_type = "binary_value"
    data_type = BinaryValue

    @classmethod
    def _to_knx(cls, value: BinaryValue) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class Step(DPTEnumData):
    """Enum for dimming control."""

    DECREASE = False
    INCREASE = True


class DPTStep(DPT1BitEnum[Step]):
    """Abstraction for KNX 1-Bit step value."""

    dpt_main_number = 1
    dpt_sub_number = 7
    value_type = "step"
    data_type = Step

    @classmethod
    def _to_knx(cls, value: Step) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class UpDown(DPTEnumData):
    """Enum for up/down."""

    UP = False
    DOWN = True


class DPTUpDown(DPT1BitEnum[UpDown]):
    """Abstraction for KNX 1-Bit up/down value."""

    dpt_main_number = 1
    dpt_sub_number = 8
    value_type = "up_down"
    data_type = UpDown

    @classmethod
    def _to_knx(cls, value: UpDown) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class OpenClose(DPTEnumData):
    """Enum for dimming control."""

    OPEN = False
    CLOSE = True


class DPTOpenClose(DPT1BitEnum[OpenClose]):
    """Abstraction for KNX 1-Bit open_close value."""

    dpt_main_number = 1
    dpt_sub_number = 9
    value_type = "open_close"
    data_type = OpenClose

    @classmethod
    def _to_knx(cls, value: OpenClose) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class Start(DPTEnumData):
    """Enum for dimming control."""

    STOP = False
    START = True


class DPTStart(DPT1BitEnum[Start]):
    """Abstraction for KNX 1-Bit start value."""

    dpt_main_number = 1
    dpt_sub_number = 10
    value_type = "start"
    data_type = Start

    @classmethod
    def _to_knx(cls, value: Start) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class State(DPTEnumData):
    """Enum for dimming control."""

    INACTIVE = False
    ACTIVE = True


class DPTState(DPT1BitEnum[State]):
    """Abstraction for KNX 1-Bit state value."""

    dpt_main_number = 1
    dpt_sub_number = 11
    value_type = "state"
    data_type = State

    @classmethod
    def _to_knx(cls, value: State) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class Invert(DPTEnumData):
    """Enum for dimming control."""

    NOT_INVERTED = False
    INVERTED = True


class DPTInvert(DPT1BitEnum[Invert]):
    """Abstraction for KNX 1-Bit invert value."""

    dpt_main_number = 1
    dpt_sub_number = 12
    value_type = "invert"
    data_type = Invert

    @classmethod
    def _to_knx(cls, value: Invert) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class DimSendStyle(DPTEnumData):
    """Enum for dimming control."""

    START_STOP = False
    CYCLICALLY = True


class DPTDimSendStyle(DPT1BitEnum[DimSendStyle]):
    """Abstraction for KNX 1-Bit dim_send_style value."""

    dpt_main_number = 1
    dpt_sub_number = 13
    value_type = "dim_send_style"
    data_type = DimSendStyle

    @classmethod
    def _to_knx(cls, value: DimSendStyle) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class InputSource(DPTEnumData):
    """Enum for dimming control."""

    FIXED = False
    CALCULATED = True


class DPTInputSource(DPT1BitEnum[InputSource]):
    """Abstraction for KNX 1-Bit input_source value."""

    dpt_main_number = 1
    dpt_sub_number = 14
    value_type = "input_source"
    data_type = InputSource

    @classmethod
    def _to_knx(cls, value: InputSource) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class Reset(DPTEnumData):
    """Enum for dimming control."""

    NO_ACTION = False
    RESET = True


class DPTReset(DPT1BitEnum[Reset]):
    """Abstraction for KNX 1-Bit reset value."""

    dpt_main_number = 1
    dpt_sub_number = 15
    value_type = "reset"
    data_type = Reset

    @classmethod
    def _to_knx(cls, value: Reset) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class Ack(DPTEnumData):
    """Enum for dimming control."""

    NO_ACTION = False
    ACKNOWLEDGE = True


class DPTAck(DPT1BitEnum[Ack]):
    """Abstraction for KNX 1-Bit ack value."""

    dpt_main_number = 1
    dpt_sub_number = 16
    value_type = "ack"
    data_type = Ack

    @classmethod
    def _to_knx(cls, value: Ack) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class Trigger(DPTEnumData):
    """Enum for dimming control."""

    TRIGGER_0 = False
    TRIGGER = True


class DPTTrigger(DPT1BitEnum[Trigger]):
    """Abstraction for KNX 1-Bit trigger value."""

    dpt_main_number = 1
    dpt_sub_number = 17
    value_type = "trigger"
    data_type = Trigger

    @classmethod
    def _to_knx(cls, value: Trigger) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class Occupancy(DPTEnumData):
    """Enum for dimming control."""

    NOT_OCCUPIED = False
    OCCUPIED = True


class DPTOccupancy(DPT1BitEnum[Occupancy]):
    """Abstraction for KNX 1-Bit occupancy value."""

    dpt_main_number = 1
    dpt_sub_number = 18
    value_type = "occupancy"
    data_type = Occupancy

    @classmethod
    def _to_knx(cls, value: Occupancy) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class WindowDoor(DPTEnumData):
    """Enum for dimming control."""

    CLOSED = False
    OPEN = True


class DPTWindowDoor(DPT1BitEnum[WindowDoor]):
    """Abstraction for KNX 1-Bit window_door value."""

    dpt_main_number = 1
    dpt_sub_number = 19
    value_type = "window_door"
    data_type = WindowDoor

    @classmethod
    def _to_knx(cls, value: WindowDoor) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class LogicalFunction(DPTEnumData):
    """Enum for dimming control."""

    OR = False
    AND = True


class DPTLogicalFunction(DPT1BitEnum[LogicalFunction]):
    """Abstraction for KNX 1-Bit logical_function value."""

    dpt_main_number = 1
    dpt_sub_number = 21
    value_type = "logical_function"
    data_type = LogicalFunction

    @classmethod
    def _to_knx(cls, value: LogicalFunction) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class SceneAB(DPTEnumData):
    """Enum for dimming control."""

    SCENE_A = False
    SCENE_B = True


class DPTSceneAB(DPT1BitEnum[SceneAB]):
    """Abstraction for KNX 1-Bit scene_ab value."""

    dpt_main_number = 1
    dpt_sub_number = 22
    value_type = "scene_ab"
    data_type = SceneAB

    @classmethod
    def _to_knx(cls, value: SceneAB) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class ShutterBlindsMode(DPTEnumData):
    """Enum for dimming control."""

    UP_DOWN_MODE = False
    STEP_STOP_MODE = True


class DPTShutterBlindsMode(DPT1BitEnum[ShutterBlindsMode]):
    """Abstraction for KNX 1-Bit shutter_blinds_mode value."""

    dpt_main_number = 1
    dpt_sub_number = 23
    value_type = "shutter_blinds_mode"
    data_type = ShutterBlindsMode

    @classmethod
    def _to_knx(cls, value: ShutterBlindsMode) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class DayNight(DPTEnumData):
    """Enum for dimming control."""

    DAY = False
    NIGHT = True


class DPTDayNight(DPT1BitEnum[DayNight]):
    """Abstraction for KNX 1-Bit day_night value."""

    dpt_main_number = 1
    dpt_sub_number = 24
    value_type = "day_night"
    data_type = DayNight

    @classmethod
    def _to_knx(cls, value: DayNight) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class HeatCool(DPTEnumData):
    """Enum for heat/cool."""

    COOL = False
    HEAT = True


class DPTHeatCool(DPT1BitEnum[HeatCool]):
    """Abstraction for KNX 1-Bit heat/cool value."""

    dpt_main_number = 1
    dpt_sub_number = 100
    value_type = "heat_cool"
    data_type = HeatCool

    @classmethod
    def _to_knx(cls, value: HeatCool) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class ConsumerProducer(DPTEnumData):
    """Enum for dimming control."""

    CONSUMER = False
    PRODUCER = True


class DPTConsumerProducer(DPT1BitEnum[ConsumerProducer]):
    """Abstraction for KNX 1-Bit consumer_producer value."""

    dpt_main_number = 1
    dpt_sub_number = 1200
    value_type = "consumer_producer"
    data_type = ConsumerProducer

    @classmethod
    def _to_knx(cls, value: ConsumerProducer) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class EnergyDirection(DPTEnumData):
    """Enum for dimming control."""

    POSITIVE = False
    NEGATIVE = True


class DPTEnergyDirection(DPT1BitEnum[EnergyDirection]):
    """Abstraction for KNX 1-Bit energy_direction value."""

    dpt_main_number = 1
    dpt_sub_number = 1201
    value_type = "energy_direction"
    data_type = EnergyDirection

    @classmethod
    def _to_knx(cls, value: EnergyDirection) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)
