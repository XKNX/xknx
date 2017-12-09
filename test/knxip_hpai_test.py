"""Unit test for KNX/IP HPAI objects."""
import unittest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import HPAI


class Test_KNXIP_HPAI(unittest.TestCase):
    """Test class for KNX/IP HPAI objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_hpai(self):
        """Test parsing and streaming HPAI KNX/IP fragment."""
        raw = ((0x08, 0x01, 0xc0, 0xa8, 0x2a, 0x01, 0x84, 0x95))

        hpai = HPAI()
        self.assertEqual(hpai.from_knx(raw), 8)
        self.assertEqual(hpai.ip_addr, '192.168.42.1')
        self.assertEqual(hpai.port, 33941)

        hpai2 = HPAI(ip_addr='192.168.42.1', port=33941)
        self.assertEqual(hpai2.to_knx(), list(raw))

    def test_hpai_wrong_input(self):
        """Test parsing of wrong HPAI KNX/IP packet."""
        raw = ((0x08, 0x01, 0xc0, 0xa8, 0x2a))

        with self.assertRaises(CouldNotParseKNXIP):
            HPAI().from_knx(raw)
