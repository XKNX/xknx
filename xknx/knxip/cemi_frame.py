"""
Module for serialization and deserialization of KNX/IP CEMI Frame.

cEMI stands for Common External Message Interface

A CEMI frame is the container to transport a KNX/IP Telegram to/from the KNX bus.

Documentation within:

    Application Note 117/08 v02
    KNX IP Communication Medium
    File: AN117 v02.01 KNX IP Communication Medium DV.pdf
"""
from typing import Union

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseKNXIP, UnsupportedCEMIMessage
from xknx.telegram import GroupAddress, PhysicalAddress, Telegram, TelegramType

from .knxip_enum import APCICommand, CEMIFlags, CEMIMessageCode


class CEMIFrame:
    """Representation of a CEMI Frame."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        xknx,
        code: CEMIMessageCode = CEMIMessageCode.L_DATA_IND,
        flags: int = 0,
        cmd: APCICommand = APCICommand.GROUP_READ,
        src_addr: PhysicalAddress = PhysicalAddress(None),
        dst_addr: Union[GroupAddress, PhysicalAddress] = GroupAddress(None),
        mpdu_len: int = 0,
        payload=None,
    ):
        """Initialize CEMIFrame object."""
        self.xknx = xknx
        self.code = code
        self.flags = flags
        self.cmd = cmd
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.mpdu_len = mpdu_len
        self.payload = payload

    @staticmethod
    def init_from_telegram(
        xknx,
        telegram: Telegram,
        code: CEMIMessageCode = CEMIMessageCode.L_DATA_IND,
        src_addr: PhysicalAddress = PhysicalAddress(None),
    ):
        """Return CEMIFrame from a Telegram."""
        cemi = CEMIFrame(xknx, code=code, src_addr=src_addr)
        # dst_addr, payload and cmd are set by telegram.setter - mpdu_len not needed for outgoing telegram
        cemi.telegram = telegram
        return cemi

    @property
    def telegram(self) -> Telegram:
        """Return telegram."""

        def resolve_telegram_type(cmd):
            """Return telegram type from APCI Command."""
            if cmd == APCICommand.GROUP_WRITE:
                return TelegramType.GROUP_WRITE
            if cmd == APCICommand.GROUP_READ:
                return TelegramType.GROUP_READ
            if cmd == APCICommand.GROUP_RESPONSE:
                return TelegramType.GROUP_RESPONSE
            raise ConversionError(f"Telegram not implemented for {self.cmd}")

        return Telegram(
            group_address=self.dst_addr,
            payload=self.payload,
            telegramtype=resolve_telegram_type(self.cmd),
        )

    @telegram.setter
    def telegram(self, telegram: Telegram):
        """Set telegram."""
        self.dst_addr = telegram.group_address
        self.payload = telegram.payload

        # TODO: Move to separate function, together with setting of
        # CEMIMessageCode
        self.flags = (
            CEMIFlags.FRAME_TYPE_STANDARD
            | CEMIFlags.DO_NOT_REPEAT
            | CEMIFlags.BROADCAST
            | CEMIFlags.PRIORITY_LOW
            | CEMIFlags.NO_ACK_REQUESTED
            | CEMIFlags.CONFIRM_NO_ERROR
            | CEMIFlags.DESTINATION_GROUP_ADDRESS
            | CEMIFlags.HOP_COUNT_1ST
        )

        # TODO: use telegram.direction
        def resolve_cmd(telegramtype: TelegramType) -> APCICommand:
            """Resolve APCICommand from TelegramType."""
            if telegramtype == TelegramType.GROUP_READ:
                return APCICommand.GROUP_READ
            if telegramtype == TelegramType.GROUP_WRITE:
                return APCICommand.GROUP_WRITE
            if telegramtype == TelegramType.GROUP_RESPONSE:
                return APCICommand.GROUP_RESPONSE
            raise TypeError()

        self.cmd = resolve_cmd(telegram.telegramtype)

    def set_hops(self, hops: int):
        """Set hops."""
        # Resetting hops
        self.flags &= 0xFFFF ^ 0x0070
        # Setting new hops
        self.flags |= hops << 4

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        if self.payload is None:
            return 11
        if isinstance(self.payload, DPTBinary):
            return 11
        if isinstance(self.payload, DPTArray):
            return 11 + len(self.payload.value)
        raise TypeError()

    def from_knx(self, raw) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        try:
            self.code = CEMIMessageCode(raw[0])
        except ValueError:
            raise UnsupportedCEMIMessage(
                "CEMIMessageCode not implemented: {} ".format(raw[0])
            )

        if self.code not in (
            CEMIMessageCode.L_DATA_IND,
            CEMIMessageCode.L_Data_REQ,
            CEMIMessageCode.L_DATA_CON,
        ):
            raise UnsupportedCEMIMessage(
                "Could not handle CEMIMessageCode: {} / {}".format(self.code, raw[0])
            )

        return self.from_knx_data_link_layer(raw)

    def from_knx_data_link_layer(self, cemi) -> int:
        """Parse L_DATA_IND, CEMIMessageCode.L_Data_REQ, CEMIMessageCode.L_DATA_CON."""
        if len(cemi) < 11:
            # eg. ETS Line-Scan issues L_DATA_IND with length 10
            raise UnsupportedCEMIMessage(
                "CEMI too small. Length: {}; CEMI: {}".format(len(cemi), cemi)
            )

        # AddIL (Additional Info Length), as specified within
        # KNX Chapter 3.6.3/4.1.4.3 "Additional information."
        # Additional information is not yet parsed.
        addil = cemi[1]
        # Control field 1 and Control field 2 - first 2 octets after Additional information
        self.flags = cemi[2 + addil] * 256 + cemi[3 + addil]

        self.src_addr = PhysicalAddress((cemi[4 + addil], cemi[5 + addil]))

        if self.flags & CEMIFlags.DESTINATION_GROUP_ADDRESS:
            self.dst_addr = GroupAddress(
                (cemi[6 + addil], cemi[7 + addil]), levels=self.xknx.address_format
            )
        else:
            self.dst_addr = PhysicalAddress((cemi[6 + addil], cemi[7 + addil]))

        self.mpdu_len = cemi[8 + addil]

        # TPCI (transport layer control information)   -> First 14 bit
        # APCI (application layer control information) -> Last  10 bit

        tpci_apci = cemi[9 + addil] * 256 + cemi[10 + addil]

        try:
            self.cmd = APCICommand(tpci_apci & 0xFFC0)
        except ValueError:
            raise UnsupportedCEMIMessage(
                "APCI not supported: {:#012b}".format(tpci_apci & 0xFFC0)
            )

        apdu = cemi[10 + addil :]
        if len(apdu) != self.mpdu_len:
            raise CouldNotParseKNXIP(
                "APDU LEN should be {} but is {}".format(self.mpdu_len, len(apdu))
            )

        if len(apdu) == 1:
            apci = tpci_apci & DPTBinary.APCI_BITMASK
            self.payload = DPTBinary(apci)
        else:
            self.payload = DPTArray(cemi[11 + addil :])

        return 10 + addil + len(apdu)

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        if not isinstance(self.src_addr, (GroupAddress, PhysicalAddress)):
            raise ConversionError("src_addr not set")
        if not isinstance(self.dst_addr, (GroupAddress, PhysicalAddress)):
            raise ConversionError("dst_addr not set")

        data = []

        data.append(self.code.value)
        data.append(0x00)
        data.append((self.flags >> 8) & 255)
        data.append(self.flags & 255)
        data.extend(self.src_addr.to_knx())
        data.extend(self.dst_addr.to_knx())

        def encode_cmd_and_payload(cmd, encoded_payload=0, appended_payload=None):
            """Encode cmd and payload."""
            if appended_payload is None:
                appended_payload = []
            data = [
                1 + len(appended_payload),
                (cmd.value >> 8) & 0xFF,
                (cmd.value & 0xFF) | (encoded_payload & DPTBinary.APCI_BITMASK),
            ]
            data.extend(appended_payload)
            return data

        if self.payload is None:
            data.extend(encode_cmd_and_payload(self.cmd))
        elif isinstance(self.payload, DPTBinary):
            data.extend(
                encode_cmd_and_payload(self.cmd, encoded_payload=self.payload.value)
            )
        elif isinstance(self.payload, DPTArray):
            data.extend(
                encode_cmd_and_payload(self.cmd, appended_payload=self.payload.value)
            )
        else:
            raise TypeError()
        return data

    def __str__(self):
        """Return object as readable string."""
        return (
            '<CEMIFrame SourceAddress="{}" DestinationAddress="{}" '
            'Flags="{:16b}" Command="{}" payload="{}" />'.format(
                self.src_addr.__repr__(),
                self.dst_addr.__repr__(),
                self.flags,
                self.cmd,
                self.payload,
            )
        )

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
