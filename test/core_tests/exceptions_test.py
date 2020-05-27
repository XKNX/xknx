"""Unit tests for exceptions"""
import pytest

from xknx.exceptions import (
    ConversionError, CouldNotParseAddress, CouldNotParseKNXIP,
    CouldNotParseTelegram, DeviceIllegalValue, XKNXException)


@pytest.mark.parametrize(
    "base,equal,diff",
    [
        (
            ConversionError("desc1"),
            ConversionError("desc1"),
            ConversionError("desc2"),
        ),
        (
            CouldNotParseAddress(123),
            CouldNotParseAddress(123),
            CouldNotParseAddress(321),
        ),
        (
            CouldNotParseKNXIP("desc1"),
            CouldNotParseKNXIP("desc1"),
            CouldNotParseKNXIP("desc2"),
        ),
        (
            CouldNotParseTelegram("desc", arg1=1, arg2=2),
            CouldNotParseTelegram("desc", arg1=1, arg2=2),
            CouldNotParseTelegram("desc", arg1=2, arg2=1),
        ),
        (
            DeviceIllegalValue("value1", "desc"),
            DeviceIllegalValue("value1", "desc"),
            DeviceIllegalValue("value1", "desc2"),
        ),
        (
            XKNXException("desc1"),
            XKNXException("desc1"),
            XKNXException("desc2"),
        ),
    ],
)
def test_exceptions(base, equal, diff):
    """Test hashability and repr of exceptions."""
    assert hash(base) == hash(equal)
    assert hash(base) != hash(diff)
    assert base == equal
    assert base != diff
    assert repr(base) == repr(equal)
    assert repr(base) != repr(diff)
