"""Unit test for KNX time objects."""
import unittest

from xknx.dpt import DPTTime, DPTWeekday
from xknx.exceptions import ConversionError


class TestDPTTime(unittest.TestCase):
    """Test class for KNX time objects."""

    #
    # TEST NORMAL TIME
    #
    def test_from_knx(self):
        """Test parsing of DPTTime object from binary values. Example 1."""
        self.assertEqual(DPTTime().from_knx((0x4D, 0x17, 0x2A)),
                         {'weekday': DPTWeekday.TUESDAY,
                          'hours': 13,
                          'minutes': 23,
                          'seconds': 42})

    def test_to_knx(self):
        """Testing KNX/Byte representation of DPTTime object."""
        raw = DPTTime().to_knx(
            {'weekday': DPTWeekday.TUESDAY,
             'hours': 13,
             'minutes': 23,
             'seconds': 42})
        self.assertEqual(raw, (0x4D, 0x17, 0x2A))

    #
    # TEST MAXIMUM TIME
    #
    def test_to_knx_max(self):
        """Testing KNX/Byte representation of DPTTime object. Maximum values."""
        raw = DPTTime().to_knx(
            {'weekday': DPTWeekday.SUNDAY,
             'hours': 23,
             'minutes': 59,
             'seconds': 59})
        self.assertEqual(raw, (0xF7, 0x3b, 0x3b))

    def test_from_knx_max(self):
        """Test parsing of DPTTime object from binary values. Example 2."""
        self.assertEqual(DPTTime().from_knx((0xF7, 0x3b, 0x3b)),
                         {'weekday': DPTWeekday.SUNDAY,
                          'hours': 23,
                          'minutes': 59,
                          'seconds': 59})

    #
    # TEST MINIMUM TIME
    #
    def test_to_knx_min(self):
        """Testing KNX/Byte representation of DPTTime object. Minimum values."""
        raw = DPTTime().to_knx(
            {'weekday': DPTWeekday.NONE,
             'hours': 0,
             'minutes': 0,
             'seconds': 0})
        self.assertEqual(raw, (0x0, 0x0, 0x0))

    def test_from_knx_min(self):
        """Test parsing of DPTTime object from binary values. Example 3."""
        self.assertEqual(DPTTime().from_knx((0x0, 0x0, 0x0)),
                         {'weekday': DPTWeekday.NONE,
                          'hours': 0,
                          'minutes': 0,
                          'seconds': 0})

    #
    # TEST INITIALIZATION
    #
    def test_to_knx_default(self):
        """Testing default initialization of DPTTime object."""
        self.assertEqual(DPTTime().to_knx({}), (0x0, 0x0, 0x0))

    def test_from_knx_wrong_size(self):
        """Test parsing from DPTTime object from wrong binary values (wrong size)."""
        with self.assertRaises(ConversionError):
            DPTTime().from_knx((0xF8, 0x23))

    def test_from_knx_wrong_bytes(self):
        """Test parsing from DPTTime object from wrong binary values (wrong bytes)."""
        with self.assertRaises(ConversionError):
            # thirs parameter exceeds limit
            DPTTime().from_knx((0xF7, 0x3b, 0x3c))

    def test_from_knx_wrong_type(self):
        """Test parsing from DPTTime object from wrong binary values (wrong type)."""
        with self.assertRaises(ConversionError):
            DPTTime().from_knx((0xF8, "0x23"))

    def test_to_knx_wrong_parameter(self):
        """Test parsing from DPTTime object from wrong string value."""
        with self.assertRaises(ConversionError):
            DPTTime().to_knx("fnord")

    def test_to_knx_wrong_seconds(self):
        """Test parsing from DPTTime object from wrong seconds value."""
        with self.assertRaises(ConversionError):
            DPTTime().to_knx({
                'hours': 12,
                'minutes': 42,
                'seconds': 61
            })

    def test_to_knx_wrong_minutes(self):
        """Test parsing from DPTTime object from wrong minutes value."""
        with self.assertRaises(ConversionError):
            DPTTime().to_knx({
                'hours': 12,
                'minutes': 61,
                'seconds': 53
            })

    def test_to_knx_wrong_hours(self):
        """Test parsing from DPTTime object from wrong hours value."""
        with self.assertRaises(ConversionError):
            DPTTime().to_knx({
                'hours': 24,
                'minutes': 42,
                'seconds': 53
            })

    def test_test_range_wrong_weekday(self):
        """Test range testing with wrong weekday (Cant be tested with normal from_/to_knx)."""
        # pylint: disable=protected-access
        self.assertFalse(DPTTime._test_range(8, 0, 0, 0))
