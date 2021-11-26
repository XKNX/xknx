"""Example for requesting a temperature."""
import asyncio
import logging
import time

from xknx import XKNX
from xknx.devices import Sensor
from xknx.io import ConnectionConfig, ConnectionType

logging.basicConfig(level=logging.INFO)
logging.getLogger("xknx.log").level = logging.DEBUG
logging.getLogger("xknx.knx").level = logging.DEBUG


async def main():
    """Connect to specific tunnelling server, time a request for a group address value."""
    connection_config = ConnectionConfig(
        connection_type=ConnectionType.TUNNELING,
        gateway_ip="10.1.0.40",
        # local_ip="10.1.0.123",
        # route_back=True,
    )
    xknx = XKNX(connection_config=connection_config)

    sensor = Sensor(
        xknx,
        name="Sensor",
        group_address_state="1/2/3",
        value_type="temperature",
    )

    async with xknx:
        start_time = time.time()
        await sensor.sync(wait_for_result=True)
        print(
            f"Value: {sensor.resolve_state()} - took {(time.time() - start_time):0.3f} seconds"
        )


asyncio.run(main())
