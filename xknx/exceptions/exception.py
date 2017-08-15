"""Module for XKXN Exceptions."""


class XKNXException(Exception):
    """Default XKNX Exception."""

    pass


class CouldNotParseTelegram(XKNXException):
    """Could not parse telegram error."""

    def __init__(self, description=""):
        """Initialize CouldNotParseTelegram class."""
        super(CouldNotParseTelegram, self).__init__("Could not parse Telegram")
        self.description = description

    def __str__(self):
        """Return object as readable string."""
        return '<CouldNotParseTelegram description="{0}" />' \
            .format(self.description)


class CouldNotParseKNXIP(XKNXException):
    """Exception falss for worong KNXIP data."""

    def __init__(self, description=""):
        """Initialize CouldNotParseTelegram class."""
        super(CouldNotParseKNXIP, self).__init__("Could not parse KNXIP")
        self.description = description

    def __str__(self):
        """Return object as readable string."""
        return '<CouldNotParseKNXIP description="{0}" />' \
            .format(self.description)


class ConversionError(XKNXException):
    """Exception class for error while converting one type to another."""

    def __init__(self, i):
        """Initialize ConversionError class."""
        super(ConversionError, self).__init__("Conversion Error")
        self.i = i

    def __str__(self):
        """Return object as readable string."""
        return '<ConversionError input="{0}" />'.format(self.i)


class CouldNotParseAddress(XKNXException):
    """Exception class for wrong address format."""

    def __init__(self, address=None):
        """Initialize CouldNotParseAddress class."""
        super(CouldNotParseAddress, self).__init__("Could not parse address")
        self.address = address

    def __str__(self):
        """Return object as readable string."""
        return '<CouldNotParseAddress address="{0}" />'.format(self.address)
