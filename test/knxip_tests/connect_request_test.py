"""Unit test for KNX/IP ConnectRequests."""
import asyncio
import unittest

from xknx import XKNX
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import (
    HPAI,
    ConnectRequest,
    ConnectRequestType,
    KNXIPFrame,
    KNXIPServiceType,
)


class Test_KNXIP_ConnectRequest(unittest.TestCase):
    """Test class for KNX/IP ConnectRequests."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_connect_request(self):
        """Test parsing and streaming connection request KNX/IP packet."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x05,
            0x00,
            0x1A,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0x84,
            0x95,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0xCC,
            0xA9,
            0x04,
            0x04,
            0x02,
            0x00,
        )
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, ConnectRequest))
        self.assertEqual(
            knxipframe.body.request_type, ConnectRequestType.TUNNEL_CONNECTION
        )
        self.assertEqual(
            knxipframe.body.control_endpoint, HPAI(ip_addr="192.168.42.1", port=33941)
        )
        self.assertEqual(
            knxipframe.body.data_endpoint, HPAI(ip_addr="192.168.42.1", port=52393)
        )

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.CONNECT_REQUEST)
        knxipframe2.body.request_type = ConnectRequestType.TUNNEL_CONNECTION
        knxipframe2.body.control_endpoint = HPAI(ip_addr="192.168.42.1", port=33941)
        knxipframe2.body.data_endpoint = HPAI(ip_addr="192.168.42.1", port=52393)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_from_knx_wrong_length_of_cri(self):
        """Test parsing and streaming wrong ConnectRequest."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x05,
            0x00,
            0x1A,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0x84,
            0x95,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0xCC,
            0xA9,
            0x02,
            0x04,
            0x02,
            0x00,
        )
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        with self.assertRaises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)

    def test_from_knx_wrong_cri(self):
        """Test parsing and streaming wrong ConnectRequest."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x05,
            0x00,
            0x1A,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0x84,
            0x95,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0xCC,
            0xA9,
            0x04,
            0x04,
            0x02,
        )
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        with self.assertRaises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)
