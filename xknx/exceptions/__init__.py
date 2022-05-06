"""Module for XKNX Exception handling."""
# flake8: noqa
from .exception import (
    CommunicationError,
    ConversionError,
    CouldNotParseAddress,
    CouldNotParseKNXIP,
    CouldNotParseTelegram,
    DeviceIllegalValue,
    IncompleteKNXIPFrame,
    InterfaceWithUserIdNotFound,
    InvalidSecureConfiguration,
    InvalidSignature,
    KNXSecureValidationError,
    SecureException,
    UnsupportedCEMIMessage,
    XKNXException,
)

__all__ = [
    "CommunicationError",
    "ConversionError",
    "CouldNotParseAddress",
    "CouldNotParseKNXIP",
    "CouldNotParseTelegram",
    "DeviceIllegalValue",
    "IncompleteKNXIPFrame",
    "InterfaceWithUserIdNotFound",
    "InvalidSecureConfiguration",
    "InvalidSignature",
    "KNXSecureValidationError",
    "SecureException",
    "UnsupportedCEMIMessage",
    "XKNXException",
]
