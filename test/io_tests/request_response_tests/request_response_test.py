"""Unit test for KNX/IP Disconnect Request/Response."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from xknx.exceptions import RequestResponseError
from xknx.io.request_response import RequestResponse
from xknx.io.transport import UDPTransport
from xknx.knxip import KNXIPBody


class _RequestResponse(RequestResponse[KNXIPBody]):  # pylint: disable=abstract-method
    """
    RequestResponse is only usable parametrized - it derives the awaited class from that.

    `_create_knxipframe()` is deliberately not overridden - one test asserts it raises.
    """

    __slots__ = ()


class TestConnectResponse:
    """Test class for xknx/io/Disconnect objects."""

    async def test_create_knxipframe_err(self) -> None:
        """Test if _create_knxipframe of base class raises an exception."""
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        request_response = _RequestResponse(udp_transport)
        request_response.timeout_in_seconds = 0

        with pytest.raises(NotImplementedError):
            await request_response.request()

    @patch(
        "xknx.io.request_response.RequestResponse._send_request", new_callable=AsyncMock
    )
    async def test_request_response_timeout(
        self, _send_request_mock: MagicMock
    ) -> None:
        """Test RequestResponse: timeout. No callback shall be left."""
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        requ_resp = _RequestResponse(udp_transport)
        requ_resp._response_received_event.wait = MagicMock(side_effect=TimeoutError())
        with pytest.raises(RequestResponseError) as exc_info:
            await requ_resp.request()
        assert str(exc_info.value) == (
            "KNX bus did not respond in time (1.0 secs) to request of type "
            "'_RequestResponse'"
        )
        # No response, so no error code either
        assert exc_info.value.error_code is None
        # Callback was removed again
        assert not udp_transport.callbacks

    @patch(
        "xknx.io.request_response.RequestResponse._send_request", new_callable=AsyncMock
    )
    async def test_request_response_cancelled(
        self, _send_request_mock: AsyncMock
    ) -> None:
        """Test RequestResponse: task cancelled. No callback shall be left."""
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        requ_resp = _RequestResponse(udp_transport)
        requ_resp._response_received_event.wait = MagicMock(
            side_effect=asyncio.CancelledError()
        )
        with pytest.raises(asyncio.CancelledError):
            await requ_resp.request()
        # Callback was removed again
        assert not udp_transport.callbacks
