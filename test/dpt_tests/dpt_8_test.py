"""Unit test for KNX 2 byte signed objects."""

import struct
from unittest.mock import patch

import pytest

from xknx.dpt import DPT2ByteSigned, DPTArray, DPTDeltaTime10Msec, DPTPercentV16
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPT2ByteSigned:
    """Test class for KNX 2 byte signed objects."""

    def test_signed_settings(self) -> None:
        """Test members of DPT2ByteSigned."""
        assert DPT2ByteSigned.value_min == -32768
        assert DPT2ByteSigned.value_max == 32767

    def test_signed_assert_min_exceeded(self) -> None:
        """Test initialization of DPT2ByteSigned with wrong value (Underflow)."""
        with pytest.raises(ConversionError):
            DPT2ByteSigned.to_knx(-32769)

    def test_signed_to_knx_exceed_limits(self) -> None:
        """Test initialization of DPT2ByteSigned with wrong value (Overflow)."""
        with pytest.raises(ConversionError):
            DPT2ByteSigned.to_knx(32768)

    def test_signed_value_max_value(self) -> None:
        """Test DPT2ByteSigned parsing and streaming."""
        assert DPT2ByteSigned.to_knx(32767) == DPTArray((0x7F, 0xFF))
        assert DPT2ByteSigned.from_knx(DPTArray((0x7F, 0xFF))) == 32767

    def test_signed_value_min_value(self) -> None:
        """Test DPT2ByteSigned parsing and streaming with null values."""
        assert DPT2ByteSigned.to_knx(-20480) == DPTArray((0xB0, 0x00))
        assert DPT2ByteSigned.from_knx(DPTArray((0xB0, 0x00))) == -20480

    def test_signed_value_0123(self) -> None:
        """Test DPT2ByteSigned parsing and streaming."""
        assert DPT2ByteSigned.to_knx(291) == DPTArray((0x01, 0x23))
        assert DPT2ByteSigned.from_knx(DPTArray((0x01, 0x23))) == 291

    def test_signed_wrong_value_from_knx(self) -> None:
        """Test DPT2ByteSigned parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPT2ByteSigned.from_knx(DPTArray((0xFF, 0x4E, 0x12)))

    def test_from_knx_unpack_error(self) -> None:
        """Test DPT2ByteSigned parsing with unpack error."""
        with patch("struct.unpack") as unpack_mock:
            unpack_mock.side_effect = struct.error()
            with pytest.raises(ConversionError):
                DPT2ByteSigned.from_knx(DPTArray((0x01, 0x23)))

    def test_to_knx_pack_error(self) -> None:
        """Test serializing DPT2ByteSigned with pack error."""
        with patch("struct.pack") as pack_mock:
            pack_mock.side_effect = struct.error()
            with pytest.raises(ConversionError):
                DPT2ByteSigned.to_knx(1234)

    def test_to_knx_rounding(self) -> None:
        """Test values are rounded to the resolution instead of truncated."""
        # 0.29 / 0.01 == 28.999999999999996 - int() would give 28
        assert DPTPercentV16.to_knx(0.29) == DPTArray((0x00, 0x1D))
        assert DPTPercentV16.to_knx(-0.29) == DPTArray((0xFF, 0xE3))
        assert DPTPercentV16.from_knx(DPTArray((0x00, 0x1D))) == 0.29
        assert DPTDeltaTime10Msec.to_knx(19) == DPTArray((0x00, 0x02))
        assert DPTDeltaTime10Msec.to_knx(-19) == DPTArray((0xFF, 0xFE))
        assert DPTDeltaTime10Msec.to_knx(327_674) == DPTArray((0x7F, 0xFF))
        with pytest.raises(ConversionError):
            DPTDeltaTime10Msec.to_knx(327_676)
