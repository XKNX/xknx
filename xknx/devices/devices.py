"""
Module for handling a vector/array of devices.

More or less an array with devices. Adds some search functionality to find devices.
"""
from __future__ import annotations

from collections.abc import Awaitable, Iterator
from typing import Callable

from xknx.telegram import Telegram
from xknx.telegram.address import DeviceGroupAddress, GroupAddress, InternalGroupAddress

from .device import Device

DeviceCallbackType = Callable[[Device], Awaitable[None]]


class Devices:
    """Class for handling a vector/array of devices."""

    def __init__(self) -> None:
        """Initialize Devices class."""
        self.__devices: list[Device] = []
        self.device_updated_cbs: list[DeviceCallbackType] = []

    def register_device_updated_cb(self, device_updated_cb: DeviceCallbackType) -> None:
        """Register callback for devices being updated."""
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(
        self, device_updated_cb: DeviceCallbackType
    ) -> None:
        """Unregister callback for devices being updated."""
        self.device_updated_cbs.remove(device_updated_cb)

    def __iter__(self) -> Iterator[Device]:
        """Iterate registered devices."""
        yield from self.__devices

    def devices_by_group_address(
        self, group_address: DeviceGroupAddress
    ) -> Iterator[Device]:
        """Return device(s) by group address."""
        for device in self.__devices:
            if device.has_group_address(group_address):
                yield device

    def __getitem__(self, key: str | int) -> Device:
        """Return device by name or by index."""
        for device in self.__devices:
            if device.name == key:
                return device
        if isinstance(key, int):
            return self.__devices[key]
        raise KeyError

    def __len__(self) -> int:
        """Return number of devices within vector."""
        return len(self.__devices)

    def __contains__(self, key: str) -> bool:
        """Return if devices with name 'key' is within devices."""
        return any(device.name == key for device in self.__devices)

    def add(self, device: Device) -> None:
        """Add device to devices vector."""
        if not isinstance(device, Device):
            raise TypeError()
        device.register_device_updated_cb(self.device_updated)
        self.__devices.append(device)

    def remove(self, device: Device) -> None:
        """Remove device from devices vector."""
        self.__devices.remove(device)

    async def device_updated(self, device: Device) -> None:
        """Call all registered device updated callbacks of device."""
        for device_updated_cb in self.device_updated_cbs:
            await device_updated_cb(device)

    async def process(self, telegram: Telegram) -> None:
        """Process telegram."""
        if isinstance(
            telegram.destination_address, (GroupAddress, InternalGroupAddress)
        ):
            for device in self.devices_by_group_address(telegram.destination_address):
                await device.process(telegram)

    async def sync(self) -> None:
        """Read state of devices from KNX bus."""
        for device in self.__devices:
            await device.sync()
