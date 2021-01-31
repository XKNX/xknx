"""
Module for managing an DPT Switch remote value.

DPT 1.001.
"""
from typing import TYPE_CHECKING, List, Optional, Union

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import AsyncCallbackType, RemoteValue

if TYPE_CHECKING:
    from xknx.telegram.address import GroupAddressableType
    from xknx.xknx import XKNX


class RemoteValueSwitch(RemoteValue[DPTBinary]):
    """Abstraction for remote value of KNX DPT 1.001 / DPT_Switch."""

    def __init__(
        self,
        xknx: "XKNX",
        group_address: Optional["GroupAddressableType"] = None,
        group_address_state: Optional["GroupAddressableType"] = None,
        sync_state: bool = True,
        device_name: Optional[str] = None,
        feature_name: str = "State",
        after_update_cb: Optional[AsyncCallbackType] = None,
        invert: bool = False,
        passive_group_addresses: Optional[List["GroupAddressableType"]] = None,
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

    def payload_valid(
        self, payload: Optional[Union[DPTArray, DPTBinary]]
    ) -> Optional[DPTBinary]:
        """Test if telegram payload may be parsed."""
        # pylint: disable=no-self-use
        return payload if isinstance(payload, DPTBinary) else None

    def to_knx(self, value: bool) -> DPTBinary:
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
