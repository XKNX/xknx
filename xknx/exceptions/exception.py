"""Module for XKXN Exceptions."""
from typing import Any, Optional, Tuple, Union


class XKNXException(Exception):
    """Default XKNX Exception."""

    def __eq__(self, other: Optional[object]) -> bool:
        """Equal operator."""
        return repr(self) == repr(other)

    def __hash__(self) -> int:
        """Hash function."""
        return hash(str(self))

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)


class CommunicationError(XKNXException):
    """Unable to communicate with KNX Bus."""

    def __init__(self, message: str, should_log: bool = True) -> None:
        """Instantiate exception."""
        super().__init__(message)

        self.should_log = should_log


class CouldNotParseTelegram(XKNXException):
    """Could not parse telegram error."""

    def __init__(self, description: str, **kwargs: Any) -> None:
        """Initialize CouldNotParseTelegram class."""
        super().__init__()
        self.description = description
        self.parameter = kwargs

    def _format_parameter(self) -> str:
        return " ".join(
            [f'{key}="{value}"' for (key, value) in sorted(self.parameter.items())]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return '<CouldNotParseTelegram description="{}" {}/>'.format(
            self.description, self._format_parameter()
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
            [f'{key}="{value}"' for (key, value) in sorted(self.parameter.items())]
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<ConversionError description="{self.description}" {self._format_parameter()}/>'


class CouldNotParseAddress(XKNXException):
    """Exception class for wrong address format."""

    def __init__(
        self, address: Union[object, str, Tuple[Any, ...], int, None] = None
    ) -> None:
        """Initialize CouldNotParseAddress class."""
        super().__init__()
        self.address = address

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<CouldNotParseAddress address="{self.address}" />'


class DeviceIllegalValue(XKNXException):
    """Exception class for setting a value of a device with an illegal value."""

    def __init__(self, value: Any, description: str) -> None:
        """Initialize DeviceIllegalValue class."""
        super().__init__()
        self.value = value
        self.description = description

    def __str__(self) -> str:
        """Return object as readable string."""
        return '<DeviceIllegalValue description="{}" value="{}" />'.format(
            self.value, self.description
        )
