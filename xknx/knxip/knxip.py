from xknx.knx import Address, AddressType, Telegram, TelegramType, \
    DPTBinary, DPTArray
from .knxip_enum import KNXIPServiceType, CEMIMessageCode,\
    APCICommand, CEMIFlags

class CouldNotParseKNXIP(Exception):
    def __init__(self, description=""):
        super(CouldNotParseKNXIP, self).__init__("Could not parse KNXIP")
        self.description = description
    def __str__(self):
        return "<CouldNotParseKNXIP description='{0}'>" \
            .format(self.description)

class ConversionException(Exception):
    def __init__(self, description=""):
        super(ConversionException, self).__init__("Conversion Exception")
        self.description = description
    def __str__(self):
        return "<ConversionException description='{0}'>" \
            .format(self.description)

class ConnectionHeader():

    HEADERLENGTH = 0x06
    PROTOCOLVERSION = 0x10

    def __init__(self):
        self.header_length = ConnectionHeader.HEADERLENGTH
        self.protocol_version = ConnectionHeader.PROTOCOLVERSION
        self.service_type_ident = KNXIPServiceType.ROUTING_INDICATION
        self.b4_reserve = 0
        self.total_length = 0 # to be set later


    def from_knx(self, data):
        if len(data) != 6:
            raise CouldNotParseKNXIP("wrong connection header length")
        if data[0] != ConnectionHeader.HEADERLENGTH:
            raise CouldNotParseKNXIP("wrong connection header length")
        if data[1] != ConnectionHeader.PROTOCOLVERSION:
            raise CouldNotParseKNXIP("wrong protocol version")

        self.header_length = data[0]
        self.protocol_version = data[1]
        self.service_type_ident = KNXIPServiceType(data[2] * 256 + data[3])
        self.b4_reserve = data[4]
        self.total_length = data[5]

    def set_length(self, cemi):
        if not isinstance(cemi, CEMIFrame):
            raise TypeError()
        self.total_length = ConnectionHeader.HEADERLENGTH + \
                           cemi.calculated_length()

    def to_knx(self):
        data = []

        data.append(self.header_length)
        data.append(self.protocol_version)
        data.append((self.service_type_ident.value >> 8) & 255)
        data.append(self.service_type_ident.value & 255)
        data.append((self.total_length>>8) & 255)
        data.append(self.total_length & 255)

        return data

    def __str__(self):
        return "<Connection HeaderLength={0}, ProtocolVersion={1}, " \
                "KNXIPServiceType={2}, Reserve={3}, TotalLength={4}>".format(
                    self.header_length,
                    self.protocol_version,
                    self.service_type_ident,
                    self.b4_reserve,
                    self.total_length)



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

    def set_hops(self, hops):
        # Resetting hops
        self.flags &= 0xFFFF ^ 0x0070
        # Setting new hops
        self.flags |= hops << 4

    def calculated_length(self):
        if self.payload is None:
            return 11
        elif isinstance(self.payload, DPTBinary):
            return 11
        elif isinstance(self.payload, DPTArray):
            return 11 + len(self.payload.value)
        else:
            raise TypeError()

    def from_knx(self, cemi):

        """Create a new CEMIFrame initialized from the given CEMI data."""
        # TODO: check that length matches
        self.code = CEMIMessageCode(cemi[0])
        offset = cemi[1]

        self.flags = cemi[2] * 256 + cemi[3]

        self.src_addr = Address((cemi[4 + offset], cemi[5 + offset]), \
                                AddressType.PHYSICAL)

        dst_addr_type = \
            AddressType.GROUP \
            if self.flags & CEMIFlags.DESTINATION_GROUP_ADDRESS \
            else AddressType.PHYSICAL
        self.dst_addr = Address((cemi[6 + offset], cemi[7 + offset]),
                                dst_addr_type)

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

        #pylint: disable=redefined-variable-type
        if len(apdu) == 1:
            apci = tpci_apci & DPTBinary.APCI_BITMASK
            self.payload = DPTBinary(apci)
        else:
            self.payload = DPTArray(cemi[11 + offset:])

    def to_knx(self):
        """Convert the CEMI frame object to its byte representation."""

        if not isinstance(self.src_addr, Address):
            raise ConversionException("src_add not set")
        if not isinstance(self.dst_addr, Address):
            raise ConversionException("dst_add not set")

        data = []

        data.append(self.code.value)
        data.append(0x00)
        data.append((self.flags >> 8) & 255)
        data.append(self.flags & 255)
        data.append(self.src_addr.byte1()& 255)
        data.append(self.src_addr.byte2()& 255)
        data.append(self.dst_addr.byte1()& 255)
        data.append(self.dst_addr.byte2()& 255)

        def encode_cmd_and_payload(cmd, encoded_payload=0,\
                                   appended_payload=None):
            if appended_payload is None:
                appended_payload = []
            data = [
                1 + len(appended_payload),
                (cmd.value >> 8) & 0xff,
                (cmd.value & 0xff) |
                (encoded_payload & DPTBinary.APCI_BITMASK)]
            data.extend(appended_payload)
            return data

        if self.payload is None:
            data.extend(encode_cmd_and_payload(self.cmd))
        elif isinstance(self.payload, DPTBinary):
            data.extend(encode_cmd_and_payload(self.cmd, \
                        encoded_payload=self.payload.value))
        elif isinstance(self.payload, DPTArray):
            data.extend(encode_cmd_and_payload(self.cmd, \
                        appended_payload=self.payload.value))
        else:
            raise TypeError()

        return data


    def __str__(self):
        return "<CEMIFrame SourceAddress={0}, DestinationAddress={1}, " \
               "Flags={2:16b} Command={3}, payload={4}>".format(
                   self.src_addr,
                   self.dst_addr,
                   self.flags,
                   self.cmd,
                   self.payload)


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

        def resolve_telegram_type(cmd):
            if cmd == APCICommand.GROUP_WRITE:
                return TelegramType.GROUP_WRITE
            elif cmd == APCICommand.GROUP_READ:
                return TelegramType.GROUP_READ
            elif cmd == APCICommand.GROUP_RESPONSE:
                return TelegramType.GROUP_RESPONSE
            else:
                raise ConversionException("Telegram not implemented for {0}" \
                                      .format(self.cemi.cmd))

        telegram.telegramtype = resolve_telegram_type(self.cemi.cmd)

        # TODO: Set telegram.direction [additional flag within KNXIP]
        return telegram

    @telegram.setter
    def telegram(self, telegram):
        self.cemi.dst_addr = telegram.group_address
        self.cemi.payload = telegram.payload

        # TODO: Move to separate function
        self.cemi.code = CEMIMessageCode.L_DATA_IND
        self.cemi.flags = (CEMIFlags.FRAME_TYPE_STANDARD |
                           CEMIFlags.DO_NOT_REPEAT |
                           CEMIFlags.BROADCAST |
                           CEMIFlags.PRIORITY_LOW |
                           CEMIFlags.NO_ACK_REQUESTED |
                           CEMIFlags.CONFIRM_NO_ERROR |
                           CEMIFlags.DESTINATION_GROUP_ADDRESS |
                           CEMIFlags.HOP_COUNT_1ST)

        # TODO: use telegram.direction

        def resolve_cmd(telegramtype):
            if telegramtype == TelegramType.GROUP_READ:
                return APCICommand.GROUP_READ
            elif telegramtype == TelegramType.GROUP_WRITE:
                return APCICommand.GROUP_WRITE
            elif telegramtype == TelegramType.GROUP_RESPONSE:
                return APCICommand.GROUP_RESPONSE
            else:
                raise TypeError()

        self.cemi.cmd = resolve_cmd(telegram.telegramtype)

    def from_knx(self, data):

        self.header.from_knx(data[0:6])
        self.cemi.from_knx(data[6:])

    def __str__(self):
        return "<KNXIPFrame {0}\n{1}>".format(self.header, self.cemi)


    def normalize(self):
        self.header.set_length(self.cemi)

    def to_knx(self):

        data = []
        data.extend(self.header.to_knx())
        data.extend(self.cemi.to_knx())
        return data
