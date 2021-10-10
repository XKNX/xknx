"""Connection States from XKNX."""
from enum import Enum


class XknxConnectionState(Enum):
    """Possible connection state values."""

    CONNECTED = "CONNECTED"
    CONNECTING = "CONNECTING"
    DISCONNECTED = "DISCONNECTED"
