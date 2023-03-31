"""
Module for managing a remote temperature value.

DPT 9.001.
"""
from __future__ import annotations

from xknx.dpt import DPTArray, DPTBinary, DPTTemperature

from .remote_value import RemoteValue


class RemoteValueTemp(RemoteValue[float]):
    """Abstraction for remote value of KNX 9.001 (DPT_Value_Temp)."""

    def to_knx(self, value: float) -> DPTArray:
        """Convert value to payload."""
        return DPTTemperature.to_knx(value)

    def from_knx(self, payload: DPTArray | DPTBinary) -> float:
        """Convert current payload to value."""
        return DPTTemperature.from_knx(payload)
