---
layout: default
---

Configuration
=============

Overview
--------

XKNX is controlled via a configuration file. Per default the configuration file is  named `xknx.yaml`. 

The configuration file contains two section. The `general` section contains the individual / physical address of the XKNX daemon (`own_address`).

Within the `groups` sections all devices are defined. For each type of device more then one section might be specified. You need to append numbers or strings to differentiate the entries, as in the example below. The appended number or string must be unique. 

How to use
----------

Use the `config` attribute when initializing `XKNX` to spefify a configuration file:

```python
xknx = XKNX(config='xknx.yaml')

for device in xknx.devices:
    print(device)
```

## [](#header-2)Example

```yaml
general:
    own_address: '15.15.249'

groups:

    binary_sensor:

        Livingroom.Switch_1:
            group_address: '1/2/7'
            actions:
              - {target: Livingroom.Outlet_1, method: 'on'}
              - {target: Livingroom.Outlet_2, counter: 2, method: 'on'}

        Livingroom.Switch_2:
            group_address: '1/2/8'
            actions:
              - {target: Livingroom.Outlet_1, method: 'off'}
              - {target: Livingroom.Outlet_2, counter: 2, method: 'off'}


        Livingroom.Switch_3:
            group_address: '1/2/2'
            actions:
              - {hook: 'off', target: Livingroom.Shutter_1, method: short_up}
              - {hook: 'off', counter: 2, target: Livingroom.Shutter_1, method: up} # Pressing more then 2 seconds

        Livingroom.Switch_4:
            group_address: '1/2/3'
            actions:
              - {hook: 'off', target: Livingroom.Shutter_1, method: short_down}
              - {hook: 'off', counter: 2, target: Livingroom.Shutter_1, method: down} # Pressing more then 2 seconds


    binary_sensor_motion_dection:
        Kitchen.Motion.Sensor: {group_address: '3/0/0', device_class: 'motion'}
        DiningRoom.Motion.Sensor: {group_address: '3/0/1', device_class: 'motion'}

        # Some states are encoded into different bits of the same group_address
        # Defining which bit should be relevant for the binary state via the "significant_bit" option
        Kitchen.Presence: {group_address: '3/0/2', device_class: 'motion', significant_bit: 2}
        Kitchen.ThermostatNightMode: {group_address: '3/0/2', device_class: 'motion', significant_bit: 1}


    switch:

        Livingroom.Outlet_1: {group_address: '1/3/1'}
        Livingroom.Outlet_2: {group_address: '1/3/2'}

    switch 2:
        Kitchen.Outlet_1: {group_address: '1/3/7'}
        Kitchen.Outlet_2: {group_address: '1/3/8'}
        Kitchen.Outlet_3: {group_address: '1/3/9'}
        Kitchen.Outlet_4: {group_address: '1/3/10'}

    cover:
        Livingroom.Shutter_1: {group_address_long: '1/4/1', group_address_short: '1/4/2', group_address_position_feedback: '1/4/3', group_address_position: '1/4/4', travel_time_down: 50, travel_time_up: 60 }
        Livingroom.Shutter_2: {group_address_long: '1/4/5', group_address_short: '1/4/6', group_address_position_feedback: '1/4/7', group_address_position: '1/4/8', travel_time_down: 50, travel_time_up: 60 }

        # Covers without direct positioning:
        Livingroom.Shutter_3: {group_address_long: '1/4/9', group_address_short: '1/4/10', group_address_position_feedback: '1/4/11', travel_time_down: 50, travel_time_up: 60 }

        # Central Shutters dont have short or position address
        Central.Shutter: {group_address_long: '1/5/1' }

    light:

        Kitchen.Light_1:     {group_address_switch: '1/6/1', group_address_brightness: '1/6/3'}
        Diningroom.Light_1:  {group_address_switch: '1/6/4', group_address_brightness: '1/6/6'}
        Living-Room.Light_1: {group_address_switch: '1/6/7'}
        # Light with extra addresses for states:
        Office.Light_1:  {group_address_switch: '1/7/4', group_address_switch_state: '1/7/5', group_address_brightness: '1/7/6', group_address_brightness_state: '1/7/7'}

    climate:
        Kitchen.Climate_1: {group_address_temperature: '1/7/1'}
        Livingroom.Climate_2: {group_address_temperature: '1/7/2', group_address_setpoint: '1/7/3'}

    # Cyclic sending of time to the KNX bus
    time:
        General.Time: {group_address: '2/1/2'}


    sensor:
        Heating.Valve1: {group_address: '2/0/0', value_type: 'percent'}
        Heating.Valve2: {group_address: '2/0/1', value_type: 'percent'}
        Some.Other.Value: {group_address: '2/0/2'}

```
