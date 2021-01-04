"""Unit test for KNX/IP ConnectionStateResponses."""
import asyncio
import unittest

from xknx import XKNX
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import ConnectionStateResponse, ErrorCode, KNXIPFrame


class Test_KNXIP_ConnStateResp(unittest.TestCase):
    """Test class for KNX/IP ConnectionStateResponses."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_disconnect_response(self):
        """Test parsing and streaming connection state response KNX/IP packet."""
        raw = (0x06, 0x10, 0x02, 0x08, 0x00, 0x08, 0x15, 0x21)
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, ConnectionStateResponse))

        self.assertEqual(knxipframe.body.communication_channel_id, 21)
        self.assertEqual(knxipframe.body.status_code, ErrorCode.E_CONNECTION_ID)

        connectionstate_response = ConnectionStateResponse(
            xknx, communication_channel_id=21, status_code=ErrorCode.E_CONNECTION_ID
        )
        knxipframe2 = KNXIPFrame.init_from_body(connectionstate_response)

        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_from_knx_wrong_header(self):
        """Test parsing and streaming wrong ConnectionStateResponse (wrong header length)."""
        raw = (0x06, 0x10, 0x02, 0x08, 0x00, 0x08, 0x15)
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with self.assertRaises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)
