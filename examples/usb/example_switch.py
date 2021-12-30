import asyncio
import logging
from xknx import XKNX

from xknx.devices import Switch
from xknx.io.connection import ConnectionConfigUSB
from xknx.usb.knx_hid_datatypes import PacketType
from xknx.usb.knx_hid_frame import KNXHIDFrame
import xknx.usb.util as usb_util


logging.basicConfig(level=logging.DEBUG)


async def main():
    xknx = XKNX(connection_config=ConnectionConfigUSB(usb_util.USBVendorId.SIEMENS_OCI702, usb_util.USBProductId.SIEMENS_OCI702))
    await xknx.start()
    switch = Switch(xknx, name="TestOutlet", group_address="1/1/11")
    await switch.set_on()
    await asyncio.sleep(2)
    await switch.set_off()
    await xknx.stop()


if __name__ == "__main__":
    asyncio.run(main())
