"""Unit test for KNX DPT 5.001 and 5.003 value."""
import unittest

from xknx.dpt import DPTAngle, DPTScaling
from xknx.exceptions import ConversionError


class TestDPTScaling(unittest.TestCase):
    """Test class for KNX scaling value."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_value_30_pct(self):
        """Test parsing and streaming of DPTScaling 30%."""
        self.assertEqual(DPTScaling().to_knx(30), (0x4C,))
        self.assertEqual(DPTScaling().from_knx((0x4C,)), 30)

    def test_value_99_pct(self):
        """Test parsing and streaming of DPTScaling 99%."""
        self.assertEqual(DPTScaling().to_knx(99), (0xFC,))
        self.assertEqual(DPTScaling().from_knx((0xFC,)), 99)

    def test_value_max(self):
        """Test parsing and streaming of DPTScaling 100%."""
        self.assertEqual(DPTScaling().to_knx(100), (0xFF,))
        self.assertEqual(DPTScaling().from_knx((0xFF,)), 100)

    def test_value_min(self):
        """Test parsing and streaming of DPTScaling 0."""
        self.assertEqual(DPTScaling().to_knx(0), (0x00,))
        self.assertEqual(DPTScaling().from_knx((0x00,)), 0)

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTScaling with wrong value (underflow)."""
        with self.assertRaises(ConversionError):
            DPTScaling().to_knx(-1)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTScaling with wrong value (overflow)."""
        with self.assertRaises(ConversionError):
            DPTScaling().to_knx(101)

    def test_to_knx_wrong_parameter(self):
        """Test parsing of DPTScaling with wrong value (string)."""
        with self.assertRaises(ConversionError):
            DPTScaling().to_knx("fnord")

    def test_from_knx_wrong_parameter(self):
        """Test parsing of DPTScaling with wrong value (3 byte array)."""
        with self.assertRaises(ConversionError):
            DPTScaling().from_knx((0x01, 0x02, 0x03))

    def test_from_knx_wrong_value(self):
        """Test parsing of DPTScaling with value which exceeds limits."""
        with self.assertRaises(ConversionError):
            DPTScaling().from_knx((0x256,))

    def test_from_knx_wrong_parameter2(self):
        """Test parsing of DPTScaling with wrong value (array containing string)."""
        with self.assertRaises(ConversionError):
            DPTScaling().from_knx(("0x23"))


class TestDPTAngle(unittest.TestCase):
    """Test class for KNX scaling value."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_value_30_deg(self):
        """Test parsing and streaming of DPTAngle 30°."""
        self.assertEqual(DPTAngle().to_knx(30), (0x15,))
        self.assertEqual(DPTAngle().from_knx((0x15,)), 30)

    def test_value_270_deg(self):
        """Test parsing and streaming of DPTAngle 270°."""
        self.assertEqual(DPTAngle().to_knx(270), (0xBF,))
        self.assertEqual(DPTAngle().from_knx((0xBF,)), 270)

    def test_value_max(self):
        """Test parsing and streaming of DPTAngle 360°."""
        self.assertEqual(DPTAngle().to_knx(360), (0xFF,))
        self.assertEqual(DPTAngle().from_knx((0xFF,)), 360)

    def test_value_min(self):
        """Test parsing and streaming of DPTAngle 0°."""
        self.assertEqual(DPTAngle().to_knx(0), (0x00,))
        self.assertEqual(DPTAngle().from_knx((0x00,)), 0)

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTAngle with wrong value (underflow)."""
        with self.assertRaises(ConversionError):
            DPTAngle().to_knx(-1)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTAngle with wrong value (overflow)."""
        with self.assertRaises(ConversionError):
            DPTAngle().to_knx(361)
