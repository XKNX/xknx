import asyncio
from xknx import XKNX
from xknx.io import Tunnel, GatewayScanner
from xknx.knx import Telegram, Address, DPTBinary


async def main():
    xknx = XKNX()
    gatewayscanner = GatewayScanner(xknx)
    await gatewayscanner.start()

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

    await tunnel.connect_udp()
    await tunnel.connect()

    await tunnel.send_telegram(Telegram(Address('1/0/15'), payload=DPTBinary(1)))
    await asyncio.sleep(2)
    await tunnel.send_telegram(Telegram(Address('1/0/15'), payload=DPTBinary(0)))
    await asyncio.sleep(2)

    await tunnel.connectionstate()
    await tunnel.disconnect()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
