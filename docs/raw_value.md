---
layout: default
title: RawValue
parent: Devices
nav_order: 7
---

# [](#header-1)RawValue - Send and receive raw values over KNX

## [](#header-2)Overview

RawValue devices send uint values to the KNX bus. Received values update the devices state. Optionally the current state can be read from the KNX bus.

## [](#header-2)Interface

- `xknx` is the XKNX object.
- `name` is the name of the object.
- `payload_length` is the appended byte size to a CEMI-Frame. `0` for DPT 1, 2 and 3.
- `group_address` is the KNX group address of the raw value device. Used for sending.
- `group_address_state` is the KNX group address of the raw value device.
- `respond_to_read` if `True` GroupValueRead requests to the `group_address` are answered. Defaults to `False`
- `sync_state` defines if and how often the value should be actively read from the bus. If `False` no GroupValueRead telegrams will be sent to its group address. Defaults to `True`
- `always_callback` defines if a callback shall be triggered for consecutive GroupValueWrite telegrams with same payload. Defaults to `False`
- `device_updated_cb` Callback for each update.

## [](#header-2)Example

```python
value = RawValue(
    xknx=xknx,
    name='Raw',
    payload_length=2,
    group_address='6/2/1',
    respond_to_read=True,
)
xknx.devices.async_add(value)

# Set a value without sending to the bus
value.remote_value.value = 23.0

# Send a new value to the bus
await value.set(24.0)

# Returns the value of in a human readable way
value.resolve_state()

# Returns the last received telegram or None
value.last_telegram
```
