"""
Module for managing a remote string value.

DPT 16.000
"""
from __future__ import annotations

from xknx.dpt import DPTArray, DPTBinary, DPTString

from .remote_value import RemoteValue


class RemoteValueString(RemoteValue[DPTArray, str]):
    """Abstraction for remote value of KNX 16.000 (DPT_String_ASCII)."""

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray | None:
        """Test if telegram payload may be parsed."""
        return (
            payload
            if isinstance(payload, DPTArray)
            and len(payload.value) == DPTString.payload_length
            else None
        )

    def to_knx(self, value: str) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(DPTString.to_knx(value))

    def from_knx(self, payload: DPTArray) -> str:
        """Convert current payload to value."""
        return DPTString.from_knx(payload.value)
