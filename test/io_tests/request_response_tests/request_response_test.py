"""Unit test for KNX/IP Disconnect Request/Response."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from xknx.io.request_response import RequestResponse
from xknx.io.transport import UDPTransport
from xknx.knxip import DisconnectResponse, KNXIPBody


class TestConnectResponse:
    """Test class for xknx/io/Disconnect objects."""

    async def test_create_knxipframe_err(self) -> None:
        """Test if create_knxipframe of base class raises an exception."""
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        request_response = RequestResponse(udp_transport, DisconnectResponse)
        request_response.timeout_in_seconds = 0

        with pytest.raises(NotImplementedError):
            await request_response.start()

    @patch("logging.Logger.debug")
    @patch(
        "xknx.io.request_response.RequestResponse.send_request", new_callable=AsyncMock
    )
    async def test_request_response_timeout(
        self, _send_request_mock: MagicMock, logger_debug_mock: AsyncMock
    ) -> None:
        """Test RequestResponse: timeout. No callback shall be left."""
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        requ_resp = RequestResponse(udp_transport, KNXIPBody)
        requ_resp.response_received_event.wait = MagicMock(
            side_effect=asyncio.TimeoutError()
        )
        await requ_resp.start()
        # Debug message was logged
        logger_debug_mock.assert_called_once_with(
            "Error: KNX bus did not respond in time (%s secs) to request of type '%s'",
            1.0,
            "RequestResponse",
        )
        # Callback was removed again
        assert not udp_transport.callbacks

    @patch(
        "xknx.io.request_response.RequestResponse.send_request", new_callable=AsyncMock
    )
    async def test_request_response_cancelled(
        self, _send_request_mock: AsyncMock
    ) -> None:
        """Test RequestResponse: task cancelled. No callback shall be left."""
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        requ_resp = RequestResponse(udp_transport, KNXIPBody)
        requ_resp.response_received_event.wait = MagicMock(
            side_effect=asyncio.CancelledError()
        )
        with pytest.raises(asyncio.CancelledError):
            await requ_resp.start()
        # Callback was removed again
        assert not udp_transport.callbacks
