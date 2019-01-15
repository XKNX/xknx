---
layout: default
---

Binary Sensor
=============

Binary sensors which have either the state "on" or "off". Binary sensors could be e.g. a switch in the wall (the thing you press on when switching on the light) or a motion detector. 

Switches are mainly intended to act on input, which means to execute so called `Actions`. An action can be the switching of an outlet or light or the moving of a cover.

The logic within switches can further handle if a button is pressed once or twice - and trigger different actions. Use the attribute `counter` for this purpose.

## [](#header-2)Overview

```python
binarysensor = BinarySensor(xknx, 'TestInput', group_address='1/2/3', device_class='motion')
```

* `xknx` is the XKNX object.
* `name` is the name of the object.
* `group_address` is the KNX group address of the sensor device.
* `device_class` may be used to store the type of sensor, e.g. "motion" for motion detectors.

## [](#header-2)Example

```python
outlet = Outlet(xknx, 'TestOutlet', group_address='1/2/3')
xknx.devices.devices.append(outlet)

binarysensor = BinarySensor(xknx, 'TestInput', group_address='1/2/3')
action_on = Action(
    xknx,
    hook='on',
    target='TestOutlet',
    method='on')
binarysensor.actions.append(action_on)
action_off = Action(
    xknx,
    hook='off',
    target='TestOutlet',
    method='off')
binarysensor.actions.append(action_off)
xknx.devices.add(binarysensor)
``` 

## [](#header-2)Configuration via **xknx.yaml**

Binary sensor objects are usually configured via [`xknx.yaml`](/configuration):

```yaml
groups:

    binary_sensor:
        Livingroom.Switch_1:
            group_address: "1/2/7"
            actions:
              - {target: Livingroom.Outlet_1, method: "on"}
              - {target: Livingroom.Outlet_2, method: "on"}

        Livingroom.Switch_2:
            group_address: "1/2/8"
            actions:
              - {target: Livingroom.Outlet_1, method: "off"}
              - {target: Livingroom.Outlet_2, method: "off"}

        Livingroom.Switch_3:
            group_address: "1/2/5"
            actions:
              - {target: Livingroom.Shutter_1, method: up}
              # Only executed if the button was switched twice:
              - {counter: 2, target: Livingroom.Shutter_1, method: short_up}

        Livingroom.Switch_4:
            group_address: "1/2/6"
            actions:
              - {target: Livingroom.Shutter_1, method: down}
              # Only executed if the button was switched twice:
              - {counter: 2, target: Livingroom.Shutter_1, method: short_down}


    switch:
        Livingroom.Outlet_1: {group_address: '1/3/1'}
        Livingroom.Outlet_2: {group_address: '1/3/2'}

    cover:
        Livingroom.Shutter_1: {group_address_long: 3171, group_address_short: 3172, group_address_position_state: 3173, group_address_position: 3174, travelling_time_down: 51, travelling_time_up: 61}
```



