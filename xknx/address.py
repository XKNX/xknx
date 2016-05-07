
class CouldNotParseAddress(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "CouldNotParseAddress"

class Address:

    address = 0

    def __init__(self, address = 0):
        self.set(address)

    def __eq__(self, other):
        return self.address == other.address

    def set(self, address):
        if type(address) is str:
            self.set_str(address)
        elif type(address) is int:
            self.set_int(address)
        elif type(address) is Address:
            self.set_int(address.address)
        else:
            raise TypeError()

    def set_str( self, address ):
        parts = address.split(".")
        if len(parts) != 3:
            raise CouldNotParseAddress()
        for part in parts:
            if not part.isnumeric():
                raise CouldNotParseAddress()
        area = int(parts[0])
        line = int(parts[1])
        device = int(parts[2])
        self.address = (area<<12) + (line<<8) + device

    def set_int(self, address):
        self.address = address

    def str(self):
        return '{0}.{1}.{2}'.format(
            ((self.address>>12)&15),
            ((self.address>>8)&15),
            (self.address&255) )
