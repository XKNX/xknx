"""Unit test for KNX/IP HPAI objects."""
import unittest

from xknx.exceptions import ConversionError, CouldNotParseKNXIP
from xknx.knxip import HPAI


class Test_KNXIP_HPAI(unittest.TestCase):
    """Test class for KNX/IP HPAI objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_hpai(self):
        """Test parsing and streaming HPAI KNX/IP fragment."""
        raw = (0x08, 0x01, 0xC0, 0xA8, 0x2A, 0x01, 0x84, 0x95)

        hpai = HPAI()
        self.assertEqual(hpai.from_knx(raw), 8)
        self.assertEqual(hpai.ip_addr, "192.168.42.1")
        self.assertEqual(hpai.port, 33941)

        hpai2 = HPAI(ip_addr="192.168.42.1", port=33941)
        self.assertEqual(hpai2.to_knx(), list(raw))

    def test_from_knx_wrong_input1(self):
        """Test parsing of wrong HPAI KNX/IP packet (wrong length)."""
        raw = (0x08, 0x01, 0xC0, 0xA8, 0x2A)
        with self.assertRaises(CouldNotParseKNXIP):
            HPAI().from_knx(raw)

    def test_from_knx_wrong_input2(self):
        """Test parsing of wrong HPAI KNX/IP packet (wrong length byte)."""
        raw = (0x09, 0x01, 0xC0, 0xA8, 0x2A, 0x01, 0x84, 0x95)
        with self.assertRaises(CouldNotParseKNXIP):
            HPAI().from_knx(raw)

    def test_from_knx_wrong_input3(self):
        """Test parsing of wrong HPAI KNX/IP packet (wrong HPAI type)."""
        raw = (0x08, 0x02, 0xC0, 0xA8, 0x2A, 0x01, 0x84, 0x95)
        with self.assertRaises(CouldNotParseKNXIP):
            HPAI().from_knx(raw)

    def test_to_knx_wrong_ip(self):
        """Test serializing HPAI to KNV/IP with wrong ip type."""
        hpai = HPAI(ip_addr=127001)
        with self.assertRaises(ConversionError):
            hpai.to_knx()
