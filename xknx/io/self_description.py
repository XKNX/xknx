"""Abstraction to send DescriptionRequest and wait for DescriptionResponse."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Final

from xknx.exceptions import CommunicationError
from xknx.io.gateway_scanner import GatewayDescriptor
from xknx.knxip import HPAI, DescriptionRequest, DescriptionResponse, KNXIPFrame

from .const import DEFAULT_MCAST_PORT
from .transport import UDPTransport
from .util import find_local_ip

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")

DESCRIPTION_TIMEOUT: Final = 2


async def request_description(
    xknx: XKNX,
    gateway_ip: str,
    gateway_port: int = DEFAULT_MCAST_PORT,
    local_ip: str | None = None,
    local_port: int = 0,
    route_back: bool = False,
) -> GatewayDescriptor | None:
    """Set up a UDP transport to request a description from a KNXnet/IP device."""
    _local_ip = local_ip or find_local_ip(gateway_ip)
    transport = UDPTransport(
        xknx,
        local_addr=(_local_ip, local_port),
        remote_addr=(gateway_ip, gateway_port),
        multicast=False,
    )
    try:
        await transport.connect()
    except OSError as err:
        logger.warning("Could not setup socket: %s", err)
        return None

    local_hpai: HPAI
    if route_back:
        local_hpai = HPAI()
    else:
        local_addr = transport.getsockname()
        local_hpai = HPAI(*local_addr)

    description_query = DescriptionQuery(
        xknx,
        transport,
        local_hpai=local_hpai,
    )
    await description_query.start()
    transport.stop()
    return description_query.gateway_descriptor


class DescriptionQuery:
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
        except CommunicationError as err:
            logger.warning("Sending DescriptionRequest failed: %s", err)
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
