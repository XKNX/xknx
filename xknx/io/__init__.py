"""
This package contains all objects managing Tunneling and Routing Connections..

- KNXIPInterface is the overall managing class.
- GatewayScanner searches for available KNX/IP devices in the local network.
- Routing uses UDP/Multicast to communicate with KNX/IP device.
- Tunnel uses UDP packets and builds a static tunnel with KNX/IP device.
"""
# flake8: noqa
from .connection import ConnectionConfig, ConnectionType, SecureConfig
from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT
from .gateway_scanner import GatewayDescriptor, GatewayScanFilter, GatewayScanner
from .knxip_interface import KNXIPInterface, knx_interface_factory
from .routing import Routing
from .self_description import DescriptionQuery
from .tunnel import TCPTunnel, UDPTunnel

__all__ = [
    "DEFAULT_MCAST_GRP",
    "DEFAULT_MCAST_PORT",
    "DescriptionQuery",
    "GatewayScanFilter",
    "GatewayScanner",
    "ConnectionConfig",
    "SecureConfig",
    "ConnectionType",
    "KNXIPInterface",
    "Routing",
    "TCPTunnel",
    "UDPTunnel",
]
