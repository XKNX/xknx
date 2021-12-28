import logging
from xknx.exceptions.exception import USBDeviceNotFoundError
from xknx.usb.util import USBDevice
from .interface import Interface
from ..usb import get_first_matching_usb_device, USBKNXInterfaceData
from xknx.io.connection import ConnectionConfigUSB
from xknx.telegram import Telegram

logger = logging.getLogger("xknx.log")


class USBInterface(Interface):
    """ """

    def __init__(self, xknx, connection_config: ConnectionConfigUSB) -> None:
        self.xknx = xknx
        self.connection_config = connection_config
        self.usb_device: USBDevice | None = None

    async def start(self) -> None:
        """
        Find USB device with given idVendor and idProduct in the connection config.

        Raises
        ------
        USBDeviceNotFoundError
            if no USB device with idVendor and idProduct can be found
        """
        self.usb_device = get_first_matching_usb_device(  # search device by providing vendor and product id
            USBKNXInterfaceData(self.connection_config.idVendor, self.connection_config.idProduct)
        )
        if not self.usb_device:
            logger.error("USBInterface could not find USB device with idVendor: 0x%04x, idProduct: 0x%04x",
                         self.connection_config.idVendor, self.connection_config.idProduct)
            raise USBDeviceNotFoundError(
                "USBInterface could not find USB device with idVendor: 0x{0:0{1}X}, idProduct: 0x{2:0{3}X}".format(
                    self.connection_config.idVendor, 4, self.connection_config.idProduct, 4))

    async def stop(self) -> None:
        """ """
        self.usb_device = None

    async def connect(self) -> bool:
        """Connect to KNX bus. Returns True on success."""
        self.usb_device.use()  # claims the interface and sets up the endpoints for read/write

    async def disconnect(self) -> None:
        """Disconnect from KNX bus."""
        raise NotImplementedError

    async def send_telegram(self, telegram: Telegram) -> None:
        """Send Telegram to KNX bus."""
        raise NotImplementedError
