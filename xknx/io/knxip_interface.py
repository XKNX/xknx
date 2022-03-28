"""
KNXIPInterface manages KNX/IP Tunneling or Routing connections.

* It searches for available devices and connects with the corresponding connect method.
* It passes KNX telegrams from the network and
* provides callbacks after having received a telegram from the network.

"""
from __future__ import annotations

import asyncio
import logging
import threading
from typing import TYPE_CHECKING, Awaitable, TypeVar

from xknx.exceptions import CommunicationError, XKNXException

from ..exceptions.exception import (
    InterfaceWithUserIdNotFound,
    InvalidSecureConfiguration,
)
from ..secure import Keyring, load_key_ring
from .connection import ConnectionConfig, ConnectionType
from .gateway_scanner import GatewayDescriptor, GatewayScanFilter, GatewayScanner
from .routing import Routing
from .tunnel import SecureTunnel, TCPTunnel, UDPTunnel, _Tunnel
from .util import find_local_ip, validate_ip

if TYPE_CHECKING:
    import concurrent

    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

    from .interface import Interface

logger = logging.getLogger("xknx.log")

T = TypeVar("T")  # pylint: disable=invalid-name


def knx_interface_factory(
    xknx: XKNX, connection_config: ConnectionConfig
) -> KNXIPInterface:
    """Create KNX/IP interface from config."""
    if connection_config.threaded:
        return KNXIPInterfaceThreaded(xknx=xknx, connection_config=connection_config)
    return KNXIPInterface(xknx=xknx, connection_config=connection_config)


class KNXIPInterface:
    """Class for managing KNX/IP Tunneling or Routing connections."""

    def __init__(
        self,
        xknx: XKNX,
        connection_config: ConnectionConfig = ConnectionConfig(),
    ):
        """Initialize KNXIPInterface class."""
        self.xknx = xknx
        self.connection_config = connection_config
        self._gateway_info: GatewayDescriptor | None = None
        self._interface: Interface | None = None

    async def start(self) -> None:
        """Start KNX/IP interface. Raise `CommunicationError` if connection fails."""
        await self._start()

    async def _start(self) -> None:
        """Start interface. Connecting KNX/IP device with the selected method."""
        if self.connection_config.connection_type == ConnectionType.ROUTING:
            await self._start_routing(local_ip=self.connection_config.local_ip)
        elif (
            self.connection_config.connection_type == ConnectionType.TUNNELING
            and self.connection_config.gateway_ip is not None
        ):
            await self._start_tunnelling_udp(
                local_ip=self.connection_config.local_ip,
                local_port=self.connection_config.local_port,
                gateway_ip=self.connection_config.gateway_ip,
                gateway_port=self.connection_config.gateway_port,
                auto_reconnect=self.connection_config.auto_reconnect,
                auto_reconnect_wait=self.connection_config.auto_reconnect_wait,
                route_back=self.connection_config.route_back,
            )
        elif (
            self.connection_config.connection_type == ConnectionType.TUNNELING_TCP
            and self.connection_config.gateway_ip is not None
        ):
            await self._start_tunnelling_tcp(
                gateway_ip=self.connection_config.gateway_ip,
                gateway_port=self.connection_config.gateway_port,
                auto_reconnect=self.connection_config.auto_reconnect,
                auto_reconnect_wait=self.connection_config.auto_reconnect_wait,
            )
        elif (
            self.connection_config.connection_type
            == ConnectionType.TUNNELING_TCP_SECURE
            and self.connection_config.gateway_ip is not None
            and self.connection_config.secure_config is not None
        ):
            secure_config = self.connection_config.secure_config
            user_id: int
            user_password: str
            device_authentication_password: str | None
            if (
                secure_config.knxkeys_file_path is not None
                and secure_config.knxkeys_password is not None
            ):
                keyring: Keyring = load_key_ring(
                    secure_config.knxkeys_file_path, secure_config.knxkeys_password
                )
                if secure_config.user_id is not None:
                    user_id = secure_config.user_id
                    interface = keyring.get_interface_by_user_id(user_id)
                    if interface is None:
                        raise InterfaceWithUserIdNotFound()

                    user_password = interface.decrypted_password
                    device_authentication_password = interface.decrypted_authentication
                else:
                    interface = keyring.interfaces[0]
                    user_id = interface.user_id
                    user_password = interface.decrypted_password
                    device_authentication_password = interface.decrypted_authentication
            else:
                user_id = secure_config.user_id or 2
                if secure_config.user_password is None:
                    raise InvalidSecureConfiguration()

                user_password = secure_config.user_password
                device_authentication_password = (
                    secure_config.device_authentication_password
                )

            await self._start_secure_tunnelling_tcp(
                gateway_ip=self.connection_config.gateway_ip,
                gateway_port=self.connection_config.gateway_port,
                auto_reconnect=self.connection_config.auto_reconnect,
                auto_reconnect_wait=self.connection_config.auto_reconnect_wait,
                user_id=user_id,
                user_password=user_password,
                device_authentication_password=device_authentication_password,
            )
        else:
            await self._start_automatic()

    async def _start_automatic(self) -> None:
        """Start GatewayScanner and connect to the found device."""
        scan_filter = self.connection_config.scan_filter
        gateway, local_interface_ip = await self.find_gateway(scan_filter)
        self._gateway_info = gateway

        if gateway.supports_tunnelling and scan_filter.routing is not True:
            await self._start_tunnelling_udp(
                local_interface_ip,
                self.connection_config.local_port,
                gateway.ip_addr,
                gateway.port,
                self.connection_config.auto_reconnect,
                self.connection_config.auto_reconnect_wait,
                route_back=self.connection_config.route_back,
            )
        elif gateway.supports_routing:
            await self._start_routing(local_interface_ip)

    async def _start_tunnelling_tcp(
        self,
        gateway_ip: str,
        gateway_port: int,
        auto_reconnect: bool,
        auto_reconnect_wait: int,
    ) -> None:
        """Start KNX/IP TCP tunnel."""
        validate_ip(gateway_ip, address_name="Gateway IP address")
        logger.debug(
            "Starting tunnel to %s:%s over TCP",
            gateway_ip,
            gateway_port,
        )
        self._interface = TCPTunnel(
            self.xknx,
            gateway_ip=gateway_ip,
            gateway_port=gateway_port,
            telegram_received_callback=self.telegram_received,
            auto_reconnect=auto_reconnect,
            auto_reconnect_wait=auto_reconnect_wait,
        )
        await self._interface.connect()

    async def _start_secure_tunnelling_tcp(
        self,
        gateway_ip: str,
        gateway_port: int,
        auto_reconnect: bool,
        auto_reconnect_wait: int,
        user_id: int,
        user_password: str,
        device_authentication_password: str | None,
    ) -> None:
        """Start KNX/IP TCP tunnel."""
        validate_ip(gateway_ip, address_name="Gateway IP address")
        logger.debug(
            "Starting secure tunnel to %s:%s over TCP",
            gateway_ip,
            gateway_port,
        )
        self._interface = SecureTunnel(
            self.xknx,
            gateway_ip=gateway_ip,
            gateway_port=gateway_port,
            auto_reconnect=auto_reconnect,
            auto_reconnect_wait=auto_reconnect_wait,
            user_id=user_id,
            user_password=user_password,
            device_authentication_password=device_authentication_password,
            telegram_received_callback=self.telegram_received,
        )
        await self._interface.connect()

    async def _start_tunnelling_udp(
        self,
        local_ip: str | None,
        local_port: int,
        gateway_ip: str,
        gateway_port: int,
        auto_reconnect: bool,
        auto_reconnect_wait: int,
        route_back: bool,
    ) -> None:
        """Start KNX/IP UDP tunnel."""
        validate_ip(gateway_ip, address_name="Gateway IP address")
        if local_ip is None:
            local_ip = find_local_ip(gateway_ip=gateway_ip)
        validate_ip(local_ip, address_name="Local IP address")
        logger.debug(
            "Starting tunnel from %s:%s to %s:%s",
            local_ip,
            local_port,
            gateway_ip,
            gateway_port,
        )
        self._interface = UDPTunnel(
            self.xknx,
            gateway_ip=gateway_ip,
            gateway_port=gateway_port,
            local_ip=local_ip,
            local_port=local_port,
            route_back=route_back,
            telegram_received_callback=self.telegram_received,
            auto_reconnect=auto_reconnect,
            auto_reconnect_wait=auto_reconnect_wait,
        )
        await self._interface.connect()

    async def _start_routing(self, local_ip: str | None = None) -> None:
        """Start KNX/IP Routing."""
        if local_ip is None:
            scan_filter = self.connection_config.scan_filter
            scan_filter.routing = True
            _gateway, local_ip = await self.find_gateway(scan_filter)
            self._gateway_info = _gateway
        validate_ip(local_ip, address_name="Local IP address")
        logger.debug("Starting Routing from %s as %s", local_ip, self.xknx.own_address)
        self._interface = Routing(self.xknx, self.telegram_received, local_ip)
        await self._interface.connect()

    async def stop(self) -> None:
        """Stop connected interfae (either Tunneling or Routing)."""
        if self._interface is not None:
            await self._interface.disconnect()
            self._interface = None

    def telegram_received(self, telegram: Telegram) -> None:
        """Put received telegram into queue. Callback for having received telegram."""
        self.xknx.telegrams.put_nowait(telegram)

    async def send_telegram(self, telegram: "Telegram") -> None:
        """Send telegram to connected device (either Tunneling or Routing)."""
        if self._interface is None:
            raise CommunicationError("KNX/IP interface not connected")
        return await self._interface.send_telegram(telegram)

    async def gateway_info(self) -> GatewayDescriptor | None:
        """Get gateway descriptor from interface."""
        if self._gateway_info is not None:
            return self._gateway_info
        if isinstance(self._interface, _Tunnel):
            return await self._interface.request_description()
        return None

    async def find_gateway(
        self, scan_filter: GatewayScanFilter
    ) -> tuple[GatewayDescriptor, str]:
        """Find Gateway and connect to it."""
        gatewayscanner = GatewayScanner(self.xknx, scan_filter=scan_filter)
        gateways = await gatewayscanner.scan()

        if not gateways:
            raise XKNXException("No Gateways found")
        gateway = gateways[0]
        # on Linux gateway.local_ip can be any interface listening to the
        # multicast group (even 127.0.0.1) so we set the interface with find_local_ip
        local_interface_ip = find_local_ip(gateway_ip=gateway.ip_addr)

        return gateway, local_interface_ip


class KNXIPInterfaceThreaded(KNXIPInterface):
    """Class for managing KNX/IP Tunneling or Routing connections."""

    def __init__(
        self,
        xknx: XKNX,
        connection_config: ConnectionConfig = ConnectionConfig(),
    ):
        """Initialize KNXIPInterface class."""
        super().__init__(xknx, connection_config)
        self._main_loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self._thread_loop: asyncio.AbstractEventLoop

        loop_loaded = threading.Event()
        connection_thread = threading.Thread(
            target=self._init_connection_loop,
            args=[loop_loaded],
            name="KNX Interface",
            daemon=True,
        )
        connection_thread.start()
        loop_loaded.wait()  # wait for the thread to initialize its loop

    def _init_connection_loop(self, loop_loaded: threading.Event) -> None:
        """Start KNX/IP interface in its own thread."""
        self._thread_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._thread_loop)
        loop_loaded.set()
        self._thread_loop.run_forever()

    async def _await_from_connection_thread(self, coro: Awaitable[T]) -> T:
        """Await coroutine in different thread."""
        fut = asyncio.run_coroutine_threadsafe(coro, self._thread_loop)
        finished = threading.Event()

        def fut_finished_cb(_: concurrent.futures.Future[T]) -> None:
            """Fire threading.Event when the future is finished."""
            finished.set()

        fut.add_done_callback(fut_finished_cb)
        # wait on that event in an executor, yielding control to _main_loop
        await self._main_loop.run_in_executor(None, finished.wait)
        return fut.result()

    async def start(self) -> None:
        """Start KNX/IP interface."""
        return await self._await_from_connection_thread(self._start())

    async def stop(self) -> None:
        """Stop connected interfae (either Tunneling or Routing)."""
        if self._interface is not None:
            await self._await_from_connection_thread(self._interface.disconnect())
            self._interface = None

    def telegram_received(self, telegram: Telegram) -> None:
        """Put received telegram into queue. Callback for having received telegram."""
        self._main_loop.call_soon_threadsafe(self.xknx.telegrams.put_nowait, telegram)

    async def send_telegram(self, telegram: "Telegram") -> None:
        """Send telegram to connected device (either Tunneling or Routing)."""
        if self._interface is None:
            raise CommunicationError("KNX/IP interface not connected")

        return await self._await_from_connection_thread(
            self._interface.send_telegram(telegram)
        )

    async def gateway_info(self) -> GatewayDescriptor | None:
        """Get gateway descriptor from interface."""
        if self._gateway_info is not None:
            return self._gateway_info
        if isinstance(self._interface, _Tunnel):
            return await self._await_from_connection_thread(
                self._interface.request_description()
            )
        return None
