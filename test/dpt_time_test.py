"""Unit test for KNX time objects."""
import unittest

from xknx.exceptions import ConversionError
from xknx.knx import DPTTime, DPTWeekday


class TestDPTTime(unittest.TestCase):
    """Test class for KNX time objects."""

    def test_from_knx(self):
        """Test parsing of DPTTime object from binary values. Example 1."""
        self.assertEqual(DPTTime().from_knx((0x4D, 0x17, 0x2A)),
                         {'weekday': DPTWeekday.TUESDAY,
                          'hours': 13,
                          'minutes': 23,
                          'seconds': 42})

    def test_from_knx_max(self):
        """Test parsing of DPTTime object from binary values. Example 2."""
        self.assertEqual(DPTTime().from_knx((0xF7, 0x3b, 0x3b)),
                         {'weekday': DPTWeekday.SUNDAY,
                          'hours': 23,
                          'minutes': 59,
                          'seconds': 59})

    def test_from_knx_min(self):
        """Test parsing of DPTTime object from binary values. Example 3."""
        self.assertEqual(DPTTime().from_knx((0x0, 0x0, 0x0)),
                         {'weekday': DPTWeekday.NONE,
                          'hours': 0,
                          'minutes': 0,
                          'seconds': 0})

    def test_to_knx(self):
        """Testing KNX/Byte representation of DPTTime object."""
        raw = DPTTime().to_knx(
            {'weekday': DPTWeekday.TUESDAY,
             'hours': 13,
             'minutes': 23,
             'seconds': 42})
        self.assertEqual(raw, (0x4D, 0x17, 0x2A))

    def test_to_knx_max(self):
        """Testing KNX/Byte representation of DPTTime object. Maximum values."""
        raw = DPTTime().to_knx(
            {'weekday': DPTWeekday.SUNDAY,
             'hours': 23,
             'minutes': 59,
             'seconds': 59})
        self.assertEqual(raw, (0xF7, 0x3b, 0x3b))

    def test_to_knx_min(self):
        """Testing KNX/Byte representation of DPTTime object. Minimum values."""
        raw = DPTTime().to_knx(
            {'weekday': DPTWeekday.NONE,
             'hours': 0,
             'minutes': 0,
             'seconds': 0})
        self.assertEqual(raw, (0x0, 0x0, 0x0))

    def test_to_knx_default(self):
        """Testing default initialization of DPTTime object."""
        self.assertEqual(DPTTime().to_knx({}), (0x0, 0x0, 0x0))

    def test_from_knx_wrong_parameter(self):
        """Test parsing from DPTTime object from wrong binary values."""
        with self.assertRaises(ConversionError):
            DPTTime().from_knx((0xF8, 0x23))

    def test_from_knx_wrong_parameter2(self):
        """Test parsing from DPTTime object from wrong binary values."""
        with self.assertRaises(ConversionError):
            DPTTime().from_knx((0xF8, "0x23"))

    def test_to_knx_wrong_parameter(self):
        """Test parsing from DPTTime object from wrong string value."""
        with self.assertRaises(ConversionError):
            DPTTime().to_knx("fnord")
