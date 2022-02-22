"""
Module for managing a remote temperature value.

DPT 9.001.
"""
from __future__ import annotations

from xknx.dpt import DPTArray, DPTBinary, DPTTemperature
from xknx.exceptions import CouldNotParseTelegram

from .remote_value import RemoteValue


class RemoteValueTemp(RemoteValue[DPTArray, float]):
    """Abstraction for remote value of KNX 9.001 (DPT_Value_Temp)."""

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTArray) and len(payload.value) == 2:
            return payload
        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))

    def to_knx(self, value: float) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(DPTTemperature.to_knx(value))

    def from_knx(self, payload: DPTArray) -> float:
        """Convert current payload to value."""
        return DPTTemperature.from_knx(payload.value)
