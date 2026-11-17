"""Implementation of Basic KNX 1-Byte signed integer values and DPT 6.020."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData, DPTNumeric
from .payload import DPTArray, DPTBinary


class DPTSignedRelativeValue(DPTNumeric):
    """
    Abstraction for KNX 1 Byte "1-octet Signed Relative Value".

    DPT 6.***
    """

    dpt_main_number = 6
    dpt_sub_number: int | None = None
    value_type = "1byte_signed"
    payload_length = 1

    value_min = -128
    value_max = 127
    resolution = 1

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        if raw[0] > cls.value_max:
            return raw[0] - 0x100
        return raw[0]

    @classmethod
    def to_knx(cls, value: int | float) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError("Value out of range")
            if knx_value < 0:
                knx_value += 0x100
            return DPTArray(knx_value & 0xFF)
        except ValueError as err:
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}", value=value
            ) from err

    @classmethod
    def _test_boundaries(cls, value: int) -> bool:
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTPercentV8(DPTSignedRelativeValue):
    """
    Abstraction for KNX DPT_Percent_V8.

    DPT 6.001
    """

    dpt_main_number = 6
    dpt_sub_number = 1
    value_type = "percentV8"
    unit = "%"


class DPTValue1Count(DPTSignedRelativeValue):
    """
    Abstraction for KNX DPT_Value_1_Count.

    DPT 6.010
    """

    dpt_main_number = 6
    dpt_sub_number = 10
    value_type = "counter_pulses"
    unit = "counter pulses"


# status bits a to e, from the most significant bit
_STATUS_BITS = {
    "status_a": 7,
    "status_b": 6,
    "status_c": 5,
    "status_d": 4,
    "status_e": 3,
}
_MODE_MASK = 0b111


@dataclass(slots=True)
class StatusMode3(DPTComplexData):
    """
    Representation of a status with mode (DPT 6.020 DPT_Status_Mode3).

    `status_a` to `status_e`: bool - `True` if the status is set
    `mode`: int 0..2 - the active mode
    """

    status_a: bool
    status_b: bool
    status_c: bool
    status_d: bool
    status_e: bool
    mode: int = field(metadata={"value_min": 0, "value_max": 2})

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> StatusMode3:
        """Init from a dictionary."""
        try:
            status = {name: data[name] for name in _STATUS_BITS}
            mode = data["mode"]
        except (KeyError, TypeError) as err:
            raise ValueError(f"Invalid value for StatusMode3: {err}") from err
        for name, value in status.items():
            if not isinstance(value, bool):
                raise ValueError(f"Invalid value for StatusMode3 `{name}`: {value!r}")
        if isinstance(mode, bool) or mode not in (0, 1, 2):
            raise ValueError(f"Invalid value for StatusMode3 `mode`: {mode!r}")
        return cls(**status, mode=mode)

    def as_dict(self) -> dict[str, int | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "status_a": self.status_a,
            "status_b": self.status_b,
            "status_c": self.status_c,
            "status_d": self.status_d,
            "status_e": self.status_e,
            "mode": self.mode,
        }


class DPTStatusMode3(DPTComplex[StatusMode3]):
    """
    Abstraction for KNX status with mode (DPT 6.020 DPT_Status_Mode3).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.7: the status bits a to e
    are 0 when set and 1 when clear; the mode field holds exactly one bit,
    001b for mode 0, 010b for mode 1 and 100b for mode 2.
    """

    data_type = StatusMode3
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 6
    dpt_sub_number = 20
    value_type = "status_mode3"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> StatusMode3:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)[0]
        mode_bits = raw & _MODE_MASK
        if mode_bits not in (0b001, 0b010, 0b100):
            raise ConversionError(f"Invalid mode bits for {cls.dpt_name()}", raw=raw)
        return StatusMode3(
            **{name: not raw >> bit & 1 for name, bit in _STATUS_BITS.items()},
            mode=mode_bits.bit_length() - 1,
        )

    @classmethod
    def _to_knx(cls, value: StatusMode3) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if isinstance(value.mode, bool) or value.mode not in (0, 1, 2):
            raise ValueError(f"Invalid value for `mode`: {value.mode!r}")
        raw = 1 << value.mode
        for name, bit in _STATUS_BITS.items():
            status = getattr(value, name)
            if not isinstance(status, bool):
                raise ValueError(f"Invalid value for `{name}`: {status!r}")
            if not status:
                raw |= 1 << bit
        return DPTArray(raw)
