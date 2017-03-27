import asyncio
from xknx import XKNX
from xknx.io.async import Tunnel, GatewayScanner
from xknx.knx import Telegram, Address, DPTBinary


@asyncio.coroutine
def build_and_destroy_tunnel(xknx):

    gatewayscanner = GatewayScanner(xknx)
    yield from gatewayscanner.async_start()

    if not gatewayscanner.found:
        print("No Gateways found")
        return

    src_address = Address("15.15.249")

    print("Connecting to {}:{} from {}".format(
        gatewayscanner.found_ip_addr,
        gatewayscanner.found_port,
        gatewayscanner.found_local_ip))

    tunnel = Tunnel(
        xknx,
        src_address,
        local_ip=gatewayscanner.found_local_ip,
        gateway_ip=gatewayscanner.found_ip_addr,
        gateway_port=gatewayscanner.found_port)

    yield from tunnel.connect_udp()
    yield from tunnel.connect()

    yield from tunnel.send_telegram(Telegram(Address('1/0/15'), payload=DPTBinary(0)))
    yield from asyncio.sleep(2)
    yield from tunnel.send_telegram(Telegram(Address('1/0/15'), payload=DPTBinary(1)))
    yield from asyncio.sleep(2)

    yield from tunnel.connectionstate()
    yield from tunnel.disconnect()


xknx = XKNX(start=False)
task = asyncio.Task(build_and_destroy_tunnel(xknx))
xknx.loop.run_until_complete(task)

