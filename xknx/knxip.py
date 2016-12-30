import time
from .colors import Colors
from .address import Address,AddressType
from .telegram import Telegram,TelegramType
from .knxip_enum import KNXIPServiceType,CEMIMessageCode,APCI_COMMAND,CEMIFlags
from .dpt import DPT_Binary,DPT_Array

# # See: http://www.knx.org/fileadmin/template/documents/downloads_support_menu/KNX_tutor_seminar_page/tutor_documentation/08_IP%20Communication_E0510a.pdf

class CouldNotParseKNXIP(Exception):
    def __init__(self, description = ""):
        self.description = description
    def __str__(self):
        return "<CouldNotParseKNXIP description='{0}'>".format(self.description)


class ConnectionHeader():

    HEADERLENGTH = 0x06
    PROTOCOLVERSION = 0x10

    def __init__(self, data = None):
        self.headerLength = ConnectionHeader.HEADERLENGTH
        self.protocolVersion = ConnectionHeader.PROTOCOLVERSION
        self.serviceTypeIdent = KNXIPServiceType.ROUTING_INDICATION
        self.b4Reserve = 0
        self.totalLength = 0 # to be set later


    def from_knx(self, data):
        if len(data) != 6:
            raise CouldNotParseKNXIP("wrong connection header length")
        if data[0] != ConnectionHeader.HEADERLENGTH:
            raise CouldNotParseKNXIP("wrong connection header length")
        if data[1] != ConnectionHeader.PROTOCOLVERSION:
            raise CouldNotParseKNXIP("wrong protocol version")

        self.headerLength = data[0]
        self.protocolVersion = data[1]
        self.serviceTypeIdent = KNXIPServiceType(data[2] * 256 + data[3])
        self.b4Reserve = data[4]
        self.totalLength = data[5]

    def set_length( self, cemi ):
        if not isinstance(cemi, CEMIFrame):
            raise TypeError()
        self.totalLength = ConnectionHeader.HEADERLENGTH + cemi.calculated_length()

    def to_knx(self):
        data = []

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
        self.code = CEMIMessageCode.L_Data_REQ
        self.flags = 0
        self.cmd = APCI_COMMAND.UNKNOWN
        self.src_addr = Address()
        self.dst_addr = Address()
        self.tpci_apci = 0
        self.mpdu_len = 0
        self.payload = None


    def _init_group(self, dst_addr = Address()):
        """CEMIMessage _init_group"""
        """
        """
        # Message Code
        self.code = CEMIMessageCode.L_DATA_IND

        self.flags = ( CEMIFlags.FRAME_TYPE_STANDARD | CEMIFlags.DO_NOT_REPEAT |
                    CEMIFlags.BROADCAST | CEMIFlags.PRIORITY_LOW |
                    CEMIFlags.NO_ACK_REQUESTED | CEMIFlags.CONFIRM_NO_ERROR |
                    CEMIFlags.DESTINATION_GROUP_ADDRESS | CEMIFlags.HOP_COUNT_1ST)

        self.dst_addr = dst_addr

    def set_hops(self,hops):
        # Resetting hops
        self.flags &= 0xFFFF ^ 0x0070
        # Setting new hops
        self.flags |= hops << 4

    def calculated_length(self):
        if self.payload is None:
            return 11
        elif isinstance( self.payload, DPT_Binary ):
            return 11
        elif isinstance(self.payload, DPT_Array ):
            return 11 + len(self.payload.value)
        else:
            raise TypeError()

    def _init_group_read(self, dst_addr):
        """CEMIMessage _init_group_read"""
        """Initialize group read """
        self._init_group(dst_addr)
        # ACPI Value
        self._set_tpci_apci_command_value(APCI_COMMAND.GROUP_READ)
        self.payload = None


    def _init_group_write(self, dst_addr = Address(), payload = None ):
        """CEMIMessage _init_group_write"""
        """Initialize group write """
        self._init_group(dst_addr)

        self._set_tpci_apci_command_value(APCI_COMMAND.GROUP_WRITE)
        self.payload = payload


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
        apci = self.tpci_apci & 0x3ff  # TODO: Looks wrong,

        #detect acpi command
        self.cmd = self._detect_acpi_command(apci)

        apdu = cemi[10 + offset:]
        if len(apdu) != self.mpdu_len:
            raise CouldNotParseKNXIP(
                "APDU LEN should be {} but is {}".format(
                    self.mpdu_len, len(apdu)))

        if len(apdu) == 1:
            # Payload is encoded in first byte
            self.payload = DPT_Binary( apci & 0x2f )
        else:
            self.payload = DPT_Array( cemi[11 + offset:] )

    def to_knx(self):
        """Convert the CEMI frame object to its byte representation."""

        data = []

        data.append(self.code.value)
        data.append(0x00)
        data.append((self.flags >> 8 )& 255)
        data.append(self.flags & 255)
        data.append(self.src_addr.byte1()& 255)
        data.append(self.src_addr.byte2()& 255)
        data.append(self.dst_addr.byte1()& 255)
        data.append(self.dst_addr.byte2()& 255)		

#TODO: duplicated code, make nicer ...
        if self.payload is None:
            data.extend([1,
                        (self.tpci_apci >> 8) & 0xff,
                         ((self.tpci_apci >> 0) & 0xff)])

        elif isinstance( self.payload, DPT_Binary ):
            data.extend([1,
                        (self.tpci_apci >> 8) & 0xff,
                        ((self.tpci_apci >> 0) & 0xff) | ( self.payload.value & 0x2F ) ] )
        elif isinstance( self.payload, DPT_Array ):
            data.extend([1 + len(self.payload.value),
                        (self.tpci_apci >> 8) & 0xff,
                        (self.tpci_apci >> 0) & 0xff])

            data.extend(self.payload.value)
        else:
            raise TypeError()

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

    def _set_tpci_apci_command_value(self,command):
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
                   "Command={2}, payload={3}>".format( self.src_addr, self.dst_addr,
                   self.cmd, ','.join(hex(b) for b in self.payload))


class KNXIPFrame:
    """Abstraction for KNX IP Frames"""


    def __init__(self):
        """Initialize object."""

        self.cemi = CEMIFrame()
        self.header = ConnectionHeader()

        self.payload = None

    @property
    def sender(self):
        """Return source address"""
        return self.cemi.src_addr

    @sender.setter
    def sender(self, sender):
        self.cemi.src_addr = Address(sender, AddressType.PHYSICAL)

    @property
    def group_address(self):
        """Return destination address"""
        return self.cemi.dst_addr

    @group_address.setter
    def group_address(self, group_address):
        self.cemi.dst_addr = Address(group_address, AddressType.GROUP)

    @property
    def telegram(self):
        telegram = Telegram()
        telegram.payload = self.cemi.payload
        telegram.group_address = self.group_address

        # TODO: Set telegram.type
        # TODO: Set telegram.direction [additional flag within KNXIP]
        return telegram

    @telegram.setter
    def telegram(self,telegram):
        self.group_address = telegram.group_address

        # TODO: use telegram.direction
        if telegram.type == TelegramType.GROUP_READ:
            self.cemi._init_group_read(telegram.group_address)
        elif telegram.type == TelegramType.GROUP_WRITE:
            self.cemi._init_group_write(telegram.group_address, telegram.payload)

        # TODO: Check if correct, FIX!
        self.cemi.code = CEMIMessageCode.L_DATA_IND
        #self.cemi.flags -= 16

    def from_knx(self, data):

        self.header.from_knx(data[0:6])
        self.cemi.from_knx(data[6:])

    def __str__(self):
        return "<KNXIPFrame {0}\n{1}>".format(self.header, self.cemi)


    def normalize(self):
        self.header.set_length( self.cemi )

    def to_knx(self):

        data = []
        data.extend(self.header.to_knx())
        data.extend(self.cemi.to_knx())
        return data;
