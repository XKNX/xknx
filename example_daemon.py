#!/usr/bin/python3

from xknx import XKNX,CouldNotResolveAddress,Config
import time

def telegram_received_callback( xknx, device, telegram):

    print("Callback received from {0}".format(device.name))

    try:

        if (device.name == "Livingroom.Switch_1" ):
            if device.is_on():
                xknx.devices.device_by_name("Livingroom.Outlet_1").set_on()
            elif device.is_off():
                xknx.devices.device_by_name("Livingroom.Outlet_1").set_off()

    except CouldNotResolveAddress as c:
        print(c)

xknx = XKNX()

Config(xknx).read()

xknx.start( True, telegram_received_callback = telegram_received_callback )

