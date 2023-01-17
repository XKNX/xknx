import asyncio
import logging

from xknx.devices import Switch
from xknx.io.connection import ConnectionConfigUSB
from xknx.xknx import XKNX

logging.basicConfig(level=logging.DEBUG)


async def main():
    xknx = XKNX(connection_config=ConnectionConfigUSB())
    await xknx.start()
    switch = Switch(xknx, name="TestOutlet", group_address="1/1/11")
    await switch.set_on()
    await asyncio.sleep(2)
    await switch.set_off()
    await xknx.stop()


if __name__ == "__main__":
    asyncio.run(main())
