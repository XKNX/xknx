"""Example on how to connecto to a KNX/IP tunneling device."""
import asyncio

from xknx import XKNX
from xknx.io import GatewayScanner, Tunnel
from xknx.knx import GroupAddress, PhysicalAddress, DPTBinary, Telegram


async def main():
    """Connect to a tunnel, send 2 telegrams and disconnect."""
    xknx = XKNX()
    gatewayscanner = GatewayScanner(xknx)
    await gatewayscanner.start()

    if not gatewayscanner.found:
        print("No Gateways found")
        return

    src_address = PhysicalAddress("15.15.249")

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

    await tunnel.send_telegram(Telegram(GroupAddress('1/0/15'), payload=DPTBinary(1)))
    await asyncio.sleep(2)
    await tunnel.send_telegram(Telegram(GroupAddress('1/0/15'), payload=DPTBinary(0)))
    await asyncio.sleep(2)

    await tunnel.connectionstate()
    await tunnel.disconnect()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
