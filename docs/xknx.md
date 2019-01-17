---
layout: default
---

# [](#header-1)The XKNX Object

# [](#header-2)Overview

The `XKNX()` object is the core element of any XKNX installation. It should be only initialized once per implementation. The XKNX object is responsible for:

* connectiong to a KNX/IP device and managing the connection
* processing all incoming KNX telegrams
* organizing all connected devices and keeping their state
* updating all connected devices from time to time
* keeping the global configuration

# [](#header-2)Initialization

```python
xknx = XKNX(config='xknx.yaml',
            loop=loop,
            own_address=Address,
            telegram_received_cb=function1,
            device_updated_cb=function2):
```

The constructor of the XKNX object takes several parameters:

* `config` defines a path to the local [XKNX.yaml](/configuration).
* `loop` points to the asyncio.loop object. Of not specified it uses `asyncio.get_event_loop()`.
* `own_address` may be used to specify the physical KNX address of the XKNX daemon. If not speficied it uses `15.15.250`.
* `telegram_received_cb` is a callback which is called after every received KNX telegram. See [callbacks](#callbacks) documentation for details.
* `device_updated_cb` is a callback after a [XKNX device](#devices) was updated. See [callbacks](#callbacks) documentation for details.

# [](#header-2)Starting

```python
await xknx.start(state_updater=False, daemon_mode=False)
```

`xknx.start()` will search for KNX/IP devices in the network and either build a KNX/IP-Tunnel or open a mulitcast KNX/IP-Routing connection. `start()` will take the following paramters

* if `state_updater` is set, XKNX will start an asynchronous process for syncing the states of all connected devices every hour
* if `daemon_mode` is set, start will only stop if Control-X is pressed. This function is useful for using XKNX as a daemon, e.g. for using the callback functions or using the internal action logic.

# [](#header-2)Stopping

```python
await xknx.stop()
```

Will disconnect from tunneling devices and stop the different queues.

# [](#header-2)Devices

The XKNX may keep all devices in a local storage named `devices`. All devices may be accessed by their name: `xknx.devices['NameOfDevice']`. If XKNX receives an update via KNX GROUP WRITE the device is updated automatically.

Example:

```python
outlet = Outlet(xknx,
                name='TestOutlet',
                group_address='1/1/11')
xknx.devices.add(outlet)

await xknx.devices['TestOutlet'].set_on()
await xknx.devices['TestOutlet'].set_off()
```


# [](#header-2)Callbacks

The `telegram_received_cb` will be called for each KNX telegram received by the XKNX daemon. Example:

```python
import asyncio
from xknx import XKNX

def telegram_received_cb(telegram):
    print("Telegram received: {0}".format(telegram))

async def main():
    xknx = XKNX(telegram_received_cb=telegram_received_cb)
    await xknx.start(daemon_mode=True)
    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

For all devices stored in the `devices` storage (see [above](#devices)) a callback for each update may be defined:

```python
import asyncio
from xknx import XKNX, Outlet


def device_updated_cb(device):
    print("Callback received from {0}".format(device.name))


async def main():
    xknx = XKNX(device_updated_cb=device_updated_cb)
    outlet = Outlet(xknx,
                    name='TestOutlet',
                    group_address='1/1/11')
    xknx.devices.add(outlet)

    await xknx.start(daemon_mode=True)

    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```




