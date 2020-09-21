"""Module for XKNX Exception handling."""
# flake8: noqa
from .exception import (
    CommunicationError,
    ConversionError,
    CouldNotParseAddress,
    CouldNotParseKNXIP,
    CouldNotParseTelegram,
    DeviceIllegalValue,
    UnsupportedCEMIMessage,
    XKNXException,
)
