# XKNX - An asynchronous KNX library written in Python

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/xknx?logo=python)
[![codecov](https://codecov.io/gh/XKNX/xknx/branch/main/graph/badge.svg?token=irWbIygS84)](https://codecov.io/gh/XKNX/xknx)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=f8b424)](https://github.com/pre-commit/pre-commit)
[![HA integration usage](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcurrent_data.json&query=%24.integrations.knx&logo=home-assistant&label=integration%20usage&color=41BDF5&cacheSeconds=21600)](https://www.home-assistant.io/integrations/knx/)
[![Discord](https://img.shields.io/discord/338619021215924227?color=7289da&label=Discord&logo=discord&logoColor=7289da)](https://discord.gg/bkZe9m4zvw)

## Documentation

See documentation at: [https://xknx.io/](https://xknx.io/)

## Help

We need your help for testing and improving XKNX. For questions, feature requests, bug reports either open an [issue](https://github.com/XKNX/xknx/issues), join the [XKNX chat on Discord](https://discord.gg/EuAQDXU) or write an [email](mailto:xknx@xknx.io).

## Development

You will need at least Python 3.10 in order to use XKNX.

Setting up your local environment:

1. Install requirements: `pip install -r requirements/testing.txt`
2. Install pre-commit hook: `pre-commit install`

## Testing

To run all tests, linters, formatters and type checker call `tox`

Running only unit tests is possible with `pytest`
Running specific unit tests can be invoked by: `pytest -vv test/management_tests/procedures_test.py -k test_nm_individual_address_serial_number_write_fail`

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
        light = Light(
            xknx,
            name='TestLight',
            group_address_switch='1/0/9',
        )
        xknx.devices.async_add(light)

        await light.set_on()
        await asyncio.sleep(2)
        await light.set_off()

asyncio.run(main())
```

## Attributions

Many thanks to [Weinzierl Engineering GmbH](https://weinzierl.de) and [MDT technologies GmbH](https://www.mdt.de) for providing us each an IP Secure Router to support testing and development of xknx.
