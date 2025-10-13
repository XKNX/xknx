---
layout: default
title: Binary Sensor
parent: Devices
nav_order: 1
---

# Binary Sensor

## [](#header-2)Overview

Binary sensors which have either the state "on" or "off". Binary sensors could be e.g. a switch in the wall (the thing you press on when switching on the light) or a motion detector.

The logic within switches can further handle if a button is pressed once or twice - and trigger different actions in HA. Use the attribute `counter` for this purpose.

## [](#header-2)Interface

- `xknx` is the XKNX object.
- `name` is the name of the object.
- `group_address_state` is the KNX group address of the sensor device.
- `invert` inverts the payload so state "on" is represented by 0 on bus and "off" by 1. Defaults to `False`
- `sync_state` defines if and how often the value should be actively read from the bus. If `False` no GroupValueRead telegrams will be sent to its group address. Defaults to `True`
- `ignore_internal_state` defines if consecutive GroupValueWrite telegrams with same payload shall be processed, regardless of the current binary sensor state. Defaults to `False`
- `context_timeout` time in seconds telegrams should be counted towards the current context to increment the counter. If set `ignore_internal_state` is set `True` internally. GroupValueResponse telegrams are ignored for this. Defaults to `None`
- `always_callback` defines if a callback shall also be triggered for consecutive telegrams with same payload, regardless of the current binary sensor state. This has precedence over `ignore_internal_state` and is applied for GroupValueWrite and GroupValueResponse telegrams. Defaults to `False`
- `reset_after` may be used to reset the internal state to `OFF` again after given time in sec. Defaults to `None`
- `device_updated_cb` Callback for each update.

## [](#header-2)Example

```python
binarysensor = BinarySensor(xknx, 'TestInput', group_address_state='2/3/4')
xknx.devices.async_add(binarysensor)

# Returns the last received Telegram or None
binarysensor.last_telegram
```
