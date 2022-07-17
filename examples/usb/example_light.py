import asyncio
import logging
from xknx import XKNX

from xknx.devices import Light
from xknx.io.connection import ConnectionConfigUSB
import xknx.usb.util as usb_util


logging.basicConfig(level=logging.DEBUG)


async def main(vendor_id, product_id):
    usb_config = ConnectionConfigUSB(vendor_id, product_id)
    xknx = XKNX(connection_config=usb_config)
    await xknx.start()
    light = Light(xknx, name="TestOutlet", group_address_switch="1/2/10")
    await light.set_on()
    await asyncio.sleep(2)
    await light.set_off()
    await xknx.stop()


if __name__ == "__main__":
    vendor = usb_util.USBVendorId.JUNG_2130USBREG
    product = usb_util.USBProductId.JUNG_2130USBREG
    asyncio.run(main(vendor, product))
