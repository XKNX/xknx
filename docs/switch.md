---
layout: default
title: Switches
parent: Devices
nav_order: 9
---

# [](#header-1)Switches

## [](#header-2)Overview

Switches are simple representations of binary actors. They mainly support switching on and off.

## [](#header-2)Interface

- `xknx` is the XKNX object.
- `name` is the name of the object.
- `group_address` is the KNX group address of the switch device. Used for sending.
- `group_address_state` is the KNX group address of the switch state. Used for updating and reading state.
- `respond_to_read` if `True` GroupValueRead requests to the `group_address` are answered. Defaults to `False`
- `sync_state` defines if and how often the value should be actively read from the bus. If `False` no GroupValueRead telegrams will be sent to its group address. Defaults to `True`
- `invert` inverts the payload so state "on" is represented by 0 on bus and "off" by 1. Defaults to `False`
- `reset_after` may be used to reset the switch to `OFF` again after given time in sec. Defaults to `None`
- `device_updated_cb` awaitable callback for each update.


## [](#header-2)Example

```python
switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')

# Accessing switch via xknx.devices
await xknx.devices['TestOutlet'].set_on()

# Switching switch on
await switch.set_on()
# Switching switch off
await switch.set_off()

# Accessing state
print(switch.state)

# Requesting state via KNX GroupValueRead
await switch.sync(wait_for_result=True)
```
