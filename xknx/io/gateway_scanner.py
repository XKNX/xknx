"""
GatewayScanner is an abstraction for searching for KNX/IP devices on the local network.

* It walks through all network interfaces
* and sends UDP multicast search requests
* it returns the first found device
"""

import anyio
from typing import List

import netifaces

from xknx.knxip import (
    HPAI, DIBServiceFamily, DIBSuppSVCFamilies, KNXIPFrame, KNXIPServiceType,
    SearchResponse)

from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT
from .udp_client import UDPClient


class GatewayDescriptor:
    """Used to return information about the discovered gateways."""

    # pylint: disable=too-few-public-methods

    def __init__(self,
                 name: str,
                 ip_addr: str,
                 port: int,
                 local_interface: str,
                 local_ip: str,
                 supports_tunnelling: bool = False,
                 supports_routing: bool = False) -> None:
        """Initialize GatewayDescriptor class."""
        # pylint: disable=too-many-arguments
        self.name = name
        self.ip_addr = ip_addr
        self.port = port
        self.local_interface = local_interface
        self.local_ip = local_ip
        self.supports_routing = supports_routing
        self.supports_tunnelling = supports_tunnelling

    def __str__(self):
        """Return object as readable string."""
        return '<GatewayDescriptor name="{0}" addr="{1}:{2}" local="{3}@{4}" routing="{5}" tunnelling="{6}" />'.format(
            self.name,
            self.ip_addr,
            self.port,
            self.local_ip,
            self.local_interface,
            self.supports_routing,
            self.supports_tunnelling)


class GatewayScanFilter:
    """Filter to limit gateway scan attempts."""

    # pylint: disable=too-few-public-methods

    def __init__(self,
                 name: str = None,
                 tunnelling: bool = None,
                 routing: bool = None) -> None:
        """Initialize GatewayScanFilter class."""
        self.name = name
        self.tunnelling = tunnelling
        self.routing = routing

    def match(self, gateway: GatewayDescriptor) -> bool:
        """Check whether the given GatewayDescriptor matches the filter."""
        if self.name is not None and self.name != gateway.name:
            return False
        if self.tunnelling is not None and self.tunnelling != gateway.supports_tunnelling:
            return False
        if self.routing is not None and self.routing != gateway.supports_routing:
            return False
        return True


class GatewayScanner():
    """Class for searching KNX/IP devices."""

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 xknx,
                 timeout_in_seconds: int = 4,
                 stop_on_found: int = 1,
                 scan_filter: GatewayScanFilter = GatewayScanFilter()) -> None:
        """Initialize GatewayScanner class."""
        self.xknx = xknx
        self.timeout_in_seconds = timeout_in_seconds
        self.stop_on_found = stop_on_found
        self.scan_filter = scan_filter
        self.found_gateways = []  # List[GatewayDescriptor]
        self._response_received = anyio.create_event()

    async def scan(self) -> List[GatewayDescriptor]:
        """Scan and return a list of GatewayDescriptors on success."""
        async with anyio.create_task_group() as tg:
            await self._send_search_requests(tg)
            async with anyio.move_on_after(self.timeout_in_seconds):
                await self._response_received.wait()

            await tg.cancel_scope.cancel()
        return self.found_gateways

    async def _send_search_requests(self, tg):
        """Find all interfaces with active IPv4 connection to search for gateways."""
        # pylint: disable=no-member
        for interface in netifaces.interfaces():
            try:
                af_inet = netifaces.ifaddresses(interface)[netifaces.AF_INET]
            except KeyError:
                continue
            ip_addr = af_inet[0]["addr"]
            await tg.spawn(self._search_interface, interface, ip_addr)

    async def _search_interface(self, interface, ip_addr):
        """Send a search request on a specific interface."""
        try:
            self.xknx.logger.debug("Searching on %s / %s", interface, ip_addr)

            udp_client = UDPClient(self.xknx,
                                (ip_addr, 0, interface),
                                (DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
                                multicast=True)

            with udp_client.receiver(KNXIPServiceType.SEARCH_RESPONSE) as recv:
                await udp_client.connect()

                self._udp_clients.append(udp_client)

                (local_addr, local_port) = udp_client.getsockname()
                knx_ip_frame = KNXIPFrame(self.xknx)
                knx_ip_frame.init(KNXIPServiceType.SEARCH_REQUEST)
                knx_ip_frame.body.discovery_endpoint = \
                    HPAI(ip_addr=local_addr, port=local_port)
                knx_ip_frame.normalize()
                await udp_client.send(knx_ip_frame)
                async with anyio.move_on_after(self.timeout_in_seconds):
                    async for msg in recv:
                        await self._response_rec_callback(msg, udp_client)
        except Exception as exc:
            self.xknx.logger.info("Could not connect to an KNX/IP device on %s: %s", interface, exc)

    async def _response_rec_callback(self, knx_ip_frame: KNXIPFrame, udp_client: UDPClient) -> None:
        """Verify and handle knxipframe. Callback from internal udpclient."""
        if not isinstance(knx_ip_frame.body, SearchResponse):
            self.xknx.logger.warning("Cant understand knxipframe")
            return

        (found_local_ip, _) = udp_client.getsockname()
        gateway = GatewayDescriptor(name=knx_ip_frame.body.device_name,
                                    ip_addr=knx_ip_frame.body.control_endpoint.ip_addr,
                                    port=knx_ip_frame.body.control_endpoint.port,
                                    local_interface=udp_client.local_addr[2],
                                    local_ip=found_local_ip)
        try:
            dib = knx_ip_frame.body[DIBSuppSVCFamilies]
            gateway.supports_routing = dib.supports(DIBServiceFamily.ROUTING)
            gateway.supports_tunnelling = dib.supports(DIBServiceFamily.TUNNELING)
        except IndexError:
            pass

        await self._add_found_gateway(gateway)

    async def _add_found_gateway(self, gateway):
        if self.scan_filter.match(gateway):
            self.found_gateways.append(gateway)
            if len(self.found_gateways) >= self.stop_on_found:
                await self._response_received.set()

