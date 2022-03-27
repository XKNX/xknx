"""Example for requesting a temperature."""
import asyncio
import logging
import time

from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.io import ConnectionConfig, ConnectionType
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite

logging.basicConfig(level=logging.INFO)
logging.getLogger("xknx.log").level = logging.DEBUG
logging.getLogger("xknx.knx").level = logging.DEBUG


async def main():
    """Connect to specific tunnelling server, time a request for a group address value."""
    connection_config = ConnectionConfig(
        connection_type=ConnectionType.AUTOMATIC,
        # local_ip="10.1.0.123",
        # route_back=True,
    )
    xknx = XKNX(connection_config=connection_config, rate_limit=0)

    telegram = Telegram(
        destination_address=GroupAddress("1/0/32"),
        payload=GroupValueWrite(DPTBinary(1)),
    )

    async with xknx:
        start_time = time.time()
        for _ in range(10):
            xknx.telegrams.put_nowait(telegram)
        await xknx.join()
        print(f"took {(time.time() - start_time):0.3f} seconds")
        await asyncio.sleep(1)


asyncio.run(main())
