from .device import Device

class CouldNotResolveName(Exception):

    def __init__(self, name):
        super(CouldNotResolveName, self).\
            __init__("Could not resolve name")
        self.name = name

    def __str__(self):
        return "CouldNotResolveName <name={0}>".\
            format(self.name)


class Devices:

    def __init__(self):
        self._devices = []


    def __iter__(self):
        yield from self._devices


    def devices_by_group_address(self, group_address):
        for device in self._devices:
            if device.has_group_address(group_address):
                yield device


    def device_by_name(self, name):
        for device in self._devices:
            if device.name == name:
                return device
        raise CouldNotResolveName(name)


    def add(self, device):
        if not isinstance(device, Device):
            raise TypeError()
        self._devices.append(device)
