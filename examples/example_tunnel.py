"""Example on how to connecto to a KNX/IP tunneling device."""
import asyncio

from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.io import GatewayScanner, Tunnel
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


async def main():
    """Connect to a tunnel, send 2 telegrams and disconnect."""
    xknx = XKNX()
    gatewayscanner = GatewayScanner(xknx)
    gateways = await gatewayscanner.scan()

    if not gateways:
        print("No Gateways found")
        return

    gateway = gateways[0]
    # an individual address will most likely be assigned by the tunnelling server
    xknx.own_address = IndividualAddress("15.15.249")

    print("Connecting to {gateway.ip_addr}:{gateway.port} from {gateway.local_ip}")

    tunnel = Tunnel(
        xknx,
        gateway_ip=gateway.ip_addr,
        gateway_port=gateway.port,
        local_ip=gateway.local_ip,
        local_port=0,
        route_back=False,
    )

    await tunnel.connect()

    await tunnel.send_telegram(
        Telegram(
            destination_address=GroupAddress("1/0/15"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
    )
    await asyncio.sleep(2)
    await tunnel.send_telegram(
        Telegram(
            destination_address=GroupAddress("1/0/15"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
    )
    await asyncio.sleep(2)

    await tunnel.disconnect()


asyncio.run(main())
