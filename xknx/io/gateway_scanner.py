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

    # pylint: disable=too-many-instance-attributes
    def __init__(self, xknx, timeout_in_seconds=4):
        """Initialize GatewayScanner class."""
        self.xknx = xknx
        self.response_received_or_timeout = asyncio.Event()
        self.found = False
        self.found_ip_addr = None
        self.found_port = None
        self.found_name = None
        self.found_local_ip = None
        self.supports_routing = False
        self.supports_tunneling = False
        self.udpclients = []
        self.timeout_in_seconds = timeout_in_seconds
        self.timeout_callback = None
        self.timeout_handle = None

    def response_rec_callback(self, knxipframe, udp_client):
        """Verify and handle knxipframe. Callback from internal udpclient."""
        if not isinstance(knxipframe.body, SearchResponse):
            self.xknx.logger.warning("Cant understand knxipframe")
            return

        if not self.found:
            self.found_ip_addr = knxipframe.body.control_endpoint.ip_addr
            self.found_port = knxipframe.body.control_endpoint.port
            self.found_name = knxipframe.body.device_name

            for dib in knxipframe.body.dibs:
                if isinstance(dib, DIBSuppSVCFamilies):
                    self.supports_routing = dib.supports(DIBServiceFamily.ROUTING)
                    self.supports_tunneling = dib.supports(DIBServiceFamily.TUNNELING)

            (self.found_local_ip, _) = udp_client.getsockname()

            self.response_received_or_timeout.set()
            self.found = True

    async def start(self):
        """Start searching."""
        await self.send_search_requests()
        await self.start_timeout()
        await self.response_received_or_timeout.wait()
        await self.stop()
        await self.stop_timeout()

    async def stop(self):
        """Stop tearing down udpclient."""
        for udpclient in self.udpclients:
            await udpclient.stop()

    async def send_search_requests(self):
        """Send search requests on all connected interfaces."""
        # pylint: disable=no-member
        for interface in netifaces.interfaces():
            try:
                af_inet = netifaces.ifaddresses(interface)[netifaces.AF_INET]
                ip_addr = af_inet[0]["addr"]
                await self.search_interface(interface, ip_addr)
            except KeyError:
                self.xknx.logger.info("Could not connect to an KNX/IP device on %s", interface)
                continue

    async def search_interface(self, interface, ip_addr):
        """Search on a specific interface."""
        self.xknx.logger.debug("Searching on %s / %s", interface, ip_addr)

        udpclient = UDPClient(self.xknx,
                              (ip_addr, 0),
                              (DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
                              multicast=True)

        udpclient.register_callback(
            self.response_rec_callback, [KNXIPServiceType.SEARCH_RESPONSE])
        await udpclient.connect()

        self.udpclients.append(udpclient)

        (local_addr, local_port) = udpclient.getsockname()
        knxipframe = KNXIPFrame(self.xknx)
        knxipframe.init(KNXIPServiceType.SEARCH_REQUEST)
        knxipframe.body.discovery_endpoint = \
            HPAI(ip_addr=local_addr, port=local_port)
        knxipframe.normalize()
        udpclient.send(knxipframe)

    def timeout(self):
        """Handle timeout for not having received a SearchResponse."""
        self.response_received_or_timeout.set()

    async def start_timeout(self):
        """Start time out."""
        self.timeout_handle = self.xknx.loop.call_later(
            self.timeout_in_seconds, self.timeout)

    async def stop_timeout(self):
        """Stop/cancel timeout."""
        self.timeout_handle.cancel()
