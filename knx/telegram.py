import time
from .colors import Colors
from .address import Address

class Telegram:
    """Abstraction for KNX telegrams"""

    def __init__(self):
        self.control = 0x06
        self.sender = Address()
        self.group = 0

        self.payload = bytearray()

    def read(self, data):

        self.print_data(data)

        self.control = data[0]
        self.sender.set( data[10]*256+data[11] )
        self.group   = data[12]*256+data[13]


        len_payload = data[14]
        for x in range(0, len_payload):
            self.payload.append(data[16+x])

    def print_data(self, data):
        i = 0;
        for b in data:
            if i in [10,11]:
                print (Colors.OKBLUE, end="")
            if i in [0,12,13]:
                print (Colors.WARNING, end="")
            if i == 14 or i >= 16:
                print (Colors.BOLD, end="")
            print (format(b, '02x'), end="")
            print (Colors.ENDC+" ", end="")
            i=i+1
        print ("")

    def dump(self):
        print('Control: {:08b}'.format(self.control))
        print('Sender: {0}'.format( self.sender.str()))
        print('Group:   {0}'.format(self.group))
        print('Payload: {:#02x}'.format(self.payload))


    def str(self):
        data = bytearray()

        data.append(self.control)
        data.append(0x10)
        data.append(0x05)
        data.append(0x30)

        data.append(0x00)
        data.append(0x11)
        data.append(0x29)
        data.append(0x00)

        data.append(0xbc)
        data.append(0xd0)
        print('{0}'.format(self.sender.address))
        data.append((self.sender.address>>8)&255)
        data.append(self.sender.address&255)

        data.append(self.group >> 8)
        data.append(self.group & 255)

        data.append(len(self.payload))
        data.append(0x00)

        for b in self.payload:
            data.append(b)

        return data
