"""
Module for managing an 1 count remote value.

DPT 6.010.
"""
from __future__ import annotations

from xknx.dpt import DPTArray, DPTBinary, DPTValue1Count

from .remote_value import RemoteValue


class RemoteValue1Count(RemoteValue[DPTArray, int]):
    """Abstraction for remote value of KNX 6.010 (DPT_Value_1_Count)."""

    # pylint: disable=no-self-use

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray | None:
        """Test if telegram payload may be parsed."""
        return (
            payload
            if isinstance(payload, DPTArray) and len(payload.value) == 1
            else None
        )

    def to_knx(self, value: int) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(DPTValue1Count.to_knx(value))

    def from_knx(self, payload: DPTArray) -> int:
        """Convert current payload to value."""
        return DPTValue1Count.from_knx(payload.value)
