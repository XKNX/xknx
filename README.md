XKNX - A KNX library written in Python
================================================

A Wrapper around KNX/UDP protocol written in python.

The wrapper is also intended to be used as a KNX logic module, which means to connect different KNX devices and make them interact.

At the moment the wrapper works with KNX/IP routers.

See documentation at: [http://xknx.io/](http://xknx.io/)


Sample Program
--------------

Switching on an outlet:

```python
#!/usr/bin/python3

from xknx import XKNX,Config

xknx = XKNX()

Config(xknx).read()

xknx.start()
xknx.devices.device_by_name("Livingroom.Outlet_1").set_on()
xknx.join()
```

Starting a daemon receiving callbacks:

```python
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
```
Chat
----

We need your help for testing and improving XKNX. Please join the chat at: https://gitter.im/XKNX/Lobby

Roadmap
-------

* Add functionality for KNX tunneling devices
* Add functionality for auto discovery for KNX/IP router and tunneling devices
* Sending Time to KNX Bus
* Sending Outside temperature to KNX Bus

Home-Assistant Plugin
---------------------

XKNX also contains a [Plugin](home-assistant-plugin) for the [Home-Assistant](https://home-assistant.io/) automation plattform

Supported / Tested Devices
--------------------------

The software was tested with the following devices:

- [GIRA KNX/IP-Routers 216700](http://www.gira.com/en/gebaeudetechnik/systeme/knx-eib_system/knx-produkte/systemgeraete/knx-ip-router.html)
- [GIRA KNX/Switching Actor  104000](http://katalog.gira.de/de_DE/deeplinking.html?artikelnr=104000&m=compare)
- [GIRA KNX/Shutter Binary Actor 103800](https://katalog.gira.de/en/datenblatt.html?id=635678)
- [GIRA KNX/Binary Input 111900 ](https://www.gira.de/gebaeudetechnik/systeme/knx-eib_system/knx-produkte/tasterschnittstellen/knxeib-universal-tasterschnittstelle.html)
- [GIRA Tastsensor 3 Plus 2-fach 514200 ](https://katalog.gira.de/de_DE/datenblatt.html?id=635019)
	(This sensor is also used as Thermostat)
- [KNX Dimmaktor 4fach](https://katalog.gira.de/de_DE/datenblatt.html?id=658701)

Sample Configuration
--------------------

```yaml

general:
    own_address: "15.15.249"
    own_ip: "192.168.42.1"

groups:

    switch:

        Livingroom.Switch_1:
            group_address: "1/2/7"
            actions:
              - {hook: "on", target: Livingroom.Outlet_1, method: "on"}
              - {hook: "on", target: Livingroom.Outlet_2, method: "on"}

        Livingroom.Switch_2:
            group_address: "1/2/8"
            actions:
              - {hook: "on", target: Livingroom.Outlet_1, method: "off"}
              - {hook: "on", target: Livingroom.Outlet_2, method: "off"}


        Livingroom.Switch_3:
            group_address: "1/2/2"
            actions:
              - {hook: "off", switch_time: "short", target: Livingroom.Shutter_1, method: short_up}
              - {hook: "off", switch_time: "long", target: Livingroom.Shutter_1, method: up} # Pressing more then 2 seconds

        Livingroom.Switch_4:
            group_address: "1/2/3"
            actions:
              - {hook: "off", switch_time: "short", target: Livingroom.Shutter_1, method: short_down}
              - {hook: "off", switch_time: "long", target: Livingroom.Shutter_1, method: down} # Pressing more then 2 seconds

    outlet:

        Livingroom.Outlet_1: {group_address: "1/3/1"}
        Livingroom.Outlet_2: {group_address: "1/3/2"}

    outlet 2:

        Kitchen.Outlet_1: {group_address: "1/3/7"}
        Kitchen.Outlet_2: {group_address: "1/3/8"}
        Kitchen.Outlet_3: {group_address: "1/3/9"}
        Kitchen.Outlet_4: {group_address: "1/3/10"}

    shutter:

        Livingroom.Shutter_1: {group_address_long: "1/4/1", group_address_short: "1/4/2", group_address_position_feedback: "1/4/3", group_address_position: "1/4/4", travel_time_down: 50, travel_time_up: 60 }
        Livingroom.Shutter_2: {group_address_long: "1/4/5", group_address_short: "1/4/6", group_address_position_feedback: "1/4/7", group_address_position: "1/4/8", travel_time_down: 50, travel_time_up: 60 }

        # Shutters without direct positioning:
        Livingroom.Shutter_3: {group_address_long: "1/4/9", group_address_short: "1/4/10", group_address_position_feedback: "1/4/11", travel_time_down: 50, travel_time_up: 60 }

        # Central Shutters dont have short or position address
        Central.Shutter: {group_address_long: "1/5/1" }

    light:

        Kitchen.Light_1:     {group_address_switch: "1/6/1", group_address_dimm: "1/6/2", group_address_dimm_feedback: "1/6/3"}
        Diningroom.Light_1:  {group_address_switch: "1/6/4", group_address_dimm: "1/6/5", group_address_dimm_feedback: "1/6/6"}
        Living-Room.Light_1: {group_address_switch: "1/6/7", group_address_dimm: "1/6/8", group_address_dimm_feedback: "1/6/9"}

    # Measuring temperature (setting target temperature coming soon)
    thermostat:
        Kitchen.Thermostat_1: {group_address: "1/7/1"}

        Livingroom.Thermostat_2: {group_address: "1/7/2"}


    # Cyclic sending of time to the KNX bus
    time:
        General.Time: {group_address: "1/8/1"}
```

Basic Operations
----------------

```python

# Outlet

xknx.devices.device_by_name("Livingroom.Outlet_1").set_on()
time.sleep(5)
xknx.devices.device_by_name("Livingroom.Outlet_2").set_off()

# Shutter
xknx.devices.device_by_name("Livingroom.Shutter_1").set_down()
time.sleep(2)
xknx.devices.device_by_name("Livingroom.Shutter_1").set_up()
time.sleep(5)
xknx.devices.device_by_name("Livingroom.Shutter_1").set_short_down()
time.sleep(5)
xknx.devices.device_by_name("Livingroom.Shutter_1").set_short_up()

```


