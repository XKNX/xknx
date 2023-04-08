"""
Module for managing a DTP Scene Number remote value.

DPT 17.001.
"""
from __future__ import annotations

from xknx.dpt import DPTArray, DPTBinary, DPTSceneNumber

from .remote_value import RemoteValue


class RemoteValueSceneNumber(RemoteValue[int]):
    """Abstraction for remote value of KNX DPT 17.001 (DPT_Scene_Number)."""

    def to_knx(self, value: int) -> DPTArray:
        """Convert value to payload."""
        return DPTSceneNumber.to_knx(value)

    def from_knx(self, payload: DPTArray | DPTBinary) -> int:
        """Convert current payload to value."""
        return DPTSceneNumber.from_knx(payload)
