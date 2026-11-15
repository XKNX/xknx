"""Unit test for KNX/IP UDP transport."""

import socket
from unittest.mock import Mock, patch

import pytest

from xknx.io.transport import UDPTransport


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
