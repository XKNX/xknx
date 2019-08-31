"""Unit test for KNX datetime objects."""
import unittest

from xknx.dpt import DPTDateTime, DPTWeekday
from xknx.exceptions import ConversionError


class TestDPTDateTime(unittest.TestCase):
    """Test class for KNX datetime objects."""

    #
    # TEST CURRENT DATE
    #
    def test_from_knx(self):
        """Test parsing of DPTDateTime object from binary values. Example 1."""
        self.assertEqual(
            DPTDateTime().from_knx((0x75, 0x0B, 0x1C, 0x17, 0x07, 0x18, 0x00, 0x00)), {
                'year': 2017,
                'month': 11,
                'day': 28,
                'weekday': DPTWeekday.NONE,
                'hours': 23,
                'minutes': 7,
                'seconds': 24
            })

    def test_to_knx(self):
        """Testing KNX/Byte representation of DPTDateTime object."""
        raw = DPTDateTime().to_knx({
            'year': 2017,
            'month': 11,
            'day': 28,
            'weekday': DPTWeekday.NONE,
            'hours': 23,
            'minutes': 7,
            'seconds': 24
        })
        self.assertEqual(raw, (0x75, 0x0B, 0x1C, 0x17, 0x07, 0x18, 0x00, 0x00))

    #
    # TEST EARLIEST DATE POSSIBLE
    #
    def test_from_knx_date_in_past(self):
        """Test parsing of DPTDateTime object from binary values. Example 1."""
        self.assertEqual(
            DPTDateTime().from_knx((0x00, 0x1, 0x1, 0x20, 0x00, 0x00, 0x00, 0x00)), {
                'year': 1900,
                'month': 1,
                'day': 1,
                'weekday': DPTWeekday.MONDAY,
                'hours': 0,
                'minutes': 0,
                'seconds': 0
            })

    def test_to_knx_date_in_past(self):
        """Testing KNX/Byte representation of DPTDateTime object."""
        raw = DPTDateTime().to_knx({
            'year': 1900,
            'month': 1,
            'day': 1,
            'weekday': DPTWeekday.MONDAY,
            'hours': 0,
            'minutes': 0,
            'seconds': 0
        })
        self.assertEqual(raw, (0x00, 0x1, 0x1, 0x20, 0x00, 0x00, 0x00, 0x00))

    #
    # TEST LATEST DATE IN THE FUTURE
    #
    def test_from_knx_date_in_future(self):
        """Test parsing of DPTDateTime object from binary values. Example 1."""
        self.assertEqual(
            DPTDateTime().from_knx((0xFF, 0x0C, 0x1F, 0xF7, 0x3B, 0x3B, 0x00, 0x00)), {
                'year': 2155,
                'month': 12,
                'day': 31,
                'weekday': DPTWeekday.SUNDAY,
                'hours': 23,
                'minutes': 59,
                'seconds': 59
            })

    def test_to_knx_date_in_future(self):
        """Testing KNX/Byte representation of DPTDateTime object."""
        raw = DPTDateTime().to_knx({
            'year': 2155,
            'month': 12,
            'day': 31,
            'weekday': DPTWeekday.SUNDAY,
            'hours': 23,
            'minutes': 59,
            'seconds': 59
        })
        self.assertEqual(raw, (0xFF, 0x0C, 0x1F, 0xF7, 0x3B, 0x3B, 0x00, 0x00))

    #
    # TEST WRONG KNX
    #
    def test_from_knx_wrong_size(self):
        """Test parsing DPTDateTime from KNX with wrong binary values (wrong size)."""
        with self.assertRaises(ConversionError):
            DPTDateTime().from_knx((0xF8, 0x23))

    def test_from_knx_wrong_bytes(self):
        """Test parsing DPTDateTime from KNX with wrong binary values (wrong bytes)."""
        with self.assertRaises(ConversionError):
            # (second byte exceeds value...)
            DPTDateTime().from_knx((0xFF, 0x0D, 0x1F, 0xF7, 0x3B, 0x3B, 0x00, 0x00))

    #
    # TEST WRONG PARAMETER
    #
    def test_to_knx_wrong_parameter(self):
        """Test parsing from DPTDateTime object from wrong string value."""
        with self.assertRaises(ConversionError):
            DPTDateTime().to_knx("hello")

    def test_to_knx_wrong_seconds(self):
        """Test parsing from DPTDateTime object from wrong seconds value."""
        with self.assertRaises(ConversionError):
            DPTDateTime().to_knx({
                'year': 2002,
                'month': 2,
                'day': 20,
                'hours': 12,
                'minutes': 42,
                'seconds': 61
            })

    def test_to_knx_wrong_minutes(self):
        """Test parsing from DPTDateTime object from wrong minutes value."""
        with self.assertRaises(ConversionError):
            DPTDateTime().to_knx({
                'year': 2002,
                'month': 12,
                'day': 20,
                'hours': 12,
                'minutes': 61,
                'seconds': 53
            })

    def test_to_knx_wrong_hours(self):
        """Test parsing from DPTDateTime object from wrong hours value."""
        with self.assertRaises(ConversionError):
            DPTDateTime().to_knx({
                'year': 2002,
                'month': 2,
                'day': 20,
                'hours': 24,
                'minutes': 42,
                'seconds': 53
            })

    def test_to_knx_wrong_day(self):
        """Test parsing from DPTDateTime object from wrong day value."""
        with self.assertRaises(ConversionError):
            DPTDateTime().to_knx({
                'year': 2002,
                'month': 1,
                'day': 32,
                'hours': 12,
                'minutes': 42,
                'seconds': 53
            })

    def test_to_knx_wrong_year(self):
        """Test parsing from DPTDateTime object from wrong year value."""
        with self.assertRaises(ConversionError):
            DPTDateTime().to_knx({
                'year': 2156,
                'month': 1,
                'day': 20,
                'hours': 12,
                'minutes': 42,
                'seconds': 53
            })

    def test_to_knx_wrong_month(self):
        """Test parsing from DPTDateTime object from wrong month value."""
        with self.assertRaises(ConversionError):
            DPTDateTime().to_knx({
                'year': 2002,
                'month': 0,
                'day': 20,
                'hours': 12,
                'minutes': 42,
                'seconds': 53
            })

    def test_test_range_wrong_weekday(self):
        """Test range testing with wrong weekday (Cant be tested with normal from_/to_knx)."""
        # pylint: disable=protected-access
        self.assertFalse(DPTDateTime._test_range(1900, 1, 1, 8, 0, 0, 0))
