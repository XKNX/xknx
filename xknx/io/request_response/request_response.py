"""
Base class for sending a specific type of KNX/IP Packet to a KNX/IP device and wait for the corresponding answer.

Will report if the corresponding answer was not received.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, ClassVar, Generic, TypeVar, get_args

from xknx.exceptions import CommunicationError, RequestResponseError
from xknx.io.transport import KNXIPTransport
from xknx.knxip import HPAI, ErrorCode, KNXIPBody, KNXIPBodyResponse, KNXIPFrame
from xknx.util import asyncio_timeout

logger = logging.getLogger("xknx.log")

ResponseBodyT = TypeVar("ResponseBodyT", bound=KNXIPBody)


class RequestResponse(Generic[ResponseBodyT]):
    """Class for sending a specific type of KNX/IP Packet to a KNX/IP device and wait for the corresponding answer."""

    __slots__ = (
        "_error_code",
        "_response",
        "response_received_event",
        "timeout_in_seconds",
        "transport",
    )

    AWAITED_RESPONSE_CLASS: ClassVar[type[ResponseBodyT]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Derive `AWAITED_RESPONSE_CLASS` from the `RequestResponse` type argument."""
        super().__init_subclass__(**kwargs)
        for orig_base in cls.__dict__.get("__orig_bases__", ()):
            # a generic intermediate class parametrizes with its own TypeVar -
            # only a concrete subclass names the response class itself
            if (args := get_args(orig_base)) and isinstance(args[0], type):
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

        self._response: ResponseBodyT | None = None
        self._error_code: ErrorCode | None = None

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        raise NotImplementedError("create_knxipframe has to be implemented")

    async def request(self) -> ResponseBodyT:
        """
        Send the request and return the response awaited for it.

        Raise `RequestResponseError` if no response arrived in time, the request
        could not be sent, or the server answered with an error status - only the
        last of which carries an `error_code`.
        """
        callb = self.transport.register_callback(
            self.response_rec_callback, [self.AWAITED_RESPONSE_CLASS.SERVICE_TYPE]
        )
        try:
            await self.send_request()
            async with asyncio_timeout(self.timeout_in_seconds):
                await self.response_received_event.wait()
        except asyncio.TimeoutError:
            raise RequestResponseError(
                f"KNX bus did not respond in time ({self.timeout_in_seconds} secs) "
                f"to request of type '{self.__class__.__name__}'"
            ) from None
        except CommunicationError as err:
            raise RequestResponseError(
                f"Sending request of type '{self.__class__.__name__}' failed: {err}"
            ) from err
        finally:
            # cleanup to not leave callbacks (for asyncio.CancelledError)
            self.transport.unregister_callback(callb)

        if self._response is None:
            raise RequestResponseError(
                f"KNX bus responded to request of type '{self.__class__.__name__}' "
                f"with error in '{self.AWAITED_RESPONSE_CLASS.__name__}': {self._error_code}",
                error_code=self._error_code,
            )
        return self._response

    async def send_request(self) -> None:
        """Build knxipframe (within derived class) and send via transport."""
        self.transport.send(self.create_knxipframe())

    def response_rec_callback(
        self, knxipframe: KNXIPFrame, source: HPAI, _: KNXIPTransport
    ) -> None:
        """Verify and handle knxipframe. Callback from internal transport."""
        body = knxipframe.body
        if not isinstance(body, self.AWAITED_RESPONSE_CLASS):
            logger.warning(
                "Could not understand knxipframe for %s: %s",
                self.__class__.__name__,
                knxipframe,
            )
            return
        self.response_received_event.set()

        if (
            isinstance(body, KNXIPBodyResponse)
            and body.status_code != ErrorCode.E_NO_ERROR
        ):
            self._error_code = body.status_code
            return
        self._response = body
