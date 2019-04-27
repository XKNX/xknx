"""Example on how to disconnect/reset all available tunneling channels."""
import asyncio

from xknx import XKNX
from xknx.io import ConnectionState, Disconnect, GatewayScanner, UDPClient


async def main():
    """Search for a Tunnelling device, walk through all possible channels and disconnect them."""
    xknx = XKNX()
    gatewayscanner = GatewayScanner(xknx)
    gateways = await gatewayscanner.scan()

    if not gateways:
        print("No Gateways found")
        return

    gateway = gateways[0]

    if not gateway.supports_tunnelling:
        print("Gateway does not support tunneling")
        return

    udp_client = UDPClient(
        xknx,
        (gateway.local_ip, 0),
        (gateway.ip_addr, gateway.port))

    await udp_client.connect()

    for i in range(0, 255):

        conn_state = ConnectionState(
            xknx,
            udp_client,
            communication_channel_id=i)

        await conn_state.start()

        if conn_state.success:
            print("Disconnecting ", i)
            disconnect = Disconnect(
                xknx,
                udp_client,
                communication_channel_id=i)

            await disconnect.start()

            if disconnect.success:
                print("Disconnected ", i)

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
