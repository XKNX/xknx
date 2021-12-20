"""
Base class for sending a specific type of KNX/IP Packet to a KNX/IP device and wait for the corresponding answer.

Will report if the corresponding answer was not received.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from xknx.io.udp_client import UDPClient
from xknx.knxip import HPAI, ErrorCode, KNXIPBodyResponse, KNXIPFrame

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class RequestResponse:
    """Class for sending a specific type of KNX/IP Packet to a KNX/IP device and wait for the corresponding answer."""

    def __init__(
        self,
        xknx: XKNX,
        udp_client: UDPClient,
        awaited_response_class: type[KNXIPBodyResponse],
        timeout_in_seconds: float = 1.0,
    ):
        """Initialize RequstResponse class."""
        self.xknx = xknx
        self.udpclient = udp_client
        self.awaited_response_class: type[KNXIPBodyResponse] = awaited_response_class
        self.response_received_event = asyncio.Event()
        self.success = False
        self.timeout_in_seconds = timeout_in_seconds

        self.response_status_code: ErrorCode | None = None

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        raise NotImplementedError("create_knxipframe has to be implemented")

    async def start(self) -> None:
        """Start. Send request and wait for an answer."""
        callb = self.udpclient.register_callback(
            self.response_rec_callback, [self.awaited_response_class.SERVICE_TYPE]
        )
        await self.send_request()

        try:
            await asyncio.wait_for(
                self.response_received_event.wait(),
                timeout=self.timeout_in_seconds,
            )
        except asyncio.TimeoutError:
            logger.debug(
                "Error: KNX bus did not respond in time (%s secs) to request of type '%s'",
                self.timeout_in_seconds,
                self.__class__.__name__,
            )
        finally:
            # cleanup to not leave callbacks (for asyncio.CancelledError)
            self.udpclient.unregister_callback(callb)

    async def send_request(self) -> None:
        """Build knxipframe (within derived class) and send via UDP."""
        self.udpclient.send(self.create_knxipframe())

    def response_rec_callback(
        self, knxipframe: KNXIPFrame, source: HPAI, _: UDPClient
    ) -> None:
        """Verify and handle knxipframe. Callback from internal udpclient."""
        if not isinstance(knxipframe.body, self.awaited_response_class):
            logger.warning("Could not understand knxipframe")
            return
        self.response_status_code = knxipframe.body.status_code
        self.response_received_event.set()
        if knxipframe.body.status_code == ErrorCode.E_NO_ERROR:
            self.success = True
            self.on_success_hook(knxipframe)
        else:
            self.on_error_hook(knxipframe)

    def on_success_hook(self, knxipframe: KNXIPFrame) -> None:
        """Do something after having received a valid answer. May be overwritten in derived class."""

    def on_error_hook(self, knxipframe: KNXIPFrame) -> None:
        """Do something after having received error within given time. May be overwritten in derived class."""
        logger.debug(
            "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
            self.__class__.__name__,
            self.awaited_response_class.__name__,
            knxipframe.body.status_code,  # type: ignore
        )
