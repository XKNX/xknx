"""Implementation of KNX DPT 2 2-bit control."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, Generic, TypeVar

from .dpt import DPTComplex, DPTComplexData, DPTEnumData
from .dpt_1 import (
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
from .payload import DPTArray, DPTBinary

_ValueT_co = TypeVar("_ValueT_co", bound=DPTEnumData, covariant=True)
_BinaryControlDataT = TypeVar(
    "_BinaryControlDataT", bound="_BinaryControlDataMixin[Any]"
)


@dataclass(slots=True)
class _BinaryControlDataMixin(Generic[_ValueT_co], DPTComplexData):
    """Mixin for BinaryControl dataclasses providing shared from_dict and as_dict."""

    _value_type: ClassVar[type[DPTEnumData]]
    control: bool
    value: _ValueT_co

    @classmethod
    def from_raw(cls: type[_BinaryControlDataT], raw: int) -> _BinaryControlDataT:
        """Init from a 2-bit raw value."""
        return cls(
            control=bool((raw >> 1) & 1),
            value=cls._value_type(bool(raw & 1)),
        )

    @classmethod
    def from_dict(
        cls: type[_BinaryControlDataT], data: Mapping[str, Any]
    ) -> _BinaryControlDataT:
        """Init from a dictionary."""
        try:
            control = bool(data["control"])
            value = cls._value_type.parse(
                # default to False if not provided since no-control could ignore value anyway
                data.get("value", False)
            )
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for {cls.__name__}: {err}") from err
        return cls(control=control, value=value)

    def as_dict(self) -> dict[str, bool | str]:
        """Create a JSON serializable dictionary."""
        return {
            "control": self.control,
            "value": self.value.name.lower(),
        }


@dataclass(slots=True)
class SwitchControl(_BinaryControlDataMixin[Switch]):
    """2-bit DPT 2.001 Switch Control value."""

    _value_type = Switch
    value: Switch


@dataclass(slots=True)
class BoolControl(_BinaryControlDataMixin[Bool]):
    """2-bit DPT 2.002 Bool Control value."""

    _value_type = Bool
    value: Bool


@dataclass(slots=True)
class EnableControl(_BinaryControlDataMixin[Enable]):
    """2-bit DPT 2.003 Enable Control value."""

    _value_type = Enable
    value: Enable


@dataclass(slots=True)
class RampControl(_BinaryControlDataMixin[Ramp]):
    """2-bit DPT 2.004 Ramp Control value."""

    _value_type = Ramp
    value: Ramp


@dataclass(slots=True)
class AlarmControl(_BinaryControlDataMixin[Alarm]):
    """2-bit DPT 2.005 Alarm Control value."""

    _value_type = Alarm
    value: Alarm


@dataclass(slots=True)
class BinaryValueControl(_BinaryControlDataMixin[BinaryValue]):
    """2-bit DPT 2.006 Binary Value Control value."""

    _value_type = BinaryValue
    value: BinaryValue


@dataclass(slots=True)
class StepControl(_BinaryControlDataMixin[Step]):
    """2-bit DPT 2.007 Step Control value."""

    _value_type = Step
    value: Step


@dataclass(slots=True)
class Direction1Control(_BinaryControlDataMixin[UpDown]):
    """2-bit DPT 2.008 Direction1 Control value."""

    _value_type = UpDown
    value: UpDown


@dataclass(slots=True)
class Direction2Control(_BinaryControlDataMixin[UpDown]):
    """2-bit DPT 2.009 Direction2 Control value."""

    _value_type = UpDown
    value: UpDown


@dataclass(slots=True)
class StartControl(_BinaryControlDataMixin[Start]):
    """2-bit DPT 2.010 Start Control value."""

    _value_type = Start
    value: Start


@dataclass(slots=True)
class StateControl(_BinaryControlDataMixin[State]):
    """2-bit DPT 2.011 State Control value."""

    _value_type = State
    value: State


@dataclass(slots=True)
class InvertControl(_BinaryControlDataMixin[Invert]):
    """2-bit DPT 2.012 Invert Control value."""

    _value_type = Invert
    value: Invert


_BinaryControlT = TypeVar(
    "_BinaryControlT", bound="_BinaryControlDataMixin[DPTEnumData]"
)


class _DPTBinaryControlBase(DPTComplex[_BinaryControlT], Generic[_BinaryControlT]):
    """
    Shared base for KNX DPT 2 2-bit binary control transcoding.

    Format: B2 — MSB = control bit (c), LSB = value bit (v).
    Encoding: raw = (c << 1) | v.

    Keeping _to_knx abstract ensures this base class is skipped by
    DPTBase.dpt_class_tree() (same pattern as DPTEnum).
    """

    payload_type = DPTBinary
    payload_length = 2
    dpt_main_number = 2

    @staticmethod
    def _encode_binary_control(value: _BinaryControlT) -> DPTBinary:
        """Encode a BinaryControl dataclass instance to a 2-bit DPTBinary payload."""
        return DPTBinary((value.control << 1) | value.value.value)

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> _BinaryControlT:
        """Parse/deserialize from KNX/IP payload data."""
        raw = cls.validate_payload(payload)[0]
        return cls.data_type.from_raw(raw)

    @classmethod
    @abstractmethod
    def _to_knx(cls, value: _BinaryControlT) -> DPTBinary:
        """Serialize to KNX/IP raw data. Subclasses call cls._encode_binary_control(value)."""


class DPTSwitchControl(_DPTBinaryControlBase[SwitchControl]):
    """Abstraction for KNX 2-bit switch control. DPT 2.001."""

    data_type = SwitchControl
    dpt_main_number = 2
    dpt_sub_number = 1
    value_type = "switch_control"

    @classmethod
    def _to_knx(cls, value: SwitchControl) -> DPTBinary:
        return cls._encode_binary_control(value)


class DPTBoolControl(_DPTBinaryControlBase[BoolControl]):
    """Abstraction for KNX 2-bit bool control. DPT 2.002."""

    data_type = BoolControl
    dpt_main_number = 2
    dpt_sub_number = 2
    value_type = "bool_control"

    @classmethod
    def _to_knx(cls, value: BoolControl) -> DPTBinary:
        return cls._encode_binary_control(value)


class DPTEnableControl(_DPTBinaryControlBase[EnableControl]):
    """Abstraction for KNX 2-bit enable control. DPT 2.003."""

    data_type = EnableControl
    dpt_main_number = 2
    dpt_sub_number = 3
    value_type = "enable_control"

    @classmethod
    def _to_knx(cls, value: EnableControl) -> DPTBinary:
        return cls._encode_binary_control(value)


class DPTRampControl(_DPTBinaryControlBase[RampControl]):
    """Abstraction for KNX 2-bit ramp control. DPT 2.004."""

    data_type = RampControl
    dpt_main_number = 2
    dpt_sub_number = 4
    value_type = "ramp_control"

    @classmethod
    def _to_knx(cls, value: RampControl) -> DPTBinary:
        return cls._encode_binary_control(value)


class DPTAlarmControl(_DPTBinaryControlBase[AlarmControl]):
    """Abstraction for KNX 2-bit alarm control. DPT 2.005."""

    data_type = AlarmControl
    dpt_main_number = 2
    dpt_sub_number = 5
    value_type = "alarm_control"

    @classmethod
    def _to_knx(cls, value: AlarmControl) -> DPTBinary:
        return cls._encode_binary_control(value)


class DPTBinaryValueControl(_DPTBinaryControlBase[BinaryValueControl]):
    """Abstraction for KNX 2-bit binary value control. DPT 2.006."""

    data_type = BinaryValueControl
    dpt_main_number = 2
    dpt_sub_number = 6
    value_type = "binary_value_control"

    @classmethod
    def _to_knx(cls, value: BinaryValueControl) -> DPTBinary:
        return cls._encode_binary_control(value)


class DPTStepControl(_DPTBinaryControlBase[StepControl]):
    """Abstraction for KNX 2-bit step control. DPT 2.007."""

    data_type = StepControl
    dpt_main_number = 2
    dpt_sub_number = 7
    value_type = "step_control"

    @classmethod
    def _to_knx(cls, value: StepControl) -> DPTBinary:
        return cls._encode_binary_control(value)


class DPTDirection1Control(_DPTBinaryControlBase[Direction1Control]):
    """Abstraction for KNX 2-bit direction1 control. DPT 2.008."""

    data_type = Direction1Control
    dpt_main_number = 2
    dpt_sub_number = 8
    value_type = "direction1_control"

    @classmethod
    def _to_knx(cls, value: Direction1Control) -> DPTBinary:
        return cls._encode_binary_control(value)


class DPTDirection2Control(_DPTBinaryControlBase[Direction2Control]):
    """Abstraction for KNX 2-bit direction2 control. DPT 2.009."""

    data_type = Direction2Control
    dpt_main_number = 2
    dpt_sub_number = 9
    value_type = "direction2_control"

    @classmethod
    def _to_knx(cls, value: Direction2Control) -> DPTBinary:
        return cls._encode_binary_control(value)


class DPTStartControl(_DPTBinaryControlBase[StartControl]):
    """Abstraction for KNX 2-bit start control. DPT 2.010."""

    data_type = StartControl
    dpt_main_number = 2
    dpt_sub_number = 10
    value_type = "start_control"

    @classmethod
    def _to_knx(cls, value: StartControl) -> DPTBinary:
        return cls._encode_binary_control(value)


class DPTStateControl(_DPTBinaryControlBase[StateControl]):
    """Abstraction for KNX 2-bit state control. DPT 2.011."""

    data_type = StateControl
    dpt_main_number = 2
    dpt_sub_number = 11
    value_type = "state_control"

    @classmethod
    def _to_knx(cls, value: StateControl) -> DPTBinary:
        return cls._encode_binary_control(value)


class DPTInvertControl(_DPTBinaryControlBase[InvertControl]):
    """Abstraction for KNX 2-bit invert control. DPT 2.012."""

    data_type = InvertControl
    dpt_main_number = 2
    dpt_sub_number = 12
    value_type = "invert_control"

    @classmethod
    def _to_knx(cls, value: InvertControl) -> DPTBinary:
        return cls._encode_binary_control(value)
