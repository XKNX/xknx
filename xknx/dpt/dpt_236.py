"""Implementation of KNX DPT 236 Prioritised Mode Control."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class PrioritisedModeControl(DPTComplexData):
    """
    Representation of Prioritised Mode Control.

    `priority_level`: int 0..7; 0 is the lowest priority
    `mode_level`: int 0..15; 0 is the "normal behaviour"
    `deactivate_priority`: bool; True deactivates the priority level
    """

    priority_level: int = field(metadata={"value_min": 0, "value_max": 7})
    mode_level: int = field(metadata={"value_min": 0, "value_max": 15})
    deactivate_priority: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PrioritisedModeControl:
        """Init from a dictionary."""
        try:
            priority_level = int(data["priority_level"])
            mode_level = int(data["mode_level"])
            deactivate_priority = data.get("deactivate_priority", False)
        except (KeyError, TypeError, ValueError, AttributeError) as err:
            raise ValueError(
                f"Invalid value for PrioritisedModeControl: {err}"
            ) from err
        if deactivate_priority not in (True, False):
            raise ValueError(
                "Invalid value for PrioritisedModeControl value "
                f"`deactivate_priority`: {deactivate_priority}"
            )
        return cls(
            priority_level=priority_level,
            mode_level=mode_level,
            deactivate_priority=bool(deactivate_priority),
        )

    def as_dict(self) -> dict[str, int | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "priority_level": self.priority_level,
            "mode_level": self.mode_level,
            "deactivate_priority": self.deactivate_priority,
        }


class DPTPrioritisedModeControl(DPTComplex[PrioritisedModeControl]):
    """
    Abstraction for KNX 1 Octet Prioritised Mode Control.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.49
    DPT 236.001
    """

    data_type = PrioritisedModeControl
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 236
    dpt_sub_number = 1
    value_type = "prioritised_mode_control"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> PrioritisedModeControl:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)[0]
        return PrioritisedModeControl(
            priority_level=raw >> 4 & 0b111,
            mode_level=raw & 0b1111,
            deactivate_priority=bool(raw & 0x80),
        )

    @classmethod
    def _to_knx(cls, value: PrioritisedModeControl) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= value.priority_level <= 7:
            raise ValueError(
                f"Priority level out of range 0..7: {value.priority_level}"
            )
        if not 0 <= value.mode_level <= 15:
            raise ValueError(f"Mode level out of range 0..15: {value.mode_level}")
        return DPTArray(
            value.deactivate_priority << 7
            | value.priority_level << 4
            | value.mode_level
        )
