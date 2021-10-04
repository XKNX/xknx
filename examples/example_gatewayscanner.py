"""Example for GatewayScanner."""
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
            print(f"Gateway found: {gateway.name} at {gateway.ip_addr}:{gateway.port}")
            if gateway.supports_tunnelling:
                print("- Device supports tunneling")
            if gateway.supports_routing:
                print(f"- Device supports routing, connecting via {gateway.local_ip}")


asyncio.run(main())
