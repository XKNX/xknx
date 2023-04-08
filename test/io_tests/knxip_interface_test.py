"""Unit test for KNX/IP Interface."""
import os
import threading
from unittest.mock import DEFAULT, Mock, patch

import pytest

from xknx import XKNX
from xknx.exceptions.exception import CommunicationError, InvalidSecureConfiguration
from xknx.io import (
    ConnectionConfig,
    ConnectionType,
    GatewayDescriptor,
    SecureConfig,
    knx_interface_factory,
)
from xknx.io.routing import Routing, SecureGroup, SecureRouting
from xknx.io.tunnel import SecureTunnel, TCPTunnel, UDPTunnel
from xknx.knxip.dib import TunnelingSlotStatus
from xknx.telegram import IndividualAddress


class TestKNXIPInterface:
    """Test class for KNX interface objects."""

    knxkeys_file = os.path.join(os.path.dirname(__file__), "resources/testcase.knxkeys")

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
            start_automatic_mock.assert_called_once_with(local_ip=None, keyring=None)
            assert threading.active_count() == 1

        async def gateway_generator_mock(_):
            secure_interface = GatewayDescriptor(
                ip_addr="10.1.2.3",
                port=3671,
                supports_tunnelling_tcp=True,
                supports_secure=True,
            )
            secure_interface.tunnelling_requires_secure = True
            yield secure_interface
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
            "xknx.io.KNXIPInterface._start_secure_tunnelling_tcp",
            side_effect=InvalidSecureConfiguration("Error"),
        ) as start_secure_tunnelling_tcp, patch(
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
            start_secure_tunnelling_tcp.assert_called_once()
            start_tunnelling_tcp_mock.assert_called_once()
            start_tunnelling_udp_mock.assert_called_once()
            start_routing_mock.assert_called_once()

    async def test_start_automatic_with_keyring(self):
        """Test starting with automatic mode and keyring."""
        connection_config = ConnectionConfig(
            secure_config=SecureConfig(
                knxkeys_file_path=self.knxkeys_file,
                knxkeys_password="password",
            )
        )
        assert connection_config.connection_type == ConnectionType.AUTOMATIC
        interface = knx_interface_factory(self.xknx, connection_config)

        # in the test keyfile the only host is 1.0.0 - others shall be skipped
        async def gateway_generator_mock(_):
            yield GatewayDescriptor(
                ip_addr="10.1.5.5",
                port=3671,
                supports_tunnelling_tcp=True,
                individual_address=IndividualAddress("5.0.0"),
            )
            yield GatewayDescriptor(
                ip_addr="10.1.0.0",
                port=3671,
                supports_tunnelling_tcp=True,
                individual_address=IndividualAddress("1.0.0"),
            )

        with patch(
            "xknx.io.knxip_interface.GatewayScanner.async_scan",
            new=gateway_generator_mock,
        ), patch(
            "xknx.io.KNXIPInterface._start_tunnelling_tcp",
        ) as start_tunnelling_tcp_mock:
            await interface.start()
            start_tunnelling_tcp_mock.assert_called_once_with(
                gateway_ip="10.1.0.0",
                gateway_port=3671,
            )

    async def test_start_automatic_with_keyring_and_ia(self):
        """Test starting with automatic mode and keyring and individual address."""
        connection_config = ConnectionConfig(
            individual_address=IndividualAddress("1.0.12"),
            secure_config=SecureConfig(
                knxkeys_file_path=self.knxkeys_file,
                knxkeys_password="password",
            ),
        )
        assert connection_config.connection_type == ConnectionType.AUTOMATIC
        interface = knx_interface_factory(self.xknx, connection_config)

        # in the test keyfile the only host is 1.0.0 - others shall be skipped
        async def gateway_generator_mock(_):
            yield GatewayDescriptor(
                ip_addr="10.1.5.5",
                port=3671,
                supports_tunnelling_tcp=True,
                individual_address=IndividualAddress("5.0.0"),
            )
            yield GatewayDescriptor(
                ip_addr="10.1.0.0",
                port=3671,
                supports_tunnelling_tcp=True,
                individual_address=IndividualAddress("1.0.0"),
            )

        with patch(
            "xknx.io.knxip_interface.GatewayScanner.async_scan",
            new=gateway_generator_mock,
        ), patch(
            "xknx.io.KNXIPInterface._start_tunnelling_tcp",
        ) as start_tunnelling_tcp_mock:
            await interface.start()
            start_tunnelling_tcp_mock.assert_called_once_with(
                gateway_ip="10.1.0.0",
                gateway_port=3671,
            )

        # IA not listed in keyring
        invalid_config = ConnectionConfig(
            individual_address=IndividualAddress("5.5.5"),
            secure_config=SecureConfig(
                knxkeys_file_path=self.knxkeys_file,
                knxkeys_password="password",
            ),
        )
        assert invalid_config.connection_type == ConnectionType.AUTOMATIC
        interface = knx_interface_factory(self.xknx, invalid_config)
        with patch(
            "xknx.io.knxip_interface.GatewayScanner.async_scan",
            new=gateway_generator_mock,
        ), pytest.raises(InvalidSecureConfiguration):
            await interface.start()

    async def test_start_udp_tunnel_connection(self):
        """Test starting UDP tunnel connection."""
        # without gateway_ip automatic is called
        gateway_ip = "127.0.0.2"
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING,
            gateway_ip=gateway_ip,
        )
        with patch(
            "xknx.io.KNXIPInterface._start_tunnelling_udp"
        ) as start_tunnelling_udp:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            start_tunnelling_udp.assert_called_once_with(
                gateway_ip=gateway_ip,
                gateway_port=3671,
                local_ip=None,
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
                interface._interface.cemi_received_callback == interface.cemi_received
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
                interface._interface.cemi_received_callback == interface.cemi_received
            )
            connect_tcp.assert_called_once_with()

    async def test_start_tcp_tunnel_connection_with_ia(self):
        """Test starting TCP tunnel connection requesting specific tunnel."""
        # without gateway_ip automatic is called
        gateway_ip = "127.0.0.2"
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP,
            gateway_ip=gateway_ip,
            individual_address="1.1.1",
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
            assert interface._interface._requested_address == IndividualAddress("1.1.1")
            assert interface._interface.auto_reconnect
            assert interface._interface.auto_reconnect_wait == 3
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.cemi_received_callback == interface.cemi_received
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
            start_routing.assert_called_once_with(local_ip=local_ip)

        with patch("xknx.io.routing.Routing.connect") as connect_routing:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            assert isinstance(interface._interface, Routing)
            assert interface._interface.local_ip == local_ip
            assert interface._interface.multicast_group == "224.0.23.12"
            assert interface._interface.multicast_port == 3671
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.cemi_received_callback == interface.cemi_received
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
            start_automatic_mock.assert_called_once_with(local_ip=None, keyring=None)

    async def test_threaded_send_cemi(self):
        """Test sending cemi with threaded connection."""
        # pylint: disable=attribute-defined-outside-init
        self.main_thread = threading.get_ident()

        def assert_thread(*args, **kwargs):
            """Test threaded connection."""
            assert self.main_thread != threading.get_ident()
            return DEFAULT  # to not disable `return_value` of send_cemi_mock

        local_ip = "127.0.0.1"
        # set local_ip to avoid gateway scanner; use routing as it is the simplest mode
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.ROUTING, local_ip=local_ip, threaded=True
        )
        cemi_mock = Mock()
        with patch(
            "xknx.io.routing.Routing.connect", side_effect=assert_thread
        ) as connect_routing_mock, patch(
            "xknx.io.routing.Routing.send_cemi",
            side_effect=assert_thread,
            return_value="test",
        ) as send_cemi_mock, patch(
            "xknx.io.routing.Routing.disconnect", side_effect=assert_thread
        ) as disconnect_routing_mock:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            connect_routing_mock.assert_called_once_with()
            assert await interface.send_cemi(cemi_mock) == "test"
            send_cemi_mock.assert_called_once_with(cemi_mock)
            await interface.stop()
            disconnect_routing_mock.assert_called_once_with()
            assert interface._interface is None

    async def test_start_secure_connection_knx_keys_user_id(self):
        """Test starting a secure connection from a knxkeys file with user_id."""
        gateway_ip = "192.168.1.1"
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP_SECURE,
            gateway_ip=gateway_ip,
            secure_config=SecureConfig(
                user_id=3,
                knxkeys_file_path=self.knxkeys_file,
                knxkeys_password="password",
            ),
        )
        gateway_description = GatewayDescriptor(
            ip_addr=gateway_ip,
            port=3671,
            supports_tunnelling_tcp=True,
            supports_secure=True,
            individual_address=IndividualAddress("1.0.0"),
        )
        gateway_description.tunnelling_requires_secure = True
        with patch(
            "xknx.io.knxip_interface.request_description",
            return_value=gateway_description,
        ), patch("xknx.io.tunnel.SecureTunnel.connect") as connect_secure:
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
                interface._interface.cemi_received_callback == interface.cemi_received
            )
            connect_secure.assert_called_once_with()

    async def test_start_secure_connection_knx_keys_ia(self):
        """Test starting a secure connection from a knxkeys file with individual address."""
        gateway_ip = "192.168.1.1"
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP_SECURE,
            gateway_ip=gateway_ip,
            individual_address="1.0.12",
            secure_config=SecureConfig(
                knxkeys_file_path=self.knxkeys_file, knxkeys_password="password"
            ),
        )
        # result of request_description is currently not used when IA is defined
        with patch(
            "xknx.io.knxip_interface.request_description",
        ), patch("xknx.io.tunnel.SecureTunnel.connect") as connect_secure:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            assert isinstance(interface._interface, SecureTunnel)
            assert interface._interface.gateway_ip == gateway_ip
            assert interface._interface.gateway_port == 3671
            assert interface._interface.auto_reconnect is True
            assert interface._interface.auto_reconnect_wait == 3
            assert interface._interface._user_id == 5
            assert interface._interface._user_password == "user3"
            assert (
                interface._interface._device_authentication_password
                == "authenticationcode"
            )
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.cemi_received_callback == interface.cemi_received
            )
            connect_secure.assert_called_once_with()

    async def test_start_secure_connection_knx_keys_first_interface(self):
        """Test starting a secure connection from a knxkeys file."""
        gateway_ip = "192.168.1.1"
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.TUNNELING_TCP_SECURE,
            gateway_ip=gateway_ip,
            secure_config=SecureConfig(
                knxkeys_file_path=self.knxkeys_file, knxkeys_password="password"
            ),
        )
        gateway_description = GatewayDescriptor(
            ip_addr=gateway_ip,
            port=3671,
            supports_tunnelling_tcp=True,
            supports_secure=True,
            individual_address=IndividualAddress("1.0.0"),
        )
        gateway_description.tunnelling_requires_secure = True
        gateway_description.tunnelling_slots = {
            IndividualAddress("1.0.1"): TunnelingSlotStatus(
                usable=True, authorized=False, free=False
            ),
            IndividualAddress("1.0.11"): TunnelingSlotStatus(
                usable=True, authorized=False, free=True
            ),
            IndividualAddress("1.0.12"): TunnelingSlotStatus(
                usable=True, authorized=False, free=True
            ),
            IndividualAddress("1.0.13"): TunnelingSlotStatus(
                usable=True, authorized=False, free=True
            ),
        }
        with patch(
            "xknx.io.knxip_interface.request_description",
            return_value=gateway_description,
        ), patch("xknx.io.tunnel.SecureTunnel.connect") as connect_secure:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            assert isinstance(interface._interface, SecureTunnel)
            assert interface._interface.gateway_ip == gateway_ip
            assert interface._interface.gateway_port == 3671
            assert interface._interface.auto_reconnect is True
            assert interface._interface.auto_reconnect_wait == 3
            assert interface._interface._user_id == 4
            assert interface._interface._user_password == "user2"
            assert (
                interface._interface._device_authentication_password
                == "authenticationcode"
            )
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.cemi_received_callback == interface.cemi_received
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
                interface._interface.cemi_received_callback == interface.cemi_received
            )
            connect_secure.assert_called_once_with()

    @pytest.mark.parametrize(
        "connection_config",
        [
            ConnectionConfig(  # invalid user_id
                connection_type=ConnectionType.TUNNELING_TCP_SECURE,
                gateway_ip="192.168.1.1",
                secure_config=SecureConfig(
                    user_id=12,
                    knxkeys_file_path=knxkeys_file,
                    knxkeys_password="password",
                ),
            ),
            ConnectionConfig(  # invalid IA
                connection_type=ConnectionType.TUNNELING_TCP_SECURE,
                gateway_ip="192.168.1.1",
                individual_address="9.9.9",
                secure_config=SecureConfig(
                    knxkeys_file_path=knxkeys_file,
                    knxkeys_password="password",
                ),
            ),
            ConnectionConfig(  # no secure_config
                connection_type=ConnectionType.TUNNELING_TCP_SECURE,
                gateway_ip="192.168.1.1",
                individual_address="9.9.9",
            ),
            ConnectionConfig(  # no password
                connection_type=ConnectionType.TUNNELING_TCP_SECURE,
                gateway_ip="192.168.1.1",
                secure_config=SecureConfig(
                    user_id=3,
                    knxkeys_file_path=knxkeys_file,
                ),
            ),
        ],
    )
    async def test_invalid_secure_error(self, connection_config):
        """Test ip secure invalid configurations."""
        gateway_ip = "192.168.1.1"
        gateway_description = GatewayDescriptor(
            ip_addr=gateway_ip,
            port=3671,
            supports_tunnelling_tcp=True,
            supports_secure=True,
            individual_address=IndividualAddress("1.0.0"),
        )
        gateway_description.tunnelling_requires_secure = True
        with patch(
            "xknx.io.knxip_interface.request_description",
            return_value=gateway_description,
        ), pytest.raises(InvalidSecureConfiguration):
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

    async def test_start_secure_routing_knx_keys(self):
        """Test starting a secure routing connection from a knxkeys file."""
        backbone_key = bytes.fromhex("cf89fd0f18f4889783c7ef44ee1f5e14")
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.ROUTING_SECURE,
            secure_config=SecureConfig(
                knxkeys_file_path=self.knxkeys_file, knxkeys_password="password"
            ),
        )
        with patch("xknx.io.routing.SecureRouting.connect") as connect_secure:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            assert isinstance(interface._interface, SecureRouting)
            assert interface._interface.backbone_key == backbone_key
            assert interface._interface.latency_ms == 1000
            assert isinstance(interface._interface.transport, SecureGroup)
            assert interface._interface.transport.remote_addr == (
                "224.0.23.12",
                3671,
            )
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.cemi_received_callback == interface.cemi_received
            )
            connect_secure.assert_called_once_with()

    async def test_start_secure_routing_manual(self):
        """Test starting a secure routing connection from a knxkeys file."""
        backbone_key_str = "cf89fd0f18f4889783c7ef44ee1f5e14"
        backbone_key = bytes.fromhex(backbone_key_str)
        connection_config = ConnectionConfig(
            connection_type=ConnectionType.ROUTING_SECURE,
            secure_config=SecureConfig(backbone_key=backbone_key_str, latency_ms=2000),
        )
        with patch("xknx.io.routing.SecureRouting.connect") as connect_secure:
            interface = knx_interface_factory(self.xknx, connection_config)
            await interface.start()
            assert isinstance(interface._interface, SecureRouting)
            assert interface._interface.backbone_key == backbone_key
            assert interface._interface.latency_ms == 2000
            assert isinstance(interface._interface.transport, SecureGroup)
            assert interface._interface.transport.remote_addr == (
                "224.0.23.12",
                3671,
            )
            assert (  # pylint: disable=comparison-with-callable
                interface._interface.cemi_received_callback == interface.cemi_received
            )
            connect_secure.assert_called_once_with()
