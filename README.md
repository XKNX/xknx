# XKNX - An Asynchronous KNX Library Written in Python

[![codecov](https://codecov.io/gh/XKNX/xknx/branch/main/graph/badge.svg?token=irWbIygS84)](https://codecov.io/gh/XKNX/xknx)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## Documentation

See documentation at: [https://xknx.io/](https://xknx.io/)

## Help

We need your help for testing and improving XKNX. For questions, feature requests, bug reports either join the [XKNX chat on Discord](https://discord.gg/EuAQDXU) or write an [email](mailto:xknx@xknx.io).

## Development

You will need at least Python 3.8 in order to use XKNX.

Setting up your local environment:

1. Install requirements: `pip install -r requirements/testing.txt`
2. Install pre-commit hook: `pre-commit install`

## Home-Assistant Plugin

XKNX contains a [plugin](https://xknx.io/home_assistant) for the [Home Assistant](https://home-assistant.io/) automation platform

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
