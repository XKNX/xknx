"""Unit test for KNX DPT 1."""

import pytest

from xknx.dpt import DPTArray, DPTBinary
from xknx.dpt.dpt_1 import DPTHeatCool, HeatCool
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTHeatCool:
    """Test class for KNX DPT HVAC Operation modes."""

    def test_to_knx(self):
        """Test parsing to KNX."""
        assert DPTHeatCool.to_knx(HeatCool.HEAT) == DPTBinary(1)
        assert DPTHeatCool.to_knx(HeatCool.COOL) == DPTBinary(0)

    def test_to_knx_by_string(self):
        """Test parsing string values to KNX."""
        assert DPTHeatCool.to_knx("heat") == DPTBinary(1)
        assert DPTHeatCool.to_knx("cool") == DPTBinary(0)

    def test_to_knx_by_value(self):
        """Test parsing string values to KNX."""
        assert DPTHeatCool.to_knx(True) == DPTBinary(1)
        assert DPTHeatCool.to_knx(1) == DPTBinary(1)
        assert DPTHeatCool.to_knx(False) == DPTBinary(0)
        assert DPTHeatCool.to_knx(0) == DPTBinary(0)

    def test_to_knx_wrong_value(self):
        """Test serializing to KNX with wrong value."""
        with pytest.raises(ConversionError):
            DPTHeatCool.to_knx(2)

    def test_mode_from_knx(self):
        """Test parsing DPTHVACMode from KNX."""
        assert DPTHeatCool.from_knx(DPTBinary(0)) == HeatCool.COOL
        assert DPTHeatCool.from_knx(DPTBinary(1)) == HeatCool.HEAT

    def test_mode_from_knx_wrong_value(self):
        """Test parsing of DPTHVACMode with wrong value)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTHeatCool.from_knx(DPTArray((1,)))
        with pytest.raises(CouldNotParseTelegram):
            DPTHeatCool.from_knx(DPTBinary(2))
