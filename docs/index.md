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
- ... supports KNX IP Secure - via tunneling or routing.
- ... supports KNX Data Secure group communication.
- ... has strong coverage with [unit tests](https://github.com/XKNX/xknx/tree/main/test).
- ... automatically updates and synchronizes all devices in the background periodically.
- ... listens for all updates of all devices on the KNX bus and updates the corresponding internal objects.
- ... has a clear abstraction of data/network/logic-layer.
- ... does clean [connect](https://github.com/XKNX/xknx/blob/main/xknx/io/connect.py) and [disconnect](https://github.com/XKNX/xknx/blob/main/xknx/io/disconnect.py) requests to the tunneling device and reconnects if KNX/IP connection failed.
- ... ships with [Home Assistant](https://home-assistant.io/).

## [](#header-2)Installation

XKNX depends on Python >= 3.9

You can install XKNX as Python package via pip:

```bash
pip install xknx
```

## [](#header-2)Hello World

```python
import asyncio
from xknx import XKNX
from xknx.tools import group_value_write

async def main():
    async with XKNX() as xknx:
        # send a binary Telegram
        await group_value_write(xknx, "1/2/3", True)
        # send a generic 1-byte Telegram
        await group_value_write(xknx, "1/2/4", [0x80])
        # send a Telegram with an encoded value
        await group_value_write(xknx, "1/2/4", 50, value_type="percent")

asyncio.run(main())
```

For more examples please check out the [examples page](https://github.com/XKNX/xknx/tree/main/examples)

# [](#header-1)Getting Help

For questions, feature requests, bugreports either join the [XKNX chat on Discord](https://discord.gg/EuAQDXU), open an issue at [GitHub](https://github.com/XKNX/xknx) or write an [email](mailto:xknx@xknx.io).

# [](#header-1)Attributions

Many thanks to [MDT technologies GmbH](https://www.mdt.de) and [Weinzierl Engineering GmbH](https://weinzierl.de) for providing us each an IP Secure Router to support testing and development of xknx.
