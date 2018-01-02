"""Unit test for KNX float object."""
import unittest

from xknx.exceptions import ConversionError
from xknx.knx import DPTFloat, DPTIEEE754, DPTHumidity, DPTLux, DPTTemperature, DPTElectricPotential, DPTElectricCurrent, DPTPower


class TestDPTFloat(unittest.TestCase):
    """Test class for KNX float object."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_value_from_documentation(self):
        """Test parsing and streaming of DPTFloat -30.00. Example from the internet[tm]."""
        self.assertEqual(DPTFloat().to_knx(-30.00), (0x8a, 0x24))
        self.assertEqual(DPTFloat().from_knx((0x8a, 0x24)), -30.00)

    def test_value_taken_from_live_thermostat(self):
        """Test parsing and streaming of DPTFloat 19.96."""
        self.assertEqual(DPTFloat().to_knx(16.96), (0x06, 0xa0))
        self.assertEqual(DPTFloat().from_knx((0x06, 0xa0)), 16.96)

    def test_zero_value(self):
        """Test parsing and streaming of DPTFloat zero value."""
        self.assertEqual(DPTFloat().to_knx(0.00), (0x00, 0x00))
        self.assertEqual(DPTFloat().from_knx((0x00, 0x00)), 0.00)

    def test_room_temperature(self):
        """Test parsing and streaming of DPTFloat 21.00. Room temperature."""
        self.assertEqual(DPTFloat().to_knx(21.00), (0x0c, 0x1a))
        self.assertEqual(DPTFloat().from_knx((0x0c, 0x1a)), 21.00)

    def test_high_temperature(self):
        """Test parsing and streaming of DPTFloat 500.00, 499.84, 500.16. Testing rounding issues."""
        self.assertEqual(DPTFloat().to_knx(500.00), (0x2E, 0x1A))
        self.assertAlmostEqual(DPTFloat().from_knx((0x2E, 0x1A)), 499.84)
        self.assertAlmostEqual(DPTFloat().from_knx((0x2E, 0x1B)), 500.16)
        self.assertEqual(DPTFloat().to_knx(499.84), (0x2E, 0x1A))
        self.assertEqual(DPTFloat().to_knx(500.16), (0x2E, 0x1B))

    def test_minor_negative_temperature(self):
        """Test parsing and streaming of DPTFloat -10.00. Testing negative values."""
        self.assertEqual(DPTFloat().to_knx(-10.00), (0x84, 0x18))
        self.assertEqual(DPTFloat().from_knx((0x84, 0x18)), -10.00)

    def test_very_cold_temperature(self):
        """Test parsing and streaming of DPTFloat -1000.00,-999.68, -1000.32. Testing rounding issues of negative values."""
        self.assertEqual(DPTFloat().to_knx(-1000.00), (0xB1, 0xE6))
        self.assertEqual(DPTFloat().from_knx((0xB1, 0xE6)), -999.68)
        self.assertEqual(DPTFloat().from_knx((0xB1, 0xE5)), -1000.32)
        self.assertEqual(DPTFloat().to_knx(-999.68), (0xB1, 0xE6))
        self.assertEqual(DPTFloat().to_knx(-1000.32), (0xB1, 0xE5))

    def test_max(self):
        """Test parsing and streaming of DPTFloat with maximum value."""
        self.assertEqual(DPTFloat().to_knx(DPTFloat.value_max), (0x7F, 0xFF))
        self.assertEqual(DPTFloat().from_knx((0x7F, 0xFF)), DPTFloat.value_max)

    def test_min(self):
        """Test parsing and streaming of DPTFloat with minimum value."""
        self.assertEqual(DPTFloat().to_knx(DPTFloat.value_min), (0xF8, 0x00))
        self.assertEqual(DPTFloat().from_knx((0xF8, 0x00)), DPTFloat.value_min)

    def test_close_to_max(self):
        """Test parsing and streaming of DPTFloat with maximum value -1."""
        self.assertEqual(DPTFloat().to_knx(670433.28), (0x7F, 0xFE))
        self.assertEqual(DPTFloat().from_knx((0x7F, 0xFE)), 670433.28)

    def test_close_to_min(self):
        """Test parsing and streaming of DPTFloat with minimum value +1."""
        self.assertEqual(DPTFloat().to_knx(-670760.96), (0xF8, 0x01))
        self.assertEqual(DPTFloat().from_knx((0xF8, 0x01)), -670760.96)

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTFloat with wrong value (underflow)."""
        with self.assertRaises(ConversionError):
            DPTFloat().to_knx(DPTFloat.value_min - 1)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTFloat with wrong value (overflow)."""
        with self.assertRaises(ConversionError):
            DPTFloat().to_knx(DPTFloat.value_max + 1)

    def test_to_knx_wrong_parameter(self):
        """Test parsing of DPTFloat with wrong value (string)."""
        with self.assertRaises(ConversionError):
            DPTFloat().to_knx("fnord")

    def test_from_knx_wrong_parameter(self):
        """Test parsing of DPTFloat with wrong value (wrong number of bytes)."""
        with self.assertRaises(ConversionError):
            DPTFloat().from_knx((0xF8, 0x01, 0x23))

    def test_from_knx_wrong_parameter2(self):
        """Test parsing of DPTFloat with wrong value (second parameter is a string)."""
        with self.assertRaises(ConversionError):
            DPTFloat().from_knx((0xF8, "0x23"))

    #
    # DPTTemperature
    #
    def test_temperature_settings(self):
        """Test attributes of DPTTemperature."""
        self.assertEqual(DPTTemperature().value_min, -273)
        self.assertEqual(DPTTemperature().value_max, 670760)
        self.assertEqual(DPTTemperature().unit, "°C")
        self.assertEqual(DPTTemperature().resolution, 1)

    def test_temperature_assert_min_exceeded(self):
        """Testing parsing of DPTTemperature with wrong value."""
        with self.assertRaises(ConversionError):
            DPTTemperature().to_knx(-274)

    def test_temperature_assert_min_exceeded_from_knx(self):
        """Testing parsing of DPTTemperature with wrong value."""
        with self.assertRaises(ConversionError):
            DPTTemperature().from_knx((0xB1, 0xE6))  # -1000

    #
    # DPTLux
    #
    def test_lux_settings(self):
        """Test attributes of DPTLux."""
        self.assertEqual(DPTLux().value_min, 0)
        self.assertEqual(DPTLux().value_max, 670760)
        self.assertEqual(DPTLux().unit, "lx")
        self.assertEqual(DPTLux().resolution, 1)

    def test_lux_assert_min_exceeded(self):
        """Test parsing of DPTLux with wrong value."""
        with self.assertRaises(ConversionError):
            DPTLux().to_knx(-1)

    #
    # DPTHumidity
    #
    def test_humidity_settings(self):
        """Test attributes of DPTHumidity."""
        self.assertEqual(DPTHumidity().value_min, 0)
        self.assertEqual(DPTHumidity().value_max, 670760)
        self.assertEqual(DPTHumidity().unit, "%")
        self.assertEqual(DPTHumidity().resolution, 1)

    def test_humidity_assert_min_exceeded(self):
        """Test parsing of DPTHumidity with wrong value."""
        with self.assertRaises(ConversionError):
            DPTHumidity().to_knx(-1)

        
    
    #
    # DPTIEEE754
    #
    def test_ieee754_values_from_power_meter(self):
        self.assertEqual(DPTIEEE754().from_knx((0x43, 0xC6, 0x80, 00)), 397)
        self.assertEqual(DPTIEEE754().to_knx(397), (0x43, 0xC6, 0x80, 00))
        self.assertEqual(DPTIEEE754().from_knx((0x42, 0x38, 0x00, 00)), 46)
        self.assertEqual(DPTIEEE754().to_knx(46), (0x42, 0x38, 0x00, 00))


    def test_ieee754_values_from_voltage_meter(self):
        self.assertEqual(round(DPTIEEE754().from_knx((0x43, 0x65, 0xE3, 0xD7)), 2), 229.89)
        self.assertEqual(DPTIEEE754().to_knx(229.89), (0x43, 0x65, 0xE3, 0xD7))

    def test_ieee754_zero_value(self):
        """Test parsing and streaming of DPTFloat zero value."""
        self.assertEqual(DPTIEEE754().from_knx((0x00, 0x00, 0x00, 0x00)), 0.00)
        self.assertEqual(DPTIEEE754().to_knx(0.00), (0x00, 0x00, 0x00, 0x00))

    def test_ieee754_to_knx_wrong_parameter(self):
        """Test parsing of DPTFloat with wrong value (string)."""
        with self.assertRaises(ConversionError):
            DPTIEEE754().to_knx("fnord")

    def test_ieee754_from_knx_wrong_parameter(self):
        """Test parsing of DPTFloat with wrong value (wrong number of bytes)."""
        with self.assertRaises(ConversionError):
            DPTIEEE754().from_knx((0xF8, 0x01, 0x23))

    def test_ieee754_from_knx_wrong_parameter2(self):
        """Test parsing of DPTFloat with wrong value (second parameter is a string)."""
        with self.assertRaises(ConversionError):
            DPTIEEE754().from_knx((0xF8, "0x23", 0x00, 0x00))


    #
    # DPTElectricCurrent
    #
    def test_electric_current_settings(self):
        """Test attributes of DPTLux."""
        self.assertEqual(DPTElectricCurrent().unit, "A")

    #
    # DPTElectricPotential
    #
    def test_electric_potential_settings(self):
        """Test attributes of DPTLux."""
        self.assertEqual(DPTElectricPotential().unit, "V")

    #
    # DPTPower
    #
    def test_power_settings(self):
            """Test attributes of DPTLux."""
            self.assertEqual(DPTPower().unit, "W")
    

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestDPTFloat)
unittest.TextTestRunner(verbosity=2).run(SUITE)
