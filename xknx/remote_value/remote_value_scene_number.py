"""
Module for managing a DTP Scene Number remote value.

DPT 17.001.
"""
from __future__ import annotations

from xknx.dpt import DPTArray, DPTBinary, DPTSceneNumber
from xknx.exceptions import CouldNotParseTelegram

from .remote_value import RemoteValue


class RemoteValueSceneNumber(RemoteValue[DPTArray, int]):
    """Abstraction for remote value of KNX DPT 17.001 (DPT_Scene_Number)."""

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTArray) and len(payload.value) == 1:
            return payload
        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))

    def to_knx(self, value: int) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(DPTSceneNumber.to_knx(value))

    def from_knx(self, payload: DPTArray) -> int:
        """Convert current payload to value."""
        return DPTSceneNumber.from_knx(payload.value)
