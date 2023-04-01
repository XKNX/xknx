"""Unit test for KNX 4 byte objects."""
import struct
from unittest.mock import patch

import pytest

from xknx.dpt import DPT4ByteSigned, DPT4ByteUnsigned, DPTArray
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPT4Byte:
    """Test class for KNX 4 byte objects."""

    # ####################################################################
    # DPT4ByteUnsigned
    #
    def test_unsigned_settings(self):
        """Test members of DPT4ByteUnsigned."""
        assert DPT4ByteUnsigned.value_min == 0
        assert DPT4ByteUnsigned.value_max == 4294967295

    def test_unsigned_assert_min_exceeded(self):
        """Test initialization of DPT4ByteUnsigned with wrong value (Underflow)."""
        with pytest.raises(ConversionError):
            DPT4ByteUnsigned.to_knx(-1)

    def test_unsigned_to_knx_exceed_limits(self):
        """Test initialization of DPT4ByteUnsigned with wrong value (Overflow)."""
        with pytest.raises(ConversionError):
            DPT4ByteUnsigned.to_knx(4294967296)

    def test_unsigned_value_max_value(self):
        """Test DPT4ByteUnsigned parsing and streaming."""
        assert DPT4ByteUnsigned.to_knx(4294967295) == DPTArray((0xFF, 0xFF, 0xFF, 0xFF))
        assert (
            DPT4ByteUnsigned.from_knx(DPTArray((0xFF, 0xFF, 0xFF, 0xFF))) == 4294967295
        )

    def test_unsigned_value_min_value(self):
        """Test parsing and streaming with null values."""
        assert DPT4ByteUnsigned.to_knx(0) == DPTArray((0x00, 0x00, 0x00, 0x00))
        assert DPT4ByteUnsigned.from_knx(DPTArray((0x00, 0x00, 0x00, 0x00))) == 0

    def test_unsigned_value_01234567(self):
        """Test DPT4ByteUnsigned parsing and streaming."""
        assert DPT4ByteUnsigned.to_knx(19088743) == DPTArray((0x01, 0x23, 0x45, 0x67))
        assert DPT4ByteUnsigned.from_knx(DPTArray((0x01, 0x23, 0x45, 0x67))) == 19088743

    def test_unsigned_wrong_value_from_knx(self):
        """Test DPT4ByteUnsigned parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPT4ByteUnsigned.from_knx(DPTArray((0xFF, 0x4E, 0x12)))

    # ####################################################################
    # DPT4ByteSigned
    #
    def test_signed_settings(self):
        """Test members of DPT4ByteSigned."""
        assert DPT4ByteSigned.value_min == -2147483648
        assert DPT4ByteSigned.value_max == 2147483647

    def test_signed_assert_min_exceeded(self):
        """Test initialization of DPT4ByteSigned with wrong value (Underflow)."""
        with pytest.raises(ConversionError):
            DPT4ByteSigned.to_knx(-2147483649)

    def test_signed_to_knx_exceed_limits(self):
        """Test initialization of DPT4ByteSigned with wrong value (Overflow)."""
        with pytest.raises(ConversionError):
            DPT4ByteSigned.to_knx(2147483648)

    def test_signed_value_max_value(self):
        """Test DPT4ByteSigned parsing and streaming."""
        assert DPT4ByteSigned.to_knx(2147483647) == DPTArray((0x7F, 0xFF, 0xFF, 0xFF))
        assert DPT4ByteSigned.from_knx(DPTArray((0x7F, 0xFF, 0xFF, 0xFF))) == 2147483647

    def test_signed_value_min_value(self):
        """Test DPT4ByteSigned parsing and streaming with null values."""
        assert DPT4ByteSigned.to_knx(-2147483648) == DPTArray((0x80, 0x00, 0x00, 0x00))
        assert (
            DPT4ByteSigned.from_knx(DPTArray((0x80, 0x00, 0x00, 0x00))) == -2147483648
        )

    def test_signed_value_01234567(self):
        """Test DPT4ByteSigned parsing and streaming."""
        assert DPT4ByteSigned.to_knx(19088743) == DPTArray((0x01, 0x23, 0x45, 0x67))
        assert DPT4ByteSigned.from_knx(DPTArray((0x01, 0x23, 0x45, 0x67))) == 19088743

    def test_signed_wrong_value_from_knx(self):
        """Test DPT4ByteSigned parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPT4ByteSigned.from_knx(DPTArray((0xFF, 0x4E, 0x12)))

    def test_from_knx_unpack_error(self):
        """Test DPT4ByteSigned parsing with unpack error."""
        with patch("struct.unpack") as unpack_mock:
            unpack_mock.side_effect = struct.error()
            with pytest.raises(ConversionError):
                DPT4ByteSigned.from_knx(DPTArray((0x01, 0x23, 0x45, 0x67)))

    def test_to_knx_pack_error(self):
        """Test serializing DPT4ByteSigned with pack error."""
        with patch("struct.pack") as pack_mock:
            pack_mock.side_effect = struct.error()
            with pytest.raises(ConversionError):
                DPT4ByteSigned.to_knx(19088743)
