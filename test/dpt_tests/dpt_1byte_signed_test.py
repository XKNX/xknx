"""Unit test for KNX DPT 1 byte relative value  objects."""
import unittest

from xknx.dpt import DPTPercentV8, DPTSignedRelativeValue, DPTValue1Count
from xknx.exceptions import ConversionError


class TestDPTRelativeValue(unittest.TestCase):
    """Test class for KNX DPT Relative Value."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_from_knx_positive(self):
        """Test positive value from KNX."""
        self.assertEqual(DPTSignedRelativeValue.from_knx((0x00, )), 0)
        self.assertEqual(DPTSignedRelativeValue.from_knx((0x01, )), 1)
        self.assertEqual(DPTSignedRelativeValue.from_knx((0x02, )), 2)
        self.assertEqual(DPTSignedRelativeValue.from_knx((0x64, )), 100)
        self.assertEqual(DPTSignedRelativeValue.from_knx((0x7F, )), 127)

    def test_from_knx_negative(self):
        """Test negative value from KNX."""
        self.assertEqual(DPTSignedRelativeValue.from_knx((0x80, )), -128)
        self.assertEqual(DPTSignedRelativeValue.from_knx((0x9C, )), -100)
        self.assertEqual(DPTSignedRelativeValue.from_knx((0xFE, )), -2)
        self.assertEqual(DPTSignedRelativeValue.from_knx((0xFF, )), -1)

    def test_to_knx_positive(self):
        """Test positive value to KNX."""
        self.assertEqual(DPTSignedRelativeValue.to_knx(0), (0x00, ))
        self.assertEqual(DPTSignedRelativeValue.to_knx(1), (0x01, ))
        self.assertEqual(DPTSignedRelativeValue.to_knx(2), (0x02, ))
        self.assertEqual(DPTSignedRelativeValue.to_knx(100), (0x64, ))
        self.assertEqual(DPTSignedRelativeValue.to_knx(127), (0x7F, ))

    def test_to_knx_negative(self):
        """Test negative value to KNX."""
        self.assertEqual(DPTSignedRelativeValue.to_knx(-128), (0x80, ))
        self.assertEqual(DPTSignedRelativeValue.to_knx(-100), (0x9C, ))
        self.assertEqual(DPTSignedRelativeValue.to_knx(-2), (0xFE, ))
        self.assertEqual(DPTSignedRelativeValue.to_knx(-1), (0xFF, ))

    def test_assert_min_exceeded(self):
        """Test initialization with wrong value (Underflow)."""
        with self.assertRaises(ConversionError):
            DPTSignedRelativeValue.to_knx(-129)

    def test_assert_max_exceeded(self):
        """Test initialization with wrong value (Overflow)."""
        with self.assertRaises(ConversionError):
            DPTSignedRelativeValue.to_knx(128)

    def test_unit(self):
        """Test unit of 1 byte relative value objects."""
        self.assertEqual(DPTSignedRelativeValue.unit, '')
        self.assertEqual(DPTPercentV8.unit, '%')
        self.assertEqual(DPTValue1Count.unit, 'counter pulses')
