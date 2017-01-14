from .device import Device

class Devices:

    def __init__(self):
        self._devices = []


    def __iter__(self):
        yield from self._devices


    def devices_by_group_address(self, group_address):
        for device in self._devices:
            if device.has_group_address(group_address):
                yield device


    def __getitem__(self, key):
        for device in self._devices:
            if device.name == key:
                return device
        raise KeyError


    def __len__(self):
        return len(self._devices)


    def add(self, device):
        if not isinstance(device, Device):
            raise TypeError()
        self._devices.append(device)
