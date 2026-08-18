"""Abstraction to send DescriptionRequest and wait for DescriptionResponse."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final, TypeVar

from xknx.exceptions import CommunicationError, RequestResponseError, XKNXException
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
from .request_response import RequestResponse
from .transport import UDPTransport

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport

logger = logging.getLogger("xknx.log")

DESCRIPTION_TIMEOUT: Final = 2

_DescriptionResponseT = TypeVar(
    "_DescriptionResponseT", bound=DescriptionResponse | SearchResponseExtended
)


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
    try:
        local_ip = await util.validate_ip(local_ip, address_name="Local IP")
        gateway_ip = await util.validate_ip(gateway_ip, address_name="Gateway IP")
    except XKNXException as err:
        raise CommunicationError("Invalid address") from err

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
        try:
            gateway = await description_query.request_gateway_descriptor()
        except RequestResponseError as err:
            raise CommunicationError(
                f"Could not fetch gateway info from {gateway_ip}:{gateway_port}"
            ) from err
        if gateway.core_version >= 2:
            search_extended_query = SearchExtendedQuery(
                transport=transport,
                local_hpai=local_hpai,
            )
            try:
                gateway = await search_extended_query.request_gateway_descriptor()
            except RequestResponseError as err:
                raise CommunicationError(
                    f"Could not fetch extended gateway info from {gateway_ip}:{gateway_port}"
                ) from err
        return gateway
    finally:
        transport.stop()


# concrete subclasses implement create_knxipframe()
class _SelfDescriptionQuery(  # pylint: disable=abstract-method
    RequestResponse[_DescriptionResponseT]
):
    """Base class for handling descriptions request-response cycles."""

    __slots__ = ("local_hpai",)

    def __init__(
        self,
        transport: KNXIPTransport,
        local_hpai: HPAI,
    ) -> None:
        """Initialize Description class."""
        super().__init__(transport, timeout_in_seconds=DESCRIPTION_TIMEOUT)
        self.local_hpai = local_hpai

    async def request_gateway_descriptor(self) -> GatewayDescriptor:
        """Send the request and describe the gateway from the response to it."""
        response = await self.request()
        gateway = GatewayDescriptor(
            ip_addr=self.transport.remote_addr[0],
            port=self.transport.remote_addr[1],
            local_ip=self.transport.getsockname()[0],
        )
        gateway.parse_dibs(response.dibs)
        return gateway


class DescriptionQuery(_SelfDescriptionQuery[DescriptionResponse]):
    """Class to send a DescriptionRequest and wait for DescriptionResponse."""

    __slots__ = ()

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        description_request = DescriptionRequest(control_endpoint=self.local_hpai)
        return KNXIPFrame.init_from_body(description_request)


class SearchExtendedQuery(_SelfDescriptionQuery[SearchResponseExtended]):
    """
    Class to send a SearchRequestExtended and wait for SearchResponseExtended to a single device.

    Does only work with UDP transports.
    """

    __slots__ = ()

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
