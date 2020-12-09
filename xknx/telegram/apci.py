"""
Module for serialization and deserialization of APCI payloads.

APCI stands for Application Layer Protocol Control Information.

An APCI payload contains a service and payload. For example, a GroupValueWrite
is a service that takes a DPT as a value.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar, Optional, Union, cast

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError


def encode_cmd_and_payload(
    cmd: "APCICommand",
    encoded_payload: int = 0,
    appended_payload: Optional[bytes] = None,
) -> bytes:
    """Encode cmd and payload."""
    if appended_payload is None:
        appended_payload = bytes()

    data = bytearray(
        [
            (cmd.value >> 8) & 0xFF,
            (cmd.value & 0xFF) | (encoded_payload & DPTBinary.APCI_BITMASK),
        ]
    )
    data.extend(appended_payload)
    return data


class APCICommand(Enum):
    """Enum class for APCI services."""

    GROUP_READ = 0x0000
    GROUP_RESPONSE = 0x0040
    GROUP_WRITE = 0x0080

    ESCAPE = 0x03C0


class APCIExtendedCommand(Enum):
    """Enum class for extended APCI services."""


class APCI(ABC):
    """
    Base class for ACPI services.

    This base class is only the interface for the derived classes.
    """

    code: ClassVar[APCICommand] = cast(APCICommand, None)

    @abstractmethod
    def calculated_length(self) -> int:
        """Get length of APCI payload - to be implemented in derived class."""

    @abstractmethod
    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data - to be implemented in derived class."""

    @abstractmethod
    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data - to be implemented in derived class."""

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__

    @staticmethod
    def resolve_apci(apci: int) -> "APCI":
        """Return APCI instance from APCI command."""
        extended = (apci & APCICommand.ESCAPE.value) == APCICommand.ESCAPE.value

        if extended:
            raise ConversionError(
                f"Class not implemented for extended APCI {apci:#012b}."
            )

        apci = apci & 0x03C0

        if apci == APCICommand.GROUP_READ.value:
            return GroupValueRead()
        if apci == APCICommand.GROUP_WRITE.value:
            return GroupValueWrite()
        if apci == APCICommand.GROUP_RESPONSE.value:
            return GroupValueResponse()
        raise ConversionError(f"Class not implemented for APCI {apci:#012b}.")


class GroupValueRead(APCI):
    """
    GroupValueRead service.

    Does not have any payload.
    """

    code = APCICommand.GROUP_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""

        # Nothing to parse, but must be implemented explicitly.
        return

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(self.code)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<GroupValueRead />"


class GroupValueWrite(APCI):
    """
    GroupValueRead service.

    Takes a value (DPT) as payload.
    """

    code = APCICommand.GROUP_WRITE

    def __init__(self, value: Optional[Union[DPTBinary, DPTArray]] = None) -> None:
        """Initialize a new instance of GroupValueWrite."""
        self.value = value

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        if isinstance(self.value, DPTBinary):
            return 1
        if isinstance(self.value, DPTArray):
            return 1 + len(self.value.value)
        raise TypeError()

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) == 2:
            self.value = DPTBinary(raw[1] & DPTBinary.APCI_BITMASK)
        else:
            self.value = DPTArray(raw[2:])

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if isinstance(self.value, DPTBinary):
            return encode_cmd_and_payload(self.code, encoded_payload=self.value.value)
        if isinstance(self.value, DPTArray):
            return encode_cmd_and_payload(
                self.code, appended_payload=bytes(self.value.value)
            )
        raise TypeError()

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<GroupValueWrite value="{self.value}" />'


class GroupValueResponse(APCI):
    """
    GroupValueResponse service.

    Takes a value (DPT) as payload.
    """

    code = APCICommand.GROUP_RESPONSE

    def __init__(self, value: Optional[Union[DPTBinary, DPTArray]] = None) -> None:
        """Initialize a new instance of GroupValueResponse."""
        self.value = value

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        if isinstance(self.value, DPTBinary):
            return 1
        if isinstance(self.value, DPTArray):
            return 1 + len(self.value.value)
        raise TypeError()

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) == 2:
            self.value = DPTBinary(raw[1] & DPTBinary.APCI_BITMASK)
        else:
            self.value = DPTArray(raw[2:])

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if isinstance(self.value, DPTBinary):
            return encode_cmd_and_payload(self.code, encoded_payload=self.value.value)
        if isinstance(self.value, DPTArray):
            return encode_cmd_and_payload(
                self.code, appended_payload=bytes(self.value.value)
            )
        raise TypeError()

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<GroupValueResponse value="{self.value}" />'
