"""
Module for managing a DTP Scene Number remote value.

DPT 17.001.
"""
from typing import Optional, Union

from xknx.dpt import DPTArray, DPTBinary, DPTSceneNumber

from .remote_value import RemoteValue


class RemoteValueSceneNumber(RemoteValue[DPTArray]):
    """Abstraction for remote value of KNX DPT 17.001 (DPT_Scene_Number)."""

    # pylint: disable=no-self-use

    def payload_valid(
        self, payload: Optional[Union[DPTArray, DPTBinary]]
    ) -> Optional[DPTArray]:
        """Test if telegram payload may be parsed."""
        return (
            payload
            if isinstance(payload, DPTArray) and len(payload.value) == 1
            else None
        )

    def to_knx(self, value: int) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(DPTSceneNumber.to_knx(value))

    def from_knx(self, payload: DPTArray) -> int:
        """Convert current payload to value."""
        return DPTSceneNumber.from_knx(payload.value)
