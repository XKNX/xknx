"""Abstraction to answer DeviceConfigurationRequests of a device management connection."""

from __future__ import annotations

from collections.abc import Callable
import logging

from xknx.knxip import (
    HPAI,
    DeviceConfigurationAck,
    DeviceConfigurationRequest,
    KNXIPFrame,
    KNXIPServiceType,
)

from .data_connection import IncomingSequenceCounter, SequenceVerdict
from .transport import KNXIPTransport, UDPTransport

logger = logging.getLogger("xknx.log")


class DeviceManagement:
    """
    Acknowledge DeviceConfigurationRequests received over a device management connection.

    A KNXnet/IP server sends requests of its own over a device management
    connection - M_PropRead.con, M_PropWrite.con, M_FuncPropStateResponse.con
    and M_PropInfo.ind are all mandatory in that direction - and repeats each
    of them until it is acknowledged, then drops the connection. Sending those
    acknowledgements is the client's part; `DeviceConfiguration` covers the
    other direction.

    The acknowledgement confirms the reception of the frame, not the cEMI it
    carries, so it is sent whatever the payload turns out to be - the frame is
    handed on as raw bytes and even one the receiver ends up ignoring is
    acknowledged.

    The connection itself belongs to the caller: this class does not open,
    close or supervise it, it only handles the frames arriving on `transport`
    for `communication_channel` while it is started. UDP only, as a device
    management connection over TCP is not acknowledged.
    """

    __slots__ = (
        "_callback",
        "_sequence",
        "cemi_received_callback",
        "communication_channel",
        "data_endpoint_addr",
        "transport",
    )

    def __init__(
        self,
        transport: UDPTransport,
        communication_channel: int,
        cemi_received_callback: Callable[[bytes], None] | None = None,
        data_endpoint: tuple[str, int] | None = None,
    ) -> None:
        """Initialize DeviceManagement class."""
        self.transport = transport
        self.communication_channel = communication_channel
        self.cemi_received_callback = cemi_received_callback
        self.data_endpoint_addr = data_endpoint
        self._sequence = IncomingSequenceCounter()
        self._callback: UDPTransport.Callback | None = None

    def start(self) -> None:
        """Start answering incoming requests."""
        if self._callback is not None:
            return
        # A sequence counter starts at 0 for every established connection, so
        # an instance reused for a new one does not carry the old count over.
        self._sequence.reset()
        self._callback = self.transport.register_callback(
            self._request_received,
            [KNXIPServiceType.DEVICE_CONFIGURATION_REQUEST],
        )

    def stop(self) -> None:
        """Stop answering incoming requests."""
        if self._callback is None:
            return
        self.transport.unregister_callback(self._callback)
        self._callback = None

    def _request_received(
        self, knxipframe: KNXIPFrame, source: HPAI, _transport: KNXIPTransport
    ) -> None:
        """Handle incoming requests."""
        if not isinstance(knxipframe.body, DeviceConfigurationRequest):
            logger.warning("Service not implemented: %s", knxipframe)
            return
        self._device_configuration_request_received(knxipframe.body)

    def _device_configuration_request_received(
        self, request: DeviceConfigurationRequest
    ) -> None:
        """Handle an incoming device configuration request."""
        if request.communication_channel_id != self.communication_channel:
            logger.debug(
                "Received DeviceConfigurationRequest for another communication channel "
                "than %s. Discarding frame: %s",
                self.communication_channel,
                request,
            )
            return
        verdict = self._sequence.evaluate(request.sequence_counter)
        if verdict is SequenceVerdict.EXPECTED:
            self._send_device_configuration_ack(request.sequence_counter)
            if self.cemi_received_callback is not None:
                self.cemi_received_callback(request.raw_cemi)
            return
        if verdict is SequenceVerdict.REPEATED:
            self._send_device_configuration_ack(request.sequence_counter)
            logger.debug(
                "Received DeviceConfigurationRequest with sequence number one less "
                "than expected. Discarding frame: %s",
                request,
            )
            return
        # Dropped without an acknowledgement; the server repeats the frame and
        # closes the connection when that is not acknowledged either. Unlike
        # the tunnel, which schedules a disconnect for servers that fail to do
        # that, this class only observes: the connection belongs to the caller,
        # and its heartbeat will notice a server that dropped the channel
        # silently.
        logger.warning(
            "Received DeviceConfigurationRequest with sequence number not equal to "
            "expected: %s. Discarding frame: %s",
            self._sequence.expected,
            request,
        )

    def _send_device_configuration_ack(self, sequence_counter: int) -> None:
        """Send a device configuration ACK after a request was received."""
        ack = DeviceConfigurationAck(
            communication_channel_id=self.communication_channel,
            sequence_counter=sequence_counter,
        )
        self.transport.send(
            KNXIPFrame.init_from_body(ack), addr=self.data_endpoint_addr
        )
