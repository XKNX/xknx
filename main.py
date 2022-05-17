import asyncio

from xknx import XKNX
from xknx.devices import Light
from xknx.io import ConnectionConfig, ConnectionType


async def light_callback(device: Light) -> None:
    print(f"light {'on' if device.state else 'off'}")


async def main() -> None:
    async with XKNX(
        connection_config=ConnectionConfig(
            gateway_ip="10.1.0.41", connection_type=ConnectionType.TUNNELING_TCP
        )
    ) as xknx:
        light = Light(
            xknx,
            "light",
            group_address_switch="1/1/45",
            group_address_switch_state="1/0/45",
        )
        light.register_device_updated_cb(light_callback)
        await asyncio.sleep(5)


asyncio.run(main())
