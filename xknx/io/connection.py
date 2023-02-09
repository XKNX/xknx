"""Manages a connection to the KNX bus."""
from __future__ import annotations

from enum import Enum, auto
import os
from typing import Any

from xknx.telegram.address import IndividualAddress, IndividualAddressableType

from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT
from .gateway_scanner import GatewayScanFilter


class ConnectionType(Enum):
    """Enum class for different types of KNX/IP Connections."""

    AUTOMATIC = auto()
    ROUTING = auto()
    ROUTING_SECURE = auto()
    TUNNELING = auto()
    TUNNELING_TCP = auto()
    TUNNELING_TCP_SECURE = auto()


class ConnectionConfig:
    """
    Connection configuration.

    Handles:
    * type of connection:
        * AUTOMATIC for using GatewayScanner for searching and finding KNX/IP devices in the network.
        * ROUTING use KNX/IP multicast routing.
        * TUNNELING connect to a specific KNX/IP tunneling device via UDP.
        * TUNNELING_TCP connect to a specific KNX/IP tunneling v2 device via TCP.
    * individual address:
        * ROUTING the individual address used as source address for routing
        * TCP TUNNELING request a specific tunnel endpoint
        * SECURE TUNNELING use a specific tunnel endpoint from the knxkeys file
    * local_ip: Local ip of the interface though which KNXIPInterface should connect.
    * gateway_ip: IP of KNX/IP tunneling device.
    * gateway_port: Port of KNX/IP tunneling device.
    * route_back: For UDP TUNNELING connection.
        The KNXnet/IP Server shall use the IP address and port in the received IP package
        as the target IP address or port number for the response to the KNXnet/IP Client.
    * multicast_group: Multicast group for KNXnet/IP routing.
    * multicast_port: Multicast port for KNXnet/IP routing.
    * auto_reconnect: Auto reconnect to KNX/IP tunneling device if connection cannot be established.
    * auto_reconnect_wait: Wait n seconds before trying to reconnect to KNX/IP tunneling device.
    * scan_filter: For AUTOMATIC connection, limit scan with the given filter
    * threaded: Run connection logic in separate thread to avoid concurrency issues in HA
    * secure_config: KNX Secure config to use
    """

    def __init__(
        self,
        *,
        connection_type: ConnectionType = ConnectionType.AUTOMATIC,
        individual_address: IndividualAddressableType | None = None,
        local_ip: str | None = None,
        local_port: int = 0,
        gateway_ip: str | None = None,
        gateway_port: int = DEFAULT_MCAST_PORT,
        route_back: bool = False,
        multicast_group: str = DEFAULT_MCAST_GRP,
        multicast_port: int = DEFAULT_MCAST_PORT,
        auto_reconnect: bool = True,
        auto_reconnect_wait: int = 3,
        scan_filter: GatewayScanFilter | None = None,
        threaded: bool = False,
        secure_config: SecureConfig | None = None,
    ):
        """Initialize ConnectionConfig class."""
        self.connection_type = connection_type
        self.individual_address = (
            IndividualAddress(individual_address) if individual_address else None
        )
        self.local_ip = local_ip
        self.local_port = local_port
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.route_back = route_back
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port
        self.auto_reconnect = auto_reconnect
        self.auto_reconnect_wait = auto_reconnect_wait
        self.scan_filter = scan_filter or GatewayScanFilter()
        self.threaded = threaded
        self.secure_config = secure_config

    def __eq__(self, other: object) -> bool:
        """Equality for ConnectionConfig class (used in unit tests)."""
        return self.__dict__ == other.__dict__


class SecureConfig:
    """
    Secure configuration.

    Handles:
    * backbone_key: Key used for KNX Secure Routing in hex representation.
    * latency_ms: Latency in milliseconds for KNX Secure Routing.
    * user_id: The user id to use when initializing the secure tunnel.
    * device_authentication_password: the authentication password to use when connecting to the tunnel.
    * user_password: the user password for knx secure.
    * knxkeys_file_path: Full path to the knxkeys file including the file name.
    * knxkeys_password: Password to decrypt the knxkeys file.
    """

    def __init__(
        self,
        *,
        backbone_key: str | None = None,
        latency_ms: int | None = None,
        user_id: int | None = None,
        device_authentication_password: str | None = None,
        user_password: str | None = None,
        knxkeys_file_path: str | os.PathLike[Any] | None = None,
        knxkeys_password: str | None = None,
    ):
        """Initialize SecureConfig class."""
        self.backbone_key = bytes.fromhex(backbone_key) if backbone_key else None
        self.latency_ms = latency_ms
        self.user_id = user_id
        self.device_authentication_password = device_authentication_password
        self.user_password = user_password
        self.knxkeys_file_path = knxkeys_file_path
        self.knxkeys_password = knxkeys_password

    def __eq__(self, other: object) -> bool:
        """Equality for SecureConfig class (used in unit tests)."""
        return self.__dict__ == other.__dict__
