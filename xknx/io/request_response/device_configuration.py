"""Abstraction to send a DeviceConfigurationRequest and wait for DeviceConfigurationAck."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.io.const import DEVICE_CONFIGURATION_REQUEST_TIMEOUT
from xknx.knxip import DeviceConfigurationAck, DeviceConfigurationRequest, KNXIPFrame

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import UDPTransport


class DeviceConfiguration(RequestResponse[DeviceConfigurationAck]):
    """Class to send DeviceConfigurationRequest and wait for DeviceConfigurationAck (UDP only)."""

    __slots__ = ("data_endpoint_addr", "device_configuration_request")

    _transport: UDPTransport

    def __init__(
        self,
        transport: UDPTransport,
        data_endpoint: tuple[str, int] | None,
        device_configuration_request: DeviceConfigurationRequest,
        timeout_in_seconds: float = DEVICE_CONFIGURATION_REQUEST_TIMEOUT,
    ) -> None:
        """Initialize DeviceConfiguration class."""
        self.data_endpoint_addr = data_endpoint
        self.device_configuration_request = device_configuration_request
        super().__init__(transport, timeout_in_seconds=timeout_in_seconds)

    async def _send_request(self) -> None:
        """Build knxipframe (within derived class) and send via UDP."""
        self._transport.send(self._create_knxipframe(), addr=self.data_endpoint_addr)

    def _create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        return KNXIPFrame.init_from_body(self.device_configuration_request)

    def _matches_request(self, body: DeviceConfigurationAck) -> bool:
        """Return whether the ACK confirms this request - not a stale one of a repeated frame."""
        return (
            body.communication_channel_id
            == self.device_configuration_request.communication_channel_id
            and body.sequence_counter
            == self.device_configuration_request.sequence_counter
        )
