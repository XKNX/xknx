"""Unit test for KNX string object."""
import unittest

from xknx.dpt import DPTString
from xknx.exceptions import ConversionError


class TestDPTString(unittest.TestCase):
    """Test class for KNX float object."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_value_from_documentation(self):
        """Test parsing and streaming Example from documentation."""
        raw = [0x4B, 0x4E, 0x58, 0x20, 0x69,
               0x73, 0x20, 0x4F, 0x4B, 0x00,
               0x00, 0x00, 0x00, 0x00]
        string = 'KNX is OK'
        self.assertEqual(DPTString.to_knx(string), raw)
        self.assertEqual(DPTString.from_knx(raw), string)

    def test_value_empty_string(self):
        """Test parsing and streaming empty string."""
        raw = [0x00, 0x00, 0x00, 0x00, 0x00,
               0x00, 0x00, 0x00, 0x00, 0x00,
               0x00, 0x00, 0x00, 0x00]
        string = ''
        self.assertEqual(DPTString.to_knx(string), raw)
        self.assertEqual(DPTString.from_knx(raw), string)

    def test_value_max_string(self):
        """Test parsing and streaming large string."""
        raw = [0x41, 0x41, 0x41, 0x41, 0x41,
               0x42, 0x42, 0x42, 0x42, 0x42,
               0x43, 0x43, 0x43, 0x43]
        string = 'AAAAABBBBBCCCC'
        self.assertEqual(DPTString.to_knx(string), raw)
        self.assertEqual(DPTString.from_knx(raw), string)

    def test_value_special_chars(self):
        """Test parsing and streaming string with special chars."""
        raw = [0x48, 0x65, 0x79, 0x21, 0x3f,
               0x24, 0x20, 0xc4, 0xd6, 0xdc,
               0xe4, 0xf6, 0xfc, 0xdf]
        string = 'Hey!?$ ÄÖÜäöüß'
        self.assertEqual(DPTString.to_knx(string), raw)
        self.assertEqual(DPTString.from_knx(raw), string)

    def test_to_knx_too_long(self):
        """Test serializing DPTString to KNX with wrong value (to long)."""
        with self.assertRaises(ConversionError):
            DPTString().to_knx("AAAAABBBBBCCCCx")

    def test_from_knx_wrong_parameter_too_large(self):
        """Test parsing of KNX string with too many elements."""
        raw = [0x00, 0x00, 0x00, 0x00, 0x00,
               0x00, 0x00, 0x00, 0x00, 0x00,
               0x00, 0x00, 0x00, 0x00, 0x00]
        with self.assertRaises(ConversionError):
            DPTString().from_knx(raw)

    def test_from_knx_wrong_parameter_too_small(self):
        """Test parsing of KNX string with too less elements."""
        raw = [0x00, 0x00, 0x00, 0x00, 0x00,
               0x00, 0x00, 0x00, 0x00, 0x00,
               0x00, 0x00, 0x00]
        with self.assertRaises(ConversionError):
            DPTString().from_knx(raw)
