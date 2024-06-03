"""
Module for serialization and deserialization of APCI payloads.

APCI stands for Application Layer Protocol Control Information.

An APCI payload contains a service and payload. For example, a GroupValueWrite
is a service that takes a DPT as a value.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import struct
from typing import ClassVar, cast

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.secure.data_secure_asdu import SecureData, SecurityControlField
from xknx.telegram.address import IndividualAddress


def encode_cmd_and_payload(
    cmd: APCIService | APCIUserService | APCIExtendedService,
    encoded_payload: int = 0,
    appended_payload: bytes | None = None,
) -> bytearray:
    """Encode cmd and payload."""
    data = bytearray(
        [
            (cmd.value >> 8) & 0b11,
            (cmd.value & 0xFF) | (encoded_payload & DPTBinary.APCI_BITMASK),
        ]
    )
    if appended_payload:
        data.extend(appended_payload)
    return data


class APCIService(Enum):
    """Enum class for APCI services."""

    GROUP_READ = 0x0000
    GROUP_RESPONSE = 0x0040
    GROUP_WRITE = 0x0080

    INDIVIDUAL_ADDRESS_WRITE = 0x00C0
    INDIVIDUAL_ADDRESS_READ = 0x0100
    INDIVIDUAL_ADDRESS_RESPONSE = 0x140

    ADC_READ = 0x0180
    ADC_RESPONSE = 0x1C0

    MEMORY_EXTENDED_WRITE = 0x1FB
    MEMORY_EXTENDED_WRITE_RESPONSE = 0x1FC
    MEMORY_EXTENDED_READ = 0x1FD
    MEMORY_EXTENDED_READ_RESPONSE = 0x1FE

    MEMORY_READ = 0x0200
    MEMORY_RESPONSE = 0x0240
    MEMORY_WRITE = 0x0280

    USER_MESSAGE = 0x02C0

    DEVICE_DESCRIPTOR_READ = 0x0300
    DEVICE_DESCRIPTOR_RESPONSE = 0x0340

    RESTART = 0x0380

    ESCAPE = 0x03C0


class APCIUserService(Enum):
    """Enum class for user message APCI services."""

    USER_MEMORY_READ = 0x02C0
    USER_MEMORY_RESPONSE = 0x02C1
    USER_MEMORY_WRITE = 0x02C2

    USER_MANUFACTURER_INFO_READ = 0x02C5
    USER_MANUFACTURER_INFO_RESPONSE = 0x02C6

    FUNCTION_PROPERTY_COMMAND = 0x02C7
    FUNCTION_PROPERTY_STATE_READ = 0x02C8
    FUNCTION_PROPERTY_STATE_RESPONSE = 0x02C9


class APCIExtendedService(Enum):
    """Enum class for extended APCI services."""

    AUTHORIZE_REQUEST = 0x03D1
    AUTHORIZE_RESPONSE = 0x03D2

    PROPERTY_VALUE_READ = 0x03D5
    PROPERTY_VALUE_RESPONSE = 0x03D6
    PROPERTY_VALUE_WRITE = 0x03D7

    PROPERTY_DESCRIPTION_READ = 0x03D8
    PROPERTY_DESCRIPTION_RESPONSE = 0x03D9

    INDIVIDUAL_ADDRESS_SERIAL_READ = 0x03DC
    INDIVIDUAL_ADDRESS_SERIAL_RESPONSE = 0x03DD
    INDIVIDUAL_ADDRESS_SERIAL_WRITE = 0x03DE

    # DataSecure
    APCI_SEC = 0x03F1


@dataclass(slots=True)
class APCI(ABC):
    """
    Base class for ACPI services.

    This base class is only the interface for the derived classes.
    """

    CODE: ClassVar[APCIService | APCIUserService | APCIExtendedService] = cast(
        APCIService, None
    )

    @abstractmethod
    def calculated_length(self) -> int:
        """Get length of APCI payload - to be implemented in derived class."""

    @abstractmethod
    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data - to be implemented in derived class."""
        # shall return bytearray instead of bytes so TPCI can be
        # added to first 6 bits of first byte in-place later

    @classmethod
    @abstractmethod
    def from_knx(cls, raw: bytes) -> APCI:
        """
        Parse/deserialize from KNX/IP raw data - to be implemented in derived class.

        `raw` shall be a complete APDU.
        Return APCI instance based on APCI service.

        There are only 16 possible APCI services. The
        `APCIService.USER_MESSAGE` and `APCIService.ESCAPE` service have
        several sub-services.
        """
        apci = (raw[0] * 256 + raw[1]) & 0x03FF
        service = apci & 0x03C0

        if service == APCIService.GROUP_READ.value:
            return GroupValueRead.from_knx(raw)
        if service == APCIService.GROUP_WRITE.value:
            return GroupValueWrite.from_knx(raw)
        if service == APCIService.GROUP_RESPONSE.value:
            return GroupValueResponse.from_knx(raw)
        if service == APCIService.INDIVIDUAL_ADDRESS_WRITE.value:
            return IndividualAddressWrite.from_knx(raw)
        if service == APCIService.INDIVIDUAL_ADDRESS_READ.value:
            return IndividualAddressRead.from_knx(raw)
        if service == APCIService.INDIVIDUAL_ADDRESS_RESPONSE.value:
            return IndividualAddressResponse.from_knx(raw)
        if service == APCIService.ADC_READ.value:
            return ADCRead.from_knx(raw)
        if service == APCIService.ADC_RESPONSE.value:
            if apci == APCIService.MEMORY_EXTENDED_WRITE.value:
                return MemoryExtendedWrite.from_knx(raw)
            if apci == APCIService.MEMORY_EXTENDED_WRITE_RESPONSE.value:
                return MemoryExtendedWriteResponse.from_knx(raw)
            if apci == APCIService.MEMORY_EXTENDED_READ.value:
                return MemoryExtendedRead.from_knx(raw)
            if apci == APCIService.MEMORY_EXTENDED_READ_RESPONSE.value:
                return MemoryExtendedReadResponse.from_knx(raw)
            return ADCResponse.from_knx(raw)
        if service == APCIService.MEMORY_READ.value:
            return MemoryRead.from_knx(raw)
        if service == APCIService.MEMORY_WRITE.value:
            return MemoryWrite.from_knx(raw)
        if service == APCIService.MEMORY_RESPONSE.value:
            return MemoryResponse.from_knx(raw)
        if service == APCIService.USER_MESSAGE.value:
            if apci == APCIUserService.USER_MEMORY_READ.value:
                return UserMemoryRead.from_knx(raw)
            if apci == APCIUserService.USER_MEMORY_RESPONSE.value:
                return UserMemoryResponse.from_knx(raw)
            if apci == APCIUserService.USER_MEMORY_WRITE.value:
                return UserMemoryWrite.from_knx(raw)
            if apci == APCIUserService.USER_MANUFACTURER_INFO_READ.value:
                return UserManufacturerInfoRead.from_knx(raw)
            if apci == APCIUserService.USER_MANUFACTURER_INFO_RESPONSE.value:
                return UserManufacturerInfoResponse.from_knx(raw)
            if apci == APCIUserService.FUNCTION_PROPERTY_COMMAND.value:
                return FunctionPropertyCommand.from_knx(raw)
            if apci == APCIUserService.FUNCTION_PROPERTY_STATE_READ.value:
                return FunctionPropertyStateRead.from_knx(raw)
            if apci == APCIUserService.FUNCTION_PROPERTY_STATE_RESPONSE.value:
                return FunctionPropertyStateResponse.from_knx(raw)
        if service == APCIService.DEVICE_DESCRIPTOR_READ.value:
            return DeviceDescriptorRead.from_knx(raw)
        if service == APCIService.DEVICE_DESCRIPTOR_RESPONSE.value:
            return DeviceDescriptorResponse.from_knx(raw)
        if service == APCIService.RESTART.value:
            return Restart.from_knx(raw)
        if service == APCIService.ESCAPE.value:
            if apci == APCIExtendedService.AUTHORIZE_REQUEST.value:
                return AuthorizeRequest.from_knx(raw)
            if apci == APCIExtendedService.AUTHORIZE_RESPONSE.value:
                return AuthorizeResponse.from_knx(raw)
            if apci == APCIExtendedService.PROPERTY_VALUE_READ.value:
                return PropertyValueRead.from_knx(raw)
            if apci == APCIExtendedService.PROPERTY_VALUE_WRITE.value:
                return PropertyValueWrite.from_knx(raw)
            if apci == APCIExtendedService.PROPERTY_VALUE_RESPONSE.value:
                return PropertyValueResponse.from_knx(raw)
            if apci == APCIExtendedService.PROPERTY_DESCRIPTION_READ.value:
                return PropertyDescriptionRead.from_knx(raw)
            if apci == APCIExtendedService.PROPERTY_DESCRIPTION_RESPONSE.value:
                return PropertyDescriptionResponse.from_knx(raw)
            if apci == APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_READ.value:
                return IndividualAddressSerialRead.from_knx(raw)
            if apci == APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_RESPONSE.value:
                return IndividualAddressSerialResponse.from_knx(raw)
            if apci == APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_WRITE.value:
                return IndividualAddressSerialWrite.from_knx(raw)
            if apci == APCIExtendedService.APCI_SEC.value:
                return SecureAPDU.from_knx(raw)

        raise ConversionError(f"Class not implemented for APCI {apci:#012b}.")


@dataclass(slots=True)
class GroupValueRead(APCI):
    """
    GroupValueRead service.

    Does not have any payload.
    """

    CODE: ClassVar = APCIService.GROUP_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    @classmethod
    def from_knx(cls, raw: bytes) -> GroupValueRead:
        """Parse/deserialize from KNX/IP raw data."""
        # Nothing to parse, but must be implemented explicitly.
        return cls()

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(self.CODE)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<GroupValueRead />"


@dataclass(slots=True)
class GroupValueWrite(APCI):
    """
    GroupValueRead service.

    Takes a value (DPT) as payload.
    """

    CODE: ClassVar = APCIService.GROUP_WRITE

    value: DPTBinary | DPTArray

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        if isinstance(self.value, DPTBinary):
            return 1
        return 1 + len(self.value.value)

    @classmethod
    def from_knx(cls, raw: bytes) -> GroupValueWrite:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) == 2:
            return cls(value=DPTBinary(raw[1] & DPTBinary.APCI_BITMASK))

        return cls(value=DPTArray(raw[2:]))

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if isinstance(self.value, DPTBinary):
            return encode_cmd_and_payload(self.CODE, encoded_payload=self.value.value)

        return encode_cmd_and_payload(
            self.CODE, appended_payload=bytes(self.value.value)
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<GroupValueWrite value="{self.value}" />'


@dataclass(slots=True)
class GroupValueResponse(APCI):
    """
    GroupValueResponse service.

    Takes a value (DPT) as payload.
    """

    CODE: ClassVar = APCIService.GROUP_RESPONSE

    value: DPTBinary | DPTArray

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        if isinstance(self.value, DPTBinary):
            return 1
        return 1 + len(self.value.value)

    @classmethod
    def from_knx(cls, raw: bytes) -> GroupValueResponse:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) == 2:
            return cls(value=DPTBinary(raw[1] & DPTBinary.APCI_BITMASK))
        return cls(value=DPTArray(raw[2:]))

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if isinstance(self.value, DPTBinary):
            return encode_cmd_and_payload(self.CODE, encoded_payload=self.value.value)
        return encode_cmd_and_payload(
            self.CODE, appended_payload=bytes(self.value.value)
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<GroupValueResponse value="{self.value}" />'


@dataclass(slots=True)
class IndividualAddressWrite(APCI):
    """
    IndividualAddressWrite service.

    Payload contains the serial number and (new) address of the device.
    """

    CODE: ClassVar = APCIService.INDIVIDUAL_ADDRESS_WRITE

    address: IndividualAddress

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3

    @classmethod
    def from_knx(cls, raw: bytes) -> IndividualAddressWrite:
        """Parse/deserialize from KNX/IP raw data."""
        (raw_address,) = struct.unpack("!H", raw[2:])
        return cls(address=IndividualAddress(raw_address))

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(self.CODE, appended_payload=self.address.to_knx())

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<IndividualAddressWrite address="{self.address}" />'


@dataclass(slots=True)
class IndividualAddressRead(APCI):
    """IndividualAddressRead service."""

    CODE: ClassVar = APCIService.INDIVIDUAL_ADDRESS_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    @classmethod
    def from_knx(cls, raw: bytes) -> IndividualAddressRead:
        """Parse/deserialize from KNX/IP raw data."""
        # Nothing to parse, but must be implemented explicitly.
        return cls()

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(self.CODE)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<IndividualAddressRead />"


@dataclass(slots=True)
class IndividualAddressResponse(APCI):
    """
    IndividualAddressResponse service.

    There is no payload, since the Telegram's source address is used as a
    response address.
    """

    CODE: ClassVar = APCIService.INDIVIDUAL_ADDRESS_RESPONSE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    @classmethod
    def from_knx(cls, raw: bytes) -> IndividualAddressResponse:
        """Parse/deserialize from KNX/IP raw data."""
        # Nothing to parse, but must be implemented explicitly.
        return cls()

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(self.CODE)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<IndividualAddressResponse />"


@dataclass(slots=True)
class ADCRead(APCI):
    """
    ADCRead service.

    Payload contains the channel and number of samples to take.
    """

    CODE: ClassVar = APCIService.ADC_READ

    channel: int
    count: int = 1

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 2

    @classmethod
    def from_knx(cls, raw: bytes) -> ADCRead:
        """Parse/deserialize from KNX/IP raw data."""
        channel, count = struct.unpack("!BB", raw[1:])

        return cls(
            channel=channel & DPTBinary.APCI_BITMASK,
            count=count,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack("!BB", self.channel, self.count)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=payload[0], appended_payload=payload[1:]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<ADCRead channel="{self.channel}" count="{self.count}" />'


@dataclass(slots=True)
class ADCResponse(APCI):
    """
    ADCResponse service.

    Payload contains the channel, number of samples and value.
    """

    CODE: ClassVar = APCIService.ADC_RESPONSE

    channel: int
    count: int = 1
    value: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4

    @classmethod
    def from_knx(cls, raw: bytes) -> ADCResponse:
        """Parse/deserialize from KNX/IP raw data."""
        channel, count, value = struct.unpack("!BBH", raw[1:])

        return cls(
            channel=channel & DPTBinary.APCI_BITMASK,
            count=count,
            value=value,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack("!BBH", self.channel, self.count, self.value)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=payload[0], appended_payload=payload[1:]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<ADCResponse channel="{self.channel}" count="{self.count}" value="{self.value}" />'


@dataclass(slots=True)
class MemoryExtendedWrite(APCI):
    """
    MemoryExtendedWrite service.

    Payload indicates address (16 MiB), count (1-255 bytes) and data.
    """

    CODE: ClassVar = APCIService.MEMORY_EXTENDED_WRITE

    address: int
    data: bytes
    count: int = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Post-initialization steps."""
        if self.count is None:
            self.count = len(self.data)  # type: ignore[unreachable]

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> MemoryExtendedWrite:
        """Parse/deserialize from KNX/IP raw data."""
        count = raw[2]
        address = int.from_bytes(raw[3:6], "big")
        data = raw[6:]

        return cls(
            count=count,
            address=address,
            data=data,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.address <= 0xFFFFFF:
            raise ConversionError("Address out of range.")
        if not 0 <= self.count <= 250:
            raise ConversionError("Count out of range.")

        size = len(self.data)
        payload = struct.pack(f"!BI{size}s", self.count, self.address, self.data)
        # suppress first byte of address
        payload = payload[:1] + payload[2:]

        return encode_cmd_and_payload(self.CODE, 0, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<MemoryExtendedWrite address="{hex(self.address)}" count="{self.count}" data="{self.data.hex()}" />'


@dataclass(slots=True)
class MemoryExtendedWriteResponse(APCI):
    """
    MemoryExtendedWriteResponse service.

    Payload indicates return code, address (16 MiB) and confirmation data.
    """

    CODE: ClassVar = APCIService.MEMORY_EXTENDED_WRITE_RESPONSE

    return_code: int
    address: int
    confirmation_data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5 + len(self.confirmation_data)

    @classmethod
    def from_knx(cls, raw: bytes) -> MemoryExtendedWriteResponse:
        """Parse/deserialize from KNX/IP raw data."""
        return_code = raw[2]
        address = int.from_bytes(raw[3:6], "big")
        confirmation_data = raw[6:]

        return cls(
            return_code=return_code,
            address=address,
            confirmation_data=confirmation_data,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.address <= 0xFFFFFF:
            raise ConversionError("Address out of range.")
        if not 0 <= self.return_code <= 255:
            raise ConversionError("Return code out of range.")

        size = len(self.confirmation_data)
        payload = struct.pack(
            f"!BI{size}s", self.return_code, self.address, self.confirmation_data
        )
        # suppress first byte of address
        payload = payload[:1] + payload[2:]

        return encode_cmd_and_payload(self.CODE, 0, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<MemoryExtendedWriteResponse return_code="{self.return_code}" address="{hex(self.address)}" confirmation_data="{self.confirmation_data.hex()}" />'


@dataclass(slots=True)
class MemoryExtendedRead(APCI):
    """
    MemoryExtendedRead service.

    Payload indicates count and address (16 MiB).
    """

    CODE: ClassVar = APCIService.MEMORY_EXTENDED_READ

    count: int
    address: int

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5

    @classmethod
    def from_knx(cls, raw: bytes) -> MemoryExtendedRead:
        """Parse/deserialize from KNX/IP raw data."""
        count = raw[2]
        address = int.from_bytes(raw[3:6], "big")

        return cls(
            count=count,
            address=address,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.address <= 0xFFFFFF:
            raise ConversionError("Address out of range.")
        if not 0 <= self.count <= 250:
            raise ConversionError("Count out of range.")

        payload = struct.pack("!BI", self.count, self.address)
        # suppress first byte of address
        payload = payload[:1] + payload[2:]

        return encode_cmd_and_payload(self.CODE, 0, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<MemoryExtendedRead count="{self.count}" address="{hex(self.address)}" />'
        )


@dataclass(slots=True)
class MemoryExtendedReadResponse(APCI):
    """
    MemoryExtendedReadResponse service.

    Payload indicates return code, address (16 MiB) and data.
    """

    CODE: ClassVar = APCIService.MEMORY_EXTENDED_READ_RESPONSE

    return_code: int
    address: int
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> MemoryExtendedReadResponse:
        """Parse/deserialize from KNX/IP raw data."""
        return_code = raw[2]
        address = int.from_bytes(raw[3:6], "big")
        data = raw[6:]

        return cls(
            return_code=return_code,
            address=address,
            data=data,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.address <= 0xFFFFFF:
            raise ConversionError("Address out of range.")

        if not 0 <= self.return_code <= 255:
            raise ConversionError("Return code out of range.")

        size = len(self.data)
        payload = struct.pack(f"!BI{size}s", self.return_code, self.address, self.data)
        # suppress first byte of address
        payload = payload[:1] + payload[2:]

        return encode_cmd_and_payload(self.CODE, 0, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<MemoryExtendedReadResponse return_code="{self.return_code}" address="{hex(self.address)}" data="{self.data.hex()}" />'


@dataclass(slots=True)
class MemoryRead(APCI):
    """
    MemoryRead service.

    Payload indicates address (64 KiB) and count (1-63 bytes).
    """

    CODE: ClassVar = APCIService.MEMORY_READ

    address: int
    count: int = 1

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3

    @classmethod
    def from_knx(cls, raw: bytes) -> MemoryRead:
        """Parse/deserialize from KNX/IP raw data."""
        count, address = struct.unpack("!BH", raw[1:])

        return cls(
            address=address,
            count=count & DPTBinary.APCI_BITMASK,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.address <= 0xFFFF:
            raise ConversionError("Address out of range.")
        if not 0 <= self.count <= 0x3F:
            raise ConversionError("Count out of range.")

        payload = struct.pack("!BH", self.count, self.address)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=payload[0], appended_payload=payload[1:]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<MemoryRead address="{hex(self.address)}" count="{self.count}" />'


@dataclass(slots=True)
class MemoryWrite(APCI):
    """
    MemoryWrite service.

    Payload indicates address (64 KiB), count (1-63 bytes) and data.
    """

    CODE: ClassVar = APCIService.MEMORY_WRITE

    address: int
    data: bytes
    count: int = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Post-initialization steps."""
        if self.count is None:
            self.count = len(self.data)  # type: ignore[unreachable]

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> MemoryWrite:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 4

        count, address, data = struct.unpack(f"!BH{size}s", raw[1:])

        return cls(
            count=count & DPTBinary.APCI_BITMASK,
            address=address,
            data=data,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.address <= 0xFFFF:
            raise ConversionError("Address out of range.")
        if not 0 <= self.count <= 0x3F:
            raise ConversionError("Count out of range.")

        size = len(self.data)
        payload = struct.pack(f"!BH{size}s", self.count, self.address, self.data)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=payload[0], appended_payload=payload[1:]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<MemoryWrite address="{hex(self.address)}" count="{self.count}" data="{self.data.hex()}" />'


@dataclass(slots=True)
class MemoryResponse(APCI):
    """
    MemoryResponse service.

    Payload indicates address (64 KiB), count (1-63 bytes) and data.
    """

    CODE: ClassVar = APCIService.MEMORY_RESPONSE

    address: int
    data: bytes
    count: int = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Post-initialization steps."""
        if self.count is None:
            self.count = len(self.data)  # type: ignore[unreachable]

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> MemoryResponse:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 4

        count, address, data = struct.unpack(f"!BH{size}s", raw[1:])

        return cls(
            count=count & DPTBinary.APCI_BITMASK,
            address=address,
            data=data,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.address <= 0xFFFF:
            raise ConversionError("Address out of range.")
        if not 0 <= self.count <= 0x3F:
            raise ConversionError("Count out of range.")

        size = len(self.data)
        payload = struct.pack(f"!BH{size}s", self.count, self.address, self.data)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=payload[0], appended_payload=payload[1:]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<MemoryResponse address="{hex(self.address)}" count="{self.count}" data="{self.data.hex()}" />'


@dataclass(slots=True)
class DeviceDescriptorRead(APCI):
    """
    DeviceDescriptorRead service.

    Payload contains the descriptor.
    """

    CODE: ClassVar = APCIService.DEVICE_DESCRIPTOR_READ

    descriptor: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    @classmethod
    def from_knx(cls, raw: bytes) -> DeviceDescriptorRead:
        """Parse/deserialize from KNX/IP raw data."""
        return cls(descriptor=raw[1] & 0x3F)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.descriptor <= 0x3F:
            raise ConversionError("Descriptor out of range.")

        return encode_cmd_and_payload(self.CODE, encoded_payload=self.descriptor)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<DeviceDescriptorRead descriptor="{self.descriptor}" />'


@dataclass(slots=True)
class DeviceDescriptorResponse(APCI):
    """
    DeviceDescriptorResponse service.

    Payload contains the descriptor and value.
    """

    CODE: ClassVar = APCIService.DEVICE_DESCRIPTOR_RESPONSE

    descriptor: int = 0
    value: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3

    @classmethod
    def from_knx(cls, raw: bytes) -> DeviceDescriptorResponse:
        """Parse/deserialize from KNX/IP raw data."""
        descriptor, value = struct.unpack("!BH", raw[1:])

        return cls(descriptor=descriptor & 0x3F, value=value)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.descriptor <= 0x3F:
            raise ConversionError("Descriptor out of range.")

        payload = struct.pack("!H", self.value)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=self.descriptor, appended_payload=payload
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<DeviceDescriptorResponse descriptor="{self.descriptor}" value="{self.value}" />'


@dataclass(slots=True)
class Restart(APCI):
    """
    Restart service.

    Does not take any payload.
    """

    # Requests a Basic Restart of the communication partner.
    # Master reset is not implemented yet.

    CODE: ClassVar = APCIService.RESTART

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    @classmethod
    def from_knx(cls, raw: bytes) -> Restart:
        """Parse/deserialize from KNX/IP raw data."""
        # Nothing to parse, but must be implemented explicitly.
        return cls()

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(self.CODE)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<Restart />"


@dataclass(slots=True)
class UserMemoryRead(APCI):
    """
    UserMemoryRead service.

    Payload indicates address (1 MiB) and count (1-15 bytes).
    """

    CODE: ClassVar = APCIUserService.USER_MEMORY_READ

    address: int = 0
    count: int = 1

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4

    @classmethod
    def from_knx(cls, raw: bytes) -> UserMemoryRead:
        """Parse/deserialize from KNX/IP raw data."""
        byte0, address = struct.unpack("!BH", raw[2:])

        return cls(
            count=byte0 & 0x0F,
            address=(((byte0 & 0xF0) >> 4) << 16) + address,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.address <= 0xFFFFF:
            raise ConversionError("Address out of range.")
        if not 0 <= self.count <= 0xF:
            raise ConversionError("Count out of range.")

        byte0 = (((self.address & 0x0F0000) >> 16) << 4) | (self.count & 0x0F)
        address = self.address & 0xFFFF

        payload = struct.pack("!BH", byte0, address)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<UserMemoryRead address="{hex(self.address)}" count="{self.count}" />'


@dataclass(slots=True)
class UserMemoryWrite(APCI):
    """
    UserMemoryWrite service.

    Payload indicates address (1 MiB), count and data.
    """

    CODE: ClassVar = APCIUserService.USER_MEMORY_WRITE

    address: int
    data: bytes
    count: int = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Post-initialization steps."""
        if self.count is None:
            self.count = len(self.data)  # type: ignore[unreachable]

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> UserMemoryWrite:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 5

        byte0, address, data = struct.unpack(f"!BH{size}s", raw[2:])

        return cls(
            address=(((byte0 & 0xF0) >> 4) << 16) + address,
            data=data,
            count=byte0 & 0x0F,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.address <= 0xFFFFF:
            raise ConversionError("Address out of range.")
        if not 0 <= self.count <= 0xF:
            raise ConversionError("Count out of range.")

        byte0 = (((self.address & 0x0F0000) >> 16) << 4) | (self.count & 0x0F)
        address = self.address & 0xFFFF

        size = len(self.data)
        payload = struct.pack(f"!BH{size}s", byte0, address, self.data)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<UserMemoryWrite address="{hex(self.address)}" count="{self.count}" data="{self.data.hex()}" />'


@dataclass(slots=True)
class UserMemoryResponse(APCI):
    """
    UserMemoryResponse service.

    Payload indicates address (1 MiB), count and data.
    """

    CODE: ClassVar = APCIUserService.USER_MEMORY_RESPONSE

    address: int
    data: bytes
    count: int = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Post-initialization steps."""
        if self.count is None:
            self.count = len(self.data)  # type: ignore[unreachable]

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> UserMemoryResponse:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 5

        byte0, address, data = struct.unpack(f"!BH{size}s", raw[2:])

        return cls(
            address=(((byte0 & 0xF0) >> 4) << 16) + address,
            data=data,
            count=byte0 & 0x0F,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.address <= 0xFFFFF:
            raise ConversionError("Address out of range.")
        if not 0 <= self.count <= 0xF:
            raise ConversionError("Count out of range.")

        byte0 = (((self.address & 0x0F0000) >> 16) << 4) | (self.count & 0x0F)
        address = self.address & 0xFFFF

        size = len(self.data)
        payload = struct.pack(f"!BH{size}s", byte0, address, self.data)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<UserMemoryResponse address="{hex(self.address)}" count="{self.count}" data="{self.data.hex()}" />'


@dataclass(slots=True)
class UserManufacturerInfoRead(APCI):
    """UserManufacturerInfoRead service."""

    CODE: ClassVar = APCIUserService.USER_MANUFACTURER_INFO_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    @classmethod
    def from_knx(cls, raw: bytes) -> UserManufacturerInfoRead:
        """Parse/deserialize from KNX/IP raw data."""
        # Nothing to parse, but must be implemented explicitly.
        return cls()

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""

        return encode_cmd_and_payload(self.CODE)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<UserManufacturerInfoRead />"


@dataclass(slots=True)
class UserManufacturerInfoResponse(APCI):
    """UserManufacturerInfoResponse service."""

    CODE: ClassVar = APCIUserService.USER_MANUFACTURER_INFO_RESPONSE

    manufacturer_id: int = 0
    data: bytes = b"\x00\x00"

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4

    @classmethod
    def from_knx(cls, raw: bytes) -> UserManufacturerInfoResponse:
        """Parse/deserialize from KNX/IP raw data."""
        manufacturer_id, data = struct.unpack("!B2s", raw[2:])
        return cls(manufacturer_id=manufacturer_id, data=data)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack("!B2s", self.manufacturer_id, self.data)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<UserManufacturerInfoResponse manufacturer_id="{self.manufacturer_id}" data="{self.data.hex()}" />'


@dataclass(slots=True)
class FunctionPropertyCommand(APCI):
    """FunctionPropertyCommand service."""

    CODE: ClassVar = APCIUserService.FUNCTION_PROPERTY_COMMAND

    object_index: int = 0
    property_id: int = 0
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> FunctionPropertyCommand:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 4
        object_index, property_id, data = struct.unpack(f"!BB{size}s", raw[2:])
        return cls(
            object_index=object_index,
            property_id=property_id,
            data=data,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        size = len(self.data)
        payload = struct.pack(
            f"!BB{size}s", self.object_index, self.property_id, self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<FunctionPropertyCommand object_index="{self.object_index}" property_id="{self.property_id}" data="{self.data.hex()}" />'


@dataclass(slots=True)
class FunctionPropertyStateRead(APCI):
    """FunctionPropertyStateRead service."""

    CODE: ClassVar = APCIUserService.FUNCTION_PROPERTY_STATE_READ

    object_index: int = 0
    property_id: int = 0
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> FunctionPropertyStateRead:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 4
        object_index, property_id, data = struct.unpack(f"!BB{size}s", raw[2:])
        return cls(
            object_index=object_index,
            property_id=property_id,
            data=data,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        size = len(self.data)
        payload = struct.pack(
            f"!BB{size}s", self.object_index, self.property_id, self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<FunctionPropertyStateRead object_index="{self.object_index}" property_id="{self.property_id}" data="{self.data.hex()}" />'


@dataclass(slots=True)
class FunctionPropertyStateResponse(APCI):
    """FunctionPropertyStateResponse service."""

    CODE: ClassVar = APCIUserService.FUNCTION_PROPERTY_STATE_RESPONSE

    object_index: int = 0
    property_id: int = 0
    return_code: int = 0
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> FunctionPropertyStateResponse:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 5
        (
            object_index,
            property_id,
            return_code,
            data,
        ) = struct.unpack(f"!BBB{size}s", raw[2:])
        return cls(
            object_index=object_index,
            property_id=property_id,
            return_code=return_code,
            data=data,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        size = len(self.data)
        payload = struct.pack(
            f"!BBB{size}s",
            self.object_index,
            self.property_id,
            self.return_code,
            self.data,
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<FunctionPropertyStateResponse object_index="{self.object_index}" property_id="{self.property_id}" return_code="{self.return_code}" data="{self.data.hex()}" />'


@dataclass(slots=True)
class AuthorizeRequest(APCI):
    """AuthorizeRequest service."""

    CODE: ClassVar = APCIExtendedService.AUTHORIZE_REQUEST

    key: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 6

    @classmethod
    def from_knx(cls, raw: bytes) -> AuthorizeRequest:
        """Parse/deserialize from KNX/IP raw data."""
        _, key = struct.unpack("!BI", raw[2:])
        return cls(key=key)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack("!BI", 0, self.key)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<AuthorizeRequest key="{self.key}" />'


@dataclass(slots=True)
class AuthorizeResponse(APCI):
    """AuthorizeResponse service."""

    CODE: ClassVar = APCIExtendedService.AUTHORIZE_RESPONSE

    level: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 2

    @classmethod
    def from_knx(cls, raw: bytes) -> AuthorizeResponse:
        """Parse/deserialize from KNX/IP raw data."""
        (level,) = struct.unpack("!B", raw[2:])
        return cls(level=level)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack("!B", self.level)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<AuthorizeResponse level="{self.level}"/>'


@dataclass(slots=True)
class PropertyValueRead(APCI):
    """
    PropertyValueRead service.

    Payload indicates object, property, count and start.
    """

    CODE: ClassVar = APCIExtendedService.PROPERTY_VALUE_READ

    object_index: int = 0
    property_id: int = 0
    count: int = 1
    start_index: int = 1

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyValueRead:
        """Parse/deserialize from KNX/IP raw data."""
        (
            object_index,
            property_id,
            count,
            start_index,
        ) = struct.unpack("!BBBB", raw[2:])
        return cls(
            object_index=object_index,
            property_id=property_id,
            count=count >> 4,
            start_index=(count & 0xF) * 256 + start_index,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.count <= 0xF:
            raise ConversionError("Count out of range.")

        payload = struct.pack(
            "!BBBB",
            self.object_index,
            self.property_id,
            (self.count << 4) + (self.start_index >> 8),
            self.start_index & 0xFF,
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<PropertyValueRead "
            f'object_index="{self.object_index}" '
            f'property_id="{self.property_id}" '
            f'count="{self.count}" '
            f'start_index="{self.start_index}" '
            "/>"
        )


@dataclass(slots=True)
class PropertyValueWrite(APCI):
    """
    PropertyValueWrite service.

    Payload indicates object, property, count, start and data itself.
    """

    CODE: ClassVar = APCIExtendedService.PROPERTY_VALUE_WRITE

    object_index: int = 0
    property_id: int = 0
    count: int = 1
    start_index: int = 0
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5 + len(self.data)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.count <= 0xF:
            raise ConversionError("Count out of range.")

        size = len(self.data)
        payload = struct.pack(
            f"!BBBB{size}s",
            self.object_index,
            self.property_id,
            (self.count << 4) + (self.start_index >> 8),
            self.start_index & 0xFF,
            self.data,
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyValueWrite:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 6
        (
            object_index,
            property_id,
            count,
            start_index,
            data,
        ) = struct.unpack(f"!BBBB{size}s", raw[2:])
        return cls(
            object_index=object_index,
            property_id=property_id,
            count=count >> 4,
            start_index=(count & 0xF) * 256 + start_index,
            data=data,
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<PropertyValueWrite "
            f'object_index="{self.object_index}" '
            f'property_id="{self.property_id}" '
            f'count="{self.count}" '
            f'start_index="{self.start_index}" '
            f'data="{self.data.hex()}" '
            "/>"
        )


@dataclass(slots=True)
class PropertyValueResponse(APCI):
    """
    PropertyValueResponse service.

    Payload indicates object, property, count, start and data itself. Size of
    the payload depends on the data.
    """

    CODE: ClassVar = APCIExtendedService.PROPERTY_VALUE_RESPONSE

    object_index: int = 0
    property_id: int = 0
    count: int = 1
    start_index: int = 0
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyValueResponse:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 6
        (
            object_index,
            property_id,
            count,
            start_index,
            data,
        ) = struct.unpack(f"!BBBB{size}s", raw[2:])
        return cls(
            object_index=object_index,
            property_id=property_id,
            count=count >> 4,
            start_index=(count & 0xF) * 256 + start_index,
            data=data,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.count <= 0xF:
            raise ConversionError("Count out of range.")

        size = len(self.data)
        payload = struct.pack(
            f"!BBBB{size}s",
            self.object_index,
            self.property_id,
            (self.count << 4) + (self.start_index >> 8),
            self.start_index & 0xFF,
            self.data,
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<PropertyValueResponse "
            f'object_index="{self.object_index}" '
            f'property_id="{self.property_id}" '
            f'count="{self.count}" '
            f'start_index="{self.start_index}" '
            f'data="{self.data.hex()}" '
            "/>"
        )


@dataclass(slots=True)
class PropertyDescriptionRead(APCI):
    """PropertyDescriptionRead service."""

    CODE: ClassVar = APCIExtendedService.PROPERTY_DESCRIPTION_READ

    object_index: int = 0
    property_id: int = 0
    property_index: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyDescriptionRead:
        """Parse/deserialize from KNX/IP raw data."""
        object_index, property_id, property_index = struct.unpack("!BBB", raw[2:])
        return cls(
            object_index=object_index,
            property_id=property_id,
            property_index=property_index,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack(
            "!BBB", self.object_index, self.property_id, self.property_index
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<PropertyDescriptionRead object_index="{self.object_index}" property_id="{self.property_id}" property_index="{self.property_index}" />'


@dataclass(slots=True)
class PropertyDescriptionResponse(APCI):
    """PropertyDescriptionResponse service."""

    CODE: ClassVar = APCIExtendedService.PROPERTY_DESCRIPTION_RESPONSE

    object_index: int = 0
    property_id: int = 0
    property_index: int = 0
    type_: int = 0
    max_count: int = 1
    access: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 8

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyDescriptionResponse:
        """Parse/deserialize from KNX/IP raw data."""
        (
            object_index,
            property_id,
            property_index,
            type_,
            max_count,
            access,
        ) = struct.unpack("!BBBBHB", raw[2:])

        return cls(
            object_index=object_index,
            property_id=property_id,
            property_index=property_index,
            type_=type_,
            max_count=max_count & 0x0FFF,
            access=access,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.max_count <= 0x0FFF:
            raise ConversionError("Max count out of range.")

        payload = struct.pack(
            "!BBBBHB",
            self.object_index,
            self.property_id,
            self.property_index,
            self.type_,
            self.max_count & 0x0FFF,
            self.access,
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<PropertyDescriptionResponse object_index="{self.object_index}" property_id="{self.property_id}" property_index="{self.property_index}" type="{self.type_}" max_count="{self.max_count}" access="{self.access}" />'


@dataclass(slots=True)
class IndividualAddressSerialRead(APCI):
    """IndividualAddressSerialRead service."""

    CODE: ClassVar = APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_READ

    serial: bytes

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 7

    @classmethod
    def from_knx(cls, raw: bytes) -> IndividualAddressSerialRead:
        """Parse/deserialize from KNX/IP raw data."""
        (serial,) = struct.unpack("!6s", raw[2:])
        return cls(serial=serial)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if len(self.serial) != 6:
            raise ConversionError("Serial must be 6 bytes.")

        payload = struct.pack("!6s", self.serial)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<IndividualAddressSerialRead serial="{self.serial.hex()}" />'


@dataclass(slots=True)
class IndividualAddressSerialResponse(APCI):
    """IndividualAddressSerialResponse service."""

    CODE: ClassVar = APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_RESPONSE

    serial: bytes
    address: IndividualAddress

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 11

    @classmethod
    def from_knx(cls, raw: bytes) -> IndividualAddressSerialResponse:
        """Parse/deserialize from KNX/IP raw data."""
        serial, raw_address, _ = struct.unpack("!6sHH", raw[2:])
        return cls(
            serial=serial,
            address=IndividualAddress(raw_address),
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if len(self.serial) != 6:
            raise ConversionError("Serial must be 6 bytes.")

        payload = struct.pack("!6s2sH", self.serial, self.address.to_knx(), 0)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<IndividualAddressSerialResponse serial="{self.serial.hex()}" address="{self.address}" />'


@dataclass(slots=True)
class IndividualAddressSerialWrite(APCI):
    """IndividualAddressSerialWrite service."""

    CODE: ClassVar = APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_WRITE

    serial: bytes
    address: IndividualAddress

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 13

    @classmethod
    def from_knx(cls, raw: bytes) -> IndividualAddressSerialWrite:
        """Parse/deserialize from KNX/IP raw data."""
        serial, raw_address, _ = struct.unpack("!6sHI", raw[2:])
        return cls(
            serial=serial,
            address=IndividualAddress(raw_address),
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if len(self.serial) != 6:
            raise ConversionError("Serial must be 6 bytes.")

        payload = struct.pack("!6s2sI", self.serial, self.address.to_knx(), 0)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<IndividualAddressSerialWrite serial="{self.serial.hex()}" address="{self.address}" />'


@dataclass(slots=True)
class SecureAPDU(APCI):
    """SecureAPDU service."""

    CODE: ClassVar = APCIExtendedService.APCI_SEC

    scf: SecurityControlField
    secured_data: SecureData

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 2 + len(self.secured_data)

    @classmethod
    def from_knx(cls, raw: bytes) -> SecureAPDU:
        """Parse/deserialize from KNX/IP raw data."""
        return cls(
            scf=SecurityControlField.from_knx(raw[2]),
            secured_data=SecureData.from_knx(raw[3:]),
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        payload = self.scf.to_knx() + self.secured_data.to_knx()
        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<SecureAPDU scf="{self.scf}" secured_data={self.secured_data!r} />'
