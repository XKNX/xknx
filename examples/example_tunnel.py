"""Example on how to connecto to a KNX/IP tunneling device."""
import asyncio

from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.io import GatewayScanner, Tunnel
from xknx.telegram import GroupAddress, PhysicalAddress, Telegram


async def main():
    """Connect to a tunnel, send 2 telegrams and disconnect."""
    xknx = XKNX()
    gatewayscanner = GatewayScanner(xknx)
    gateways = await gatewayscanner.scan()

    if not gateways:
        print("No Gateways found")
        return

    gateway = gateways[0]
    src_address = PhysicalAddress("15.15.249")

    print("Connecting to {}:{} from {}".format(
        gateway.ip_addr,
        gateway.port,
        gateway.local_ip))

    tunnel = Tunnel(
        xknx,
        src_address,
        local_ip=gateway.local_ip,
        gateway_ip=gateway.ip_addr,
        gateway_port=gateway.port)

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
