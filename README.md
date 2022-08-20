# XKNX - An asynchronous KNX library written in Python

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/xknx?logo=python)
[![codecov](https://codecov.io/gh/XKNX/xknx/branch/main/graph/badge.svg?token=irWbIygS84)](https://codecov.io/gh/XKNX/xknx)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=f8b424)](https://github.com/pre-commit/pre-commit)
[![HA integration usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/data.json&query=current.integrations.knx)](https://www.home-assistant.io/integrations/knx/)
[![Discord](https://img.shields.io/discord/338619021215924227?color=7289da&label=Discord&logo=discord&logoColor=7289da)](https://discord.gg/bkZe9m4zvw)

## Documentation

See documentation at: [https://xknx.io/](https://xknx.io/)

## Help

We need your help for testing and improving XKNX. For questions, feature requests, bug reports either open an [issue](https://github.com/XKNX/xknx/issues), join the [XKNX chat on Discord](https://discord.gg/EuAQDXU) or write an [email](mailto:xknx@xknx.io).

## Development

You will need at least Python 3.9 in order to use XKNX.

Setting up your local environment:

1. Install requirements: `pip install -r requirements/testing.txt`
2. Install pre-commit hook: `pre-commit install`

## Home-Assistant

XKNX is the underlying library for the KNX integration in [Home Assistant](https://home-assistant.io/).

## Example

```python
"""Example for switching a light on and off."""
import asyncio

from xknx import XKNX
from xknx.devices import Light


async def main():
    """Connect to KNX/IP bus, switch on light, wait 2 seconds and switch it off again."""
    async with XKNX() as xknx:
        light = Light(xknx,
                      name='TestLight',
                      group_address_switch='1/0/9')
        await light.set_on()
        await asyncio.sleep(2)
        await light.set_off()

asyncio.run(main())
```

# Attributions

Many thanks to [Weinzierl Engineering GmbH](https://weinzierl.de) and [MDT technologies GmbH](https://www.mdt.de) for providing us each an IP Secure Router to support testing and development of xknx.
