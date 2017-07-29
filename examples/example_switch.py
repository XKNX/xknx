"""Example for Switch device."""
import asyncio
from xknx import XKNX
from xknx.devices import Switch

async def main():
    """Connect to KNX/IP device, switch on outlet, wait 2 seconds and switch of off again."""
    xknx = XKNX()
    await xknx.start()
    switch = Switch(xknx,
                    name='TestOutlet',
                    group_address='1/1/11')
    switch.set_on()
    await asyncio.sleep(2)
    switch.set_off()
    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
