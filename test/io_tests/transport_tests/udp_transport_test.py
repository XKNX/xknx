"""Unit test for KNX/IP UDP transport."""

import socket
from unittest.mock import Mock, patch

import pytest

from xknx.io.transport import UDPTransport
from xknx.io.transport.udp_transport import MULTICAST_TTL


class TestUDPTransport:
    """Test class for UDPTransport."""

    def test_create_multicast_sock_closed_on_error(self) -> None:
        """Test the socket is closed when configuring the multicast socket fails."""
        sock_mock = Mock(spec=socket.socket)
        sock_mock.setsockopt.side_effect = OSError("No such device")
        with (
            patch("socket.socket", return_value=sock_mock),
            pytest.raises(OSError, match="No such device"),
        ):
            UDPTransport.create_multicast_sock("10.1.1.1", ("224.0.23.12", 3671))
        sock_mock.close.assert_called_once_with()

    def test_create_multicast_sock(self) -> None:
        """Test the configured multicast socket is returned."""
        sock_mock = Mock(spec=socket.socket)
        with patch("socket.socket", return_value=sock_mock):
            sock = UDPTransport.create_multicast_sock("10.1.1.1", ("224.0.23.12", 3671))
        assert sock is sock_mock
        sock_mock.bind.assert_called_once()
        sock_mock.close.assert_not_called()

    @pytest.mark.parametrize("multicast", [True, False])
    async def test_multicast_send_socket(self, multicast: bool) -> None:
        """Test interface and TTL are set for sending to a multicast address."""
        transport = UDPTransport(
            local_addr=("127.0.0.1", 0),
            remote_addr=("224.0.0.254", 3671),
            multicast=multicast,
        )
        await transport.connect()
        try:
            assert transport.transport is not None
            sock = transport.transport.get_extra_info("socket")
            assert (
                sock.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL)
                == MULTICAST_TTL
            )
            assert sock.getsockopt(
                socket.IPPROTO_IP, socket.IP_MULTICAST_IF, 4
            ) == socket.inet_aton("127.0.0.1")
        finally:
            transport.stop()

    async def test_unicast_send_socket(self) -> None:
        """Test multicast options are left alone for a unicast remote address."""
        transport = UDPTransport(
            local_addr=("127.0.0.1", 0),
            remote_addr=("127.0.0.1", 3671),
        )
        await transport.connect()
        try:
            assert transport.transport is not None
            sock = transport.transport.get_extra_info("socket")
            assert sock.getsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL) == 1
        finally:
            transport.stop()

    async def test_multicast_interface_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test a refused multicast interface is logged and doesn't fail connect."""
        transport = UDPTransport(
            local_addr=("127.0.0.1", 0),
            remote_addr=("224.0.0.254", 3671),
        )
        sock_mock = Mock()
        sock_mock.setsockopt.side_effect = [None, OSError("Can't assign address")]
        transport.transport = Mock()
        transport.transport.get_extra_info.return_value = sock_mock
        transport._configure_multicast_send()
        assert "Could not set multicast interface to 127.0.0.1" in caplog.text
