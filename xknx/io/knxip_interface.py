"""
KNXIPInterface manages KNX/IP Tunneling or Routing connections.

* It searches for available devices and connects with the corresponding connect method.
* It passes KNX telegrams from the network and
* provides callbacks after having received a telegram from the network.

"""
from enum import Enum

from xknx.exceptions import XKNXException

from .const import DEFAULT_MCAST_PORT
from .gateway_scanner import GatewayScanner
from .routing import Routing
from .tunnel import Tunnel


class ConnectionType(Enum):
    """Enum class for different types of KNX/IP Connections."""

    AUTOMATIC = 0
    TUNNELING = 1
    ROUTING = 2


class ConnectionConfig:
    """
    Connection configuration.

    Handles:
    * type of connection:
        * AUTOMATIC for using GatewayScanner for searching and finding KNX/IP devices in the network.
        * TUNNELING connect to a specific KNX/IP tunneling device.
        * ROUTING use KNX/IP multicast routing.
    * local_ip: Local ip of the interface though which KNXIPInterface should connect.
    * gateway_ip: IP of KNX/IP tunneling device.
    * gateway_port: Port of KNX/IP tunneling device.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self,
                 connection_type=ConnectionType.AUTOMATIC,
                 local_ip=None,
                 gateway_ip=None,
                 gateway_port=DEFAULT_MCAST_PORT):
        """Initialize ConnectionConfig class."""
        self.connection_type = connection_type
        self.local_ip = local_ip
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port


class KNXIPInterface():
    """Class for managing KNX/IP Tunneling or Routing connections."""

    def __init__(self, xknx, connection_config=ConnectionConfig()):
        """Initialize KNXIPInterface class."""
        self.xknx = xknx
        self.interface = None
        self.connection_config = connection_config

    async def start(self):
        """Start interface. Connecting KNX/IP device with the selected method."""
        if self.connection_config.connection_type == ConnectionType.AUTOMATIC:
            await self.start_automatic()
        elif self.connection_config.connection_type == ConnectionType.ROUTING:
            await self.start_routing(
                self.connection_config.local_ip)
        elif self.connection_config.connection_type == ConnectionType.TUNNELING:
            await self.start_tunnelling(
                self.connection_config.local_ip,
                self.connection_config.gateway_ip,
                self.connection_config.gateway_port)

    async def start_automatic(self):
        """Start GatewayScanner and connect to the found device."""
        gatewayscanner = GatewayScanner(self.xknx)
        await gatewayscanner.start()
        await gatewayscanner.stop()

        if not gatewayscanner.found:
            raise XKNXException("No Gateways found")

        if gatewayscanner.supports_tunneling:
            await self.start_tunnelling(gatewayscanner.found_local_ip,
                                        gatewayscanner.found_ip_addr,
                                        gatewayscanner.found_port)
        elif gatewayscanner.supports_routing:
            await self.start_routing(gatewayscanner.found_local_ip)

    async def start_tunnelling(self, local_ip, gateway_ip, gateway_port):
        """Start KNX/IP tunnel."""
        self.xknx.logger.debug("Starting tunnel to %s:%s from %s", gateway_ip, gateway_port, local_ip)
        self.interface = Tunnel(
            self.xknx,
            self.xknx.own_address,
            local_ip=local_ip,
            gateway_ip=gateway_ip,
            gateway_port=gateway_port,
            telegram_received_callback=self.telegram_received)
        await self.interface.start()

    async def start_routing(self, local_ip):
        """Start KNX/IP Routing."""
        self.xknx.logger.debug("Starting Routing from %s", local_ip)
        self.interface = Routing(
            self.xknx,
            self.telegram_received,
            local_ip)
        await self.interface.start()

    async def stop(self):
        """Stop connected interfae (either Tunneling or Routing)."""
        if self.interface is not None:
            await self.interface.stop()
            self.interface = None

    def telegram_received(self, telegram):
        """Put received telegram into queue. Callback for having received telegram."""
        self.xknx.loop.create_task(
            self.xknx.telegrams.put(telegram))

    async def send_telegram(self, telegram):
        """Send telegram to connected device (either Tunneling or Routing)."""
        await self.interface.send_telegram(telegram)
