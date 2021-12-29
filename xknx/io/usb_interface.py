import logging

from xknx.io.usb_client import USBClient
from .interface import Interface
from xknx.io.connection import ConnectionConfigUSB
from xknx.telegram import Telegram

logger = logging.getLogger("xknx.log")


class USBInterface(Interface):
    """ """

    def __init__(self, xknx, connection_config: ConnectionConfigUSB) -> None:
        self.xknx = xknx
        self.usb_client: USBClient = USBClient(connection_config)

    async def start(self) -> None:
        """
        Find USB device with given idVendor and idProduct in the connection config.

        Raises
        ------
        USBDeviceNotFoundError
            if no USB device with idVendor and idProduct can be found
        """
        self.usb_client.start()

    async def stop(self) -> None:
        """ """
        self.usb_client.stop()

    async def connect(self) -> bool:
        """Connect to KNX bus. Returns True on success."""
        self.usb_client.connect()

    async def disconnect(self) -> None:
        """Disconnect from KNX bus."""
        self.usb_client.disconnect()

    async def send_telegram(self, telegram: Telegram) -> None:
        """Send Telegram to KNX bus."""
        self.usb_client.send_telegram(telegram=telegram)

    async def _receive_telegram(self, telegram: Telegram) -> None:
        """ """
        self.xknx.telegrams.put_nowait(telegram)