"""
Abstract base for a specific IP transports (TCP or UDP).

* It starts and stops a socket
* It handles callbacks for incoming frame service types
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from xknx.knxip import HPAI, KNXIPFrame, KNXIPServiceType

TransportCallbackType = Callable[[KNXIPFrame, HPAI, "KNXIPTransport"], None]


class KNXIPTransport(ABC):
    """Abstract base class for KNX/IP transports."""

    callbacks: list[KNXIPTransport.Callback]
    local_hpai: HPAI

    class Callback:
        """Callback class for handling callbacks for different 'KNX service types' of received packets."""

        def __init__(
            self,
            callback: TransportCallbackType,
            service_types: list[KNXIPServiceType] | None = None,
        ):
            """Initialize Callback class."""
            self.callback = callback
            self.service_types = service_types or []

        def has_service(self, service_type: KNXIPServiceType) -> bool:
            """Test if callback is listening for given service type."""
            return len(self.service_types) == 0 or service_type in self.service_types

    def register_callback(
        self,
        callback: TransportCallbackType,
        service_types: list[KNXIPServiceType] | None = None,
    ) -> KNXIPTransport.Callback:
        """Register callback."""
        if service_types is None:
            service_types = []

        callb = KNXIPTransport.Callback(callback, service_types)
        self.callbacks.append(callb)
        return callb

    def unregister_callback(self, callb: KNXIPTransport.Callback) -> None:
        """Unregister callback."""
        self.callbacks.remove(callb)

    @abstractmethod
    async def connect(self) -> None:
        """Connect transport."""

    @abstractmethod
    def send(self, knxipframe: KNXIPFrame, addr: tuple[str, int] | None = None) -> None:
        """Send KNXIPFrame via transport."""

    @abstractmethod
    def stop(self) -> None:
        """Stop transport."""

    @abstractmethod
    def getsockname(self) -> tuple[str, int]:
        """Return socket IP and port."""
