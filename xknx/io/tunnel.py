"""
Abstraction for handling KNX/IP tunnels.

Tunnels connect to KNX/IP devices directly via UDP or TCP and build a static connection.
"""
from __future__ import annotations

from abc import abstractmethod
import asyncio
import logging
from typing import TYPE_CHECKING, Awaitable, Callable

from xknx.core import XknxConnectionState
from xknx.exceptions import CommunicationError
from xknx.knxip import (
    HPAI,
    CEMIFrame,
    CEMIMessageCode,
    DisconnectRequest,
    DisconnectResponse,
    HostProtocol,
    KNXIPFrame,
    KNXIPServiceType,
    TunnellingAck,
    TunnellingRequest,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection

from .const import HEARTBEAT_RATE
from .gateway_scanner import GatewayDescriptor
from .interface import Interface
from .request_response import Connect, ConnectionState, Disconnect, Tunnelling
from .secure_session import SecureSession
from .self_description import DescriptionQuery
from .transport import KNXIPTransport, TCPTransport, UDPTransport

if TYPE_CHECKING:
    from xknx.xknx import XKNX

TelegramCallbackType = Callable[[Telegram], None]

logger = logging.getLogger("xknx.log")

# See 3/6/3 EMI_IMI §4.1.5 Data Link Layer messages
REQUEST_TO_CONFIRMATION_TIMEOUT = 3


class _Tunnel(Interface):
    """Class for handling KNX/IP tunnels."""

    transport: KNXIPTransport

    def __init__(
        self,
        xknx: XKNX,
        telegram_received_callback: TelegramCallbackType | None = None,
        auto_reconnect: bool = True,
        auto_reconnect_wait: int = 3,
    ):
        """Initialize Tunnel class."""
        self.xknx = xknx
        self.auto_reconnect = auto_reconnect
        self.auto_reconnect_wait = auto_reconnect_wait

        self.communication_channel: int | None = None
        self.local_hpai: HPAI = HPAI()
        self.sequence_number = 0
        self.telegram_received_callback = telegram_received_callback
        self._data_endpoint_addr: tuple[str, int] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._initial_connection = True
        self._is_reconnecting = False
        self._reconnect_task: asyncio.Task[None] | None = None
        self._src_address = xknx.own_address
        self._tunnelling_request_confirmation_event = asyncio.Event()

        self._init_transport()
        self.transport.register_callback(
            self._request_received,
            [KNXIPServiceType.TUNNELLING_REQUEST, KNXIPServiceType.DISCONNECT_REQUEST],
        )

    @abstractmethod
    def _init_transport(self) -> None:
        """Initialize transport transport."""
        # set up self.transport

    @abstractmethod
    async def setup_tunnel(self) -> None:
        """Set up tunnel before sending a ConnectionRequest."""
        # eg. set local HPAI used for control and data endpoint

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
            await self.transport.connect()
            await self.setup_tunnel()
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
            if not self._initial_connection and self.auto_reconnect:
                self._reconnect_task = asyncio.create_task(self._reconnect())
                return False
            # close transport to prevent open file descriptors
            self.transport.stop()
            raise CommunicationError(
                "Tunnel connection could not be established"
            ) from ex
        else:
            self._tunnel_established()
            await self.xknx.connection_manager.connection_state_changed(
                XknxConnectionState.CONNECTED
            )
            return True

    def _tunnel_established(self) -> None:
        """Set up interface when the tunnel is ready."""
        self._initial_connection = False
        self.sequence_number = 0
        self.start_heartbeat()

    def _tunnel_lost(self) -> None:
        """Prepare for reconnection or shutdown when the connection is lost. Callback."""
        self.stop_heartbeat()
        asyncio.create_task(
            self.xknx.connection_manager.connection_state_changed(
                XknxConnectionState.DISCONNECTED
            )
        )
        self._data_endpoint_addr = None
        if self.auto_reconnect:
            self._reconnect_task = asyncio.create_task(self._reconnect())
        else:
            raise CommunicationError("Tunnel connection closed.")

    async def _reconnect(self) -> None:
        """Reconnect to tunnel device."""
        if self.transport.transport:
            await self._disconnect_request(True)
            self.transport.stop()
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
        self.stop_heartbeat()
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        self._data_endpoint_addr = None
        self._stop_reconnect()
        await self._disconnect_request(False)
        self.transport.stop()

    ####################
    #
    # OUTGOING REQUESTS
    #
    ####################

    async def _connect_request(self) -> bool:
        """Connect to tunnelling server. Set communication_channel and src_address."""
        connect = Connect(transport=self.transport, local_hpai=self.local_hpai)
        await connect.start()
        if connect.success:
            self.communication_channel = connect.communication_channel
            # assign data_endpoint received from server
            self._data_endpoint_addr = (
                connect.data_endpoint.addr_tuple
                if not connect.data_endpoint.route_back
                else None
            )
            # Use the individual address provided by the tunnelling server
            self._src_address = IndividualAddress(connect.identifier)
            self.xknx.current_address = self._src_address
            logger.debug(
                "Tunnel established communication_channel=%s, address=%s",
                connect.communication_channel,
                self._src_address,
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
            transport=self.transport,
            communication_channel_id=self.communication_channel,
            local_hpai=self.local_hpai,
        )
        await conn_state.start()
        return conn_state.success

    async def _disconnect_request(self, ignore_error: bool = False) -> None:
        """Disconnect from tunnel device. Delete communication_channel."""
        if self.communication_channel is not None:
            disconnect = Disconnect(
                transport=self.transport,
                communication_channel_id=self.communication_channel,
                local_hpai=self.local_hpai,
            )
            await disconnect.start()
            if not disconnect.success and not ignore_error:
                self.communication_channel = None
                raise CommunicationError("Could not disconnect channel")
            logger.debug(
                "Tunnel disconnected (communication_channel: %s)",
                self.communication_channel,
            )
        self.communication_channel = None

    async def request_description(self) -> GatewayDescriptor | None:
        """Request description from tunneling server."""
        description = DescriptionQuery(
            transport=self.transport,
            local_hpai=self.local_hpai,
        )
        await description.start()
        return description.gateway_descriptor

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

    @abstractmethod
    async def _tunnelling_request(self, telegram: Telegram) -> bool:
        """Send Telegram to tunnelling device."""

    async def _wait_for_tunnelling_request_confirmation(
        self, send_tunneling_request_aw: Awaitable[None], telegram: Telegram
    ) -> None:
        """Wait for confirmation of tunnelling request."""
        self._tunnelling_request_confirmation_event.clear()
        send_and_wait_for_confirmation = asyncio.gather(
            send_tunneling_request_aw,
            self._tunnelling_request_confirmation_event.wait(),
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
            # could return False here to retry sending the telegram (tcp without ACK)

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
        self, knxipframe: KNXIPFrame, source: HPAI, _transport: KNXIPTransport
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

    def _disconnect_request_received(
        self, disconnect_request: DisconnectRequest
    ) -> None:
        """Handle incoming disconnect request."""
        logger.warning("Received DisconnectRequest from tunnelling sever.")
        # We should not receive DisconnectRequest for other communication_channels
        # If we do we close our communication_channel before reconnection.
        if disconnect_request.communication_channel_id == self.communication_channel:
            disconnect_response = DisconnectResponse(
                communication_channel_id=self.communication_channel,
            )
            self.transport.send(KNXIPFrame.init_from_body(disconnect_response))
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


class UDPTunnel(_Tunnel):
    """Class for handling KNX/IP UDP tunnels."""

    transport: UDPTransport

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
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.local_ip = local_ip
        self.local_port = local_port
        self.route_back = route_back
        super().__init__(
            xknx=xknx,
            telegram_received_callback=telegram_received_callback,
            auto_reconnect=auto_reconnect,
            auto_reconnect_wait=auto_reconnect_wait,
        )

    def _init_transport(self) -> None:
        """Initialize transport transport."""
        self.transport = UDPTransport(
            local_addr=(self.local_ip, self.local_port),
            remote_addr=(self.gateway_ip, self.gateway_port),
            multicast=False,
        )

    async def setup_tunnel(self) -> None:
        """Set up tunnel before sending a ConnectionRequest."""
        if self.route_back:
            self.local_hpai = HPAI()
            return
        (local_addr, local_port) = self.transport.getsockname()
        self.local_hpai = HPAI(ip_addr=local_addr, port=local_port)

    # OUTGOING REQUESTS

    async def _tunnelling_request(self, telegram: Telegram) -> bool:
        """Send Telegram to tunnelling device."""
        if self.communication_channel is None:
            raise CommunicationError(
                "Sending telegram failed. No active communication channel."
            )
        tunnelling = Tunnelling(
            transport=self.transport,
            data_endpoint=self._data_endpoint_addr,
            telegram=telegram,
            src_address=self._src_address,
            sequence_counter=self.sequence_number,
            communication_channel_id=self.communication_channel,
        )
        await self._wait_for_tunnelling_request_confirmation(
            send_tunneling_request_aw=tunnelling.start(), telegram=telegram
        )
        return tunnelling.success

    # INCOMING REQUESTS

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
        super()._tunnelling_request_received(tunneling_request)

    def _send_tunnelling_ack(
        self, communication_channel_id: int, sequence_counter: int
    ) -> None:
        """Send tunnelling ACK after tunnelling request received."""
        ack = TunnellingAck(
            communication_channel_id=communication_channel_id,
            sequence_counter=sequence_counter,
        )
        self.transport.send(
            KNXIPFrame.init_from_body(ack), addr=self._data_endpoint_addr
        )


class TCPTunnel(_Tunnel):
    """Class for handling KNX/IP TCP tunnels."""

    transport: TCPTransport

    def __init__(
        self,
        xknx: XKNX,
        gateway_ip: str,
        gateway_port: int,
        telegram_received_callback: TelegramCallbackType | None = None,
        auto_reconnect: bool = True,
        auto_reconnect_wait: int = 3,
    ):
        """Initialize Tunnel class."""
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        super().__init__(
            xknx=xknx,
            telegram_received_callback=telegram_received_callback,
            auto_reconnect=auto_reconnect,
            auto_reconnect_wait=auto_reconnect_wait,
        )
        # TCP always uses 0.0.0.0:0
        self.local_hpai = HPAI(protocol=HostProtocol.IPV4_TCP)

    def _init_transport(self) -> None:
        """Initialize transport transport."""
        self.transport = TCPTransport(
            remote_addr=(self.gateway_ip, self.gateway_port),
            connection_lost_cb=self._tunnel_lost,
        )

    async def setup_tunnel(self) -> None:
        """Set up tunnel before sending a ConnectionRequest."""

    async def _tunnelling_request(self, telegram: Telegram) -> bool:
        """Send Telegram to tunnelling device."""
        if self.communication_channel is None:
            raise CommunicationError(
                "Sending telegram failed. No active communication channel."
            )
        cemi = CEMIFrame.init_from_telegram(
            telegram=telegram,
            code=CEMIMessageCode.L_DATA_REQ,
            src_addr=self._src_address,
        )
        tunnelling_request = TunnellingRequest(
            communication_channel_id=self.communication_channel,
            sequence_counter=self.sequence_number,
            cemi=cemi,
        )

        async def _async_wrapper() -> None:
            self.transport.send(KNXIPFrame.init_from_body(tunnelling_request))

        await self._wait_for_tunnelling_request_confirmation(
            send_tunneling_request_aw=_async_wrapper(),
            telegram=telegram,
        )
        return True


class SecureTunnel(TCPTunnel):
    """Class for handling KNX/IP secure TCP tunnels."""

    transport: SecureSession

    def __init__(
        self,
        xknx: XKNX,
        gateway_ip: str,
        gateway_port: int,
        user_id: int,
        user_password: str,
        telegram_received_callback: TelegramCallbackType | None = None,
        auto_reconnect: bool = True,
        auto_reconnect_wait: int = 3,
        device_authentication_password: str | None = None,
    ):
        """Initialize SecureTunnel class."""
        self._device_authentication_password = device_authentication_password
        self._user_id = user_id
        self._user_password = user_password
        super().__init__(
            xknx=xknx,
            gateway_ip=gateway_ip,
            gateway_port=gateway_port,
            telegram_received_callback=telegram_received_callback,
            auto_reconnect=auto_reconnect,
            auto_reconnect_wait=auto_reconnect_wait,
        )

    def _init_transport(self) -> None:
        """Initialize transport transport."""
        self.transport = SecureSession(
            remote_addr=(self.gateway_ip, self.gateway_port),
            user_id=self._user_id,
            user_password=self._user_password,
            device_authentication_password=self._device_authentication_password,
            connection_lost_cb=self._tunnel_lost,
        )
