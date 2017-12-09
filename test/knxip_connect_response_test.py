"""Unit test for KNX/IP ConnectResponses."""
import asyncio
import unittest

from xknx import XKNX
from xknx.knxip import (HPAI, ConnectRequestType, ConnectResponse, ErrorCode,
                        KNXIPFrame, KNXIPServiceType)


class Test_KNXIP_ConnectResponse(unittest.TestCase):
    """Test class for KNX/IP ConnectResponses."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_connect_response(self):
        """Test parsing and streaming connection response KNX/IP packet."""
        raw = ((0x06, 0x10, 0x02, 0x06, 0x00, 0x14, 0x01, 0x00,
                0x08, 0x01, 0xc0, 0xa8, 0x2a, 0x0a, 0x0e, 0x57,
                0x04, 0x04, 0x11, 0xff))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        self.assertTrue(isinstance(knxipframe.body, ConnectResponse))
        self.assertEqual(knxipframe.body.communication_channel, 1)
        self.assertEqual(
            knxipframe.body.status_code,
            ErrorCode.E_NO_ERROR)
        self.assertEqual(
            knxipframe.body.control_endpoint,
            HPAI(ip_addr='192.168.42.10', port=3671))
        self.assertEqual(
            knxipframe.body.request_type,
            ConnectRequestType.TUNNEL_CONNECTION)
        self.assertEqual(knxipframe.body.identifier, 4607)

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.CONNECT_RESPONSE)
        knxipframe2.status_code = ErrorCode.E_NO_ERROR
        knxipframe2.body.communication_channel = 1
        knxipframe2.body.request_type = ConnectRequestType.TUNNEL_CONNECTION
        knxipframe2.body.control_endpoint = HPAI(
            ip_addr='192.168.42.10', port=3671)
        knxipframe2.body.identifier = 4607
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))
