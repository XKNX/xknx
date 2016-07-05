import time
from .colors import Colors
from .address import Address

class Telegram:
    """Abstraction for KNX telegrams"""

    def __init__(self):

        self.sender = Address()
        self.group_address = 0

        self.payload = bytearray()

    def read(self, data):

        self.print_data(data)

        self.sender.set( data[10]*256+data[11] )
        self.group_address   = data[12]*256+data[13]

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
        #print('Control: {:08b}'.format(self.control))
        print('Sender: {0}'.format( self.sender.str()))
        print('Group:   {0}'.format(self.group_address))
        #print('Payload: {:#02x}'.format(self.payload))

        for b in self.payload:
            print('Payload: {:#02x}'.format(b))

    def str(self):
        data = bytearray()

        # See: http://www.knx.org/fileadmin/template/documents/downloads_support_menu/KNX_tutor_seminar_page/tutor_documentation/08_IP%20Communication_E0510a.pdf

        # KNX Header
        data.append(0x06)

        #Protocol version
        data.append(0x10)

        # Service identifier
        # Known values:
        #
        #   0x04 0x20 -> KNXnet/IP Tunnelling: TUNNELLING_REQUEST
        #   0x04 0x21 -> KNXnet/IP Tunnelling: TUNNELLING_ACK
        #   0x05 0x30 KNXnet/IP Routing
        #
        data.append(0x05) # IP Routing 0530
        data.append(0x30)

        # Total length
        total_length = 16 + len(self.payload) 
        data.append((total_length>>8)&255)
        data.append(total_length&255)

        # Message code
        data.append(0x29)

        # Length of additional information (for future usage)
        data.append(0x00)

        # Control field
        data.append(0xbc) #b4 ?

        # Type of target address
        data.append(0xd0)

        # Sender address
        data.append((self.sender.address>>8)&255)
        data.append(self.sender.address&255)

        # Target address
        data.append((self.group_address >> 8)&255)
        data.append(self.group_address & 255)

        # Payload length
        data.append(len(self.payload))

        # Zero
        data.append(0x00)

        # Payload
        for b in self.payload:
            data.append(b)

        return data
