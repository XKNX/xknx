XKNX
====

A Wrapper around KNX/UDP protocol written in python.

This program only works with KNX/IP router.


Supported / Tested Devices
--------------------------

The software was tested with the following devices:

- [GIRA KNX/IP-Routers 216700](http://www.gira.com/en/gebaeudetechnik/systeme/knx-eib_system/knx-produkte/systemgeraete/knx-ip-router.html)
- [GIRA KNX/Switching Actor  104000](http://katalog.gira.de/de_DE/deeplinking.html?artikelnr=104000&m=compare)
- [GIRA KNX/Shutter Binary Actor 103800](https://katalog.gira.de/en/datenblatt.html?id=635678)
- [GIRA KNX/Binary Input 111900 ](https://www.gira.de/gebaeudetechnik/systeme/knx-eib_system/knx-produkte/tasterschnittstellen/knxeib-universal-tasterschnittstelle.html)

Sample Configuration
--------------------

```yaml
general:
    own_address: "15.15.249"
    own_ip: "192.168.42.1"

groups:

    switch:
        Livingroom.Switch1:
            group_address: 1025
            actions:
              - {hook: "off", switch_time: "long", target: Livingroom.Shutter_1, method: up}
              - {hook: "off", switch_time: "short", target: Livingroom.Shutter_1, method: short_up}

        Livingroom.Switch2:
            group_address: 1026
            actions:
              - {hook: "off", switch_time: "long", target: Livingroom.Shutter_1, method: down}
              - {hook: "off", switch_time: "short", target: Livingroom.Shutter_1, method: short_down}

        Livingroom.Switch3:
            group_address: 1027
            actions:
              - {hook: "on", target: Livingroom.Outlet_1, method: "on"}
              - {hook: "on", target: Livingroom.Outlet_2, method: "on"}
              - {hook: "on", target: Livingroom.Outlet_3, method: "on"}
              - {hook: "on", target: Livingroom.Outlet_4, method: "on"}

        Livingroom.Switch4:
            group_address: 1028
            actions:
              - {hook: "on", target: Livingroom.Outlet_1, method: "off"}
              - {hook: "on", target: Livingroom.Outlet_2, method: "off"}
              - {hook: "on", target: Livingroom.Outlet_3, method: "off"}
              - {hook: "on", target: Livingroom.Outlet_4, method: "off"}

    outlet:
        Livingroom.Outlet_1: {group_address: 65}
        Livingroom.Outlet_2: {group_address: 66}
        Livingroom.Outlet_3: {group_address: 67}
        Livingroom.Outlet_4: {group_address: 68}

    outlet 2:
        Kitchen.Outlet_1: {group_address: 12}
        Kitchen.Outlet_2: {group_address: 13}
        Kitchen.Outlet_3: {group_address: 14}
        Kitchen.Outlet_4: {group_address: 15}

    shutter:
        Livingroom.Shutter_1: {group_address_long: 9, group_address_short: 10, group_address_position: 11}

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
