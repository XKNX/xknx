"""Unit test for KNX scene number."""
import pytest

from xknx.dpt import DPTArray, DPTSceneNumber
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTSceneNumber:
    """Test class for KNX scaling value."""

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            ((0x31,), 50),
            ((0x3F,), 64),
            ((0x00,), 1),
        ],
    )
    def test_transcoder(self, raw, value):
        """Test parsing and streaming of DPTSceneNumber."""
        assert DPTSceneNumber.to_knx(value) == DPTArray(raw)
        assert DPTSceneNumber.from_knx(DPTArray(raw)) == value

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTSceneNumber with wrong value (underflow)."""
        with pytest.raises(ConversionError):
            DPTSceneNumber.to_knx(DPTSceneNumber.value_min - 1)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTSceneNumber with wrong value (overflow)."""
        with pytest.raises(ConversionError):
            DPTSceneNumber.to_knx(DPTSceneNumber.value_max + 1)

    def test_to_knx_wrong_parameter(self):
        """Test parsing of DPTSceneNumber with wrong value (string)."""
        with pytest.raises(ConversionError):
            DPTSceneNumber.to_knx("fnord")

    def test_from_knx_wrong_parameter(self):
        """Test parsing of DPTSceneNumber with wrong value (3 byte array)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTSceneNumber.from_knx(DPTArray((0x01, 0x02, 0x03)))

    def test_from_knx_wrong_value(self):
        """Test parsing of DPTSceneNumber with value which exceeds limits."""
        with pytest.raises(ConversionError):
            DPTSceneNumber.from_knx(DPTArray((0x64,)))
