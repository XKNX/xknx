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
devices:
    1.1.0: IP Router
    1.1.1: Pushbutton interface
    1.1.2: Switching actuator

    1.1.255: ETS

groups:
    switch:
        Livingroom.Switch_1: {group_address: 1}
        Livingroom.Switch_2: {group_address: 2}
        Livingroom.Switch_3: {group_address: 3}
        Livingroom.Switch_4: {group_address: 4}

    outlet:
        Livingroom.Outlet_1: {group_address: 65}
        Livingroom.Outlet_2: {group_address: 66}

    dimmer:
        Kitchen.Dimmer_1: {group_address: 9}
        Kitchen.Dimmer_2: {group_address: 10}
        Kitchen.Dimmer_4: {group_address: 11}

    outlet 2:
        Kitchen.Outlet_1: {group_address: 12}
        Kitchen.Outlet_2: {group_address: 13}
        Kitchen.Outlet_3: {group_address: 14}
        Kitchen.Outlet_4: {group_address: 15}
```

Basic Operations
----------------

```python

# Outlet

nameresolver_.device_by_name("Livingroom.Outlet_1").set_on()
time.sleep(5)
nameresolver_.device_by_name("Livingroom.Outlet_2").set_off()

# Shutter
nameresolver_.device_by_name("Livingroom.Shutter_1").set_down()
time.sleep(2)
nameresolver_.device_by_name("Livingroom.Shutter_1").set_up()
time.sleep(5)
nameresolver_.device_by_name("Livingroom.Shutter_1").set_short_down()
time.sleep(5)
nameresolver_.device_by_name("Livingroom.Shutter_1").set_short_up()

```


Sample Program
--------------


```python
#!/usr/bin/python3

from xknx import Multicast,NameResolver,nameresolver_


def callback( telegram):

    device = nameresolver_.device_by_group_address(telegram.group)

    device.process(telegram)

    if (device.name == "Livingroom.Switch_1" ):
        if device.is_on():
            nameresolver_.device_by_name("Livingroom.Outlet_1").set_on()
        elif device.is_off():
            nameresolver_.device_by_name("Livingroom.Outlet_1").set_off()

    if (device.name == "Livingroom.Switch_2" ):
        if device.is_on():
            nameresolver_.device_by_name("Livingroom.Outlet_2").set_on()
        elif device.is_off():
            nameresolver_.device_by_name("Livingroom.Outlet_2").set_off()

nameresolver_.read_configuration()

nameresolver_.update_thread_start(60)

Multicast().recv(callback)
```
