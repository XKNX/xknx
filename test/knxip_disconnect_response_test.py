"""Unit test for KNX/IP DisconnectResponse objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.knxip import (DisconnectResponse, ErrorCode, KNXIPFrame,
                        KNXIPServiceType)


class Test_KNXIP_DisconnectResp(unittest.TestCase):
    """Test class for KNX/IP DisconnectResponse objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_disconnect_response(self):
        """Test parsing and streaming DisconnectResponse KNX/IP packet."""
        raw = ((0x06, 0x10, 0x02, 0x0A, 0x00, 0x08, 0x15, 0x25))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, DisconnectResponse))

        self.assertEqual(
            knxipframe.body.communication_channel_id, 21)
        self.assertEqual(
            knxipframe.body.status_code, ErrorCode.E_NO_MORE_UNIQUE_CONNECTIONS)

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.DISCONNECT_RESPONSE)
        knxipframe2.body.communication_channel_id = 21
        knxipframe2.body.status_code = ErrorCode.E_NO_MORE_UNIQUE_CONNECTIONS
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))
