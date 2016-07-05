from .device import Device

class Dimmer(Device):
    def __init__(self, name, group_address):
        Device.__init__(self)
        self.name = name
        self.group_address = group_address

    def has_group_address(self, group_address):
        return self.group_address == group_address

    def __str__(self):
        return "<Dimmer group_address={0}, name={1}>".format(self.group_address,self.name)


