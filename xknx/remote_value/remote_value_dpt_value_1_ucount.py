"""
Module for managing a DTP 5010 remote value.

DPT 5.010.
"""
from __future__ import annotations

from xknx.dpt import DPTArray, DPTBinary, DPTValue1Ucount
from xknx.exceptions import CouldNotParseTelegram

from .remote_value import RemoteValue


class RemoteValueDptValue1Ucount(RemoteValue[DPTArray, int]):
    """Abstraction for remote value of KNX DPT 5.010."""

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTArray) and len(payload.value) == 1:
            return payload
        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))

    def to_knx(self, value: int) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(DPTValue1Ucount.to_knx(value))

    def from_knx(self, payload: DPTArray) -> int:
        """Convert current payload to value."""
        return DPTValue1Ucount.from_knx(payload.value)
