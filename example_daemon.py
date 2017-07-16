#!/usr/bin/python3

from xknx import XKNX,Config
import time

def device_updated_callback( xknx, device):

    print("Callback received from {0}".format(device.name))

    if (device.name == "Livingroom.Switch_1" ):
        if device.is_on():
            xknx.devices["Livingroom.Outlet_1"].set_on()
        elif device.is_off():
            xknx.devices["Livingroom.Outlet_1"].set_off()

xknx = XKNX(config = "/path/tox/xknx.yaml")

xknx.start( daemon_mode=True, device_updated_callback=device_updated_callback )

