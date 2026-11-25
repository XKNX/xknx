"""Test the debug logs stating what a socket is used for and over which interface."""

import asyncio
from collections.abc import Iterator
import logging
from unittest.mock import patch

import pytest

from xknx import XKNX
from xknx.exceptions import CommunicationError
from xknx.io import (
    ConnectionConfig,
    ConnectionType,
    SecureConfig,
    knx_interface_factory,
    util,
)
from xknx.io.self_description import request_description
from xknx.io.transport import TCPTransport, UDPTransport

from ..conftest import EventLoopClockAdvancer

GATEWAY_IP = "192.168.1.2"
LOCAL_IP = "127.0.0.1"


@pytest.fixture(autouse=True)
def debug_log(caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    """Capture debug logs of `xknx.log` with a local interface named lo0."""
    with (
        caplog.at_level(logging.DEBUG, logger="xknx.log"),
        patch("xknx.io.util.get_local_interface_name", return_value="lo0"),
    ):
        yield


def test_describe_local_interface() -> None:
    """Test formatting a local interface for log messages."""
    assert util.describe_local_interface(LOCAL_IP) == f"lo0 ({LOCAL_IP})"
    with patch("xknx.io.util.get_local_interface_name", return_value=""):
        assert util.describe_local_interface(LOCAL_IP) == LOCAL_IP


@pytest.mark.parametrize(
    ("kwargs", "purpose"),
    [({}, "UDP communication"), ({"purpose": "UDP tunnel"}, "UDP tunnel")],
)
async def test_udp_transport_log(
    kwargs: dict[str, str],
    purpose: str,
    caplog: pytest.LogCaptureFixture,
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test a UDP transport logging its purpose when starting and closing the socket."""
    transport = UDPTransport(
        local_addr=(LOCAL_IP, 0), remote_addr=(GATEWAY_IP, 3671), **kwargs
    )
    await transport.connect()
    assert caplog.messages == [
        f"Started socket for {purpose} to {GATEWAY_IP}:3671 over lo0 ({LOCAL_IP})"
    ]
    caplog.clear()
    transport.stop()
    await time_travel(0)
    assert caplog.messages == [f"Closing socket for {purpose}."]


@pytest.mark.parametrize(
    ("kwargs", "purpose"),
    [({}, "TCP communication"), ({"purpose": "TCP tunnel"}, "TCP tunnel")],
)
async def test_tcp_transport_log(
    kwargs: dict[str, str],
    purpose: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a TCP transport logging its purpose when starting and closing the socket."""
    server = await asyncio.start_server(lambda _reader, _writer: None, LOCAL_IP, 0)
    port = server.sockets[0].getsockname()[1]
    transport = TCPTransport(remote_addr=(LOCAL_IP, port), **kwargs)
    try:
        await transport.connect()
        assert caplog.messages == [
            f"Started socket for {purpose} to {LOCAL_IP}:{port} over lo0 ({LOCAL_IP})"
        ]
        caplog.clear()
        transport.stop()
        await asyncio.sleep(0)
        assert caplog.messages == [f"Closing socket for {purpose}. None"]
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.parametrize(
    ("connection_config", "connect_target", "purpose"),
    [
        (
            ConnectionConfig(
                connection_type=ConnectionType.TUNNELING,
                gateway_ip=GATEWAY_IP,
                local_ip=LOCAL_IP,
            ),
            "xknx.io.tunnel.UDPTunnel.connect",
            "UDP tunnel",
        ),
        (
            ConnectionConfig(
                connection_type=ConnectionType.TUNNELING_TCP,
                gateway_ip=GATEWAY_IP,
            ),
            "xknx.io.tunnel.TCPTunnel.connect",
            "TCP tunnel",
        ),
        (
            ConnectionConfig(
                connection_type=ConnectionType.TUNNELING_TCP_SECURE,
                gateway_ip=GATEWAY_IP,
                secure_config=SecureConfig(user_id=3, user_password="password"),
            ),
            "xknx.io.tunnel.SecureTunnel.connect",
            "secure tunnel",
        ),
        (
            ConnectionConfig(
                connection_type=ConnectionType.ROUTING,
                local_ip=LOCAL_IP,
            ),
            "xknx.io.routing.Routing.connect",
            "routing",
        ),
        (
            ConnectionConfig(
                connection_type=ConnectionType.ROUTING_SECURE,
                local_ip=LOCAL_IP,
                secure_config=SecureConfig(
                    backbone_key="cf89fd0f18f4889783c7ef44ee1f5e14"
                ),
            ),
            "xknx.io.routing.SecureRouting.connect",
            "secure routing",
        ),
    ],
)
async def test_connection_transport_purpose(
    connection_config: ConnectionConfig,
    connect_target: str,
    purpose: str,
) -> None:
    """Test the transport of a permanent connection knowing its purpose."""
    interface = knx_interface_factory(XKNX(), connection_config)
    with patch(connect_target):
        await interface.start()
    assert interface._interface is not None
    assert interface._interface.transport.purpose == purpose  # type: ignore[attr-defined]


@pytest.mark.parametrize("local_ip", [None, LOCAL_IP])
async def test_request_description_log(
    local_ip: str | None,
    caplog: pytest.LogCaptureFixture,
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test the logs of a description request with a found or configured `local_ip`."""
    with (
        patch("xknx.io.util.find_local_ip", return_value=LOCAL_IP),
        patch("xknx.io.self_description.UDPTransport.send"),
        pytest.raises(CommunicationError),
    ):
        task = asyncio.create_task(request_description(GATEWAY_IP, local_ip=local_ip))
        await time_travel(10)
        await task
    assert caplog.messages == [
        f"Started socket for description request to {GATEWAY_IP}:3671"
        f" over lo0 ({LOCAL_IP})",
        "Closing socket for description request.",
    ]


async def test_request_description_log_fallback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the logs of a description request falling back to the default interface."""
    with (
        patch("xknx.io.util.get_local_ips", return_value=[]),
        patch("xknx.io.util.get_default_local_ip", return_value=LOCAL_IP),
        patch(
            "xknx.io.self_description.UDPTransport.connect", side_effect=OSError("boom")
        ),
        pytest.raises(CommunicationError),
    ):
        await request_description(GATEWAY_IP)
    assert caplog.messages == [
        "No interface on same subnet as gateway found.",
        "Falling back to default interface and enabling route back.",
    ]
