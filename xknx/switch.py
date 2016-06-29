from .binaryinput import BinaryInput
from .device import Device


class Switch(BinaryInput):
    def __init__(self, name, group_address):
        BinaryInput.__init__(self, group_address)
        Device.__init__(self)
        self.name = name
        self.group_address = group_address

    def __str__(self):
        return "<Switch group_address={0}, name={1}>".format(self.group_address,self.name)
