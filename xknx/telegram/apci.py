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

    SYSTEM_NETWORK_PARAMETER_READ = 0x1C8
    SYSTEM_NETWORK_PARAMETER_RESPONSE = 0x1C9
    SYSTEM_NETWORK_PARAMETER_WRITE = 0x1CA

    PROPERTY_EXT_VALUE_READ = 0x1CC
    PROPERTY_EXT_VALUE_RESPONSE = 0x1CD
    PROPERTY_EXT_VALUE_WRITE_CON = 0x1CE
    PROPERTY_EXT_VALUE_WRITE_CON_RES = 0x1CF
    PROPERTY_EXT_VALUE_WRITE_UNCON = 0x1D0
    PROPERTY_EXT_VALUE_INFO_REPORT = 0x1D1
    PROPERTY_EXT_DESCRIPTION_READ = 0x1D2
    PROPERTY_EXT_DESCRIPTION_RESPONSE = 0x1D3

    FUNCTION_PROPERTY_EXT_COMMAND = 0x1D4
    FUNCTION_PROPERTY_EXT_STATE_READ = 0x1D5
    FUNCTION_PROPERTY_EXT_STATE_RESPONSE = 0x1D6

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
    RESTART_MASTER_RESET = 0x0381
    RESTART_MASTER_RESET_RESPONSE = 0x03A1

    ESCAPE = 0x03C0


class APCIUserService(Enum):
    """Enum class for user message APCI services."""

    USER_MEMORY_READ = 0x02C0
    USER_MEMORY_RESPONSE = 0x02C1
    USER_MEMORY_WRITE = 0x02C2

    USER_MEMORY_BIT_WRITE = 0x02C4

    USER_MANUFACTURER_INFO_READ = 0x02C5
    USER_MANUFACTURER_INFO_RESPONSE = 0x02C6

    FUNCTION_PROPERTY_COMMAND = 0x02C7
    FUNCTION_PROPERTY_STATE_READ = 0x02C8
    FUNCTION_PROPERTY_STATE_RESPONSE = 0x02C9


class APCIExtendedService(Enum):
    """Enum class for extended APCI services."""

    # Coupler specific services
    FILTER_TABLE_OPEN = 0x03C0
    FILTER_TABLE_READ = 0x03C1
    FILTER_TABLE_RESPONSE = 0x03C2
    FILTER_TABLE_WRITE = 0x03C3

    ROUTER_MEMORY_READ = 0x03C8
    ROUTER_MEMORY_RESPONSE = 0x03C9
    ROUTER_MEMORY_WRITE = 0x03CA

    ROUTER_STATUS_READ = 0x03CD
    ROUTER_STATUS_RESPONSE = 0x03CE
    ROUTER_STATUS_WRITE = 0x03CF

    # not for future use
    MEMORY_BIT_WRITE = 0x03D0

    AUTHORIZE_REQUEST = 0x03D1
    AUTHORIZE_RESPONSE = 0x03D2

    KEY_WRITE = 0x03D3
    KEY_RESPONSE = 0x03D4

    PROPERTY_VALUE_READ = 0x03D5
    PROPERTY_VALUE_RESPONSE = 0x03D6
    PROPERTY_VALUE_WRITE = 0x03D7

    PROPERTY_DESCRIPTION_READ = 0x03D8
    PROPERTY_DESCRIPTION_RESPONSE = 0x03D9

    NETWORK_PARAMETER_READ = 0x03DA
    NETWORK_PARAMETER_RESPONSE = 0x03DB

    INDIVIDUAL_ADDRESS_SERIAL_READ = 0x03DC
    INDIVIDUAL_ADDRESS_SERIAL_RESPONSE = 0x03DD
    INDIVIDUAL_ADDRESS_SERIAL_WRITE = 0x03DE

    # Open media specific services
    DOMAIN_ADDRESS_WRITE = 0x03E0
    DOMAIN_ADDRESS_READ = 0x03E1
    DOMAIN_ADDRESS_RESPONSE = 0x03E2
    DOMAIN_ADDRESS_SELECTIVE_READ = 0x03E3

    NETWORK_PARAMETER_WRITE = 0x03E4

    LINK_READ = 0x03E5
    LINK_RESPONSE = 0x03E6
    LINK_WRITE = 0x03E7

    GROUP_PROP_VALUE_READ = 0x03E8
    GROUP_PROP_VALUE_RESPONSE = 0x03E9
    GROUP_PROP_VALUE_WRITE = 0x03EA
    GROUP_PROP_VALUE_INFO_REPORT = 0x03EB

    DOMAIN_ADDRESS_SERIAL_NUMBER_READ = 0x03EC
    DOMAIN_ADDRESS_SERIAL_NUMBER_RESPONSE = 0x03ED
    DOMAIN_ADDRESS_SERIAL_NUMBER_WRITE = 0x03EE

    FILE_STREAM_INFO_REPORT = 0x03F0

    # DataSecure
    APCI_SEC = 0x03F1


class ReturnCode(Enum):
    """Enum class for Generic device management Return Codes."""

    ## Basic positive Return Code
    # The service, function or command is executed successfully, without additional information.
    E_SUCCESS = 0x00
    ## Generic negative Return Codes
    # Memory cannot be accessed or only with fault(s).
    E_MEMORY_ERROR = 0xF1
    # The command is not supported by this server.
    E_COMMAND_INVALID = 0xF2
    # The command is supported and well formatted, but not possible to
    # execute right now - there is a dependency that is not fulfilled.
    E_COMMAND_IMPOSSIBLE = 0xF3
    # Requested data will not fit into a Frame supported by this server.
    # This shall be used for Device limitations of the maximum supported Frame length
    # by accessing resources (Properties, Function Properties, memory…) of the device.
    E_LENGTH_EXCEEDS_MAX_APDU_LENGTH = 0xF4
    # Writing data beyond what is reserved for the addressed Resource.
    E_DATA_OVERFLOW = 0xF5
    # Write value too low. Preferable to give this instead of “Value not supported”.
    E_DATA_MIN = 0xF6
    # Write value too high. Preferable to give this instead of “Value not supported”.
    E_DATA_MAX = 0xF7
    # The service or function is supported, but request data is not valid for this receiver.
    E_DATA_VOID = 0xF8
    # Data could generally be written, but not possible at this time.
    E_TEMPORARILY_NOT_AVAILABLE = 0xF9
    # Read access attempted to a “write only” service or Resource.
    E_ACCESS_WRITE_ONLY = 0xFA
    # Write access attempted to a “read only” service or Resource.
    E_ACCESS_READ_ONLY = 0xFB
    # Access denied due to authorization reasons. A_Authorize as well as KNX Security
    E_ACCESS_DENIED = 0xFC
    # Interface Object or Property is not present, or index is out of range.
    E_ADDRESS_VOID = 0xFD
    # Write access with a wrong datatype (Datapoint length).
    E_DATA_TYPE_CONFLICT = 0xFE
    # The service, function or command has failed without a closer indication of the problem.
    E_ERROR = 0xFF
    ## Generic positive Return Codes
    # (01h-1Fh - None proposed)
    ## Specific positive Return Codes
    # (20h-5Fh - None proposed)
    ## Specific negative Return Codes
    # (A0h-DFh - None proposed)


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
            if apci == APCIService.SYSTEM_NETWORK_PARAMETER_READ.value:
                return SystemNetworkParameterRead.from_knx(raw)
            if apci == APCIService.SYSTEM_NETWORK_PARAMETER_RESPONSE.value:
                return SystemNetworkParameterResponse.from_knx(raw)
            if apci == APCIService.SYSTEM_NETWORK_PARAMETER_WRITE.value:
                return SystemNetworkParameterWrite.from_knx(raw)
            if apci == APCIService.PROPERTY_EXT_VALUE_READ.value:
                return PropertyExtValueRead.from_knx(raw)
            if apci == APCIService.PROPERTY_EXT_VALUE_RESPONSE.value:
                return PropertyExtValueResponse.from_knx(raw)
            if apci == APCIService.PROPERTY_EXT_VALUE_WRITE_CON.value:
                return PropertyExtValueWriteCon.from_knx(raw)
            if apci == APCIService.PROPERTY_EXT_VALUE_WRITE_CON_RES.value:
                return PropertyExtValueWriteConRes.from_knx(raw)
            if apci == APCIService.PROPERTY_EXT_VALUE_WRITE_UNCON.value:
                return PropertyExtValueWriteUnCon.from_knx(raw)
            if apci == APCIService.PROPERTY_EXT_VALUE_INFO_REPORT.value:
                return PropertyExtValueInfoReport.from_knx(raw)
            if apci == APCIService.PROPERTY_EXT_DESCRIPTION_READ.value:
                return PropertyExtDescriptionRead.from_knx(raw)
            if apci == APCIService.PROPERTY_EXT_DESCRIPTION_RESPONSE.value:
                return PropertyExtDescriptionResponse.from_knx(raw)
            if apci == APCIService.MEMORY_EXTENDED_WRITE.value:
                return MemoryExtendedWrite.from_knx(raw)
            if apci == APCIService.MEMORY_EXTENDED_WRITE_RESPONSE.value:
                return MemoryExtendedWriteResponse.from_knx(raw)
            if apci == APCIService.MEMORY_EXTENDED_READ.value:
                return MemoryExtendedRead.from_knx(raw)
            if apci == APCIService.MEMORY_EXTENDED_READ_RESPONSE.value:
                return MemoryExtendedReadResponse.from_knx(raw)
            if apci == APCIService.FUNCTION_PROPERTY_EXT_COMMAND.value:
                return FunctionPropertyExtCommand.from_knx(raw)
            if apci == APCIService.FUNCTION_PROPERTY_EXT_STATE_READ.value:
                return FunctionPropertyExtStateRead.from_knx(raw)
            if apci == APCIService.FUNCTION_PROPERTY_EXT_STATE_RESPONSE.value:
                return FunctionPropertyExtStateResponse.from_knx(raw)
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
            if apci == APCIUserService.USER_MEMORY_BIT_WRITE.value:
                return UserMemoryBitWrite.from_knx(raw)
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
            if apci == APCIService.RESTART_MASTER_RESET.value:
                return RestartMasterReset.from_knx(raw)
            if apci == APCIService.RESTART_MASTER_RESET_RESPONSE.value:
                return RestartMasterResetResponse.from_knx(raw)
            return Restart.from_knx(raw)
        if service == APCIService.ESCAPE.value:
            if apci == APCIExtendedService.FILTER_TABLE_OPEN.value:
                return FilterTableOpen.from_knx(raw)
            if apci == APCIExtendedService.FILTER_TABLE_READ.value:
                return FilterTableRead.from_knx(raw)
            if apci == APCIExtendedService.FILTER_TABLE_RESPONSE.value:
                return FilterTableResponse.from_knx(raw)
            if apci == APCIExtendedService.FILTER_TABLE_WRITE.value:
                return FilterTableWrite.from_knx(raw)
            if apci == APCIExtendedService.ROUTER_MEMORY_READ.value:
                return RouterMemoryRead.from_knx(raw)
            if apci == APCIExtendedService.ROUTER_MEMORY_RESPONSE.value:
                return RouterMemoryResponse.from_knx(raw)
            if apci == APCIExtendedService.ROUTER_MEMORY_WRITE.value:
                return RouterMemoryWrite.from_knx(raw)
            if apci == APCIExtendedService.ROUTER_STATUS_READ.value:
                return RouterStatusRead.from_knx(raw)
            if apci == APCIExtendedService.ROUTER_STATUS_RESPONSE.value:
                return RouterStatusResponse.from_knx(raw)
            if apci == APCIExtendedService.ROUTER_STATUS_WRITE.value:
                return RouterStatusWrite.from_knx(raw)
            if apci == APCIExtendedService.MEMORY_BIT_WRITE.value:
                return MemoryBitWrite.from_knx(raw)
            if apci == APCIExtendedService.AUTHORIZE_REQUEST.value:
                return AuthorizeRequest.from_knx(raw)
            if apci == APCIExtendedService.AUTHORIZE_RESPONSE.value:
                return AuthorizeResponse.from_knx(raw)
            if apci == APCIExtendedService.KEY_WRITE.value:
                return KeyWrite.from_knx(raw)
            if apci == APCIExtendedService.KEY_RESPONSE.value:
                return KeyResponse.from_knx(raw)
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
            if apci == APCIExtendedService.NETWORK_PARAMETER_READ.value:
                return NetworkParameterRead.from_knx(raw)
            if apci == APCIExtendedService.NETWORK_PARAMETER_RESPONSE.value:
                return NetworkParameterResponse.from_knx(raw)
            if apci == APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_READ.value:
                return IndividualAddressSerialRead.from_knx(raw)
            if apci == APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_RESPONSE.value:
                return IndividualAddressSerialResponse.from_knx(raw)
            if apci == APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_WRITE.value:
                return IndividualAddressSerialWrite.from_knx(raw)
            if apci == APCIExtendedService.DOMAIN_ADDRESS_WRITE.value:
                return DomainAddressWrite.from_knx(raw)
            if apci == APCIExtendedService.DOMAIN_ADDRESS_READ.value:
                return DomainAddressRead.from_knx(raw)
            if apci == APCIExtendedService.DOMAIN_ADDRESS_RESPONSE.value:
                return DomainAddressResponse.from_knx(raw)
            if apci == APCIExtendedService.DOMAIN_ADDRESS_SELECTIVE_READ.value:
                return DomainAddressSelectiveRead.from_knx(raw)
            if apci == APCIExtendedService.NETWORK_PARAMETER_WRITE.value:
                return NetworkParameterWrite.from_knx(raw)
            if apci == APCIExtendedService.LINK_READ.value:
                return LinkRead.from_knx(raw)
            if apci == APCIExtendedService.LINK_RESPONSE.value:
                return LinkResponse.from_knx(raw)
            if apci == APCIExtendedService.LINK_WRITE.value:
                return LinkWrite.from_knx(raw)
            if apci == APCIExtendedService.GROUP_PROP_VALUE_READ.value:
                return GroupPropValueRead.from_knx(raw)
            if apci == APCIExtendedService.GROUP_PROP_VALUE_RESPONSE.value:
                return GroupPropValueResponse.from_knx(raw)
            if apci == APCIExtendedService.GROUP_PROP_VALUE_WRITE.value:
                return GroupPropValueWrite.from_knx(raw)
            if apci == APCIExtendedService.GROUP_PROP_VALUE_INFO_REPORT.value:
                return GroupPropValueInfoReport.from_knx(raw)
            if apci == APCIExtendedService.DOMAIN_ADDRESS_SERIAL_NUMBER_READ.value:
                return DomainAddressSerialNumberRead.from_knx(raw)
            if apci == APCIExtendedService.DOMAIN_ADDRESS_SERIAL_NUMBER_RESPONSE.value:
                return DomainAddressSerialNumberResponse.from_knx(raw)
            if apci == APCIExtendedService.DOMAIN_ADDRESS_SERIAL_NUMBER_WRITE.value:
                return DomainAddressSerialNumberWrite.from_knx(raw)
            if apci == APCIExtendedService.FILE_STREAM_INFO_REPORT.value:
                return FileStreamInfoReport.from_knx(raw)
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


def _pack_function_property_ext_header(
    interface_object_type: int, object_instance: int, property_id: int
) -> bytes:
    """
    Serialize the A_FunctionPropertyExt* ASDU header.

    16 bit interface_object_type, then a 12 bit object_instance
    followed by a 12 bit property_id, packed into 3 bytes. See KNX
    Specification 03_03_07 Application Layer §3.4.8.2.
    """
    if not 0 <= interface_object_type <= 0xFFFF:
        raise ConversionError("Interface object type out of range.")
    if not 0 <= object_instance <= 0xFFF:
        raise ConversionError("Object instance out of range.")
    if not 0 <= property_id <= 0xFFF:
        raise ConversionError("Property ID out of range.")
    return struct.pack(
        "!HBBB",
        interface_object_type,
        object_instance >> 4,
        ((object_instance & 0xF) << 4) | (property_id >> 8),
        property_id & 0xFF,
    )


def _unpack_function_property_ext_header(raw: bytes) -> tuple[int, int, int]:
    """
    Parse the A_FunctionPropertyExt* ASDU header.

    `raw` shall be the complete APDU (raw[2:4] is the 16 bit
    interface_object_type, raw[4:7] packs the 12 bit object_instance and
    12 bit property_id with no reserved bits). See KNX Specification
    03_03_07 Application Layer §3.4.8.
    """
    interface_object_type = (raw[2] << 8) | raw[3]
    object_instance = (raw[4] << 4) | (raw[5] >> 4)
    property_id = ((raw[5] & 0x0F) << 8) | raw[6]
    return interface_object_type, object_instance, property_id


@dataclass(slots=True)
class FunctionPropertyExtCommand(APCI):
    """
    FunctionPropertyExtCommand service.

    See KNX Specification 03_03_07 Application Layer §3.4.8.1
    A_FunctionPropertyExtCommand.

    Payload contains a 16 bit Interface Object Type, a 12 bit Object
    Instance, a 12 bit Property ID, and function-specific input data of
    variable length.
    """

    CODE: ClassVar = APCIService.FUNCTION_PROPERTY_EXT_COMMAND

    interface_object_type: int
    object_instance: int
    property_id: int
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 6 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> FunctionPropertyExtCommand:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 7:
            raise ConversionError(
                f"Invalid length for A_FunctionPropertyExtCommand in CEMI: {raw.hex()}"
            )
        interface_object_type, object_instance, property_id = (
            _unpack_function_property_ext_header(raw)
        )

        return cls(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            data=raw[7:],
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        header = _pack_function_property_ext_header(
            self.interface_object_type, self.object_instance, self.property_id
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=header + self.data)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<FunctionPropertyExtCommand "
            f'interface_object_type="{self.interface_object_type}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'data="{self.data.hex()}" />'
        )


@dataclass(slots=True)
class FunctionPropertyExtStateRead(APCI):
    """
    FunctionPropertyExtStateRead service.

    See KNX Specification 03_03_07 Application Layer §3.4.8.2
    A_FunctionPropertyExtState_Read.

    Payload contains a 16 bit Interface Object Type, a 12 bit Object
    Instance, a 12 bit Property ID, and function-specific input data of
    variable length.
    """

    CODE: ClassVar = APCIService.FUNCTION_PROPERTY_EXT_STATE_READ

    interface_object_type: int
    object_instance: int
    property_id: int
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 6 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> FunctionPropertyExtStateRead:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 7:
            raise ConversionError(
                f"Invalid length for A_FunctionPropertyExtState_Read in CEMI: {raw.hex()}"
            )
        interface_object_type, object_instance, property_id = (
            _unpack_function_property_ext_header(raw)
        )

        return cls(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            data=raw[7:],
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        header = _pack_function_property_ext_header(
            self.interface_object_type, self.object_instance, self.property_id
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=header + self.data)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<FunctionPropertyExtStateRead "
            f'interface_object_type="{self.interface_object_type}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'data="{self.data.hex()}" />'
        )


@dataclass(slots=True)
class FunctionPropertyExtStateResponse(APCI):
    """
    FunctionPropertyExtStateResponse service.

    See KNX Specification 03_03_07 Application Layer §3.4.8.2
    A_FunctionPropertyExtState_Response.

    Same header as FunctionPropertyExtStateRead (16 bit
    Interface Object Type, 12 bit Object Instance, 12 bit Property ID),
    followed by a 1 byte return_code and function-specific output data
    of variable length.
    """

    CODE: ClassVar = APCIService.FUNCTION_PROPERTY_EXT_STATE_RESPONSE

    interface_object_type: int
    object_instance: int
    property_id: int
    return_code: ReturnCode
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 7 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> FunctionPropertyExtStateResponse:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 8:
            raise ConversionError(
                f"Invalid length for A_FunctionPropertyExtState_Response in CEMI: {raw.hex()}"
            )
        interface_object_type, object_instance, property_id = (
            _unpack_function_property_ext_header(raw)
        )
        try:
            return_code = ReturnCode(raw[7])
        except ValueError:
            raise ConversionError(
                f"Invalid return code for A_FunctionPropertyExtState_Response in CEMI: {raw.hex()}"
            ) from None

        return cls(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            return_code=return_code,
            data=raw[8:],
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        header = _pack_function_property_ext_header(
            self.interface_object_type, self.object_instance, self.property_id
        )

        return encode_cmd_and_payload(
            self.CODE,
            appended_payload=header + bytes([self.return_code.value]) + self.data,
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<FunctionPropertyExtStateResponse "
            f'interface_object_type="{self.interface_object_type}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'return_code="{self.return_code.name}" '
            f'data="{self.data.hex()}" />'
        )


def _pack_system_network_parameter_header(object_type: int, property_id: int) -> bytes:
    """
    Serialize the A_SystemNetworkParameter_Read/Response ASDU header.

    16 bit object_type, then a 12 bit property_id followed by 4 reserved
    bits (always emitted as 0). See KNX Specification 03_03_07
    Application Layer §3.3.8.
    """
    if not 0 <= object_type <= 0xFFFF:
        raise ConversionError("Object type out of range.")
    if not 0 <= property_id <= 0xFFF:
        raise ConversionError("Property ID out of range.")
    return struct.pack("!HH", object_type, property_id << 4)


def _unpack_system_network_parameter_header(raw: bytes) -> tuple[int, int]:
    """
    Parse the A_SystemNetworkParameter_Read/Response ASDU header.

    `raw` shall be the complete APDU (raw[2:4] is the 16 bit object_type,
    raw[4] and the upper nibble of raw[5] form the 12 bit property_id, the
    lower nibble of raw[5] is reserved and discarded). See KNX
    Specification 03_03_07 Application Layer §3.3.8.
    """
    object_type = (raw[2] << 8) | raw[3]
    property_id = (raw[4] << 4) | (raw[5] >> 4)
    return object_type, property_id


@dataclass(slots=True)
class SystemNetworkParameterRead(APCI):
    """
    SystemNetworkParameterRead service.

    See KNX Specification 03_03_07 Application Layer §3.3.8
    A_SystemNetworkParameter_Read.

    APCI 0x1C8 falls within the same 4 bit service nibble (0b0111) that is
    otherwise used for A_ADC_Response, but is a distinct, dedicated service.
    Payload contains a 16 bit interface object type, a 12 bit Property ID
    and a PID-specific, variable-length test_info used eg. by ETS to
    discover devices and system parameters via broadcast.
    """

    CODE: ClassVar = APCIService.SYSTEM_NETWORK_PARAMETER_READ

    object_type: int
    property_id: int
    test_info: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5 + len(self.test_info)

    @classmethod
    def from_knx(cls, raw: bytes) -> SystemNetworkParameterRead:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 6:
            raise ConversionError(
                f"Invalid length for A_SystemNetworkParameter_Read in CEMI: {raw.hex()}"
            )
        object_type, property_id = _unpack_system_network_parameter_header(raw)

        return cls(
            object_type=object_type,
            property_id=property_id,
            test_info=raw[6:],
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        payload = _pack_system_network_parameter_header(
            self.object_type, self.property_id
        )

        return encode_cmd_and_payload(
            self.CODE, appended_payload=payload + self.test_info
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<SystemNetworkParameterRead object_type="{self.object_type}" '
            f'property_id="{self.property_id}" test_info="{self.test_info.hex()}" />'
        )


@dataclass(slots=True)
class SystemNetworkParameterResponse(APCI):
    """
    SystemNetworkParameterResponse service.

    See KNX Specification 03_03_07 Application Layer §3.3.8
    A_SystemNetworkParameter_Response.

    Same header as SystemNetworkParameterRead (16 bit object_type, 12 bit
    property_id, 4 reserved bits). Beyond that, the PDU has two
    variable-length fields, test_info and test_result, with no length
    indicator on the wire separating them - the boundary is only known if
    the original request's test_info length is known. Since APCI parsing
    here is stateless, both are kept together as `test_info_and_result`
    instead of guessing a split.
    """

    CODE: ClassVar = APCIService.SYSTEM_NETWORK_PARAMETER_RESPONSE

    object_type: int
    property_id: int
    test_info_and_result: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5 + len(self.test_info_and_result)

    @classmethod
    def from_knx(cls, raw: bytes) -> SystemNetworkParameterResponse:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 6:
            raise ConversionError(
                f"Invalid length for A_SystemNetworkParameter_Response in CEMI: {raw.hex()}"
            )
        object_type, property_id = _unpack_system_network_parameter_header(raw)

        return cls(
            object_type=object_type,
            property_id=property_id,
            test_info_and_result=raw[6:],
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        payload = _pack_system_network_parameter_header(
            self.object_type, self.property_id
        )

        return encode_cmd_and_payload(
            self.CODE, appended_payload=payload + self.test_info_and_result
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<SystemNetworkParameterResponse object_type="{self.object_type}" '
            f'property_id="{self.property_id}" '
            f'test_info_and_result="{self.test_info_and_result.hex()}" />'
        )


@dataclass(slots=True)
class SystemNetworkParameterWrite(APCI):
    """
    SystemNetworkParameterWrite service.

    See KNX Specification 03_03_07 Application Layer §3.3.9
    A_SystemNetworkParameter_Write.

    Same header as SystemNetworkParameterRead/Response (16 bit object_type,
    12 bit property_id, 4 reserved bits), followed by a PID-specific,
    variable-length value to write.
    """

    CODE: ClassVar = APCIService.SYSTEM_NETWORK_PARAMETER_WRITE

    object_type: int
    property_id: int
    value: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 5 + len(self.value)

    @classmethod
    def from_knx(cls, raw: bytes) -> SystemNetworkParameterWrite:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 6:
            raise ConversionError(
                f"Invalid length for A_SystemNetworkParameter_Write in CEMI: {raw.hex()}"
            )
        object_type, property_id = _unpack_system_network_parameter_header(raw)

        return cls(
            object_type=object_type,
            property_id=property_id,
            value=raw[6:],
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        payload = _pack_system_network_parameter_header(
            self.object_type, self.property_id
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload + self.value)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<SystemNetworkParameterWrite object_type="{self.object_type}" '
            f'property_id="{self.property_id}" value="{self.value.hex()}" />'
        )


@dataclass(slots=True)
class PropertyExtValueRead(APCI):
    """
    PropertyExtValueRead service.

    See KNX Specification 03_03_07 Application Layer §3.4.5.1
    A_PropertyExtValue_Read.

    Payload contains a 16 bit Interface Object Type, a 12 bit Object
    Instance, a 12 bit Property ID, a 1 byte Number of Elements and a
    2 byte Start Index.
    """

    CODE: ClassVar = APCIService.PROPERTY_EXT_VALUE_READ

    interface_object_type: int
    object_instance: int
    property_id: int
    nr_of_elem: int = 1
    start_index: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 9

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyExtValueRead:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != 10:
            raise ConversionError(
                f"Invalid length for A_PropertyExtValue_Read in CEMI: {raw.hex()}"
            )
        interface_object_type, object_instance, property_id = (
            _unpack_function_property_ext_header(raw)
        )
        nr_of_elem, start_index = struct.unpack("!BH", raw[7:10])

        return cls(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            nr_of_elem=nr_of_elem,
            start_index=start_index,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        header = _pack_function_property_ext_header(
            self.interface_object_type, self.object_instance, self.property_id
        )
        if not 0 <= self.nr_of_elem <= 0xFF:
            raise ConversionError("Number of elements out of range.")
        if not 0 <= self.start_index <= 0xFFFF:
            raise ConversionError("Start index out of range.")
        payload = header + struct.pack("!BH", self.nr_of_elem, self.start_index)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<PropertyExtValueRead "
            f'interface_object_type="{self.interface_object_type}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'nr_of_elem="{self.nr_of_elem}" '
            f'start_index="{self.start_index}" />'
        )


@dataclass(slots=True)
class PropertyExtValueResponse(APCI):
    """
    PropertyExtValueResponse service.

    See KNX Specification 03_03_07 Application Layer §3.4.5.1
    A_PropertyExtValue_Response (defined alongside A_PropertyExtValue_Read).

    Payload contains a 16 bit Interface Object Type, a 12 bit Object
    Instance, a 12 bit Property ID, a 1 byte Number of Elements, a 2
    byte Start Index and variable-length data.
    """

    CODE: ClassVar = APCIService.PROPERTY_EXT_VALUE_RESPONSE

    interface_object_type: int
    object_instance: int
    property_id: int
    nr_of_elem: int = 1
    start_index: int = 0
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 9 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyExtValueResponse:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 10:
            raise ConversionError(
                f"Invalid length for A_PropertyExtValue_Response in CEMI: {raw.hex()}"
            )
        interface_object_type, object_instance, property_id = (
            _unpack_function_property_ext_header(raw)
        )
        nr_of_elem, start_index = struct.unpack("!BH", raw[7:10])

        return cls(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            nr_of_elem=nr_of_elem,
            start_index=start_index,
            data=raw[10:],
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        header = _pack_function_property_ext_header(
            self.interface_object_type, self.object_instance, self.property_id
        )
        if not 0 <= self.nr_of_elem <= 0xFF:
            raise ConversionError("Number of elements out of range.")
        if not 0 <= self.start_index <= 0xFFFF:
            raise ConversionError("Start index out of range.")
        payload = (
            header + struct.pack("!BH", self.nr_of_elem, self.start_index) + self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<PropertyExtValueResponse "
            f'interface_object_type="{self.interface_object_type}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'nr_of_elem="{self.nr_of_elem}" '
            f'start_index="{self.start_index}" '
            f'data="{self.data.hex()}" />'
        )


@dataclass(slots=True)
class PropertyExtValueWriteCon(APCI):
    """
    PropertyExtValueWriteCon service.

    See KNX Specification 03_03_07 Application Layer §3.4.5.2
    A_PropertyExtValue_WriteCon-service.

    Same payload as PropertyExtValueResponse: a 16 bit Interface Object
    Type, a 12 bit Object Instance, a 12 bit Property ID, a 1 byte
    Number of Elements, a 2 byte Start Index and variable-length data.
    """

    CODE: ClassVar = APCIService.PROPERTY_EXT_VALUE_WRITE_CON

    interface_object_type: int
    object_instance: int
    property_id: int
    nr_of_elem: int = 1
    start_index: int = 0
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 9 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyExtValueWriteCon:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 10:
            raise ConversionError(
                f"Invalid length for A_PropertyExtValue_WriteCon in CEMI: {raw.hex()}"
            )
        interface_object_type, object_instance, property_id = (
            _unpack_function_property_ext_header(raw)
        )
        nr_of_elem, start_index = struct.unpack("!BH", raw[7:10])

        return cls(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            nr_of_elem=nr_of_elem,
            start_index=start_index,
            data=raw[10:],
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        header = _pack_function_property_ext_header(
            self.interface_object_type, self.object_instance, self.property_id
        )
        if not 0 <= self.nr_of_elem <= 0xFF:
            raise ConversionError("Number of elements out of range.")
        if not 0 <= self.start_index <= 0xFFFF:
            raise ConversionError("Start index out of range.")
        payload = (
            header + struct.pack("!BH", self.nr_of_elem, self.start_index) + self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<PropertyExtValueWriteCon "
            f'interface_object_type="{self.interface_object_type}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'nr_of_elem="{self.nr_of_elem}" '
            f'start_index="{self.start_index}" '
            f'data="{self.data.hex()}" />'
        )


@dataclass(slots=True)
class PropertyExtValueWriteConRes(APCI):
    """
    PropertyExtValueWriteConRes service.

    See KNX Specification 03_03_07 Application Layer §3.4.5.2
    A_PropertyExtValue_WriteConRes (defined alongside
    A_PropertyExtValue_WriteCon-service).

    Same payload as PropertyExtValueRead: a 16 bit Interface Object
    Type, a 12 bit Object Instance, a 12 bit Property ID, a 1 byte
    Number of Elements and a 2 byte Start Index, followed by a 1 byte
    return_code.
    """

    CODE: ClassVar = APCIService.PROPERTY_EXT_VALUE_WRITE_CON_RES

    interface_object_type: int
    object_instance: int
    property_id: int
    return_code: ReturnCode
    nr_of_elem: int = 1
    start_index: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 10

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyExtValueWriteConRes:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != 11:
            raise ConversionError(
                f"Invalid length for A_PropertyExtValue_WriteConRes in CEMI: {raw.hex()}"
            )
        interface_object_type, object_instance, property_id = (
            _unpack_function_property_ext_header(raw)
        )
        nr_of_elem, start_index = struct.unpack("!BH", raw[7:10])
        try:
            return_code = ReturnCode(raw[10])
        except ValueError:
            raise ConversionError(
                f"Invalid return code for A_PropertyExtValue_WriteConRes in CEMI: {raw.hex()}"
            ) from None

        return cls(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            return_code=return_code,
            nr_of_elem=nr_of_elem,
            start_index=start_index,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        header = _pack_function_property_ext_header(
            self.interface_object_type, self.object_instance, self.property_id
        )
        if not 0 <= self.nr_of_elem <= 0xFF:
            raise ConversionError("Number of elements out of range.")
        if not 0 <= self.start_index <= 0xFFFF:
            raise ConversionError("Start index out of range.")
        payload = (
            header
            + struct.pack("!BH", self.nr_of_elem, self.start_index)
            + bytes([self.return_code.value])
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<PropertyExtValueWriteConRes "
            f'interface_object_type="{self.interface_object_type}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'nr_of_elem="{self.nr_of_elem}" '
            f'start_index="{self.start_index}" '
            f'return_code="{self.return_code.name}" />'
        )


@dataclass(slots=True)
class PropertyExtValueWriteUnCon(APCI):
    """
    PropertyExtValueWriteUnCon service.

    See KNX Specification 03_03_07 Application Layer §3.4.5.3
    A_PropertyExtValue_WriteUnCon-service.

    Same payload as PropertyExtValueWriteCon (and PropertyExtValueResponse):
    a 16 bit Interface Object Type, a 12 bit Object Instance, a 12 bit
    Property ID, a 1 byte Number of Elements, a 2 byte Start Index and
    variable-length data. Unconfirmed - not followed by a response.
    """

    CODE: ClassVar = APCIService.PROPERTY_EXT_VALUE_WRITE_UNCON

    interface_object_type: int
    object_instance: int
    property_id: int
    nr_of_elem: int = 1
    start_index: int = 0
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 9 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyExtValueWriteUnCon:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 10:
            raise ConversionError(
                f"Invalid length for A_PropertyExtValue_WriteUnCon in CEMI: {raw.hex()}"
            )
        interface_object_type, object_instance, property_id = (
            _unpack_function_property_ext_header(raw)
        )
        nr_of_elem, start_index = struct.unpack("!BH", raw[7:10])

        return cls(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            nr_of_elem=nr_of_elem,
            start_index=start_index,
            data=raw[10:],
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        header = _pack_function_property_ext_header(
            self.interface_object_type, self.object_instance, self.property_id
        )
        if not 0 <= self.nr_of_elem <= 0xFF:
            raise ConversionError("Number of elements out of range.")
        if not 0 <= self.start_index <= 0xFFFF:
            raise ConversionError("Start index out of range.")
        payload = (
            header + struct.pack("!BH", self.nr_of_elem, self.start_index) + self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<PropertyExtValueWriteUnCon "
            f'interface_object_type="{self.interface_object_type}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'nr_of_elem="{self.nr_of_elem}" '
            f'start_index="{self.start_index}" '
            f'data="{self.data.hex()}" />'
        )


@dataclass(slots=True)
class PropertyExtValueInfoReport(APCI):
    """
    PropertyExtValueInfoReport service.

    See KNX Specification 03_03_07 Application Layer §3.4.5.4
    A_PropertyExtValue_InfoReport-service.

    Same payload as PropertyExtValueResponse/WriteCon/WriteUnCon: a 16
    bit Interface Object Type, a 12 bit Object Instance, a 12 bit
    Property ID, a 1 byte Number of Elements, a 2 byte Start Index and
    variable-length data. Unconfirmed - not followed by a response.
    """

    CODE: ClassVar = APCIService.PROPERTY_EXT_VALUE_INFO_REPORT

    interface_object_type: int
    object_instance: int
    property_id: int
    nr_of_elem: int = 1
    start_index: int = 0
    data: bytes = b""

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 9 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyExtValueInfoReport:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 10:
            raise ConversionError(
                f"Invalid length for A_PropertyExtValue_InfoReport in CEMI: {raw.hex()}"
            )
        interface_object_type, object_instance, property_id = (
            _unpack_function_property_ext_header(raw)
        )
        nr_of_elem, start_index = struct.unpack("!BH", raw[7:10])

        return cls(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            nr_of_elem=nr_of_elem,
            start_index=start_index,
            data=raw[10:],
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        header = _pack_function_property_ext_header(
            self.interface_object_type, self.object_instance, self.property_id
        )
        if not 0 <= self.nr_of_elem <= 0xFF:
            raise ConversionError("Number of elements out of range.")
        if not 0 <= self.start_index <= 0xFFFF:
            raise ConversionError("Start index out of range.")
        payload = (
            header + struct.pack("!BH", self.nr_of_elem, self.start_index) + self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<PropertyExtValueInfoReport "
            f'interface_object_type="{self.interface_object_type}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'nr_of_elem="{self.nr_of_elem}" '
            f'start_index="{self.start_index}" '
            f'data="{self.data.hex()}" />'
        )


@dataclass(slots=True)
class PropertyExtDescriptionRead(APCI):
    """
    PropertyExtDescriptionRead service.

    See KNX Specification 03_03_07 Application Layer §3.4.3.2
    A_PropertyExtDescription_Read-service.

    Same header as A_PropertyExtValue_* (16 bit Interface Object Type,
    12 bit Object Instance, 12 bit Property ID), followed by a 4 bit
    Property Description Type and a 12 bit Property Index.
    """

    CODE: ClassVar = APCIService.PROPERTY_EXT_DESCRIPTION_READ

    interface_object_type: int
    object_instance: int
    property_id: int
    description_type: int = 0
    property_index: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 8

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyExtDescriptionRead:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != 9:
            raise ConversionError(
                f"Invalid length for A_PropertyExtDescription_Read in CEMI: {raw.hex()}"
            )
        interface_object_type, object_instance, property_id = (
            _unpack_function_property_ext_header(raw)
        )
        description_type = raw[7] >> 4
        property_index = ((raw[7] & 0x0F) << 8) | raw[8]

        return cls(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            description_type=description_type,
            property_index=property_index,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        header = _pack_function_property_ext_header(
            self.interface_object_type, self.object_instance, self.property_id
        )
        if not 0 <= self.description_type <= 0xF:
            raise ConversionError("Property description type out of range.")
        if not 0 <= self.property_index <= 0xFFF:
            raise ConversionError("Property index out of range.")
        payload = header + struct.pack(
            "!BB",
            (self.description_type << 4) | (self.property_index >> 8),
            self.property_index & 0xFF,
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<PropertyExtDescriptionRead "
            f'interface_object_type="{self.interface_object_type}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'description_type="{self.description_type}" '
            f'property_index="{self.property_index}" />'
        )


@dataclass(slots=True)
class PropertyExtDescriptionResponse(APCI):
    """
    PropertyExtDescriptionResponse service.

    See KNX Specification 03_03_07 Application Layer §3.4.3.2
    A_PropertyExtDescription_Response (defined alongside
    A_PropertyExtDescription_Read-service).

    Same header as A_PropertyExtDescription_Read (16 bit Interface
    Object Type, 12 bit Object Instance, 12 bit Property ID, 4 bit
    Property Description Type, 12 bit Property Index), followed by a
    2 byte DPT main number, a 2 byte DPT sub number, a 1 bit writable
    flag, a reserved bit (always 0), a 6 bit PDT, a 2 byte Max Number
    of Elements, a 4 bit read level and a 4 bit write level.
    """

    CODE: ClassVar = APCIService.PROPERTY_EXT_DESCRIPTION_RESPONSE

    interface_object_type: int
    object_instance: int
    property_id: int
    description_type: int = 0
    property_index: int = 0
    dpt_main: int = 0
    dpt_sub: int = 0
    writable: bool = False
    pdt: int = 0
    max_nr_of_elem: int = 0
    read_level: int = 0
    write_level: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 16

    @classmethod
    def from_knx(cls, raw: bytes) -> PropertyExtDescriptionResponse:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != 17:
            raise ConversionError(
                f"Invalid length for A_PropertyExtDescription_Response in CEMI: {raw.hex()}"
            )
        interface_object_type, object_instance, property_id = (
            _unpack_function_property_ext_header(raw)
        )
        description_type = raw[7] >> 4
        property_index = ((raw[7] & 0x0F) << 8) | raw[8]
        dpt_main, dpt_sub, writable_pdt, max_nr_of_elem, level = struct.unpack(
            "!HHBHB", raw[9:17]
        )

        return cls(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            description_type=description_type,
            property_index=property_index,
            dpt_main=dpt_main,
            dpt_sub=dpt_sub,
            writable=bool(writable_pdt & 0x80),
            pdt=writable_pdt & 0x3F,
            max_nr_of_elem=max_nr_of_elem,
            read_level=level >> 4,
            write_level=level & 0x0F,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        header = _pack_function_property_ext_header(
            self.interface_object_type, self.object_instance, self.property_id
        )
        if not 0 <= self.description_type <= 0xF:
            raise ConversionError("Property description type out of range.")
        if not 0 <= self.property_index <= 0xFFF:
            raise ConversionError("Property index out of range.")
        if not 0 <= self.dpt_main <= 0xFFFF:
            raise ConversionError("DPT main number out of range.")
        if not 0 <= self.dpt_sub <= 0xFFFF:
            raise ConversionError("DPT sub number out of range.")
        if not 0 <= self.pdt <= 0x3F:
            raise ConversionError("PDT out of range.")
        if not 0 <= self.max_nr_of_elem <= 0xFFFF:
            raise ConversionError("Max number of elements out of range.")
        if not 0 <= self.read_level <= 0xF:
            raise ConversionError("Read level out of range.")
        if not 0 <= self.write_level <= 0xF:
            raise ConversionError("Write level out of range.")

        payload = (
            header
            + struct.pack(
                "!BB",
                (self.description_type << 4) | (self.property_index >> 8),
                self.property_index & 0xFF,
            )
            + struct.pack(
                "!HHBHB",
                self.dpt_main,
                self.dpt_sub,
                (0x80 if self.writable else 0x00) | self.pdt,
                self.max_nr_of_elem,
                (self.read_level << 4) | self.write_level,
            )
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<PropertyExtDescriptionResponse "
            f'interface_object_type="{self.interface_object_type}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'description_type="{self.description_type}" '
            f'property_index="{self.property_index}" '
            f'dpt_main="{self.dpt_main}" '
            f'dpt_sub="{self.dpt_sub}" '
            f'writable="{self.writable}" '
            f'pdt="{self.pdt}" '
            f'max_nr_of_elem="{self.max_nr_of_elem}" '
            f'read_level="{self.read_level}" '
            f'write_level="{self.write_level}" />'
        )


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

    See KNX Specification 03_03_07 Application Layer §3.4.2.2
    A_Restart. The 10 bit APCI for the A_Restart family is 4 bits
    (1110) selecting the service, 1 bit for request (0) vs response
    (1), 4 reserved bits (0), and 1 bit for restart type: 0 for Basic
    Restart (this class, no payload) or 1 for Master Reset (see
    RestartMasterReset).
    """

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
class RestartMasterReset(APCI):
    """
    RestartMasterReset service.

    See KNX Specification 03_03_07 Application Layer §3.4.2.2
    A_Restart_Master_Reset - the request variant (restart type bit set,
    see Restart's docstring for the full APCI bit layout).

    Payload contains a 1 byte erase_code and a 1 byte channel_number.
    """

    CODE: ClassVar = APCIService.RESTART_MASTER_RESET

    erase_code: int
    channel_number: int = 0

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 3

    @classmethod
    def from_knx(cls, raw: bytes) -> RestartMasterReset:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != 4:
            raise ConversionError(
                f"Invalid length for A_Restart_Master_Reset in CEMI: {raw.hex()}"
            )
        erase_code, channel_number = struct.unpack("!BB", raw[2:])

        return cls(erase_code=erase_code, channel_number=channel_number)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.erase_code <= 0xFF:
            raise ConversionError("Erase code out of range.")
        if not 0 <= self.channel_number <= 0xFF:
            raise ConversionError("Channel number out of range.")
        payload = struct.pack("!BB", self.erase_code, self.channel_number)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<RestartMasterReset erase_code="{self.erase_code}" '
            f'channel_number="{self.channel_number}" />'
        )


@dataclass(slots=True)
class RestartMasterResetResponse(APCI):
    """
    RestartMasterResetResponse service.

    See KNX Specification 03_03_07 Application Layer §3.4.2.2
    A_Restart_Response - a Basic Restart (RestartMasterReset with
    restart_type unset) is never confirmed at the application layer, so
    this is only ever sent in reply to a Master Reset request.

    Payload contains a 1 byte error_code and a 2 byte process_time.
    """

    CODE: ClassVar = APCIService.RESTART_MASTER_RESET_RESPONSE

    error_code: int
    process_time: int

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4

    @classmethod
    def from_knx(cls, raw: bytes) -> RestartMasterResetResponse:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != 5:
            raise ConversionError(
                f"Invalid length for A_Restart_Response in CEMI: {raw.hex()}"
            )
        error_code, process_time = struct.unpack("!BH", raw[2:])

        return cls(error_code=error_code, process_time=process_time)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.error_code <= 0xFF:
            raise ConversionError("Error code out of range.")
        if not 0 <= self.process_time <= 0xFFFF:
            raise ConversionError("Process time out of range.")
        payload = struct.pack("!BH", self.error_code, self.process_time)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<RestartMasterResetResponse error_code="{self.error_code}" '
            f'process_time="{self.process_time}" />'
        )


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
class UserMemoryBitWrite(APCI):
    """
    UserMemoryBitWrite service.

    See KNX Specification 03_03_07 Application Layer §3.5.6.4
    A_UserMemoryBit_Write.

    Payload contains a 1 byte number (octet count of the contiguous
    block to modify, 1-5), a 2 byte memory_address, and_data and
    xor_data - both `number` bytes long. Each result bit is computed as
    (and_data_bit AND block_bit) XOR xor_data_bit, i.e. and_data=0/
    xor_data=0 clears a bit, and_data=0/xor_data=1 sets it, and_data=1/
    xor_data=0 leaves it unmodified and and_data=1/xor_data=1 inverts
    it.
    """

    CODE: ClassVar = APCIUserService.USER_MEMORY_BIT_WRITE

    address: int
    and_data: bytes
    xor_data: bytes

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.and_data) + len(self.xor_data)

    @classmethod
    def from_knx(cls, raw: bytes) -> UserMemoryBitWrite:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 6:
            raise ConversionError(
                f"Invalid length for A_UserMemoryBit_Write in CEMI: {raw.hex()}"
            )
        number = raw[2]
        if len(raw) != 5 + 2 * number:
            raise ConversionError(
                f"Invalid length for A_UserMemoryBit_Write in CEMI: {raw.hex()}"
            )
        address = (raw[3] << 8) | raw[4]
        and_data = raw[5 : 5 + number]
        xor_data = raw[5 + number : 5 + 2 * number]

        return cls(address=address, and_data=and_data, xor_data=xor_data)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.address <= 0xFFFF:
            raise ConversionError("Address out of range.")
        number = len(self.and_data)
        if not 0 <= number <= 0xFF:
            raise ConversionError("Number out of range.")
        if len(self.xor_data) != number:
            raise ConversionError("and_data and xor_data must have the same length.")

        payload = (
            struct.pack("!BH", number, self.address) + self.and_data + self.xor_data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<UserMemoryBitWrite address="{hex(self.address)}" '
            f'and_data="{self.and_data.hex()}" xor_data="{self.xor_data.hex()}" />'
        )


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
class FilterTableOpen(APCI):
    """
    FilterTableOpen service.

    See KNX Specification 03_03_07 Application Layer §3.6.1
    A_FilterTable_Open. Coupler specific service - opens access to the
    remote Filter Table before A_FilterTable_Read/Write are used. No
    payload.
    """

    CODE: ClassVar = APCIExtendedService.FILTER_TABLE_OPEN

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 1

    @classmethod
    def from_knx(cls, raw: bytes) -> FilterTableOpen:
        """Parse/deserialize from KNX/IP raw data."""
        # Nothing to parse, but must be implemented explicitly.
        return cls()

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        return encode_cmd_and_payload(self.CODE)

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<FilterTableOpen />"


@dataclass(slots=True)
class FilterTableRead(APCI):
    """
    FilterTableRead service.

    See KNX Specification 03_03_07 Application Layer §3.6.2
    A_FilterTable_Read. Coupler specific service - requires
    A_FilterTable_Open first.

    Payload contains a 1 byte number (octet count to read, 1-254) and
    a 2 byte filter_table_address.
    """

    CODE: ClassVar = APCIExtendedService.FILTER_TABLE_READ

    filter_table_address: int
    number: int = 1

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4

    @classmethod
    def from_knx(cls, raw: bytes) -> FilterTableRead:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != 5:
            raise ConversionError(
                f"Invalid length for A_FilterTable_Read in CEMI: {raw.hex()}"
            )
        number, filter_table_address = struct.unpack("!BH", raw[2:])

        return cls(filter_table_address=filter_table_address, number=number)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 1 <= self.number <= 254:
            raise ConversionError("Number out of range.")
        if not 0 <= self.filter_table_address <= 0xFFFF:
            raise ConversionError("Filter table address out of range.")

        payload = struct.pack("!BH", self.number, self.filter_table_address)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<FilterTableRead "
            f'filter_table_address="{hex(self.filter_table_address)}" '
            f'number="{self.number}" />'
        )


@dataclass(slots=True)
class FilterTableResponse(APCI):
    """
    FilterTableResponse service.

    See KNX Specification 03_03_07 Application Layer §3.6.2
    A_FilterTable_Response (defined alongside A_FilterTable_Read).
    Coupler specific service.

    Payload contains a 1 byte number (octet count), a 2 byte
    filter_table_address and `number` bytes of data. A device signals
    an error (e.g. address space unreachable or protected, illegal
    number of octets requested) by responding with number=0 and no
    data.
    """

    CODE: ClassVar = APCIExtendedService.FILTER_TABLE_RESPONSE

    filter_table_address: int
    data: bytes = b""
    number: int = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Post-initialization steps."""
        if self.number is None:
            self.number = len(self.data)  # type: ignore[unreachable]

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> FilterTableResponse:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 5:
            raise ConversionError(
                f"Invalid length for A_FilterTable_Response in CEMI: {raw.hex()}"
            )
        size = len(raw) - 5
        number, filter_table_address, data = struct.unpack(f"!BH{size}s", raw[2:])

        return cls(
            filter_table_address=filter_table_address,
            data=data,
            number=number,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.number <= 254:
            raise ConversionError("Number out of range.")
        if not 0 <= self.filter_table_address <= 0xFFFF:
            raise ConversionError("Filter table address out of range.")

        size = len(self.data)
        payload = struct.pack(
            f"!BH{size}s", self.number, self.filter_table_address, self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<FilterTableResponse "
            f'filter_table_address="{hex(self.filter_table_address)}" '
            f'number="{self.number}" data="{self.data.hex()}" />'
        )


@dataclass(slots=True)
class FilterTableWrite(APCI):
    """
    FilterTableWrite service.

    See KNX Specification 03_03_07 Application Layer §3.6.3
    A_FilterTable_Write. Coupler specific service - requires
    A_FilterTable_Open first.

    Same payload as FilterTableResponse: a 1 byte number (octet count
    to write, 1-254), a 2 byte filter_table_address and `number` bytes
    of data.
    """

    CODE: ClassVar = APCIExtendedService.FILTER_TABLE_WRITE

    filter_table_address: int
    data: bytes = b""
    number: int = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Post-initialization steps."""
        if self.number is None:
            self.number = len(self.data)  # type: ignore[unreachable]

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> FilterTableWrite:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 6:
            raise ConversionError(
                f"Invalid length for A_FilterTable_Write in CEMI: {raw.hex()}"
            )
        size = len(raw) - 5
        number, filter_table_address, data = struct.unpack(f"!BH{size}s", raw[2:])

        return cls(
            filter_table_address=filter_table_address,
            data=data,
            number=number,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 1 <= self.number <= 254:
            raise ConversionError("Number out of range.")
        if not 0 <= self.filter_table_address <= 0xFFFF:
            raise ConversionError("Filter table address out of range.")

        size = len(self.data)
        payload = struct.pack(
            f"!BH{size}s", self.number, self.filter_table_address, self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<FilterTableWrite "
            f'filter_table_address="{hex(self.filter_table_address)}" '
            f'number="{self.number}" data="{self.data.hex()}" />'
        )


@dataclass(slots=True)
class RouterMemoryRead(APCI):
    """
    RouterMemoryRead service.

    See KNX Specification 03_03_07 Application Layer §3.6.4
    A_RouterMemory_Read. Coupler specific service - reads the memory of
    the second controller of the remote communication controller.

    Payload contains a 1 byte number (octet count to read, 1-254) and
    a 2 byte memory_address.
    """

    CODE: ClassVar = APCIExtendedService.ROUTER_MEMORY_READ

    memory_address: int
    number: int = 1

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4

    @classmethod
    def from_knx(cls, raw: bytes) -> RouterMemoryRead:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != 5:
            raise ConversionError(
                f"Invalid length for A_RouterMemory_Read in CEMI: {raw.hex()}"
            )
        number, memory_address = struct.unpack("!BH", raw[2:])

        return cls(memory_address=memory_address, number=number)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 1 <= self.number <= 254:
            raise ConversionError("Number out of range.")
        if not 0 <= self.memory_address <= 0xFFFF:
            raise ConversionError("Memory address out of range.")

        payload = struct.pack("!BH", self.number, self.memory_address)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<RouterMemoryRead "
            f'memory_address="{hex(self.memory_address)}" number="{self.number}" />'
        )


@dataclass(slots=True)
class RouterMemoryResponse(APCI):
    """
    RouterMemoryResponse service.

    See KNX Specification 03_03_07 Application Layer §3.6.4
    A_RouterMemory_Response (defined alongside A_RouterMemory_Read).
    Coupler specific service.

    Payload contains a 1 byte number (octet count), a 2 byte
    memory_address and `number` bytes of data.
    """

    CODE: ClassVar = APCIExtendedService.ROUTER_MEMORY_RESPONSE

    memory_address: int
    data: bytes = b""
    number: int = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Post-initialization steps."""
        if self.number is None:
            self.number = len(self.data)  # type: ignore[unreachable]

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> RouterMemoryResponse:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 5:
            raise ConversionError(
                f"Invalid length for A_RouterMemory_Response in CEMI: {raw.hex()}"
            )
        size = len(raw) - 5
        number, memory_address, data = struct.unpack(f"!BH{size}s", raw[2:])

        return cls(
            memory_address=memory_address,
            data=data,
            number=number,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.number <= 254:
            raise ConversionError("Number out of range.")
        if not 0 <= self.memory_address <= 0xFFFF:
            raise ConversionError("Memory address out of range.")

        size = len(self.data)
        payload = struct.pack(
            f"!BH{size}s", self.number, self.memory_address, self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<RouterMemoryResponse "
            f'memory_address="{hex(self.memory_address)}" number="{self.number}" '
            f'data="{self.data.hex()}" />'
        )


@dataclass(slots=True)
class RouterMemoryWrite(APCI):
    """
    RouterMemoryWrite service.

    See KNX Specification 03_03_07 Application Layer §3.6.5
    A_RouterMemory_Write. Coupler specific service - writes the memory
    of the second controller of the remote communication controller.

    Same payload as RouterMemoryResponse: a 1 byte number (octet count
    to write, 1-254), a 2 byte memory_address and `number` bytes of
    data.
    """

    CODE: ClassVar = APCIExtendedService.ROUTER_MEMORY_WRITE

    memory_address: int
    data: bytes = b""
    number: int = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Post-initialization steps."""
        if self.number is None:
            self.number = len(self.data)  # type: ignore[unreachable]

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.data)

    @classmethod
    def from_knx(cls, raw: bytes) -> RouterMemoryWrite:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 6:
            raise ConversionError(
                f"Invalid length for A_RouterMemory_Write in CEMI: {raw.hex()}"
            )
        size = len(raw) - 5
        number, memory_address, data = struct.unpack(f"!BH{size}s", raw[2:])

        return cls(
            memory_address=memory_address,
            data=data,
            number=number,
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 1 <= self.number <= 254:
            raise ConversionError("Number out of range.")
        if not 0 <= self.memory_address <= 0xFFFF:
            raise ConversionError("Memory address out of range.")

        size = len(self.data)
        payload = struct.pack(
            f"!BH{size}s", self.number, self.memory_address, self.data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<RouterMemoryWrite "
            f'memory_address="{hex(self.memory_address)}" number="{self.number}" '
            f'data="{self.data.hex()}" />'
        )


@dataclass(slots=True)
class RouterStatusRead(APCI):
    """
    RouterStatusRead service.

    See KNX Specification 03_03_07 Application Layer A_RouterStatus_Read.
    Coupler specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.ROUTER_STATUS_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_RouterStatus_Read is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> RouterStatusRead:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_RouterStatus_Read is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_RouterStatus_Read is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<RouterStatusRead (not implemented) />"


@dataclass(slots=True)
class RouterStatusResponse(APCI):
    """
    RouterStatusResponse service.

    See KNX Specification 03_03_07 Application Layer A_RouterStatus_Response.
    Coupler specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.ROUTER_STATUS_RESPONSE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_RouterStatus_Response is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> RouterStatusResponse:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_RouterStatus_Response is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_RouterStatus_Response is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<RouterStatusResponse (not implemented) />"


@dataclass(slots=True)
class RouterStatusWrite(APCI):
    """
    RouterStatusWrite service.

    See KNX Specification 03_03_07 Application Layer A_RouterStatus_Write.
    Coupler specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.ROUTER_STATUS_WRITE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_RouterStatus_Write is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> RouterStatusWrite:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_RouterStatus_Write is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_RouterStatus_Write is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<RouterStatusWrite (not implemented) />"


@dataclass(slots=True)
class MemoryBitWrite(APCI):
    """
    MemoryBitWrite service.

    See KNX Specification 03_03_07 Application Layer §3.5.5
    A_MemoryBit_Write. Marked "not for future use" by the coupler
    services table, but fully defined - same layout as
    A_UserMemoryBit_Write.

    Payload contains a 1 byte number (octet count of the contiguous
    block to modify, 1-5), a 2 byte memory_address, and_data and
    xor_data - both `number` bytes long. Each result bit is computed as
    (and_data_bit AND block_bit) XOR xor_data_bit, i.e. and_data=0/
    xor_data=0 clears a bit, and_data=0/xor_data=1 sets it, and_data=1/
    xor_data=0 leaves it unmodified and and_data=1/xor_data=1 inverts
    it.
    """

    CODE: ClassVar = APCIExtendedService.MEMORY_BIT_WRITE

    memory_address: int
    and_data: bytes
    xor_data: bytes

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 4 + len(self.and_data) + len(self.xor_data)

    @classmethod
    def from_knx(cls, raw: bytes) -> MemoryBitWrite:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 6:
            raise ConversionError(
                f"Invalid length for A_MemoryBit_Write in CEMI: {raw.hex()}"
            )
        number = raw[2]
        if len(raw) != 5 + 2 * number:
            raise ConversionError(
                f"Invalid length for A_MemoryBit_Write in CEMI: {raw.hex()}"
            )
        memory_address = (raw[3] << 8) | raw[4]
        and_data = raw[5 : 5 + number]
        xor_data = raw[5 + number : 5 + 2 * number]

        return cls(memory_address=memory_address, and_data=and_data, xor_data=xor_data)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.memory_address <= 0xFFFF:
            raise ConversionError("Memory address out of range.")
        number = len(self.and_data)
        if not 0 <= number <= 0xFF:
            raise ConversionError("Number out of range.")
        if len(self.xor_data) != number:
            raise ConversionError("and_data and xor_data must have the same length.")

        payload = (
            struct.pack("!BH", number, self.memory_address)
            + self.and_data
            + self.xor_data
        )

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<MemoryBitWrite memory_address="{hex(self.memory_address)}" '
            f'and_data="{self.and_data.hex()}" xor_data="{self.xor_data.hex()}" />'
        )


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
class KeyWrite(APCI):
    """
    KeyWrite service.

    See KNX Specification 03_03_07 Application Layer §3.5.8 A_Key_Write.
    Modifies (or, with key=0xFFFFFFFF, deletes) the key associated to
    an access level.

    Payload contains a 1 byte level and a 4 byte key.
    """

    CODE: ClassVar = APCIExtendedService.KEY_WRITE

    level: int
    key: int

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 6

    @classmethod
    def from_knx(cls, raw: bytes) -> KeyWrite:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != 7:
            raise ConversionError(
                f"Invalid length for A_Key_Write in CEMI: {raw.hex()}"
            )
        level, key = struct.unpack("!BI", raw[2:])

        return cls(level=level, key=key)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.level <= 0xFF:
            raise ConversionError("Level out of range.")
        if not 0 <= self.key <= 0xFFFFFFFF:
            raise ConversionError("Key out of range.")

        payload = struct.pack("!BI", self.level, self.key)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<KeyWrite level="{self.level}" key="{self.key:#010x}" />'


@dataclass(slots=True)
class KeyResponse(APCI):
    """
    KeyResponse service.

    See KNX Specification 03_03_07 Application Layer §3.5.8
    A_Key_Response (defined alongside A_Key_Write). Contains the access
    level set for the key, or 0xFF if the current access level was
    higher than the level being written.

    Payload contains a 1 byte level.
    """

    CODE: ClassVar = APCIExtendedService.KEY_RESPONSE

    level: int

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        return 2

    @classmethod
    def from_knx(cls, raw: bytes) -> KeyResponse:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != 3:
            raise ConversionError(
                f"Invalid length for A_Key_Response in CEMI: {raw.hex()}"
            )
        (level,) = struct.unpack("!B", raw[2:])

        return cls(level=level)

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= self.level <= 0xFF:
            raise ConversionError("Level out of range.")

        payload = struct.pack("!B", self.level)

        return encode_cmd_and_payload(self.CODE, appended_payload=payload)

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<KeyResponse level="{self.level}" />'


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
class NetworkParameterRead(APCI):
    """
    NetworkParameterRead service.

    See KNX Specification 03_03_07 Application Layer A_NetworkParameter_Read.
    Payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.NETWORK_PARAMETER_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_NetworkParameter_Read is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> NetworkParameterRead:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_NetworkParameter_Read is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_NetworkParameter_Read is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<NetworkParameterRead (not implemented) />"


@dataclass(slots=True)
class NetworkParameterResponse(APCI):
    """
    NetworkParameterResponse service.

    See KNX Specification 03_03_07 Application Layer A_NetworkParameter_Response.
    Payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.NETWORK_PARAMETER_RESPONSE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_NetworkParameter_Response is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> NetworkParameterResponse:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_NetworkParameter_Response is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_NetworkParameter_Response is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<NetworkParameterResponse (not implemented) />"


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
class DomainAddressWrite(APCI):
    """
    DomainAddressWrite service.

    See KNX Specification 03_03_07 Application Layer A_DomainAddress_Write.
    Open media specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.DOMAIN_ADDRESS_WRITE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_DomainAddress_Write is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> DomainAddressWrite:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_DomainAddress_Write is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_DomainAddress_Write is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<DomainAddressWrite (not implemented) />"


@dataclass(slots=True)
class DomainAddressRead(APCI):
    """
    DomainAddressRead service.

    See KNX Specification 03_03_07 Application Layer A_DomainAddress_Read.
    Open media specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.DOMAIN_ADDRESS_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_DomainAddress_Read is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> DomainAddressRead:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_DomainAddress_Read is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_DomainAddress_Read is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<DomainAddressRead (not implemented) />"


@dataclass(slots=True)
class DomainAddressResponse(APCI):
    """
    DomainAddressResponse service.

    See KNX Specification 03_03_07 Application Layer A_DomainAddress_Response.
    Open media specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.DOMAIN_ADDRESS_RESPONSE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_DomainAddress_Response is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> DomainAddressResponse:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_DomainAddress_Response is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_DomainAddress_Response is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<DomainAddressResponse (not implemented) />"


@dataclass(slots=True)
class DomainAddressSelectiveRead(APCI):
    """
    DomainAddressSelectiveRead service.

    See KNX Specification 03_03_07 Application Layer
    A_DomainAddressSelective_Read. Open media specific service - payload
    layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.DOMAIN_ADDRESS_SELECTIVE_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError(
            "A_DomainAddressSelective_Read is not implemented yet."
        )

    @classmethod
    def from_knx(cls, raw: bytes) -> DomainAddressSelectiveRead:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError(
            "A_DomainAddressSelective_Read is not implemented yet."
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError(
            "A_DomainAddressSelective_Read is not implemented yet."
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<DomainAddressSelectiveRead (not implemented) />"


@dataclass(slots=True)
class NetworkParameterWrite(APCI):
    """
    NetworkParameterWrite service.

    See KNX Specification 03_03_07 Application Layer A_NetworkParameter_Write.
    Open media specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.NETWORK_PARAMETER_WRITE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_NetworkParameter_Write is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> NetworkParameterWrite:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_NetworkParameter_Write is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_NetworkParameter_Write is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<NetworkParameterWrite (not implemented) />"


@dataclass(slots=True)
class LinkRead(APCI):
    """
    LinkRead service.

    See KNX Specification 03_03_07 Application Layer A_Link_Read.
    Open media specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.LINK_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_Link_Read is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> LinkRead:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_Link_Read is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_Link_Read is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<LinkRead (not implemented) />"


@dataclass(slots=True)
class LinkResponse(APCI):
    """
    LinkResponse service.

    See KNX Specification 03_03_07 Application Layer A_Link_Response.
    Open media specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.LINK_RESPONSE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_Link_Response is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> LinkResponse:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_Link_Response is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_Link_Response is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<LinkResponse (not implemented) />"


@dataclass(slots=True)
class LinkWrite(APCI):
    """
    LinkWrite service.

    See KNX Specification 03_03_07 Application Layer A_Link_Write.
    Open media specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.LINK_WRITE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_Link_Write is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> LinkWrite:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_Link_Write is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_Link_Write is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<LinkWrite (not implemented) />"


@dataclass(slots=True)
class GroupPropValueRead(APCI):
    """
    GroupPropValueRead service.

    See KNX Specification 03_03_07 Application Layer A_GroupPropValue_Read.
    Open media specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.GROUP_PROP_VALUE_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_GroupPropValue_Read is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> GroupPropValueRead:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_GroupPropValue_Read is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_GroupPropValue_Read is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<GroupPropValueRead (not implemented) />"


@dataclass(slots=True)
class GroupPropValueResponse(APCI):
    """
    GroupPropValueResponse service.

    See KNX Specification 03_03_07 Application Layer A_GroupPropValue_Response.
    Open media specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.GROUP_PROP_VALUE_RESPONSE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_GroupPropValue_Response is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> GroupPropValueResponse:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_GroupPropValue_Response is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_GroupPropValue_Response is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<GroupPropValueResponse (not implemented) />"


@dataclass(slots=True)
class GroupPropValueWrite(APCI):
    """
    GroupPropValueWrite service.

    See KNX Specification 03_03_07 Application Layer A_GroupPropValue_Write.
    Open media specific service - payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.GROUP_PROP_VALUE_WRITE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_GroupPropValue_Write is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> GroupPropValueWrite:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_GroupPropValue_Write is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_GroupPropValue_Write is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<GroupPropValueWrite (not implemented) />"


@dataclass(slots=True)
class GroupPropValueInfoReport(APCI):
    """
    GroupPropValueInfoReport service.

    See KNX Specification 03_03_07 Application Layer
    A_GroupPropValue_InfoReport. Open media specific service - payload
    layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.GROUP_PROP_VALUE_INFO_REPORT

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_GroupPropValue_InfoReport is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> GroupPropValueInfoReport:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_GroupPropValue_InfoReport is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_GroupPropValue_InfoReport is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<GroupPropValueInfoReport (not implemented) />"


@dataclass(slots=True)
class DomainAddressSerialNumberRead(APCI):
    """
    DomainAddressSerialNumberRead service.

    See KNX Specification 03_03_07 Application Layer
    A_DomainAddressSerialNumber_Read. Open media specific service -
    payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.DOMAIN_ADDRESS_SERIAL_NUMBER_READ

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError(
            "A_DomainAddressSerialNumber_Read is not implemented yet."
        )

    @classmethod
    def from_knx(cls, raw: bytes) -> DomainAddressSerialNumberRead:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError(
            "A_DomainAddressSerialNumber_Read is not implemented yet."
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError(
            "A_DomainAddressSerialNumber_Read is not implemented yet."
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<DomainAddressSerialNumberRead (not implemented) />"


@dataclass(slots=True)
class DomainAddressSerialNumberResponse(APCI):
    """
    DomainAddressSerialNumberResponse service.

    See KNX Specification 03_03_07 Application Layer
    A_DomainAddressSerialNumber_Response. Open media specific service -
    payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.DOMAIN_ADDRESS_SERIAL_NUMBER_RESPONSE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError(
            "A_DomainAddressSerialNumber_Response is not implemented yet."
        )

    @classmethod
    def from_knx(cls, raw: bytes) -> DomainAddressSerialNumberResponse:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError(
            "A_DomainAddressSerialNumber_Response is not implemented yet."
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError(
            "A_DomainAddressSerialNumber_Response is not implemented yet."
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<DomainAddressSerialNumberResponse (not implemented) />"


@dataclass(slots=True)
class DomainAddressSerialNumberWrite(APCI):
    """
    DomainAddressSerialNumberWrite service.

    See KNX Specification 03_03_07 Application Layer
    A_DomainAddressSerialNumber_Write. Open media specific service -
    payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.DOMAIN_ADDRESS_SERIAL_NUMBER_WRITE

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError(
            "A_DomainAddressSerialNumber_Write is not implemented yet."
        )

    @classmethod
    def from_knx(cls, raw: bytes) -> DomainAddressSerialNumberWrite:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError(
            "A_DomainAddressSerialNumber_Write is not implemented yet."
        )

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError(
            "A_DomainAddressSerialNumber_Write is not implemented yet."
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<DomainAddressSerialNumberWrite (not implemented) />"


@dataclass(slots=True)
class FileStreamInfoReport(APCI):
    """
    FileStreamInfoReport service.

    See KNX Specification 03_03_07 Application Layer A_FileStream_InfoReport.
    Payload layout not implemented yet.
    """

    CODE: ClassVar = APCIExtendedService.FILE_STREAM_INFO_REPORT

    def calculated_length(self) -> int:
        """Get length of APCI payload."""
        raise NotImplementedError("A_FileStream_InfoReport is not implemented yet.")

    @classmethod
    def from_knx(cls, raw: bytes) -> FileStreamInfoReport:
        """Parse/deserialize from KNX/IP raw data."""
        raise NotImplementedError("A_FileStream_InfoReport is not implemented yet.")

    def to_knx(self) -> bytearray:
        """Serialize to KNX/IP raw data."""
        raise NotImplementedError("A_FileStream_InfoReport is not implemented yet.")

    def __str__(self) -> str:
        """Return object as readable string."""
        return "<FileStreamInfoReport (not implemented) />"


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
