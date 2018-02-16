"""
GatewayScanner is an abstraction for searching for KNX/IP devices on the local network.

* It walks through all network interfaces
* and sends UDP multicast search requests
* it returns the first found device
"""

import asyncio

import netifaces
from xknx.knxip import (HPAI, DIBServiceFamily, DIBSuppSVCFamilies, KNXIPFrame,
                        KNXIPServiceType, SearchResponse)

from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT
from .udp_client import UDPClient


class GatewayScanner():
    """Class for searching KNX/IP devices."""

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes
    def __init__(self, xknx, timeout_in_seconds=4):
        """Initialize GatewayScanner class."""
        self.xknx = xknx
        self.timeout_in_seconds = timeout_in_seconds
        self.found = False
        self.found_ip_addr = None
        self.found_port = None
        self.found_name = None
        self.found_local_ip = None
        self.supports_routing = False
        self.supports_tunneling = False
        self._udp_clients = []
        self._response_received_or_timeout = asyncio.Event()
        self._timeout_callback = None
        self._timeout_handle = None

    async def start(self):
        """Start searching."""
        await self._send_search_requests()
        await self._start_timeout()
        await self._response_received_or_timeout.wait()
        await self.stop()
        await self._stop_timeout()

    async def stop(self):
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
                               (ip_addr, 0),
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

    def _response_rec_callback(self, knx_ip_frame, udp_client):
        """Verify and handle knxipframe. Callback from internal udpclient."""
        if not isinstance(knx_ip_frame.body, SearchResponse):
            self.xknx.logger.warning("Cant understand knxipframe")
            return

        if not self.found:
            self.found_ip_addr = knx_ip_frame.body.control_endpoint.ip_addr
            self.found_port = knx_ip_frame.body.control_endpoint.port
            self.found_name = knx_ip_frame.body.device_name

            for dib in knx_ip_frame.body.dibs:
                if isinstance(dib, DIBSuppSVCFamilies):
                    self.supports_routing = dib.supports(DIBServiceFamily.ROUTING)
                    self.supports_tunneling = dib.supports(DIBServiceFamily.TUNNELING)

            (self.found_local_ip, _) = udp_client.getsockname()

            self._response_received_or_timeout.set()
            self.found = True

    def _timeout(self):
        """Handle timeout for not having received a SearchResponse."""
        self._response_received_or_timeout.set()

    async def _start_timeout(self):
        """Start time out."""
        self._timeout_handle = self.xknx.loop.call_later(
            self.timeout_in_seconds, self._timeout)

    async def _stop_timeout(self):
        """Stop/cancel timeout."""
        self._timeout_handle.cancel()
