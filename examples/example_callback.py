"""Example for running a callback when a devices state changed."""

import asyncio

from xknx import XKNX
from xknx.devices import Light
from xknx.io import ConnectionConfig, ConnectionType


def light_callback(light: Light) -> None:
    """Run callback when the light changed any of its state."""
    print(f"{light.name} - {light.state}")


async def main() -> None:
    """Connect to KNX/IP bus, turn on Light device and wait."""
    xknx = XKNX(
        connection_config=ConnectionConfig(
            gateway_ip="10.1.0.41",
            connection_type=ConnectionType.TUNNELING_TCP,
        ),
    )
    await xknx.start()
    light = Light(
        xknx,
        name="TestLight",
        group_address_switch="1/1/45",
        group_address_switch_state="1/0/45",
        device_updated_cb=light_callback,
    )
    xknx.devices.async_add(light)
    # turn on light and listen for 10 seconds for changes
    await light.set_on()
    await asyncio.sleep(10)
    await xknx.stop()


asyncio.run(main())
