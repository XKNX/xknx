"""
Abstract base for a specific KNX/IP connection (Tunneling or Routing).

* It handles connection and disconnections
* It starts and stops a udp transport
* It packs Telegrams into KNX Frames and passes them to a udp transport
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

from xknx.cemi import CEMIFrame
from xknx.core import XknxConnectionState, XknxConnectionType
from xknx.telegram import IndividualAddress

from .transport.ip_transport import KNXIPTransport

if TYPE_CHECKING:
    from xknx.xknx import XKNX

CEMIBytesCallbackType = Callable[[bytes], None]


class Interface(ABC):
    """Abstract base class for KNX/IP connections."""

    __slots__ = ("cemi_received_callback", "transport", "xknx")

    connection_type: ClassVar[XknxConnectionType]
    cemi_received_callback: CEMIBytesCallbackType
    transport: KNXIPTransport
    xknx: XKNX

    @abstractmethod
    async def connect(self) -> None:
        """Connect to KNX bus. Raise CommunicationError when not successful."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from KNX bus."""

    @abstractmethod
    async def send_cemi(self, cemi: CEMIFrame) -> None:
        """Send CEMIFrame to KNX bus."""

    def connection_state_changed(self, state: XknxConnectionState) -> None:
        """Update connection state via connection manager."""
        self.xknx.connection_manager.connection_state_changed(
            state, self.connection_type
        )

    def _set_individual_address(self, address: IndividualAddress) -> None:
        """Set current individual address."""
        self.xknx.current_address = address
