---
layout: default
title: NumericValue
parent: Devices
nav_order: 6
---

# [](#header-1)NumericValue - Send and receive numeric values over KNX

## [](#header-2)Overview

NumericValue devices send values to the KNX bus. Received values update the devices state. Optionally the current state can be read from the KNX bus.

## [](#header-2)Interface

- `xknx` is the XKNX object.
- `name` is the name of the object.
- `group_address` is the KNX group address of the numeric value device. Used for sending.
- `group_address_state` is the KNX group address of the numeric value device.
- `respond_to_read` if `True` GroupValueRead requests to the `group_address` are answered. Defaults to `False`
- `sync_state` defines if and how often the value should be actively read from the bus. If `False` no GroupValueRead telegrams will be sent to its group address. Defaults to `True`
- `value_type` controls how the value should be encoded / decoded. The attribute may have may have parseable value types representing numeric values.
- `always_callback` defines if a callback shall be triggered for consecutive GroupValueWrite telegrams with same payload. Defaults to `False`
- `device_updated_cb` awaitable callback for each update.

## [](#header-2)Example

```python
value = NumericValue(
    xknx=xknx,
    name='Temperature limit',
    group_address='6/2/1',
    respond_to_read=True,
    value_type='temperature'
)

# Set a value without sending to the bus
value.sensor_value.value = 23.0

# Send a new value to the bus
await value.set(24.0)

# Returns the value of in a human readable way
value.resolve_state()

# Returns the unit of the value as string
value.unit_of_measurement()

# Returns the last received telegram or None
value.last_telegram
```
