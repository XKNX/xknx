"""Unit test for KNX/IP TunnellingAck objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import DisconnectRequest, KNXIPHeader, KNXIPServiceType


class Test_KNXIP_Header(unittest.TestCase):
    """Test class for KNX/IP TunnellingAck objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_from_knx(self):
        """Test parsing and streaming wrong Header (wrong length byte)."""
        raw = ((0x06, 0x10, 0x04, 0x21, 0x00, 0x0a))
        xknx = XKNX(loop=self.loop)
        header = KNXIPHeader(xknx)
        self.assertEqual(header.from_knx(raw), 6)
        self.assertEqual(header.header_length, 6)
        self.assertEqual(header.protocol_version, 16)
        self.assertEqual(header.service_type_ident, KNXIPServiceType.TUNNELLING_ACK)
        self.assertEqual(header.b4_reserve, 0)
        self.assertEqual(header.total_length, 10)
        self.assertEqual(header.to_knx(), list(raw))

    def test_set_length(self):
        """Test setting length."""
        xknx = XKNX(loop=self.loop)
        header = KNXIPHeader(xknx)
        header.set_length(DisconnectRequest(xknx))
        # 6 (header) + 2 + 8 (HPAI length)
        self.assertEqual(header.total_length, 16)

    def test_set_length_error(self):
        """Test setting length with wrong type."""
        xknx = XKNX(loop=self.loop)
        header = KNXIPHeader(xknx)
        with self.assertRaises(TypeError):
            header.set_length(2)

    def test_from_knx_wrong_header(self):
        """Test parsing and streaming wrong Header (wrong length)."""
        raw = ((0x06, 0x10, 0x04, 0x21, 0x00))
        xknx = XKNX(loop=self.loop)
        header = KNXIPHeader(xknx)
        with self.assertRaises(CouldNotParseKNXIP):
            header.from_knx(raw)

    def test_from_knx_wrong_header2(self):
        """Test parsing and streaming wrong Header (wrong length byte)."""
        raw = ((0x05, 0x10, 0x04, 0x21, 0x00, 0x0a))
        xknx = XKNX(loop=self.loop)
        header = KNXIPHeader(xknx)
        with self.assertRaises(CouldNotParseKNXIP):
            header.from_knx(raw)

    def test_from_knx_wrong_header3(self):
        """Test parsing and streaming wrong Header (wrong protocol version)."""
        raw = ((0x06, 0x11, 0x04, 0x21, 0x00, 0x0a))
        xknx = XKNX(loop=self.loop)
        header = KNXIPHeader(xknx)
        with self.assertRaises(CouldNotParseKNXIP):
            header.from_knx(raw)
