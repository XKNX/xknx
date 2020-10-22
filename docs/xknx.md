---
layout: default
title: XKNX Object
nav_order: 3
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
            address_format=GroupAddressType.LONG
            telegram_received_cb=None,
            device_updated_cb=None,
            rate_limit=DEFAULT_RATE_LIMIT,
            multicast_group=DEFAULT_MCAST_GRP,
            multicast_port=DEFAULT_MCAST_PORT,
            log_directory=None,
            state_updater=False,
            daemon_mode=False,
            connection_config=ConnectionConfig())
```

The constructor of the XKNX object takes several parameters:

* `config` defines a path to the local [XKNX.yaml](/configuration).
* `loop` points to the asyncio.loop object. Of not specified it uses `asyncio.get_event_loop()`.
* `own_address` may be used to specify the physical KNX address of the XKNX daemon. If not speficied it uses `15.15.250`.
* `address_format` may be used to specify the type of group addresses to use. Possible values are:
** FREE: integer or hex representation
** SHORT: representation like '1/34' without middle groups
** LONG: representation like '1/2/34' with middle groups
* `telegram_received_cb` is a callback which is called after every received KNX telegram. See [callbacks](#callbacks) documentation for details.
* `device_updated_cb` is an async callback after a [XKNX device](#devices) was updated. See [callbacks](#callbacks) documentation for details.
* `rate_limit` in telegrams per second - can be used to limit the outgoing traffic to the KNX/IP interface. The default value is 20 packets per second.
* `multicast_group` is the multicast IP address - can be used to override the default multicast address (`224.0.23.12`)
* `multicast_port` is the multicast port - can be used to override the default multicast port (`3671`)
* `log_directory` is the path to the log directory - when set to a valid directory we log to a dedicated file in this directory called `xknx.log`. The log files are rotated each night and will exist for 7 days. After that the oldest one will be deleted.
* if `state_updater` is set, XKNX will start (once `start() is called) an asynchronous process for syncing the states of all connected devices every hour
* if `daemon_mode` is set, start will only stop if Control-X is pressed. This function is useful for using XKNX as a daemon, e.g. for using the callback functions or using the internal action logic.
* `connection_config` replaces a ConnectionConfig() that was read from a yaml config file.

# [](#header-2)Starting

```python
await xknx.start()
```

`xknx.start()` will search for KNX/IP devices in the network and either build a KNX/IP-Tunnel or open a mulitcast KNX/IP-Routing connection. `start()` will not take any parameters.

# [](#header-2)Stopping

```python
await xknx.stop()
```

Will disconnect from tunneling devices and stop the different queues.

# [](#header-2)Using XKNX as an asynchronous context manager

Except of writing:

```python
import asyncio

async def main():
    xknx = XKNX()
    await xknx.start()
    switch = Switch(xknx,
                name='TestSwitch',
                group_address='1/1/11')

    await switch.set_on()
    await xknx.stop()

asyncio.run(main())
```

you can now use the following syntax:

```python
import asyncio

async def main():
    async with XKNX() as xknx:
        switch = Switch(xknx,
                name='TestSwitch',
                group_address='1/1/11')

        await switch.set_on()

asyncio.run(main())
```

# [](#header-2)Devices

The XKNX may keep all devices in a local storage named `devices`. All devices may be accessed by their name: `xknx.devices['NameOfDevice']`. If XKNX receives an update via KNX GROUP WRITE the device is updated automatically.

Example:

```python
switch = Switch(xknx,
                name='TestSwitch',
                group_address='1/1/11')

await xknx.devices['TestSwitch'].set_on()
await xknx.devices['TestSwitch'].set_off()
```


# [](#header-2)Callbacks

The `telegram_received_cb` will be called for each KNX telegram received by the XKNX daemon. Example:

```python
import asyncio
from xknx import XKNX

async def telegram_received_cb(telegram):
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
from xknx import XKNX
from xknx.devices import Switch


async def device_updated_cb(device):
    print("Callback received from {0}".format(device.name))


async def main():
    xknx = XKNX(device_updated_cb=device_updated_cb)
    switch = Switch(xknx,
                    name='TestSwitch',
                    group_address='1/1/11')

    await xknx.start(daemon_mode=True)

    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

# [](#header-2)Dockerised xknx's app 

If you planned to run xknx into a container, you have to setup udp port binding from your host to the container.
The host ip and port must be setup into the configuration file or env variables.

Available env variables are:
- XKNX_GENERAL_OWN_ADDRESS
- XKNX_GENERAL_RATE_LIMIT
- XKNX_GENERAL_MULTICAST_GROUP
- XKNX_GENERAL_MULTICAST_PORT
- XKNX_CONNECTION_GATEWAY_IP: Your KNX Gateway IP address
- XKNX_CONNECTION_GATEWAY_PORT: Your KNX Gateway UDP port
- XKNX_CONNECTION_LOCAL_IP
- XKNX_CONNECTION_LOCAL_PORT: Container internal UDP port, target of the forward from the host
- XKNX_CONNECTION_BIND_IP: IP address of the host machine
- XKNX_CONNECTION_BIND_PORT: UDP port used in the host machine, must be forwarded to the container

Exanple of a `docker run` with an xknx based app:

```bash
docker run --name myapp -d \
  -e XKNX_CONNECTION_GATEWAY_IP='192.168.0.123' \
  -e XKNX_CONNECTION_LOCAL_PORT=12399 \
  -e XKNX_CONNECTION_BIND_IP='192.168.0.100' 
  -e XKNX_CONNECTION_BIND_PORT=12300 \
  -p 12300:12399/udp myapp:latest
```
