"""Connection States from XKNX."""
from enum import Enum


class XknxConnectionState(Enum):
    """Possible connection state values."""

    CONNECTED = "CONNECTED"
    CONNECTING = "CONNECTING"
    DISCONNECTED = "DISCONNECTED"


class XknxConnectionType(Enum):
    """Possible connection type values."""

    NOT_CONNECTED = None
    ROUTING = "Routing"
    ROUTING_SECURE = "Routing IP Secure"
    TUNNEL_SECURE = "Tunnel IP Secure"
    TUNNEL_TCP = "Tunnel TCP"
    TUNNEL_UDP = "Tunnel UDP"
