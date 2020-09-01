"""Unit test for KNX/IP SearchResponse objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.knxip import (
    HPAI,
    DIBDeviceInformation,
    DIBServiceFamily,
    DIBSuppSVCFamilies,
    KNXIPFrame,
    KNXIPServiceType,
    SearchResponse,
)


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

    def test_search_response(self):
        """Test parsing and streaming SearchResponse KNX/IP packet."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x02,
            0x00,
            0x50,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x0A,
            0x0E,
            0x57,
            0x36,
            0x01,
            0x02,
            0x00,
            0x11,
            0x00,
            0x00,
            0x00,
            0x11,
            0x22,
            0x33,
            0x44,
            0x55,
            0x66,
            0xE0,
            0x00,
            0x17,
            0x0C,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x47,
            0x69,
            0x72,
            0x61,
            0x20,
            0x4B,
            0x4E,
            0x58,
            0x2F,
            0x49,
            0x50,
            0x2D,
            0x52,
            0x6F,
            0x75,
            0x74,
            0x65,
            0x72,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x0C,
            0x02,
            0x02,
            0x01,
            0x03,
            0x02,
            0x04,
            0x01,
            0x05,
            0x01,
            0x07,
            0x01,
        )
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        self.assertEqual(knxipframe.from_knx(raw), 80)
        self.assertEqual(knxipframe.to_knx(), list(raw))

        self.assertTrue(isinstance(knxipframe.body, SearchResponse))
        self.assertEqual(knxipframe.body.control_endpoint, HPAI("192.168.42.10", 3671))
        self.assertEqual(len(knxipframe.body.dibs), 2)
        # Specific testing of parsing and serializing of
        # DIBDeviceInformation and DIBSuppSVCFamilies is
        # done within knxip_dib_test.py
        self.assertTrue(isinstance(knxipframe.body.dibs[0], DIBDeviceInformation))
        self.assertTrue(isinstance(knxipframe.body.dibs[1], DIBSuppSVCFamilies))
        self.assertEqual(knxipframe.body.device_name, "Gira KNX/IP-Router")
        self.assertTrue(knxipframe.body.dibs[1].supports(DIBServiceFamily.ROUTING))
        self.assertTrue(knxipframe.body.dibs[1].supports(DIBServiceFamily.TUNNELING))
        self.assertFalse(
            knxipframe.body.dibs[1].supports(DIBServiceFamily.OBJECT_SERVER)
        )

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.SEARCH_RESPONSE)
        knxipframe2.body.control_endpoint = HPAI(ip_addr="192.168.42.10", port=3671)
        knxipframe2.body.dibs.append(knxipframe.body.dibs[0])
        knxipframe2.body.dibs.append(knxipframe.body.dibs[1])
        knxipframe2.normalize()
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_unknown_device_name(self):
        """Test device_name if no DIBDeviceInformation is present."""
        xknx = XKNX(loop=self.loop)
        search_response = SearchResponse(xknx)
        self.assertEqual(search_response.device_name, "UNKNOWN")
