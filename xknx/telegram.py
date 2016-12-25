import time
from .colors import Colors
from .address import Address,AddressType
from enum import Enum

class CouldNotParseCEMI(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "CouldNotParseCEMI"
		
class APCI_COMMAND(Enum):
    GROUP_READ = 1
    GROUP_WRITE = 2
    GROUP_RESPONSE = 3
    UNKNOWN = 0xff
	
class ServiceType(Enum):		
    SEARCH_REQUEST = 0x0201
    SEARCH_RESPONSE = 0x0202
    DESCRIPTION_REQUEST = 0x0203
    DESCRIPTION_RESPONSE = 0x0204
    CONNECT_REQUEST = 0x0205
    CONNECT_RESPONSE = 0x0206
    CONNECTIONSTATE_REQUEST = 0x0207
    CONNECTIONSTATE_RESPONSE = 0x0208
    DISCONNECT_REQUEST = 0x0209
    DISCONNECT_RESPONSE = 0x020a
    DEVICE_CONFIGURATION_REQUEST = 0x0310
    DEVICE_CONFIGURATION_ACK = 0x0111
    TUNNELING_REQUEST = 0x0420
    TUNNELLING_ACK = 0x0421
    ROUTING_INDICATION = 0x0530
    ROUTING_LOST_MESSAGE = 0x0531
    UNKNOWN = 0x0000
	
class CEMIMessage():
    """Representation of a CEMI message."""
	
    def __init__(self, cemi = None):      
        """Initialize object."""
        self.code = 0
        self.ctl1 = 0
        self.ctl2 = 0
        self.cmd = APCI_COMMAND.UNKNOWN
        self.src_addr = Address()
        self.dst_addr = Address()  
        self.tpci_apci = 0
        self.mpdu_len = 0
        self.data = [0]
        if cemi != None: 
            self._from_cemi_frame(cemi)
  
    def _from_cemi_frame(self, cemi):
	
        """Create a new CEMIMessage initialized from the given CEMI data."""
        # TODO: check that length matches
        self.code = cemi[0]
        offset = cemi[1]

        self.ctl1 = cemi[2]
        self.ctl2 = cemi[3]
        
        self.src_addr = Address((cemi[4 + offset], cemi[5 + offset]), AddressType.PHYSICAL)
        self.dst_addr = Address((cemi[6 + offset], cemi[7 + offset]), AddressType.GROUP)

        self.mpdu_len = cemi[8 + offset]

        self.tpci_apci = cemi[9 + offset] * 256 + cemi[10 + offset]
        apci = self.tpci_apci & 0x3ff

        #detect acpi command
        self.cmd = self._detect_acpi_command(apci)

        apdu = cemi[10 + offset:]
        if len(apdu) != self.mpdu_len:
            raise CouldNotParseCEMI(
                "APDU LEN should be {} but is {}".format(
                    self.mpdu_len, len(apdu)))

        if len(apdu) == 1:
            self.data = [apci & 0x2f]
        else:
            self.data = cemi[11 + offset:]
			

    def _to_cemi_frame(self):
        """Convert the CEMI frame object to its byte representation. Not testet"""
        cemi = [self.code, 0x00, self.ctl1, self.ctl2,
                self.src_addr.byte1, self.src_addr.byte2,
                self.dst_addr.byte1, self.dst_addr.byte2,
               ]
        if (len(self.data) == 1) and ((self.data[0] & 3) == self.data[0]):
            # less than 6 bit of data, pack into APCI byte
            cemi.extend([1, (self.tpci_apci >> 8) & 0xff,
                         ((self.tpci_apci >> 0) & 0xff) + self.data[0]])
        else:
            cemi.extend([1 + len(self.data), (self.tpci_apci >> 8) &
                         0xff, (self.tpci_apci >> 0) & 0xff])
            cemi.extend(self.data)

        return cemi
		
    @staticmethod			
    def _detect_acpi_command(apci):
        # for APCI codes see KNX Standard 03/03/07 Application layer
        # table Application Layer control field
        if apci & 0x080:
            return APCI_COMMAND.GROUP_WRITE
        elif apci == 0:
            return APCI_COMMAND.GROUP_READ
        elif apci & 0x40:
            return APCI_COMMAND.GROUP_RESPONSE
        else:
            return APCI_COMMAND.UNKNOWN

class Telegram:
    """Abstraction for KNX telegrams"""

		
    def __init__(self):
        """Initialize object."""
        self.headerLength = 0
        self.protocolVersion = 0
        self.serviceTypeIdent = ServiceType.UNKNOWN
        self.b4Reserve = 0
        self.totalLength = 0
        self.message = CEMIMessage()
		
        self.payload = bytearray()
    @property
    def sender(self):
        """Return source address"""
        return self.message.src_addr
		
    @property
    def group_address(self):
        """Return destination address"""
        return self.message.dst_addr
			
    def _from_telegram(self, data):
        self.headerLength = data[0]
        self.protocolVersion = data[1]
        self.serviceTypeIdent = ServiceType(data[2] * 256 + data[3])
        self.b4Reserve = data[4]
        self.totalLength = data[5]	
        self.message = CEMIMessage(data[6:])		
		
    def read(self, data):

        self.print_data(data)

        self._from_telegram(data)
		
        print(self)

        len_payload = data[14]
        for x in range(0, len_payload):
            self.payload.append(data[16+x])
			
    def __str__(self):
        return "<KNXIPFrame IPBody->HeaderLength={0}, ProtocolVersion={1}, ServiceType={2}, Reserve={3}, TotalLength={4}>\n<CEMIBody->SourceAddress={5}, DestinationAddress={6}, Command={7}, Data={8}>".format(self.headerLength, self.protocolVersion, self.serviceTypeIdent, self.b4Reserve, self.totalLength, self.message.src_addr, self.message.dst_addr, self.message.cmd, self.message.data)
	
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
