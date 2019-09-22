XKNX - An Asynchronous KNX Library Written in Python
====================================================

[![Build Status](https://travis-ci.org/XKNX/xknx.svg?branch=master)](https://travis-ci.org/XKNX/xknx)
[![Coverage Status](https://coveralls.io/repos/github/XKNX/xknx/badge.svg?branch=master)](https://coveralls.io/github/XKNX/xknx?branch=master)


Documentation
-------------


See documentation at: [https://xknx.io/](https://xknx.io/)

Help
----

We need your help for testing and improving XKNX. For questions, feature requests, bug reports either join the [XKNX chat on Discord](https://discord.gg/EuAQDXU) or write an [email](mailto:xknx@xknx.io).



Home-Assistant Plugin
---------------------

XKNX contains a [plugin](https://xknx.io/home_assistant) for the [Home Assistant](https://home-assistant.io/) automation platform


Example
-------

```python
"""Example for switching a light on and off."""
import asyncio
from xknx import XKNX
from xknx.devices import Light

async def main():
    """Connect to KNX/IP bus, switch on light, wait 2 seconds and switch it off again."""
    xknx = XKNX()
    await xknx.start()
    light = Light(xknx,
                  name='TestLight',
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
