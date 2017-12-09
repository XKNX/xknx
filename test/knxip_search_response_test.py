"""Unit test for KNX/IP SearchResponse objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.knxip import (HPAI, DIBDeviceInformation, DIBServiceFamily,
                        DIBSuppSVCFamilies, KNXIPFrame, KNXIPServiceType,
                        SearchResponse)


class Test_KNXIP_Discovery(unittest.TestCase):
    """Test class for KNX/IP SearchResponse objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_connect_request(self):
        """Test parsing and streaming SearchResponse KNX/IP packet."""
        raw = ((0x06, 0x10, 0x02, 0x02, 0x00, 0x50, 0x08, 0x01,
                0xc0, 0xa8, 0x2a, 0x0a, 0x0e, 0x57, 0x36, 0x01,
                0x02, 0x00, 0x11, 0x00, 0x00, 0x00, 0x11, 0x22,
                0x33, 0x44, 0x55, 0x66, 0xe0, 0x00, 0x17, 0x0c,
                0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x47, 0x69,
                0x72, 0x61, 0x20, 0x4b, 0x4e, 0x58, 0x2f, 0x49,
                0x50, 0x2d, 0x52, 0x6f, 0x75, 0x74, 0x65, 0x72,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x0c, 0x02, 0x02, 0x01,
                0x03, 0x02, 0x04, 0x01, 0x05, 0x01, 0x07, 0x01))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        self.assertEqual(knxipframe.from_knx(raw), 80)
        self.assertEqual(knxipframe.to_knx(), list(raw))

        self.assertTrue(isinstance(knxipframe.body, SearchResponse))
        self.assertEqual(
            knxipframe.body.control_endpoint,
            HPAI("192.168.42.10", 3671))
        self.assertEqual(len(knxipframe.body.dibs), 2)
        # Specific testing of parsing and serializing of
        # DIBDeviceInformation and DIBSuppSVCFamilies is
        # done within knxip_dib_test.py
        self.assertTrue(isinstance(
            knxipframe.body.dibs[0], DIBDeviceInformation))
        self.assertTrue(isinstance(
            knxipframe.body.dibs[1], DIBSuppSVCFamilies))
        self.assertEqual(knxipframe.body.device_name, "Gira KNX/IP-Router")
        self.assertTrue(knxipframe.body.dibs[1].supports(DIBServiceFamily.ROUTING))
        self.assertTrue(knxipframe.body.dibs[1].supports(DIBServiceFamily.TUNNELING))
        self.assertFalse(knxipframe.body.dibs[1].supports(DIBServiceFamily.OBJECT_SERVER))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.SEARCH_RESPONSE)
        knxipframe2.body.control_endpoint = \
            HPAI(ip_addr="192.168.42.10", port=3671)
        knxipframe2.body.dibs.append(knxipframe.body.dibs[0])
        knxipframe2.body.dibs.append(knxipframe.body.dibs[1])
        knxipframe2.normalize()
        self.assertEqual(knxipframe2.to_knx(), list(raw))
