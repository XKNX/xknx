"""Unit test for KNX/IP SearchRequest objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.knxip import HPAI, KNXIPFrame, KNXIPServiceType, SearchRequest


class Test_KNXIP_Discovery(unittest.TestCase):
    """Test class for KNX/IP SearchRequest objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_connect_request(self):
        """Test parsing and streaming SearchRequest KNX/IP packet."""
        raw = ((0x06, 0x10, 0x02, 0x01, 0x00, 0x0e, 0x08, 0x01,
                0xe0, 0x00, 0x17, 0x0c, 0x0e, 0x57))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, SearchRequest))
        self.assertEqual(
            knxipframe.body.discovery_endpoint,
            HPAI(ip_addr="224.0.23.12", port=3671))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.SEARCH_REQUEST)
        knxipframe2.body.discovery_endpoint = \
            HPAI(ip_addr="224.0.23.12", port=3671)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))
