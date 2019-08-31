"""Unit test for KNX date objects."""
import unittest

from xknx.dpt import DPTDate
from xknx.exceptions import ConversionError


class TestDPTDate(unittest.TestCase):
    """Test class for KNX date objects."""

    def test_from_knx(self):
        """Test parsing of DPTDate object from binary values. Example 1."""
        self.assertEqual(
            DPTDate().from_knx((0x04, 0x01, 0x02)), {
                'year': 2002,
                'month': 1,
                'day': 4
            })

    def test_from_knx_old_date(self):
        """Test parsing of DPTDate object from binary values. Example 2."""
        self.assertEqual(
            DPTDate().from_knx((0x1F, 0x01, 0x5A)), {
                'year': 1990,
                'month': 1,
                'day': 31
            })

    def test_from_knx_future_date(self):
        """Test parsing of DPTDate object from binary values. Example 3."""
        self.assertEqual(
            DPTDate().from_knx((0x04, 0x0C, 0x59)), {
                'year': 2089,
                'month': 12,
                'day': 4
            })

    def test_to_knx(self):
        """Testing KNX/Byte representation of DPTDate object. Example 1."""
        raw = DPTDate().to_knx({
            'year': 2002,
            'month': 1,
            'day': 4
        })
        self.assertEqual(raw, (0x04, 0x01, 0x02))

    def test_to_knx_old_date(self):
        """Testing KNX/Byte representation of DPTDate object. Example 2."""
        raw = DPTDate().to_knx({
            'year': 1990,
            'month': 1,
            'day': 31
        })
        self.assertEqual(raw, (0x1F, 0x01, 0x5A))

    def test_to_knx_future_date(self):
        """Testing KNX/Byte representation of DPTDate object. Example 3."""
        raw = DPTDate().to_knx({
            'year': 2089,
            'month': 12,
            'day': 4
        })
        self.assertEqual(raw, (0x04, 0x0C, 0x59))

    def test_from_knx_wrong_parameter(self):
        """Test parsing from DPTDate object from wrong binary values."""
        with self.assertRaises(ConversionError):
            DPTDate().from_knx((0xF8, 0x23))

    def test_to_knx_wrong_parameter(self):
        """Test parsing from DPTDate object from wrong string value."""
        with self.assertRaises(ConversionError):
            DPTDate().to_knx("hello")

    def test_to_knx_wrong_day(self):
        """Test parsing from DPTDate object from wrong day value."""
        with self.assertRaises(ConversionError):
            DPTDate().to_knx({
                'year': 2002,
                'month': 1,
                'day': 32
            })

    def test_to_knx_wrong_year(self):
        """Test parsing from DPTDate object from wrong year value."""
        with self.assertRaises(ConversionError):
            DPTDate().to_knx({
                'year': 2091,
                'month': 1,
                'day': 20
            })

    def test_to_knx_wrong_month(self):
        """Test parsing from DPTDate object from wrong month value."""
        with self.assertRaises(ConversionError):
            DPTDate().to_knx({
                'year': 2002,
                'month': 0,
                'day': 20
            })

    def test_from_knx_wrong_range_month(self):
        """Test Exception when parsing DPTDAte from KNX with wrong month."""
        with self.assertRaises(ConversionError):
            DPTDate().from_knx((0x04, 0x00, 0x59))

    def test_from_knx_wrong_range_year(self):
        """Test Exception when parsing DPTDate from KNX with wrong year."""
        with self.assertRaises(ConversionError):
            DPTDate().from_knx((0x04, 0x01, 0x64))
