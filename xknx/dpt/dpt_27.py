"""Implementation of KNX DPT 27 Combined Info On Off."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary

_OUTPUT_COUNT: Final = 16
_OUTPUT_FIELDS: Final = tuple(f"output_{n}" for n in range(1, _OUTPUT_COUNT + 1))


@dataclass(slots=True)
class CombinedInfoOnOff(DPTComplexData):
    """
    Representation of the combined On/Off state of up to 16 outputs.

    `output_1` .. `output_16`: True if the output is On, False if it is Off;
    None if its state is not valid (mask bit 0) - eg. the output is not used.
    """

    output_1: bool | None = None
    output_2: bool | None = None
    output_3: bool | None = None
    output_4: bool | None = None
    output_5: bool | None = None
    output_6: bool | None = None
    output_7: bool | None = None
    output_8: bool | None = None
    output_9: bool | None = None
    output_10: bool | None = None
    output_11: bool | None = None
    output_12: bool | None = None
    output_13: bool | None = None
    output_14: bool | None = None
    output_15: bool | None = None
    output_16: bool | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CombinedInfoOnOff:
        """Init from a dictionary."""
        states: dict[str, bool | None] = {}
        for name in _OUTPUT_FIELDS:
            try:
                state = data.get(name)
            except AttributeError as err:
                raise ValueError(f"Invalid value for CombinedInfoOnOff: {err}") from err
            if state is not None and not isinstance(state, bool):
                raise ValueError(
                    f"Invalid value for CombinedInfoOnOff `{name}`: {state}"
                )
            states[name] = state
        return cls(**states)

    def as_dict(self) -> dict[str, bool | None]:
        """Create a JSON serializable dictionary."""
        return {name: getattr(self, name) for name in _OUTPUT_FIELDS}


class DPTCombinedInfoOnOff(DPTComplex[CombinedInfoOnOff]):
    """
    Abstraction for KNX 4 octet Combined Info On Off (DPT 27.001).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.26.1
    Bit 0..15 (s0..s15) carry the state of output 1..16, bit 16..31 (m0..m15)
    whether that state is valid. Bit 0 is the LSB of the last octet.
    """

    data_type = CombinedInfoOnOff
    payload_type = DPTArray
    payload_length = 4
    dpt_main_number = 27
    dpt_sub_number = 1
    value_type = "combined_info_on_off"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> CombinedInfoOnOff:
        """Parse/deserialize from KNX/IP raw data."""
        raw = int.from_bytes(cls.validate_payload(payload), "big")
        states = raw & 0xFFFF
        masks = raw >> _OUTPUT_COUNT
        return CombinedInfoOnOff(
            **{
                name: bool(states >> bit & 1) if masks >> bit & 1 else None
                for bit, name in enumerate(_OUTPUT_FIELDS)
            }
        )

    @classmethod
    def _to_knx(cls, value: CombinedInfoOnOff) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        states = 0
        masks = 0
        for bit, name in enumerate(_OUTPUT_FIELDS):
            state = getattr(value, name)
            if state is None:
                # state bit of a not valid output is sent as 0
                continue
            if not isinstance(state, bool):
                raise ValueError(f"Invalid value for `{name}`: {state}")
            masks |= 1 << bit
            states |= state << bit
        return DPTArray((masks << _OUTPUT_COUNT | states).to_bytes(4, "big"))
