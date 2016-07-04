XKNX
====

A Wrapper around KNX/UDP protocol written in python.

This program only works with KNX/IP router.

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
