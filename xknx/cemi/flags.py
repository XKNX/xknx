"""
Control fields of a cEMI L_Data frame.

The two control field octets Ctrl1 and Ctrl2 are specified in
3/6/3 EMI_IMI §4.1.4.3.2 and 3/2/2 Communication Medium TP1 §2.2.2 / §2.2.5.3.

    Ctrl1                            Ctrl2
    7  6  5  4  3  2  1  0           7  6  5  4  3  2  1  0
    FT  r  R SB  P  P  A  C          AT  H  H  H  E  E  E  E

Not every field is independent state: the Frame Type (FT) follows from the NPDU
length and the Address Type (AT) from the destination address, so both are
derived when serializing - see `CEMILData`. The received Frame Type is still kept
for inspection; the Address Type can be read from the type of the destination
address.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from xknx.exceptions import ConversionError

# Ctrl1 and Ctrl2 are handled as one 16 bit value: Ctrl1 << 8 | Ctrl2.
# The Frame Type and Address Type bits are not listed here - `CEMIFrameType` and
# `CEMIAddressType` place their own bit.
# Ctrl1
DO_NOT_REPEAT = 0b00100000_00000000
BROADCAST = 0b00010000_00000000
PRIORITY_MASK = 0b00001100_00000000
PRIORITY_OFFSET = 10
ACK_REQUESTED = 0b00000010_00000000
CONFIRM_ERROR = 0b00000001_00000000

# Ctrl2
HOP_COUNT_MASK = 0b00000000_01110000
HOP_COUNT_OFFSET = 4
EXTENDED_FRAME_FORMAT_MASK = 0b00000000_00001111

MAX_HOP_COUNT = 7


class CEMIPriority(IntEnum):
    """Priority of a cEMI L_Data frame. See 3/2/2 §2.2.2 Figure 28."""

    SYSTEM = 0b00
    NORMAL = 0b01
    URGENT = 0b10
    LOW = 0b11


class CEMIFrameType(IntEnum):
    """
    Frame Type of a cEMI L_Data frame. See 3/6/3 §4.1.4.3.2.

    An L_Data_Standard frame carries at most 15 octets after the TPCI octet;
    longer APDUs require an L_Data_Extended frame - 3/2/2 §2.2.4 and §2.2.5.1.
    """

    EXTENDED = 0
    STANDARD = 1

    def to_knx(self) -> int:
        """Serialize to the Frame Type bit of the control field - Ctrl1 b7."""
        return self << 15

    @classmethod
    def from_knx(cls, raw: int) -> CEMIFrameType:
        """Parse the Frame Type bit from the control field."""
        return cls(raw >> 15 & 0b1)


class CEMIAddressType(IntEnum):
    """
    Destination Address Type of a cEMI L_Data frame. See 3/6/3 §4.1.4.3.2.

    Follows from the type of the destination address, so it is not held by
    `CEMIFlags` - see `CEMILData.address_type`.
    """

    INDIVIDUAL = 0
    GROUP = 1

    def to_knx(self) -> int:
        """Serialize to the Address Type bit of the control field - Ctrl2 b7."""
        return self << 7

    @classmethod
    def from_knx(cls, raw: int) -> CEMIAddressType:
        """Parse the Address Type bit from the control field."""
        return cls(raw >> 7 & 0b1)


class CEMIFrameFormat(IntEnum):
    """
    Extended Frame Format (EFF) of a cEMI L_Data frame. See 3/2/2 §2.2.5.3.

    `STANDARD` is used for L_Data_Standard frames as well as for long
    L_Data_Extended frames. `LTE_HEE` covers 01xxb - the two least significant
    bits hold the LTE extended address type. All other values are reserved.
    """

    STANDARD = 0b0000
    LTE_HEE = 0b0100

    @classmethod
    def _missing_(cls, value: object) -> CEMIFrameFormat | None:
        """Resolve the whole 01xxb range to LTE_HEE; reserved values fail."""
        if isinstance(value, int) and value & 0b1100 == cls.LTE_HEE:
            return cls.LTE_HEE
        return None


@dataclass(slots=True)
class CEMIFlags:
    """
    Control fields of a cEMI L_Data frame.

    `frame_type` is informational: it holds what was received and is ignored when
    serializing, as the Frame Type of an outgoing frame follows from its NPDU length
    and is passed to `to_knx()` by the frame. The Address Type is not held at all -
    it can be read from the type of the destination address. The Extended Frame
    Format does not follow from anything else, so `frame_format` is serialized as
    held; it is `STANDARD` for every frame xknx currently supports.

    `confirm_error` is only meaningful in an L_Data.con frame.
    """

    priority: CEMIPriority = CEMIPriority.LOW
    # `repeat_on_error` and `system_broadcast` are inverted on the wire
    repeat_on_error: bool = False
    system_broadcast: bool = False
    acknowledge_request: bool = False
    confirm_error: bool = False
    hop_count: int = 6
    # as received; not used when serializing
    frame_type: CEMIFrameType = CEMIFrameType.STANDARD
    frame_format: CEMIFrameFormat = CEMIFrameFormat.STANDARD

    def to_knx(self) -> int:
        """
        Serialize the control field bits held by this object.

        The Frame Type and Address Type bits are left clear; the frame ORs them in
        from `CEMIFrameType.to_knx()` and `CEMIAddressType.to_knx()`. `self.frame_type`
        holds the Frame Type of a received frame and is not used here. The Extended
        Frame Format is serialized - Data Secure protects it, so the value on the
        wire and the one fed to the MAC have to come from the same place.
        """
        if not 0 <= self.hop_count <= MAX_HOP_COUNT:
            raise ConversionError(f"Hop count out of range: {self.hop_count}")

        return (
            (0 if self.repeat_on_error else DO_NOT_REPEAT)
            | (0 if self.system_broadcast else BROADCAST)
            | (self.priority << PRIORITY_OFFSET)
            | (ACK_REQUESTED if self.acknowledge_request else 0)
            | (CONFIRM_ERROR if self.confirm_error else 0)
            | (self.hop_count << HOP_COUNT_OFFSET)
            | self.frame_format
        )

    @classmethod
    def from_knx(cls, raw: int) -> CEMIFlags:
        """
        Parse the control field.

        Raise `ConversionError` for a reserved Extended Frame Format. The Frame Type
        is kept but not evaluated: "any receiver shall be tolerant towards the use of
        the Frame Format" - 3/6/3 §4.1.5.2.3.
        """
        _eff = raw & EXTENDED_FRAME_FORMAT_MASK
        try:
            frame_format = CEMIFrameFormat(_eff)
        except ValueError:
            raise ConversionError(
                f"Reserved Extended Frame Format: {_eff:#06b}"
            ) from None

        return cls(
            priority=CEMIPriority((raw & PRIORITY_MASK) >> PRIORITY_OFFSET),
            repeat_on_error=not raw & DO_NOT_REPEAT,
            system_broadcast=not raw & BROADCAST,
            acknowledge_request=bool(raw & ACK_REQUESTED),
            confirm_error=bool(raw & CONFIRM_ERROR),
            hop_count=(raw & HOP_COUNT_MASK) >> HOP_COUNT_OFFSET,
            frame_type=CEMIFrameType.from_knx(raw),
            frame_format=frame_format,
        )

    def __str__(self) -> str:
        """Return object as compact readable string."""
        _set_flags = [
            name
            for name, value in (
                ("repeat_on_error", self.repeat_on_error),
                ("system_broadcast", self.system_broadcast),
                ("acknowledge_request", self.acknowledge_request),
                ("confirm_error", self.confirm_error),
            )
            if value
        ]
        return " ".join(
            (
                self.priority.name,
                self.frame_type.name,
                f"hop_count={self.hop_count}",
                *_set_flags,
            )
        )
