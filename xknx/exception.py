"""
Module for XKXN Exceptions.
"""

class XKNXException(Exception):
    """Default XKNX Exception."""

    pass


class CouldNotParseTelegram(XKNXException):
    """Could not parse telegram error."""

    pass
