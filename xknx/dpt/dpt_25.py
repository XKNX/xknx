"""Implementation of KNX DPT 25 double nibbles."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary

_REPETITIONS_MAX = 3


@dataclass(slots=True)
class DoubleNibble(DPTComplexData):
    """
    Representation of busy and nak repetitions.

    `busy`: int 0..3; number of busy repetitions.
    `nak`: int 0..3; number of nak repetitions.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.4
    """

    busy: int = field(metadata={"value_min": 0, "value_max": _REPETITIONS_MAX})
    nak: int = field(metadata={"value_min": 0, "value_max": _REPETITIONS_MAX})

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DoubleNibble:
        """Init from a dictionary."""
        try:
            busy = int(data["busy"])
            nak = int(data["nak"])
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for DoubleNibble: {err}") from err
        return cls(busy=busy, nak=nak)

    def as_dict(self) -> dict[str, int]:
        """Create a JSON serializable dictionary."""
        return {
            "busy": self.busy,
            "nak": self.nak,
        }


class DPTDoubleNibble(DPTComplex[DoubleNibble]):
    """Abstraction for KNX 1 octet busy and nak repetitions (DPT 25.1000)."""

    data_type = DoubleNibble
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 25
    dpt_sub_number = 1000
    value_type = "double_nibble"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> DoubleNibble:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)[0]
        busy = raw >> 4
        nak = raw & 0x0F
        if busy > _REPETITIONS_MAX or nak > _REPETITIONS_MAX:
            raise ConversionError(
                f"Could not parse {cls.dpt_name()}: repetitions out of range 0..3",
                payload=payload,
            )
        return DoubleNibble(busy=busy, nak=nak)

    @classmethod
    def _to_knx(cls, value: DoubleNibble) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        for name, repetitions in (("busy", value.busy), ("nak", value.nak)):
            if not isinstance(repetitions, int) or not (
                0 <= repetitions <= _REPETITIONS_MAX
            ):
                raise ConversionError(
                    f"{name} out of range 0..{_REPETITIONS_MAX}: {repetitions}",
                    value=value,
                )
        return DPTArray(value.busy << 4 | value.nak)
