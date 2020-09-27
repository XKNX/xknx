"""
Abstraction for handling KNX/IP tunnels.

Tunnels connect to KNX/IP devices directly via UDP and build a static UDP connection.
"""
import asyncio
import logging

from xknx.exceptions import CommunicationError, XKNXException
from xknx.knxip import (
    CEMIMessageCode,
    KNXIPFrame,
    KNXIPServiceType,
    TunnellingAck,
    TunnellingRequest,
)
from xknx.telegram import PhysicalAddress, TelegramDirection

from .connect import Connect
from .connectionstate import ConnectionState
from .disconnect import Disconnect
from .tunnelling import Tunnelling
from .udp_client import UDPClient

logger = logging.getLogger("xknx.log")


class Tunnel:
    """Class for handling KNX/IP tunnels."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        xknx,
        local_ip,
        gateway_ip,
        gateway_port,
        telegram_received_callback=None,
        auto_reconnect=False,
        auto_reconnect_wait=3,
    ):
        """Initialize Tunnel class."""
        # pylint: disable=too-many-arguments
        self.xknx = xknx
        self.local_ip = local_ip
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
            self.xknx, (self.local_ip, 0), (self.gateway_ip, self.gateway_port)
        )

        self.udp_client.register_callback(
            self.tunnel_reqest_received, [TunnellingRequest.service_type]
        )

    def tunnel_reqest_received(self, knxipframe, udp_client):
        """Handle incoming tunnel request."""
        # pylint: disable=unused-argument
        if knxipframe.header.service_type_ident != KNXIPServiceType.TUNNELLING_REQUEST:
            logger.warning("Service not implemented: %s", knxipframe)
        else:
            self.send_ack(
                knxipframe.body.communication_channel_id,
                knxipframe.body.sequence_counter,
            )
            # Don't handle invalid cemi frames (None) and only handle incoming L_DATA_IND frames.
            # Ignore L_DATA_CON confirmation frames. L_DATA_REQ frames should only be outgoing.
            if (
                knxipframe.body.cemi is not None
                and knxipframe.body.cemi.code is CEMIMessageCode.L_DATA_IND
            ):
                telegram = knxipframe.body.cemi.telegram
                telegram.direction = TelegramDirection.INCOMING
                if self.telegram_received_callback is not None:
                    self.telegram_received_callback(telegram)

    def send_ack(self, communication_channel_id, sequence_counter):
        """Send tunnelling ACK after tunnelling request received."""
        ack = TunnellingAck(
            self.xknx,
            communication_channel_id=communication_channel_id,
            sequence_counter=sequence_counter,
        )
        self.udp_client.send(KNXIPFrame.init_from_body(ack))

    async def start(self):
        """Start tunneling."""
        await self.connect_udp()
        await self.connect()

    async def connect_udp(self):
        """Connect udp_client."""
        await self.udp_client.connect()

    async def connect(self):
        """Connect/build tunnel."""
        connect = Connect(self.xknx, self.udp_client)
        await connect.start()
        if not connect.success:
            if self.auto_reconnect:
                logger.warning(
                    "Could not connect to KNX. Retry in %s seconds.",
                    self.auto_reconnect_wait,
                )
                self._reconnect_task = asyncio.create_task(self.schedule_reconnect())
                return
            raise CommunicationError(
                "Could not establish connection", not self._is_reconnecting
            )
        logger.debug(
            "Tunnel established communication_channel=%s, id=%s",
            connect.communication_channel,
            connect.identifier,
        )
        if self._is_reconnecting:
            logger.info("Successfully reconnected to KNX bus.")
        self._reconnect_task = None
        self._is_reconnecting = False
        self.communication_channel = connect.communication_channel
        # Use the individual address provided by the tunnelling server
        self._src_address = PhysicalAddress(connect.identifier)
        self.sequence_number = 0
        await self.start_heartbeat()

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
        success = await self._send_telegram_impl(telegram)
        if not success:
            logger.debug("Sending of telegram failed. Retrying a second time.")
            success = await self._send_telegram_impl(telegram)
            if not success:
                logger.debug("Resending telegram failed. Reconnecting to tunnel.")
                await self.reconnect()
                success = await self._send_telegram_impl(telegram)
                if not success:
                    raise CommunicationError(
                        "Resending the telegram repeatedly failed.", False
                    )
        self.increase_sequence_number()

    async def _send_telegram_impl(self, telegram):
        """Send Telegram to tunnelling device - implementation."""
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

    def increase_sequence_number(self):
        """Increase sequence number."""
        self.sequence_number += 1
        if self.sequence_number == 256:
            self.sequence_number = 0

    async def connectionstate(self):
        """Return state of tunnel. True if tunnel is in good shape."""
        conn_state = ConnectionState(
            self.xknx,
            self.udp_client,
            communication_channel_id=self.communication_channel,
        )
        await conn_state.start()
        return conn_state.success

    async def disconnect(self, ignore_error=False):
        """Disconnect from tunnel device."""
        # only send disconnect request if we ever were connected
        if self.communication_channel is None:
            # close udp client to prevent open file descriptors
            await self.udp_client.stop()
            return
        disconnect = Disconnect(
            self.xknx,
            self.udp_client,
            communication_channel_id=self.communication_channel,
        )
        await disconnect.start()
        if not disconnect.success and not ignore_error:
            raise XKNXException("Could not disconnect channel")
        logger.debug(
            "Tunnel disconnected (communication_channel: %s)",
            self.communication_channel,
        )
        # close udp client to prevent open file descriptors
        await self.udp_client.stop()

    async def reconnect(self):
        """Reconnect to tunnel device."""
        self._is_reconnecting = True
        await self.stop_heartbeat()
        await self.disconnect(True)
        self.init_udp_client()
        await self.start()

    async def schedule_reconnect(self):
        """Schedule reconnect to KNX."""
        await asyncio.sleep(self.auto_reconnect_wait)
        await self.reconnect()

    async def stop_reconnect(self):
        """Stop reconnect task if running."""
        if self._reconnect_task is not None:
            self._reconnect_task.cancel()
            self._reconnect_task = None

    async def stop(self):
        """Stop tunneling."""
        # XXX: set disconnect ignore_error True here. Is there actually anything
        #      which can happen if disconnect fails? normally this fails because
        #      we have no connection...
        # await self.disconnect()
        await self.stop_heartbeat()
        await self.stop_reconnect()
        await self.disconnect(True)

    async def start_heartbeat(self):
        """Start heartbeat for monitoring state of tunnel, as suggested by 03.08.02 KNX Core 5.4."""
        self._heartbeat_task = asyncio.create_task(self.do_heartbeat())

    async def stop_heartbeat(self):
        """Stop heartbeat task if running."""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def do_heartbeat(self):
        """Heartbeat: Worker 'thread', endless loop for sending heartbeat requests."""
        while True:
            await asyncio.sleep(15)
            await self.do_heartbeat_impl()

    async def do_heartbeat_impl(self):
        """Heartbeat: checking connection state and handling result."""
        connectionsstate = await self.connectionstate()
        if connectionsstate:
            await self.do_heartbeat_success()
        else:
            await self.do_heartbeat_failed()

    async def do_heartbeat_success(self):
        """Heartbeat: handling success."""
        self.number_heartbeat_failed = 0

    async def do_heartbeat_failed(self):
        """Heartbeat: handling error."""
        self.number_heartbeat_failed = self.number_heartbeat_failed + 1
        if self.number_heartbeat_failed > 3:
            if not self._is_reconnecting:
                logger.warning("Heartbeat to KNX bus failed. Reconnecting.")
            try:
                await self.stop_reconnect()
                await self.reconnect()
                self.number_heartbeat_failed = 0
                await self.stop_heartbeat()
            except CommunicationError as exc:
                if exc.should_log:
                    logger.warning(exc)
