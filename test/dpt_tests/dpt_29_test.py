"""Unit test for KNX 8 byte signed objects."""

import pytest

from xknx.dpt import DPT8ByteSigned, DPTArray
from xknx.exceptions import ConversionError


class TestDPT8ByteSigned:
    """Test class for KNX 8 byte signed objects."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        (
            (b"\x00\x00\x00\x00\x00\x00\x00\x00", 0),
            (b"\x00\x00\x00\x00\x00\x00\x00\x01", 1),
            (b"\x00\x00\x00\x00\x00\x00\x00\xe6", 230),
            (b"\xff\xff\xff\xff\xff\xff\xff\x1a", -230),
            # limits
            (b"\x7f\xff\xff\xff\xff\xff\xff\xff", 9_223_372_036_854_775_807),
            (b"\x80\x00\x00\x00\x00\x00\x00\x00", -9_223_372_036_854_775_808),
        ),
    )
    def test_values(self, raw, expected):
        """Test valid values."""
        assert DPT8ByteSigned.to_knx(expected) == DPTArray(raw)
        assert DPT8ByteSigned.from_knx(DPTArray(raw)) == expected

    @pytest.mark.parametrize(
        "value", (9_223_372_036_854_775_808, -9_223_372_036_854_775_809)
    )
    def test_exceeding_limits(self, value):
        """Test invalid values."""
        with pytest.raises(ConversionError):
            DPT8ByteSigned.to_knx(value)
