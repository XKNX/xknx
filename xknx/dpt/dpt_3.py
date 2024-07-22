"""Implementation of KNX DPT 3 4-bit control."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData
from .dpt_1 import Step, UpDown
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class ControlDimming(DPTComplexData):
    """
    Class for dimming control.

    Range is subdivided into `2**(step_code-1)`; `step_code=0` indicates break.
    """

    control: Step
    step_code: int  # 1..7 higher is more intervals -> slower; 0 stop

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ControlDimming:
        """Init from a dictionary."""
        try:
            control = Step.parse(data["control"])
            step_code = int(data["step_code"])
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for ControlDimming: {err}") from err
        return cls(control=control, step_code=step_code)

    def as_dict(self) -> dict[str, int | str]:
        """Create a JSON serializable dictionary."""
        return {
            "control": self.control.name.lower(),
            "step_code": self.step_code,
        }


class DPTControlDimming(DPTComplex[ControlDimming]):
    """
    Abstraction for KNX 4-Bit dimming control.

    DPT 3.007
    """

    data_type = ControlDimming
    payload_type = DPTBinary
    payload_length = 4
    dpt_main_number = 3
    dpt_sub_number = 7
    value_type = "control_dimming"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ControlDimming:
        """Parse/deserialize from KNX/IP payload data."""
        raw = cls.validate_payload(payload)[0]
        return ControlDimming(
            control=Step((raw & 0b1000) >> 3),
            step_code=raw & 0b0111,
        )

    @classmethod
    def _to_knx(cls, value: ControlDimming) -> DPTBinary:
        """Serialize to KNX/IP raw data."""
        if not 0 <= value.step_code <= 7:
            raise ConversionError("Invalid value for step_code: must be 0..7")
        return DPTBinary(value.control.value << 3 | value.step_code)


@dataclass(slots=True)
class ControlBlinds(DPTComplexData):
    """
    Class for blinds control.

    Range is subdivided into `2**(step_code-1)`; `step_code=0` indicates break.
    """

    control: UpDown
    step_code: int  # 1..7 higher is more intervals -> slower; 0 stop

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ControlBlinds:
        """Init from a dictionary."""
        try:
            control = UpDown.parse(data["control"])
            step_code = int(data["step_code"])
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for ControlBlinds: {err}") from err
        return cls(control=control, step_code=step_code)

    def as_dict(self) -> dict[str, int | str]:
        """Create a JSON serializable dictionary."""
        return {
            "control": self.control.name.lower(),
            "step_code": self.step_code,
        }


class DPTControlBlinds(DPTComplex[ControlBlinds]):
    """
    Abstraction for KNX 4-Bit dimming control.

    DPT 3.008
    """

    data_type = ControlBlinds
    payload_type = DPTBinary
    payload_length = 4
    dpt_main_number = 3
    dpt_sub_number = 8
    value_type = "control_blinds"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ControlBlinds:
        """Parse/deserialize from KNX/IP payload data."""
        raw = cls.validate_payload(payload)[0]
        return ControlBlinds(
            control=UpDown((raw & 0b1000) >> 3),
            step_code=raw & 0b0111,
        )

    @classmethod
    def _to_knx(cls, value: ControlBlinds) -> DPTBinary:
        """Serialize to KNX/IP raw data."""
        if not 0 <= value.step_code <= 7:
            raise ConversionError("Invalid value for step_code: must be 0..7")
        return DPTBinary(value.control.value << 3 | value.step_code)
