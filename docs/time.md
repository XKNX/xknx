---
layout: default
title: Time
parent: Devices
nav_order: 10
---

# [](#header-1)Time

## [](#header-2)Overview

XKNX provides the possibility to send the local time, date or both combined to the KNX bus in regular intervals with `TimeDevice`, `DateDevice` or `DateTimeDevice`.

## [](#header-2)Example

```python
time_device = TimeDevice(
    xknx, 'TimeTest',
    group_address='1/2/3',
    localtime=True
)
xknx.devices.async_add(time_device)

# `sync()` doesn't send a GroupValueRead when localtime is True but sends the current time to KNX bus
await xknx.devices['TimeTest'].sync()
```

* `xknx` is the XKNX object.
* `name` is the name of the object.
* `group_address` is the KNX group address of the sensor device.
* `localtime` If set `True` sync() and GroupValueRead requests always return the current systems local time and it is also sent every 60 minutes. Same if set to a `datetime.tzinfo` object, but the time for that timezone information will be used. On `False` the set value will be sent, no automatic sending will be scheduled. Default: `True`
* `device_updated_cb` Callback for each update.

## [](#header-2)Local time

When XKNX is started, a DateDevice, DateTimeDevice or TimeDevice will automatically send the time to the KNX bus every hour. This can be disabled by setting `localtime=False`.

```python
import asyncio
from xknx import XKNX
from xknx.devices import DateTimeDevice

async def main():
    async with XKNX(daemon_mode=True) as xknx:
        dt_device = DateTimeDevice(xknx, 'TimeTest', group_address='1/2/3')
        xknx.devices.async_add(dt_device)
        print("Sending datetime object to KNX bus every hour")

asyncio.run(main())
```

## [](#header-2)Interface

```python
from xknx import XKNX
from xknx.devices import DateDevice

xknx = XKNX()
date_device = DateDevice(xknx, 'TimeTest', group_address='1/2/3')
xknx.devices.async_add(date_device)

await xknx.start()
# Sending Time to KNX bus
await time_device.broadcast_localtime()
```

