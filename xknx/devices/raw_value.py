"""
Module for managing a raw value via KNX.

It provides functionality for

* reading the current value from KNX bus or providing a value to the bus.
* send local state changes to KNX bus.
* watching for state updates from KNX bus.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from xknx.remote_value import GroupAddressesType, RemoteValueRaw

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX


class RawValue(Device):
    """Class for managing a raw value."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        payload_length: int,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        respond_to_read: bool = False,
        sync_state: bool | int | float | str = True,
        always_callback: bool = False,
        device_updated_cb: DeviceCallbackType | None = None,
    ):
        """Initialize Sensor class."""
        super().__init__(xknx, name, device_updated_cb)
        self.always_callback = always_callback
        self.respond_to_read = respond_to_read
        self.remote_value = RemoteValueRaw(
            xknx,
            payload_length=payload_length,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            device_name=self.name,
            after_update_cb=self.after_update,
        )

    def _iter_remote_values(self) -> Iterator[RemoteValueRaw]:
        """Iterate the devices RemoteValue classes."""
        yield self.remote_value

    @property
    def last_telegram(self) -> Telegram | None:
        """Return the last telegram received from the RemoteValue."""
        return self.remote_value.telegram

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        await self.remote_value.process(telegram, always_callback=self.always_callback)

    async def process_group_read(self, telegram: "Telegram") -> None:
        """Process incoming GroupValueResponse telegrams."""
        if (
            self.respond_to_read
            and telegram.destination_address == self.remote_value.group_address
        ):
            await self.remote_value.respond()

    async def set(self, value: int) -> None:
        """Set new value."""
        await self.remote_value.set(value)

    def resolve_state(self) -> int | None:
        """Return the current state of the sensor as an unsigned integer."""
        return self.remote_value.value

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<RawValue name="{self.name}" '
            f"addresses={self.remote_value.group_addr_str()} "
            f"value={self.resolve_state().__repr__()}/>"
        )
