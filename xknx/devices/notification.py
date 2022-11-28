"""Module for managing a text via KNX."""
from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from xknx.remote_value import GroupAddressesType, RemoteValueString

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX


class Notification(Device):
    """Class for managing a notification."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        respond_to_read: bool = False,
        sync_state: bool | int | float | str = True,
        value_type: int | str | None = None,
        device_updated_cb: DeviceCallbackType[Notification] | None = None,
    ):
        """Initialize notification class."""
        super().__init__(xknx, name, device_updated_cb)

        self.respond_to_read = respond_to_read
        self.remote_value = RemoteValueString(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            value_type=value_type,
            device_name=name,
            feature_name="Text",
            after_update_cb=self.after_update,
        )

    def _iter_remote_values(self) -> Iterator[RemoteValueString]:
        """Iterate the devices RemoteValue classes."""
        yield self.remote_value

    @property
    def message(self) -> str | None:
        """Return the current message."""
        return self.remote_value.value

    async def set(self, message: str) -> None:
        """Set message."""
        cropped_message = message[:14]
        await self.remote_value.set(cropped_message)

    async def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        await self.remote_value.process(telegram)

    async def process_group_read(self, telegram: Telegram) -> None:
        """Process incoming GroupValueResponse telegrams."""
        if (
            self.respond_to_read
            and telegram.destination_address == self.remote_value.group_address
        ):
            await self.remote_value.respond()

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<Notification name="{self.name}" message={self.remote_value.group_addr_str()} />'
