"""Unit test for KNX/IP TunnelingRequest objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.knx import GroupAddress, DPTBinary, Telegram
from xknx.knxip import (CEMIFrame, KNXIPFrame, KNXIPServiceType,
                        TunnellingRequest)


class Test_KNXIP_TunnelingReq(unittest.TestCase):
    """Test class for KNX/IP TunelingRequest objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_connect_request(self):
        """Test parsing and streaming connection tunneling request KNX/IP packet."""
        raw = ((0x06, 0x10, 0x04, 0x20, 0x00, 0x15, 0x04, 0x01,
                0x17, 0x00, 0x11, 0x00, 0xbc, 0xe0, 0x00, 0x00,
                0x48, 0x08, 0x01, 0x00, 0x81))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, TunnellingRequest))
        self.assertEqual(knxipframe.body.communication_channel_id, 1)
        self.assertEqual(knxipframe.body.sequence_counter, 23)
        self.assertTrue(isinstance(knxipframe.body.cemi, CEMIFrame))

        self.assertEqual(knxipframe.body.cemi.telegram,
                         Telegram(GroupAddress('9/0/8'), payload=DPTBinary(1)))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.TUNNELLING_REQUEST)
        knxipframe2.body.cemi.telegram = Telegram(
            GroupAddress('9/0/8'), payload=DPTBinary(1))
        knxipframe2.body.sequence_counter = 23
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))
