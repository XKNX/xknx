"""Example for GatewayScanner."""

import asyncio

from xknx import XKNX
from xknx.io import GatewayScanner


async def main() -> None:
    """Search for available KNX/IP devices with GatewayScanner and print out result if a device was found."""
    xknx = XKNX()
    gatewayscanner = GatewayScanner(xknx)

    async for gateway in gatewayscanner.async_scan():
        print(f"{gateway.name}")
        print(f"  {'Individual address:':<19} {gateway.individual_address}")
        print(f"  {'IP:':<19} {gateway.ip_addr}:{gateway.port}")
        print(f"  {'Serial number:':<19} {gateway.serial_number}")
        print(f"  {'MAC address:':<19} {gateway.mac_address}")
        print(
            f"  {'Supports secure:':<19} {'Yes' if gateway.supports_secure else 'No'}"
        )
        tunnelling = (
            "Secure"
            if gateway.tunnelling_requires_secure
            else "TCP"
            if gateway.supports_tunnelling_tcp
            else "UDP"
            if gateway.supports_tunnelling
            else "Not supported"
        )
        print(f"  {'Tunnelling:':<19} {tunnelling}")
        routing = (
            "Secure"
            if gateway.routing_requires_secure
            else "Plain"
            if gateway.supports_routing
            else "Not supported"
        )
        print(f"  {'Routing:':<19} {routing}")
        if gateway.supports_routing:
            print(f"  {'Multicast group:':<19} {gateway.multicast_address}")
        print()

    if not gatewayscanner.found_gateways:
        print("No Gateways found")


asyncio.run(main())
