from xknx import XKNX
from xknx.io.async import KNXIPDisconnect

xknx = XKNX()

knxipdisconnect= KNXIPDisconnect(
    xknx,
    own_ip="192.168.42.1",
    gateway_ip="192.168.42.10",
    gateway_port=3671,
    communication_channel_id=1)

knxipdisconnect.disconnect()
