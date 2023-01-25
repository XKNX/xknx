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

from xknx.exceptions import ConversionError, UnsupportedCEMIMessage
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import APCI
from xknx.telegram.tpci import TPCI, TDataBroadcast

from .const import CEMIFlags, CEMIMessageCode


class CEMIFrame:
    """Representation of a CEMI Frame."""

    def __init__(
        self,
        *,
        code: CEMIMessageCode,
        flags: int,
        src_addr: IndividualAddress,
        dst_addr: GroupAddress | IndividualAddress,
        tpci: TPCI,
        payload: APCI | None,
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
        src_addr: IndividualAddress | None = None,
    ) -> CEMIFrame:
        """Return CEMIFrame from a Telegram."""
        flags = (
            CEMIFlags.FRAME_TYPE_STANDARD
            | CEMIFlags.DO_NOT_REPEAT
            | CEMIFlags.BROADCAST
            | CEMIFlags.NO_ACK_REQUESTED
            | CEMIFlags.CONFIRM_NO_ERROR
            | CEMIFlags.HOP_COUNT_1ST
        )
        if isinstance(telegram.destination_address, GroupAddress):
            flags |= CEMIFlags.DESTINATION_GROUP_ADDRESS
            if isinstance(telegram.tpci, TDataBroadcast):
                flags |= CEMIFlags.PRIORITY_SYSTEM
            else:
                flags |= CEMIFlags.PRIORITY_LOW
        elif isinstance(telegram.destination_address, IndividualAddress):
            flags |= (
                CEMIFlags.DESTINATION_INDIVIDUAL_ADDRESS | CEMIFlags.PRIORITY_SYSTEM
            )
        else:
            raise TypeError()

        return CEMIFrame(
            code=code,
            flags=flags,
            src_addr=src_addr or telegram.source_address,
            dst_addr=telegram.destination_address,
            tpci=telegram.tpci,
            payload=telegram.payload,
        )

    @property
    def telegram(self) -> Telegram:
        """Return telegram."""

        return Telegram(
            destination_address=self.dst_addr,
            payload=self.payload,
            source_address=self.src_addr,
            tpci=self.tpci,
        )

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

    @staticmethod
    def from_knx(raw: bytes) -> CEMIFrame:
        """Parse/deserialize from KNX/IP raw data."""
        try:
            code = CEMIMessageCode(raw[0])
        except ValueError:
            raise UnsupportedCEMIMessage(
                f"CEMIMessageCode not implemented: {raw[0]} in CEMI: {raw.hex()}"
            )

        if code in (
            CEMIMessageCode.L_DATA_IND,
            CEMIMessageCode.L_DATA_REQ,
            CEMIMessageCode.L_DATA_CON,
        ):
            return CEMIFrame.from_knx_data_link_layer(raw, code)

        raise UnsupportedCEMIMessage(
            f"Could not handle CEMIMessageCode: {code} / {raw[0]} in CEMI: {raw.hex()}"
        )

    @staticmethod
    def from_knx_data_link_layer(cemi: bytes, code: CEMIMessageCode) -> CEMIFrame:
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
        flags = cemi[2 + addil] * 256 + cemi[3 + addil]

        src_addr = IndividualAddress.from_knx(cemi[4 + addil : 6 + addil])

        _dst_is_group_address = bool(flags & CEMIFlags.DESTINATION_GROUP_ADDRESS)
        dst_addr: GroupAddress | IndividualAddress = (
            GroupAddress.from_knx(cemi[6 + addil : 8 + addil])
            if _dst_is_group_address
            else IndividualAddress.from_knx(cemi[6 + addil : 8 + addil])
        )

        _npdu_len = cemi[8 + addil]
        _tpdu = cemi[9 + addil :]
        _apdu = bytes([_tpdu[0] & 0b11]) + _tpdu[1:]  # clear TPCI bits
        if len(_apdu) != (_npdu_len + 1):  # TCPI octet not included in NPDU length
            raise UnsupportedCEMIMessage(
                f"APDU LEN should be {_npdu_len} but is {len(_apdu) - 1} in CEMI: {cemi.hex()}"
            )

        # TPCI (transport layer control information)
        # - with control bit set -> 8 bit; no APDU
        # - no control bit set (data) -> First 6 bit
        # APCI (application layer control information) -> Last  10 bit of TPCI/APCI
        try:
            tpci = TPCI.resolve(
                raw_tpci=_tpdu[0],
                dst_is_group_address=_dst_is_group_address,
                dst_is_zero=not dst_addr.raw,
            )
        except ConversionError as err:
            raise UnsupportedCEMIMessage(
                f"TPCI not supported: {_tpdu[0]:#10b}"
            ) from err

        if tpci.control:
            if _npdu_len:
                raise UnsupportedCEMIMessage(
                    f"Invalid length for control TPDU {tpci}: {_npdu_len}"
                )
            return CEMIFrame(
                code=code,
                flags=flags,
                src_addr=src_addr,
                dst_addr=dst_addr,
                tpci=tpci,
                payload=None,
            )

        try:
            payload = APCI.from_knx(_apdu)
        except ConversionError as err:
            raise UnsupportedCEMIMessage("APDU not supported") from err

        return CEMIFrame(
            code=code,
            flags=flags,
            src_addr=src_addr,
            dst_addr=dst_addr,
            tpci=tpci,
            payload=payload,
        )

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.tpci.control:
            tpdu = self.tpci.to_knx().to_bytes(1, "big")
            npdu_len = 0
        else:
            if not isinstance(self.payload, APCI):
                raise ConversionError(
                    f"Invalid payload set for data TPDU: {type(self.payload)}"
                )
            tpdu = self.payload.to_knx()
            tpdu[0] |= self.tpci.to_knx()
            npdu_len = self.payload.calculated_length()

        return (
            bytes(
                (
                    self.code.value,
                    0x00,  # Additional information length
                )
            )
            + self.flags.to_bytes(2, "big")
            + self.src_addr.to_knx()
            + self.dst_addr.to_knx()
            + npdu_len.to_bytes(1, "big")
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
