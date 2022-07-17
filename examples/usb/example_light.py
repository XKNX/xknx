import asyncio
import logging
from xknx import XKNX

from xknx.devices import Light
from xknx.io.connection import ConnectionConfigUSB
from xknx.usb.util import USBVendorId, USBProductId


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
    vendor_id = USBVendorId.JUNG_2130USBREG
    product_id = USBProductId.JUNG_2130USBREG
    usb_config = ConnectionConfigUSB(vendor_id, product_id)
    switch_group_address = "1/2/10"

    asyncio.run(main(usb_config, switch_group_address))
