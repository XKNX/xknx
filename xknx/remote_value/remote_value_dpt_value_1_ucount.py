"""
Module for managing a DTP 5010 remote value.

DPT 5.010.
"""
from __future__ import annotations

from xknx.dpt import DPTArray, DPTBinary, DPTValue1Ucount

from .remote_value import RemoteValue


class RemoteValueDptValue1Ucount(RemoteValue[int]):
    """Abstraction for remote value of KNX DPT 5.010."""

    def to_knx(self, value: int) -> DPTArray:
        """Convert value to payload."""
        return DPTValue1Ucount.to_knx(value)

    def from_knx(self, payload: DPTArray | DPTBinary) -> int:
        """Convert current payload to value."""
        return DPTValue1Ucount.from_knx(payload)
