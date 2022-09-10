"""Example for connecting to a specific KNX interface."""
import asyncio
import logging
import time

from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType
from xknx.tools import read_group_value

logging.basicConfig(level=logging.INFO)
logging.getLogger("xknx.log").level = logging.DEBUG
logging.getLogger("xknx.knx").level = logging.DEBUG


async def main() -> None:
    """Connect to specific tunnelling server, time a request for a group address value."""
    connection_config = ConnectionConfig(
        connection_type=ConnectionType.TUNNELING,
        gateway_ip="10.1.0.40",
        # local_ip="10.1.0.123",
        # route_back=True,
    )
    xknx = XKNX(connection_config=connection_config)

    async with xknx:
        start_time = time.time()
        result = await read_group_value(xknx, "5/1/20", value_type="temperature")
        print(f"Value: {result} - took {(time.time() - start_time):0.3f} seconds")


asyncio.run(main())
