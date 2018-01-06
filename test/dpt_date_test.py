"""Unit test for KNX date objects."""
import unittest

from xknx.exceptions import ConversionError
from xknx.knx import DPTDate


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

    def test_to_knx(self):
        """Testing KNX/Byte representation of DPTDate object."""
        raw = DPTDate().to_knx({
            'year': 2002,
            'month': 1,
            'day': 4
        })
        self.assertEqual(raw, (0x04, 0x01, 0x02))

    def test_from_knx_wrong_parameter(self):
        """Test parsing from DPTDate object from wrong binary values."""
        with self.assertRaises(ConversionError):
            DPTDate().from_knx((0xF8, 0x23))

    def test_to_knx_wrong_parameter(self):
        """Test parsing from DPTDate object from wrong string value."""
        with self.assertRaises(ConversionError):
            DPTDate().to_knx("hello")


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestDPTDate)
unittest.TextTestRunner(verbosity=2).run(SUITE)
