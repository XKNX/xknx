"""
Abstract base for a specific IP transports (TCP or UDP).

* It starts and stops a socket
* It handles callbacks for incoming frame service types
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Callable, cast

from xknx.exceptions import CommunicationError
from xknx.knxip import HPAI, KNXIPFrame, KNXIPServiceType

TransportCallbackType = Callable[[KNXIPFrame, HPAI, "KNXIPTransport"], None]

knx_logger = logging.getLogger("xknx.knx")


class KNXIPTransport(ABC):
    """Abstract base class for KNX/IP transports."""

    callbacks: list[KNXIPTransport.Callback]
    local_hpai: HPAI
    remote_addr: tuple[str, int]
    transport: asyncio.BaseTransport | None

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
            return not self.service_types or service_type in self.service_types

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

    def handle_knxipframe(self, knxipframe: KNXIPFrame, source: HPAI) -> None:
        """Handle KNXIP Frame and call all callbacks matching the service type ident."""
        handled = False
        for callback in self.callbacks:
            if callback.has_service(knxipframe.header.service_type_ident):
                callback.callback(knxipframe, source, self)
                handled = True
        if not handled:
            knx_logger.debug(
                "Unhandled: %s from: %s",
                knxipframe.header.service_type_ident,
                source,
            )

    @abstractmethod
    async def connect(self) -> None:
        """Connect transport."""

    @abstractmethod
    def send(self, knxipframe: KNXIPFrame, addr: tuple[str, int] | None = None) -> None:
        """Send KNXIPFrame via transport."""

    def getsockname(self) -> tuple[str, int]:
        """Return socket IP and port."""
        if self.transport is None:
            raise CommunicationError(
                "No transport defined. Socket information not resolveable"
            )
        return cast(tuple[str, int], self.transport.get_extra_info("sockname"))

    def getremote(self) -> str | None:
        """Return peername."""
        return (
            self.transport.get_extra_info("peername")
            if self.transport is not None
            else None
        )

    def stop(self) -> None:
        """Stop socket."""
        if self.transport is not None:
            self.transport.close()
            self.transport = None
