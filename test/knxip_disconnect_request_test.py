"""Unit test for KNX/IP Disconnect objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.knxip import HPAI, DisconnectRequest, KNXIPFrame, KNXIPServiceType


class Test_KNXIP_DisconnectReq(unittest.TestCase):
    """Test class for KNX/IP Disconnect objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_disconnect_request(self):
        """Test parsing and streaming DisconnectRequest KNX/IP packet."""
        raw = ((0x06, 0x10, 0x02, 0x09, 0x00, 0x10, 0x15, 0x00,
                0x08, 0x01, 0xC0, 0xA8, 0xC8, 0x0C, 0xC3, 0xB4))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, DisconnectRequest))

        self.assertEqual(
            knxipframe.body.communication_channel_id, 21)
        self.assertEqual(
            knxipframe.body.control_endpoint,
            HPAI(ip_addr='192.168.200.12', port=50100))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.DISCONNECT_REQUEST)
        knxipframe2.body.communication_channel_id = 21
        knxipframe2.body.control_endpoint = HPAI(
            ip_addr='192.168.200.12', port=50100)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))
