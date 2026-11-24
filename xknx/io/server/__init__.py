"""
KNXnet/IP tunnelling server - KNX v01.07.01 - Tunnelling 03.08.04 - §2.

`KNXIPTunnellingServer` lets KNXnet/IP tunnelling clients use the bus connection
of an XKNX instance, e.g. a KNX USB interface as a KNXnet/IP interface.
"""

from .connection import TunnelInfo
from .tunnelling_server import KNXIPTunnellingServer

__all__ = [
    "KNXIPTunnellingServer",
    "TunnelInfo",
]
