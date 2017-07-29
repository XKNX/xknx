"""
Abstraction for handling KNX/IP tunnels.

Tunnels connect to KNX/IP devices directly via UDP and build a static UDP connection.
"""
import asyncio
from xknx.knx import TelegramDirection
from xknx.knxip import TunnellingRequest, KNXIPFrame, KNXIPServiceType
from .disconnect import Disconnect
from .connectionstate import ConnectionState
from .connect import Connect
from .tunnelling import Tunnelling
from .udp_client import UDPClient

class Tunnel():
    """Class for handling KNX/IP tunnels."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, xknx, src_address, local_ip, gateway_ip, gateway_port, telegram_received_callback=None):
        """Initialize Tunnel class."""
        # pylint: disable=too-many-arguments
        self.xknx = xknx
        self.src_address = src_address
        self.local_ip = local_ip
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.telegram_received_callback = telegram_received_callback

        self.udp_client = None
        self.init_udp_client()

        self.sequence_number = 0
        self.communication_channel = None
        self.number_heartbeat_failed = 0

    def init_udp_client(self):
        """Initialize udp_client."""
        self.udp_client = UDPClient(self.xknx,
                                    (self.local_ip, 0),
                                    (self.gateway_ip, self.gateway_port))

        self.udp_client.register_callback(
            self.tunnel_reqest_received, [TunnellingRequest.service_type])


    def tunnel_reqest_received(self, knxipframe, udp_client):
        """Callback for tunnel request received."""
        # pylint: disable=unused-argument
        if knxipframe.header.service_type_ident != \
                KNXIPServiceType.TUNNELLING_REQUEST:
            print("SERVICE TYPE NOT IMPLEMENETED: ", knxipframe)
        else:
            self.send_ack(knxipframe.body.communication_channel_id, knxipframe.body.sequence_counter)
            telegram = knxipframe.body.cemi.telegram
            telegram.direction = TelegramDirection.INCOMING
            if self.telegram_received_callback is not None:
                self.telegram_received_callback(telegram)

    def send_ack(self, communication_channel_id, sequence_counter):
        """Send tunneling ACK after tunneling request received."""
        ack_knxipframe = KNXIPFrame()
        ack_knxipframe.init(KNXIPServiceType.TUNNELLING_ACK)
        ack_knxipframe.body.communication_channel_id = communication_channel_id
        ack_knxipframe.body.sequence_counter = sequence_counter
        ack_knxipframe.normalize()
        self.udp_client.send(ack_knxipframe)

    @asyncio.coroutine
    def start(self):
        """Start tunneling."""
        yield from self.connect_udp()
        yield from self.connect()

    @asyncio.coroutine
    def connect_udp(self):
        """Connect udp_client."""
        yield from self.udp_client.connect()


    @asyncio.coroutine
    def connect(self):
        """Connect/build tunnel."""
        connect = Connect(
            self.xknx,
            self.udp_client)
        yield from connect.start()
        if not connect.success:
            raise Exception("Could not establish connection")
        print("Tunnel established communication_channel={0}, id={1}".format(
            connect.communication_channel, connect.identifier))
        self.communication_channel = connect.communication_channel
        self.sequence_number = 0
        yield from self.start_heartbeat()

    @asyncio.coroutine
    def send_telegram(self, telegram):
        """Send Telegram to routing tunelling device."""
        tunnelling = Tunnelling(
            self.xknx,
            self.udp_client,
            telegram,
            self.src_address,
            self.sequence_number,
            self.communication_channel)
        self.sequence_number += 1
        if self.sequence_number == 256:
            self.sequence_number = 0
        yield from tunnelling.start()
        if not tunnelling.success:
            raise Exception("Could not send telegram to tunnel")

    @asyncio.coroutine
    def connectionstate(self):
        """Return state of tunnel. True if tunnel is in good shape."""
        conn_state = ConnectionState(
            self.xknx,
            self.udp_client,
            communication_channel_id=self.communication_channel)
        yield from conn_state.start()
        return conn_state.success

    @asyncio.coroutine
    def disconnect(self, ignore_error=False):
        """Disconnect from tunnel device."""
        disconnect = Disconnect(
            self.xknx,
            self.udp_client,
            communication_channel_id=self.communication_channel)
        yield from disconnect.start()
        if not disconnect.success and not ignore_error:
            raise Exception("Could not disconnect channel")
        else:
            print("Tunnel disconnected (communication_channel: {0})".format(self.communication_channel))

    @asyncio.coroutine
    def stop(self):
        """Stop tunneling."""
        yield from self.disconnect()
        yield from self.udp_client.stop()

    @asyncio.coroutine
    def start_heartbeat(self):
        """Start heartbeat for monitoring state of tunnel, as suggested by 03.08.02 KNX Core 5.4."""
        self.xknx.loop.create_task(
            self.do_heartbeat())

    @asyncio.coroutine
    def do_heartbeat(self):
        """Heartbeat: Worker 'thread', endless loop for sending heartbeat requests."""
        while True:
            yield from asyncio.sleep(15)
            yield from self.do_heartbeat_impl()

    @asyncio.coroutine
    def do_heartbeat_impl(self):
        """Heartbeat: checking connection state and handling result."""
        connectionsstate = yield from self.connectionstate()
        if connectionsstate:
            yield from self.do_heartbeat_success()
        else:
            yield from self.do_heartbeat_failed()

    @asyncio.coroutine
    def do_heartbeat_success(self):
        """Heartbeat: handling success."""
        self.number_heartbeat_failed = 0

    @asyncio.coroutine
    def do_heartbeat_failed(self):
        """Heartbeat: handling error."""
        self.number_heartbeat_failed = self.number_heartbeat_failed + 1
        if self.number_heartbeat_failed > 3:
            print("HEARTBEAT FAILED - RECONNECTING")
            yield from self.disconnect(True)
            self.init_udp_client()
            yield from self.start()
            self.number_heartbeat_failed = 0
