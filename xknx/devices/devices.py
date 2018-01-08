"""
Module for handling a vector/array of devices.

More or less an array with devices. Adds some search functionality to find devices.
"""
from .device import Device


class Devices:
    """Class for handling a vector/array of devices."""

    def __init__(self):
        """Initialize Devices class."""
        self.__devices = []
        self.device_updated_cbs = []

    def register_device_updated_cb(self, device_updated_cb):
        """Register callback for devices beeing updated."""
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(self, device_updated_cb):
        """Unregister callback for devices beeing updated."""
        self.device_updated_cbs.remove(device_updated_cb)

    def __iter__(self):
        """Iterator."""
        yield from self.__devices

    def devices_by_group_address(self, group_address):
        """Return device(s) by group address."""
        for device in self.__devices:
            if device.has_group_address(group_address):
                yield device

    def __getitem__(self, key):
        """Return device by name or by index."""
        for device in self.__devices:
            if device.name == key:
                return device
        if isinstance(key, int):
            return self.__devices[key]
        raise KeyError

    def __len__(self):
        """Return number of devices within vector."""
        return len(self.__devices)

    def add(self, device):
        """Add device to devices vector."""
        if not isinstance(device, Device):
            raise TypeError()
        device.register_device_updated_cb(self.device_updated)
        self.__devices.append(device)

    async def device_updated(self, device):
        """Call all registered device updated callbacks of device."""
        for device_updated_cb in self.device_updated_cbs:
            await device_updated_cb(device)

    async def sync(self):
        """Read state of devices from KNX bus."""
        for device in self.__devices:
            await device.sync()
