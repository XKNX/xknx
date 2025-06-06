"""
KNXIPInterface manages KNX/IP Tunneling or Routing connections.

* It searches for available devices and connects with the corresponding connect method.
* It passes KNX telegrams from the network and
* provides callbacks after having received a telegram from the network.

"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
import logging
import threading
from typing import TYPE_CHECKING, Any, TypeVar

from xknx.cemi import CEMIFrame
from xknx.exceptions import (
    CommunicationError,
    InvalidSecureConfiguration,
    XKNXException,
)
from xknx.io import util
from xknx.secure.keyring import InterfaceType, Keyring, XMLInterface, load_keyring
from xknx.telegram import IndividualAddress

from .connection import ConnectionConfig, ConnectionType
from .const import DEFAULT_INDIVIDUAL_ADDRESS
from .gateway_scanner import GatewayDescriptor, GatewayScanner
from .routing import Routing, SecureRouting
from .self_description import request_description
from .tunnel import SecureTunnel, TCPTunnel, UDPTunnel, _Tunnel

if TYPE_CHECKING:
    import concurrent

    from xknx.xknx import XKNX

    from .interface import Interface

logger = logging.getLogger("xknx.log")

T = TypeVar("T")  # pylint: disable=invalid-name


def knx_interface_factory(
    xknx: XKNX,
    connection_config: ConnectionConfig,
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
        connection_config: ConnectionConfig | None = None,
    ) -> None:
        """Initialize KNXIPInterface class."""
        self.xknx = xknx
        self.connection_config = connection_config or ConnectionConfig()
        self._gateway_info: GatewayDescriptor | None = None
        self._interface: Interface | None = None

    async def start(self) -> None:
        """Start KNX/IP interface. Raise `CommunicationError` if connection fails."""
        await self._start()

    async def _start(self) -> None:
        """Start interface. Connecting KNX/IP device with the selected method."""
        if gateway_ip := self.connection_config.gateway_ip:
            gateway_ip = await util.validate_ip(gateway_ip, address_name="Gateway IP")
        if local_ip := self.connection_config.local_ip:
            local_ip = await util.validate_ip(local_ip, address_name="Local IP")
        keyring: Keyring | None = None
        if secure_config := self.connection_config.secure_config:
            if secure_config.keyring is not None:
                keyring = secure_config.keyring
            elif (
                secure_config.knxkeys_file_path is not None
                and secure_config.knxkeys_password is not None
            ):
                keyring = await load_keyring(
                    secure_config.knxkeys_file_path,
                    secure_config.knxkeys_password,
                )
        self.xknx.cemi_handler.data_secure_init(keyring=keyring)

        if self.connection_config.connection_type == ConnectionType.ROUTING:
            await self._start_routing(local_ip=local_ip)
        elif self.connection_config.connection_type == ConnectionType.ROUTING_SECURE:
            await self._start_secure_routing(local_ip=local_ip, keyring=keyring)
        elif (
            self.connection_config.connection_type == ConnectionType.TUNNELING
            and gateway_ip is not None
        ):
            await self._start_tunnelling_udp(
                gateway_ip=gateway_ip,
                gateway_port=self.connection_config.gateway_port,
                local_ip=local_ip,
            )
        elif (
            self.connection_config.connection_type == ConnectionType.TUNNELING_TCP
            and gateway_ip is not None
        ):
            await self._start_tunnelling_tcp(
                gateway_ip=gateway_ip,
                gateway_port=self.connection_config.gateway_port,
            )
        elif (
            self.connection_config.connection_type
            == ConnectionType.TUNNELING_TCP_SECURE
            and gateway_ip is not None
        ):
            await self._start_secure_tunnelling_tcp(
                gateway_ip=gateway_ip,
                gateway_port=self.connection_config.gateway_port,
                keyring=keyring,
            )
        else:
            await self._start_automatic(local_ip=local_ip, keyring=keyring)

    async def _start_automatic(
        self,
        local_ip: str | None,
        keyring: Keyring | None,
    ) -> None:
        """Start GatewayScanner and connect to the found device."""
        keyring_host_filter: set[IndividualAddress] = set()
        if keyring:
            if required_addr := self.connection_config.individual_address:
                _host_ia = keyring.get_tunnel_host_by_interface(
                    tunnelling_slot=required_addr
                )
                if _host_ia is None:
                    raise InvalidSecureConfiguration(
                        f"No host for required address {required_addr} found in keyring file."
                    )
                keyring_host_filter.add(_host_ia)
            else:
                keyring_host_filter.update(
                    interface.host
                    for interface in keyring.interfaces
                    if interface.host is not None
                    and interface.type is InterfaceType.TUNNELING
                )
        async for gateway in GatewayScanner(
            self.xknx,
            local_ip=local_ip,
            scan_filter=self.connection_config.scan_filter,
        ).async_scan():
            if (
                keyring_host_filter
                and gateway.individual_address not in keyring_host_filter
            ):
                logger.debug("Skipping %s. No match in keyring file", gateway)
                continue
            try:
                if gateway.supports_tunnelling_tcp:
                    if gateway.tunnelling_requires_secure:
                        await self._start_secure_tunnelling_tcp(
                            gateway_ip=gateway.ip_addr,
                            gateway_port=gateway.port,
                            gateway_descriptor=gateway,
                            keyring=keyring,
                        )
                    else:
                        await self._start_tunnelling_tcp(
                            gateway_ip=gateway.ip_addr,
                            gateway_port=gateway.port,
                        )
                elif (
                    gateway.supports_tunnelling
                    and not gateway.tunnelling_requires_secure
                ):
                    await self._start_tunnelling_udp(
                        gateway_ip=gateway.ip_addr,
                        gateway_port=gateway.port,
                        local_ip=local_ip,
                    )
                elif gateway.supports_routing and not gateway.routing_requires_secure:
                    await self._start_routing(local_ip=local_ip)
            except CommunicationError as ex:
                logger.debug("Skipping %s. Could not connect: %s", gateway, ex)
                continue
            except InvalidSecureConfiguration as ex:
                logger.debug(
                    "Skipping %s. Invalid secure configuration: %s", gateway, ex
                )
                continue
            else:
                self._gateway_info = gateway
                break
        else:
            raise CommunicationError(
                f"No usable KNX/IP device found{' in keyring file' if keyring_host_filter else ''}."
            )

    async def _start_tunnelling_tcp(
        self,
        gateway_ip: str,
        gateway_port: int,
    ) -> None:
        """Start KNX/IP TCP tunnel."""
        tunnel_address = self.connection_config.individual_address

        logger.debug(
            "Starting tunnel to %s:%s over TCP%s",
            gateway_ip,
            gateway_port,
            f" requesting individual address {tunnel_address}"
            if tunnel_address
            else "",
        )
        self._interface = TCPTunnel(
            self.xknx,
            gateway_ip=gateway_ip,
            gateway_port=gateway_port,
            individual_address=tunnel_address,
            cemi_received_callback=self.cemi_received,
            auto_reconnect=self.connection_config.auto_reconnect,
            auto_reconnect_wait=self.connection_config.auto_reconnect_wait,
        )
        await self._interface.connect()

    async def _start_secure_tunnelling_tcp(
        self,
        gateway_ip: str,
        gateway_port: int,
        gateway_descriptor: GatewayDescriptor | None = None,
        keyring: Keyring | None = None,
    ) -> None:
        """Start KNX/IP Secure TCP tunnel."""
        if (secure_config := self.connection_config.secure_config) is None:
            raise InvalidSecureConfiguration("SecureConfig missing in ConnectionConfig")

        if (
            secure_config.user_id is not None
            and secure_config.user_password is not None
        ):
            user_id = secure_config.user_id
            user_password = secure_config.user_password
            device_authentication_password = (
                secure_config.device_authentication_password
            )
        elif keyring is not None:
            _gateway = gateway_descriptor or await request_description(
                gateway_ip=gateway_ip, gateway_port=gateway_port
            )
            xml_interface = self._get_tunnel_interface_from_keyring(
                keyring=keyring,
                gateway_descriptor=_gateway,
                individual_address=self.connection_config.individual_address,
                config_user_id=secure_config.user_id,
            )
            if (
                xml_interface.user_id is None
                or xml_interface.decrypted_password is None
            ):
                raise InvalidSecureConfiguration(
                    f"No user_id or password found for tunnel {xml_interface.individual_address}"
                )
            user_id = xml_interface.user_id
            user_password = xml_interface.decrypted_password
            device_authentication_password = xml_interface.decrypted_authentication
        else:
            raise InvalidSecureConfiguration(
                "No `user_id` or `knxkeys_file_path` and password found in secure configuration"
            )

        logger.debug(
            "Starting secure tunnel to %s:%s over TCP",
            gateway_ip,
            gateway_port,
        )
        self._interface = SecureTunnel(
            self.xknx,
            gateway_ip=gateway_ip,
            gateway_port=gateway_port,
            auto_reconnect=self.connection_config.auto_reconnect,
            auto_reconnect_wait=self.connection_config.auto_reconnect_wait,
            user_id=user_id,
            user_password=user_password,
            device_authentication_password=device_authentication_password,
            cemi_received_callback=self.cemi_received,
        )
        await self._interface.connect()

    @staticmethod
    def _get_tunnel_interface_from_keyring(
        keyring: Keyring,
        gateway_descriptor: GatewayDescriptor,
        individual_address: IndividualAddress | None = None,
        config_user_id: int | None = None,
    ) -> XMLInterface:
        """
        Get tunnel interface from keyring.

        Precedence: configured individual address > configured user id > first free tunnel interface
        """
        if individual_address:
            if xml_interface := keyring.get_tunnel_interface_by_individual_address(
                individual_address
            ):
                return xml_interface
            raise InvalidSecureConfiguration(
                f"Interface with individual address {individual_address} not found in keyfile"
            )

        if not (host_ia := gateway_descriptor.individual_address):
            raise InvalidSecureConfiguration(
                "Gateway does not provide individual address"
            )
        if config_user_id:
            if xml_interface := keyring.get_tunnel_interface_by_host_and_user_id(
                host=host_ia, user_id=config_user_id
            ):
                return xml_interface
            raise InvalidSecureConfiguration(
                f"Interface of host {host_ia} with user_id {config_user_id} not found in keyfile"
            )

        _free_slots = [
            tunnel_ia
            for tunnel_ia, slot in gateway_descriptor.tunnelling_slots.items()
            if slot.usable and slot.free
        ]
        if not _free_slots:
            raise InvalidSecureConfiguration(
                f"No free tunnelling slots found on gateway {host_ia}"
            )
        for _tunnel_ia in _free_slots:
            if xml_interface := keyring.get_tunnel_interface_by_individual_address(
                tunnelling_slot=_tunnel_ia
            ):
                return xml_interface

        raise InvalidSecureConfiguration(
            "No credentials for any free tunnelling slot found in keyfile"
        )

    async def _start_tunnelling_udp(
        self,
        gateway_ip: str,
        gateway_port: int,
        local_ip: str | None,
    ) -> None:
        """Start KNX/IP UDP tunnel."""
        local_port = self.connection_config.local_port
        route_back = self.connection_config.route_back

        local_ip = local_ip or util.find_local_ip(gateway_ip=gateway_ip)
        if local_ip is None:
            local_ip = await util.get_default_local_ip(gateway_ip)
            if local_ip is None:
                raise XKNXException("No network interface found.")
            route_back = True
            logger.debug("Falling back to default interface and enabling route back.")

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
            cemi_received_callback=self.cemi_received,
            auto_reconnect=self.connection_config.auto_reconnect,
            auto_reconnect_wait=self.connection_config.auto_reconnect_wait,
        )
        await self._interface.connect()

    async def _start_routing(self, local_ip: str | None) -> None:
        """Start KNX/IP Routing."""
        multicast_group = self.connection_config.multicast_group
        multicast_port = self.connection_config.multicast_port

        local_ip = local_ip or await util.get_default_local_ip()
        if local_ip is None:
            raise XKNXException("No network interface found.")

        individual_address = (
            self.connection_config.individual_address or DEFAULT_INDIVIDUAL_ADDRESS
        )

        logger.debug(
            "Starting Routing from %s as %s via %s:%s",
            local_ip,
            individual_address,
            multicast_group,
            multicast_port,
        )
        self._interface = Routing(
            self.xknx,
            individual_address=individual_address,
            cemi_received_callback=self.cemi_received,
            local_ip=local_ip,
            multicast_group=multicast_group,
            multicast_port=multicast_port,
        )
        await self._interface.connect()

    async def _start_secure_routing(
        self,
        local_ip: str | None,
        keyring: Keyring | None = None,
    ) -> None:
        """Start KNX/IP Routing."""
        if self.connection_config.secure_config is None:
            raise InvalidSecureConfiguration("SecureConfig missing in ConnectionConfig")
        backbone_key = self.connection_config.secure_config.backbone_key
        latency_ms = self.connection_config.secure_config.latency_ms
        multicast_group = self.connection_config.multicast_group
        multicast_port = self.connection_config.multicast_port

        if keyring is not None and keyring.backbone is not None:
            # default to manually configured values
            backbone_key = backbone_key or keyring.backbone.decrypted_key
            latency_ms = latency_ms or keyring.backbone.latency
            if keyring.backbone.multicast_address:
                multicast_group = keyring.backbone.multicast_address
        if not backbone_key:
            raise InvalidSecureConfiguration(
                "No backbone key found in secure configuration"
            )

        local_ip = local_ip or await util.get_default_local_ip()
        if local_ip is None:
            raise XKNXException("No network interface found.")

        individual_address = (
            self.connection_config.individual_address or DEFAULT_INDIVIDUAL_ADDRESS
        )

        logger.debug(
            "Starting Secure Routing from %s as %s via %s:%s",
            local_ip,
            individual_address,
            multicast_group,
            multicast_port,
        )
        self._interface = SecureRouting(
            self.xknx,
            individual_address=individual_address,
            cemi_received_callback=self.cemi_received,
            local_ip=local_ip,
            backbone_key=backbone_key,
            latency_ms=latency_ms,
            multicast_group=multicast_group,
            multicast_port=multicast_port,
        )
        await self._interface.connect()

    async def stop(self) -> None:
        """Stop connected interfae (either Tunneling or Routing)."""
        if self._interface is not None:
            await self._interface.disconnect()
            self._interface = None

    def cemi_received(self, raw_cemi: bytes) -> None:
        """Pass raw CEMIFrame data to CEMIHandler. Callback for having received CEMIFrames."""
        self.xknx.cemi_handler.handle_raw_cemi(raw_cemi)

    async def send_cemi(self, cemi: CEMIFrame) -> None:
        """Send CEMIFrame to connected device (either Tunneling or Routing)."""
        # to ease converting L_Data.req CEMI frames to L_Data.ind and local confirmation
        # in routing we pass `CEMIFrame` from the CEMIHandler here, instead of raw bytes
        if self._interface is None:
            raise CommunicationError("KNX/IP interface not connected")
        return await self._interface.send_cemi(cemi)

    async def gateway_info(self) -> GatewayDescriptor | None:
        """Get gateway descriptor from interface."""
        if self._gateway_info is not None:
            return self._gateway_info
        if isinstance(self._interface, _Tunnel):
            return await self._interface.request_description()
        return None


class KNXIPInterfaceThreaded(KNXIPInterface):
    """Class for managing KNX/IP Tunneling or Routing connections."""

    def __init__(
        self,
        xknx: XKNX,
        connection_config: ConnectionConfig | None = None,
    ) -> None:
        """Initialize KNXIPInterface class."""
        super().__init__(xknx, connection_config)
        self._main_loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self._connection_thread: threading.Thread | None = None
        self._thread_loop: asyncio.AbstractEventLoop | None = None

    def _init_connection_thread(self) -> None:
        """Start KNX/IP interface in its own thread."""
        loop_loaded = threading.Event()
        self._connection_thread = threading.Thread(
            target=self._init_connection_loop,
            args=[loop_loaded],
            name="KNX Interface",
            daemon=True,
        )
        self._connection_thread.start()
        loop_loaded.wait()  # wait for the thread to initialize its loop

    def _init_connection_loop(self, loop_loaded: threading.Event) -> None:
        """Start KNX/IP interface in its own thread."""
        self._thread_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._thread_loop)
        loop_loaded.set()
        self._thread_loop.run_forever()

    async def _await_from_connection_thread(self, coro: Coroutine[Any, Any, T]) -> T:
        """Await coroutine in different thread."""
        if self._thread_loop is None:
            raise CommunicationError("KNX connection thread not initialized.")

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
        if self._connection_thread is not None or self._thread_loop is not None:
            raise CommunicationError("KNX threaded interface already initialized.")
        await self._main_loop.run_in_executor(None, self._init_connection_thread)
        try:
            return await self._await_from_connection_thread(self._start())
        except CommunicationError:
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop connected interface (either Tunneling or Routing)."""
        if self._interface is not None:
            await self._await_from_connection_thread(self._interface.disconnect())
            self._interface = None
        if self._thread_loop is not None:
            self._thread_loop.call_soon_threadsafe(self._thread_loop.stop)
            self._thread_loop = None
        if self._connection_thread is not None:
            self._connection_thread.join()
            self._connection_thread = None

    def cemi_received(self, raw_cemi: bytes) -> None:
        """Pass CEMIFrame to CEMIHandler. Callback for having received CEMIFrames."""
        self._main_loop.call_soon_threadsafe(super().cemi_received, raw_cemi)

    async def send_cemi(self, cemi: CEMIFrame) -> None:
        """Send CEMIFrame to connected device (either Tunneling or Routing)."""
        if self._interface is None:
            raise CommunicationError("KNX/IP interface not connected")

        return await self._await_from_connection_thread(self._interface.send_cemi(cemi))

    async def gateway_info(self) -> GatewayDescriptor | None:
        """Get gateway descriptor from interface."""
        if self._gateway_info is not None:
            return self._gateway_info
        if isinstance(self._interface, _Tunnel):
            return await self._await_from_connection_thread(
                self._interface.request_description()
            )
        return None
