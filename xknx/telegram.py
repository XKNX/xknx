import time
from .colors import Colors
from .address import Address,AddressType
class CouldNotParseCEMI(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "CouldNotParseCEMI"
		
class CEMIMessage():
    """Representation of a CEMI message."""

    CMD_GROUP_READ = 1
    CMD_GROUP_WRITE = 2
    CMD_GROUP_RESPONSE = 3
    CMD_UNKNOWN = 0xff

    code = 0
    ctl1 = 0
    ctl2 = 0
    src_addr = None
    dst_addr = None
    cmd = None
    tpci_apci = 0
    mpdu_len = 0
    data = [0]

    def __init__(self):
        """Initialize object."""
        pass

    @classmethod
    def from_body(self, cemi, offsetIPBody = 0):
	
        """Create a new CEMIMessage initialized from the given CEMI data."""
        # TODO: check that length matches
        #self.message = CEMIMessage()
        self.code = cemi[0 + offsetIPBody]
        offset = cemi[1 + offsetIPBody]

        self.ctl1 = cemi[2 + offsetIPBody]
        self.ctl2 = cemi[3 + offsetIPBody]

        self.src_addr = Address(cemi[4 + offset + offsetIPBody] * 256 + cemi[5 + offset + offsetIPBody], AddressType.PHYSICAL)
        self.dst_addr = Address(cemi[6 + offset + offsetIPBody] * 256 + cemi[7 + offset + offsetIPBody])

        self.mpdu_len = cemi[8 + offset + offsetIPBody]

        tpci_apci = cemi[9 + offset + offsetIPBody] * 256 + cemi[10 + offset + offsetIPBody]
        apci = tpci_apci & 0x3ff

        # for APCI codes see KNX Standard 03/03/07 Application layer
        # table Application Layer control field
        if apci & 0x080:
            # Group write
            self.cmd = CEMIMessage.CMD_GROUP_WRITE
        elif apci == 0:
            self.cmd = CEMIMessage.CMD_GROUP_READ
        elif apci & 0x40:
            self.cmd = CEMIMessage.CMD_GROUP_RESPONSE
        else:
            self.cmd = CEMIMessage.CMD_UNKNOWN

        apdu = cemi[10 + offset + offsetIPBody:]
        if len(apdu) != self.mpdu_len:
            raise CouldNotParseCEMI(
                "APDU LEN should be {} but is {}".format(
                    self.mpdu_len, len(apdu)))

        if len(apdu) == 1:
            self.data = [apci & 0x2f]
        else:
            self.data = cemi[11 + offset + offsetIPBody:]


    def to_body(self):
        """Convert the CEMI frame object to its byte representation."""
        body = [self.code, 0x00, self.ctl1, self.ctl2,
                (self.src_addr >> 8) & 0xff, (self.src_addr >> 0) & 0xff,
                (self.dst_addr >> 8) & 0xff, (self.dst_addr >> 0) & 0xff,
               ]
        if (len(self.data) == 1) and ((self.data[0] & 3) == self.data[0]):
            # less than 6 bit of data, pack into APCI byte
            body.extend([1, (self.tpci_apci >> 8) & 0xff,
                         ((self.tpci_apci >> 0) & 0xff) + self.data[0]])
        else:
            body.extend([1 + len(self.data), (self.tpci_apci >> 8) &
                         0xff, (self.tpci_apci >> 0) & 0xff])
            body.extend(self.data)

        return body

class KNXnetIPBody():
   
	
    def __init__(self):
        """Initialize object."""
        self.headerLength = 0
        self.protokollVersion = 0
        self.serviceTypeIdent = 0
        self.b4Reserve = 0
        self.totalLength = 0
        self.message = CEMIMessage()
        pass
		
    def from_telegram(self, data):
        self.headerLength = data[0]
        self.protokollVersion = data[1]
        self.serviceTypeIdent = data[2] * 256 + data[3]
        self.b4Reserve = data[4]
        self.totalLength = data[5]		
        self.message.from_body(data, 6)

        print ("IPBody->HeaderLength:", format(self.headerLength, '02x'), " ProtocolVersion:",format(self.protokollVersion, '02x'), " ServiceType:",format(self.serviceTypeIdent, '02x')," reserve:",format(self.b4Reserve, '02x')," TotalLength:",format(self.totalLength, '02x'))
        print ("CEMIBody->SourceAddress:", self.message.src_addr, " DestinationAddress:",self.message.dst_addr, " APCI_Command:",self.message.cmd," Data:",self.message.data," ")
			
class Telegram:
    """Abstraction for KNX telegrams"""

    def __init__(self):

        self.knxbody = KNXnetIPBody()
		
        self.sender = Address()
        self.group_address = Address()

        self.payload = bytearray()

    def read(self, data):

        self.print_data(data)
        self.knxbody.from_telegram(data)
        self.sender = Address(data[10]*256+data[11],AddressType.PHYSICAL)
        self.group_address = Address(data[12]*256+data[13])

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
        print('Sender: {0}'.format( self.sender.__str__()))
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
        data.append( self.sender.byte1() )
        data.append( self.sender.byte2() )

        # Target address
        data.append( self.group_address.byte1() )
        data.append( self.group_address.byte2() )

        # Payload length
        data.append(len(self.payload))

        # Zero
        data.append(0x00)

        # Payload
        for b in self.payload:
            data.append(b)

        return data
