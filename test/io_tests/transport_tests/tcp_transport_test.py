"""Unit test for KNX/IP TCP transport."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from xknx.exceptions import CommunicationError
from xknx.io.const import TCP_CONNECT_TIMEOUT
from xknx.io.transport import TCPTransport
from xknx.knxip import ConnectionStateResponse, KNXIPFrame

from ...conftest import EventLoopClockAdvancer


class TestTCPTransport:
    """Test class for TCPTransport."""

    async def test_connect_timeout(self, time_travel: EventLoopClockAdvancer) -> None:
        """Test connecting raises CommunicationError when the TCP connection is not established in time."""
        transport = TCPTransport(("192.168.1.2", 3671))

        async def _never_connect(*args: object, **kwargs: object) -> None:
            await asyncio.sleep(3600)

        with patch.object(
            asyncio.get_running_loop(), "create_connection", new=_never_connect
        ):
            connect_task = asyncio.create_task(transport.connect())
            await time_travel(TCP_CONNECT_TIMEOUT)
            with pytest.raises(CommunicationError, match="could not be established"):
                await connect_task
        assert transport.transport is None

    async def test_connect_os_error(self) -> None:
        """Test an OSError of the socket connection is propagated."""
        transport = TCPTransport(("192.168.1.2", 3671))
        with (
            patch.object(
                asyncio.get_running_loop(),
                "create_connection",
                new=AsyncMock(side_effect=OSError("refused")),
            ),
            pytest.raises(OSError),
        ):
            await transport.connect()

    async def test_buffer_reset(self) -> None:
        """Test a partial frame of a previous connection is dropped on stop and connect."""
        transport = TCPTransport(("192.168.1.2", 3671))
        frame_received_mock = Mock()
        transport.register_callback(frame_received_mock)
        response = KNXIPFrame.init_from_body(
            ConnectionStateResponse(communication_channel_id=23)
        ).to_knx()

        # partial frame received - buffered
        transport.transport = Mock()
        transport.data_received_callback(response[:3])
        assert transport._buffer == response[:3]
        frame_received_mock.assert_not_called()
        # connection closed - buffer dropped with the transport
        transport.stop()
        assert transport.transport is None
        assert transport._buffer == b""

        # a partial frame received right before the connection was lost
        transport._buffer = response[:3]
        asyncio_transport = Mock()
        with patch.object(
            asyncio.get_running_loop(),
            "create_connection",
            new=AsyncMock(return_value=(asyncio_transport, None)),
        ):
            await transport.connect()
        assert transport.transport is asyncio_transport
        assert transport._buffer == b""
        # the first frame of the new connection is parsed as a whole
        transport.data_received_callback(response)
        frame_received_mock.assert_called_once()
        assert transport._buffer == b""
