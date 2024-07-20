"""Unit test for KNX DPT 1."""

import pytest

from xknx.dpt import DPTArray, DPTBinary
from xknx.dpt.dpt_1 import DPTHeatCool, DPTStep, DPTUpDown, HeatCool, Step, UpDown
from xknx.exceptions import ConversionError, CouldNotParseTelegram


@pytest.mark.parametrize(
    ("dpt", "value_false", "value_true"),
    [
        (DPTStep, Step.DECREASE, Step.INCREASE),
        (DPTUpDown, UpDown.UP, UpDown.DOWN),
        (DPTHeatCool, HeatCool.COOL, HeatCool.HEAT),
    ],
)
class TestDPT1:
    """Test class for KNX DPT 1 values."""

    def test_to_knx(self, dpt, value_true, value_false):
        """Test parsing to KNX."""
        assert dpt.to_knx(value_true) == DPTBinary(1)
        assert dpt.to_knx(value_false) == DPTBinary(0)

    def test_to_knx_by_string(self, dpt, value_true, value_false):
        """Test parsing string values to KNX."""
        assert dpt.to_knx(value_true.name.lower()) == DPTBinary(1)
        assert dpt.to_knx(value_false.name.lower()) == DPTBinary(0)

    def test_to_knx_by_value(self, dpt, value_true, value_false):
        """Test parsing string values to KNX."""
        assert dpt.to_knx(True) == DPTBinary(1)
        assert dpt.to_knx(1) == DPTBinary(1)
        assert dpt.to_knx(False) == DPTBinary(0)
        assert dpt.to_knx(0) == DPTBinary(0)

    def test_to_knx_wrong_value(self, dpt, value_true, value_false):
        """Test serializing to KNX with wrong value."""
        with pytest.raises(ConversionError):
            dpt.to_knx(2)

    def test_from_knx(self, dpt, value_true, value_false):
        """Test parsing from KNX."""
        assert dpt.from_knx(DPTBinary(0)) == value_false
        assert dpt.from_knx(DPTBinary(1)) == value_true

    def test_from_knx_wrong_value(self, dpt, value_true, value_false):
        """Test parsing with wrong value)."""
        with pytest.raises(CouldNotParseTelegram):
            dpt.from_knx(DPTArray((1,)))
        with pytest.raises(CouldNotParseTelegram):
            dpt.from_knx(DPTBinary(2))
