#!/usr/bin/python3

from xknx import Multicast,CouldNotResolveAddress,Config
import time

def callback( device, telegram):

    print("Callback received from {0}".format(device.name))

    try:

        if (device.name == "Livingroom.Switch_1" ):
            if device.is_on():
                devices_.device_by_name("Livingroom.Outlet_1").set_on()
            elif device.is_off():
                devices_.device_by_name("Livingroom.Outlet_1").set_off()

    except CouldNotResolveAddress as c:
        print(c)
        
Config.read()

Multicast().recv(callback)

