"""
Base class for sending a specific type of KNX/IP Packet to a KNX/IP device and wait for the corresponding answer.

Will report if the corresponding answer was not received.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, ClassVar, Generic, TypeVar, get_args

from xknx.exceptions import CommunicationError
from xknx.io.transport import KNXIPTransport
from xknx.knxip import HPAI, ErrorCode, KNXIPBody, KNXIPBodyResponse, KNXIPFrame
from xknx.util import asyncio_timeout

logger = logging.getLogger("xknx.log")

ResponseBodyT = TypeVar("ResponseBodyT", bound=KNXIPBody)


class RequestResponse(Generic[ResponseBodyT]):
    """Class for sending a specific type of KNX/IP Packet to a KNX/IP device and wait for the corresponding answer."""

    __slots__ = (
        "response",
        "response_received_event",
        "response_status_code",
        "timeout_in_seconds",
        "transport",
    )

    AWAITED_RESPONSE_CLASS: ClassVar[type[ResponseBodyT]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Derive `AWAITED_RESPONSE_CLASS` from the `RequestResponse` type argument."""
        super().__init_subclass__(**kwargs)
        for orig_base in cls.__dict__.get("__orig_bases__", ()):
            if args := get_args(orig_base):
                cls.AWAITED_RESPONSE_CLASS = args[0]
                return

    def __init__(
        self,
        transport: KNXIPTransport,
        timeout_in_seconds: float = 1.0,
    ) -> None:
        """Initialize RequstResponse class."""
        self.transport = transport
        self.response_received_event = asyncio.Event()
        self.timeout_in_seconds = timeout_in_seconds

        self.response: ResponseBodyT | None = None
        self.response_status_code: ErrorCode | None = None

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        raise NotImplementedError("create_knxipframe has to be implemented")

    async def start(self) -> None:
        """Start. Send request and wait for an answer."""
        callb = self.transport.register_callback(
            self.response_rec_callback, [self.AWAITED_RESPONSE_CLASS.SERVICE_TYPE]
        )
        try:
            await self.send_request()
            async with asyncio_timeout(self.timeout_in_seconds):
                await self.response_received_event.wait()
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
        body = knxipframe.body
        if not isinstance(body, self.AWAITED_RESPONSE_CLASS):
            logger.warning("Could not understand knxipframe")
            return
        self.response_received_event.set()

        if isinstance(body, KNXIPBodyResponse):
            self.response_status_code = body.status_code
            if body.status_code != ErrorCode.E_NO_ERROR:
                logger.debug(
                    "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                    self.__class__.__name__,
                    self.AWAITED_RESPONSE_CLASS.__name__,
                    body.status_code,
                )
                return
        self.response = body
