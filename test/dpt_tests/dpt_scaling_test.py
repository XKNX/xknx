"""Unit test for KNX DPT 5.001 and 5.003 value."""
import pytest

from xknx.dpt import DPTAngle, DPTArray, DPTScaling
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTScaling:
    """Test class for KNX scaling value."""

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            ((0x4C,), 30),
            ((0xFC,), 99),
            ((0xFF,), 100),
            ((0x00,), 0),
        ],
    )
    def test_transcoder(self, raw, value):
        """Test parsing and streaming of DPTScaling."""
        assert DPTScaling.to_knx(value) == DPTArray(raw)
        assert DPTScaling.from_knx(DPTArray(raw)) == value

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTScaling with wrong value (underflow)."""
        with pytest.raises(ConversionError):
            DPTScaling.to_knx(-1)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTScaling with wrong value (overflow)."""
        with pytest.raises(ConversionError):
            DPTScaling.to_knx(101)

    def test_to_knx_wrong_parameter(self):
        """Test parsing of DPTScaling with wrong value (string)."""
        with pytest.raises(ConversionError):
            DPTScaling.to_knx("fnord")

    def test_from_knx_wrong_parameter(self):
        """Test parsing of DPTScaling with wrong value (3 byte array)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTScaling.from_knx(DPTArray((0x01, 0x02, 0x03)))

    def test_from_knx_wrong_value(self):
        """Test parsing of DPTScaling with value which exceeds limits."""
        with pytest.raises(ConversionError):
            DPTScaling.from_knx(DPTArray((0x256,)))


class TestDPTAngle:
    """Test class for KNX scaling value."""

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            ((0x15,), 30),
            ((0xBF,), 270),
            ((0xFF,), 360),
            ((0x00,), 0),
        ],
    )
    def test_transcoder(self, raw, value):
        """Test parsing and streaming of DPTAngle."""
        assert DPTAngle.to_knx(value) == DPTArray(raw)
        assert DPTAngle.from_knx(DPTArray(raw)) == value

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTAngle with wrong value (underflow)."""
        with pytest.raises(ConversionError):
            DPTAngle.to_knx(-1)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTAngle with wrong value (overflow)."""
        with pytest.raises(ConversionError):
            DPTAngle.to_knx(361)
