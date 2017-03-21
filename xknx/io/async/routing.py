import asyncio
from xknx.knx import TelegramDirection
from xknx.knxip import KNXIPFrame, KNXIPServiceType, APCICommand
from .udp_client import UDPClient
from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT


class Routing():

    def __init__(self, xknx, telegram_received_callback, local_ip):
        self.xknx = xknx
        self.telegram_received_callback = telegram_received_callback
        self.local_ip = local_ip

        self.udpclient = UDPClient(self.xknx,
            (local_ip, 0),
            (DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
            multicast=True, bind_to_multicast_addr=True)

        self.udpclient.register_callback(
            self.response_rec_callback,
            [KNXIPServiceType.ROUTING_INDICATION])


    def response_rec_callback(self, knxipframe, _):
        if knxipframe.body.src_addr == self.xknx.globals.own_address:
            print("Ignoring own packet")
        elif knxipframe.header.service_type_ident != \
                KNXIPServiceType.ROUTING_INDICATION:
            print("SERVICE TYPE NOT IMPLEMENETED: ", knxipframe)
        elif knxipframe.body.cmd not in [APCICommand.GROUP_READ,
                                         APCICommand.GROUP_WRITE,
                                         APCICommand.GROUP_RESPONSE]:
            print("APCI NOT IMPLEMENETED: ", knxipframe)
        else:
            telegram = knxipframe.body.telegram
            telegram.direction = TelegramDirection.INCOMING

            if self.telegram_received_callback is not None:
                self.telegram_received_callback(telegram)

    @asyncio.coroutine
    def send_telegram(self, telegram):
        knxipframe = KNXIPFrame()
        knxipframe.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe.body.src_addr = self.xknx.globals.own_address
        knxipframe.body.telegram = telegram
        knxipframe.body.sender = self.xknx.globals.own_address
        knxipframe.normalize()
        yield from self.send_knxipframe(knxipframe)


    @asyncio.coroutine
    def send_knxipframe(self, knxipframe):
        yield from self.interface.send_knxipframe(knxipframe)


    @asyncio.coroutine
    def send_knxipframe(self, knxipframe):
        self.udpclient.send(knxipframe)


    @asyncio.coroutine
    def start(self):
        yield from self.udpclient.connect()


    @asyncio.coroutine
    def async_stop(self):
        yield from self.udpclient.stop()
