import asyncio
import logging

from xknx.core.thread import BaseThread
from xknx.telegram import Telegram
from xknx.usb.knx_hid_helper import KNXToTelegram
from xknx.usb.util import USBDevice

logger = logging.getLogger("xknx.log")


class USBReceiveThread(BaseThread):
    """ """

    def __init__(
        self, xknx, usb_device: USBDevice, queue: asyncio.Queue[Telegram | None]
    ):
        """ """
        super().__init__(name="USBReceiveThread")
        self._xknx = xknx
        self._usb_device: USBDevice = usb_device
        self._receive_queue: asyncio.Queue[Telegram | None] = queue
        self._knx_to_telegram = KNXToTelegram()

    def run(self) -> None:
        """ """
        while self._is_active.is_set():
            usb_data = self._usb_device.read()
            done, telegram = self._knx_to_telegram.process(usb_data)
            if done:
                try:
                    self._xknx.telegrams.put_nowait(telegram)
                except asyncio.QueueFull:
                    logger.warning(f"queue full, dropping {telegram}")
