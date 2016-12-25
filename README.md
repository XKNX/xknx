XKNX
====

A Wrapper around KNX/UDP protocol written in python.

The wrapper is also intended to be used as a KNX logic module, which means to connect different KNX devices and make them interact.

At the moment the wrapper works with KNX/IP router.

Roadmap
-------

* Add functionality for KNX tunneling devices
* Add functionality for auto discovery for KNX/IP router and tunneling devices


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

        Livingroom.Shutter_1: {group_address_long: "1/4/1", group_address_short: "1/4/2", group_address_position_feedback: "1/4/3", group_address_position: "1/4/4"}
        Livingroom.Shutter_2: {group_address_long: "1/4/5", group_address_short: "1/4/6", group_address_position_feedback: "1/4/7", group_address_position: "1/4/8"}

        # Central Shutters dont have short or position address
        Central.Shutter: {group_address_long: "1/5/1" }

    dimmer:

        Kitchen.Light_1:     {group_address_switch: "1/6/1", group_address_dimm: "1/6/2", group_address_dimm_feedback: "1/6/3"}
        Diningroom.Light_1:  {group_address_switch: "1/6/4", group_address_dimm: "1/6/5", group_address_dimm_feedback: "1/6/6"}
        Living-Room.Light_1: {group_address_switch: "1/6/7", group_address_dimm: "1/6/8", group_address_dimm_feedback: "1/6/9"}
```

Basic Operations
----------------

```python

# Outlet

devices_.device_by_name("Livingroom.Outlet_1").set_on()
time.sleep(5)
devices_.device_by_name("Livingroom.Outlet_2").set_off()

# Shutter
devices_.device_by_name("Livingroom.Shutter_1").set_down()
time.sleep(2)
devices_.device_by_name("Livingroom.Shutter_1").set_up()
time.sleep(5)
devices_.device_by_name("Livingroom.Shutter_1").set_short_down()
time.sleep(5)
devices_.device_by_name("Livingroom.Shutter_1").set_short_up()

```


Sample Program
--------------

```
#!/usr/bin/python3
from xknx import Multicast,Devices,devices_,Config

Config.read()
Multicast().recv()
```

`Multicast().recv()` may also take a callback as parameter:

```python
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
```
