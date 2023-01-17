import asyncio
import logging

from xknx.devices import Light
from xknx.io.connection import ConnectionConfigUSB
from xknx.xknx import XKNX

logging.basicConfig(level=logging.DEBUG)


async def main(config, switch_group_address):
    xknx = XKNX(connection_config=config)
    await xknx.start()
    light = Light(xknx, name="TestOutlet", group_address_switch=switch_group_address)
    await light.set_on()
    await asyncio.sleep(2)
    await light.set_off()
    await xknx.stop()


if __name__ == "__main__":
    switch_group_address = "1/2/10"
    asyncio.run(main(ConnectionConfigUSB(), switch_group_address))
