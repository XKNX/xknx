import asyncio
from xknx import XKNX
from xknx.io.async import Connect, ConnectionState, Disconnect, Tunnelling, UDPClient
from xknx.knx import Telegram, Address, DPTBinary


def build_and_destroy_tunnel(xknx):

    own_ip="192.168.42.1"
    gateway_ip="192.168.42.10"
    gateway_port=3671

    udp_client = UDPClient(xknx)

    yield from udp_client.connect(
             own_ip,
             (gateway_ip, gateway_port),
            multicast=False)

    connect = Connect(
        xknx,
        udp_client)
    yield from connect.async_start()

    if not connect.success:
        raise Exception("Could not establish connection")

    print("Tunnel established communication_channel={0}, id={1}".format(
        connect.communication_channel, connect.identifier))

    #----------------------

    conn_state = ConnectionState(
        xknx,
        udp_client,
        communication_channel_id=connect.communication_channel)

    yield from conn_state.async_start()

    if not conn_state.success:
        raise Exception("Could not get connection state of connection")

    print("Communication state channel ",  connect.communication_channel)

    #---------------------

    sequence_number = 0

    tunnelling = Tunnelling(
        xknx,
        udp_client,
        Telegram(Address('1/0/15'), payload=DPTBinary(0)),
        Address("15.15.249"),
        sequence_number)

    yield from tunnelling.async_start()

    if not tunnelling.success:
        #raise Exception("Could not send telegram to tunnel")
        print("Did not receive ack")


    #---------------------

    disconnect = Disconnect(
        xknx,
        udp_client,
        communication_channel_id=connect.communication_channel)

    yield from disconnect.async_start()

    if not disconnect.success:
        raise Exception("Could not disconnect channel")

    print("Disconnected ", connect.communication_channel)


xknx = XKNX()

task = asyncio.Task(
    build_and_destroy_tunnel(xknx))
xknx.loop.run_until_complete(task)

