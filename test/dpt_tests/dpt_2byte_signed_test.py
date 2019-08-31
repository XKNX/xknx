"""Unit test for KNX 2 byte signed objects."""
import struct
import unittest
from unittest.mock import patch

from xknx.dpt import DPT2ByteSigned
from xknx.exceptions import ConversionError


class TestDPT2ByteSigned(unittest.TestCase):
    """Test class for KNX 2 byte signed objects."""
    # pylint: disable=too-many-public-methods,invalid-name

    def test_signed_settings(self):
        """Test members of DPT2ByteSigned."""
        self.assertEqual(DPT2ByteSigned().value_min, -32768)
        self.assertEqual(DPT2ByteSigned().value_max, 32767)

    def test_signed_assert_min_exceeded(self):
        """Test initialization of DPT2ByteSigned with wrong value (Underflow)."""
        with self.assertRaises(ConversionError):
            DPT2ByteSigned().to_knx(-32769)

    def test_signed_to_knx_exceed_limits(self):
        """Test initialization of DPT2ByteSigned with wrong value (Overflow)."""
        with self.assertRaises(ConversionError):
            DPT2ByteSigned().to_knx(32768)

    def test_signed_value_max_value(self):
        """Test DPT2ByteSigned parsing and streaming."""
        self.assertEqual(DPT2ByteSigned().to_knx(32767), (0x7F, 0xFF))
        self.assertEqual(DPT2ByteSigned().from_knx((0x7F, 0xFF)), 32767)

    def test_signed_value_min_value(self):
        """Test DPT2ByteSigned parsing and streaming with null values."""
        self.assertEqual(DPT2ByteSigned().to_knx(-20480), (0xB0, 0x00))
        self.assertEqual(DPT2ByteSigned().from_knx((0xB0, 0x00)), -20480)

    def test_signed_value_0123(self):
        """Test DPT2ByteSigned parsing and streaming."""
        self.assertEqual(DPT2ByteSigned().to_knx(291), (0x01, 0x23))
        self.assertEqual(DPT2ByteSigned().from_knx((0x01, 0x23)), 291)

    def test_signed_wrong_value_from_knx(self):
        """Test DPT2ByteSigned parsing with wrong value."""
        with self.assertRaises(ConversionError):
            DPT2ByteSigned().from_knx((0xFF, 0x4E, 0x12))

    def test_from_knx_unpack_error(self):
        """Test DPT2ByteSigned parsing with unpack error."""
        with patch('struct.unpack') as unpackMock:
            unpackMock.side_effect = struct.error()
            with self.assertRaises(ConversionError):
                DPT2ByteSigned().from_knx((0x01, 0x23))

    def test_to_knx_pack_error(self):
        """Test serializing DPT2ByteSigned with pack error."""
        with patch('struct.pack') as packMock:
            packMock.side_effect = struct.error()
            with self.assertRaises(ConversionError):
                DPT2ByteSigned().to_knx(1234)
