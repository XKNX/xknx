"""
Abstract base for a specific KNX/IP connection (Tunneling or Routing).

* It handles connection and disconnections
* It starts and stops a udp transport
* It packs Telegrams into KNX Frames and passes them to a udp transport
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from xknx.cemi import CEMIFrame

CEMICallbackType = Callable[[CEMIFrame], None]


class Interface(ABC):
    """Abstract base class for KNX/IP connections."""

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to KNX bus. Returns True on success."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from KNX bus."""

    @abstractmethod
    async def send_cemi(self, cemi: CEMIFrame) -> None:
        """Send CEMIFrame to KNX bus."""
