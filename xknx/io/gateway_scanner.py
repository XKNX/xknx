"""
GatewayScanner is an abstraction for searching for KNX/IP devices on the local network.

It walks through all network interfaces and sends UDP multicast
SearchRequest and SearchRequestExtended frames.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from functools import partial
import logging
from typing import TYPE_CHECKING

from xknx.exceptions import XKNXException
from xknx.io import util
from xknx.knxip import (
    HPAI,
    SRP,
    DIBServiceFamily,
    DIBTypeCode,
    KNXIPFrame,
    KNXIPServiceType,
    SearchRequest,
    SearchRequestExtended,
    SearchResponse,
    SearchResponseExtended,
)
from xknx.knxip.dib import (
    DIB,
    DIBDeviceInformation,
    DIBSecuredServiceFamilies,
    DIBSuppSVCFamilies,
    DIBTunnelingInfo,
    TunnelingSlotStatus,
)
from xknx.telegram import IndividualAddress

from .transport import UDPTransport

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class GatewayDescriptor:
    """Used to return information about the discovered gateways."""

    def __init__(
        self,
        ip_addr: str,
        port: int,
        local_ip: str = "",
        local_interface: str = "",
        name: str = "UNKNOWN",
        supports_routing: bool = False,
        supports_tunnelling: bool = False,
        supports_tunnelling_tcp: bool = False,
        supports_secure: bool = False,
        individual_address: IndividualAddress | None = None,
    ):
        """Initialize GatewayDescriptor class."""
        self.name = name
        self.ip_addr = ip_addr
        self.port = port
        self.individual_address = individual_address
        self.local_interface = local_interface
        self.local_ip = local_ip
        self.supports_routing = supports_routing
        self.supports_tunnelling = supports_tunnelling
        self.supports_tunnelling_tcp = supports_tunnelling_tcp
        self.supports_secure = supports_secure

        self.core_version: int = 0
        self.routing_requires_secure: bool | None = None
        self.tunnelling_requires_secure: bool | None = None
        self.tunnelling_slots: dict[IndividualAddress, TunnelingSlotStatus] = {}

    def parse_dibs(self, dibs: list[DIB]) -> None:
        """Parse DIBs for gateway information."""
        for dib in dibs:
            if isinstance(dib, DIBDeviceInformation):
                self.name = dib.name
                self.individual_address = dib.individual_address
                continue
            if isinstance(dib, DIBSuppSVCFamilies):
                self.core_version = dib.version(DIBServiceFamily.CORE) or 0
                self.supports_routing = dib.supports(DIBServiceFamily.ROUTING)
                if _tunnelling_version := dib.version(DIBServiceFamily.TUNNELING):
                    self.supports_tunnelling = True
                    self.supports_tunnelling_tcp = _tunnelling_version >= 2
                self.supports_secure = dib.supports(
                    DIBServiceFamily.SECURITY, version=1
                )
                continue
            if isinstance(dib, DIBSecuredServiceFamilies):
                self.tunnelling_requires_secure = dib.supports(
                    DIBServiceFamily.TUNNELING
                )
                self.routing_requires_secure = dib.supports(DIBServiceFamily.ROUTING)
                continue
            if isinstance(dib, DIBTunnelingInfo):
                self.tunnelling_slots = dib.slots
                continue

    def __repr__(self) -> str:
        """Return object as representation string."""
        return (
            "GatewayDescriptor(\n"
            f"    name={self.name},\n"
            f"    ip_addr={self.ip_addr},\n"
            f"    port={self.port},\n"
            f"    individual_address={self.individual_address}\n"
            f"    local_interface={self.local_interface},\n"
            f"    local_ip={self.local_ip},\n"
            f"    core_version={self.core_version},\n"
            f"    supports_routing={self.supports_routing},\n"
            f"    supports_tunnelling={self.supports_tunnelling},\n"
            f"    supports_tunnelling_tcp={self.supports_tunnelling_tcp},\n"
            f"    supports_secure={self.supports_secure},\n"
            f"    routing_requires_secure={self.routing_requires_secure}\n"
            f"    tunnelling_requires_secure={self.tunnelling_requires_secure}\n"
            f"    tunnelling_slots={self.tunnelling_slots}\n"
            ")"
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return f"{self.individual_address} - {self.name} @ {self.ip_addr}:{self.port}"


class GatewayScanFilter:
    """Filter to limit gateway scan results.

    If `name` doesn't match the gateway name, the gateway will be ignored.

    Connection methods are treated as OR if `True` is set for multiple methods.
    Non-secure methods don't match if secure is required.
    """

    def __init__(
        self,
        name: str | None = None,
        tunnelling: bool | None = True,
        tunnelling_tcp: bool | None = True,
        routing: bool | None = True,
        secure_tunnelling: bool | None = True,
        secure_routing: bool | None = True,
    ):
        """Initialize GatewayScanFilter class."""
        self.name = name
        self.tunnelling = tunnelling
        self.tunnelling_tcp = tunnelling_tcp
        self.routing = routing
        self.secure_tunnelling = secure_tunnelling
        self.secure_routing = secure_routing

    def match(self, gateway: GatewayDescriptor) -> bool:
        """Check whether the device is a gateway and given GatewayDescriptor matches the filter."""
        if self.name is not None and self.name != gateway.name:
            return False
        if (
            self.tunnelling
            and gateway.supports_tunnelling
            and not gateway.tunnelling_requires_secure
        ):
            return True
        if (
            self.tunnelling_tcp
            and gateway.supports_tunnelling_tcp
            and not gateway.tunnelling_requires_secure
        ):
            return True
        if (
            self.routing
            and gateway.supports_routing
            and not gateway.routing_requires_secure
        ):
            return True
        if (
            self.secure_tunnelling
            and gateway.supports_tunnelling_tcp
            and gateway.tunnelling_requires_secure
        ):
            return True
        if (
            self.secure_routing
            and gateway.supports_routing
            and gateway.routing_requires_secure
        ):
            return True
        return False

    def __eq__(self, other: object) -> bool:
        """Equality for GatewayScanFilter class."""
        return self.__dict__ == other.__dict__


class GatewayScanner:
    """Class for searching KNX/IP devices."""

    def __init__(
        self,
        xknx: XKNX,
        local_ip: str | None = None,
        timeout_in_seconds: float = 3.0,
        stop_on_found: int | None = None,
        scan_filter: GatewayScanFilter | None = None,
    ):
        """Initialize GatewayScanner class."""
        self.xknx = xknx
        self.local_ip = local_ip
        self.timeout_in_seconds = timeout_in_seconds
        self.stop_on_found = stop_on_found
        self.scan_filter = scan_filter or GatewayScanFilter()
        self.found_gateways: dict[HPAI, GatewayDescriptor] = {}
        self._response_received_event = asyncio.Event()

    async def scan(self) -> list[GatewayDescriptor]:
        """Scan and return a list of GatewayDescriptors on success."""
        await self._scan()
        return list(self.found_gateways.values())

    async def async_scan(self) -> AsyncGenerator[GatewayDescriptor, None]:
        """Search and yield found gateways."""
        queue: asyncio.Queue[GatewayDescriptor | None] = asyncio.Queue()
        scan_task = asyncio.create_task(self._scan(queue=queue))
        try:
            while True:
                gateway = await queue.get()
                if gateway is None:
                    return
                yield gateway
        finally:
            # cleanup after GeneratorExit or XKNXExceptions
            if not scan_task.done():
                scan_task.cancel()
            await scan_task  # to bubble up exceptions

    async def _scan(
        self, queue: asyncio.Queue[GatewayDescriptor | None] | None = None
    ) -> None:
        """Scan for gateways."""
        local_ip = self.local_ip or await util.get_default_local_ip(
            remote_ip=self.xknx.multicast_group
        )
        if local_ip is None:
            if queue is not None:
                queue.put_nowait(None)
            raise XKNXException("No usable network interface found.")
        interface_name = util.get_local_interface_name(local_ip=local_ip)
        logger.debug("Searching on %s / %s", interface_name, local_ip)

        udp_transport = UDPTransport(
            local_addr=(local_ip, 0),
            remote_addr=(self.xknx.multicast_group, self.xknx.multicast_port),
        )
        udp_transport.register_callback(
            partial(self._response_rec_callback, interface=interface_name, queue=queue),
            [
                KNXIPServiceType.SEARCH_RESPONSE,
                KNXIPServiceType.SEARCH_RESPONSE_EXTENDED,
            ],
        )
        try:
            await self._send_search_requests(udp_transport=udp_transport)
            await asyncio.wait_for(
                self._response_received_event.wait(),
                timeout=self.timeout_in_seconds,
            )
        except asyncio.TimeoutError:
            pass
        except asyncio.CancelledError:
            pass
        finally:
            udp_transport.stop()
            if queue is not None:
                queue.put_nowait(None)

    @staticmethod
    async def _send_search_requests(udp_transport: UDPTransport) -> None:
        """Send search requests on a specific interface."""
        await udp_transport.connect()
        discovery_endpoint = HPAI(*udp_transport.getsockname())
        # send SearchRequestExtended requesting needed DIBs
        search_request_extended = SearchRequestExtended(
            discovery_endpoint=discovery_endpoint,
            srps=[
                SRP.request_device_description(
                    [
                        DIBTypeCode.DEVICE_INFO,
                        DIBTypeCode.SUPP_SVC_FAMILIES,
                        DIBTypeCode.SECURED_SERVICE_FAMILIES,
                        DIBTypeCode.TUNNELING_INFO,
                    ]
                )
            ],
        )
        udp_transport.send(KNXIPFrame.init_from_body(search_request_extended))
        # send SearchRequest for Core-V1 devices
        search_request = SearchRequest(discovery_endpoint=discovery_endpoint)
        udp_transport.send(KNXIPFrame.init_from_body(search_request))

    def _response_rec_callback(
        self,
        knx_ip_frame: KNXIPFrame,
        source: HPAI,
        udp_transport: UDPTransport,
        interface: str = "",
        queue: asyncio.Queue[GatewayDescriptor | None] | None = None,
    ) -> None:
        """Verify and handle knxipframe. Callback from internal udp_transport."""
        if not isinstance(knx_ip_frame.body, (SearchResponse, SearchResponseExtended)):
            logger.warning("Could not understand knxipframe")
            return

        # skip non-extended SearchResponse for Core-V2 devices
        if knx_ip_frame.header.service_type_ident == KNXIPServiceType.SEARCH_RESPONSE:
            if svc_families_dib := next(
                (
                    dib
                    for dib in knx_ip_frame.body.dibs
                    if isinstance(dib, DIBSuppSVCFamilies)
                ),
                None,
            ):
                if svc_families_dib.supports(DIBServiceFamily.CORE, version=2):
                    logger.debug("Skipping SearchResponse for Core-V2 device")
                    return

        gateway = GatewayDescriptor(
            ip_addr=knx_ip_frame.body.control_endpoint.ip_addr,
            port=knx_ip_frame.body.control_endpoint.port,
            local_ip=udp_transport.local_addr[0],
            local_interface=interface,
        )
        gateway.parse_dibs(knx_ip_frame.body.dibs)

        logger.debug("Found KNX/IP device at %s: %s", source, repr(gateway))
        if self.scan_filter.match(gateway):
            self.found_gateways[knx_ip_frame.body.control_endpoint] = gateway
            if queue is not None:
                queue.put_nowait(gateway)
            if self.stop_on_found and len(self.found_gateways) >= self.stop_on_found:
                self._response_received_event.set()
