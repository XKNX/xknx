import asyncio
from xknx import XKNX
from xknx.io import GatewayScanner

async def main():
    xknx = XKNX()
    gatewayscanner = GatewayScanner(xknx)
    await gatewayscanner.start()

    if not gatewayscanner.found:
        print("No Gateways found")

    else:
        print("Gateway found: {0} / {1}:{2}".format(
            gatewayscanner.found_name,
            gatewayscanner.found_ip_addr,
            gatewayscanner.found_port))
        if gatewayscanner.supports_tunneling:
            print("- Device supports tunneling")
        if gatewayscanner.supports_routing:
            print("- Device supports routing, connecting via {0}".format(
                gatewayscanner.found_local_ip))

    await gatewayscanner.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
