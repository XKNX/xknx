import time
from .colors import Colors
from .address import Address,AddressType
from .telegram import Telegram,TelegramType
from .knxip_enum import KNXIPServiceType,CEMIMessageCode,APCICommand,CEMIFlags
from .dpt import DPT_Binary,DPT_Array

# # See: http://www.knx.org/fileadmin/template/documents/downloads_support_menu/KNX_tutor_seminar_page/tutor_documentation/08_IP%20Communication_E0510a.pdf

class CouldNotParseKNXIP(Exception):
    def __init__(self, description = ""):
        self.description = description
    def __str__(self):
        return "<CouldNotParseKNXIP description='{0}'>".format(self.description)

class ConversionException(Exception):
    def __init__(self, description = ""):
        self.description = description
    def __str__(self):
        return "<ConversionException description='{0}'>".format(self.description)

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
        self.cmd = APCICommand.GROUP_READ
        self.src_addr = Address()
        self.dst_addr = Address()
        self.mpdu_len = 0
        self.payload = None

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

    def from_knx(self, cemi):

        """Create a new CEMIFrame initialized from the given CEMI data."""
        # TODO: check that length matches
        self.code = CEMIMessageCode(cemi[0])
        offset = cemi[1]

        self.flags = cemi[2] * 256 + cemi[3]

        self.src_addr = Address((cemi[4 + offset], cemi[5 + offset]), AddressType.PHYSICAL)

        dst_addr_type = \
            AddressType.GROUP \
            if self.flags & CEMIFlags.DESTINATION_GROUP_ADDRESS \
            else AddressType.PHYSICAL
        self.dst_addr = Address((cemi[6 + offset], cemi[7 + offset]), dst_addr_type)

        self.mpdu_len = cemi[8 + offset]

        # TPCI (transport layer control information)   -> First 14 bit
        # APCI (application layer control information) -> Last  10 bit 

        tpci_apci = cemi[9 + offset] * 256 + cemi[10 + offset]

        self.cmd = APCICommand(tpci_apci & 0xFFC0)

        apdu = cemi[10 + offset:]
        if len(apdu) != self.mpdu_len:
            raise CouldNotParseKNXIP(
                "APDU LEN should be {} but is {}".format(
                    self.mpdu_len, len(apdu)))

        if len(apdu) == 1:
            apci = tpci_apci & DPT_Binary.APCI_BITMASK
            self.payload = DPT_Binary( apci )
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

        def encode_cmd_and_payload( cmd, encoded_payload = 0, appended_payload = []):
            data = [
                1 + len( appended_payload ),
                (cmd.value >> 8) & 0xff,
                (cmd.value & 0xff) | ( encoded_payload & DPT_Binary.APCI_BITMASK ) ]
            data.extend(appended_payload)
            return data

        if self.payload is None:
            data.extend( encode_cmd_and_payload( self.cmd ) )
        elif isinstance( self.payload, DPT_Binary ):
            data.extend( encode_cmd_and_payload( self.cmd, encoded_payload = self.payload.value ) )
        elif isinstance( self.payload, DPT_Array ):
            data.extend( encode_cmd_and_payload( self.cmd, appended_payload = self.payload.value ) )
        else:
            raise TypeError()

        return data


    def __str__(self):
            return "<CEMIFrame SourceAddress={0}, DestinationAddress={1}, " \
                   "Flags={2:16b} Command={3}, payload={4}>".format( self.src_addr, self.dst_addr,
                   self.flags, self.cmd, self.payload)


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

        if self.cemi.cmd == APCICommand.GROUP_WRITE:
            telegram.type = TelegramType.GROUP_WRITE
        elif self.cemi.cmd == APCICommand.GROUP_READ:
            telegram.type = TelegramType.GROUP_READ
        elif self.cemi.cmd == APCICommand.GROUP_RESPONSE:
            telegram.type = TelegramType.GROUP_RESPONSE
        else:
            raise ConversionException("Telegram not implemented for {0}".format(self.cemi.cmd))

        # TODO: Set telegram.direction [additional flag within KNXIP]
        return telegram

    @telegram.setter
    def telegram(self,telegram):
        self.cemi.dst_addr = telegram.group_address
        self.cemi.payload = telegram.payload

        # TODO: Move to separate function
        self.cemi.code = CEMIMessageCode.L_DATA_IND
        self.cemi.flags = ( CEMIFlags.FRAME_TYPE_STANDARD | CEMIFlags.DO_NOT_REPEAT |
                    CEMIFlags.BROADCAST | CEMIFlags.PRIORITY_LOW |
                    CEMIFlags.NO_ACK_REQUESTED | CEMIFlags.CONFIRM_NO_ERROR |
                    CEMIFlags.DESTINATION_GROUP_ADDRESS | CEMIFlags.HOP_COUNT_1ST)

        # TODO: use telegram.direction
        if telegram.type == TelegramType.GROUP_READ:
            self.cemi.cmd = APCICommand.GROUP_READ
        elif telegram.type == TelegramType.GROUP_WRITE:
            self.cemi.cmd = APCICommand.GROUP_WRITE
        elif telegram.type == TelegramType.GROUP_RESPONSE:
            self.cemi.cmd = APCICommand.GROUP_RESPONSE
        else:
            raise TypeError()


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
