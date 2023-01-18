from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.core.thread import BaseThread
from xknx.io.interface import CEMICallbackType
from xknx.usb.knx_hid_helper import KNXtoCEMI
from xknx.usb.util import USBDevice

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class USBReceiveThread(BaseThread):
    """ """

    def __init__(
        self,
        xknx: XKNX,
        usb_device: USBDevice,
        cemi_received_callback: CEMICallbackType,
    ):
        """ """
        super().__init__(name="USBReceiveThread")
        self._xknx = xknx
        self._usb_device: USBDevice = usb_device
        self._knx_to_telegram = KNXtoCEMI()
        self.cemi_received_callback = cemi_received_callback

    def run(self) -> None:
        """ """
        while self._is_active.is_set():
            usb_data = self._usb_device.read()
            done, cemi_frame = self._knx_to_telegram.process(usb_data)
            if done and cemi_frame:
                self.cemi_received_callback(cemi_frame)
