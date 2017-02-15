import asyncio
from xknx.knx import TelegramDirection
from xknx.knxip import KNXIPFrame, KNXIPServiceType, APCICommand
from .udp_client import UDPClient
from .udp_server import UDPServer
from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT


class KNXIPInterface():

    def __init__(self, xknx):
        self.xknx = xknx
        self.udp_server = None


    def response_rec_callback(self, knxipframe):
        #print(knxipframe)
        if knxipframe.header.service_type_ident == \
                KNXIPServiceType.ROUTING_INDICATION:
            self.handle_frame_routing_indication(knxipframe)
        else:
            print("SERVICE TYPE NOT IMPLEMENETED: ", knxipframe)


    def handle_frame_routing_indication(self, knxipframe):
        if knxipframe.body.src_addr == self.xknx.globals.own_address:
            # Ignoring own KNXIPFrame
            pass
        elif knxipframe.body.cmd not in [APCICommand.GROUP_READ,
                                         APCICommand.GROUP_WRITE,
                                         APCICommand.GROUP_RESPONSE]:
            print("APCI NOT IMPLEMENETED: ", knxipframe)

        else:
            telegram = knxipframe.body.telegram
            telegram.direction = TelegramDirection.INCOMING
            self.xknx.loop.create_task(
                self.xknx.telegrams.put(telegram))


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
        udpclient = UDPClient(self.xknx)
        yield from udpclient.connect(
            self.xknx.globals.own_ip,
            (DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
            multicast=True,
            local_port=DEFAULT_MCAST_PORT)
        udpclient.send(knxipframe)
        yield from udpclient.stop()


    @asyncio.coroutine
    def start(self):
        self.udp_server = UDPServer(
            self.xknx,
            own_ip=self.xknx.globals.own_ip,
            multicast=True)
        self.udp_server.register_callback(
            self.response_rec_callback,
            [KNXIPServiceType.ROUTING_INDICATION])
        yield from self.udp_server.start()
