#!/usr/bin/python3

from xknx import XKNX,Address, MulticastDaemon,TelegramProcessor,StateUpdater,Devices,CouldNotResolveAddress,Config
import time

def callback( xknx, device, telegram):

    try:
        if (device.name == "Livingroom.Switch_1" ):
            if device.is_on():
                xknx.devices.device_by_name("Livingroom.Shutter_1").set_down()
                xknx.devices.device_by_name("Livingroom.Outlet_1").set_on()
            elif device.is_off():
                xknx.devices.device_by_name("Livingroom.Shutter_1").set_up()
                xknx.devices.device_by_name("Livingroom.Outlet_1").set_off()

        if (device.name == "Livingroom.Switch_2" ):
            if device.is_on():
                xknx.devices.device_by_name("Livingroom.Shutter_1").set_short_down()
                xknx.devices.device_by_name("Livingroom.Outlet_2").set_on()
            elif device.is_off():
                xknx.devices.device_by_name("Livingroom.Shutter_1").set_short_up()
                xknx.devices.device_by_name("Livingroom.Outlet_2").set_off()

        if (device.name == "Livingroom.Switch_3" ):
            if device.is_on():
                xknx.devices.device_by_name("Livingroom.Outlet_2/1").set_on()
                xknx.devices.device_by_name("Livingroom.Outlet_2/2").set_on()
            elif device.is_off():
                xknx.devices.device_by_name("Livingroom.Outlet_2/1").set_off()
                xknx.devices.device_by_name("Livingroom.Outlet_2/2").set_off()

        if (device.name == "Livingroom.Switch_4" ):
            if device.is_on():
                xknx.devices.device_by_name("Livingroom.Outlet_2/1").set_on()
                xknx.devices.device_by_name("Livingroom.Outlet_2/2").set_on()
                xknx.devices.device_by_name("Livingroom.Outlet_2/3").set_on()
                xknx.devices.device_by_name("Livingroom.Outlet_2/4").set_on()
            elif device.is_off():
                xknx.devices.device_by_name("Livingroom.Outlet_2/1").set_off()
                xknx.devices.device_by_name("Livingroom.Outlet_2/2").set_off()
                xknx.devices.device_by_name("Livingroom.Outlet_2/3").set_off()
                xknx.devices.device_by_name("Livingroom.Outlet_2/4").set_off()

    except CouldNotResolveAddress as c:
        print(c)

xknx = XKNX()

Config(xknx).read()

#devices = xknx.devices.get_devices()
#for device in devices:
#    print(device)

#print("down");
#xknx.devices.device_by_name("Livingroom.Shutter_1").set_down()
#time.sleep(2)
#print("up");
#xknx.devices.device_by_name("Livingroom.Shutter_1").set_up()
#time.sleep(5)
#print("short down")
#xknx.devices.device_by_name("Livingroom.Shutter_1").set_short_down()
#time.sleep(5)
#print("short up")
#xknx.devices.device_by_name("Livingroom.Shutter_1").set_short_up()

TelegramProcessor.start(xknx)
MulticastDaemon.start(xknx, callback)
StateUpdater.start(xknx, 10)

while True:
	pass
