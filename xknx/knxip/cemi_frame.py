"""
Module for serialization and deserialization of KNX/IP CEMI Frame.

cEMI stands for Common External Message Interface

A CEMI frame is the container to transport a KNX/IP Telegram to/from the KNX bus.

Documentation within:

    Application Note 117/08 v02
    KNX IP Communication Medium
    File: AN117 v02.01 KNX IP Communication Medium DV.pdf
"""
from typing import TYPE_CHECKING, List, Optional, Union

from xknx.exceptions import ConversionError, CouldNotParseKNXIP, UnsupportedCEMIMessage
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import APCI

from .knxip_enum import CEMIFlags, CEMIMessageCode

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class CEMIFrame:
    """Representation of a CEMI Frame."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        xknx: "XKNX",
        code: CEMIMessageCode = CEMIMessageCode.L_DATA_IND,
        flags: int = 0,
        src_addr: IndividualAddress = IndividualAddress(None),
        dst_addr: Union[GroupAddress, IndividualAddress] = GroupAddress(None),
        mpdu_len: int = 0,
        payload: Optional[APCI] = None,
    ):
        """Initialize CEMIFrame object."""
        self.xknx = xknx
        self.code = code
        self.flags = flags
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.mpdu_len = mpdu_len
        self.payload = payload

    @staticmethod
    def init_from_telegram(
        xknx: "XKNX",
        telegram: Telegram,
        code: CEMIMessageCode = CEMIMessageCode.L_DATA_IND,
        src_addr: IndividualAddress = IndividualAddress(None),
    ) -> "CEMIFrame":
        """Return CEMIFrame from a Telegram."""
        cemi = CEMIFrame(xknx, code=code, src_addr=src_addr)
        # dst_addr, payload and cmd are set by telegram.setter - mpdu_len not needed for outgoing telegram
        cemi.telegram = telegram
        return cemi

    @property
    def telegram(self) -> Telegram:
        """Return telegram."""

        return Telegram(
            destination_address=self.dst_addr,
            payload=self.payload,
            source_address=self.src_addr,
        )

    @telegram.setter
    def telegram(self, telegram: Telegram) -> None:
        """Set telegram."""
        self.dst_addr = telegram.destination_address
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
            | CEMIFlags.HOP_COUNT_1ST
        )

        if isinstance(telegram.destination_address, GroupAddress):
            self.flags |= CEMIFlags.DESTINATION_GROUP_ADDRESS
        elif isinstance(telegram.destination_address, IndividualAddress):
            self.flags |= CEMIFlags.DESTINATION_INDIVIDUAL_ADDRESS
        else:
            raise TypeError()

    def set_hops(self, hops: int) -> None:
        """Set hops."""
        # Resetting hops
        self.flags &= 0xFFFF ^ 0x0070
        # Setting new hops
        self.flags |= hops << 4

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        if not isinstance(self.payload, APCI):
            raise TypeError()
        return 10 + self.payload.calculated_length()

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        try:
            self.code = CEMIMessageCode(raw[0])
        except ValueError:
            raise UnsupportedCEMIMessage(
                "CEMIMessageCode not implemented: {} in CEMI: {}".format(
                    raw[0], raw.hex()
                )
            )

        if self.code not in (
            CEMIMessageCode.L_DATA_IND,
            CEMIMessageCode.L_DATA_REQ,
            CEMIMessageCode.L_DATA_CON,
        ):
            raise UnsupportedCEMIMessage(
                "Could not handle CEMIMessageCode: {} / {} in CEMI: {}".format(
                    self.code, raw[0], raw.hex()
                )
            )

        return self.from_knx_data_link_layer(raw)

    def from_knx_data_link_layer(self, cemi: bytes) -> int:
        """Parse L_DATA_IND, CEMIMessageCode.L_DATA_REQ, CEMIMessageCode.L_DATA_CON."""
        if len(cemi) < 11:
            # eg. ETS Line-Scan issues L_DATA_IND with length 10
            raise UnsupportedCEMIMessage(
                "CEMI too small. Length: {}; CEMI: {}".format(len(cemi), cemi.hex())
            )

        # AddIL (Additional Info Length), as specified within
        # KNX Chapter 3.6.3/4.1.4.3 "Additional information."
        # Additional information is not yet parsed.
        addil = cemi[1]
        # Control field 1 and Control field 2 - first 2 octets after Additional information
        self.flags = cemi[2 + addil] * 256 + cemi[3 + addil]

        self.src_addr = IndividualAddress((cemi[4 + addil], cemi[5 + addil]))

        if self.flags & CEMIFlags.DESTINATION_GROUP_ADDRESS:
            self.dst_addr = GroupAddress(
                (cemi[6 + addil], cemi[7 + addil]), levels=self.xknx.address_format
            )
        else:
            self.dst_addr = IndividualAddress((cemi[6 + addil], cemi[7 + addil]))

        self.mpdu_len = cemi[8 + addil]

        # TPCI (transport layer control information)   -> First 14 bit
        # APCI (application layer control information) -> Last  10 bit

        apdu = cemi[9 + addil :]
        if len(apdu) != (self.mpdu_len + 1):
            raise CouldNotParseKNXIP(
                "APDU LEN should be {} but is {} in CEMI: {}".format(
                    self.mpdu_len, len(apdu), cemi.hex()
                )
            )

        tpci_apci = (apdu[0] << 8) + apdu[1]

        try:
            self.payload = APCI.resolve_apci(tpci_apci & 0x03FF)
        except ConversionError:
            raise UnsupportedCEMIMessage(
                "APCI not supported: {:#012b}".format(tpci_apci & 0x03FF)
            )

        self.payload.from_knx(apdu)

        return 10 + addil + self.mpdu_len

    def to_knx(self) -> List[int]:
        """Serialize to KNX/IP raw data."""
        if not isinstance(self.payload, APCI):
            raise TypeError()
        if not isinstance(self.src_addr, (GroupAddress, IndividualAddress)):
            raise ConversionError("src_addr not set")
        if not isinstance(self.dst_addr, (GroupAddress, IndividualAddress)):
            raise ConversionError("dst_addr not set")

        data = []

        data.append(self.code.value)
        data.append(0x00)
        data.append((self.flags >> 8) & 255)
        data.append(self.flags & 255)
        data.extend(self.src_addr.to_knx())
        data.extend(self.dst_addr.to_knx())
        data.append(self.payload.calculated_length())
        data.extend(self.payload.to_knx())

        return data

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            '<CEMIFrame SourceAddress="{}" DestinationAddress="{}" '
            'Flags="{:16b}" payload="{}" />'.format(
                self.src_addr.__repr__(),
                self.dst_addr.__repr__(),
                self.flags,
                self.payload,
            )
        )

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__
