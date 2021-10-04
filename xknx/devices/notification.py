"""Module for managing a notification via KNX."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterator

from xknx.remote_value import GroupAddressesType, RemoteValueString

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Notification(Device):
    """Class for managing a notification."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        device_updated_cb: DeviceCallbackType | None = None,
    ):
        """Initialize notification class."""
        super().__init__(xknx, name, device_updated_cb)

        self._message = RemoteValueString(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            device_name=name,
            feature_name="Message",
            after_update_cb=self.after_update,
        )

    def _iter_remote_values(self) -> Iterator[RemoteValueString]:
        """Iterate the devices RemoteValue classes."""
        yield self._message

    @property
    def message(self) -> str | None:
        """Return the current message."""
        return self._message.value

    async def set(self, message: str) -> None:
        """Set message."""
        cropped_message = message[:14]
        await self._message.set(cropped_message)

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        await self._message.process(telegram)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<Notification name="{self.name}" message={self._message.group_addr_str()} />'
