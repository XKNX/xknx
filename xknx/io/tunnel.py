"""
Abstraction for handling KNX/IP tunnels.

Tunnels connect to KNX/IP devices directly via UDP and build a static UDP connection.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Callable

from xknx.exceptions import CommunicationError, XKNXException
from xknx.knxip import (
    HPAI,
    CEMIMessageCode,
    DisconnectRequest,
    DisconnectResponse,
    KNXIPFrame,
    KNXIPServiceType,
    TunnellingAck,
    TunnellingRequest,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection

from ..core import XknxConnectionState
from .const import HEARTBEAT_RATE
from .interface import Interface
from .request_response import Connect, ConnectionState, Disconnect, Tunnelling
from .udp_client import UDPClient

if TYPE_CHECKING:
    from xknx.xknx import XKNX

TelegramCallbackType = Callable[[Telegram], None]

logger = logging.getLogger("xknx.log")

# See 3/6/3 EMI_IMI §4.1.5 Data Link Layer messages
REQUEST_TO_CONFIRMATION_TIMEOUT = 3


class Tunnel(Interface):
    """Class for handling KNX/IP tunnels."""

    def __init__(
        self,
        xknx: XKNX,
        gateway_ip: str,
        gateway_port: int,
        local_ip: str,
        local_port: int = 0,
        route_back: bool = False,
        telegram_received_callback: TelegramCallbackType | None = None,
        auto_reconnect: bool = True,
        auto_reconnect_wait: int = 3,
    ):
        """Initialize Tunnel class."""
        self.xknx = xknx
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.local_ip = local_ip
        self.local_port = local_port
        self.route_back = route_back
        self.telegram_received_callback = telegram_received_callback

        self._tunnelling_request_confirmation_event = asyncio.Event()

        self.udp_client: UDPClient
        self.init_udp_client()

        self._src_address = xknx.own_address
        self.sequence_number = 0
        self.communication_channel: int | None = None
        self.number_heartbeat_failed = 0

        self.auto_reconnect = auto_reconnect
        self.auto_reconnect_wait = auto_reconnect_wait

        self._heartbeat_task: asyncio.Task[None] | None = None
        self._reconnect_task: asyncio.Task[None] | None = None

        self._is_reconnecting = False

    def init_udp_client(self) -> None:
        """Initialize udp_client."""
        self.udp_client = UDPClient(
            self.xknx,
            (self.local_ip, self.local_port),
            (self.gateway_ip, self.gateway_port),
        )

        self.udp_client.register_callback(
            self._request_received,
            [KNXIPServiceType.TUNNELLING_REQUEST, KNXIPServiceType.DISCONNECT_REQUEST],
        )

    ####################
    #
    # CONNECT DISCONNECT
    #
    ####################

    async def connect(self) -> bool:
        """Connect to a KNX tunneling interface. Returns True on success."""
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTING
        )
        try:
            await self.udp_client.connect()
            await self._connect_request()
        except (OSError, CommunicationError) as ex:
            logger.debug(
                "Could not establish connection to KNX/IP interface. %s: %s",
                type(ex).__name__,
                ex,
            )
            await self.xknx.connection_manager.connection_state_changed(
                XknxConnectionState.DISCONNECTED
            )
            if self.auto_reconnect:
                self._reconnect_task = asyncio.create_task(self._reconnect())
                return False
            # close udp client to prevent open file descriptors
            await self.udp_client.stop()
            raise ex
        else:
            self._tunnel_established()
            await self.xknx.connection_manager.connection_state_changed(
                XknxConnectionState.CONNECTED
            )
            return True

    def _tunnel_established(self) -> None:
        """Set up interface when the tunnel is ready."""
        self.sequence_number = 0
        # self._stop_reconnect()
        self.start_heartbeat()

    def _tunnel_lost(self) -> None:
        """Prepare for reconnection or shutdown when the connection is lost. Callback."""
        asyncio.create_task(
            self.xknx.connection_manager.connection_state_changed(
                XknxConnectionState.DISCONNECTED
            )
        )
        self.stop_heartbeat()
        if self.auto_reconnect:
            self._reconnect_task = asyncio.create_task(self._reconnect())
        else:
            raise CommunicationError("Tunnel connection closed.")

    async def _reconnect(self) -> None:
        """Reconnect to tunnel device."""
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTING
        )
        await self._disconnect_request(True)
        await self.udp_client.stop()
        await asyncio.sleep(self.auto_reconnect_wait)
        if await self.connect():
            logger.info("Successfully reconnected to KNX bus.")

    def _stop_reconnect(self) -> None:
        """Stop reconnect task if running."""
        if self._reconnect_task is not None:
            self._reconnect_task.cancel()
            self._reconnect_task = None

    async def disconnect(self) -> None:
        """Disconnect tunneling connection."""
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        self.stop_heartbeat()
        self._stop_reconnect()
        await self._disconnect_request(False)
        await self.udp_client.stop()

    ####################
    #
    # OUTGOING REQUESTS
    #
    ####################

    async def _connect_request(self) -> bool:
        """Connect to tunnelling server. Set communication_channel and src_address."""
        connect = Connect(self.xknx, self.udp_client, route_back=self.route_back)
        await connect.start()
        if connect.success:
            self.communication_channel = connect.communication_channel
            # Use the individual address provided by the tunnelling server
            self._src_address = IndividualAddress(connect.identifier)
            self.xknx.current_address = self._src_address
            logger.debug(
                "Tunnel established communication_channel=%s, id=%s",
                connect.communication_channel,
                connect.identifier,
            )
            return True
        raise CommunicationError(
            f"ConnectRequest failed. Status code: {connect.response_status_code}"
        )

    async def _connectionstate_request(self) -> bool:
        """Return state of tunnel. True if tunnel is in good shape."""
        if self.communication_channel is None:
            raise CommunicationError("No active communication channel.")
        conn_state = ConnectionState(
            self.xknx,
            self.udp_client,
            communication_channel_id=self.communication_channel,
            route_back=self.route_back,
        )
        await conn_state.start()
        return conn_state.success

    async def _disconnect_request(self, ignore_error: bool = False) -> None:
        """Disconnect from tunnel device. Delete communication_channel."""
        if self.communication_channel is not None:
            disconnect = Disconnect(
                self.xknx,
                self.udp_client,
                communication_channel_id=self.communication_channel,
                route_back=self.route_back,
            )
            await disconnect.start()
            if not disconnect.success and not ignore_error:
                self.communication_channel = None
                raise XKNXException("Could not disconnect channel")
            logger.debug(
                "Tunnel disconnected (communication_channel: %s)",
                self.communication_channel,
            )
        self.communication_channel = None

    async def send_telegram(self, telegram: Telegram) -> None:
        """
        Send Telegram to routing tunnelling device - retry mechanism.

        If a TUNNELLING_REQUEST frame is not confirmed within the TUNNELLING_REQUEST_TIME_- OUT
        time of one (1) second then the frame shall be repeated once with the same sequence counter
        value by the sending KNXnet/IP device.

        If the KNXnet/IP device does not receive a TUNNELLING_ACK frame within the
        TUNNELLING_- REQUEST_TIMEOUT (= 1 second) or the status of a received
        TUNNELLING_ACK frame signals any kind of error condition, the sending device
        shall repeat the TUNNELLING_REQUEST frame once and then terminate the
        connection by sending a DISCONNECT_REQUEST frame to the other device’s
        control endpoint.
        """
        success = await self._tunnelling_request(telegram)
        if not success:
            logger.debug("Sending of telegram failed. Retrying a second time.")
            success = await self._tunnelling_request(telegram)
            if not success:
                logger.debug("Resending telegram failed. Reconnecting to tunnel.")
                # TODO: How to test this?
                if self._reconnect_task is None or self._reconnect_task.done():
                    self._tunnel_lost()
                await self.xknx.connection_manager.connected.wait()
                success = await self._tunnelling_request(telegram)
                if not success:
                    raise CommunicationError(
                        "Resending the telegram repeatedly failed.", True
                    )
        self._increase_sequence_number()

    async def _tunnelling_request(self, telegram: Telegram) -> bool:
        """Send Telegram to tunnelling device."""
        if self.communication_channel is None:
            raise CommunicationError(
                "Sending telegram failed. No active communication channel."
            )
        tunnelling = Tunnelling(
            self.xknx,
            self.udp_client,
            telegram,
            self._src_address,
            self.sequence_number,
            self.communication_channel,
        )
        self._tunnelling_request_confirmation_event.clear()
        send_and_wait_for_confirmation = asyncio.gather(
            tunnelling.start(), self._tunnelling_request_confirmation_event.wait()
        )
        try:
            await asyncio.wait_for(
                send_and_wait_for_confirmation, timeout=REQUEST_TO_CONFIRMATION_TIMEOUT
            )
        except asyncio.TimeoutError:
            # REQUEST_TO_CONFIRMATION_TIMEOUT is longer than tunnelling timeout of 1 second
            # so exception should always be from self._tunnelling_request_confirmation_event
            logger.warning(
                "L_DATA_CON Data Link Layer confirmation timed out for %s", telegram
            )
        return tunnelling.success

    def _increase_sequence_number(self) -> None:
        """Increase sequence number."""
        self.sequence_number += 1
        if self.sequence_number == 256:
            self.sequence_number = 0

    ####################
    #
    # INCOMING REQUESTS
    #
    ####################

    def _request_received(
        self, knxipframe: KNXIPFrame, source: HPAI, _udp_client: UDPClient
    ) -> None:
        """Handle incoming requests."""
        if isinstance(knxipframe.body, TunnellingRequest):
            self._tunnelling_request_received(knxipframe.body)
        elif isinstance(knxipframe.body, DisconnectRequest):
            self._disconnect_request_received(knxipframe.body)
        else:
            logger.warning("Service not implemented: %s", knxipframe)

    def _tunnelling_request_received(
        self, tunneling_request: TunnellingRequest
    ) -> None:
        """Handle incoming tunnel request."""
        # we should only ACK if the request matches the expected sequence number or one less
        # we should not ACK and discard the request if the sequence number is higher than the expected sequence number
        #   or if the sequence number lower thatn (expected -1)
        self._send_tunnelling_ack(
            tunneling_request.communication_channel_id,
            tunneling_request.sequence_counter,
        )
        if tunneling_request.cemi is None:
            # Don't handle invalid cemi frames (None)
            return
        if tunneling_request.cemi.code is CEMIMessageCode.L_DATA_IND:
            telegram = tunneling_request.cemi.telegram
            telegram.direction = TelegramDirection.INCOMING
            if self.telegram_received_callback is not None:
                self.telegram_received_callback(telegram)
        elif tunneling_request.cemi.code is CEMIMessageCode.L_DATA_CON:
            # L_DATA_CON confirmation frame signals ready to send next telegram
            self._tunnelling_request_confirmation_event.set()
        elif tunneling_request.cemi.code is CEMIMessageCode.L_DATA_REQ:
            # L_DATA_REQ frames should only be outgoing.
            logger.warning(
                "Tunnel received unexpected L_DATA_REQ frame: %s", tunneling_request
            )

    def _send_tunnelling_ack(
        self, communication_channel_id: int, sequence_counter: int
    ) -> None:
        """Send tunnelling ACK after tunnelling request received."""
        ack = TunnellingAck(
            self.xknx,
            communication_channel_id=communication_channel_id,
            sequence_counter=sequence_counter,
        )
        self.udp_client.send(KNXIPFrame.init_from_body(ack))

    def _disconnect_request_received(
        self, disconnect_request: DisconnectRequest
    ) -> None:
        """Handle incoming disconnect request."""
        logger.warning("Received DisconnectRequest from tunnelling sever.")
        # We should not receive DisconnectRequest for other communication_channels
        # If we do we close our communication_channel before reconnection.
        if disconnect_request.communication_channel_id == self.communication_channel:
            disconnect_response = DisconnectResponse(
                self.xknx,
                communication_channel_id=self.communication_channel,
            )
            self.udp_client.send(KNXIPFrame.init_from_body(disconnect_response))
            self.communication_channel = None
        self._tunnel_lost()

    ####################
    #
    # HEARTBEAT
    #
    ####################

    def start_heartbeat(self) -> None:
        """Start heartbeat for monitoring state of tunnel, as suggested by 03.08.02 KNX Core 5.4."""
        self._heartbeat_task = asyncio.create_task(self.do_heartbeat())

    def stop_heartbeat(self) -> None:
        """Stop heartbeat task if running."""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def do_heartbeat(self) -> None:
        """Heartbeat: Worker task, endless loop for sending heartbeat requests."""
        while True:
            try:
                await asyncio.sleep(HEARTBEAT_RATE)
                if not await self._connectionstate_request():
                    await self._do_heartbeat_failed()
            except CommunicationError as err:
                logger.warning("Heartbeat to KNX bus failed. %s", err)
                self._tunnel_lost()

    async def _do_heartbeat_failed(self) -> None:
        """Heartbeat: handling error."""
        # first heartbeat failed - try 3 more times before disconnecting.
        for _heartbeats_failed in range(3):
            if await self._connectionstate_request():
                return
        # 3 retries failed
        raise CommunicationError("No answer from tunneling server.")
