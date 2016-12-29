import time
from .colors import Colors
from .address import Address,AddressType
from .telegram import Telegram
from .knxip_enum import KNXIPServiceType,CEMIMessageCode,APCI_COMMAND,CEMIFlags 

# # See: http://www.knx.org/fileadmin/template/documents/downloads_support_menu/KNX_tutor_seminar_page/tutor_documentation/08_IP%20Communication_E0510a.pdf

class CouldNotParseKNXIP(Exception):
    def __init__(self, description = ""):
        self.description = description
    def __str__(self):
        return "<CouldNotParseKNXIP description='{0}'>".format(self.description)


class ConnectionHeader():

    def __init__(self, data = None):
        self.headerLength = 0x06
        self.protocolVersion = 0x10
        self.serviceTypeIdent = KNXIPServiceType.ROUTING_INDICATION
        self.b4Reserve = 0
        self.totalLength = 0 # to be set later


    def from_knx(self, data):
        if len(data) != 6:
            raise CouldNotParseKNXIP("wrong connection header length")
        if data[0] != 0x06:
            raise CouldNotParseKNXIP("wrong connection header length")
        if data[1] != 0x10:
            raise CouldNotParseKNXIP("wrong protocol version")

        self.headerLength = data[0]
        self.protocolVersion = data[1]
        self.serviceTypeIdent = KNXIPServiceType(data[2] * 256 + data[3])
        self.b4Reserve = data[4]
        self.totalLength = data[5]


    def to_knx(self):
        data = bytearray()

        data.append( self.headerLength)
        data.append( self.protocolVersion)
        data.append( ( self.serviceTypeIdent.value >> 8 ) & 255 )
        data.append( self.serviceTypeIdent.value & 255 )
        data.append( ( self.totalLength>>8 ) & 255 )
        data.append (self.totalLength & 255 )

        return data

    def __str__(self):
        return "<Connection HeaderLength={0}, ProtocolVersion={1}, " \
                "KNXIPServiceType={2}, Reserve={3}, TotalLength={4}>".format(
                self.headerLength, self.protocolVersion, self.serviceTypeIdent,
                self.b4Reserve, self.totalLength)



class CEMIFrame():
    """Representation of a CEMI Frame."""

    def __init__(self):
        """CEMIFrame __init__ object."""
        self.code = 0
        self.flags = 0
        self.cmd = APCI_COMMAND.UNKNOWN
        self.src_addr = Address()
        self.dst_addr = Address()
        self.tpci_apci = 0
        self.mpdu_len = 0
        self.data = [0]


    def _init_group(self, dst_addr = Address()):
        """CEMIMessage _init_group"""
        """
        """
        # Message Code
        self.code = CEMIMessageCode.L_Data_REQ

        self.flags = ( CEMIFlags.FRAME_TYPE_STANDARD | CEMIFlags.DO_NOT_REPEAT |
                    CEMIFlags.BROADCAST | CEMIFlags.PRIORITY_LOW |
                    CEMIFlags.NO_ACK_REQUESTED | CEMIFlags.CONFIRM_NO_ERROR |
                    CEMIFlags.DESTINATION_GROUP_ADDRESS | CEMIFlags.HOP_COUNT_1ST)

        self.src_addr = Address()
        self.dst_addr = dst_addr

    def _init_group_read(self, dst_addr):
        """CEMIMessage _init_group_read"""
        """Initialize group read """
        self.init_group(dst_addr)
        # ACPI Value
        _set_tpci_apci_command_value(APCI_COMMAND.GROUP_READ)
        # DATA
        self.data = [0]


    def _init_group_write(self, dst_addr = Address(), data=None):
        """CEMIMessage _init_group_write"""
        """Initialize group write """
        self.init_group(dst_addr)
        # ACPI Value
        _set_tpci_apci_command_value(APCI_COMMAND.GROUP_WRITE)
        # DATA
        if data is None:
            self.data = [0]
        else:
            self.data = data


    def from_knx(self, cemi):

        """Create a new CEMIFrame initialized from the given CEMI data."""
        # TODO: check that length matches
        self.code = CEMIMessageCode(cemi[0])
        offset = cemi[1]

        self.flags = cemi[2] * 256 + cemi[3]

        self.src_addr = Address((cemi[4 + offset], cemi[5 + offset]), AddressType.PHYSICAL)
        self.dst_addr = Address((cemi[6 + offset], cemi[7 + offset]), AddressType.GROUP)

        self.mpdu_len = cemi[8 + offset]

        self.tpci_apci = cemi[9 + offset] * 256 + cemi[10 + offset]
        apci = self.tpci_apci & 0x3ff

        #detect acpi command
        self.cmd = self._detect_acpi_command(apci)

        apdu = cemi[10 + offset:]
        if len(apdu) != self.mpdu_len:
            raise CouldNotParseKNXIP(
                "APDU LEN should be {} but is {}".format(
                    self.mpdu_len, len(apdu)))
        #check Date in ACPI Byte
        if len(apdu) == 1:
            self.data = [apci & 0x2f]
        else:
            self.data = cemi[11 + offset:]


    def to_knx(self):
        """Convert the CEMI frame object to its byte representation. Not testet"""
        data = [self.code.value, 0x00, (self.flags >> 8 )& 255, self.flags & 255,
                self.src_addr.byte1(), self.src_addr.byte2(),
                self.dst_addr.byte1(), self.dst_addr.byte2(),
               ]
        if (len(self.data) == 1) and ((self.data[0] & 3) == self.data[0]):
            # less than 6 bit of data, pack into APCI byte
            data.extend([1, (self.tpci_apci >> 8) & 0xff,
                         ((self.tpci_apci >> 0) & 0xff) + self.data[0]])
        else:
            data.extend([1 + len(self.data), (self.tpci_apci >> 8) &
                         0xff, (self.tpci_apci >> 0) & 0xff])
            data.extend(self.data)

        return data


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

    @staticmethod
    def _set_tpci_apci_command_value(command):
        # for APCI codes see KNX Standard 03/03/07 Application layer
        # table Application Layer control field
        if command == APCI_COMMAND.GROUP_WRITE :
            self.cmd = APCI_COMMAND.GROUP_WRITE
            self.tpci_apci =  0x00 * 256 + 0x80
        elif command == APCI_COMMAND.GROUP_READ :
            self.cmd = APCI_COMMAND.GROUP_READ
            self.tpci_apci =   0x00
        else:
            self.cmd = APCI_COMMAND.UNKNOWN
            self.tpci_apci =   0x00

    def __str__(self):
            return "<CEMIFrame SourceAddress={0}, DestinationAddress={1}, " \
                   "Command={2}, Data={3}>".format( self.src_addr, self.dst_addr,
                   self.cmd, self.data)


class KNXIPFrame:
    """Abstraction for KNX telegrams"""


    def __init__(self):
        """Initialize object."""

        self.cemi = CEMIFrame()
        self.header = ConnectionHeader()

        self.payload = bytearray()

    @property
    def sender(self):
        """Return source address"""
        return self.cemi.src_addr

    @sender.setter
    def sender(self, sender):
        self.cemi.src_addr = Address(sender)

    @property
    def group_address(self):
        """Return destination address"""
        return self.cemi.dst_addr

    @group_address.setter
    def group_address(self, group_address):
        self.cemi.dst_addr = Address(group_address)

    @property
    def telegram(self):
        telegram = Telegram()
        telegram.payload = self.payload
        telegram.group_address = self.group_address
        return telegram

    @telegram.setter
    def telegram(self,telegram):
        self.group_address = telegram.group_address
        self.payload = telegram.payload

    def from_knx(self, data):

        self.header.from_knx(data[0:6])
        self.cemi.from_knx(data[6:])

        print(self)

        len_payload = data[14]
        for x in range(0, len_payload):
            self.payload.append(data[16+x])

    def __str__(self):
        return "<KNXIPFrame {0} {1}>".format(self.header, self.cemi)


    def to_knx(self):
        data = bytearray()

        # TODO: Better calculation
        self.header.totalLength = 16 + len(self.payload)

        data = self.header.to_knx()

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
