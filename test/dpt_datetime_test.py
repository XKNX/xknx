"""Unit test for KNX datetime objects."""
import unittest

from xknx.exceptions import ConversionError
from xknx.knx import DPTDateTime, DPTWeekday


class TestDPTDateTime(unittest.TestCase):
    """Test class for KNX datetime objects."""

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

    def test_from_knx_wrong_parameter(self):
        """Test parsing from DPTDateTime object from wrong binary values."""
        with self.assertRaises(ConversionError):
            DPTDateTime().from_knx((0xF8, 0x23))

    def test_to_knx_wrong_parameter(self):
        """Test parsing from DPTDateTime object from wrong string value."""
        with self.assertRaises(ConversionError):
            DPTDateTime().to_knx("hello")


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestDPTDateTime)
unittest.TextTestRunner(verbosity=2).run(SUITE)
