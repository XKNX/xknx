"""Example on how to disconnect/reset all available tunneling channels."""
import asyncio

from xknx import XKNX
from xknx.io import GatewayScanner
from xknx.io.request_response import ConnectionState, Disconnect
from xknx.io.transport import UDPTransport
from xknx.knxip import HPAI


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

    udp_transport = UDPTransport((gateway.local_ip, 0), (gateway.ip_addr, gateway.port))

    await udp_transport.connect()
    local_hpai = HPAI(*udp_transport.getsockname())

    for i in range(255):
        conn_state = ConnectionState(
            udp_transport, communication_channel_id=i, local_hpai=local_hpai
        )

        await conn_state.start()

        if conn_state.success:
            print("Disconnecting ", i)
            disconnect = Disconnect(
                udp_transport, communication_channel_id=i, local_hpai=local_hpai
            )

            await disconnect.start()

            if disconnect.success:
                print("Disconnected ", i)


asyncio.run(main())
