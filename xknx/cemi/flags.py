"""
Control fields of a cEMI L_Data frame.

The two control field octets Ctrl1 and Ctrl2 are specified in
3/6/3 EMI_IMI §4.1.4.3.2 and 3/2/2 Communication Medium TP1 §2.2.2 / §2.2.5.3.

    Ctrl1                            Ctrl2
    7  6  5  4  3  2  1  0           7  6  5  4  3  2  1  0
    FT  r  R SB  P  P  A  C          AT  H  H  H  E  E  E  E

Not every field is independent state: the Frame Type (FT) follows from the NPDU
length and the Address Type (AT) from the destination address, so both are
derived when serializing - see `CEMILData`. The Extended Frame Format (EFF) is
always 0 for the frame types XKNX supports.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from xknx.exceptions import ConversionError

# Ctrl1
FRAME_TYPE_STANDARD = 0b10000000
DO_NOT_REPEAT = 0b00100000
BROADCAST = 0b00010000
PRIORITY_MASK = 0b00001100
PRIORITY_OFFSET = 2
ACK_REQUESTED = 0b00000010
CONFIRM_ERROR = 0b00000001

# Ctrl2
DESTINATION_GROUP_ADDRESS = 0b10000000
HOP_COUNT_MASK = 0b01110000
HOP_COUNT_OFFSET = 4
EXTENDED_FRAME_FORMAT_MASK = 0b00001111
# 0000b is used for L_Data_Standard frames as well as for long L_Data_Extended
# frames; 01xxb denotes LTE-HEE (zone addressed) frames. The rest is reserved.
STANDARD_FRAME_FORMAT = 0b0000
LTE_FRAME_FORMAT = 0b0100

MAX_HOP_COUNT = 7


class CEMIPriority(IntEnum):
    """Priority of a cEMI L_Data frame. See 3/2/2 §2.2.2 Figure 28."""

    SYSTEM = 0b00
    NORMAL = 0b01
    URGENT = 0b10
    LOW = 0b11


@dataclass(slots=True)
class CEMIFlags:
    """
    Control fields of a cEMI L_Data frame.

    Holds only the fields that are independent state. Frame Type, Address Type and
    Extended Frame Format are not stored - they follow from the frame itself.

    `confirm_error` is only meaningful in an L_Data.con frame.
    """

    priority: CEMIPriority = CEMIPriority.LOW
    # `repeat_on_error` and `system_broadcast` are inverted on the wire
    repeat_on_error: bool = False
    system_broadcast: bool = False
    acknowledge_request: bool = False
    confirm_error: bool = False
    hop_count: int = 6

    def to_knx(self, *, frame_type_standard: bool, dst_is_group_address: bool) -> bytes:
        """
        Serialize to Ctrl1 and Ctrl2.

        Frame Type and Address Type are not held by this object; they are passed in
        by the frame that knows its NPDU length and destination address.
        """
        if not 0 <= self.hop_count <= MAX_HOP_COUNT:
            raise ConversionError(f"Hop count out of range: {self.hop_count}")

        ctrl1 = (
            (FRAME_TYPE_STANDARD if frame_type_standard else 0)
            | (0 if self.repeat_on_error else DO_NOT_REPEAT)
            | (0 if self.system_broadcast else BROADCAST)
            | (self.priority << PRIORITY_OFFSET)
            | (ACK_REQUESTED if self.acknowledge_request else 0)
            | (CONFIRM_ERROR if self.confirm_error else 0)
        )
        ctrl2 = (
            (DESTINATION_GROUP_ADDRESS if dst_is_group_address else 0)
            | (self.hop_count << HOP_COUNT_OFFSET)
            | STANDARD_FRAME_FORMAT
        )
        return bytes((ctrl1, ctrl2))

    @classmethod
    def from_knx(cls, raw: bytes) -> CEMIFlags:
        """
        Parse Ctrl1 and Ctrl2.

        The Frame Type is deliberately not evaluated: "any receiver shall be
        tolerant towards the use of the Frame Format" - 3/6/3 §4.1.5.2.3.
        """
        ctrl1, ctrl2 = raw[0], raw[1]
        return cls(
            priority=CEMIPriority((ctrl1 & PRIORITY_MASK) >> PRIORITY_OFFSET),
            repeat_on_error=not ctrl1 & DO_NOT_REPEAT,
            system_broadcast=not ctrl1 & BROADCAST,
            acknowledge_request=bool(ctrl1 & ACK_REQUESTED),
            confirm_error=bool(ctrl1 & CONFIRM_ERROR),
            hop_count=(ctrl2 & HOP_COUNT_MASK) >> HOP_COUNT_OFFSET,
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            f"CEMIFlags(priority={self.priority.name} "
            f"hop_count={self.hop_count} "
            f"repeat_on_error={self.repeat_on_error} "
            f"system_broadcast={self.system_broadcast} "
            f"acknowledge_request={self.acknowledge_request} "
            f"confirm_error={self.confirm_error})"
        )
