"""Unit test for KNX/IP Disconnect Request/Response."""
import asyncio
import unittest

import pytest
pytestmark = pytest.mark.asyncio

from xknx import XKNX
from xknx.io import RequestResponse, UDPClient
from xknx.knxip import DisconnectResponse


class TestConnectResponse(unittest.TestCase):
    """Test class for xknx/io/Disconnect objects."""

    async def test_create_knxipframe_err(self):
        """Test if create_knxipframe of base class raises an exception."""
        xknx = XKNX()
        udp_client = UDPClient(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        request_response = RequestResponse(xknx, udp_client, DisconnectResponse)
        request_response.timeout_in_seconds = 0

        with self.assertRaises(NotImplementedError):
            await asyncio.Task(request_response.start())
