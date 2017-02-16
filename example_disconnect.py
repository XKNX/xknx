from xknx import XKNX
from xknx.io.async import KNXIPDisconnect

xknx = XKNX()


for i in range(0,255):

    knxipdisconnect= KNXIPDisconnect(
        xknx,
        own_ip="192.168.42.1",
        gateway_ip="192.168.42.10",
        gateway_port=3671,
        communication_channel_id=i)

    knxipdisconnect.disconnect()
