"""
Base class for sending a specific type of KNX/IP Packet to a KNX/IP device and wait for the corresponding answer.

Will report if the corresponding answer was not received.
"""
from __future__ import annotations

import asyncio
import logging

from xknx.exceptions import CommunicationError
from xknx.io.transport import KNXIPTransport
from xknx.knxip import HPAI, ErrorCode, KNXIPBody, KNXIPBodyResponse, KNXIPFrame

logger = logging.getLogger("xknx.log")


class RequestResponse:
    """Class for sending a specific type of KNX/IP Packet to a KNX/IP device and wait for the corresponding answer."""

    def __init__(
        self,
        transport: KNXIPTransport,
        awaited_response_class: type[KNXIPBody],
        timeout_in_seconds: float = 1.0,
    ):
        """Initialize RequstResponse class."""
        self.transport = transport
        self.awaited_response_class: type[KNXIPBody] = awaited_response_class
        self.response_received_event = asyncio.Event()
        self.success = False
        self.timeout_in_seconds = timeout_in_seconds

        self.response_status_code: ErrorCode | None = None

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        raise NotImplementedError("create_knxipframe has to be implemented")

    async def start(self) -> None:
        """Start. Send request and wait for an answer."""
        callb = self.transport.register_callback(
            self.response_rec_callback, [self.awaited_response_class.SERVICE_TYPE]
        )
        try:
            await self.send_request()
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
        except CommunicationError as err:
            logger.warning(
                "Sending request of type '%s' failed: %s", self.__class__.__name__, err
            )
        finally:
            # cleanup to not leave callbacks (for asyncio.CancelledError)
            self.transport.unregister_callback(callb)

    async def send_request(self) -> None:
        """Build knxipframe (within derived class) and send via transport."""
        self.transport.send(self.create_knxipframe())

    def response_rec_callback(
        self, knxipframe: KNXIPFrame, source: HPAI, _: KNXIPTransport
    ) -> None:
        """Verify and handle knxipframe. Callback from internal transport."""
        if not isinstance(knxipframe.body, self.awaited_response_class):
            logger.warning("Could not understand knxipframe")
            return
        self.response_received_event.set()

        if isinstance(knxipframe.body, KNXIPBodyResponse):
            self.response_status_code = knxipframe.body.status_code
            if knxipframe.body.status_code != ErrorCode.E_NO_ERROR:
                logger.debug(
                    "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                    self.__class__.__name__,
                    self.awaited_response_class.__name__,
                    knxipframe.body.status_code,
                )
                return
        self.success = True
        self.on_success_hook(knxipframe)

    def on_success_hook(self, knxipframe: KNXIPFrame) -> None:
        """Do something after having received a valid answer. May be overwritten in derived class."""
