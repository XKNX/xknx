"""Unit test for KNX 2 byte float objects."""

import pytest

from xknx.dpt import (
    DPT2ByteFloat,
    DPTAirFlow,
    DPTArray,
    DPTEnthalpy,
    DPTHumidity,
    DPTLux,
    DPTPartsPerMillion,
    DPTTemperature,
    DPTVoltage,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTFloat:
    """Test class for KNX 2 byte/octet float object."""

    # ####################################################################
    # DPT2ByteFloat
    #
    def test_value_from_documentation(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat -30.00. Example from the internet[tm]."""
        assert DPT2ByteFloat.to_knx(-30.00) == DPTArray((0x8A, 0x24))
        assert DPT2ByteFloat.from_knx(DPTArray((0x8A, 0x24))) == -30.00

    def test_value_taken_from_live_thermostat(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat 19.96."""
        assert DPT2ByteFloat.to_knx(16.96) == DPTArray((0x06, 0xA0))
        assert DPT2ByteFloat.from_knx(DPTArray((0x06, 0xA0))) == 16.96

    def test_zero_value(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat zero value."""
        assert DPT2ByteFloat.to_knx(0.00) == DPTArray((0x00, 0x00))
        assert DPT2ByteFloat.from_knx(DPTArray((0x00, 0x00))) == 0.00

    def test_near_zero_value(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat near zero value."""
        assert DPT2ByteFloat.to_knx(0.0002) == DPTArray((0x00, 0x00))
        assert DPT2ByteFloat.to_knx(0.005) == DPTArray((0x00, 0x00))
        assert DPT2ByteFloat.to_knx(0.00501) == DPTArray((0x00, 0x01))

        assert DPT2ByteFloat.to_knx(-0.0) == DPTArray((0x00, 0x00))
        # ETS would convert values < 0 and >= -0.005 to 0x8000
        # which is equivalent to -20.48 so we handle this differently
        assert DPT2ByteFloat.to_knx(-0.0002) == DPTArray((0x00, 0x00))
        assert DPT2ByteFloat.to_knx(-0.005) == DPTArray((0x00, 0x00))
        assert DPT2ByteFloat.to_knx(-0.00501) == DPTArray(
            (0x87, 0xFF)
        )  # this is ETS-conform again

        assert DPT2ByteFloat.from_knx(DPTArray((0x00, 0x01))) == 0.01
        assert DPT2ByteFloat.from_knx(DPTArray((0x87, 0xFF))) == -0.01

    def test_room_temperature(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat 21.00. Room temperature."""
        assert DPT2ByteFloat.to_knx(21.00) == DPTArray((0x0C, 0x1A))
        assert DPT2ByteFloat.from_knx(DPTArray((0x0C, 0x1A))) == 21.00

    def test_high_temperature(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat 500.00, 499.84, 500.16. Testing rounding issues."""
        assert DPT2ByteFloat.to_knx(500.00) == DPTArray((0x2E, 0x1A))
        assert (
            round(abs(DPT2ByteFloat.from_knx(DPTArray((0x2E, 0x1A))) - 499.84), 7) == 0
        )
        assert (
            round(abs(DPT2ByteFloat.from_knx(DPTArray((0x2E, 0x1B))) - 500.16), 7) == 0
        )
        assert DPT2ByteFloat.to_knx(499.84) == DPTArray((0x2E, 0x1A))
        assert DPT2ByteFloat.to_knx(500.16) == DPTArray((0x2E, 0x1B))

    def test_minor_negative_temperature(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat -10.00. Testing negative values."""
        assert DPT2ByteFloat.to_knx(-10.00) == DPTArray((0x84, 0x18))
        assert DPT2ByteFloat.from_knx(DPTArray((0x84, 0x18))) == -10.00

    def test_very_cold_temperature(self) -> None:
        """
        Test parsing and streaming of DPT2ByteFloat -1000.00,-999.68, -1000.32.

        Testing rounding issues of negative values.
        """
        assert DPT2ByteFloat.to_knx(-1000.00) == DPTArray((0xB1, 0xE6))
        assert DPT2ByteFloat.from_knx(DPTArray((0xB1, 0xE6))) == -999.68
        assert DPT2ByteFloat.from_knx(DPTArray((0xB1, 0xE5))) == -1000.32
        assert DPT2ByteFloat.to_knx(-999.68) == DPTArray((0xB1, 0xE6))
        assert DPT2ByteFloat.to_knx(-1000.32) == DPTArray((0xB1, 0xE5))

    def test_max(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat with maximum value."""
        assert DPT2ByteFloat.to_knx(DPT2ByteFloat.value_max) == DPTArray((0x7F, 0xFF))
        assert DPT2ByteFloat.from_knx(DPTArray((0x7F, 0xFF))) == DPT2ByteFloat.value_max

    def test_close_to_limit(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat with numeric limit."""
        assert DPT2ByteFloat.to_knx(20.48) == DPTArray((0x0C, 0x00))
        assert DPT2ByteFloat.from_knx(DPTArray((0x0C, 0x00))) == 20.48
        assert DPT2ByteFloat.to_knx(-20.48) == DPTArray((0x80, 0x00))
        assert DPT2ByteFloat.from_knx(DPTArray((0x80, 0x00))) == -20.48

    def test_min(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat with minimum value."""
        assert DPT2ByteFloat.to_knx(DPT2ByteFloat.value_min) == DPTArray((0xF8, 0x00))
        assert DPT2ByteFloat.from_knx(DPTArray((0xF8, 0x00))) == DPT2ByteFloat.value_min

    def test_close_to_max(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat with maximum value -1."""
        assert DPT2ByteFloat.to_knx(670433.28) == DPTArray((0x7F, 0xFE))
        assert DPT2ByteFloat.from_knx(DPTArray((0x7F, 0xFE))) == 670433.28

    def test_close_to_min(self) -> None:
        """Test parsing and streaming of DPT2ByteFloat with minimum value +1."""
        assert DPT2ByteFloat.to_knx(-670760.96) == DPTArray((0xF8, 0x01))
        assert DPT2ByteFloat.from_knx(DPTArray((0xF8, 0x01))) == -670760.96

    def test_to_knx_min_exceeded(self) -> None:
        """Test parsing of DPT2ByteFloat with wrong value (underflow)."""
        with pytest.raises(ConversionError):
            DPT2ByteFloat.to_knx(DPT2ByteFloat.value_min - 1)

    def test_to_knx_max_exceeded(self) -> None:
        """Test parsing of DPT2ByteFloat with wrong value (overflow)."""
        with pytest.raises(ConversionError):
            DPT2ByteFloat.to_knx(DPT2ByteFloat.value_max + 1)

    def test_to_knx_wrong_parameter(self) -> None:
        """Test parsing of DPT2ByteFloat with wrong value (string)."""
        with pytest.raises(ConversionError):
            DPT2ByteFloat.to_knx("fnord")

    def test_from_knx_wrong_parameter(self) -> None:
        """Test parsing of DPT2ByteFloat with wrong value (wrong number of bytes)."""
        with pytest.raises(CouldNotParseTelegram):
            DPT2ByteFloat.from_knx(DPTArray((0xF8, 0x01, 0x23)))

    #
    # DPTTemperature
    #
    def test_temperature_settings(self) -> None:
        """Test attributes of DPTTemperature."""
        assert DPTTemperature.value_min == -273
        assert DPTTemperature.value_max == 670760
        assert DPTTemperature.unit == "°C"
        assert DPTTemperature.resolution == 0.01

    def test_temperature_assert_min_exceeded(self) -> None:
        """Testing parsing of DPTTemperature with wrong value."""
        with pytest.raises(ConversionError):
            DPTTemperature.to_knx(-274)

    def test_temperature_assert_min_exceeded_from_knx(self) -> None:
        """Testing parsing of DPTTemperature with wrong value."""
        with pytest.raises(ConversionError):
            DPTTemperature.from_knx(DPTArray((0xB1, 0xE6)))  # -1000

    #
    # DPTLux
    #
    def test_lux_settings(self) -> None:
        """Test attributes of DPTLux."""
        assert DPTLux.value_min == 0
        assert DPTLux.value_max == 670760
        assert DPTLux.unit == "lx"
        assert DPTLux.resolution == 0.01

    def test_lux_assert_min_exceeded(self) -> None:
        """Test parsing of DPTLux with wrong value."""
        with pytest.raises(ConversionError):
            DPTLux.to_knx(-1)

    #
    # DPTHumidity
    #
    def test_humidity_settings(self) -> None:
        """Test attributes of DPTHumidity."""
        assert DPTHumidity.value_min == 0
        assert DPTHumidity.value_max == 670760
        assert DPTHumidity.unit == "%"
        assert DPTHumidity.resolution == 0.01

    def test_humidity_assert_min_exceeded(self) -> None:
        """Test parsing of DPTHumidity with wrong value."""
        with pytest.raises(ConversionError):
            DPTHumidity.to_knx(-1)

    #
    # DPTEnthalpy
    #
    def test_enthalpy_settings(self) -> None:
        """Test attributes of DPTEnthalpy."""
        assert DPTEnthalpy.unit == "H"

    #
    # DPTPartsPerMillion
    #
    def test_partspermillion_settings(self) -> None:
        """Test attributes of DPTPartsPerMillion."""
        assert DPTPartsPerMillion.unit == "ppm"

    #
    # DPTAirFlow
    #
    def test_airflow_settings(self) -> None:
        """Test attributes of DPTAirFlow."""
        assert DPTAirFlow.unit == "m³/h"

    #
    # DPTVoltage
    #
    def test_voltage_settings(self) -> None:
        """Test attributes of DPTVoltage."""
        assert DPTVoltage.unit == "mV"
