"""
Module for managing an 1 count remote value.

DPT 6.010.
"""
from __future__ import annotations

from xknx.dpt import DPTArray, DPTBinary, DPTValue1Count

from .remote_value import RemoteValue


class RemoteValue1Count(RemoteValue[int]):
    """Abstraction for remote value of KNX 6.010 (DPT_Value_1_Count)."""

    def to_knx(self, value: int) -> DPTArray:
        """Convert value to payload."""
        return DPTValue1Count.to_knx(value)

    def from_knx(self, payload: DPTArray | DPTBinary) -> int:
        """Convert current payload to value."""
        return DPTValue1Count.from_knx(payload)
