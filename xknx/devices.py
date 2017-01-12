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
        self.devices = []

    def devices_by_group_address(self, group_address):
        for device in self.devices:
            if device.has_group_address(group_address):
                yield device

    def device_by_name(self, name):
        for device in self.devices:
            if device.name == name:
                return device
        raise CouldNotResolveName(name)

    def get_devices(self):
        return self.devices


    def add(self, device):
        if not isinstance(device, Device):
            raise TypeError()
        self.devices.append(device)
