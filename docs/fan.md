---
layout: default
title: Fan
parent: Devices
nav_order: 4
---

# [](#header-1)Fans

## [](#header-2)Overview

Fans are simple representations of KNX controlled fans. They support setting the speed either directly or with four fixed levels. These levels are "off", "low", "medium", "high". The configured speed for each level can be adjusted.

## [](#header-2)Interface

- `xknx` XKNX object.
- `name` name of the device.
- `group_address` is the KNX group address of the fan device. Used for sending.
- `group_address_state` is the KNX group address of the fan state. Used for updating and reading state.
- `device_updated_cb` awaitable callback for each update.
- `mode` Enum for the type of the fan control. Can be *Percent* or *Step*. Default: FanSpeedMode.Percent
- `fan_value_off` is the fan speed which represents the "off" setting of the fan. Default: 0
- `fan_value_low` is the fan speed which represents the "low" setting of the fan. Default: 33
- `fan_value_medium` is the fan speed which represents the "medium" setting of the fan. Default: 66
- `fan_value_high` is the fan speed which represents the "high" setting of the fan. Default: 100

## [](#header-2)Example

```python
fan = Fan(xknx,
              'TestFan',
              group_address='1/2/1',
              group_address_state='1/2/2')

# Set the fan speed
await fan.set_speed(50)

# Accessing speed
print(fan.current_speed)

# Set the fan speed level
await fan.set_speed_level("medium")

# Accessing speed level
print(fan.current_speed_level)

# Requesting state via KNX GroupValueRead
await fan.sync()
```

## [](#header-2)Configuration via **xknx.yaml**

Fans are usually configured via [`xknx.yaml`](/configuration):

```yaml
groups:
    fan:
        Livingroom.Fan_1: {group_address: '1/4/1', group_address_state: '1/4/2' }
```
