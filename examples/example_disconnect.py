"""Example on how to disconnect/reset all available tunneling channels."""
import asyncio
from xknx import XKNX
from xknx.io import GatewayScanner, UDPClient, Disconnect, ConnectionState

async def main():
    """Search for a Tunelling device, walk through all possible channels and disconnect them."""
    xknx = XKNX()
    gatewayscanner = GatewayScanner(xknx)
    await gatewayscanner.start()

    if not gatewayscanner.found:
        print("No Gateways found")
        return

    if not gatewayscanner.supports_tunneling:
        print("Gateway does not support tunneling")
        return

    udp_client = UDPClient(
        xknx,
        (gatewayscanner.found_local_ip, 0),
        (gatewayscanner.found_ip_addr, gatewayscanner.found_port))

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
