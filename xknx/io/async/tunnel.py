import asyncio
from xknx.knx import Telegram, Address, DPTBinary, TelegramDirection
from xknx.knxip import TunnellingRequest, KNXIPFrame, KNXIPServiceType
from .disconnect import Disconnect
from .connectionstate import ConnectionState
from .connect import Connect
from .tunnelling import Tunnelling
from .udp_client import UDPClient

class Tunnel():

    def __init__(self, xknx, src_address, local_ip, gateway_ip, gateway_port, telegram_received_callback=None):
        self.xknx = xknx
        self.src_address = src_address 
        self.local_ip = local_ip
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.telegram_received_callback = telegram_received_callback

        self.udp_client = UDPClient(self.xknx,
            (self.local_ip, 0),
            (self.gateway_ip, self.gateway_port))

        self.udp_client.register_callback(
            self.tunnel_reqest_received, [TunnellingRequest.service_type])

        self.sequence_number = 0
        self.communication_channel = None


    def tunnel_reqest_received(self, knxipframe, udp_client):
        if knxipframe.header.service_type_ident != \
                KNXIPServiceType.TUNNELLING_REQUEST:
            print("SERVICE TYPE NOT IMPLEMENETED: ", knxipframe)
        else:
            self.send_ack( knxipframe.body.communication_channel_id, knxipframe.body.sequence_counter )
            telegram = knxipframe.body.cemi.telegram
            telegram.direction = TelegramDirection.INCOMING
            if self.telegram_received_callback is not None:
                self.telegram_received_callback(telegram)


    def send_ack(self, communication_channel_id, sequence_counter):
        ack_knxipframe = KNXIPFrame()
        ack_knxipframe.init(KNXIPServiceType.TUNNELLING_ACK)
        ack_knxipframe.body.communication_channel_id = communication_channel_id  
        ack_knxipframe.body.sequence_counter = sequence_counter
        ack_knxipframe.normalize()
        self.udp_client.send(ack_knxipframe)

    @asyncio.coroutine
    def start(self):
        yield from self.connect_udp()
        yield from self.connect()


    @asyncio.coroutine
    def connect_udp(self):
        yield from self.udp_client.connect()


    @asyncio.coroutine
    def connect(self):
        connect = Connect(
            self.xknx,
            self.udp_client)
        yield from connect.async_start()
        if not connect.success:
            raise Exception("Could not establish connection")
        print("Tunnel established communication_channel={0}, id={1}".format(
            connect.communication_channel, connect.identifier))
        self.communication_channel = connect.communication_channel

    @asyncio.coroutine
    def send_telegram(self, telegram):
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
        yield from tunnelling.async_start()
        if not tunnelling.success:
            raise Exception("Could not send telegram to tunnel")


    @asyncio.coroutine
    def connectionstate(self):
        conn_state = ConnectionState(
            self.xknx,
            self.udp_client,
            communication_channel_id=self.communication_channel)
        yield from conn_state.async_start()
        if not conn_state.success:
            raise Exception("Could not get connection state of connection")


    @asyncio.coroutine
    def disconnect(self):
        disconnect = Disconnect(
            self.xknx,
            self.udp_client,
            communication_channel_id=self.communication_channel)
        yield from disconnect.async_start()
        if not disconnect.success:
            raise Exception("Could not disconnect channel")
        print("Tunnel disconnected (communication_channel: {0})".format(self.communication_channel))

    @asyncio.coroutine
    def async_stop(self):
        yield from self.disconnect()
        yield from self.udp_client.stop()
