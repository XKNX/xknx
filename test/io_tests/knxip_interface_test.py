"""Unit test for KNX/IP Interface."""
import threading
from unittest.mock import patch

import pytest
from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType, knx_interface_factory


@pytest.mark.asyncio
class TestKNXIPInterface:
    """Test class for KNX interface objects."""

    def setup_method(self):
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.xknx = XKNX()

    async def test_start_automatic_connection(self):
        """Test starting automatic connection."""
        connection_config = ConnectionConfig()
        assert connection_config.connection_type == ConnectionType.AUTOMATIC
        with patch("xknx.io.KNXIPInterface._start_automatic") as start_automatic_mock:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_automatic_mock.assert_called_once_with()
            assert threading.active_count() == 1

    async def test_start_udp_tunnel_connection(self):
        """Test starting UDP tunnel connection."""
        # without gateway_ip automatic is called
        gateway_ip = "127.0.0.2"
        connection_config = ConnectionConfig(
            ConnectionType.TUNNELING, gateway_ip=gateway_ip
        )
        with patch(
            "xknx.io.KNXIPInterface._start_tunnelling_udp"
        ) as start_tunnelling_udp:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_tunnelling_udp.assert_called_once_with(
                local_ip=None,
                local_port=0,
                gateway_ip=gateway_ip,
                gateway_port=3671,
                auto_reconnect=True,
                auto_reconnect_wait=3,
                route_back=False,
            )

    async def test_start_tcp_tunnel_connection(self):
        """Test starting TCP tunnel connection."""
        # without gateway_ip automatic is called
        gateway_ip = "127.0.0.2"
        connection_config = ConnectionConfig(
            ConnectionType.TUNNELING_TCP, gateway_ip=gateway_ip
        )
        with patch(
            "xknx.io.KNXIPInterface._start_tunnelling_tcp"
        ) as start_tunnelling_tcp:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_tunnelling_tcp.assert_called_once_with(
                gateway_ip=gateway_ip,
                gateway_port=3671,
                auto_reconnect=True,
                auto_reconnect_wait=3,
            )

    async def test_start_routing_connection(self):
        """Test starting routing connection."""
        connection_config = ConnectionConfig(ConnectionType.ROUTING)
        with patch("xknx.io.KNXIPInterface._start_routing") as start_routing:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_routing.assert_called_once_with(
                local_ip=None,
            )

    async def test_threaded_connection(self):
        """Test starting threaded connection."""
        # pylint: disable=attribute-defined-outside-init
        self.main_thread = threading.get_ident()

        def assert_thread(*args, **kwargs):
            """Test threaded connection."""
            assert self.main_thread != threading.get_ident()

        connection_config = ConnectionConfig(threaded=True)
        assert connection_config.connection_type == ConnectionType.AUTOMATIC
        with patch(
            "xknx.io.KNXIPInterface._start_automatic", side_effect=assert_thread
        ) as start_automatic_mock:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_automatic_mock.assert_called_once_with()
