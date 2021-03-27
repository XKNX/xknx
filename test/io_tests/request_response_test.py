"""Unit test for KNX/IP Disconnect Request/Response."""
import asyncio
import unittest
from unittest.mock import MagicMock, patch

from xknx import XKNX
from xknx.io import UDPClient
from xknx.io.request_response import RequestResponse
from xknx.knxip import DisconnectResponse, KNXIPBody


class AsyncMock(MagicMock):
    """Async Mock."""

    # pylint: disable=invalid-overridden-method
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


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
        xknx = XKNX()
        udp_client = UDPClient(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        request_response = RequestResponse(xknx, udp_client, DisconnectResponse)
        request_response.timeout_in_seconds = 0

        with self.assertRaises(NotImplementedError):
            self.loop.run_until_complete(request_response.start())

    @patch("logging.Logger.debug")
    @patch(
        "xknx.io.request_response.RequestResponse.send_request", new_callable=AsyncMock
    )
    def test_request_response_timeout(self, _send_request_mock, logger_debug_mock):
        """Test RequestResponse: timeout. No callback shall be left."""
        xknx = XKNX()
        udp_client = UDPClient(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        requ_resp = RequestResponse(xknx, udp_client, KNXIPBody)
        requ_resp.response_received_or_timeout.wait = MagicMock(
            side_effect=asyncio.TimeoutError()
        )
        self.loop.run_until_complete(requ_resp.start())
        # Debug message was logged
        logger_debug_mock.assert_called_once_with(
            "Error: KNX bus did not respond in time (%s secs) to request of type '%s'",
            1.0,
            "RequestResponse",
        )
        # Callback was removed again
        self.assertEqual(udp_client.callbacks, [])

    @patch(
        "xknx.io.request_response.RequestResponse.send_request", new_callable=AsyncMock
    )
    def test_request_response_cancelled(self, _send_request_mock):
        """Test RequestResponse: task cancelled. No callback shall be left."""
        xknx = XKNX()
        udp_client = UDPClient(xknx, ("192.168.1.1", 0), ("192.168.1.2", 1234))
        requ_resp = RequestResponse(xknx, udp_client, KNXIPBody)
        requ_resp.response_received_or_timeout.wait = MagicMock(
            side_effect=asyncio.CancelledError()
        )
        with self.assertRaises(asyncio.CancelledError):
            self.loop.run_until_complete(requ_resp.start())
        # Callback was removed again
        self.assertEqual(udp_client.callbacks, [])
