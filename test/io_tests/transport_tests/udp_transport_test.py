"""Unit test for KNX/IP UDP transport."""

import logging
from unittest.mock import Mock

import pytest

from xknx.io.transport import UDPTransport


async def test_factory_debug_log(caplog: pytest.LogCaptureFixture) -> None:
    """Test received datagrams are logged in hex only when debug logging is enabled."""
    callback = Mock()
    factory = UDPTransport.UDPTransportFactory(data_received_callback=callback)
    caplog.set_level(logging.INFO, logger="xknx.raw_socket")
    factory.datagram_received(b"\x06\x10", ("192.168.1.2", 3671))
    assert "0610" not in caplog.text
    caplog.set_level(logging.DEBUG, logger="xknx.raw_socket")
    factory.datagram_received(b"\x06\x10", ("192.168.1.2", 3671))
    assert "0610" in caplog.text
    assert callback.call_count == 2
