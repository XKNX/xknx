"""Test the debug logs stating what a socket is opened for and over which interface."""

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
from xknx.io.tunnel import SecureTunnel, TCPTunnel

GATEWAY_IP = "192.168.1.2"
LOCAL_IP = "192.168.1.50"


@pytest.fixture(autouse=True)
def debug_log(caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    """Capture debug logs of `xknx.log` with a local interface named en0."""
    with (
        caplog.at_level(logging.DEBUG, logger="xknx.log"),
        patch("xknx.io.util.get_local_interface_name", return_value="en0"),
    ):
        yield


def test_describe_local_interface() -> None:
    """Test formatting a local interface for log messages."""
    assert util.describe_local_interface(LOCAL_IP) == f"en0 ({LOCAL_IP})"
    with patch("xknx.io.util.get_local_interface_name", return_value=""):
        assert util.describe_local_interface(LOCAL_IP) == LOCAL_IP


@pytest.mark.parametrize(
    ("connection_config", "connect_target", "message"),
    [
        (
            ConnectionConfig(
                connection_type=ConnectionType.TUNNELING,
                gateway_ip=GATEWAY_IP,
                local_ip=LOCAL_IP,
            ),
            "xknx.io.tunnel.UDPTunnel.connect",
            f"Initializing socket for UDP tunnel to {GATEWAY_IP}:3671 over en0 ({LOCAL_IP})",
        ),
        (
            ConnectionConfig(
                connection_type=ConnectionType.TUNNELING_TCP,
                gateway_ip=GATEWAY_IP,
            ),
            "xknx.io.tunnel.TCPTunnel.connect",
            f"Initializing socket for TCP tunnel to {GATEWAY_IP}:3671",
        ),
        (
            ConnectionConfig(
                connection_type=ConnectionType.TUNNELING_TCP,
                gateway_ip=GATEWAY_IP,
                individual_address="1.1.1",
            ),
            "xknx.io.tunnel.TCPTunnel.connect",
            f"Initializing socket for TCP tunnel to {GATEWAY_IP}:3671"
            " requesting individual address 1.1.1",
        ),
        (
            ConnectionConfig(
                connection_type=ConnectionType.TUNNELING_TCP_SECURE,
                gateway_ip=GATEWAY_IP,
                secure_config=SecureConfig(user_id=3, user_password="password"),
            ),
            "xknx.io.tunnel.SecureTunnel.connect",
            f"Initializing socket for secure TCP tunnel to {GATEWAY_IP}:3671",
        ),
        (
            ConnectionConfig(
                connection_type=ConnectionType.ROUTING,
                local_ip=LOCAL_IP,
            ),
            "xknx.io.routing.Routing.connect",
            "Initializing socket for routing as 15.15.250 via 224.0.23.12:3671"
            f" over en0 ({LOCAL_IP})",
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
            "Initializing socket for secure routing as 15.15.250 via 224.0.23.12:3671"
            f" over en0 ({LOCAL_IP})",
        ),
    ],
)
async def test_interface_start_log(
    connection_config: ConnectionConfig,
    connect_target: str,
    message: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the log of a permanent connection with a configured `local_ip`."""
    with patch(connect_target):
        await knx_interface_factory(XKNX(), connection_config).start()
    assert message in caplog.messages


async def test_udp_tunnel_log_interface_found(caplog: pytest.LogCaptureFixture) -> None:
    """Test the log of a UDP tunnel over an interface found for the gateway."""
    connection_config = ConnectionConfig(
        connection_type=ConnectionType.TUNNELING, gateway_ip=GATEWAY_IP
    )
    with (
        patch("xknx.io.util.find_local_ip", return_value=LOCAL_IP),
        patch("xknx.io.tunnel.UDPTunnel.connect"),
    ):
        await knx_interface_factory(XKNX(), connection_config).start()
    assert caplog.messages == [
        f"Initializing socket for UDP tunnel to {GATEWAY_IP}:3671 over en0 ({LOCAL_IP})"
    ]


async def test_udp_tunnel_log_fallback(caplog: pytest.LogCaptureFixture) -> None:
    """Test the logs of a UDP tunnel falling back to the default interface."""
    connection_config = ConnectionConfig(
        connection_type=ConnectionType.TUNNELING, gateway_ip=GATEWAY_IP
    )
    with (
        patch("xknx.io.util.find_local_ip", return_value=None),
        patch("xknx.io.util.get_default_local_ip", return_value=LOCAL_IP),
        patch("xknx.io.tunnel.UDPTunnel.connect"),
    ):
        await knx_interface_factory(XKNX(), connection_config).start()
    assert caplog.messages == [
        f"No interface on same subnet as {GATEWAY_IP} found. "
        "Falling back to default interface and enabling route back.",
        f"Initializing socket for UDP tunnel to {GATEWAY_IP}:3671 over en0 ({LOCAL_IP})",
    ]


async def test_routing_log_default_interface(caplog: pytest.LogCaptureFixture) -> None:
    """Test the log of routing over the default interface."""
    connection_config = ConnectionConfig(connection_type=ConnectionType.ROUTING)
    with (
        patch("xknx.io.util.get_default_local_ip", return_value=LOCAL_IP),
        patch("xknx.io.routing.Routing.connect"),
    ):
        await knx_interface_factory(XKNX(), connection_config).start()
    assert caplog.messages == [
        "Initializing socket for routing as 15.15.250 via 224.0.23.12:3671"
        f" over en0 ({LOCAL_IP})"
    ]


@pytest.mark.parametrize(
    ("tunnel_cls", "name"),
    [(TCPTunnel, "TCP tunnel"), (SecureTunnel, "secure TCP tunnel")],
)
async def test_tcp_tunnel_connected_log(
    tunnel_cls: type[TCPTunnel],
    name: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the log of the interface the OS chose for a TCP connection."""
    kwargs = (
        {"user_id": 3, "user_password": "password"}
        if tunnel_cls is SecureTunnel
        else {}
    )
    tunnel = tunnel_cls(
        XKNX(),
        cemi_received_callback=lambda _: None,
        gateway_ip=GATEWAY_IP,
        gateway_port=3671,
        **kwargs,
    )
    with patch(
        "xknx.io.transport.tcp_transport.TCPTransport.getsockname",
        return_value=(LOCAL_IP, 54321),
    ):
        await tunnel.setup_tunnel()
    assert caplog.messages == [
        f"Socket for {name} to {GATEWAY_IP}:3671 connected over en0 ({LOCAL_IP})"
    ]
    # no socket - nothing to log
    caplog.clear()
    await tunnel.setup_tunnel()
    assert not caplog.messages


@pytest.mark.parametrize("local_ip", [None, LOCAL_IP])
async def test_request_description_log(
    local_ip: str | None, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the log of a description request with a found or configured `local_ip`."""
    with (
        patch("xknx.io.util.find_local_ip", return_value=LOCAL_IP),
        patch(
            "xknx.io.self_description.UDPTransport.connect", side_effect=OSError("boom")
        ),
        pytest.raises(CommunicationError),
    ):
        await request_description(GATEWAY_IP, local_ip=local_ip)
    assert caplog.messages == [
        f"Starting socket for description request to {GATEWAY_IP}:3671"
        f" over en0 ({LOCAL_IP})"
    ]


async def test_request_description_log_fallback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the logs of a description request falling back to the default interface."""
    with (
        patch("xknx.io.util.find_local_ip", return_value=None),
        patch("xknx.io.util.get_default_local_ip", return_value=LOCAL_IP),
        patch(
            "xknx.io.self_description.UDPTransport.connect", side_effect=OSError("boom")
        ),
        pytest.raises(CommunicationError),
    ):
        await request_description(GATEWAY_IP)
    assert caplog.messages == [
        f"No interface on same subnet as {GATEWAY_IP} found. "
        "Falling back to default interface and enabling route back.",
        f"Starting socket for description request to {GATEWAY_IP}:3671"
        f" over en0 ({LOCAL_IP})",
    ]
