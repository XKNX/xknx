import logging

from ..usb import get_first_matching_usb_device, USBKNXInterfaceData
from xknx.exceptions.exception import USBDeviceNotFoundError
from xknx.io.connection import ConnectionConfigUSB
from xknx.telegram import Telegram
from xknx.usb.util import USBDevice


logger = logging.getLogger("xknx.log")


class USBClient:
    """ """
    def __init__(self, connection_config: ConnectionConfigUSB) -> None:
        self.connection_config = connection_config
        self.usb_device: USBDevice | None = None

    def start(self) -> None:
        """ """
        self.usb_device = get_first_matching_usb_device(  # search device by providing vendor and product id
            USBKNXInterfaceData(self.connection_config.idVendor, self.connection_config.idProduct)
        )
        if not self.usb_device:
            logger.error("USBInterface could not find USB device with idVendor: 0x%04x, idProduct: 0x%04x",
                         self.connection_config.idVendor, self.connection_config.idProduct)
            raise USBDeviceNotFoundError(
                "USBInterface could not find USB device with idVendor: 0x{0:0{1}X}, idProduct: 0x{2:0{3}X}".format(
                    self.connection_config.idVendor, 4, self.connection_config.idProduct, 4))
        raise NotImplementedError

    def stop(self) -> None:
        """ """
        self.usb_device.release()
        self.usb_device = None

    def connect(self) -> bool:
        """ """
        self.usb_device.use()  # claims the interface and sets up the endpoints for read/write
        raise NotImplementedError

    def disconnect(self) -> None:
        """ """
        raise NotImplementedError

    def send_telegram(self, telegram: Telegram) -> None:
        """ """
        raise NotImplementedError
