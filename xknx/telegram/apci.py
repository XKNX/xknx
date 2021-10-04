"""
Module for serialization and deserialization of APCI payloads.

APCI stands for Application Layer Protocol Control Information.

An APCI payload contains a service and payload. For example, a GroupValueWrite
is a service that takes a DPT as a value.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
import struct
from typing import ClassVar, cast

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.telegram.address import IndividualAddress


def encode_cmd_and_payload(
    cmd: APCIService | APCIUserService | APCIExtendedService,
    encoded_payload: int = 0,
    appended_payload: bytes | None = None,
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
    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data - to be implemented in derived class."""

    @abstractmethod
    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data - to be implemented in derived class."""

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__

    @staticmethod
    def resolve_apci(apci: int) -> APCI:
        """
        Return APCI instance from APCI command.

        There are only 16 possible APCI services. The
        `APCIService.USER_MESSAGE` and `APCIService.ESCAPE` service have
        several sub-services.
        """
        service = apci & 0x03C0

        if service == APCIService.GROUP_READ.value:
            return GroupValueRead()
        if service == APCIService.GROUP_WRITE.value:
            return GroupValueWrite()
        if service == APCIService.GROUP_RESPONSE.value:
            return GroupValueResponse()
        if service == APCIService.INDIVIDUAL_ADDRESS_WRITE.value:
            return IndividualAddressWrite()
        if service == APCIService.INDIVIDUAL_ADDRESS_READ.value:
            return IndividualAddressRead()
        if service == APCIService.INDIVIDUAL_ADDRESS_RESPONSE.value:
            return IndividualAddressResponse()
        if service == APCIService.ADC_READ.value:
            return ADCRead()
        if service == APCIService.ADC_RESPONSE.value:
            return ADCResponse()
        if service == APCIService.MEMORY_READ.value:
            return MemoryRead()
        if service == APCIService.MEMORY_WRITE.value:
            return MemoryWrite()
        if service == APCIService.MEMORY_RESPONSE.value:
            return MemoryResponse()
        if service == APCIService.USER_MESSAGE.value:
            if apci == APCIUserService.USER_MEMORY_READ.value:
                return UserMemoryRead()
            if apci == APCIUserService.USER_MEMORY_RESPONSE.value:
                return UserMemoryResponse()
            if apci == APCIUserService.USER_MEMORY_WRITE.value:
                return UserMemoryWrite()
            if apci == APCIUserService.USER_MANUFACTURER_INFO_READ.value:
                return UserManufacturerInfoRead()
            if apci == APCIUserService.USER_MANUFACTURER_INFO_RESPONSE.value:
                return UserManufacturerInfoResponse()
            if apci == APCIUserService.FUNCTION_PROPERTY_COMMAND.value:
                return FunctionPropertyCommand()
            if apci == APCIUserService.FUNCTION_PROPERTY_STATE_READ.value:
                return FunctionPropertyStateRead()
            if apci == APCIUserService.FUNCTION_PROPERTY_STATE_RESPONSE.value:
                return FunctionPropertyStateResponse()
        if service == APCIService.DEVICE_DESCRIPTOR_READ.value:
            return DeviceDescriptorRead()
        if service == APCIService.DEVICE_DESCRIPTOR_RESPONSE.value:
            return DeviceDescriptorResponse()
        if service == APCIService.RESTART.value:
            return Restart()
        if service == APCIService.ESCAPE.value:
            if apci == APCIExtendedService.AUTHORIZE_REQUEST.value:
                return AuthorizeRequest()
            if apci == APCIExtendedService.AUTHORIZE_RESPONSE.value:
                return AuthorizeResponse()
            if apci == APCIExtendedService.PROPERTY_VALUE_READ.value:
                return PropertyValueRead()
            if apci == APCIExtendedService.PROPERTY_VALUE_WRITE.value:
                return PropertyValueWrite()
            if apci == APCIExtendedService.PROPERTY_VALUE_RESPONSE.value:
                return PropertyValueResponse()
            if apci == APCIExtendedService.PROPERTY_DESCRIPTION_READ.value:
                return PropertyDescriptionRead()
            if apci == APCIExtendedService.PROPERTY_DESCRIPTION_RESPONSE.value:
                return PropertyDescriptionResponse()
            if apci == APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_READ.value:
                return IndividualAddressSerialRead()
            if apci == APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_RESPONSE.value:
                return IndividualAddressSerialResponse()
            if apci == APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_WRITE.value:
                return IndividualAddressSerialWrite()

        raise ConversionError(f"Class not implemented for APCI {apci:#012b}.")


class GroupValueRead(APCI):
    """
    GroupValueRead service.

    Does not have any payload.
    """

    CODE = APCIService.GROUP_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""

        # Nothing to parse, but must be implemented explicitly.
        return

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(self.CODE)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<GroupValueRead />"


class GroupValueWrite(APCI):
    """
    GroupValueRead service.

    Takes a value (DPT) as payload.
    """

    CODE = APCIService.GROUP_WRITE

    def __init__(self, value: DPTBinary | DPTArray | None = None) -> None:
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
            return encode_cmd_and_payload(self.CODE, encoded_payload=self.value.value)
        if isinstance(self.value, DPTArray):
            return encode_cmd_and_payload(
                self.CODE, appended_payload=bytes(self.value.value)
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

    CODE = APCIService.GROUP_RESPONSE

    def __init__(self, value: DPTBinary | DPTArray | None = None) -> None:
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
            return encode_cmd_and_payload(self.CODE, encoded_payload=self.value.value)
        if isinstance(self.value, DPTArray):
            return encode_cmd_and_payload(
                self.CODE, appended_payload=bytes(self.value.value)
            )
        raise TypeError()

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<GroupValueResponse value="{self.value}" />'


class IndividualAddressWrite(APCI):
    """
    IndividualAddressWrite service.

    Payload contains the serial number and (new) address of the device.
    """

    CODE = APCIService.INDIVIDUAL_ADDRESS_WRITE

    def __init__(
        self,
        address: IndividualAddress | None = None,
    ) -> None:
        """Initialize a new instance of IndividualAddressWrite."""
        if address is None:
            address = IndividualAddress("0.0.0")

        self.address = address

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        address_high, address_low = struct.unpack("!BB", raw[2:])

        self.address = IndividualAddress((address_high, address_low))

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(
            self.CODE, appended_payload=bytes(self.address.to_knx())
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<IndividualAddressWrite address="{self.address}" />'


class IndividualAddressRead(APCI):
    """IndividualAddressRead service."""

    CODE = APCIService.INDIVIDUAL_ADDRESS_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""

        # Nothing to parse, but must be implemented explicitly.
        return

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(self.CODE)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<IndividualAddressRead />"


class IndividualAddressResponse(APCI):
    """
    IndividualAddressResponse service.

    There is no payload, since the Telegram's source address is used as a
    response address.
    """

    CODE = APCIService.INDIVIDUAL_ADDRESS_RESPONSE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""

        # Nothing to parse, but must be implemented explicitly.
        return

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(self.CODE)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<IndividualAddressResponse />"


class ADCRead(APCI):
    """
    ADCRead service.

    Payload contains the channel and number of samples to take.
    """

    CODE = APCIService.ADC_READ

    def __init__(self, channel: int = 0, count: int = 0) -> None:
        """Initialize a new instance of ADCRead."""
        self.channel = channel
        self.count = count

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 2

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        channel, self.count = struct.unpack("!BB", raw[1:])

        self.channel = channel & DPTBinary.APCI_BITMASK

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack("!BB", self.channel, self.count)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=payload[0], appended_payload=payload[1:]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<ADCRead channel="{self.channel}" count="{self.count}" />'


class ADCResponse(APCI):
    """
    ADCResponse service.

    Payload contains the channel, number of samples and value.
    """

    CODE = APCIService.ADC_RESPONSE

    def __init__(self, channel: int = 0, count: int = 0, value: int = 0) -> None:
        """Initialize a new instance of ADCResponse."""
        self.channel = channel
        self.count = count
        self.value = value

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        channel, self.count, self.value = struct.unpack("!BBH", raw[1:])

        self.channel = channel & DPTBinary.APCI_BITMASK

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack("!BBH", self.channel, self.count, self.value)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=payload[0], appended_payload=payload[1:]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<ADCResponse channel="{self.channel}" count="{self.count}" value="{self.value}" />'


class MemoryRead(APCI):
    """
    MemoryRead service.

    Payload indicates address (64 KiB) and count (1-63 bytes).
    """

    CODE = APCIService.MEMORY_READ

    def __init__(self, address: int = 0, count: int = 0) -> None:
        """Initialize a new instance of MemoryRead."""
        self.address = address
        self.count = count

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        count, self.address = struct.unpack("!BH", raw[1:])

        self.count = count & DPTBinary.APCI_BITMASK

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.address < 0 or self.address >= 2 ** 16:
            raise ConversionError("Address out of range.")
        if self.count < 0 or self.count >= 2 ** 6:
            raise ConversionError("Count out of range.")

        payload = struct.pack("!BH", self.count, self.address)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=payload[0], appended_payload=payload[1:]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<MemoryRead address="{hex(self.address)}" count="{self.count}" />'


class MemoryWrite(APCI):
    """
    MemoryWrite service.

    Payload indicates address (64 KiB), count (1-63 bytes) and data.
    """

    CODE = APCIService.MEMORY_WRITE

    def __init__(
        self, address: int = 0, count: int = 0, data: bytes | None = None
    ) -> None:
        """Initialize a new instance of MemoryWrite."""

        if data is None:
            data = bytearray()

        self.address = address
        self.count = count
        self.data = data

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3 + len(self.data)

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 4

        count, self.address, self.data = struct.unpack(f"!BH{size}s", raw[1:])

        self.count = count & DPTBinary.APCI_BITMASK

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.address < 0 or self.address >= 2 ** 16:
            raise ConversionError("Address out of range.")
        if self.count < 0 or self.count >= 2 ** 6:
            raise ConversionError("Count out of range.")

        size = len(self.data)
        payload = struct.pack(f"!BH{size}s", self.count, self.address, self.data)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=payload[0], appended_payload=payload[1:]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<MemoryWrite address="{hex(self.address)}" count="{self.count}" data="{self.data.hex()}" />'


class MemoryResponse(APCI):
    """
    MemoryResponse service.

    Payload indicates address (64 KiB), count (1-63 bytes) and data.
    """

    CODE = APCIService.MEMORY_RESPONSE

    def __init__(
        self, address: int = 0, count: int = 0, data: bytes | None = None
    ) -> None:
        """Initialize a new instance of MemoryResponse."""

        if data is None:
            data = bytearray()

        self.address = address
        self.count = count
        self.data = data

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3 + len(self.data)

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 4

        count, self.address, self.data = struct.unpack(f"!BH{size}s", raw[1:])

        self.count = count & DPTBinary.APCI_BITMASK

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.address < 0 or self.address >= 2 ** 16:
            raise ConversionError("Address out of range.")
        if self.count < 0 or self.count >= 2 ** 6:
            raise ConversionError("Count out of range.")

        size = len(self.data)
        payload = struct.pack(f"!BH{size}s", self.count, self.address, self.data)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=payload[0], appended_payload=payload[1:]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<MemoryResponse address="{hex(self.address)}" count="{self.count}" data="{self.data.hex()}" />'


class DeviceDescriptorRead(APCI):
    """
    DeviceDescriptorRead service.

    Payload contains the descriptor.
    """

    CODE = APCIService.DEVICE_DESCRIPTOR_READ

    def __init__(self, descriptor: int = 0) -> None:
        """Initialize a new instance of DeviceDescriptorRead."""
        self.descriptor = descriptor

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        self.descriptor = raw[1] & 0x3F

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.descriptor < 0 or self.descriptor >= 2 ** 6:
            raise ConversionError("Descriptor out of range.")

        return encode_cmd_and_payload(self.CODE, encoded_payload=self.descriptor)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<DeviceDescriptorRead descriptor="{self.descriptor}" />'


class DeviceDescriptorResponse(APCI):
    """
    DeviceDescriptorResponse service.

    Payload contains the descriptor and value.
    """

    CODE = APCIService.DEVICE_DESCRIPTOR_RESPONSE

    def __init__(self, descriptor: int = 0, value: int = 0) -> None:
        """Initialize a new instance of DeviceDescriptorResponse."""
        self.descriptor = descriptor
        self.value = value

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        self.descriptor, self.value = struct.unpack("!BH", raw[1:])

        self.descriptor = self.descriptor & 0x3F

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.descriptor < 0 or self.descriptor >= 2 ** 6:
            raise ConversionError("Descriptor out of range.")

        payload = struct.pack("!H", self.value)

        return encode_cmd_and_payload(
            self.CODE, encoded_payload=self.descriptor, appended_payload=payload
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<DeviceDescriptorResponse descriptor="{self.descriptor}" value="{self.value}" />'


class Restart(APCI):
    """
    Restart service.

    Does not take any payload.
    """

    CODE = APCIService.RESTART

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""

        # Nothing to parse, but must be implemented explicitly.
        return

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(self.CODE)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<Restart />"


class UserMemoryRead(APCI):
    """
    UserMemoryRead service.

    Payload indicates address (1 MiB) and count (1-15 bytes).
    """

    CODE = APCIUserService.USER_MEMORY_READ

    def __init__(self, address: int = 0, count: int = 0) -> None:
        """Initialize a new instance of UserMemoryRead."""
        self.address = address
        self.count = count

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        byte0, address = struct.unpack("!BH", raw[2:])

        self.count = byte0 & 0x0F
        self.address = (((byte0 & 0xF0) >> 4) << 16) + address

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.address < 0 or self.address >= 2 ** 20:
            raise ConversionError("Address out of range.")
        if self.count < 0 or self.count >= 2 ** 4:
            raise ConversionError("Count out of range.")

        byte0 = (((self.address & 0x0F0000) >> 16) << 4) | (self.count & 0x0F)
        address = self.address & 0xFFFF

        payload = struct.pack("!BH", byte0, address)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<UserMemoryRead address="{hex(self.address)}" count="{self.count}" />'


class UserMemoryWrite(APCI):
    """
    UserMemoryWrite service.

    Payload indicates address (1 MiB), count and data.
    """

    CODE = APCIUserService.USER_MEMORY_WRITE

    def __init__(
        self, address: int = 0, count: int = 0, data: bytes | None = None
    ) -> None:
        """Initialize a new instance of UserMemoryWrite."""

        if data is None:
            data = bytearray()

        self.address = address
        self.count = count
        self.data = data

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.data)

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 5

        byte0, address, self.data = struct.unpack(f"!BH{size}s", raw[2:])

        self.count = byte0 & 0x0F
        self.address = (((byte0 & 0xF0) >> 4) << 16) + address

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.address < 0 or self.address >= 2 ** 20:
            raise ConversionError("Address out of range.")
        if self.count < 0 or self.count >= 2 ** 4:
            raise ConversionError("Count out of range.")

        byte0 = (((self.address & 0x0F0000) >> 16) << 4) | (self.count & 0x0F)
        address = self.address & 0xFFFF

        size = len(self.data)
        payload = struct.pack(f"!BH{size}s", byte0, address, self.data)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<UserMemoryWrite address="{hex(self.address)}" count="{self.count}" data="{self.data.hex()}" />'


class UserMemoryResponse(APCI):
    """
    UserMemoryResponse service.

    Payload indicates address (1 MiB), count and data.
    """

    CODE = APCIUserService.USER_MEMORY_RESPONSE

    def __init__(
        self, address: int = 0, count: int = 0, data: bytes | None = None
    ) -> None:
        """Initialize a new instance of UserMemoryResponse."""

        if data is None:
            data = bytearray()

        self.address = address
        self.count = count
        self.data = data

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.data)

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 5

        byte0, address, self.data = struct.unpack(f"!BH{size}s", raw[2:])

        self.count = byte0 & 0x0F
        self.address = (((byte0 & 0xF0) >> 4) << 16) + address

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.address < 0 or self.address >= 2 ** 20:
            raise ConversionError("Address out of range.")
        if self.count < 0 or self.count >= 2 ** 4:
            raise ConversionError("Count out of range.")

        byte0 = (((self.address & 0x0F0000) >> 16) << 4) | (self.count & 0x0F)
        address = self.address & 0xFFFF

        size = len(self.data)
        payload = struct.pack(f"!BH{size}s", byte0, address, self.data)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<UserMemoryResponse address="{hex(self.address)}" count="{self.count}" data="{self.data.hex()}" />'


class UserManufacturerInfoRead(APCI):
    """UserManufacturerInfoRead service."""

    CODE = APCIUserService.USER_MANUFACTURER_INFO_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""

        # Nothing to parse, but must be implemented explicitly.
        return

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""

        return encode_cmd_and_payload(self.CODE)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<UserManufacturerInfoRead />"


class UserManufacturerInfoResponse(APCI):
    """UserManufacturerInfoResponse service."""

    CODE = APCIUserService.USER_MANUFACTURER_INFO_RESPONSE

    def __init__(self, manufacturer_id: int = 0, data: bytes | None = None) -> None:
        """Initialize a new instance of UserManufacturerInfoResponse."""
        if data is None:
            data = bytes([0x00, 0x00])

        self.manufacturer_id = manufacturer_id
        self.data = data

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        self.manufacturer_id, self.data = struct.unpack("!B2s", raw[2:])

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack("!B2s", self.manufacturer_id, self.data)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<UserManufacturerInfoResponse manufacturer_id="{self.manufacturer_id}" data="{self.data.hex()}" />'


class FunctionPropertyCommand(APCI):
    """FunctionPropertyCommand service."""

    CODE = APCIUserService.FUNCTION_PROPERTY_COMMAND

    def __init__(
        self, object_index: int = 0, property_id: int = 0, data: bytes | None = None
    ) -> None:
        """Initialize a new instance of FunctionPropertyCommand."""
        if data is None:
            data = bytes()

        self.object_index = object_index
        self.property_id = property_id
        self.data = data

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3 + len(self.data)

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 4

        self.object_index, self.property_id, self.data = struct.unpack(
            f"!BB{size}s", raw[2:]
        )

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        size = len(self.data)
        payload = struct.pack(
            f"!BB{size}s", self.object_index, self.property_id, self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<FunctionPropertyCommand object_index="{self.object_index}" property_id="{self.property_id}" data="{self.data.hex()}" />'


class FunctionPropertyStateRead(APCI):
    """FunctionPropertyStateRead service."""

    CODE = APCIUserService.FUNCTION_PROPERTY_STATE_READ

    def __init__(
        self, object_index: int = 0, property_id: int = 0, data: bytes | None = None
    ) -> None:
        """Initialize a new instance of FunctionPropertyStateRead."""
        if data is None:
            data = bytes()

        self.object_index = object_index
        self.property_id = property_id
        self.data = data

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3 + len(self.data)

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 4

        self.object_index, self.property_id, self.data = struct.unpack(
            f"!BB{size}s", raw[2:]
        )

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        size = len(self.data)
        payload = struct.pack(
            f"!BB{size}s", self.object_index, self.property_id, self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<FunctionPropertyStateRead object_index="{self.object_index}" property_id="{self.property_id}" data="{self.data.hex()}" />'


class FunctionPropertyStateResponse(APCI):
    """FunctionPropertyStateResponse service."""

    CODE = APCIUserService.FUNCTION_PROPERTY_STATE_READ

    def __init__(
        self,
        object_index: int = 0,
        property_id: int = 0,
        return_code: int = 0,
        data: bytes | None = None,
    ) -> None:
        """Initialize a new instance of FunctionPropertyStateResponse."""
        if data is None:
            data = bytes()

        self.object_index = object_index
        self.property_id = property_id
        self.return_code = return_code
        self.data = data

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.data)

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 5

        (
            self.object_index,
            self.property_id,
            self.return_code,
            self.data,
        ) = struct.unpack(f"!BBB{size}s", raw[2:])

    def to_knx(self) -> bytes:
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


class AuthorizeRequest(APCI):
    """AuthorizeRequest service."""

    CODE = APCIExtendedService.AUTHORIZE_REQUEST

    def __init__(self, key: int = 0) -> None:
        """Initialize a new instance of AuthorizeRequest."""
        self.key = key

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        _, self.key = struct.unpack("!BI", raw[2:])

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack("!BI", 0, self.key)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<AuthorizeRequest key="{self.key}" />'


class AuthorizeResponse(APCI):
    """AuthorizeResponse service."""

    CODE = APCIExtendedService.AUTHORIZE_RESPONSE

    def __init__(self, level: int = 0) -> None:
        """Initialize a new instance of AuthorizeResponse."""
        self.level = level

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 2

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        (self.level,) = struct.unpack("!B", raw[2:])

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack("!B", self.level)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<AuthorizeResponse level="{self.level}"/>'


class PropertyValueRead(APCI):
    """
    PropertyValueRead service.

    Payload indicates object, property, count and start.
    """

    CODE = APCIExtendedService.PROPERTY_VALUE_READ

    def __init__(
        self,
        object_index: int = 0,
        property_id: int = 0,
        count: int = 0,
        start_index: int = 1,
    ) -> None:
        """Initialize a new instance of PropertyValueRead."""
        self.object_index = object_index
        self.property_id = property_id
        self.count = count
        self.start_index = start_index

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        (
            self.object_index,
            self.property_id,
            count,
            self.start_index,
        ) = struct.unpack("!BBBB", raw[2:])

        self.count = count >> 4

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.count < 0 or self.count > 2 ** 4:
            raise ConversionError("Count out of range.")

        payload = struct.pack(
            "!BBBB",
            self.object_index,
            self.property_id,
            self.count << 4,
            self.start_index,
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


class PropertyValueWrite(APCI):
    """
    PropertyValueWrite service.

    Payload indicates object, property, count, start and data itself.
    """

    CODE = APCIExtendedService.PROPERTY_VALUE_WRITE

    def __init__(
        self,
        object_index: int = 0,
        property_id: int = 0,
        count: int = 0,
        start_index: int = 0,
        data: bytes | None = None,
    ) -> None:
        """Initialize a new instance of PropertyValueWrite."""

        if data is None:
            data = bytearray()

        self.object_index = object_index
        self.property_id = property_id
        self.count = count
        self.start_index = start_index
        self.data = data

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5 + len(self.data)

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.count < 0 or self.count > 2 ** 4:
            raise ConversionError("Count out of range.")

        size = len(self.data)
        count = self.count << 4
        payload = struct.pack(
            f"!BBBB{size}s",
            self.object_index,
            self.property_id,
            count,
            self.start_index,
            self.data,
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 6

        (
            _,
            self.object_index,
            self.property_id,
            self.count,
            self.start_index,
            self.data,
        ) = struct.unpack(f"!BBBBB{size}s", raw[1:])

        self.count = self.count >> 4

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


class PropertyValueResponse(APCI):
    """
    PropertyValueResponse service.

    Payload indicates object, property, count, start and data itself. Size of
    the payload depends on the data.
    """

    CODE = APCIExtendedService.PROPERTY_VALUE_RESPONSE

    def __init__(
        self,
        object_index: int = 0,
        property_id: int = 0,
        count: int = 0,
        start_index: int = 0,
        data: bytes | None = None,
    ) -> None:
        """Initialize a new instance of PropertyValueResponse."""

        if data is None:
            data = bytearray()

        self.object_index = object_index
        self.property_id = property_id
        self.count = count
        self.start_index = start_index
        self.data = data

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5 + len(self.data)

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        size = len(raw) - 6

        (
            _,
            self.object_index,
            self.property_id,
            self.count,
            self.start_index,
            self.data,
        ) = struct.unpack(f"!BBBBB{size}s", raw[1:])

        self.count = self.count >> 4

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.count < 0 or self.count > 2 ** 4:
            raise ConversionError("Count out of range.")

        size = len(self.data)
        count = self.count << 4
        payload = struct.pack(
            f"!BBBB{size}s",
            self.object_index,
            self.property_id,
            count,
            self.start_index,
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


class PropertyDescriptionRead(APCI):
    """PropertyDescriptionRead service."""

    CODE = APCIExtendedService.PROPERTY_DESCRIPTION_READ

    def __init__(
        self, object_index: int = 0, property_id: int = 0, property_index: int = 0
    ) -> None:
        """Initialize a new instance of PropertyDescriptionRead."""
        self.object_index = object_index
        self.property_id = property_id
        self.property_index = property_index

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        self.object_index, self.property_id, self.property_index = struct.unpack(
            "!BBB", raw[2:]
        )

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        payload = struct.pack(
            "!BBB", self.object_index, self.property_id, self.property_index
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<PropertyDescriptionRead object_index="{self.object_index}" property_id="{self.property_id}" property_index="{self.property_index}" />'


class PropertyDescriptionResponse(APCI):
    """PropertyDescriptionResponse service."""

    CODE = APCIExtendedService.PROPERTY_DESCRIPTION_RESPONSE

    def __init__(
        self,
        object_index: int = 0,
        property_id: int = 0,
        property_index: int = 0,
        type_: int = 0,
        max_count: int = 0,
        access: int = 0,
    ) -> None:
        """Initialize a new instance of PropertyDescriptionRead."""
        self.object_index = object_index
        self.property_id = property_id
        self.property_index = property_index
        self.type = type_
        self.max_count = max_count
        self.access = access

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 8

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        (
            self.object_index,
            self.property_id,
            self.property_index,
            self.type,
            max_count,
            self.access,
        ) = struct.unpack("!BBBBHB", raw[2:])

        self.max_count = max_count & 0x0FFF

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.max_count < 0 or self.max_count >= 2 ** 12:
            raise ConversionError("Max count out of range.")

        payload = struct.pack(
            "!BBBBHB",
            self.object_index,
            self.property_id,
            self.property_index,
            self.type,
            self.max_count & 0x0FFF,
            self.access,
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<PropertyDescriptionResponse object_index="{self.object_index}" property_id="{self.property_id}" property_index="{self.property_index}" type="{self.type}" max_count="{self.max_count}" access="{self.access}" />'


class IndividualAddressSerialRead(APCI):
    """IndividualAddressSerialRead service."""

    CODE = APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_READ

    def __init__(self, serial: bytes | None = None) -> None:
        """Initialize a new instance of PropertyDescriptionRead."""
        if serial is None:
            serial = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

        self.serial = serial

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 7

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        (self.serial,) = struct.unpack("!6s", raw[2:])

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if len(self.serial) != 6:
            raise ConversionError("Serial must be 6 bytes.")

        payload = struct.pack("!6s", self.serial)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<IndividualAddressSerialRead serial="{self.serial.hex()}" />'


class IndividualAddressSerialResponse(APCI):
    """IndividualAddressSerialResponse service."""

    CODE = APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_RESPONSE

    def __init__(
        self,
        serial: bytes | None = None,
        address: IndividualAddress | None = None,
    ) -> None:
        """Initialize a new instance of IndividualAddressSerialResponse."""
        if serial is None:
            serial = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        if address is None:
            address = IndividualAddress("0.0.0")

        self.serial = serial
        self.address = address

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 11

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        self.serial, address_high, address_low, _ = struct.unpack("!6sBBH", raw[2:])

        self.address = IndividualAddress((address_high, address_low))

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if len(self.serial) != 6:
            raise ConversionError("Serial must be 6 bytes.")

        address_high, address_low = self.address.to_knx()
        payload = struct.pack("!6sBBH", self.serial, address_high, address_low, 0)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<IndividualAddressSerialResponse serial="{self.serial.hex()}" address="{self.address}" />'


class IndividualAddressSerialWrite(APCI):
    """IndividualAddressSerialWrite service."""

    CODE = APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_WRITE

    def __init__(
        self,
        serial: bytes | None = None,
        address: IndividualAddress | None = None,
    ) -> None:
        """Initialize a new instance of IndividualAddressSerialWrite."""
        if serial is None:
            serial = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        if address is None:
            address = IndividualAddress("0.0.0")

        self.serial = serial
        self.address = address

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 13

    def from_knx(self, raw: bytes) -> None:
        """Parse/deserialize from KNX/IP raw data."""
        self.serial, address_high, address_low, _ = struct.unpack("!6sBBI", raw[2:])

        self.address = IndividualAddress((address_high, address_low))

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if len(self.serial) != 6:
            raise ConversionError("Serial must be 6 bytes.")

        address_high, address_low = self.address.to_knx()
        payload = struct.pack("!6sBBI", self.serial, address_high, address_low, 0)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<IndividualAddressSerialWrite serial="{self.serial.hex()}" address="{self.address}" />'
