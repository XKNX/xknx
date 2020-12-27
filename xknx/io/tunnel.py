"""
Abstraction for handling KNX/IP tunnels.

Tunnels connect to KNX/IP devices directly via UDP and build a static UDP connection.
"""
import asyncio
import logging

from xknx.exceptions import CommunicationError, XKNXException
from xknx.knxip import (
    CEMIMessageCode,
    DisconnectRequest,
    DisconnectResponse,
    KNXIPFrame,
    KNXIPServiceType,
    TunnellingAck,
    TunnellingRequest,
)
from xknx.telegram import IndividualAddress, TelegramDirection

from .connect import Connect
from .connectionstate import ConnectionState
from .const import HEARTBEAT_RATE
from .disconnect import Disconnect
from .interface import Interface
from .tunnelling import Tunnelling
from .udp_client import UDPClient

logger = logging.getLogger("xknx.log")


class Tunnel(Interface):
    """Class for handling KNX/IP tunnels."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        xknx,
        local_ip,
        local_port,
        gateway_ip,
        gateway_port,
        route_back,
        telegram_received_callback=None,
        auto_reconnect=False,
        auto_reconnect_wait=3,
    ):
        """Initialize Tunnel class."""
        # pylint: disable=too-many-arguments
        self.xknx = xknx
        self.local_ip = local_ip
        self.local_port = local_port
        self.route_back = route_back
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.telegram_received_callback = telegram_received_callback

        self.udp_client = None
        self.init_udp_client()

        self._src_address = xknx.own_address
        self.sequence_number = 0
        self.communication_channel = None
        self.number_heartbeat_failed = 0

        self.auto_reconnect = auto_reconnect
        self.auto_reconnect_wait = auto_reconnect_wait

        self._heartbeat_task = None
        self._reconnect_task = None

        self._is_reconnecting = False

    def init_udp_client(self):
        """Initialize udp_client."""
        self.udp_client = UDPClient(
            self.xknx, (self.local_ip, self.local_port), (self.gateway_ip, self.gateway_port)
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

    async def connect(self):
        """Connect to a KNX tunneling interface. Returns True on success."""
        try:
            await self.udp_client.connect()
            await self._connect_request()
        except (OSError, CommunicationError) as ex:
            logger.debug(
                "Could not establish connection to KNX/IP interface. %s: %s",
                type(ex).__name__,
                ex,
            )
            if self.auto_reconnect:
                self._reconnect_task = asyncio.create_task(self._reconnect())
                return False
            # close udp client to prevent open file descriptors
            await self.udp_client.stop()
            raise ex
        else:
            self._tunnel_established()
            return True

    def _tunnel_established(self):
        """Set up interface when the tunnel is ready."""
        self.sequence_number = 0
        self.xknx.connected.set()
        # self._stop_reconnect()
        self.start_heartbeat()

    def _tunnel_lost(self):
        """Prepare for reconnection or shutdown when the connection is lost. Callback."""
        self.xknx.connected.clear()
        self.stop_heartbeat()
        if self.auto_reconnect:
            self._reconnect_task = asyncio.create_task(self._reconnect())
        else:
            raise CommunicationError("Tunnel connection closed.")

    async def _reconnect(self):
        """Reconnect to tunnel device."""
        # only send disconnect request if we ever were connected
        if self.communication_channel is not None:
            await self._disconnect_request(True)
            self.communication_channel = None
        await self.udp_client.stop()
        await asyncio.sleep(self.auto_reconnect_wait)
        if await self.connect():
            logger.info("Successfully reconnected to KNX bus.")

    def _stop_reconnect(self):
        """Stop reconnect task if running."""
        if self._reconnect_task is not None:
            self._reconnect_task.cancel()
            self._reconnect_task = None

    async def disconnect(self):
        """Disconnect tunneling connection."""
        self.xknx.connected.clear()
        self.stop_heartbeat()
        self._stop_reconnect()
        if self.communication_channel is not None:
            await self._disconnect_request(False)
            self.communication_channel = None
        await self.udp_client.stop()

    ####################
    #
    # OUTGOING REQUESTS
    #
    ####################

    async def _connect_request(self) -> bool:
        """Connect to tunnelling server. Return True if succeeded."""
        connect = Connect(self.xknx, self.udp_client, route_back=self.route_back)
        await connect.start()
        if connect.success:
            self.communication_channel = connect.communication_channel
            # Use the individual address provided by the tunnelling server
            self._src_address = IndividualAddress(connect.identifier)
            logger.debug(
                "Tunnel established communication_channel=%s, id=%s",
                connect.communication_channel,
                connect.identifier,
            )
            return True
        raise CommunicationError("ConnectRequest failed")

    async def _connectionstate_request(self):
        """Return state of tunnel. True if tunnel is in good shape."""
        conn_state = ConnectionState(
            self.xknx,
            self.udp_client,
            communication_channel_id=self.communication_channel,
            route_back=self.route_back,
        )
        await conn_state.start()
        return conn_state.success

    async def _disconnect_request(self, ignore_error=False):
        """Disconnect from tunnel device."""
        disconnect = Disconnect(
            self.xknx,
            self.udp_client,
            communication_channel_id=self.communication_channel,
            route_back=self.route_back,
        )
        await disconnect.start()
        if not disconnect.success and not ignore_error:
            raise XKNXException("Could not disconnect channel")
        logger.debug(
            "Tunnel disconnected (communication_channel: %s)",
            self.communication_channel,
        )

    async def send_telegram(self, telegram):
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
                await self.xknx.connected.wait()
                success = await self._tunnelling_request(telegram)
                if not success:
                    raise CommunicationError(
                        "Resending the telegram repeatedly failed.", True
                    )
        self._increase_sequence_number()

    async def _tunnelling_request(self, telegram):
        """Send Telegram to tunnelling device."""
        tunnelling = Tunnelling(
            self.xknx,
            self.udp_client,
            telegram,
            self._src_address,
            self.sequence_number,
            self.communication_channel,
        )
        await tunnelling.start()
        return tunnelling.success

    def _increase_sequence_number(self):
        """Increase sequence number."""
        self.sequence_number += 1
        if self.sequence_number == 256:
            self.sequence_number = 0

    ####################
    #
    # INCOMING REQUESTS
    #
    ####################

    def _request_received(self, knxipframe, _udp_client):
        """Handle incoming requests."""
        # pylint: disable=unused-argument
        if knxipframe.header.service_type_ident is KNXIPServiceType.TUNNELLING_REQUEST:
            self._tunnelling_request_received(knxipframe.body)
        elif (
            knxipframe.header.service_type_ident is KNXIPServiceType.DISCONNECT_REQUEST
        ):
            self._disconnect_request_received(knxipframe.body)
        else:
            logger.warning("Service not implemented: %s", knxipframe)

    def _tunnelling_request_received(self, tunneling_request: TunnellingRequest):
        """Handle incoming tunnel request."""
        self._send_tunnelling_ack(
            tunneling_request.communication_channel_id,
            tunneling_request.sequence_counter,
        )
        # Don't handle invalid cemi frames (None) and only handle incoming L_DATA_IND frames.
        # Ignore L_DATA_CON confirmation frames. L_DATA_REQ frames should only be outgoing.
        if (
            tunneling_request.cemi is not None
            and tunneling_request.cemi.code is CEMIMessageCode.L_DATA_IND
        ):
            telegram = tunneling_request.cemi.telegram
            telegram.direction = TelegramDirection.INCOMING
            if self.telegram_received_callback is not None:
                self.telegram_received_callback(telegram)

    def _send_tunnelling_ack(self, communication_channel_id, sequence_counter):
        """Send tunnelling ACK after tunnelling request received."""
        ack = TunnellingAck(
            self.xknx,
            communication_channel_id=communication_channel_id,
            sequence_counter=sequence_counter,
        )
        self.udp_client.send(KNXIPFrame.init_from_body(ack))

    def _disconnect_request_received(self, disconnect_request: DisconnectRequest):
        """Handle incoming disconnect request."""
        logger.warning("Received DisconnectRequest from tunnelling sever.")
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

    def start_heartbeat(self):
        """Start heartbeat for monitoring state of tunnel, as suggested by 03.08.02 KNX Core 5.4."""
        self._heartbeat_task = asyncio.create_task(self.do_heartbeat())

    def stop_heartbeat(self):
        """Stop heartbeat task if running."""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def do_heartbeat(self):
        """Heartbeat: Worker task, endless loop for sending heartbeat requests."""
        while True:
            await asyncio.sleep(HEARTBEAT_RATE)
            if not await self._connectionstate_request():
                await self._do_heartbeat_failed()

    async def _do_heartbeat_failed(self):
        """Heartbeat: handling error."""
        # first heartbeat failed - try 3 more times before disconnecting.
        for _heartbeats_failed in range(3):
            if await self._connectionstate_request():
                return
        # 3 retries failed
        logger.warning("Heartbeat to KNX bus failed. Reconnecting.")
        self._tunnel_lost()
