"""
Module for serialization and deserialization of TPCI payloads.

TPCI stands for Transport Layer Protocol Control Information.

An APCI payload contains a service and payload. For example, a GroupValueWrite
is a service that takes a DPT as a value.
"""
from __future__ import annotations

from abc import ABC
from typing import ClassVar

from xknx.exceptions import ConversionError

CONTROL_BIT_MASK = 0x80
NUMBERED_BIT_MASK = 0x40


class TPCI(ABC):
    """
    Base class for TCPI services.

    This base class is only the interface for the derived classes.
    """

    control: ClassVar[bool]
    numbered: ClassVar[bool]
    sequence_number: int = 0
    control_flags: ClassVar[int | None] = None

    def to_knx(self) -> int:
        """Serialize to KNX/IP raw data."""
        return (
            self.control << 7
            | self.numbered << 6
            | (self.sequence_number & 0xF) << 2
            | (self.control_flags or 0)
        )

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

    def __repr__(self) -> str:
        """Return object as readable string."""
        _sequence_number = (
            f"sequence_number={self.sequence_number}" if self.numbered else ""
        )
        return f"{self.__class__.__name__}({_sequence_number})"

    @staticmethod
    def resolve(raw_tpci: int, dst_is_group_address: bool, dst_is_zero: bool) -> TPCI:
        """
        Return TPCI instance from TPCI command.

        See KNX Specifications 03_03_04 Transport Layer v01.02.02 AS §2 TPDU
        """
        control = raw_tpci & CONTROL_BIT_MASK
        numbered = raw_tpci & NUMBERED_BIT_MASK
        sequence_number = (raw_tpci >> 2) & 0xF

        if dst_is_group_address:
            if control or numbered:
                raise ConversionError("Invalid TPCI flags in group addressed frame.")
            if not sequence_number:
                if dst_is_zero:
                    return TDataBroadcast()
                return TDataGroup()
            if sequence_number == 1:
                # TDataTagGroup uses sequence number field as flag
                return TDataTagGroup()

        if not numbered and sequence_number:
            raise ConversionError("Sequence number not allowed for unnumbered TPCI")

        if not control:
            # data - last 2 bits are part of APCI
            if numbered:
                return TDataConnected(sequence_number=sequence_number)
            return TDataIndividual()
        # unnumbered control
        control_flags = raw_tpci & 0b11
        if not numbered:
            if control_flags == 0:
                return TConnect()
            if control_flags == 1:
                return TDisconnect()
        # numbered control
        if control_flags == 0b10:
            return TAck(sequence_number=sequence_number)
        if control_flags == 0b11:
            return TNak(sequence_number=sequence_number)

        raise ConversionError(f"Unknown TPCI {raw_tpci:#10b}.")


class TDataGroup(TPCI):
    """T_Data_Group class."""

    control = False
    numbered = False

    def to_knx(self) -> int:
        """Serialize to KNX/IP raw data."""
        return 0


class TDataBroadcast(TPCI):
    """T_Data_Broadcast class."""

    control = False
    numbered = False

    def to_knx(self) -> int:
        """Serialize to KNX/IP raw data."""
        return 0


class TDataTagGroup(TPCI):
    """T_Data_Tag_Group class."""

    control = False
    numbered = False
    sequence_number = 0b0001


class TDataIndividual(TPCI):
    """T_Data_Individual class."""

    control = False
    numbered = False

    def to_knx(self) -> int:
        """Serialize to KNX/IP raw data."""
        return 0


class TDataConnected(TPCI):
    """T_Data_Connected class."""

    control = False
    numbered = True

    def __init__(self, sequence_number: int):
        """Initialize TDataConnected."""
        self.sequence_number = sequence_number


class TConnect(TPCI):
    """T_Connect class."""

    control = True
    numbered = False
    control_flags = 0b00


class TDisconnect(TPCI):
    """T_Disconnect class."""

    control = True
    numbered = False
    control_flags = 0b01


class TAck(TPCI):
    """T_Ack class."""

    control = True
    numbered = True
    control_flags = 0b10

    def __init__(self, sequence_number: int):
        """Initialize TAck."""
        self.sequence_number = sequence_number


class TNak(TPCI):
    """T_Nak class."""

    control = True
    numbered = True
    control_flags = 0b11

    def __init__(self, sequence_number: int):
        """Initialize TNak."""
        self.sequence_number = sequence_number
