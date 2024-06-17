"""
Module for handling a vector/array of devices.

More or less an array with devices. Adds some search functionality to find devices.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator

from xknx.telegram import Telegram
from xknx.telegram.address import DeviceGroupAddress, GroupAddress, InternalGroupAddress
from xknx.typing import DeviceCallbackType

from .device import Device


class Devices:
    """Class for handling a vector/array of devices."""

    def __init__(self, started: asyncio.Event) -> None:
        """Initialize Devices class."""
        self.started = started  # xknx.started
        self.__devices: list[Device] = []
        self.device_updated_cbs: list[DeviceCallbackType[Device]] = []

    def async_start_device_tasks(self) -> None:
        """Start all devices tasks."""
        for device in self.__devices:
            device.async_start_tasks()

    def async_remove_device_tasks(self) -> None:
        """Remove all devices tasks."""
        for device in self.__devices:
            device.async_remove_tasks()

    def register_device_updated_cb(
        self, device_updated_cb: DeviceCallbackType[Device]
    ) -> None:
        """Register callback for devices being updated."""
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(
        self, device_updated_cb: DeviceCallbackType[Device]
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

    def async_add(self, device: Device) -> None:
        """Add device to active XKNX devices."""
        device.register_device_updated_cb(self.device_updated)
        self.__devices.append(device)
        device.register_state_updater()
        if self.started.is_set():
            # start if device was added after async_start_device_tasks() / xknx.start()
            device.async_start_tasks()

    def async_remove(self, device: Device) -> None:
        """Remove device from XKNX devices."""
        device.async_remove_tasks()
        device.unregister_state_updater()
        device.unregister_device_updated_cb(self.device_updated)
        self.__devices.remove(device)

    def device_updated(self, device: Device) -> None:
        """Call all registered device updated callbacks of device."""
        for device_updated_cb in self.device_updated_cbs:
            device_updated_cb(device)

    def process(self, telegram: Telegram) -> None:
        """Process telegram."""
        if isinstance(
            telegram.destination_address, GroupAddress | InternalGroupAddress
        ):
            for device in self.devices_by_group_address(telegram.destination_address):
                device.process(telegram)

    async def sync(self) -> None:
        """Read state of devices from KNX bus."""
        await asyncio.gather(*[device.sync() for device in self.__devices])
