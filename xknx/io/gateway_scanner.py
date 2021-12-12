"""
GatewayScanner is an abstraction for searching for KNX/IP devices on the local network.

* It walks through all network interfaces
* and sends UDP multicast search requests
* it returns the first found device
"""
from __future__ import annotations

import asyncio
from functools import partial
import logging
from typing import TYPE_CHECKING

import netifaces
from xknx.knxip import (
    HPAI,
    DIBDeviceInformation,
    DIBServiceFamily,
    DIBSuppSVCFamilies,
    KNXIPFrame,
    KNXIPServiceType,
    SearchRequest,
    SearchResponse,
)
from xknx.telegram import IndividualAddress

from .udp_client import UDPClient

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class GatewayDescriptor:
    """Used to return information about the discovered gateways."""

    def __init__(
        self,
        name: str,
        ip_addr: str,
        port: int,
        local_interface: str,
        local_ip: str,
        supports_routing: bool = False,
        supports_tunnelling: bool = False,
        individual_address: IndividualAddress | None = None,
    ):
        """Initialize GatewayDescriptor class."""
        self.name = name
        self.ip_addr = ip_addr
        self.port = port
        self.local_interface = local_interface
        self.local_ip = local_ip
        self.supports_routing = supports_routing
        self.supports_tunnelling = supports_tunnelling
        self.individual_address = individual_address

    def __repr__(self) -> str:
        """Return object as representation string."""
        return (
            "GatewayDescriptor(\n"
            f"    name={self.name},\n"
            f"    ip_addr={self.ip_addr},\n"
            f"    port={self.port},\n"
            f"    local_interface={self.local_interface},\n"
            f"    local_ip={self.local_ip},\n"
            f"    supports_routing={self.supports_routing},\n"
            f"    supports_tunnelling={self.supports_tunnelling},\n"
            f"    individual_address={self.individual_address}\n"
            ")"
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f"{self.individual_address} - {self.name} @ {self.ip_addr}:{self.port}"


class GatewayScanFilter:
    """Filter to limit gateway scan attempts.

    If `tunnelling` and `routing` are set it is treated as AND.
    KNX/IP devices that don't support `tunnelling` or `routing` aren't matched.
    """

    def __init__(
        self,
        name: str | None = None,
        tunnelling: bool | None = None,
        routing: bool | None = None,
    ):
        """Initialize GatewayScanFilter class."""
        self.name = name
        self.tunnelling = tunnelling
        self.routing = routing

    def match(self, gateway: GatewayDescriptor) -> bool:
        """Check whether the device is a gateway and given GatewayDescriptor matches the filter."""
        if self.name is not None and self.name != gateway.name:
            return False
        if (
            self.tunnelling is not None
            and self.tunnelling != gateway.supports_tunnelling
        ):
            return False
        if self.routing is not None and self.routing != gateway.supports_routing:
            return False
        return gateway.supports_tunnelling or gateway.supports_routing


class GatewayScanner:
    """Class for searching KNX/IP devices."""

    def __init__(
        self,
        xknx: XKNX,
        timeout_in_seconds: float = 4.0,
        stop_on_found: int | None = 1,
        scan_filter: GatewayScanFilter = GatewayScanFilter(),
    ):
        """Initialize GatewayScanner class."""
        self.xknx = xknx
        self.timeout_in_seconds = timeout_in_seconds
        self.stop_on_found = stop_on_found
        self.scan_filter = scan_filter
        self.found_gateways: list[GatewayDescriptor] = []
        self._udp_clients: list[UDPClient] = []
        self._response_received_event = asyncio.Event()
        self._count_upper_bound = 0
        """Clean value of self.stop_on_found, computed when ``scan`` is called."""

    async def scan(self) -> list[GatewayDescriptor]:
        """Scan and return a list of GatewayDescriptors on success."""
        if self.stop_on_found is None:
            self._count_upper_bound = 0
        else:
            self._count_upper_bound = max(0, self.stop_on_found)
        await self._send_search_requests()
        try:
            await asyncio.wait_for(
                self._response_received_event.wait(),
                timeout=self.timeout_in_seconds,
            )
        except asyncio.TimeoutError:
            pass
        finally:
            await self._stop()

        return self.found_gateways

    async def _stop(self) -> None:
        """Stop tearing down udpclient."""
        for udp_client in self._udp_clients:
            await udp_client.stop()

    async def _send_search_requests(self) -> None:
        """Find all interfaces with active IPv4 connection to search for gateways."""
        for interface in netifaces.interfaces():
            try:
                af_inet = netifaces.ifaddresses(interface)[netifaces.AF_INET]
                ip_addr = af_inet[0]["addr"]
            except KeyError:
                logger.debug("No IPv4 address found on %s", interface)
                continue
            except ValueError as err:
                # rare case when an interface disappears during search initialisation
                logger.debug("Invalid interface %s: %s", interface, err)
                continue
            else:
                await self._search_interface(interface, ip_addr)

    async def _search_interface(self, interface: str, ip_addr: str) -> None:
        """Send a search request on a specific interface."""
        logger.debug("Searching on %s / %s", interface, ip_addr)

        udp_client = UDPClient(
            self.xknx,
            (ip_addr, 0),
            (self.xknx.multicast_group, self.xknx.multicast_port),
            multicast=True,
        )

        udp_client.register_callback(
            partial(self._response_rec_callback, interface=interface),
            [KNXIPServiceType.SEARCH_RESPONSE],
        )
        await udp_client.connect()

        self._udp_clients.append(udp_client)

        (_, local_port) = udp_client.getsockname()
        discovery_endpoint = HPAI(ip_addr=ip_addr, port=local_port)

        search_request = SearchRequest(self.xknx, discovery_endpoint=discovery_endpoint)
        udp_client.send(KNXIPFrame.init_from_body(search_request))

    def _response_rec_callback(
        self,
        knx_ip_frame: KNXIPFrame,
        source: HPAI,
        udp_client: UDPClient,
        interface: str = "",
    ) -> None:
        """Verify and handle knxipframe. Callback from internal udpclient."""
        if not isinstance(knx_ip_frame.body, SearchResponse):
            logger.warning("Could not understand knxipframe")
            return

        gateway = GatewayDescriptor(
            name=knx_ip_frame.body.device_name,
            ip_addr=knx_ip_frame.body.control_endpoint.ip_addr,
            port=knx_ip_frame.body.control_endpoint.port,
            local_interface=interface,
            local_ip=udp_client.local_addr[0],
        )
        try:
            dib = next(
                dib
                for dib in knx_ip_frame.body.dibs
                if isinstance(dib, DIBSuppSVCFamilies)
            )
            gateway.supports_routing = dib.supports(DIBServiceFamily.ROUTING)
            gateway.supports_tunnelling = dib.supports(DIBServiceFamily.TUNNELING)
        except StopIteration:
            pass

        try:
            device_infos = next(
                device_infos
                for device_infos in knx_ip_frame.body.dibs
                if isinstance(device_infos, DIBDeviceInformation)
            )
            gateway.individual_address = device_infos.individual_address
        except StopIteration:
            pass

        logger.debug("Found KNX/IP device at %s: %s", source, repr(gateway))
        self._add_found_gateway(gateway)

    def _add_found_gateway(self, gateway: GatewayDescriptor) -> None:
        if self.scan_filter.match(gateway) and not any(
            _gateway.individual_address == gateway.individual_address
            for _gateway in self.found_gateways
        ):
            self.found_gateways.append(gateway)
            if 0 < self._count_upper_bound <= len(self.found_gateways):
                self._response_received_event.set()
