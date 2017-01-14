from .device import Device

class Devices:

    def __init__(self):
        self.__devices = []


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
        raise KeyError


    def __len__(self):
        return len(self.__devices)


    def add(self, device):
        if not isinstance(device, Device):
            raise TypeError()
        self.__devices.append(device)
