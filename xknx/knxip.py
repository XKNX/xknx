import time
from .colors import Colors
from .address import Address,AddressType
from .telegram import Telegram
from .knxip_enum import KNXIPServiceType,CEMIMessageCode,APCI_COMMAND 

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
        self.ctl1 = 0
        self.ctl2 = 0
        self.cmd = APCI_COMMAND.UNKNOWN
        self.src_addr = Address()
        self.dst_addr = Address()
        self.tpci_apci = 0
        self.mpdu_len = 0
        self.data = [0]


    def _init_group(self, dst_addr = Address()):
        """CEMIMessage _init_group"""
        """
        Control Field 1
         Bit  |
        ------+---------------------------------------------------------------
          7   | Frame Type  - 0x0 for extended frame
              |               0x1 for standard frame
        ------+---------------------------------------------------------------
          6   | Reserved
              |
        ------+---------------------------------------------------------------
          5   | Repeat Flag - 0x0 repeat frame on medium in case of an error
              |               0x1 do not repeat
        ------+---------------------------------------------------------------
          4   | System Broadcast - 0x0 system broadcast
              |                    0x1 broadcast
        ------+---------------------------------------------------------------
          3   | Priority    - 0x0 system
              |               0x1 normal
        ------+               0x2 urgent
          2   |               0x3 low
              |
        ------+---------------------------------------------------------------
          1   | Acknowledge Request - 0x0 no ACK requested
              | (L_Data.req)          0x1 ACK requested
        ------+---------------------------------------------------------------
          0   | Confirm      - 0x0 no error
              | (L_Data.con) - 0x1 error
        ------+---------------------------------------------------------------

        Control Field 2

         Bit  |
        ------+---------------------------------------------------------------
          7   | Destination Address Type - 0x0 individual address
              |                          - 0x1 group address
        ------+---------------------------------------------------------------
         6-4  | Hop Count (0-7)
        ------+---------------------------------------------------------------
         3-0  | Extended Frame Format - 0x0 standard frame
        ------+---------------------------------------------------------------
        """
        # Message Code
        self.code = CEMIMessageCode.L_Data_REQ
        # Control Field 1 -> frametype 1, repeat 1, system broadcast 1, priority 3, ack-req 0, confirm-flag 0
        self.ctl1 = 0xbc
        # Control Field 2 -> dst_addr type 1, hop count 6, extended frame format
        self.ctl2 = 0xe0

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
        data = [self.code.value, 0x00, self.ctl1, self.ctl2,
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
