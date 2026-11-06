"""
Frames of the KNX TP1 medium as received in a cEMI L_Busmon.ind.

KNX v01.03.03 - Communication Medium TP1 03.02.02 - §2.2 specifies the frame formats:

    L_Data_Standard     CTRL  SA SA  DA DA  AT|HC|LG       TPDU  FCS
    L_Data_Extended     CTRL  CTRLE  SA SA  DA DA  LG      TPDU  FCS
    Acknowledgement     ACK (CCh), NAK (0Ch), BUSY (C0h) or NAK+BUSY (00h)

The TPDU starts with the TPCI octet; the length field counts the octets after it.
The check octet (FCS) is a NOT XOR over all preceding octets of the frame.
"""

from __future__ import annotations

from enum import IntEnum

from xknx.exceptions import ConversionError, CouldNotParseCEMI, UnsupportedCEMIMessage
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, TelegramDirection

from .cemi_frame import CEMILData
from .const import MAX_NPDU_LENGTH, STANDARD_FRAME_MAX_NPDU_LENGTH
from .flags import (
    BROADCAST,
    DO_NOT_REPEAT,
    EXTENDED_FRAME_FORMAT_MASK,
    HOP_COUNT_MASK,
    HOP_COUNT_OFFSET,
    MAX_HOP_COUNT,
    PRIORITY_MASK,
    PRIORITY_OFFSET,
    CEMIAddressType,
    CEMIFrameType,
    CEMIPriority,
)

# Control field of an L_Data frame: FT 0 r 1 p1 p0 0 0
# KNX v01.03.03 - Communication Medium TP1 03.02.02 - §2.2.2
_L_DATA_CTRL_MASK = 0b0101_0011
_L_DATA_CTRL_VALUE = 0b0001_0000
_L_POLL_DATA_CTRL = 0xF0
# length field of an L_Data_Standard frame in the octet holding AT and hop count
_STANDARD_LENGTH_MASK = 0x0F
# CTRL (+ CTRLE), SA, DA, length and TPCI octet - and the check octet
_STANDARD_OVERHEAD = 8
_EXTENDED_OVERHEAD = 9


class TP1Acknowledgement(IntEnum):
    """
    Short acknowledgement frame of the TP1 medium.

    KNX v01.03.03 - Communication Medium TP1 03.02.02 - §2.2.7
    """

    ACK = 0xCC
    NAK = 0x0C
    BUSY = 0xC0
    # BUSY and NAK sent at the same time - shall be handled as BUSY
    NAK_BUSY = 0x00

    @property
    def busy(self) -> bool:
        """Return True for BUSY and NAK+BUSY."""
        return self in (TP1Acknowledgement.BUSY, TP1Acknowledgement.NAK_BUSY)

    @classmethod
    def from_knx(cls, raw: bytes) -> TP1Acknowledgement:
        """Parse a single octet acknowledgement frame."""
        if len(raw) != 1:
            raise CouldNotParseCEMI(
                f"Invalid TP1 acknowledgement frame length: {len(raw)}; "
                f"frame: {raw.hex()}"
            )
        try:
            return cls(raw[0])
        except ValueError:
            raise UnsupportedCEMIMessage(
                f"Unknown TP1 acknowledgement frame: {raw.hex()}"
            ) from None

    def to_knx(self) -> bytes:
        """Serialize to the raw frame."""
        return bytes((self.value,))


class TP1DataFrame:
    """
    L_Data_Standard or L_Data_Extended frame of the TP1 medium.

    `tpdu` holds the TPCI octet and the following octets as received, so the
    frame can be decoded even if its APDU is not supported by xknx. Use
    `cemi_l_data()` or `telegram()` to parse it.

    `checksum` is the check octet as received. If not given, it is calculated
    from the other fields.
    """

    __slots__ = (
        "checksum",
        "dst_addr",
        "frame_type",
        "hop_count",
        "priority",
        "repeated",
        "src_addr",
        "tpdu",
    )

    def __init__(
        self,
        *,
        src_addr: IndividualAddress,
        dst_addr: GroupAddress | IndividualAddress,
        tpdu: bytes,
        priority: CEMIPriority = CEMIPriority.LOW,
        repeated: bool = False,
        hop_count: int = 6,
        frame_type: CEMIFrameType = CEMIFrameType.STANDARD,
        checksum: int | None = None,
    ) -> None:
        """Initialize TP1DataFrame object."""
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.tpdu = tpdu
        self.priority = priority
        self.repeated = repeated
        self.hop_count = hop_count
        self.frame_type = frame_type
        self.checksum: int = (
            checksum
            if checksum is not None
            else calculate_checksum(self._to_knx_without_checksum())
        )

    @property
    def address_type(self) -> CEMIAddressType:
        """Return the Address Type of the destination address."""
        return (
            CEMIAddressType.GROUP
            if isinstance(self.dst_addr, GroupAddress)
            else CEMIAddressType.INDIVIDUAL
        )

    @property
    def checksum_valid(self) -> bool:
        """Return True if the check octet matches the other octets of the frame."""
        return self.checksum == calculate_checksum(self._to_knx_without_checksum())

    @classmethod
    def from_knx(cls, raw: bytes) -> TP1DataFrame:
        """Parse an L_Data_Standard or L_Data_Extended frame."""
        if len(raw) < _STANDARD_OVERHEAD:
            raise CouldNotParseCEMI(f"TP1 frame too small: {raw.hex()}")
        ctrl = raw[0]
        if ctrl & _L_DATA_CTRL_MASK != _L_DATA_CTRL_VALUE:
            raise UnsupportedCEMIMessage(
                f"No TP1 L_Data frame. Control field: {ctrl:#04x}; frame: {raw.hex()}"
            )
        if CEMIFrameType.from_knx(ctrl << 8) is CEMIFrameType.STANDARD:
            # AT, hop count and length share one octet
            ctrl_2 = raw[5] & ~_STANDARD_LENGTH_MASK
            length = raw[5] & _STANDARD_LENGTH_MASK
            addresses = raw[1:5]
            tpdu_start = 6
            expected_length = _STANDARD_OVERHEAD + length
        else:
            ctrl_2 = raw[1]
            length = raw[6]
            addresses = raw[2:6]
            tpdu_start = 7
            expected_length = _EXTENDED_OVERHEAD + length
            # only EFF 0000b uses standard addresses
            # KNX v01.03.03 - Communication Medium TP1 03.02.02 - §2.2.5.5
            if _eff := ctrl_2 & EXTENDED_FRAME_FORMAT_MASK:
                raise UnsupportedCEMIMessage(
                    f"Extended Frame Format not supported: {_eff:#06b}; "
                    f"frame: {raw.hex()}"
                )
            if length > MAX_NPDU_LENGTH:
                raise UnsupportedCEMIMessage(
                    f"TP1 frame length escape code not supported; frame: {raw.hex()}"
                )
        if len(raw) != expected_length:
            raise CouldNotParseCEMI(
                f"TP1 frame length should be {expected_length} but is {len(raw)}; "
                f"frame: {raw.hex()}"
            )
        # same layout as the cEMI control fields Ctrl1 and Ctrl2
        control_field = ctrl << 8 | ctrl_2
        address_type = CEMIAddressType.from_knx(control_field)
        return cls(
            src_addr=IndividualAddress.from_knx(addresses[0:2]),
            dst_addr=(
                GroupAddress.from_knx(addresses[2:4])
                if address_type is CEMIAddressType.GROUP
                else IndividualAddress.from_knx(addresses[2:4])
            ),
            tpdu=raw[tpdu_start:-1],
            priority=CEMIPriority((control_field & PRIORITY_MASK) >> PRIORITY_OFFSET),
            repeated=not control_field & DO_NOT_REPEAT,
            hop_count=(control_field & HOP_COUNT_MASK) >> HOP_COUNT_OFFSET,
            frame_type=CEMIFrameType.from_knx(control_field),
            checksum=raw[-1],
        )

    def _control_field(self) -> int:
        """Return the Control field and the AT / hop count bits as one 16 bit value."""
        if not 0 <= self.hop_count <= MAX_HOP_COUNT:
            raise ConversionError(f"Hop count out of range: {self.hop_count}")
        return (
            self.frame_type.to_knx()
            | (0 if self.repeated else DO_NOT_REPEAT)
            | BROADCAST
            | (self.priority << PRIORITY_OFFSET)
            | self.address_type.to_knx()
            | (self.hop_count << HOP_COUNT_OFFSET)
        )

    def _to_knx_without_checksum(self) -> bytes:
        """Serialize all octets of the frame except the check octet."""
        if not self.tpdu:
            raise ConversionError("TPDU of a TP1 frame requires a TPCI octet")
        length = len(self.tpdu) - 1
        ctrl, ctrl_2 = self._control_field().to_bytes(2, "big")
        addresses = self.src_addr.to_knx() + self.dst_addr.to_knx()
        if self.frame_type is CEMIFrameType.STANDARD:
            if length > STANDARD_FRAME_MAX_NPDU_LENGTH:
                raise ConversionError(
                    f"TPDU too long for an L_Data_Standard frame: {length} octets "
                    "after the TPCI octet"
                )
            return bytes((ctrl,)) + addresses + bytes((ctrl_2 | length,)) + self.tpdu
        if length > MAX_NPDU_LENGTH:
            raise ConversionError(
                f"TPDU too long for an L_Data_Extended frame: {length} octets "
                "after the TPCI octet"
            )
        return bytes((ctrl, ctrl_2)) + addresses + bytes((length,)) + self.tpdu

    def to_knx(self) -> bytes:
        """Serialize to the raw frame."""
        return self._to_knx_without_checksum() + bytes((self.checksum,))

    def cemi_l_data(self) -> CEMILData:
        """
        Parse the frame to CEMILData.

        Raise `CouldNotParseCEMI` or `UnsupportedCEMIMessage` if the TPDU can not be
        parsed.
        """
        return CEMILData.from_knx(
            self._control_field().to_bytes(2, "big")
            + self.src_addr.to_knx()
            + self.dst_addr.to_knx()
            + bytes((len(self.tpdu) - 1,))
            + self.tpdu
        )

    def telegram(self) -> Telegram:
        """
        Return an incoming Telegram from the frame.

        Raise `CouldNotParseCEMI` or `UnsupportedCEMIMessage` if the TPDU can not be
        parsed.
        """
        telegram = self.cemi_l_data().telegram()
        telegram.direction = TelegramDirection.INCOMING
        return telegram

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        if not isinstance(other, TP1DataFrame):
            return NotImplemented
        return all(
            getattr(self, attribute) == getattr(other, attribute)
            for attribute in self.__slots__
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "TP1DataFrame("
            f'src_addr="{self.src_addr}" '
            f'dst_addr="{self.dst_addr}" '
            f"priority={self.priority.name} "
            f"frame_type={self.frame_type.name} "
            f"repeated={self.repeated} "
            f"hop_count={self.hop_count} "
            f'tpdu="{self.tpdu.hex()}" '
            f"checksum_valid={self.checksum_valid})"
        )


def calculate_checksum(raw: bytes) -> int:
    """
    Return the check octet for the given octets of a frame.

    NOT XOR over all octets
    KNX v01.03.03 - Communication Medium TP1 03.02.02 - §2.2.4.6
    """
    checksum = 0xFF
    for octet in raw:
        checksum ^= octet
    return checksum


def parse_tp1_frame(raw: bytes) -> TP1DataFrame | TP1Acknowledgement:
    """
    Parse a raw frame of the TP1 medium.

    A single octet is an acknowledgement frame. Raise `CouldNotParseCEMI` for a
    malformed frame and `UnsupportedCEMIMessage` for an L_Poll_Data frame or an
    unknown Control field.
    """
    if not raw:
        raise CouldNotParseCEMI("Empty TP1 frame")
    if len(raw) == 1:
        return TP1Acknowledgement.from_knx(raw)
    if raw[0] == _L_POLL_DATA_CTRL:
        raise UnsupportedCEMIMessage(
            f"TP1 L_Poll_Data frame not supported: {raw.hex()}"
        )
    return TP1DataFrame.from_knx(raw)
