import asyncio
from .gateway_scanner import GatewayScanner

from .routing import Routing
from .tunnel import Tunnel


class KNXIPInterface():

    def __init__(self, xknx):
        self.xknx = xknx
        self.interface = None


    @asyncio.coroutine
    def start(self):
        gatewayscanner = GatewayScanner(self.xknx)
        yield from gatewayscanner.async_start()
        gatewayscanner.stop()

        if not gatewayscanner.found:
            raise Exception("No Gateways found")

        print("Connecting to {}:{} from {}".format(
            gatewayscanner.found_ip_addr,
            gatewayscanner.found_port,
            gatewayscanner.found_local_ip))

        self.interface = Tunnel(
            self.xknx,
            self.xknx.globals.own_address,
            local_ip=gatewayscanner.found_local_ip,
            gateway_ip=gatewayscanner.found_ip_addr,
            gateway_port=gatewayscanner.found_port,
            telegram_received_callback=self.telegram_received)
        yield from self.interface.start()

        #self.interface = Routing(
        #    self.xknx,
        #    self.telegram_received,
        #    gatewayscanner.found_local_ip)
        #yield from self.interface.start()


    @asyncio.coroutine
    def async_stop(self):
        if self.interface is not None:
            yield from self.interface.async_stop()
            self.interface = None

    def telegram_received(self, telegram):
        self.xknx.loop.create_task(
            self.xknx.telegrams.put(telegram))


    @asyncio.coroutine
    def send_telegram(self, telegram):
        yield from self.interface.send_telegram(telegram)
