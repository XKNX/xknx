"""
KNXIPInterface manages KNX/IP Tunneling or Routing connections.

* It searches for available devices and connects with the corresponding connect method.
* It passes KNX telegrams from the network and
* provides callbacks after having received a telegram from the network.

"""
from enum import Enum
import ipaddress
import logging
from typing import TYPE_CHECKING, Optional, cast

import netifaces
from xknx.exceptions import CommunicationError, XKNXException

from .const import DEFAULT_MCAST_PORT
from .gateway_scanner import GatewayScanFilter, GatewayScanner
from .routing import Routing
from .tunnel import Tunnel

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

    from .interface import Interface

logger = logging.getLogger("xknx.log")


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
    * route_back: the KNXnet/IP Server shall use the IP address and the port number in the IP package
        received as the target IP address or port number for the response to the KNXnet/IP Client.
    * auto_reconnect: Auto reconnect to KNX/IP tunneling device if connection cannot be established.
    * auto_reconnect_wait: Wait n seconds before trying to reconnect to KNX/IP tunneling device.
    * scan_filter: For AUTOMATIC connection, limit scan with the given filter
    """

    # pylint: disable=too-few-public-methods,too-many-instance-attributes

    def __init__(
        self,
        connection_type: ConnectionType = ConnectionType.AUTOMATIC,
        local_ip: Optional[str] = None,
        local_port: int = 0,
        gateway_ip: Optional[str] = None,
        gateway_port: int = DEFAULT_MCAST_PORT,
        route_back: bool = False,
        auto_reconnect: bool = True,
        auto_reconnect_wait: int = 3,
        scan_filter: GatewayScanFilter = GatewayScanFilter(),
    ):
        """Initialize ConnectionConfig class."""
        # pylint: disable=too-many-arguments
        self.connection_type = connection_type
        self.local_ip = local_ip
        self.local_port = local_port
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.route_back = route_back
        self.auto_reconnect = auto_reconnect
        self.auto_reconnect_wait = auto_reconnect_wait
        if connection_type == ConnectionType.TUNNELING:
            scan_filter.tunnelling = True
        elif connection_type == ConnectionType.ROUTING:
            scan_filter.routing = True
        self.scan_filter = scan_filter

    def __eq__(self, other: object) -> bool:
        """Equality for ConnectionConfig class (used in unit tests)."""
        return self.__dict__ == other.__dict__


class KNXIPInterface:
    """Class for managing KNX/IP Tunneling or Routing connections."""

    def __init__(
        self,
        xknx: "XKNX",
        connection_config: ConnectionConfig = ConnectionConfig(),
    ):
        """Initialize KNXIPInterface class."""
        self.xknx = xknx
        self.interface: Optional["Interface"] = None
        self.connection_config = connection_config

    async def start(self) -> None:
        """Start interface. Connecting KNX/IP device with the selected method."""
        if (
            self.connection_config.connection_type == ConnectionType.ROUTING
            and self.connection_config.local_ip is not None
        ):
            await self.start_routing(self.connection_config.local_ip)
        elif (
            self.connection_config.connection_type == ConnectionType.TUNNELING
            and self.connection_config.gateway_ip is not None
        ):
            await self.start_tunnelling(
                local_ip=self.connection_config.local_ip,
                local_port=self.connection_config.local_port,
                gateway_ip=self.connection_config.gateway_ip,
                gateway_port=self.connection_config.gateway_port,
                auto_reconnect=self.connection_config.auto_reconnect,
                auto_reconnect_wait=self.connection_config.auto_reconnect_wait,
                route_back=self.connection_config.route_back,
            )
        else:
            await self.start_automatic(self.connection_config.scan_filter)

    async def start_automatic(self, scan_filter: GatewayScanFilter) -> None:
        """Start GatewayScanner and connect to the found device."""
        gatewayscanner = GatewayScanner(self.xknx, scan_filter=scan_filter)
        gateways = await gatewayscanner.scan()

        if not gateways:
            raise XKNXException("No Gateways found")

        gateway = gateways[0]

        # on Linux gateway.local_ip can be any interface listening to the
        # multicast group (even 127.0.0.1) so we set the interface with find_local_ip
        local_interface_ip = self.find_local_ip(gateway_ip=gateway.ip_addr)

        if gateway.supports_tunnelling and scan_filter.routing is not True:
            await self.start_tunnelling(
                local_interface_ip,
                self.connection_config.local_port,
                gateway.ip_addr,
                gateway.port,
                self.connection_config.auto_reconnect,
                self.connection_config.auto_reconnect_wait,
                route_back=self.connection_config.route_back,
            )
        elif gateway.supports_routing:
            await self.start_routing(local_interface_ip)

    async def start_tunnelling(
        self,
        local_ip: Optional[str],
        local_port: int,
        gateway_ip: str,
        gateway_port: int,
        auto_reconnect: bool,
        auto_reconnect_wait: int,
        route_back: bool,
    ) -> None:
        """Start KNX/IP tunnel."""
        # pylint: disable=too-many-arguments
        validate_ip(gateway_ip, address_name="Gateway IP address")
        if local_ip is None:
            local_ip = self.find_local_ip(gateway_ip=gateway_ip)
        validate_ip(local_ip, address_name="Local IP address")
        logger.debug(
            "Starting tunnel from %s:%s to %s:%s",
            local_ip,
            local_port,
            gateway_ip,
            gateway_port,
        )
        self.interface = Tunnel(
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
        await self.interface.connect()

    async def start_routing(self, local_ip: str) -> None:
        """Start KNX/IP Routing."""
        validate_ip(local_ip, address_name="Local IP address")
        logger.debug("Starting Routing from %s as %s", local_ip, self.xknx.own_address)
        self.interface = Routing(self.xknx, self.telegram_received, local_ip)
        await self.interface.connect()

    async def stop(self) -> None:
        """Stop connected interfae (either Tunneling or Routing)."""
        if self.interface is not None:
            await self.interface.disconnect()
            self.interface = None

    def telegram_received(self, telegram: "Telegram") -> None:
        """Put received telegram into queue. Callback for having received telegram."""
        self.xknx.telegrams.put_nowait(telegram)

    async def send_telegram(self, telegram: "Telegram") -> None:
        """Send telegram to connected device (either Tunneling or Routing)."""
        if self.interface is not None:
            await self.interface.send_telegram(telegram)
        else:
            raise CommunicationError("KNX/IP interface not connected")

    @staticmethod
    def find_local_ip(gateway_ip: str) -> str:
        """Find local IP address on same subnet as gateway."""

        def _scan_interfaces(gateway: ipaddress.IPv4Address) -> Optional[str]:
            """Return local IP address on same subnet as given gateway."""
            for interface in netifaces.interfaces():
                try:
                    af_inet = netifaces.ifaddresses(interface)[netifaces.AF_INET]
                    for link in af_inet:
                        network = ipaddress.IPv4Network(
                            (link["addr"], link["netmask"]), strict=False
                        )
                        if gateway in network:
                            logger.debug("Using interface: %s", interface)
                            return cast(str, link["addr"])
                except KeyError:
                    logger.debug(
                        "Could not find IPv4 address on interface %s", interface
                    )
                    continue
            return None

        def _find_default_gateway() -> ipaddress.IPv4Address:
            """Return IP address of default gateway."""
            gws = netifaces.gateways()
            return ipaddress.IPv4Address(gws["default"][netifaces.AF_INET][0])

        gateway = ipaddress.IPv4Address(gateway_ip)
        local_ip = _scan_interfaces(gateway)
        if local_ip is None:
            logger.warning(
                "No interface on same subnet as gateway found. Falling back to default gateway."
            )
            default_gateway = _find_default_gateway()
            local_ip = _scan_interfaces(default_gateway)
        assert isinstance(local_ip, str)
        return local_ip


def validate_ip(address: str, address_name: str = "IP address") -> None:
    """Raise an exception if address cannot be parsed as IPv4 address."""
    try:
        ipaddress.IPv4Address(address)
    except ipaddress.AddressValueError as ex:
        raise XKNXException("%s is not a valid IPv4 address." % address_name) from ex
