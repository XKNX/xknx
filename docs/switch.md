---
layout: default
title: Switches
parent: Devices
nav_order: 6
---

# [](#header-1)Switches

## [](#header-2)Overview

Switches are simple representations of binary actors. They mainly support switching on and off.

## [](#header-2)Interface

- `xknx` is the XKNX object.
- `name` is the name of the object.
- `group_address` is the KNX group address of the switch device. Used for sending.
- `group_address_state` is the KNX group address of the switch state. Used for updating and reading state.
- `invert` inverts the payload so state "on" is represented by 0 on bus and "off" by 1. Defaults to `False`
- `reset_after` may be used to reset the switch to `OFF` again after given time in sec. Defaults to `None`
- `icon` for the switch (see [icon documentation](https://www.home-assistant.io/docs/configuration/customizing-devices/#icon) for details).
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

# Accessing switch via 'do'
await switch.do('on')
await switch.do('off')

# Accessing state
print(switch.state)

# Requesting state via KNX GroupValueRead
await switch.sync(wait_for_result=True)
```

## [](#header-2)Configuration via **xknx.yaml**

Switches are usually configured via [`xknx.yaml`](/configuration):

```yaml
groups:
    switch:
        Livingroom.Outlet_1: {group_address: '1/3/1'}
        Livingroom.Outlet_2: {group_address: '1/3/2', icon: 'mdi:power-socket-eu'}
```




