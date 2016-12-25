from .binaryoutput import BinaryOutput
from .address import Address

class Outlet(BinaryOutput):
    def __init__(self, xknx, name, config):
        group_address = Address(config["group_address"])
        BinaryOutput.__init__(self, xknx, name, group_address)
        self.group_address = group_address

    def __str__(self):
        return "<Outlet group_address={0}, name={1}>".format(self.group_address,self.name)

