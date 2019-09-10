"""Module for XKXN Exceptions."""


class XKNXException(Exception):
    """Default XKNX Exception."""

    def __eq__(self, other):
        """Equal operator."""
        return repr(self) == repr(other)

    def __hash__(self):
        """Hash function."""
        return hash(str(self))

    def __repr__(self):
        """Representation of object."""
        return str(self)


class CouldNotParseTelegram(XKNXException):
    """Could not parse telegram error."""

    def __init__(self, description, **kwargs):
        """Initialize CouldNotParseTelegram class."""
        super().__init__()
        self.description = description
        self.parameter = kwargs

    def _format_parameter(self):
        return " ".join(['%s="%s"' % (key, value) for (key, value) in sorted(self.parameter.items())])

    def __str__(self):
        """Return object as readable string."""
        return '<CouldNotParseTelegram description="{0}" {1}/>' \
            .format(self.description, self._format_parameter())


class CouldNotParseKNXIP(XKNXException):
    """Exception class for wrong KNXIP data."""

    def __init__(self, description=""):
        """Initialize CouldNotParseTelegram class."""
        super().__init__()
        self.description = description

    def __str__(self):
        """Return object as readable string."""
        return '<CouldNotParseKNXIP description="{0}" />' \
            .format(self.description)


class ConversionError(XKNXException):
    """Exception class for error while converting one type to another."""

    def __init__(self, description, **kwargs):
        """Initialize ConversionError class."""
        super().__init__()
        self.description = description
        self.parameter = kwargs

    def _format_parameter(self):
        return " ".join(['%s="%s"' % (key, value) for (key, value) in sorted(self.parameter.items())])

    def __str__(self):
        """Return object as readable string."""
        return '<ConversionError description="{0}" {1}/>'.format(self.description, self._format_parameter())


class CouldNotParseAddress(XKNXException):
    """Exception class for wrong address format."""

    def __init__(self, address=None):
        """Initialize CouldNotParseAddress class."""
        super().__init__()
        self.address = address

    def __str__(self):
        """Return object as readable string."""
        return '<CouldNotParseAddress address="{0}" />'.format(self.address)


class DeviceIllegalValue(XKNXException):
    """Exception class for setting a value of a device with an illegal value."""

    def __init__(self, value, description):
        """Initialize DeviceIllegalValue class."""
        super().__init__()
        self.value = value
        self.description = description

    def __str__(self):
        """Return object as readable string."""
        return '<DeviceIllegalValue description="{0}" value="{1}" />'.format(
            self.value,
            self.description)
