"""Unit test for KNX 2 byte objects."""
import unittest

from xknx.dpt import DPTUElCurrentmA
from xknx.exceptions import ConversionError


class TestDPT2byte(unittest.TestCase):
    """Test class for KNX 2 byte objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    #
    # DPTUElCurrentmA
    #
    def test_current_settings(self):
        """Test members of DPTUElCurrentmA."""
        self.assertEqual(DPTUElCurrentmA().value_min, 0)
        self.assertEqual(DPTUElCurrentmA().value_max, 65535)
        self.assertEqual(DPTUElCurrentmA().unit, "mA")
        self.assertEqual(DPTUElCurrentmA().resolution, 1)

    def test_current_assert_min_exceeded(self):
        """Test initialization of DPTUElCurrentmA with wrong value (Underflow)."""
        with self.assertRaises(ConversionError):
            DPTUElCurrentmA().to_knx(-1)

    def test_current_to_knx_exceed_limits(self):
        """Test initialization of DPTUElCurrentmA with wrong value (Overflow)."""
        with self.assertRaises(ConversionError):
            DPTUElCurrentmA().to_knx(65536)

    def test_current_value_max_value(self):
        """Test DPTUElCurrentmA parsing and streaming."""
        self.assertEqual(DPTUElCurrentmA().to_knx(65535), (0xFF, 0xFF))
        self.assertEqual(DPTUElCurrentmA().from_knx((0xFF, 0xFF)), 65535)

    def test_current_value_min_value(self):
        """Test DPTUElCurrentmA parsing and streaming with null values."""
        self.assertEqual(DPTUElCurrentmA().to_knx(0), (0x00, 0x00))
        self.assertEqual(DPTUElCurrentmA().from_knx((0x00, 0x00)), 0)

    def test_current_value_38(self):
        """Test DPTUElCurrentmA parsing and streaming 38mA."""
        self.assertEqual(DPTUElCurrentmA().to_knx(38), (0x00, 0x26))
        self.assertEqual(DPTUElCurrentmA().from_knx((0x00, 0x26)), 38)

    def test_current_value_78(self):
        """Test DPTUElCurrentmA parsing and streaming 78mA."""
        self.assertEqual(DPTUElCurrentmA().to_knx(78), (0x00, 0x4E))
        self.assertEqual(DPTUElCurrentmA().from_knx((0x00, 0x4E)), 78)

    def test_current_value_1234(self):
        """Test DPTUElCurrentmA parsing and streaming 4660mA."""
        self.assertEqual(DPTUElCurrentmA().to_knx(4660), (0x12, 0x34))
        self.assertEqual(DPTUElCurrentmA().from_knx((0x12, 0x34)), 4660)

    def test_current_wrong_value_from_knx(self):
        """Test DPTUElCurrentmA parsing with wrong value."""
        with self.assertRaises(ConversionError):
            DPTUElCurrentmA().from_knx((0xFF, 0x4E, 0x12))
