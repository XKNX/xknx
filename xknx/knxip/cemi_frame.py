"""
Module for serialization and deserialization of KNX/IP CEMI Frame.

cEMI stands for Common External Message Interface

A CEMI frame is the container to transport a KNX/IP Telegram to/from the KNX bus.

Documentation within:

    Application Note 117/08 v02
    KNX IP Communication Medium
    File: AN117 v02.01 KNX IP Communication Medium DV.pdf
"""
from __future__ import annotations

from xknx.exceptions import ConversionError, CouldNotParseKNXIP, UnsupportedCEMIMessage
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import APCI
from xknx.telegram.tpci import TPCI, TDataGroup

from .knxip_enum import CEMIFlags, CEMIMessageCode


class CEMIFrame:
    """Representation of a CEMI Frame."""

    def __init__(
        self,
        code: CEMIMessageCode = CEMIMessageCode.L_DATA_IND,
        flags: int = 0,
        src_addr: IndividualAddress = IndividualAddress(None),
        dst_addr: GroupAddress | IndividualAddress = GroupAddress(None),
        tpci: TPCI = TDataGroup(),
        payload: APCI | None = None,
    ):
        """Initialize CEMIFrame object."""
        self.code = code
        self.flags = flags
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.tpci = tpci
        self.payload = payload

    @staticmethod
    def init_from_telegram(
        telegram: Telegram,
        code: CEMIMessageCode = CEMIMessageCode.L_DATA_IND,
        src_addr: IndividualAddress = IndividualAddress(None),
    ) -> CEMIFrame:
        """Return CEMIFrame from a Telegram."""
        cemi = CEMIFrame(code=code, src_addr=src_addr)
        # dst_addr, payload and cmd are set by telegram.setter
        cemi.telegram = telegram
        return cemi

    @property
    def telegram(self) -> Telegram:
        """Return telegram."""

        return Telegram(
            destination_address=self.dst_addr,
            payload=self.payload,
            source_address=self.src_addr,
            tpci=self.tpci,
        )

    @telegram.setter
    def telegram(self, telegram: Telegram) -> None:
        """Set telegram."""
        # TODO: Move to separate function, together with setting of
        # CEMIMessageCode
        self.flags = (
            CEMIFlags.FRAME_TYPE_STANDARD
            | CEMIFlags.DO_NOT_REPEAT
            | CEMIFlags.BROADCAST
            | CEMIFlags.NO_ACK_REQUESTED
            | CEMIFlags.CONFIRM_NO_ERROR
            | CEMIFlags.HOP_COUNT_1ST
        )

        if isinstance(telegram.destination_address, GroupAddress):
            self.flags |= CEMIFlags.DESTINATION_GROUP_ADDRESS | CEMIFlags.PRIORITY_LOW
        elif isinstance(telegram.destination_address, IndividualAddress):
            self.flags |= (
                CEMIFlags.DESTINATION_INDIVIDUAL_ADDRESS | CEMIFlags.PRIORITY_SYSTEM
            )
        else:
            raise TypeError()

        self.dst_addr = telegram.destination_address
        self.tpci = telegram.tpci
        self.payload = telegram.payload

    def set_hops(self, hops: int) -> None:
        """Set hops."""
        # Resetting hops
        self.flags &= 0xFFFF ^ 0x0070
        # Setting new hops
        self.flags |= hops << 4

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        if not self.tpci.control and self.payload is not None:
            return 10 + self.payload.calculated_length()
        if self.tpci.control and self.payload is None:
            return 10
        raise TypeError("Data TPDU must have a payload; control TPDU must not.")

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        try:
            self.code = CEMIMessageCode(raw[0])
        except ValueError:
            raise UnsupportedCEMIMessage(
                f"CEMIMessageCode not implemented: {raw[0]} in CEMI: {raw.hex()}"
            )

        if self.code not in (
            CEMIMessageCode.L_DATA_IND,
            CEMIMessageCode.L_DATA_REQ,
            CEMIMessageCode.L_DATA_CON,
        ):
            raise UnsupportedCEMIMessage(
                f"Could not handle CEMIMessageCode: {self.code} / {raw[0]} in CEMI: {raw.hex()}"
            )

        return self.from_knx_data_link_layer(raw)

    def from_knx_data_link_layer(self, cemi: bytes) -> int:
        """Parse L_DATA_IND, CEMIMessageCode.L_DATA_REQ, CEMIMessageCode.L_DATA_CON."""
        if len(cemi) < 10:
            raise UnsupportedCEMIMessage(
                f"CEMI too small. Length: {len(cemi)}; CEMI: {cemi.hex()}"
            )

        # AddIL (Additional Info Length), as specified within
        # KNX Chapter 3.6.3/4.1.4.3 "Additional information."
        # Additional information is not yet parsed.
        addil = cemi[1]
        # Control field 1 and Control field 2 - first 2 octets after Additional information
        self.flags = cemi[2 + addil] * 256 + cemi[3 + addil]

        self.src_addr = IndividualAddress((cemi[4 + addil], cemi[5 + addil]))

        dst_is_group_address = bool(self.flags & CEMIFlags.DESTINATION_GROUP_ADDRESS)
        dst_raw_address = (cemi[6 + addil], cemi[7 + addil])
        self.dst_addr = (
            GroupAddress(dst_raw_address)
            if dst_is_group_address
            else IndividualAddress(dst_raw_address)
        )

        npdu_len = cemi[8 + addil]

        apdu = cemi[9 + addil :]
        if len(apdu) != (npdu_len + 1):  # TCPI octet not included in NPDU length
            raise CouldNotParseKNXIP(
                f"APDU LEN should be {npdu_len} but is {len(apdu) - 1} in CEMI: {cemi.hex()}"
            )

        # TPCI (transport layer control information)
        # - with control bit set -> 8 bit; no APDU
        # - no control bit set (data) -> First 6 bit
        # APCI (application layer control information) -> Last  10 bit of TPCI/APCI
        try:
            self.tpci = TPCI.resolve(
                raw_tpci=cemi[9 + addil], dst_is_group_address=dst_is_group_address
            )
        except ConversionError as err:
            raise UnsupportedCEMIMessage(
                f"TPCI not supported: {cemi[9 + addil]:#10b}"
            ) from err

        if self.tpci.control:
            if npdu_len:
                raise UnsupportedCEMIMessage(
                    f"Invalid length for control TPDU {self.tpci}: {npdu_len}"
                )
            return 10 + addil

        _apci = apdu[0] * 256 + apdu[1]
        try:
            self.payload = APCI.resolve_apci(_apci)
        except ConversionError as err:
            raise UnsupportedCEMIMessage(f"APCI not supported: {_apci:#012b}") from err

        self.payload.from_knx(apdu)

        return 10 + addil + npdu_len

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.tpci.control:
            tpdu = bytes([self.tpci.to_knx()])
            npdu_len = 0
        else:
            if not isinstance(self.payload, APCI):
                raise ConversionError(
                    f"Invalid payload set for data TPDU: {self.payload.__class__}"
                )
            tpdu = self.payload.to_knx()
            tpdu[0] |= self.tpci.to_knx()
            npdu_len = self.payload.calculated_length()

        if not isinstance(self.src_addr, IndividualAddress):
            raise ConversionError("src_addr invalid")
        if not isinstance(self.dst_addr, (GroupAddress, IndividualAddress)):
            raise ConversionError("dst_addr invalid")

        return (
            bytes(
                (
                    self.code.value,
                    0x00,  # Additional information length
                )
            )
            + self.flags.to_bytes(2, "big")
            + bytes(
                (
                    *self.src_addr.to_knx(),
                    *self.dst_addr.to_knx(),
                    npdu_len,
                )
            )
            + tpdu
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<CEMIFrame "
            f'code="{self.code.name}" '
            f'src_addr="{self.src_addr.__repr__()}" '
            f'dst_addr="{self.dst_addr.__repr__()}" '
            f'flags="{self.flags:16b}" '
            f'tpci="{self.tpci}" '
            f'payload="{self.payload}" />'
        )

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__
