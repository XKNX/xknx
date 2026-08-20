"""Module for XKXN Exceptions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from xknx.knxip import ErrorCode


class XKNXException(Exception):
    """Default XKNX Exception."""

    def __eq__(self, other: object | None) -> bool:
        """Equal operator."""
        return repr(self) == repr(other)

    def __hash__(self) -> int:
        """Hash function."""
        return hash(str(self))

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)


class CommunicationError(XKNXException):
    """Unable to communicate with KNX bus."""

    def __init__(self, message: str, should_log: bool = True) -> None:
        """Instantiate exception."""
        super().__init__(message)

        self.should_log = should_log


class ConfirmationError(CommunicationError):
    """No confirmation received from KNX server for sent Telegram."""


class TunnellingAckError(CommunicationError):
    """No ACK or error status received from UDP KNX server for sent Telegram."""


class IPSecureError(CommunicationError):
    """Error in IP Secure communication."""


class RequestResponseError(CommunicationError):
    """A KNXnet/IP request was not answered, or answered with an error status."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode | None = None,
        should_log: bool = True,
    ) -> None:
        """Instantiate exception. `error_code` is None when no response arrived."""
        super().__init__(message, should_log)

        self.error_code = error_code


class CouldNotParseTelegram(XKNXException):
    """Could not parse telegram error."""

    def __init__(self, description: str, **kwargs: Any) -> None:
        """Initialize CouldNotParseTelegram class."""
        super().__init__()
        self.description = description
        self.parameter = kwargs

    def _format_parameter(self) -> str:
        return " ".join(
            [f"{key}={value!r}" for (key, value) in sorted(self.parameter.items())]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<CouldNotParseTelegram "
            f'description="{self.description}" {self._format_parameter()}/>'
        )


class CouldNotParseKNXIP(XKNXException):
    """Exception class for wrong KNXIP data."""

    def __init__(self, description: str = "") -> None:
        """Initialize CouldNotParseKNXIP class."""
        super().__init__()
        self.description = description

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<CouldNotParseKNXIP description="{self.description}" />'


class KNXSecureValidationError(CouldNotParseKNXIP):
    """Exception class for invalid KNX Secure data."""

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<KNXSecureValidationError description="{self.description}" />'


class IncompleteKNXIPFrame(CouldNotParseKNXIP):
    """
    Exception class for incomplete KNXIP data.

    Used for TCP connections to indicate to buffer the data until the complete frame is received.
    UDP connections should just handle CouldNotParseKNXIP.
    """

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<IncompleteKNXIPFrame description="{self.description}" />'


class CouldNotParseCEMI(XKNXException):
    """Exception class for wrong CEMI data."""

    def __init__(self, description: str = "") -> None:
        """Initialize CouldNotParseCEMI class."""
        super().__init__()
        self.description = description

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<CouldNotParseCEMI description="{self.description}" />'


class UnsupportedCEMIMessage(XKNXException):
    """Exception class for unsupported CEMI Messages."""

    def __init__(self, description: str = "") -> None:
        """Initialize UnsupportedCEMIMessage class."""
        super().__init__()
        self.description = description

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<UnsupportedCEMIMessage description="{self.description}" />'


class ConversionError(XKNXException):
    """Exception class for error while converting one type to another."""

    def __init__(self, description: str, **kwargs: Any) -> None:
        """Initialize ConversionError class."""
        super().__init__()
        self.description = description
        self.parameter = kwargs

    def _format_parameter(self) -> str:
        return " ".join(
            [f"{key}={value!r}" for (key, value) in sorted(self.parameter.items())]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<ConversionError description="{self.description}" {self._format_parameter()}/>'


class UnsupportedAPCIService(ConversionError):
    """
    Exception for a valid but not defined or not implemented APCI service.

    Subclass of `ConversionError` so existing handlers keep catching it, while
    allowing the CEMI layer to tell an unsupported service (benign, to be
    ignored per KNX v02.01.01 - Application Layer 03.03.07 - §2.2) apart
    from a malformed/truncated APDU.
    """

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<UnsupportedAPCIService description="{self.description}" {self._format_parameter()}/>'


class CouldNotParseAddress(XKNXException):
    """Exception class for wrong address format."""

    def __init__(self, address: Any = None, message: str = "") -> None:
        """Initialize CouldNotParseAddress class."""
        super().__init__()
        self.address = address
        self.message = message

    def __str__(self) -> str:
        """Return object as readable string."""
        _msg = f'message="{self.message}" ' if self.message else ""
        return f"<CouldNotParseAddress address={self.address!r} {_msg}/>"


class DeviceIllegalValue(XKNXException):
    """Exception class for setting a value of a device with an illegal value."""

    def __init__(self, description: str, value: Any) -> None:
        """Initialize DeviceIllegalValue class."""
        super().__init__()
        self.value = value
        self.description = description

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<DeviceIllegalValue description="{self.description}" value={self.value!r} />'


class DataSecureError(XKNXException):
    """Exception class for KNX Data Secure handling."""

    def __init__(self, message: str, log_level: int = logging.WARNING) -> None:
        """Instantiate exception."""
        super().__init__(message)
        self.log_level = log_level


class InvalidSecureConfiguration(XKNXException):
    """Exception class used when the secure configuration is invalid."""


class ManagementConnectionError(XKNXException):
    """Exception class used when a management connection fails."""


class ManagementConnectionRefused(ManagementConnectionError):
    """Exception class used when a management connection request is refused."""


class ManagementConnectionTimeout(ManagementConnectionError):
    """Exception class used when a management connection timed out."""
