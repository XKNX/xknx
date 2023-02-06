"""Abstraction to send DescriptionRequest and wait for DescriptionResponse."""
from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
import logging
from typing import TYPE_CHECKING, Final

from xknx.exceptions import CommunicationError
from xknx.io import util
from xknx.io.gateway_scanner import GatewayDescriptor
from xknx.knxip import (
    HPAI,
    SRP,
    DescriptionRequest,
    DescriptionResponse,
    DIBTypeCode,
    KNXIPFrame,
    SearchRequestExtended,
    SearchResponseExtended,
)

from .const import DEFAULT_MCAST_PORT
from .transport import UDPTransport

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport

logger = logging.getLogger("xknx.log")

DESCRIPTION_TIMEOUT: Final = 2


async def request_description(
    gateway_ip: str,
    gateway_port: int = DEFAULT_MCAST_PORT,
    local_ip: str | None = None,
    local_port: int = 0,
    route_back: bool = False,
) -> GatewayDescriptor:
    """Set up a UDP transport to request a description from a KNXnet/IP device."""
    local_ip = local_ip or util.find_local_ip(gateway_ip)
    if local_ip is None:
        # Fall back to default interface and use route back
        local_ip = await util.get_default_local_ip(gateway_ip)
        if local_ip is None:
            raise CommunicationError(
                f"No network interface found to request gateway info from {gateway_ip}:{gateway_port}"
            )
        route_back = True

    transport = UDPTransport(
        local_addr=(local_ip, local_port),
        remote_addr=(gateway_ip, gateway_port),
        multicast=False,
    )
    try:
        await transport.connect()
    except OSError as err:
        raise CommunicationError(
            "Could not setup socket to request gateway info"
        ) from err
    else:
        local_hpai: HPAI
        if route_back:
            local_hpai = HPAI()
        else:
            local_addr = transport.getsockname()
            local_hpai = HPAI(*local_addr)

        description_query = DescriptionQuery(
            transport=transport,
            local_hpai=local_hpai,
        )
        await description_query.start()
        gateway = description_query.gateway_descriptor
        if gateway is None:
            raise CommunicationError(
                f"Could not fetch gateway info from {gateway_ip}:{gateway_port}"
            )
        if gateway.core_version >= 2:
            search_extended_query = SearchExtendedQuery(
                transport=transport,
                local_hpai=local_hpai,
            )
            await search_extended_query.start()
            gateway = search_extended_query.gateway_descriptor
            if gateway is None:
                raise CommunicationError(
                    f"Could not fetch extended gateway info from {gateway_ip}:{gateway_port}"
                )
        return gateway
    finally:
        transport.stop()


class _SelfDescriptionQuery(ABC):
    """Base class for handling descriptions request-response cycles."""

    expected_response_class: type[DescriptionResponse] | type[SearchResponseExtended]

    def __init__(
        self,
        transport: KNXIPTransport,
        local_hpai: HPAI,
    ) -> None:
        """Initialize Description class."""
        self.transport = transport
        self.local_hpai = local_hpai

        self.gateway_descriptor: GatewayDescriptor | None = None
        self.response_received_event = asyncio.Event()

    @abstractmethod
    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""

    async def start(self) -> None:
        """Start. Send request and wait for an answer."""
        callb = self.transport.register_callback(
            self.response_rec_callback, [self.expected_response_class.SERVICE_TYPE]
        )
        frame = self.create_knxipframe()
        try:
            self.transport.send(frame)
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
            logger.warning("Sending %s failed: %s", frame.body.__class__.__name__, err)
        finally:
            # cleanup to not leave callbacks (for asyncio.CancelledError)
            self.transport.unregister_callback(callb)

    def response_rec_callback(
        self, knxipframe: KNXIPFrame, source: HPAI, _: KNXIPTransport
    ) -> None:
        """Verify and handle knxipframe. Callback from internal transport."""
        if not isinstance(knxipframe.body, self.expected_response_class):
            logger.warning(
                "Wrong knxipframe for %s: %s", self.__class__.__name__, knxipframe
            )
            return
        self.response_received_event.set()
        # Set gateway descriptor attribute
        gateway = GatewayDescriptor(
            ip_addr=self.transport.remote_addr[0],
            port=self.transport.remote_addr[1],
            local_ip=self.transport.getsockname()[0],
        )
        gateway.parse_dibs(knxipframe.body.dibs)  # type: ignore[attr-defined]
        self.gateway_descriptor = gateway


class DescriptionQuery(_SelfDescriptionQuery):
    """Class to send a DescriptionRequest and wait for DescriptionResponse."""

    expected_response_class = DescriptionResponse

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        description_request = DescriptionRequest(control_endpoint=self.local_hpai)
        return KNXIPFrame.init_from_body(description_request)


class SearchExtendedQuery(_SelfDescriptionQuery):
    """
    Class to send a SearchRequestExtended and wait for SearchResponseExtended to a single device.

    Does only work with UDP transports.
    """

    expected_response_class = SearchResponseExtended

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        search_extended_request = SearchRequestExtended(
            discovery_endpoint=self.local_hpai,
            srps=[
                SRP.request_device_description(
                    [
                        DIBTypeCode.DEVICE_INFO,
                        DIBTypeCode.SUPP_SVC_FAMILIES,
                        DIBTypeCode.SECURED_SERVICE_FAMILIES,
                        DIBTypeCode.TUNNELING_INFO,
                    ]
                )
            ],
        )
        return KNXIPFrame.init_from_body(search_extended_request)
