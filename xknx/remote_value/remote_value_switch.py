"""
Module for managing an DPT Switch remote value.

DPT 1.001.
"""
from typing import List, Optional

from xknx.dpt import DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import RemoteValue


class RemoteValueSwitch(RemoteValue):
    """Abstraction for remote value of KNX DPT 1.001 / DPT_Switch."""

    def __init__(
        self,
        xknx,
        group_address=None,
        group_address_state=None,
        sync_state: bool = True,
        device_name: str = None,
        feature_name: str = "State",
        after_update_cb=None,
        invert: Optional[bool] = False,
        passive_group_addresses: List[str] = None,
    ):
        """Initialize remote value of KNX DPT 1.001."""
        # pylint: disable=too-many-arguments
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
            passive_group_addresses=passive_group_addresses,
        )
        self.invert = bool(invert)

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    def to_knx(self, value: bool):
        """Convert value to payload."""
        if isinstance(value, bool):
            return DPTBinary(value ^ self.invert)
        raise ConversionError(
            "value invalid",
            value=value,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    def from_knx(self, payload: DPTBinary) -> bool:
        """Convert current payload to value."""
        if payload == DPTBinary(0):
            return self.invert
        if payload == DPTBinary(1):
            return not self.invert
        raise CouldNotParseTelegram(
            "payload invalid",
            payload=payload,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    async def off(self) -> None:
        """Set value to OFF."""
        await self.set(False)

    async def on(self) -> None:
        """Set value to ON."""
        # pylint: disable=invalid-name
        await self.set(True)
