"""Module for KNX helper functions."""

from xknx.exceptions import ConversionError


def test_bytesarray(raw, length):
    """Test if array of raw bytes has the correct length and values of correct type."""
    if not isinstance(raw, (tuple, list)) \
            or len(raw) != length \
            or any(not isinstance(byte, int) for byte in raw) \
            or any(byte < 0 for byte in raw) \
            or any(byte > 255 for byte in raw):
        raise ConversionError("Invalid raw bytes", raw=raw)
