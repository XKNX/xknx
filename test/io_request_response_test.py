"""Unit test for KNX/IP Disconnect Request/Response."""
import asyncio
import unittest

from xknx import XKNX
from xknx.io import RequestResponse, UDPClient
from xknx.knxip import DisconnectResponse


class TestConnectResponse(unittest.TestCase):
    """Test class for xknx/io/Disconnect objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_create_knxipframe_err(self):
        """Test if create_knxipframe of base class raises an exception."""
        xknx = XKNX(loop=self.loop)
        udp_client = UDPClient(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        request_response = RequestResponse(xknx, udp_client, DisconnectResponse)
        request_response.timeout_in_seconds = 0

        with self.assertRaises(NotImplementedError):
            self.loop.run_until_complete(asyncio.Task(request_response.start()))
