"""Unit test for KNX DPT 5.010 value."""
import unittest

from xknx.dpt import DPTTariff, DPTValue1Ucount
from xknx.exceptions import ConversionError


class TestDPTValue1Ucount(unittest.TestCase):
    """Test class for KNX 8-bit unsigned value."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_value_50(self):
        """Test parsing and streaming of DPTValue1Ucount 50."""
        self.assertEqual(DPTValue1Ucount().to_knx(50), (0x32,))
        self.assertEqual(DPTValue1Ucount().from_knx((0x32,)), 50)

    def test_value_max(self):
        """Test parsing and streaming of DPTValue1Ucount 255."""
        self.assertEqual(DPTValue1Ucount().to_knx(255), (0xFF,))
        self.assertEqual(DPTValue1Ucount().from_knx((0xFF,)), 255)

    def test_value_min(self):
        """Test parsing and streaming of DPTValue1Ucount 0."""
        self.assertEqual(DPTValue1Ucount().to_knx(0), (0x00,))
        self.assertEqual(DPTValue1Ucount().from_knx((0x00,)), 0)

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTValue1Ucount with wrong value (underflow)."""
        with self.assertRaises(ConversionError):
            DPTValue1Ucount().to_knx(DPTValue1Ucount.value_min - 1)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTValue1Ucount with wrong value (overflow)."""
        with self.assertRaises(ConversionError):
            DPTValue1Ucount().to_knx(DPTValue1Ucount.value_max + 1)

    def test_to_knx_wrong_parameter(self):
        """Test parsing of DPTValue1Ucount with wrong value (string)."""
        with self.assertRaises(ConversionError):
            DPTValue1Ucount().to_knx("fnord")

    def test_from_knx_wrong_parameter(self):
        """Test parsing of DPTValue1Ucount with wrong value (3 byte array)."""
        with self.assertRaises(ConversionError):
            DPTValue1Ucount().from_knx((0x01, 0x02, 0x03))

    def test_from_knx_wrong_value(self):
        """Test parsing of DPTValue1Ucount with value which exceeds limits."""
        with self.assertRaises(ConversionError):
            DPTValue1Ucount().from_knx((0x256,))

    def test_from_knx_wrong_parameter2(self):
        """Test parsing of DPTValue1Ucount with wrong value (array containing string)."""
        with self.assertRaises(ConversionError):
            DPTValue1Ucount().from_knx(("0x23"))


class TestDPTTariff(unittest.TestCase):
    """Test class for KNX 8-bit tariff information."""

    def test_from_knx_max_exceeded(self):
        """Test parsing of DPTTariff with wrong value (overflow)."""
        with self.assertRaises(ConversionError):
            DPTTariff().from_knx((0xFF,))
