"""Unit test for KNX 2 byte signed objects."""
import struct
from unittest.mock import patch

import pytest

from xknx.dpt import DPT2ByteSigned, DPTArray
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPT2ByteSigned:
    """Test class for KNX 2 byte signed objects."""

    def test_signed_settings(self):
        """Test members of DPT2ByteSigned."""
        assert DPT2ByteSigned.value_min == -32768
        assert DPT2ByteSigned.value_max == 32767

    def test_signed_assert_min_exceeded(self):
        """Test initialization of DPT2ByteSigned with wrong value (Underflow)."""
        with pytest.raises(ConversionError):
            DPT2ByteSigned.to_knx(-32769)

    def test_signed_to_knx_exceed_limits(self):
        """Test initialization of DPT2ByteSigned with wrong value (Overflow)."""
        with pytest.raises(ConversionError):
            DPT2ByteSigned.to_knx(32768)

    def test_signed_value_max_value(self):
        """Test DPT2ByteSigned parsing and streaming."""
        assert DPT2ByteSigned.to_knx(32767) == DPTArray((0x7F, 0xFF))
        assert DPT2ByteSigned.from_knx(DPTArray((0x7F, 0xFF))) == 32767

    def test_signed_value_min_value(self):
        """Test DPT2ByteSigned parsing and streaming with null values."""
        assert DPT2ByteSigned.to_knx(-20480) == DPTArray((0xB0, 0x00))
        assert DPT2ByteSigned.from_knx(DPTArray((0xB0, 0x00))) == -20480

    def test_signed_value_0123(self):
        """Test DPT2ByteSigned parsing and streaming."""
        assert DPT2ByteSigned.to_knx(291) == DPTArray((0x01, 0x23))
        assert DPT2ByteSigned.from_knx(DPTArray((0x01, 0x23))) == 291

    def test_signed_wrong_value_from_knx(self):
        """Test DPT2ByteSigned parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPT2ByteSigned.from_knx(DPTArray((0xFF, 0x4E, 0x12)))

    def test_from_knx_unpack_error(self):
        """Test DPT2ByteSigned parsing with unpack error."""
        with patch("struct.unpack") as unpack_mock:
            unpack_mock.side_effect = struct.error()
            with pytest.raises(ConversionError):
                DPT2ByteSigned.from_knx(DPTArray((0x01, 0x23)))

    def test_to_knx_pack_error(self):
        """Test serializing DPT2ByteSigned with pack error."""
        with patch("struct.pack") as pack_mock:
            pack_mock.side_effect = struct.error()
            with pytest.raises(ConversionError):
                DPT2ByteSigned.to_knx(1234)
