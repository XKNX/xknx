"""Unit test for KNX scaling value."""
import unittest

from xknx.exceptions import ConversionError
from xknx.knx import DPTInteger


class TestDPTInteger(unittest.TestCase):
    """Test class for KNX scaling value."""

    # pylint: disable=too-many-public-methods,invalid-name,protected-access

    def test_value_zero(self):
        """Test parsing and streaming of DPTInteger 0."""
        self.assertEqual(DPTInteger.to_knx(0, octets=1, signed=False), (0x0,))
        self.assertEqual(DPTInteger.to_knx(0, octets=2, signed=False), (0x0, 0x0))
        self.assertEqual(DPTInteger.to_knx(0, octets=4, signed=False), (0x0, 0x0, 0x0, 0x0))
        self.assertEqual(DPTInteger.to_knx(0, octets=1, signed=True), (0x0,))
        self.assertEqual(DPTInteger.to_knx(0, octets=2, signed=True), (0x0, 0x0))
        self.assertEqual(DPTInteger.to_knx(0, octets=4, signed=True), (0x0, 0x0, 0x0, 0x0))
        self.assertEqual(DPTInteger.from_knx((0x0,), octets=1, signed=False), 0)
        self.assertEqual(DPTInteger.from_knx((0x0, 0x0), octets=2, signed=False), 0)
        self.assertEqual(DPTInteger.from_knx((0x0, 0x0, 0x0, 0x0), octets=4, signed=False), 0)
        self.assertEqual(DPTInteger.from_knx((0x0,), octets=1, signed=True), 0)
        self.assertEqual(DPTInteger.from_knx((0x0, 0x0), octets=2, signed=True), 0)
        self.assertEqual(DPTInteger.from_knx((0x0, 0x0, 0x0, 0x0), octets=4, signed=True), 0)

    def test_value_50(self):
        """Test parsing and streaming of DPTInteger 50."""
        self.assertEqual(DPTInteger.to_knx(50, octets=1, signed=False), (0x32,))
        self.assertEqual(DPTInteger.to_knx(50, octets=2, signed=False), (0x0, 0x32))
        self.assertEqual(DPTInteger.to_knx(50, octets=4, signed=False), (0x0, 0x0, 0x0, 0x32))
        self.assertEqual(DPTInteger.to_knx(50, octets=1, signed=True), (0x32,))
        self.assertEqual(DPTInteger.to_knx(50, octets=2, signed=True), (0x0, 0x32))
        self.assertEqual(DPTInteger.to_knx(50, octets=4, signed=True), (0x0, 0x0, 0x0, 0x32))
        self.assertEqual(DPTInteger.from_knx((0x32,), octets=1, signed=False), 50)
        self.assertEqual(DPTInteger.from_knx((0x0, 0x32), octets=2, signed=False), 50)
        self.assertEqual(DPTInteger.from_knx((0x0, 0x0, 0x0, 0x32), octets=4, signed=False), 50)
        self.assertEqual(DPTInteger.from_knx((0x32,), octets=1, signed=True), 50)
        self.assertEqual(DPTInteger.from_knx((0x0, 0x32), octets=2, signed=True), 50)
        self.assertEqual(DPTInteger.from_knx((0x0, 0x0, 0x0, 0x32), octets=4, signed=True), 50)

    def test_value_minus_50(self):
        """Test parsing and streaming of DPTInteger -50."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-50, octets=1, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-50, octets=2, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-50, octets=4, signed=False)
        self.assertEqual(DPTInteger.to_knx(-50, octets=1, signed=True), (0xCE,))
        self.assertEqual(DPTInteger.to_knx(-50, octets=2, signed=True), (0xFF, 0xCE))
        self.assertEqual(DPTInteger.to_knx(-50, octets=4, signed=True), (0xFF, 0xFF, 0xFF, 0xCE))
        self.assertEqual(DPTInteger.from_knx((0xCE,), octets=1, signed=True), -50)
        self.assertEqual(DPTInteger.from_knx((0xFF, 0xCE), octets=2, signed=True), -50)
        self.assertEqual(DPTInteger.from_knx((0xFF, 0xFF, 0xFF, 0xCE), octets=4, signed=True), -50)

    def test_value_255(self):
        """Test parsing and streaming of DPTInteger 255 - max value short."""
        self.assertEqual(DPTInteger.to_knx(255, octets=1, signed=False), (0xFF,))
        self.assertEqual(DPTInteger.to_knx(255, octets=2, signed=False), (0x0, 0xFF))
        self.assertEqual(DPTInteger.to_knx(255, octets=4, signed=False), (0x0, 0x0, 0x0, 0xFF))
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(255, octets=1, signed=True)
        self.assertEqual(DPTInteger.to_knx(255, octets=2, signed=True), (0x0, 0xFF))
        self.assertEqual(DPTInteger.to_knx(255, octets=4, signed=True), (0x0, 0x0, 0x0, 0xFF))
        self.assertEqual(DPTInteger.from_knx((0xFF,), octets=1, signed=False), 255)
        self.assertEqual(DPTInteger.from_knx((0x0, 0xFF), octets=2, signed=False), 255)
        self.assertEqual(DPTInteger.from_knx((0x0, 0x0, 0x0, 0xFF), octets=4, signed=False), 255)

    def test_value_minus_255(self):
        """Test parsing and streaming of DPTInteger -255."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-255, octets=1, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-255, octets=2, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-255, octets=4, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-255, octets=1, signed=True)
        self.assertEqual(DPTInteger.to_knx(-255, octets=2, signed=True), (0xFF, 0x1))
        self.assertEqual(DPTInteger.to_knx(-255, octets=4, signed=True), (0xFF, 0xFF, 0xFF, 0x1))
        self.assertEqual(DPTInteger.from_knx((0xFF, 0x1), octets=2, signed=True), -255)
        self.assertEqual(DPTInteger.from_knx((0xFF, 0xFF, 0xFF, 0x01), octets=4, signed=True), -255)

    def test_value_1000(self):
        """Test parsing and streaming of DPTInteger 1000."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(1000, octets=1, signed=False)
        self.assertEqual(DPTInteger.to_knx(1000, octets=2, signed=False), (0x3, 0xE8))
        self.assertEqual(DPTInteger.to_knx(1000, octets=4, signed=False), (0x0, 0x0, 0x3, 0xE8))
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(1000, octets=1, signed=True)
        self.assertEqual(DPTInteger.to_knx(1000, octets=2, signed=True), (0x3, 0xE8))
        self.assertEqual(DPTInteger.to_knx(1000, octets=4, signed=True), (0x0, 0x0, 0x3, 0xE8))
        self.assertEqual(DPTInteger.from_knx((0x3, 0xE8), octets=2, signed=False), 1000)
        self.assertEqual(DPTInteger.from_knx((0x0, 0x0, 0x3, 0xE8), octets=4, signed=False), 1000)

    def test_value_minus_1000(self):
        """Test parsing and streaming of DPTInteger -1000."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-1000, octets=1, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-1000, octets=2, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-1000, octets=4, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-1000, octets=1, signed=True)
        self.assertEqual(DPTInteger.to_knx(-1000, octets=2, signed=True), (0xFC, 0x18))
        self.assertEqual(DPTInteger.to_knx(-1000, octets=4, signed=True), (0xFF, 0xFF, 0xFC, 0x18))
        self.assertEqual(DPTInteger.from_knx((0xFC, 0x18), octets=2, signed=True), -1000)
        self.assertEqual(DPTInteger.from_knx((0xFF, 0xFF, 0xFC, 0x18), octets=4, signed=True), -1000)

    def test_value_65535(self):
        """Test parsing and streaming of DPTInteger 1000 - max value int."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(65535, octets=1, signed=False)
        self.assertEqual(DPTInteger.to_knx(65535, octets=2, signed=False), (0xFF, 0xFF))
        self.assertEqual(DPTInteger.to_knx(65535, octets=4, signed=False), (0x0, 0x0, 0xFF, 0xFF))
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(65535, octets=1, signed=True)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(65535, octets=2, signed=True)
        self.assertEqual(DPTInteger.to_knx(65535, octets=4, signed=True), (0x0, 0x0, 0xFF, 0xFF))
        self.assertEqual(DPTInteger.from_knx((0xFF, 0xFF), octets=2, signed=False), 65535)
        self.assertEqual(DPTInteger.from_knx((0x0, 0x0, 0xFF, 0xFF), octets=4, signed=False), 65535)

    def test_value_minus_60000(self):
        """Test parsing and streaming of DPTInteger -60000."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-60000, octets=1, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-60000, octets=2, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-60000, octets=4, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-60000, octets=1, signed=True)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-60000, octets=2, signed=True)
        self.assertEqual(DPTInteger.to_knx(-60000, octets=4, signed=True), (0xFF, 0xFF, 0x15, 0xA0))
        self.assertEqual(DPTInteger.from_knx((0xFF, 0xFF, 0x15, 0xA0), octets=4, signed=True), -60000)

    def test_value_2147483647(self):
        """Test parsing and streaming of DPTInteger 2147483647 - max value singed long."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(2147483647, octets=1, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(2147483647, octets=2, signed=False)
        self.assertEqual(DPTInteger.to_knx(2147483647, octets=4, signed=False), (0x7F, 0x0FF, 0xFF, 0xFF))
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(2147483647, octets=1, signed=True)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(2147483647, octets=2, signed=True)
        self.assertEqual(DPTInteger.to_knx(2147483647, octets=4, signed=True), (0x7F, 0xFF, 0xFF, 0xFF))
        self.assertEqual(DPTInteger.from_knx((0x7F, 0x0FF, 0xFF, 0xFF), octets=4, signed=True), 2147483647)
        self.assertEqual(DPTInteger.from_knx((0x7F, 0x0FF, 0xFF, 0xFF), octets=4, signed=False), 2147483647)

    def test_value_minus_2147483648(self):
        """Test parsing and streaming of DPTInteger -2147483648 - min value signed long."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-2147483648, octets=1, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-2147483648, octets=2, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-2147483648, octets=4, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-2147483648, octets=1, signed=True)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(-2147483648, octets=2, signed=True)
        self.assertEqual(DPTInteger.to_knx(-2147483648, octets=4, signed=True), (0x80, 0x00, 0x00, 0x00))
        self.assertEqual(DPTInteger.from_knx((0x80, 0x0, 0x0, 0x0), octets=4, signed=True), -2147483648)

    def test_value_4294967295(self):
        """Test parsing and streaming of DPTInteger 4294967295 - max value unsigned long."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(4294967295, octets=1, signed=False)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(4294967295, octets=2, signed=False)
        self.assertEqual(DPTInteger.to_knx(4294967295, octets=4, signed=False), (0xFF, 0x0FF, 0xFF, 0xFF))
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(4294967295, octets=1, signed=True)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(4294967295, octets=2, signed=True)
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(4294967295, octets=4, signed=True)
        self.assertEqual(DPTInteger.from_knx((0xFF, 0x0FF, 0xFF, 0xFF), octets=4, signed=False), 4294967295)

    def test_max_value(self):
        """Test parsing and streaming of DPTInteger 63."""
        self.assertEqual(DPTInteger.to_knx(63, max_value=63), (0x3F,))
        self.assertEqual(DPTInteger.from_knx((0x3F,), max_value=63), 63)

    def test_value_min(self):
        """Test parsing and streaming of DPTInteger 0."""
        self.assertEqual(DPTInteger.to_knx(0), (0x00,))
        self.assertEqual(DPTInteger.from_knx((0x00,)), 0)

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTInteger with wrong value (underflow)."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(4, min_value=5)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTInteger with wrong value (overflow)."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx(256)

    def test_to_knx_wrong_parameter(self):
        """Test parsing of DPTInteger with wrong value (string)."""
        with self.assertRaises(ConversionError):
            DPTInteger.to_knx("fnord")

    def test_from_knx_wrong_parameter(self):
        """Test parsing of DPTInteger with wrong value (wrong octet count)."""
        with self.assertRaises(ConversionError):
            DPTInteger.from_knx((0x01), octets=3)
        with self.assertRaises(ConversionError):
            DPTInteger.from_knx((0x01, 0x02, 0x03))

    def test_from_knx_wrong_value(self):
        """Test parsing of DPTInteger with value which exceeds limits."""
        with self.assertRaises(ConversionError):
            DPTInteger.from_knx((0x64,), max_value=63)

    def test_from_knx_wrong_parameter2(self):
        """Test parsing of DPTInteger with wrong value (array containing string)."""
        with self.assertRaises(ConversionError):
            DPTInteger.from_knx(("0x23"))

    def test_from_knx_impossible_octet_size(self):
        """Test parsing of DPTInteger with wrong octet value."""
        with self.assertRaises(ConversionError):
            DPTInteger.from_knx((0x23, 0x23, 0x23), octets=3)

    def test_max_min_values(self):
        """Test max/min values if different sigend/unsigend int values."""
        # Unsigned short
        self.assertEqual(DPTInteger._calc_max_value(octets=1, signed=False), 255)
        self.assertEqual(DPTInteger._calc_min_value(octets=1, signed=False), 0)
        # Signed short
        self.assertEqual(DPTInteger._calc_max_value(octets=1, signed=True), 127)
        self.assertEqual(DPTInteger._calc_min_value(octets=1, signed=True), -128)
        # Unsigned int
        self.assertEqual(DPTInteger._calc_max_value(octets=2, signed=False), 65535)
        self.assertEqual(DPTInteger._calc_min_value(octets=2, signed=False), 0)
        # Signed int
        self.assertEqual(DPTInteger._calc_max_value(octets=2, signed=True), 32767)
        self.assertEqual(DPTInteger._calc_min_value(octets=2, signed=True), -32768)
        # Unsigned long
        self.assertEqual(DPTInteger._calc_max_value(octets=4, signed=False), 4294967295)
        self.assertEqual(DPTInteger._calc_min_value(octets=4, signed=False), 0)
        # Signed long
        self.assertEqual(DPTInteger._calc_max_value(octets=4, signed=True), 2147483647)
        self.assertEqual(DPTInteger._calc_min_value(octets=4, signed=True), -2147483648)
