"""Unit test for KNX/IP Interface."""
import os
import threading
from unittest.mock import DEFAULT, Mock, patch

import pytest

from xknx import XKNX
from xknx.exceptions.exception import (
    CommunicationError,
    InterfaceWithUserIdNotFound,
    InvalidSecureConfiguration,
)
from xknx.io import (
    ConnectionConfig,
    ConnectionType,
    GatewayDescriptor,
    SecureConfig,
    knx_interface_factory,
)
from xknx.io.routing import Routing
from xknx.io.tunnel import SecureTunnel, TCPTunnel, UDPTunnel


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
        interface = knx_interface_factory(self.xknx, connection_config)
        with patch("xknx.io.KNXIPInterface._start_automatic") as start_automatic_mock:
            await interface.start()
            start_automatic_mock.assert_called_once_with()
            assert threading.active_count() == 1

        async def gateway_generator_mock(_):
            yield GatewayDescriptor(
                ip_addr="10.1.2.3", port=3671, supports_tunnelling_tcp=True
            )
            yield GatewayDescriptor(
                ip_addr="10.1.2.3", port=3671, supports_tunnelling=True
            )
            yield GatewayDescriptor(
                ip_addr="10.1.2.3", port=3671, supports_routing=True
            )

        with patch(
            "xknx.io.knxip_interface.GatewayScanner.async_scan",
            new=gateway_generator_mock,
        ), patch(
            "xknx.io.KNXIPInterface._start_tunnelling_tcp",
            side_effect=CommunicationError("Error"),
        ) as start_tunnelling_tcp_mock, patch(
            "xknx.io.KNXIPInterface._start_tunnelling_udp",
            side_effect=CommunicationError("Error"),
        ) as start_tunnelling_udp_mock, patch(
            "xknx.io.KNXIPInterface._start_routing",
            side_effect=CommunicationError("Error"),
        ) as start_routing_mock:
            with pytest.raises(CommunicationError):
                await interface.start()
            start_tunnelling_tcp_mock.assert_called_once()
            start_tunnelling_udp_mock.assert_called_once()
            start_routing_mock.assert_called_once()

    async def test_start_udp_tunnel_connection(self):
        """Test starting UDP tunnel connection."""
        # without gateway_ip automatic is called
        gateway_ip = "127.0.0.2"
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING, gateway_ip=gateway_ip
        )
        with patch(
            "xknx.io.KNXIPInterface._start_tunnelling_udp"
        ) as start_tunnelling_udp:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_tunnelling_udp.assert_called_once_with(
                gateway_ip=gateway_ip,
                gateway_port=3671,
            )
        with patch("xknx.io.tunnel.UDPTunnel.connect") as connect_udp:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            assert isinstance(interface._interface, UDPTunnel)
            assert interface._interface.local_ip == "127.0.0.1"
            assert interface._interface.local_port == 0
            assert interface._interface.gateway_ip == gateway_ip
            assert interface._interface.gateway_port == 3671
            assert interface._interface.auto_reconnect
            assert interface._interface.auto_reconnect_wait == 3
            assert interface._interface.route_back is False
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.telegram_received_callback
                == interface.telegram_received
            )
            connect_udp.assert_called_once_with()

    async def test_start_tcp_tunnel_connection(self):
        """Test starting TCP tunnel connection."""
        # without gateway_ip automatic is called
        gateway_ip = "127.0.0.2"
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP, gateway_ip=gateway_ip
        )
        with patch(
            "xknx.io.KNXIPInterface._start_tunnelling_tcp"
        ) as start_tunnelling_tcp:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_tunnelling_tcp.assert_called_once_with(
                gateway_ip=gateway_ip,
                gateway_port=3671,
            )
        with patch("xknx.io.tunnel.TCPTunnel.connect") as connect_tcp:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            assert isinstance(interface._interface, TCPTunnel)
            assert interface._interface.gateway_ip == gateway_ip
            assert interface._interface.gateway_port == 3671
            assert interface._interface.auto_reconnect
            assert interface._interface.auto_reconnect_wait == 3
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.telegram_received_callback
                == interface.telegram_received
            )
            connect_tcp.assert_called_once_with()

    async def test_start_routing_connection(self):
        """Test starting routing connection."""
        local_ip = "127.0.0.1"
        # set local_ip to avoid gateway scanner
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.ROUTING, local_ip=local_ip
        )
        with patch("xknx.io.KNXIPInterface._start_routing") as start_routing:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_routing.assert_called_once_with(
                local_ip=local_ip,
            )
        with patch("xknx.io.routing.Routing.connect") as connect_routing:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            assert isinstance(interface._interface, Routing)
            assert interface._interface.local_ip == local_ip
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.telegram_received_callback
                == interface.telegram_received
            )
            connect_routing.assert_called_once_with()

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

    async def test_threaded_send_telegram(self):
        """Test sending telegram with threaded connection."""
        # pylint: disable=attribute-defined-outside-init
        self.main_thread = threading.get_ident()

        def assert_thread(*args, **kwargs):
            """Test threaded connection."""
            assert self.main_thread != threading.get_ident()
            return DEFAULT  # to not disable `return_value` of send_telegram_mock

        local_ip = "127.0.0.1"
        # set local_ip to avoid gateway scanner; use routing as it is the simplest mode
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.ROUTING, local_ip=local_ip, threaded=True
        )
        telegram_mock = Mock()
        with patch(
            "xknx.io.routing.Routing.connect", side_effect=assert_thread
        ) as connect_routing_mock, patch(
            "xknx.io.routing.Routing.send_telegram",
            side_effect=assert_thread,
            return_value="test",
        ) as send_telegram_mock, patch(
            "xknx.io.routing.Routing.disconnect", side_effect=assert_thread
        ) as disconnect_routing_mock:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            connect_routing_mock.assert_called_once_with()
            assert await interface.send_telegram(telegram_mock) == "test"
            send_telegram_mock.assert_called_once_with(telegram_mock)
            await interface.stop()
            disconnect_routing_mock.assert_called_once_with()
            assert interface._interface is None

    async def test_start_secure_connection_knx_keys(self):
        """Test starting a secure connection from a knxkeys file."""
        gateway_ip = "192.168.1.1"
        knxkeys_file = os.path.join(
            os.path.dirname(__file__), "resources/testcase.knxkeys"
        )
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP_SECURE,
            gateway_ip=gateway_ip,
            secure_config=SecureConfig(
                user_id=3, knxkeys_file_path=knxkeys_file, knxkeys_password="password"
            ),
        )
        with patch(
            "xknx.io.KNXIPInterface._start_secure_tunnelling_tcp"
        ) as start_secure_tunnel:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_secure_tunnel.assert_called_once_with(
                gateway_ip="192.168.1.1",
                gateway_port=3671,
                user_id=3,
                user_password="user1",
                device_authentication_password="authenticationcode",
            )
        with patch("xknx.io.tunnel.SecureTunnel.connect") as connect_secure:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            assert isinstance(interface._interface, SecureTunnel)
            assert interface._interface.gateway_ip == gateway_ip
            assert interface._interface.gateway_port == 3671
            assert interface._interface.auto_reconnect is True
            assert interface._interface.auto_reconnect_wait == 3
            assert interface._interface._user_id == 3
            assert interface._interface._user_password == "user1"
            assert (
                interface._interface._device_authentication_password
                == "authenticationcode"
            )
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.telegram_received_callback
                == interface.telegram_received
            )
            connect_secure.assert_called_once_with()

    async def test_start_secure_connection_knx_keys_first_interface(self):
        """Test starting a secure connection from a knxkeys file."""
        gateway_ip = "192.168.1.1"
        knxkeys_file = os.path.join(
            os.path.dirname(__file__), "resources/testcase.knxkeys"
        )
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP_SECURE,
            gateway_ip=gateway_ip,
            secure_config=SecureConfig(
                knxkeys_file_path=knxkeys_file, knxkeys_password="password"
            ),
        )
        with patch(
            "xknx.io.KNXIPInterface._start_secure_tunnelling_tcp"
        ) as start_secure_tunnel:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_secure_tunnel.assert_called_once_with(
                gateway_ip="192.168.1.1",
                gateway_port=3671,
                user_id=3,
                user_password="user1",
                device_authentication_password="authenticationcode",
            )
        with patch("xknx.io.tunnel.SecureTunnel.connect") as connect_secure:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            assert isinstance(interface._interface, SecureTunnel)
            assert interface._interface.gateway_ip == gateway_ip
            assert interface._interface.gateway_port == 3671
            assert interface._interface.auto_reconnect is True
            assert interface._interface.auto_reconnect_wait == 3
            assert interface._interface._user_id == 3
            assert interface._interface._user_password == "user1"
            assert (
                interface._interface._device_authentication_password
                == "authenticationcode"
            )
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.telegram_received_callback
                == interface.telegram_received
            )
            connect_secure.assert_called_once_with()

    async def test_start_secure_with_manual_passwords(self):
        """Test starting a secure connection from manual passwords."""
        gateway_ip = "192.168.1.1"
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP_SECURE,
            gateway_ip=gateway_ip,
            secure_config=SecureConfig(
                user_id=3,
                device_authentication_password="authenticationcode",
                user_password="user1",
            ),
        )
        with patch(
            "xknx.io.KNXIPInterface._start_secure_tunnelling_tcp"
        ) as start_secure_tunnel:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_secure_tunnel.assert_called_once_with(
                gateway_ip="192.168.1.1",
                gateway_port=3671,
                user_id=3,
                user_password="user1",
                device_authentication_password="authenticationcode",
            )
        with patch("xknx.io.tunnel.SecureTunnel.connect") as connect_secure:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            assert isinstance(interface._interface, SecureTunnel)
            assert interface._interface.gateway_ip == gateway_ip
            assert interface._interface.gateway_port == 3671
            assert interface._interface.auto_reconnect is True
            assert interface._interface.auto_reconnect_wait == 3
            assert interface._interface._user_id == 3
            assert interface._interface._user_password == "user1"
            assert (
                interface._interface._device_authentication_password
                == "authenticationcode"
            )
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.telegram_received_callback
                == interface.telegram_received
            )
            connect_secure.assert_called_once_with()

    async def test_invalid_user_id_secure_error(self):
        """Test ip secure."""
        gateway_ip = "192.168.1.1"
        knxkeys_file = os.path.join(
            os.path.dirname(__file__), "resources/testcase.knxkeys"
        )
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP_SECURE,
            gateway_ip=gateway_ip,
            secure_config=SecureConfig(
                user_id=12, knxkeys_file_path=knxkeys_file, knxkeys_password="password"
            ),
        )
        with pytest.raises(InterfaceWithUserIdNotFound):
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()

    async def test_invalid_user_password(self):
        """Test ip secure."""
        gateway_ip = "192.168.1.1"
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP_SECURE,
            gateway_ip=gateway_ip,
            secure_config=SecureConfig(
                user_id=1,
            ),
        )
        with pytest.raises(InvalidSecureConfiguration):
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
