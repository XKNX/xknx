"""
GatewayScanner is an abstraction for searching for KNX/IP devices on the local network.

* It walks through all network interfaces
* and sends UDP multicast search requests
* it returns the first found device
"""

import asyncio
from typing import List

import netifaces
from xknx.knxip import (HPAI, DIBServiceFamily, DIBSuppSVCFamilies, KNXIPFrame,
                        KNXIPServiceType, SearchResponse)

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
        return '<GatewayDescriptor name="{0}" addr="{1}:{2}" local="{3}@{4}" routing="{5}" tunnelling="{6} />'.format(
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
        self._udp_clients = []
        self._response_received_or_timeout = asyncio.Event()
        self._timeout_callback = None
        self._timeout_handle = None

    async def scan(self) -> List[GatewayDescriptor]:
        """Scan and return a list of GatewayDescriptors on success."""
        await self._send_search_requests()
        await self._start_timeout()
        await self._response_received_or_timeout.wait()
        await self._stop()
        await self._stop_timeout()
        return self.found_gateways

    async def _stop(self):
        """Stop tearing down udpclient."""
        for udp_client in self._udp_clients:
            await udp_client.stop()

    async def _send_search_requests(self):
        """Send search requests on all connected interfaces."""
        # pylint: disable=no-member
        for interface in netifaces.interfaces():
            try:
                af_inet = netifaces.ifaddresses(interface)[netifaces.AF_INET]
                ip_addr = af_inet[0]["addr"]
                await self._search_interface(interface, ip_addr)
            except KeyError:
                self.xknx.logger.info("Could not connect to an KNX/IP device on %s", interface)
                continue

    async def _search_interface(self, interface, ip_addr):
        """Search on a specific interface."""
        self.xknx.logger.debug("Searching on %s / %s", interface, ip_addr)

        udp_client = UDPClient(self.xknx,
                               (ip_addr, 0, interface),
                               (DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
                               multicast=True)

        udp_client.register_callback(
            self._response_rec_callback, [KNXIPServiceType.SEARCH_RESPONSE])
        await udp_client.connect()

        self._udp_clients.append(udp_client)

        (local_addr, local_port) = udp_client.getsockname()
        knx_ip_frame = KNXIPFrame(self.xknx)
        knx_ip_frame.init(KNXIPServiceType.SEARCH_REQUEST)
        knx_ip_frame.body.discovery_endpoint = \
            HPAI(ip_addr=local_addr, port=local_port)
        knx_ip_frame.normalize()
        udp_client.send(knx_ip_frame)

    def _response_rec_callback(self, knx_ip_frame: KNXIPFrame, udp_client: UDPClient) -> None:
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

        self._add_found_gateway(gateway)

    def _add_found_gateway(self, gateway):
        if self.scan_filter.match(gateway):
            self.found_gateways.append(gateway)
            if len(self.found_gateways) >= self.stop_on_found:
                self._response_received_or_timeout.set()

    def _timeout(self):
        """Handle timeout for not having received enough SearchResponse."""
        self._response_received_or_timeout.set()

    async def _start_timeout(self):
        """Start time out."""
        self._timeout_handle = self.xknx.loop.call_later(
            self.timeout_in_seconds, self._timeout)

    async def _stop_timeout(self):
        """Stop/cancel timeout."""
        self._timeout_handle.cancel()
