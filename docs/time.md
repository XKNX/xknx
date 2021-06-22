---
layout: default
title: Time
parent: Devices
nav_order: 10
---

# [](#header-1)Time

## [](#header-2)Overview

XKNX provides the possibility to send the local time, date or both combined to the KNX bus in regular intervals. This can be used to display the time within [KNX touch sensors](https://katalog.gira.de/en/datenblatt.html?id=638294) or for KNX automation schemes programmed with the ETS.

## [](#header-2)Example

```python
time_device = DateTime(
    xknx, 'TimeTest',
    group_address='1/2/3',
    broadcast_type='TIME',
    localtime=True
)

# `sync()` doesn't send a GroupValueRead when localtime is True but sends the current time to KNX bus
await xknx.devices['TimeTest'].sync()
```

* `xknx` is the XKNX object.
* `name` is the name of the object.
* `group_address` is the KNX group address of the sensor device.
* `broadcast_type` defines the value type that will be sent to the KNX bus. Valid attributes are: 'time', 'date' and 'datetime'. Default: `time`
* `localtime` If set `True` sync() and GroupValueRead requests always return the current local time. On `False` the set value will be sent. Default: `True`
* `device_updated_cb` awaitable callback for each update.

## [](#header-2)Daemon mode

When XKNX is started in [daemon mode](/xknx), with START_STATE_UPDATER enabled, XKNX will automatically send the time to the KNX bus with the `sync_state`-loop.

```python
import asyncio
from xknx import XKNX
from xknx.devices import DateTime

async def main():
    async with XKNX(daemon_mode=True) as xknx:
        time = DateTime(xknx, 'TimeTest', group_address='1/2/3')
        print("Sending time to KNX bus every hour")

asyncio.run(main())
```

## [](#header-2)Interface


```python
from xknx import XKNX
from xknx.devices import DateTime

xknx = XKNX()
time_device = DateTime(xknx, 'TimeTest', group_address='1/2/3', broadcast_type='time')

await xknx.start()
# Sending Time to KNX bus
await time_device.broadcast_localtime()
```

