"""Module for XKNX Exception handling."""
# flake8: noqa
from .exception import (
    CommunicationError,
    ConfirmationError,
    ConversionError,
    CouldNotParseAddress,
    CouldNotParseCEMI,
    CouldNotParseKNXIP,
    CouldNotParseTelegram,
    DataSecureError,
    DeviceIllegalValue,
    IncompleteKNXIPFrame,
    InvalidSecureConfiguration,
    KNXSecureValidationError,
    ManagementConnectionError,
    ManagementConnectionRefused,
    ManagementConnectionTimeout,
    ManagementConnectionWriteAddressError,
    SecureException,
    TunnellingAckError,
    UnsupportedCEMIMessage,
    XKNXException,
)

__all__ = [
    "CommunicationError",
    "ConfirmationError",
    "ConversionError",
    "CouldNotParseAddress",
    "CouldNotParseCEMI",
    "CouldNotParseKNXIP",
    "CouldNotParseTelegram",
    "DataSecureError",
    "DeviceIllegalValue",
    "ManagementConnectionError",
    "ManagementConnectionRefused",
    "ManagementConnectionTimeout",
    "ManagementConnectionWriteAddressError",
    "IncompleteKNXIPFrame",
    "InvalidSecureConfiguration",
    "KNXSecureValidationError",
    "SecureException",
    "TunnellingAckError",
    "UnsupportedCEMIMessage",
    "XKNXException",
]
