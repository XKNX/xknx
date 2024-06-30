"""Unit test for KNX 4 byte float objects."""

import math
import struct
from unittest.mock import patch

import pytest

from xknx.dpt import (
    DPT4ByteFloat,
    DPTArray,
    DPTElectricCurrent,
    DPTElectricPotential,
    DPTFrequency,
    DPTPhaseAngleDeg,
    DPTPower,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPT4ByteFloat:
    """Test class for KNX 4 byte/octet float object."""

    def test_4byte_float_values_from_power_meter(self):
        """Test parsing DPT4ByteFloat value from power meter."""
        assert DPT4ByteFloat.from_knx(DPTArray((0x43, 0xC6, 0x80, 00))) == 397
        assert DPT4ByteFloat.to_knx(397) == DPTArray((0x43, 0xC6, 0x80, 00))
        assert DPT4ByteFloat.from_knx(DPTArray((0x42, 0x38, 0x00, 00))) == 46
        assert DPT4ByteFloat.to_knx(46) == DPTArray((0x42, 0x38, 0x00, 00))

    def test_14_033(self):
        """Test parsing DPTFrequency unit."""
        assert DPTFrequency.unit == "Hz"

    def test_14_055(self):
        """Test DPTPhaseAngleDeg object."""
        assert DPT4ByteFloat.from_knx(DPTArray((0x42, 0xEF, 0x00, 0x00))) == 119.5
        assert DPT4ByteFloat.to_knx(119.5) == DPTArray((0x42, 0xEF, 0x00, 0x00))
        assert DPTPhaseAngleDeg.unit == "°"

    def test_14_057(self):
        """Test DPT4ByteFloat object."""
        assert DPT4ByteFloat.from_knx(DPTArray((0x3F, 0x71, 0xEB, 0x86))) == 0.9450001
        assert DPT4ByteFloat.to_knx(0.945000052452) == DPTArray(
            (0x3F, 0x71, 0xEB, 0x86)
        )
        assert DPT4ByteFloat.unit is None

    def test_4byte_float_values_from_voltage_meter(self):
        """Test parsing DPT4ByteFloat from voltage meter."""
        assert DPT4ByteFloat.from_knx(DPTArray((0x43, 0x65, 0xE3, 0xD7))) == 229.89
        assert DPT4ByteFloat.to_knx(229.89) == DPTArray((0x43, 0x65, 0xE3, 0xD7))

    def test_4byte_float_zero_value(self):
        """Test parsing and streaming of DPT4ByteFloat zero value."""
        assert DPT4ByteFloat.from_knx(DPTArray((0x00, 0x00, 0x00, 0x00))) == 0.00
        assert DPT4ByteFloat.to_knx(0.00) == DPTArray((0x00, 0x00, 0x00, 0x00))

    def test_4byte_float_special_value(self):
        """Test parsing and streaming of DPT4ByteFloat special value."""
        assert math.isnan(DPT4ByteFloat.from_knx(DPTArray((0x7F, 0xC0, 0x00, 0x00))))
        assert DPT4ByteFloat.to_knx(float("nan")) == DPTArray((0x7F, 0xC0, 0x00, 0x00))

        assert math.isinf(DPT4ByteFloat.from_knx(DPTArray((0x7F, 0x80, 0x00, 0x00))))
        assert DPT4ByteFloat.to_knx(float("inf")) == DPTArray((0x7F, 0x80, 0x00, 0x00))

        assert DPT4ByteFloat.from_knx(DPTArray((0xFF, 0x80, 0x00, 0x00))) == float(
            "-inf"
        )
        assert DPT4ByteFloat.to_knx(float("-inf")) == DPTArray((0xFF, 0x80, 0x00, 0x00))

        assert DPT4ByteFloat.from_knx(DPTArray((0x80, 0x00, 0x00, 0x00))) == float("-0")
        assert DPT4ByteFloat.to_knx(float("-0")) == DPTArray((0x80, 0x00, 0x00, 0x00))

    def test_4byte_float_to_knx_wrong_parameter(self):
        """Test parsing of DPT4ByteFloat with wrong value (string)."""
        with pytest.raises(ConversionError):
            DPT4ByteFloat.to_knx("fnord")

    def test_4byte_float_from_knx_wrong_parameter(self):
        """Test parsing of DPT4ByteFloat with wrong value (wrong number of bytes)."""
        with pytest.raises(CouldNotParseTelegram):
            DPT4ByteFloat.from_knx(DPTArray((0xF8, 0x01, 0x23)))

    def test_4byte_flaot_from_knx_unpack_error(self):
        """Test DPT4ByteFloat parsing with unpack error."""
        with patch("struct.unpack") as unpack_mock:
            unpack_mock.side_effect = struct.error()
            with pytest.raises(ConversionError):
                DPT4ByteFloat.from_knx(DPTArray((0x01, 0x23, 0x02, 0x02)))

    #
    # DPTElectricCurrent
    #
    def test_electric_current_settings(self):
        """Test attributes of DPTElectricCurrent."""
        assert DPTElectricCurrent.unit == "A"

    #
    # DPTElectricPotential
    #
    def test_electric_potential_settings(self):
        """Test attributes of DPTElectricPotential."""
        assert DPTElectricPotential.unit == "V"

    #
    # DPTPower
    #
    def test_power_settings(self):
        """Test attributes of DPTPower."""
        assert DPTPower.unit == "W"
