import asyncio
from .device import Device

class Devices:

    def __init__(self):
        """Initialize Devices class."""
        self.__devices = []
        self.device_updated_cbs = []

    def register_device_updated_cb(self, device_updated_cb):
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(self, device_updated_cb):
        self.device_updated_cbs.remove(device_updated_cb)

    def __iter__(self):
        yield from self.__devices


    def devices_by_group_address(self, group_address):
        for device in self.__devices:
            if device.has_group_address(group_address):
                yield device


    def __getitem__(self, key):
        for device in self.__devices:
            if device.name == key:
                return device
        if isinstance(key, int):
            return self.__devices[key]
        raise KeyError


    def __len__(self):
        return len(self.__devices)


    def add(self, device):
        if not isinstance(device, Device):
            raise TypeError()
        device.register_device_updated_cb(self.device_updated)
        self.__devices.append(device)

    def device_updated(self, device):
        for device_updated_cb in self.device_updated_cbs:
            device_updated_cb(device)

    @asyncio.coroutine
    def sync(self):
        for device in self.__devices:
            yield from device.sync()
