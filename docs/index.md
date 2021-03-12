---
layout: default
title: Asynchronous Python Library for KNX
nav_exclude: true
---

# [](#header-1)Asynchronous Python Library for KNX

XKNX is an Asynchronous Python library for reading and writing [KNX](<https://en.wikipedia.org/wiki/KNX_(standard)>)/IP packets.

[![Coverage Status](https://coveralls.io/repos/github/XKNX/xknx/badge.svg?branch=main)](https://coveralls.io/github/XKNX/xknx?branch=main)

## [](#header-2)Overview

XKNX...

- ... does [cooperative multitasking via asyncio](https://github.com/XKNX/xknx/blob/main/examples/example_light_state.py) and is 100% thread safe.
- ... provides support for KNX/IP [routing](https://github.com/XKNX/xknx/blob/main/xknx/io/routing.py) _and_ [tunneling](https://github.com/XKNX/xknx/blob/main/xknx/io/tunnel.py) devices.
- ... has strong coverage with [unit tests](https://github.com/XKNX/xknx/tree/main/test).
- ... automatically updates and synchronizes all devices in the background periodically.
- ... listens for all updates of all devices on the KNX bus and updates the corresponding internal objects.
- ... has a clear abstraction of data/network/logic-layer.
- ... provides Heartbeat monitoring for Tunneling connections + clean reconnect if KNX/IP connection failed.
- ... does clean [connect](https://github.com/XKNX/xknx/blob/main/xknx/io/connect.py) and [disconnect](https://github.com/XKNX/xknx/blob/main/xknx/io/disconnect.py) requests to the tunneling device.
- ... ships with [Home Assistant](https://home-assistant.io/).

## [](#header-2)Installation

XKNX depends on Python >= 3.7

You can install XKNX as Python package via pip:

```bash
pip install xknx
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
    await asyncio.sleep(2)
    await xknx.stop()

asyncio.run(main())
```

For more examples please check out the [examples page](https://github.com/XKNX/xknx/tree/main/examples)

# [](#header-1)Getting Help

For questions, feature requests, bugreports either join the [XKNX chat on Discord](https://discord.gg/EuAQDXU), open an issue at [GitHub](https://github.com/XKNX/xknx) or write an [email](mailto:xknx@xknx.io).
