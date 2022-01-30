"""Abstraction to send DescriptionRequest and wait for DescriptionResponse."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Final

from xknx.exceptions import XKNXException
from xknx.io.gateway_scanner import GatewayDescriptor
from xknx.knxip import HPAI, DescriptionRequest, DescriptionResponse, KNXIPFrame

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")

DESCRIPTION_TIMEOUT: Final = 2


class RequestDescription:
    """Class to send a DescriptionRequest and wait for DescriptionResponse."""

    def __init__(self, xknx: XKNX, transport: KNXIPTransport, local_hpai: HPAI):
        """Initialize Description class."""
        self.xknx = xknx
        self.transport = transport
        self.local_hpai = local_hpai

        self.gateway_descriptor: GatewayDescriptor | None = None
        self.response_received_event = asyncio.Event()

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        description_request = DescriptionRequest(
            self.xknx,
            control_endpoint=self.local_hpai,
        )
        return KNXIPFrame.init_from_body(description_request)

    async def start(self) -> None:
        """Start. Send request and wait for an answer."""
        callb = self.transport.register_callback(
            self.response_rec_callback, [DescriptionResponse.SERVICE_TYPE]
        )

        try:
            self.transport.send(self.create_knxipframe())
            await asyncio.wait_for(
                self.response_received_event.wait(),
                timeout=DESCRIPTION_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.debug(
                "Error: KNX bus did not respond in time (%s secs) to request of type '%s'",
                DESCRIPTION_TIMEOUT,
                self.__class__.__name__,
            )
        except XKNXException as ex:
            logger.error("Error: %s", ex)
        finally:
            # cleanup to not leave callbacks (for asyncio.CancelledError)
            self.transport.unregister_callback(callb)

    def response_rec_callback(
        self, knxipframe: KNXIPFrame, source: HPAI, _: KNXIPTransport
    ) -> None:
        """Verify and handle knxipframe. Callback from internal transport."""
        if not isinstance(knxipframe.body, DescriptionResponse):
            logger.warning("Wrong knxipframe for DescriptionRequest: %s", knxipframe)
            return
        self.response_received_event.set()
        # Set gateway descriptior attribute
        gateway = GatewayDescriptor(
            ip_addr=self.transport.remote_addr[0],
            port=self.transport.remote_addr[1],
            local_ip=self.transport.getsockname()[0],
        )
        gateway.parse_dibs(knxipframe.body.dibs)
        self.gateway_descriptor = gateway
