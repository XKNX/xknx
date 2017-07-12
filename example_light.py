import time
from xknx import XKNX, Light

xknx = XKNX()

light = Light(xknx,
              name='TestLight',
              group_address_switch='1/0/9')
xknx.devices.add(light)

xknx.devices["TestLight"].set_on()
