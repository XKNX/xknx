"""Example for Switch device."""
import asyncio

from xknx import XKNX
from xknx.devices import Switch


async def main():
    """Connect to KNX/IP device, switch on outlet, read current power consumption, wait 2 seconds, switch it off again and print out total energy used."""
    xknx = XKNX()
    await xknx.start()
    switch = Switch(
        xknx,
        name="TestOutletMetered",
        group_address="1/1/11",
        group_address_current_power="1/1/12",
        group_address_total_energy="1/1/13",
    )
    await switch.set_on()
    print(switch.current_power)
    await asyncio.sleep(2)
    await switch.set_off()
    print(switch.total_energy)
    await xknx.stop()


asyncio.run(main())
