---
layout: default
title: Time
nav_order: 7
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
xknx.devices.add(time_device)

# Sending time to knx bus
await xknx.devices['TimeTest'].sync()
``` 

* `xknx` is the XKNX object.
* `name` is the name of the object.
* `group_address` is the KNX group address of the sensor device.
* `broadcast_type` defines the value type that will be sent to the KNX bus. Valid attributes are: 'time', 'date' and 'datetime'. Default: `time`
* `localtime` If set `True` sync() and GroupValueRead requests always return the current local time. On `False` the set value will be sent. Default: `True`


## [](#header-2)Configuration via **xknx.yaml**

Time objects are usually configured via [`xknx.yaml`](/configuration):

```yaml
groups:
    time:
        General.Time: {group_address: '2/1/2'}
```

## [](#header-2)Daemon mode

When XKNX is started in [daemon mode](/xknx), with START_STATE_UPDATER enabled, XKNX will automatically send the time to the KNX bus with the `sync_state`-loop. 

```python
import asyncio
from xknx import XKNX
from xknx.devices import DateTime

async def main():
    xknx = XKNX()
    time = DateTime(xknx, 'TimeTest', group_address='1/2/3')
    xknx.devices.add(time)
    print("Sending time to KNX bus every hour")
    await xknx.start(daemon_mode=True, state_updater=True)
    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

## [](#header-2)Interface


```python
from xknx import XKNX
from xknx.devices import DateTime

xknx = XKNX()
time_device = DateTime(xknx, 'TimeTest', group_address='1/2/3', broadcast_type='time')

# Sending Time to KNX bus 
await time_device.broadcast_localtime()
```

