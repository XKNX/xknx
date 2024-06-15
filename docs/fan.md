---
layout: default
title: Fan
parent: Devices
nav_order: 4
---

# [](#header-1)Fans

## [](#header-2)Overview

Fans are simple representations of KNX controlled fans. They support switching on/off, setting the speed and the oscillation.

## [](#header-2)Interface

- `xknx` XKNX object.
- `name` name of the device.
- `group_address_speed` is the KNX group address of the fan speed. Used for sending. If no `group_address_switch` is provided, it will implicitly control switching the fan on/off as well. *DPT 5.001 / 5.010*
- `group_address_speed_state` is the KNX group address of the fan speed state. Used for updating and reading state. *DPT 5.001 / 5.010*
- `group_address_oscillation` is the KNX group address of the oscillation. Used for sending. *DPT 1.001*
- `group_address_oscillation_state` is the KNX group address of the fan oscillation state. Used for updating and reading state. *DPT 1.001*
- `group_address_switch` is the KNX group address of the fan on/off state. If not used, on/off will implicitly be controlled via `group_address_speed` instead. Used for sending. *DPT 1.001*
- `group_address_switch_state` is the KNX group address of the fan on/off state. Used for updating and reading state. *DPT 1.001*
- `sync_state` defines if and how often the value should be actively read from the bus. If `False` no GroupValueRead telegrams will be sent to its group address. Defaults to `True`
- `device_updated_cb` Callback for each update.
- `max_step` Maximum step amount for fans which are controlled with steps and not percentage. If this attribute is set, the fan is controlled by sending the step value in the range `0` and `max_step`. In that case, the group address DPT changes from *DPT 5.001* to *DPT 5.010*. Default: None

## [](#header-2)Example

```python
fan = Fan(
    xknx,
    'TestFan',
    group_address_speed='1/2/1',
    group_address_speed_state='1/2/2',
    group_address_oscillation='1/2/3',
    group_address_oscillation_state='1/2/4'
)
xknx.devices.async_add(fan)

# Set the fan speed
await fan.set_speed(50)

# Accessing speed
print(fan.current_speed)

# Set the oscillation
await fan.set_oscillation(True)

# Accessing oscillation
print(fan.current_oscillation)

# Accessing on/off state
print(fan.is_on)

# Requesting state via KNX GroupValueRead
await fan.sync()
```
