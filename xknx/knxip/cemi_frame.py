from xknx.knx import Address, AddressType, DPTBinary, DPTArray, \
    Telegram, TelegramType

from .knxip_enum import CEMIMessageCode, APCICommand, CEMIFlags
from .body import KNXIPBody
from .exception import CouldNotParseKNXIP, ConversionException

class CEMIFrame(KNXIPBody):
    """Representation of a CEMI Frame."""
    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        """CEMIFrame __init__ object."""
        super(CEMIFrame, self).__init__()
        self.code = CEMIMessageCode.L_DATA_IND
        self.flags = 0
        self.cmd = APCICommand.GROUP_READ
        self.src_addr = Address()
        self.dst_addr = Address()
        self.mpdu_len = 0
        self.payload = None

    @property
    def telegram(self):
        telegram = Telegram()
        telegram.payload = self.payload
        telegram.group_address = self.dst_addr

        def resolve_telegram_type(cmd):
            if cmd == APCICommand.GROUP_WRITE:
                return TelegramType.GROUP_WRITE
            elif cmd == APCICommand.GROUP_READ:
                return TelegramType.GROUP_READ
            elif cmd == APCICommand.GROUP_RESPONSE:
                return TelegramType.GROUP_RESPONSE
            else:
                raise ConversionException("Telegram not implemented for {0}" \
                                      .format(self.cmd))

        telegram.telegramtype = resolve_telegram_type(self.cmd)

        # TODO: Set telegram.direction [additional flag within KNXIP]
        return telegram


    @telegram.setter
    def telegram(self, telegram):

        self.dst_addr = telegram.group_address
        self.payload = telegram.payload

        # TODO: Move to separate function, together with setting of
        # CEMIMessageCode
        self.flags = (CEMIFlags.FRAME_TYPE_STANDARD |
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

        self.cmd = resolve_cmd(telegram.telegramtype)


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
        if len(cemi) < 11:
            raise CouldNotParseKNXIP("CEMI too small")

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

        return 10 + offset + len(apdu)

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
        data.extend(self.src_addr.to_knx())
        data.extend(self.dst_addr.to_knx())

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
