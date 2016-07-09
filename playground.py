#!/usr/bin/python3

from xknx import Multicast,Devices,devices_,CouldNotResolveAddress,Config
import time

def callback( telegram):

    try:
        device = devices_.device_by_group_address(telegram.group_address)

        device.process(telegram)

        if (device.name == "Livingroom.Switch_1" ):
            if device.is_on():
                devices_.device_by_name("Livingroom.Shutter_1").set_down()
                devices_.device_by_name("Livingroom.Outlet_1").set_on()
            elif device.is_off():
                devices_.device_by_name("Livingroom.Shutter_1").set_up()
                devices_.device_by_name("Livingroom.Outlet_1").set_off()

        if (device.name == "Livingroom.Switch_2" ):
            if device.is_on():
                devices_.device_by_name("Livingroom.Shutter_1").set_short_down()
                devices_.device_by_name("Livingroom.Outlet_2").set_on()
            elif device.is_off():
                devices_.device_by_name("Livingroom.Shutter_1").set_short_up()
                devices_.device_by_name("Livingroom.Outlet_2").set_off()

        if (device.name == "Livingroom.Switch_3" ):
            if device.is_on():
                devices_.device_by_name("Livingroom.Outlet_2/1").set_on()
                devices_.device_by_name("Livingroom.Outlet_2/2").set_on()
            elif device.is_off():
                devices_.device_by_name("Livingroom.Outlet_2/1").set_off()
                devices_.device_by_name("Livingroom.Outlet_2/2").set_off()

        if (device.name == "Livingroom.Switch_4" ):
            if device.is_on():
                devices_.device_by_name("Livingroom.Outlet_2/1").set_on()
                devices_.device_by_name("Livingroom.Outlet_2/2").set_on()
                devices_.device_by_name("Livingroom.Outlet_2/3").set_on()
                devices_.device_by_name("Livingroom.Outlet_2/4").set_on()
            elif device.is_off():
                devices_.device_by_name("Livingroom.Outlet_2/1").set_off()
                devices_.device_by_name("Livingroom.Outlet_2/2").set_off()
                devices_.device_by_name("Livingroom.Outlet_2/3").set_off()
                devices_.device_by_name("Livingroom.Outlet_2/4").set_off()

    except CouldNotResolveAddress as c:
        print(c)
        
Config.read()

#devices_.update_thread_start(20)

#devices = devices_.get_devices()
#for device in devices:
#    print(device)

#print("down");
#devices_.device_by_name("Livingroom.Shutter_1").set_down()
#time.sleep(2)
#print("up");
#devices_.device_by_name("Livingroom.Shutter_1").set_up()
#time.sleep(5)
#print("short down")
#devices_.device_by_name("Livingroom.Shutter_1").set_short_down()
#time.sleep(5)
#print("short up")
#devices_.device_by_name("Livingroom.Shutter_1").set_short_up()

Multicast().recv(callback)

