---
layout: default
---

# [](#header-1)Asynchronous Python Library for KNX

XKNX is an Asynchronous  Python library for reading and writing [KNX](https://en.wikipedia.org/wiki/KNX_(standard))/IP packets. 

[![Coverage Status](https://coveralls.io/repos/github/XKNX/xknx/badge.svg?branch=master)](https://coveralls.io/github/XKNX/xknx?branch=master)

## [](#header-2)Overview

XKNX...
* ... does [cooperative multitasking via asyncio](https://github.com/XKNX/xknx/blob/master/examples/example_light_state.py) and is 100% thread safe.
* ... provides support for KNX/IP [routing](https://github.com/XKNX/xknx/blob/master/xknx/io/routing.py) *and* [tunneling](https://github.com/XKNX/xknx/blob/master/xknx/io/tunnel.py) devices.
* ... has strong coverage with [unit tests](https://github.com/XKNX/xknx/tree/master/test).
* ... automatically updates and synchronizes all devices in the background periodically.
* ... listens for all updates of all devices on the KNX bus and updates the corresponding internal objects.
* ... has a clear abstraction of data/network/logic-layer.
* ... provides Heartbeat monitoring for Tunneling connections + clean reconnect if KNX/IP connection failed.
* ... does clean [connect](https://github.com/XKNX/xknx/blob/master/xknx/io/connect.py) and [disconnect](https://github.com/XKNX/xknx/blob/master/xknx/io/disconnect.py) requests to the tunneling device.
* ... ships with [Home Assistant](https://home-assistant.io/).

## [](#header-2)Installation

XKNX depends on Python >= 3.5. (All prior versions of Python < 3.5 have a bug in their multicast implementation.)

You can install XKNX as Python package via pip3:

```bash
sudo pip3 install xknx
``` 

## [](#header-2)Hello World

```python
import asyncio
from xknx import XKNX
from xknx.devices import Light

async def main():
    xknx = XKNX()
    await xknx.start()
    light = Light(xknx,
                  name='HelloWorldLight',
                  group_address_switch='1/0/9')
    await light.set_on()
    await asyncio.sleep(2)
    await light.set_off()
    await xknx.stop()


# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

For more examples please check out the [examples page](https://github.com/XKNX/xknx/tree/master/examples)

# [](#header-1)Getting Help

For questions, feature requests, bugreports wither join the [XKNX chat on Discord](https://discord.gg/EuAQDXU) or write an [email](mailto:xknx@xknx.io).


