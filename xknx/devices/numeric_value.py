"""
Module for managing a generic numeric value via KNX.

It provides functionality for

* reading the current state from KNX bus or providing its state to the bus.
* send local state changes to KNX bus.
* watching for state updates from KNX bus.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from xknx.remote_value import GroupAddressesType, RemoteValueNumeric

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX


class NumericValue(Device):
    """Class for managing a numeric value."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        respond_to_read: bool = False,
        sync_state: bool | int | float | str = True,
        value_type: int | str | None = None,
        always_callback: bool = False,
        device_updated_cb: DeviceCallbackType[NumericValue] | None = None,
    ):
        """Initialize Sensor class."""
        super().__init__(xknx, name, device_updated_cb)
        self.always_callback = always_callback
        self.respond_to_read = respond_to_read
        self.sensor_value = RemoteValueNumeric(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            value_type=value_type,
            device_name=self.name,
            after_update_cb=self.after_update,
        )

    def _iter_remote_values(self) -> Iterator[RemoteValueNumeric]:
        """Iterate the devices RemoteValue classes."""
        yield self.sensor_value

    @property
    def last_telegram(self) -> Telegram | None:
        """Return the last telegram received from the RemoteValue."""
        return self.sensor_value.telegram

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        await self.sensor_value.process(telegram, always_callback=self.always_callback)

    async def process_group_read(self, telegram: "Telegram") -> None:
        """Process incoming GroupValueResponse telegrams."""
        if (
            self.respond_to_read
            and telegram.destination_address == self.sensor_value.group_address
        ):
            await self.sensor_value.respond()

    async def set(self, value: float | int) -> None:
        """Set new value."""
        await self.sensor_value.set(value)

    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self.sensor_value.unit_of_measurement

    def ha_device_class(self) -> str | None:
        """Return the home assistant device class as string."""
        return self.sensor_value.ha_device_class

    def resolve_state(self) -> float | int | None:
        """Return the current state of the sensor as a human readable string."""
        return self.sensor_value.value

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<NumericValue name="{self.name}" '
            f"addresses={self.sensor_value.group_addr_str()} "
            f"value={self.resolve_state().__repr__()} "
            f'unit="{self.unit_of_measurement()}"/>'
        )
