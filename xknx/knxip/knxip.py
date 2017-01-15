from xknx.knx import Address, AddressType, Telegram, TelegramType
from .knxip_enum import CEMIMessageCode,\
    APCICommand, CEMIFlags
from .header import KNXIPHeader
from .cemi_frame import CEMIFrame
from .exception import ConversionException

class KNXIPFrame:
    """Abstraction for KNX IP Frames"""


    def __init__(self):
        """Initialize object."""

        self.cemi = CEMIFrame()
        self.header = KNXIPHeader()

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
