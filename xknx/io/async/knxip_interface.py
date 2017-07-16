import asyncio
from enum import Enum
from .gateway_scanner import GatewayScanner

from .routing import Routing
from .tunnel import Tunnel

class ConnectionType(Enum):
    AUTOMATIC = 0
    TUNNEL = 1
    ROUTING = 2


class ConnectionConfig:
    # pylint: disable=too-few-public-methods
    def __init__(self,
                 connection_type=ConnectionType.AUTOMATIC,
                 local_ip=None,
                 gateway_ip=None,
                 gateway_port=3671):
        self.connection_type = connection_type
        self.local_ip = local_ip
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port



class KNXIPInterface():

    def __init__(self, xknx, connection_config=ConnectionConfig()):
        self.xknx = xknx
        self.interface = None
        self.connection_config = connection_config

    @asyncio.coroutine
    def start(self):
        if self.connection_config.connection_type == ConnectionType.AUTOMATIC:
            yield from self.start_automatic()
        elif self.connection_config.connection_type == ConnectionType.ROUTING:
            yield from self.start_routing(
                self.connection_config.local_ip)
        elif self.connection_config.connection_type == ConnectionType.TUNNEL:
            yield from self.start_tunnelling(
                self.connection_config.local_ip,
                self.connection_config.gateway_ip,
                self.connection_config.gateway_port)

    @asyncio.coroutine
    def start_automatic(self):
        gatewayscanner = GatewayScanner(self.xknx)
        yield from gatewayscanner.async_start()
        gatewayscanner.stop()

        if not gatewayscanner.found:
            raise Exception("No Gateways found")

        if gatewayscanner.supports_tunneling:
            yield from self.start_tunnelling(gatewayscanner.found_local_ip,
                                             gatewayscanner.found_ip_addr,
                                             gatewayscanner.found_port)

        elif gatewayscanner.supports_routing:
            yield from self.start_routing(gatewayscanner.found_local_ip)


    @asyncio.coroutine
    def start_tunnelling(self, local_ip, gateway_ip, gateway_port):
        print("Starting tunnel to {}:{} from {}".format(
            gateway_ip,
            gateway_port,
            local_ip))
        self.interface = Tunnel(
            self.xknx,
            self.xknx.globals.own_address,
            local_ip=local_ip,
            gateway_ip=gateway_ip,
            gateway_port=gateway_port,
            telegram_received_callback=self.telegram_received)
        yield from self.interface.start()

    @asyncio.coroutine
    def start_routing(self, local_ip):
        print("Starting Routing from {}".format(local_ip))
        self.interface = Routing(
            self.xknx,
            self.telegram_received,
            local_ip)
        yield from self.interface.start()


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
