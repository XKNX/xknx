from .binaryoutput import BinaryOutput

class Outlet(BinaryOutput):
    def __init__(self, name, group_address):
        BinaryOutput.__init__(self, group_address)
        self.name = name
        self.group_address = group_address

    def __str__(self):
        return "<Outlet group_address={0}, name={1}>".format(self.group_address,self.name)

