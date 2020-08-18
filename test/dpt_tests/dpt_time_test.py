"""Unit test for KNX time objects."""
import time
import unittest

from xknx.dpt import DPTTime
from xknx.exceptions import ConversionError


class TestDPTTime(unittest.TestCase):
    """Test class for KNX time objects."""

    #
    # TEST NORMAL TIME
    #
    def test_from_knx(self):
        """Test parsing of DPTTime object from binary values. Example 1."""
        self.assertEqual(
            DPTTime().from_knx((0x4D, 0x17, 0x2A)),
            time.strptime("13 23 42 2", "%H %M %S %w")
        )

    def test_to_knx(self):
        """Testing KNX/Byte representation of DPTTime object."""
        raw = DPTTime().to_knx(
            time.strptime("13 23 42 2", "%H %M %S %w"))
        self.assertEqual(raw, (0x4D, 0x17, 0x2A))

    #
    # TEST MAXIMUM TIME
    #
    def test_to_knx_max(self):
        """Testing KNX/Byte representation of DPTTime object. Maximum values."""
        raw = DPTTime().to_knx(
            time.strptime("23 59 59 0", "%H %M %S %w"))
        self.assertEqual(raw, (0xF7, 0x3b, 0x3b))

    def test_from_knx_max(self):
        """Test parsing of DPTTime object from binary values. Example 2."""
        self.assertEqual(
            DPTTime().from_knx((0xF7, 0x3b, 0x3b)),
            time.strptime("23 59 59 0", "%H %M %S %w")
        )

    #
    # TEST MINIMUM TIME
    #
    def test_to_knx_min(self):
        """Testing KNX/Byte representation of DPTTime object. Minimum values."""
        raw = DPTTime().to_knx(
            time.strptime("0 0 0", "%H %M %S"))
        self.assertEqual(raw, (0x0, 0x0, 0x0))

    def test_from_knx_min(self):
        """Test parsing of DPTTime object from binary values. Example 3."""
        self.assertEqual(
            DPTTime().from_knx((0x0, 0x0, 0x0)),
            time.strptime("0 0 0", "%H %M %S")
        )

    #
    # TEST INITIALIZATION
    #
    def test_to_knx_default(self):
        """Testing default initialization of DPTTime object."""
        self.assertEqual(
            DPTTime().to_knx(time.strptime("", "")),
            (0x0, 0x0, 0x0)
        )

    def test_from_knx_wrong_size(self):
        """Test parsing from DPTTime object from wrong binary values (wrong size)."""
        with self.assertRaises(ConversionError):
            DPTTime().from_knx((0xF8, 0x23))

    def test_from_knx_wrong_bytes(self):
        """Test parsing from DPTTime object from wrong binary values (wrong bytes)."""
        with self.assertRaises(ConversionError):
            # this parameter exceeds limit
            DPTTime().from_knx((0xF7, 0x3b, 0x3c))

    def test_from_knx_wrong_type(self):
        """Test parsing from DPTTime object from wrong binary values (wrong type)."""
        with self.assertRaises(ConversionError):
            DPTTime().from_knx((0xF8, "0x23"))

    def test_to_knx_wrong_parameter(self):
        """Test parsing from DPTTime object from wrong string value."""
        with self.assertRaises(ConversionError):
            DPTTime().to_knx("fnord")
