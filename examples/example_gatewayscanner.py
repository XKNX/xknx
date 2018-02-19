"""Example for GateayScanner."""
import asyncio

from xknx import XKNX
from xknx.io import GatewayScanner


async def main():
    """Search for available KNX/IP devices with GatewayScanner and print out result if a device was found."""
    xknx = XKNX()
    gatewayscanner = GatewayScanner(xknx)
    gateways = await gatewayscanner.scan()

    if not gateways:
        print("No Gateways found")

    else:
        for gateway in gateways:
            print("Gateway found: {0} / {1}:{2}".format(
                gateway.name,
                gateway.ip_addr,
                gateway.port))
            if gateway.supports_tunnelling:
                print("- Device supports tunneling")
            if gateway.supports_routing:
                print("- Device supports routing, connecting via {0}".format(
                    gateway.local_ip))

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
